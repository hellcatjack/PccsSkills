from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
from typing import Any

import soundfile as sf

from .models import PacketTiming, SourceManifest, StreamSummary
from .policy import (
    PolicyError,
    assert_safe_command,
    assert_safe_output,
    assert_source_unchanged,
    sha256_file,
)


class ProbeError(RuntimeError):
    pass


class AmbiguousAudioStreamError(ProbeError):
    pass


def _run_json(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads(completed.stdout)


def _optional_int(value: Any) -> int | None:
    if value in (None, "N/A", ""):
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value in (None, "N/A", ""):
        return None
    return float(value)


def _stream_summary(stream: dict[str, Any]) -> StreamSummary:
    return StreamSummary(
        index=int(stream["index"]),
        codec_type=str(stream.get("codec_type", "unknown")),
        codec_name=stream.get("codec_name"),
        time_base=stream.get("time_base"),
        start_pts=_optional_int(stream.get("start_pts")),
        start_time=_optional_float(stream.get("start_time")),
        duration_ts=_optional_int(stream.get("duration_ts")),
        duration=_optional_float(stream.get("duration")),
        tags={str(k): str(v) for k, v in stream.get("tags", {}).items()},
        disposition={
            str(k): int(v) for k, v in stream.get("disposition", {}).items()
        },
    )


def _packet_timing(packet: dict[str, Any]) -> PacketTiming:
    return PacketTiming(
        pts=_optional_int(packet.get("pts")),
        pts_time=_optional_float(packet.get("pts_time")),
        duration=_optional_int(packet.get("duration")),
        duration_time=_optional_float(packet.get("duration_time")),
    )


def _decoded_sample_count(
    source: Path,
    audio_ordinal: int,
    channels: int,
) -> int:
    args = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-map",
        f"0:a:{audio_ordinal}",
        "-f",
        "f64le",
        "-c:a",
        "pcm_f64le",
        "-",
    ]
    assert_safe_command(args)
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stdout is None or process.stderr is None:
        raise ProbeError("Unable to open FFmpeg pipes")

    byte_count = 0
    while True:
        chunk = process.stdout.read(1024 * 1024)
        if not chunk:
            break
        byte_count += len(chunk)
    stderr = process.stderr.read().decode("utf-8", errors="replace")
    return_code = process.wait()
    if return_code != 0:
        raise ProbeError(f"FFmpeg decode failed: {stderr.strip()}")

    bytes_per_frame = 8 * channels
    if byte_count % bytes_per_frame:
        raise ProbeError("Decoded PCM byte count is not frame aligned")
    return byte_count // bytes_per_frame


def hash_stream_packets(source: Path, stream_index: int) -> str:
    args = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-map",
        f"0:{stream_index}",
        "-c",
        "copy",
        "-f",
        "hash",
        "-hash",
        "sha256",
        "-",
    ]
    assert_safe_command(args)
    completed = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"SHA256=([0-9a-fA-F]{64})", completed.stdout)
    if not match:
        raise ProbeError(f"Unable to hash stream {stream_index}")
    return match.group(1).lower()


def _packet_gaps(
    packets: list[dict[str, Any]], sample_rate: int
) -> tuple[tuple[float, float], ...]:
    gaps: list[tuple[float, float]] = []
    previous_end: float | None = None
    tolerance = max(2.0 / sample_rate, 0.00001)
    for packet in packets:
        start = _optional_float(packet.get("pts_time"))
        duration = _optional_float(packet.get("duration_time"))
        if start is None:
            continue
        if previous_end is not None and start - previous_end > tolerance:
            gaps.append((previous_end, start))
        if duration is not None:
            previous_end = start + duration
        else:
            previous_end = start
    return tuple(gaps)


def probe_source(source: Path, audio_stream: int | None = None) -> SourceManifest:
    source = source.resolve()
    if not source.is_file():
        raise ProbeError(f"Source file does not exist: {source}")

    media = _run_json(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(source),
        ]
    )
    streams = media.get("streams", [])
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    if not audio_streams:
        raise ProbeError("Source contains no audio streams")

    if audio_stream is None:
        if len(audio_streams) != 1:
            raise AmbiguousAudioStreamError(
                f"Source contains {len(audio_streams)} audio streams; select a zero-based audio ordinal"
            )
        audio_ordinal = 0
    else:
        audio_ordinal = int(audio_stream)
        if audio_ordinal < 0 or audio_ordinal >= len(audio_streams):
            raise ProbeError(f"Audio ordinal is out of range: {audio_ordinal}")

    selected = audio_streams[audio_ordinal]
    stream_index = int(selected["index"])
    sample_rate = int(selected["sample_rate"])
    channels = int(selected["channels"])
    decoded_samples = _decoded_sample_count(source, audio_ordinal, channels)

    packet_data = _run_json(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            f"a:{audio_ordinal}",
            "-show_packets",
            "-show_entries",
            "packet=pts,pts_time,duration,duration_time",
            "-of",
            "json",
            str(source),
        ]
    )
    packets = packet_data.get("packets", [])
    first_packet = _packet_timing(packets[0]) if packets else None
    last_packet = _packet_timing(packets[-1]) if packets else None

    start_time = _optional_float(selected.get("start_time"))
    if start_time is None and first_packet is not None:
        start_time = first_packet.pts_time
    if start_time is None:
        start_time = 0.0

    non_target_hashes = {
        f"stream:{int(item['index'])}": hash_stream_packets(source, int(item["index"]))
        for item in streams
        if int(item["index"]) != stream_index
    }
    video_streams = tuple(
        _stream_summary(item) for item in streams if item.get("codec_type") == "video"
    )
    other_streams = tuple(
        _stream_summary(item) for item in streams if int(item["index"]) != stream_index
    )

    format_info = media.get("format", {})
    return SourceManifest(
        source_path=str(source),
        source_sha256=sha256_file(source),
        format_name=str(format_info.get("format_name", "unknown")),
        format_duration=_optional_float(format_info.get("duration")),
        audio_ordinal=audio_ordinal,
        stream_index=stream_index,
        codec_name=str(selected.get("codec_name", "unknown")),
        sample_rate=sample_rate,
        channels=channels,
        channel_layout=selected.get("channel_layout"),
        time_base=str(selected.get("time_base", f"1/{sample_rate}")),
        start_pts=_optional_int(selected.get("start_pts")),
        start_time=start_time,
        duration_ts=_optional_int(selected.get("duration_ts")),
        duration_seconds=decoded_samples / sample_rate,
        decoded_sample_count=decoded_samples,
        first_packet=first_packet,
        last_packet=last_packet,
        packet_gaps=_packet_gaps(packets, sample_rate),
        video_streams=video_streams,
        other_streams=other_streams,
        non_target_stream_hashes=non_target_hashes,
        tags={str(k): str(v) for k, v in selected.get("tags", {}).items()},
        disposition={
            str(k): int(v) for k, v in selected.get("disposition", {}).items()
        },
    )


def extract_baseline(manifest: SourceManifest, work_dir: Path) -> Path:
    source = Path(manifest.source_path)
    assert_source_unchanged(source, manifest.source_sha256)
    work_dir.mkdir(parents=True, exist_ok=True)
    output = work_dir / "baseline.wav"
    assert_safe_output(source, output)

    args = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-map",
        f"0:a:{manifest.audio_ordinal}",
        "-vn",
        "-sn",
        "-dn",
        "-c:a",
        "pcm_f32le",
        str(output),
    ]
    assert_safe_command(args)
    subprocess.run(args, check=True)

    info = sf.info(output)
    if info.frames != manifest.decoded_sample_count:
        raise PolicyError(
            f"Baseline sample mismatch: expected {manifest.decoded_sample_count}, found {info.frames}"
        )
    if info.samplerate != manifest.sample_rate or info.channels != manifest.channels:
        raise PolicyError("Baseline format differs from source audio")
    assert_source_unchanged(source, manifest.source_sha256)
    return output
