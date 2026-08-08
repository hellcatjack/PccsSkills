#!/usr/bin/env python3
"""Align external audio to a video, replace one audio stream, and verify the result."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Sequence

import numpy as np


ANALYSIS_SAMPLE_RATE = 8000
FEATURE_SECONDS = 0.1


class ReplacementError(RuntimeError):
    pass


def run_process(command: Sequence[str], *, capture_stdout: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [str(part) for part in command],
        stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise ReplacementError(f"Command failed ({result.returncode}): {' '.join(map(str, command))}\n{stderr}")
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def ffprobe_json(path: Path, ffprobe: str = "ffprobe") -> dict[str, Any]:
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    result = run_process(command, capture_stdout=True)
    return json.loads(result.stdout.decode("utf-8"))


def parse_rate(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator)
    return float(value)


def video_timing(probe: dict[str, Any]) -> dict[str, Any]:
    stream = next((item for item in probe["streams"] if item["codec_type"] == "video"), None)
    if stream is None:
        raise ReplacementError("Input has no video stream")
    frame_rate = parse_rate(stream.get("avg_frame_rate") or stream.get("r_frame_rate"))
    duration = float(stream.get("duration") or 0.0)
    frame_count = int(stream.get("nb_frames") or 0)
    if duration <= 0 and frame_count and frame_rate:
        duration = frame_count / frame_rate
    if duration <= 0:
        raise ReplacementError("Cannot determine authoritative video-stream duration")
    return {
        "global_stream_index": int(stream["index"]),
        "duration_seconds": duration,
        "frame_rate": frame_rate,
        "frame_count": frame_count,
        "codec": stream.get("codec_name"),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "start_time": float(stream.get("start_time") or 0.0),
    }


def audio_stream(probe: dict[str, Any], ordinal: int) -> dict[str, Any]:
    streams = [item for item in probe["streams"] if item["codec_type"] == "audio"]
    if ordinal < 0 or ordinal >= len(streams):
        raise ReplacementError(f"Audio ordinal {ordinal} does not exist; found {len(streams)} audio stream(s)")
    return streams[ordinal]


def decode_analysis_pcm(
    path: Path,
    audio_ordinal: int,
    *,
    ffmpeg: str = "ffmpeg",
    sample_rate: int = ANALYSIS_SAMPLE_RATE,
) -> np.ndarray:
    command = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(path),
        "-map",
        f"0:a:{audio_ordinal}",
        "-vn",
        "-af",
        "highpass=f=100,lowpass=f=3800",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "s16le",
        "-",
    ]
    result = run_process(command, capture_stdout=True)
    return np.frombuffer(result.stdout, dtype="<i2").astype(np.float32) / 32768.0


def normalized_valid_correlation(signal: np.ndarray, query: np.ndarray) -> np.ndarray:
    if len(query) > len(signal):
        raise ReplacementError("Correlation query is longer than signal")
    query64 = np.asarray(query, dtype=np.float64)
    signal64 = np.asarray(signal, dtype=np.float64)
    query64 -= query64.mean()
    fft_size = 1 << ((len(signal64) + len(query64) - 2).bit_length())
    convolution = np.fft.irfft(
        np.fft.rfft(signal64, fft_size) * np.fft.rfft(query64[::-1], fft_size),
        fft_size,
    )
    numerator = convolution[len(query64) - 1 : len(signal64)]
    cumulative = np.concatenate(([0.0], np.cumsum(signal64)))
    cumulative_sq = np.concatenate(([0.0], np.cumsum(signal64 * signal64)))
    window_sum = cumulative[len(query64) :] - cumulative[: -len(query64)]
    window_sq = cumulative_sq[len(query64) :] - cumulative_sq[: -len(query64)]
    variance = np.maximum(window_sq - window_sum * window_sum / len(query64), 1e-20)
    denominator = np.sqrt(variance * np.sum(query64 * query64))
    return numerator / denominator


def spectral_features(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    hop = max(32, round(sample_rate * FEATURE_SECONDS))
    frame_count = len(samples) // hop
    if frame_count < 10:
        raise ReplacementError("Audio is too short for reliable alignment")
    samples = samples[: frame_count * hop]
    window = np.hanning(hop).astype(np.float32)
    frequencies = np.fft.rfftfreq(hop, 1.0 / sample_rate)
    bands = ((100, 250), (250, 500), (500, 900), (900, 1400), (1400, 2200), (2200, 3200), (3200, 3900))
    chunks: list[np.ndarray] = []
    for start in range(0, frame_count, 2000):
        frames = samples[start * hop : min(frame_count, start + 2000) * hop].reshape(-1, hop)
        weighted = frames * window
        spectrum = np.abs(np.fft.rfft(weighted, axis=1)) ** 2
        columns = [np.log1p(np.mean(weighted * weighted, axis=1) * 1e7)]
        for low, high in bands:
            mask = (frequencies >= low) & (frequencies < high)
            columns.append(np.log1p(np.mean(spectrum[:, mask], axis=1) * 1e4))
        chunks.append(np.stack(columns, axis=1).astype(np.float32))
    return np.concatenate(chunks, axis=0)


def _parabolic_peak(values: np.ndarray, index: int) -> float:
    if index <= 0 or index >= len(values) - 1:
        return 0.0
    denominator = values[index - 1] - 2 * values[index] + values[index + 1]
    if abs(denominator) < 1e-20:
        return 0.0
    return float(0.5 * (values[index - 1] - values[index + 1]) / denominator)


def estimate_alignment_arrays(
    video_audio: np.ndarray,
    external_audio: np.ndarray,
    sample_rate: int = ANALYSIS_SAMPLE_RATE,
    *,
    anchor_count: int = 7,
) -> dict[str, Any]:
    video_audio = np.asarray(video_audio, dtype=np.float32)
    external_audio = np.asarray(external_audio, dtype=np.float32)
    if len(external_audio) < len(video_audio):
        raise ReplacementError("External recording is shorter than the video reference audio")
    if anchor_count < 3:
        raise ReplacementError("At least three anchors are required")

    video_features = spectral_features(video_audio, sample_rate)
    external_features = spectral_features(external_audio, sample_rate)
    score = np.zeros(len(external_features) - len(video_features) + 1, dtype=np.float64)
    for column in range(video_features.shape[1]):
        score += normalized_valid_correlation(external_features[:, column], video_features[:, column])
    score /= video_features.shape[1]
    best_index = int(np.argmax(score))
    coarse_offset = best_index * FEATURE_SECONDS

    exclusion = max(1, round(2.0 / FEATURE_SECONDS))
    runner_score = -1.0
    runner_index = -1
    if len(score) > 2 * exclusion + 1:
        mask = np.ones(len(score), dtype=bool)
        mask[max(0, best_index - exclusion) : min(len(score), best_index + exclusion + 1)] = False
        if np.any(mask):
            masked_indices = np.flatnonzero(mask)
            local = int(np.argmax(score[mask]))
            runner_index = int(masked_indices[local])
            runner_score = float(score[runner_index])

    duration = len(video_audio) / sample_rate
    half_window = min(15.0, max(0.5, duration / (anchor_count * 4.0)))
    search_margin = 1.0
    # Keep the final query clear of an uncertain codec-framed tail.  The coarse
    # estimate can differ from the refined offset by part of search_margin.
    safe_video_end = min(
        duration,
        len(external_audio) / sample_rate - coarse_offset - search_margin,
    )
    if safe_video_end <= 0:
        raise ReplacementError("The coarse match leaves no complete anchor window")
    if safe_video_end <= 2 * half_window:
        half_window = safe_video_end / 4.0
    centers = np.linspace(half_window, safe_video_end - half_window, anchor_count)
    anchors: list[dict[str, float]] = []
    for center in centers:
        query_start = max(0.0, float(center) - half_window)
        query_end = min(duration, float(center) + half_window)
        query = video_audio[round(query_start * sample_rate) : round(query_end * sample_rate)]
        search_start = max(0.0, coarse_offset + query_start - search_margin)
        search_end = min(
            len(external_audio) / sample_rate,
            coarse_offset + query_end + search_margin,
        )
        search_audio = external_audio[round(search_start * sample_rate) : round(search_end * sample_rate)]
        correlation = normalized_valid_correlation(search_audio, query)
        magnitude = np.abs(correlation)
        peak = int(np.argmax(magnitude))
        fractional = _parabolic_peak(magnitude, peak)
        external_query_start = search_start + (peak + fractional) / sample_rate
        anchors.append(
            {
                "video_center_seconds": float(center),
                "external_offset_seconds": float(external_query_start - query_start),
                "correlation": float(magnitude[peak]),
            }
        )

    times = np.array([anchor["video_center_seconds"] for anchor in anchors])
    offsets = np.array([anchor["external_offset_seconds"] for anchor in anchors])
    slope, intercept = np.polyfit(times, offsets, 1)
    predicted = intercept + slope * times
    residuals = offsets - predicted
    return {
        "external_start_seconds": float(intercept),
        "external_start_timecode": format_timecode(float(intercept)),
        "coarse_start_seconds": float(coarse_offset),
        "global_score": float(score[best_index]),
        "runner_up_start_seconds": float(runner_index * FEATURE_SECONDS) if runner_index >= 0 else None,
        "runner_up_score": runner_score if runner_index >= 0 else None,
        "candidate_score_gap": float(score[best_index] - runner_score) if runner_index >= 0 else None,
        "anchors": anchors,
        "minimum_anchor_correlation": float(min(anchor["correlation"] for anchor in anchors)),
        "clock_scale": float(1.0 + slope),
        "drift_seconds_per_video_second": float(slope),
        "drift_over_video_seconds": float(slope * duration),
        "maximum_anchor_residual_seconds": float(np.max(np.abs(residuals))),
        "video_decoded_duration_seconds": float(duration),
        "external_decoded_duration_seconds": float(len(external_audio) / sample_rate),
        "analysis_sample_rate": sample_rate,
    }


def format_timecode(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remainder = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remainder:07.4f}"


def build_mux_command(
    *,
    ffmpeg: str,
    video_path: Path,
    external_audio_path: Path,
    output_path: Path,
    streams: list[dict[str, Any]],
    target_audio_stream_index: int,
    external_start_seconds: float,
    video_duration_seconds: float,
    audio_bitrate: str,
    sample_rate: int,
    channels: int,
    external_audio_ordinal: int = 0,
    language: str | None = None,
    disposition: str | None = None,
) -> list[str]:
    audio_ordinal = -1
    target_output_audio_ordinal = None
    command = [
        ffmpeg,
        "-hide_banner",
        "-n",
        "-i",
        str(video_path),
        "-i",
        str(external_audio_path),
        "-filter_complex",
        (
            f"[1:a:{external_audio_ordinal}]"
            f"atrim=start={external_start_seconds:.9f}:duration={video_duration_seconds:.9f},"
            "asetpts=PTS-STARTPTS[replacement_audio]"
        ),
    ]
    for stream in streams:
        if stream["codec_type"] == "audio":
            audio_ordinal += 1
        if int(stream["index"]) == target_audio_stream_index:
            command.extend(["-map", "[replacement_audio]"])
            target_output_audio_ordinal = audio_ordinal
        else:
            command.extend(["-map", f"0:{int(stream['index'])}"])
    if target_output_audio_ordinal is None:
        raise ReplacementError("Target audio global stream index was not mapped")
    ordinal = target_output_audio_ordinal
    command.extend(
        [
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            "-c",
            "copy",
            f"-c:a:{ordinal}",
            "aac",
            f"-b:a:{ordinal}",
            audio_bitrate,
            f"-ar:a:{ordinal}",
            str(sample_rate),
            f"-ac:a:{ordinal}",
            str(channels),
        ]
    )
    if language:
        command.extend([f"-metadata:s:a:{ordinal}", f"language={language}"])
    if disposition:
        command.extend([f"-disposition:a:{ordinal}", disposition])
    command.append(str(output_path))
    return command


def disposition_string(stream: dict[str, Any]) -> str | None:
    values = stream.get("disposition") or {}
    active = [key for key, enabled in values.items() if enabled and key not in {"attached_pic"}]
    return "+".join(active) if active else "0"


def packet_hash(path: Path, stream_index: int, ffmpeg: str = "ffmpeg") -> str:
    command = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(path),
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
    result = run_process(command, capture_stdout=True)
    match = re.search(rb"SHA256=([0-9a-fA-F]{64})", result.stdout)
    if not match:
        raise ReplacementError(f"Could not read packet hash for stream {stream_index}")
    return match.group(1).decode("ascii").lower()


def alignment_status(report: dict[str, Any], frame_seconds: float) -> tuple[str, list[str]]:
    failures = []
    if report["global_score"] < 0.35:
        failures.append(f"global score {report['global_score']:.3f} is below 0.35")
    if report["minimum_anchor_correlation"] < 0.45:
        failures.append(f"minimum anchor correlation {report['minimum_anchor_correlation']:.3f} is below 0.45")
    gap = report.get("candidate_score_gap")
    if gap is not None and gap < 0.10:
        failures.append(f"candidate score gap {gap:.3f} is below 0.10")
    if abs(report["drift_over_video_seconds"]) > frame_seconds:
        failures.append(
            f"accumulated drift {report['drift_over_video_seconds']:.6f}s exceeds one frame {frame_seconds:.6f}s"
        )
    return ("pass" if not failures else "review_required", failures)


def analyze_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    video_probe = ffprobe_json(args.video, args.ffprobe)
    audio_probe = ffprobe_json(args.audio, args.ffprobe)
    timing = video_timing(video_probe)
    target = audio_stream(video_probe, args.video_audio_ordinal)
    external_stream = audio_stream(audio_probe, args.external_audio_ordinal)
    video_pcm = decode_analysis_pcm(args.video, args.video_audio_ordinal, ffmpeg=args.ffmpeg)
    external_pcm = decode_analysis_pcm(args.audio, args.external_audio_ordinal, ffmpeg=args.ffmpeg)
    alignment = estimate_alignment_arrays(video_pcm, external_pcm, ANALYSIS_SAMPLE_RATE, anchor_count=args.anchor_count)
    frame_seconds = 1.0 / timing["frame_rate"] if timing["frame_rate"] else 1.0 / 30.0
    status, failures = alignment_status(alignment, frame_seconds)
    alignment.update(
        {
            "status": status,
            "review_reasons": failures,
            "video": str(args.video.resolve()),
            "external_audio": str(args.audio.resolve()),
            "video_timing": timing,
            "target_video_audio_ordinal": args.video_audio_ordinal,
            "target_video_audio_global_index": int(target["index"]),
            "external_audio_ordinal": args.external_audio_ordinal,
            "external_stream": {
                "codec": external_stream.get("codec_name"),
                "sample_rate": int(external_stream.get("sample_rate") or 0),
                "channels": int(external_stream.get("channels") or 0),
            },
        }
    )
    return alignment, video_pcm, external_pcm


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_output(
    args: argparse.Namespace,
    report: dict[str, Any],
    source_probe: dict[str, Any],
    external_pcm: np.ndarray,
    source_hashes: dict[str, str],
    command: list[str],
) -> dict[str, Any]:
    output_probe = ffprobe_json(args.output, args.ffprobe)
    source_timing = video_timing(source_probe)
    output_timing = video_timing(output_probe)
    target_index = int(report["target_video_audio_global_index"])
    non_target_hashes = []
    for stream in source_probe["streams"]:
        index = int(stream["index"])
        if index == target_index:
            continue
        source_packet_hash = packet_hash(args.video, index, args.ffmpeg)
        output_packet_hash = packet_hash(args.output, index, args.ffmpeg)
        non_target_hashes.append(
            {
                "stream_index": index,
                "codec_type": stream["codec_type"],
                "source": source_packet_hash,
                "output": output_packet_hash,
                "match": source_packet_hash == output_packet_hash,
            }
        )

    decode_command = [
        args.ffmpeg,
        "-v",
        "error",
        "-xerror",
        "-i",
        str(args.output),
        "-map",
        "0",
        "-f",
        "null",
        "-",
    ]
    decode_result = subprocess.run(decode_command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
    final_pcm = decode_analysis_pcm(args.output, args.video_audio_ordinal, ffmpeg=args.ffmpeg)
    final_alignment = estimate_alignment_arrays(
        final_pcm,
        external_pcm,
        ANALYSIS_SAMPLE_RATE,
        anchor_count=args.anchor_count,
    )
    output_audio = audio_stream(output_probe, args.video_audio_ordinal)
    audio_duration = float(output_audio.get("duration") or len(final_pcm) / ANALYSIS_SAMPLE_RATE)
    frame_seconds = 1.0 / source_timing["frame_rate"] if source_timing["frame_rate"] else 1.0 / 30.0
    source_hashes_after = {
        "video": sha256_file(args.video),
        "external_audio": sha256_file(args.audio),
    }
    filter_text = " ".join(command)
    checks = {
        "source_hashes_unchanged": source_hashes_after == source_hashes,
        "video_duration_unchanged": abs(output_timing["duration_seconds"] - source_timing["duration_seconds"]) <= 1e-6,
        "video_frame_count_unchanged": output_timing["frame_count"] == source_timing["frame_count"],
        "non_target_packet_hashes_match": all(item["match"] for item in non_target_hashes),
        "audio_duration_within_one_frame": abs(audio_duration - source_timing["duration_seconds"]) <= frame_seconds,
        "final_alignment_within_one_millisecond": abs(
            final_alignment["external_start_seconds"] - report["external_start_seconds"]
        ) <= 0.001,
        "full_decode_passed": decode_result.returncode == 0,
        "no_added_fades": "afade" not in filter_text and "acrossfade" not in filter_text,
        "no_shortest": "-shortest" not in command,
        "video_stream_copy_requested": "-c" in command and "copy" in command,
    }
    return {
        "output_probe": output_probe,
        "output_sha256": sha256_file(args.output),
        "source_hashes_after": source_hashes_after,
        "non_target_stream_packet_hashes": non_target_hashes,
        "final_audio_alignment": final_alignment,
        "full_decode": {
            "exit_code": decode_result.returncode,
            "stderr": decode_result.stderr.decode("utf-8", errors="replace"),
        },
        "checks": checks,
        "status": "pass" if all(checks.values()) else "fail",
    }


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--video-audio-ordinal", type=int, default=0)
    parser.add_argument("--external-audio-ordinal", type=int, default=0)
    parser.add_argument("--anchor-count", type=int, default=7)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="Analyze full recordings and write alignment.json")
    add_common_arguments(analyze)
    run = subparsers.add_parser("run", help="Analyze, replace the audio stream, and verify the output")
    add_common_arguments(run)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--audio-bitrate", default="192k")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for path in (args.video, args.audio):
        if not path.is_file():
            raise ReplacementError(f"Input does not exist: {path}")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    alignment, _, external_pcm = analyze_inputs(args)
    alignment_path = args.work_dir / "alignment.json"
    write_json(alignment_path, alignment)
    print(json.dumps(alignment, ensure_ascii=False, indent=2))
    if args.command == "analyze":
        return 0 if alignment["status"] == "pass" else 2
    if alignment["status"] != "pass":
        raise ReplacementError("Alignment requires review; output was not created")
    if args.output.exists():
        raise ReplacementError(f"Output already exists; refusing to overwrite: {args.output}")

    source_probe = ffprobe_json(args.video, args.ffprobe)
    external_probe = ffprobe_json(args.audio, args.ffprobe)
    timing = video_timing(source_probe)
    frame_seconds = 1.0 / timing["frame_rate"] if timing["frame_rate"] else 1.0 / 30.0
    external_end = alignment["external_start_seconds"] + timing["duration_seconds"]
    if external_end - alignment["external_decoded_duration_seconds"] > frame_seconds:
        raise ReplacementError("External recording does not contain the complete video interval")

    target = audio_stream(source_probe, args.video_audio_ordinal)
    external = audio_stream(external_probe, args.external_audio_ordinal)
    tags = target.get("tags") or {}
    command = build_mux_command(
        ffmpeg=args.ffmpeg,
        video_path=args.video,
        external_audio_path=args.audio,
        output_path=args.output,
        streams=source_probe["streams"],
        target_audio_stream_index=int(target["index"]),
        external_start_seconds=alignment["external_start_seconds"],
        video_duration_seconds=timing["duration_seconds"],
        audio_bitrate=args.audio_bitrate,
        sample_rate=int(external.get("sample_rate") or 48000),
        channels=int(external.get("channels") or 2),
        external_audio_ordinal=args.external_audio_ordinal,
        language=tags.get("language"),
        disposition=disposition_string(target),
    )
    source_hashes = {"video": sha256_file(args.video), "external_audio": sha256_file(args.audio)}
    audit = {
        "inputs": {
            "video": str(args.video.resolve()),
            "external_audio": str(args.audio.resolve()),
            "source_hashes_before": source_hashes,
        },
        "alignment": alignment,
        "executed_command": command,
    }
    write_json(args.work_dir / "replacement-audit.pending.json", audit)
    run_process(command)
    verification = verify_output(args, alignment, source_probe, external_pcm, source_hashes, command)
    audit["verification"] = verification
    write_json(args.work_dir / "replacement-audit.json", audit)
    if verification["status"] != "pass":
        raise ReplacementError("Replacement was created but mandatory verification failed")
    print(json.dumps({"output": str(args.output.resolve()), "status": "pass"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReplacementError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
