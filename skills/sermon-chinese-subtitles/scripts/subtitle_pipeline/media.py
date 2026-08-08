from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


FORMAL_SUFFIX = "_YouTube简体中文字幕_高精度校订版"
WINDOWS_FORBIDDEN = re.compile(r'[<>:"/\\|?*]')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def probe_media(path: Path) -> dict:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe is required but was not found on PATH")
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            (
                "format=duration,format_name:"
                "stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,"
                "sample_rate,channels,channel_layout,start_time,duration:stream_disposition"
            ),
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    payload = json.loads(completed.stdout)
    streams = payload.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if not video_streams:
        raise ValueError(f"specified sermon media has no video stream: {path}")
    if not audio_streams:
        raise ValueError(f"specified sermon video has no audio stream: {path}")
    duration_text = payload.get("format", {}).get("duration")
    if duration_text is None:
        raise ValueError(f"ffprobe did not report the media duration: {path}")
    return {
        "path": str(path),
        "format_duration": float(duration_text),
        "format_name": payload.get("format", {}).get("format_name"),
        "streams": streams,
        "video_streams": video_streams,
        "audio_streams": audio_streams,
    }


def _safe_stem(stem: str) -> str:
    cleaned = WINDOWS_FORBIDDEN.sub("", stem).rstrip(". ")
    if not cleaned:
        raise ValueError("video filename does not contain a usable output stem")
    return cleaned


def allocate_output_path(video: Path) -> Path:
    video = Path(video).resolve()
    base = video.parent / f"{_safe_stem(video.stem)}{FORMAL_SUFFIX}.srt"
    if not base.exists():
        return base
    version = 2
    while True:
        candidate = base.with_name(f"{base.stem}_v{version}{base.suffix}")
        if not candidate.exists():
            return candidate
        version += 1


def _allocate_run_dir(root: Path) -> Path:
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    candidate = root / timestamp
    counter = 2
    while candidate.exists():
        candidate = root / f"{timestamp}-{counter}"
        counter += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def create_run(
    video: Path,
    *,
    pptx: Path | None = None,
    audio_stream: int | None = None,
    work_root: Path | None = None,
) -> dict:
    video = Path(video).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    pptx_path = Path(pptx).resolve() if pptx is not None else None
    if pptx_path is not None and not pptx_path.is_file():
        raise FileNotFoundError(pptx_path)
    probe = probe_media(video)
    audio_streams = probe["audio_streams"]
    if audio_stream is None:
        if len(audio_streams) != 1:
            raise ValueError(
                f"specified video has multiple audio tracks ({len(audio_streams)}); "
                "provide the zero-based audio ordinal"
            )
        ordinal = 0
    else:
        ordinal = int(audio_stream)
        if ordinal < 0 or ordinal >= len(audio_streams):
            raise ValueError(
                f"audio ordinal {ordinal} is outside 0..{len(audio_streams) - 1}"
            )
    selected = audio_streams[ordinal]
    root = (
        Path(work_root).resolve()
        if work_root is not None
        else video.parent / "_work" / "subtitles" / _safe_stem(video.stem)
    )
    run_dir = _allocate_run_dir(root)
    output_path = allocate_output_path(video)
    inputs = [
        {
            "role": "specified_video",
            "path": str(video),
            "sha256": sha256(video),
        }
    ]
    if pptx_path is not None:
        inputs.append(
            {
                "role": "source_pptx",
                "path": str(pptx_path),
                "sha256": sha256(pptx_path),
            }
        )
    manifest = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "run_dir": str(run_dir),
        "formal_output": str(output_path),
        "inputs": inputs,
        "selected_audio": {
            "ordinal": ordinal,
            "stream_index": int(selected["index"]),
            "codec_name": selected.get("codec_name"),
            "sample_rate": selected.get("sample_rate"),
            "channels": selected.get("channels"),
            "start_time": selected.get("start_time"),
            "duration": selected.get("duration"),
        },
        "probe": probe,
    }
    manifest_path = run_dir / "source_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "run_dir": str(run_dir),
        "manifest_path": str(manifest_path),
        "formal_output": str(output_path),
        "manifest": manifest,
    }


def extract_selected_audio(manifest: dict, destination: Path) -> dict:
    video = Path(next(item["path"] for item in manifest["inputs"] if item["role"] == "specified_video"))
    ordinal = int(manifest["selected_audio"]["ordinal"])
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required but was not found on PATH")
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(video),
            "-map",
            f"0:a:{ordinal}",
            "-vn",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ],
        check=True,
    )
    return {"path": str(destination), "sha256": sha256(destination)}
