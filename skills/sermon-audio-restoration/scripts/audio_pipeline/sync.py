from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy import signal
import soundfile as sf

from .models import LatencyResult
from .policy import (
    PolicyError,
    assert_safe_command,
    assert_safe_output,
    assert_source_unchanged,
    sha256_file,
)
from .probe import hash_stream_packets, probe_source


def _read_window(path: Path, start: int, frames: int) -> np.ndarray:
    with sf.SoundFile(path) as audio:
        audio.seek(start)
        block = audio.read(frames, dtype="float32", always_2d=True)
    return block.mean(axis=1, dtype=np.float64)


def _offset_for_window(
    reference: np.ndarray,
    candidate: np.ndarray,
    max_lag: int,
) -> tuple[int, float]:
    length = min(len(reference), len(candidate))
    reference = reference[:length] - np.mean(reference[:length])
    candidate = candidate[:length] - np.mean(candidate[:length])
    correlation = signal.correlate(candidate, reference, mode="full", method="fft")
    lags = signal.correlation_lags(len(candidate), len(reference), mode="full")
    allowed = np.abs(lags) <= max_lag
    local_correlation = correlation[allowed]
    local_lags = lags[allowed]
    best = int(np.argmax(np.abs(local_correlation)))
    denominator = float(np.linalg.norm(reference) * np.linalg.norm(candidate)) + 1e-20
    confidence = float(abs(local_correlation[best]) / denominator)
    return int(local_lags[best]), min(1.0, confidence)


def measure_latency(
    reference: Path,
    candidate: Path,
    *,
    repair_intervals: tuple[tuple[float, float], ...] = (),
    window_seconds: float = 2.0,
    max_lag_seconds: float = 0.05,
) -> LatencyResult:
    reference_info = sf.info(reference)
    candidate_info = sf.info(candidate)
    if (
        reference_info.samplerate != candidate_info.samplerate
        or reference_info.channels != candidate_info.channels
        or reference_info.frames != candidate_info.frames
    ):
        raise PolicyError("Latency sources must share sample rate, channels, and frames")

    sample_rate = reference_info.samplerate
    total_frames = reference_info.frames
    window_frames = min(total_frames, max(1024, round(window_seconds * sample_rate)))
    max_lag = max(1, round(max_lag_seconds * sample_rate))
    centers = [int(total_frames * fraction) for fraction in (0.05, 0.25, 0.5, 0.75, 0.95)]
    centers.extend(round(((start + end) / 2.0) * sample_rate) for start, end in repair_intervals)

    offsets: list[int] = []
    confidences: list[float] = []
    positions: list[float] = []
    for center in centers:
        start = max(0, min(total_frames - window_frames, center - window_frames // 2))
        reference_window = _read_window(reference, start, window_frames)
        candidate_window = _read_window(candidate, start, window_frames)
        offset, confidence = _offset_for_window(reference_window, candidate_window, max_lag)
        offsets.append(offset)
        confidences.append(confidence)
        positions.append(start / max(1, total_frames))

    global_offset = int(round(float(np.median(offsets))))
    drift_slope = (
        float(np.polyfit(np.asarray(positions), np.asarray(offsets), 1)[0])
        if len(set(positions)) >= 2
        else 0.0
    )
    return LatencyResult(
        global_offset_samples=global_offset,
        anchor_offsets_samples=tuple(offsets),
        drift_slope_samples=drift_slope,
        confidence=float(np.mean(confidences)),
    )


def assert_zero_latency(result: LatencyResult) -> None:
    if result.global_offset_samples != 0:
        raise PolicyError(
            f"Processing latency is {result.global_offset_samples} samples, expected zero"
        )
    if any(offset != 0 for offset in result.anchor_offsets_samples):
        raise PolicyError(
            f"One or more latency anchors are non-zero: {result.anchor_offsets_samples}"
        )
    if abs(result.drift_slope_samples) > 0.01:
        raise PolicyError(
            f"Cumulative drift slope is non-zero: {result.drift_slope_samples} samples"
        )


def _probe_json(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_chapters",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads(completed.stdout)


def _disposition_expression(disposition: dict[str, int]) -> str:
    enabled = [name for name, value in disposition.items() if int(value) == 1]
    return "+".join(enabled) if enabled else "0"


def _choose_aac_makeup_gain(
    *,
    measured_lufs: float,
    measured_true_peak_dbtp: float,
    target_lufs: float,
    target_true_peak_dbtp: float,
) -> float:
    desired_lufs = target_lufs - 0.25
    loudness_gain = desired_lufs - measured_lufs
    peak_gain_limit = target_true_peak_dbtp - 0.1 - measured_true_peak_dbtp
    makeup_gain = min(loudness_gain, peak_gain_limit)
    predicted_lufs = measured_lufs + makeup_gain
    predicted_true_peak = measured_true_peak_dbtp + makeup_gain
    if abs(predicted_lufs - target_lufs) > 0.5:
        raise PolicyError(
            "AAC calibration cannot meet the loudness target without violating "
            f"the peak margin: predicted {predicted_lufs:.2f} LUFS"
        )
    if predicted_true_peak > target_true_peak_dbtp:
        raise PolicyError(
            "AAC calibration would exceed the true-peak target: "
            f"predicted {predicted_true_peak:.2f} dBTP"
        )
    return makeup_gain


def _aac_precondition_filter(
    final_true_peak_dbtp: float,
    *,
    makeup_gain_db: float = 0.0,
) -> str:
    peak_limit = 10 ** ((final_true_peak_dbtp - 1.0) / 20.0)
    output_gain = 10 ** (makeup_gain_db / 20.0)
    return (
        f"alimiter=limit={peak_limit:.9f}:attack=5:release=50:"
        f"level=false:level_out={output_gain:.9f}:latency=true"
    )


def _calibrate_aac_makeup(
    master: Path,
    output: Path,
    *,
    sample_rate: int,
    channels: int,
    target_lufs: float,
    target_true_peak_dbtp: float,
) -> float:
    calibration = output.with_name(f"{output.stem}.aac-calibration.m4a")
    assert_safe_output(master, calibration, protected_paths=(output,))
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(master),
        "-map",
        "0:a:0",
        "-af",
        _aac_precondition_filter(target_true_peak_dbtp),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        str(calibration),
    ]
    assert_safe_command(command)
    try:
        subprocess.run(command, check=True)
        from .verify import _media_loudness

        measured_lufs, measured_true_peak = _media_loudness(calibration, 0)
        if measured_lufs is None or measured_true_peak is None:
            raise PolicyError("Could not measure the AAC calibration encode")
        return _choose_aac_makeup_gain(
            measured_lufs=measured_lufs,
            measured_true_peak_dbtp=measured_true_peak,
            target_lufs=target_lufs,
            target_true_peak_dbtp=target_true_peak_dbtp,
        )
    finally:
        calibration.unlink(missing_ok=True)


def remux_replacement_audio(
    source: Path,
    master: Path,
    stream_index: int,
    output: Path,
    final_integrated_lufs: float = -16.0,
    final_true_peak_dbtp: float = -1.5,
) -> Path:
    source = source.resolve()
    master = master.resolve()
    output = output.resolve()
    source_hash = sha256_file(source)
    assert_safe_output(source, output, protected_paths=(master,))

    media = _probe_json(source)
    streams = media.get("streams", [])
    selected = next(
        (item for item in streams if int(item["index"]) == int(stream_index)),
        None,
    )
    if selected is None or selected.get("codec_type") != "audio":
        raise PolicyError(f"Selected stream is not an audio stream: {stream_index}")

    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    audio_ordinal = next(
        index
        for index, item in enumerate(audio_streams)
        if int(item["index"]) == int(stream_index)
    )
    source_manifest = probe_source(source, audio_stream=audio_ordinal)
    master_info = sf.info(master)
    if (
        master_info.frames != source_manifest.decoded_sample_count
        or master_info.samplerate != source_manifest.sample_rate
        or master_info.channels != source_manifest.channels
    ):
        raise PolicyError("Replacement master does not match the selected source timeline")

    aac_makeup_gain = _calibrate_aac_makeup(
        master,
        output,
        sample_rate=source_manifest.sample_rate,
        channels=source_manifest.channels,
        target_lufs=final_integrated_lufs,
        target_true_peak_dbtp=final_true_peak_dbtp,
    )

    chapters = media.get("chapters", [])
    chapter_data_indexes = {
        int(stream["index"])
        for stream in streams
        if chapters
        and stream.get("codec_type") == "data"
        and stream.get("codec_name") == "bin_data"
    }

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(source),
        "-itsoffset",
        f"{source_manifest.start_time:.12f}",
        "-i",
        str(master),
    ]
    for stream in streams:
        index = int(stream["index"])
        if index in chapter_data_indexes:
            continue
        command.extend(["-map", "1:a:0" if index == stream_index else f"0:{index}"])
    chapter_source = "0" if chapters else "-1"
    command.extend(
        [
            "-map_metadata",
            "0",
            "-map_chapters",
            chapter_source,
            "-c",
            "copy",
            f"-c:a:{audio_ordinal}",
            "aac",
            f"-filter:a:{audio_ordinal}",
            _aac_precondition_filter(
                final_true_peak_dbtp,
                makeup_gain_db=aac_makeup_gain,
            ),
            f"-b:a:{audio_ordinal}",
            "192k",
            f"-ar:a:{audio_ordinal}",
            str(source_manifest.sample_rate),
            f"-ac:a:{audio_ordinal}",
            str(source_manifest.channels),
        ]
    )
    for key, value in source_manifest.tags.items():
        command.extend([f"-metadata:s:a:{audio_ordinal}", f"{key}={value}"])
    command.extend(
        [
            f"-disposition:a:{audio_ordinal}",
            _disposition_expression(source_manifest.disposition),
            str(output),
        ]
    )
    assert_safe_command(command)
    subprocess.run(command, check=True)

    output_media = _probe_json(output)
    output_streams = output_media.get("streams", [])
    if len(output_streams) != len(streams):
        raise PolicyError("Remux changed the number of streams")
    for stream in streams:
        index = int(stream["index"])
        if index == stream_index:
            continue
        before = hash_stream_packets(source, index)
        after = hash_stream_packets(output, index)
        if before != after:
            raise PolicyError(f"Non-target stream {index} changed during remux")

    output_selected = output_streams[stream_index]
    output_start = float(output_selected.get("start_time", 0.0))
    if abs(output_start - source_manifest.start_time) > 1.0 / source_manifest.sample_rate:
        raise PolicyError(
            f"Replacement audio start changed: {source_manifest.start_time} -> {output_start}"
        )
    assert_source_unchanged(source, source_hash)
    return output
