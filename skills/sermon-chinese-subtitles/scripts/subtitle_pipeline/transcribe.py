from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _context_values(context: dict) -> list[str]:
    values: list[str] = []
    for key in ("sermon_title", "speaker"):
        value = str(context.get(key, "")).strip()
        if value:
            values.append(value)
    for key in ("scripture", "sermon_points", "proper_names", "hotwords", "church_terms"):
        raw = context.get(key, [])
        if isinstance(raw, str):
            raw = [raw]
        values.extend(str(item).strip() for item in raw if str(item).strip())
    return list(dict.fromkeys(values))


def build_transcribe_options(pass_name: str, context: dict) -> dict:
    if pass_name not in {"primary", "precision", "regional"}:
        raise ValueError(f"unknown ASR pass: {pass_name}")
    context_values = _context_values(context)
    prompt_prefix = str(context.get("prompt_prefix", "华语基督教讲道。"))
    prompt = prompt_prefix + "本讲上下文与专有词：" + "、".join(context_values) + "。"
    hotword_values = []
    for key in ("proper_names", "hotwords", "church_terms"):
        raw = context.get(key, [])
        if isinstance(raw, str):
            raw = [raw]
        hotword_values.extend(str(item).strip() for item in raw if str(item).strip())
    options = {
        "language": "zh",
        "beam_size": {"primary": 5, "precision": 8, "regional": 10}[pass_name],
        "temperature": 0.0,
        "condition_on_previous_text": True,
        "repetition_penalty": 1.1,
        "no_repeat_ngram_size": 3,
        "hallucination_silence_threshold": 2.0,
        "initial_prompt": prompt,
        "hotwords": " ".join(dict.fromkeys(hotword_values)),
        "vad_filter": pass_name != "regional",
        "word_timestamps": True,
    }
    if pass_name == "primary":
        options["vad_parameters"] = {
            "min_silence_duration_ms": 500,
            "max_speech_duration_s": 30,
            "speech_pad_ms": 300,
        }
    elif pass_name == "precision":
        options["vad_parameters"] = {
            "min_silence_duration_ms": 350,
            "max_speech_duration_s": 20,
            "speech_pad_ms": 250,
        }
    return options


def validate_regions(regions: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    seen: set[str] = set()
    for index, region in enumerate(regions, start=1):
        region_id = str(region.get("id", "")).strip()
        reason = str(region.get("reason", "")).strip()
        start = float(region.get("start", -1))
        end = float(region.get("end", -1))
        if not region_id or region_id in seen:
            raise ValueError(f"regional ASR entry {index} requires a unique id")
        if not reason:
            raise ValueError(f"regional ASR entry {region_id} requires a semantic reason")
        if start < 0 or end <= start:
            raise ValueError(
                f"regional ASR entry {region_id} must use a positive absolute interval"
            )
        seen.add(region_id)
        normalized.append({"id": region_id, "start": start, "end": end, "reason": reason})
    return normalized


def _enable_nvidia_dlls() -> list[object]:
    handles: list[object] = []
    site_packages = Path(sys.prefix) / "Lib" / "site-packages"
    candidates = [
        site_packages / "nvidia" / "cublas" / "bin",
        site_packages / "nvidia" / "cudnn" / "bin",
        site_packages / "nvidia" / "cuda_nvrtc" / "bin",
    ]
    existing = [str(path) for path in candidates if path.is_dir()]
    if existing:
        os.environ["PATH"] = os.pathsep.join(existing + [os.environ.get("PATH", "")])
        if hasattr(os, "add_dll_directory"):
            handles.extend(os.add_dll_directory(path) for path in existing)
    return handles


def _load_model(model_name: str, model_dir: Path | None, allow_model_download: bool):
    try:
        from faster_whisper import WhisperModel
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "faster-whisper is unavailable; run scripts/bootstrap.ps1 before transcription"
        ) from error
    kwargs = {
        "download_root": str(model_dir) if model_dir else None,
        "local_files_only": not allow_model_download,
        "cpu_threads": max(1, os.cpu_count() or 1),
        "num_workers": 1,
    }
    try:
        return WhisperModel(model_name, device="cuda", compute_type="float16", **kwargs), "cuda"
    except Exception as cuda_error:
        try:
            return WhisperModel(model_name, device="cpu", compute_type="int8", **kwargs), "cpu"
        except Exception as cpu_error:
            raise RuntimeError(
                f"unable to load local Faster-Whisper model {model_name!r}; "
                f"CUDA error: {cuda_error}; CPU error: {cpu_error}"
            ) from cpu_error


def collect_segments(segments_iter, *, timestamp_offset: float = 0.0) -> list[dict]:
    items: list[dict] = []
    for segment in segments_iter:
        items.append(
            {
                "id": segment.id,
                "start": round(float(segment.start) + timestamp_offset, 3),
                "end": round(float(segment.end) + timestamp_offset, 3),
                "text": str(segment.text).strip(),
                "avg_logprob": round(float(segment.avg_logprob), 4),
                "no_speech_prob": round(float(segment.no_speech_prob), 4),
                "words": [
                    {
                        "start": round(float(word.start) + timestamp_offset, 3),
                        "end": round(float(word.end) + timestamp_offset, 3),
                        "word": str(word.word),
                        "probability": round(float(word.probability), 4),
                    }
                    for word in (segment.words or [])
                ],
            }
        )
    return items


def run_transcription(
    media_path: Path,
    output_json: Path,
    *,
    pass_name: str,
    context: dict,
    model_name: str = "large-v3",
    model_dir: Path | None = None,
    allow_model_download: bool = False,
    regions: list[dict] | None = None,
    output_text: Path | None = None,
    timestamp_offset: float = 0.0,
) -> dict:
    media_path = Path(media_path).resolve()
    if not media_path.is_file():
        raise FileNotFoundError(media_path)
    if pass_name == "regional" and not regions:
        raise ValueError("regional ASR requires at least one evidence-driven absolute region")
    if pass_name != "regional" and regions:
        raise ValueError("full ASR passes do not accept regional windows")
    handles = _enable_nvidia_dlls()
    model, device = _load_model(model_name, model_dir, allow_model_download)
    base_options = build_transcribe_options(pass_name, context)

    if pass_name == "regional":
        region_results: list[dict] = []
        for region in validate_regions(regions or []):
            options = dict(base_options)
            options["initial_prompt"] = (
                f"{base_options['initial_prompt']}当前疑难区段：{region['reason']}。"
            )
            local_start = max(0.0, float(region["start"]) - timestamp_offset)
            local_end = float(region["end"]) - timestamp_offset
            if local_end <= local_start:
                raise ValueError(
                    f"regional ASR entry {region['id']} lies before the selected audio stream"
                )
            segments_iter, info = model.transcribe(
                str(media_path),
                clip_timestamps=[local_start, local_end],
                **options,
            )
            region_results.append(
                {
                    **region,
                    "segments": collect_segments(
                        segments_iter, timestamp_offset=timestamp_offset
                    ),
                    "language": info.language,
                    "language_probability": info.language_probability,
                }
            )
        payload = {
            "media": str(media_path),
            "model": model_name,
            "device": device,
            "pass": pass_name,
            "timestamp_offset": timestamp_offset,
            "regions": region_results,
        }
        text_lines = [
            f"[{segment['start']:.3f} --> {segment['end']:.3f}] {segment['text']}"
            for region in region_results
            for segment in region["segments"]
        ]
    else:
        segments_iter, info = model.transcribe(str(media_path), **base_options)
        segments = collect_segments(segments_iter, timestamp_offset=timestamp_offset)
        payload = {
            "media": str(media_path),
            "model": model_name,
            "device": device,
            "pass": pass_name,
            "timestamp_offset": timestamp_offset,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": segments,
        }
        text_lines = [
            f"[{segment['start']:.3f} --> {segment['end']:.3f}] {segment['text']}"
            for segment in segments
        ]
    output_json = Path(output_json).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if output_text is not None:
        Path(output_text).resolve().write_text(
            "\n".join(text_lines) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    del handles
    return payload
