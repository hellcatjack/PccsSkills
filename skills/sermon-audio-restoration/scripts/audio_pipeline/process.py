from __future__ import annotations

import json
import math
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

import numpy as np
import soundfile as sf

from .integrity import assert_no_added_fades
from .models import ProcessResult, ProcessingPlan, ProcessingStep
from .policy import PolicyError, assert_safe_command, assert_safe_output


class ProcessingError(RuntimeError):
    pass


class DependencyUnavailable(ProcessingError):
    pass


def _number(value: Any) -> str:
    return f"{float(value):.8g}"


def _timeline_enable(start: float, end: float) -> str:
    return f"enable='between(t\\,{_number(start)}\\,{_number(end)})'"


def build_filter_for_step(step: ProcessingStep) -> str:
    parameters = step.parameters
    if step.kind == "declick":
        return "adeclick"
    if step.kind == "declip":
        return "adeclip"
    if step.kind == "notch":
        return ":".join(
            [
                f"equalizer=f={_number(parameters['frequency_hz'])}",
                "width_type=h",
                f"width={_number(parameters.get('width_hz', 12.0))}",
                f"g={_number(parameters.get('gain_db', -12.0))}",
                _timeline_enable(float(parameters["start"]), float(parameters["end"])),
            ]
        )
    if step.kind == "dehum":
        base = float(parameters.get("base_frequency_hz", 60.0))
        harmonics = int(parameters.get("harmonics", 4))
        width = float(parameters.get("width_hz", 3.0))
        return ",".join(
            f"equalizer=f={_number(base * index)}:width_type=h:width={_number(width)}:g=-15"
            for index in range(1, harmonics + 1)
        )
    if step.kind == "plosive-control":
        return ":".join(
            [
                f"highpass=f={_number(parameters.get('cutoff_hz', 100.0))}",
                "p=2",
                _timeline_enable(float(parameters["start"]), float(parameters["end"])),
            ]
        )
    if step.kind == "denoise-light":
        return (
            f"afftdn=nr={_number(parameters.get('reduction_db', 6.0))}:"
            f"nf={_number(parameters.get('noise_floor_db', -50.0))}:tn=1"
        )
    if step.kind == "level":
        max_gain_db = float(parameters.get("max_gain_db", 6.0))
        max_gain_linear = max(1.0, 10.0 ** (max_gain_db / 20.0))
        link = "true" if parameters.get("couple_channels", True) else "false"
        return (
            f"speechnorm=e={_number(max_gain_linear)}:"
            f"r={_number(parameters.get('raise_per_half_cycle', 0.00001))}:"
            f"l={link}:p=0.95"
        )
    raise ProcessingError(f"Unsupported FFmpeg processing step: {step.kind}")


def validate_stage_sample_count(path: Path, *, expected_frames: int) -> int:
    actual = int(sf.info(path).frames)
    if actual != expected_frames:
        raise PolicyError(
            f"Processing stage changed sample count: expected {expected_frames}, found {actual}"
        )
    return actual


def _run_ffmpeg_filter(
    input_path: Path,
    output_path: Path,
    filter_expression: str,
    sample_rate: int,
    channels: int,
) -> tuple[str, ...]:
    assert_safe_output(input_path, output_path)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(input_path),
        "-map",
        "0:a:0",
        "-af",
        filter_expression,
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        "-c:a",
        "pcm_f32le",
        str(output_path),
    ]
    assert_safe_command(command)
    subprocess.run(command, check=True)
    return tuple(command)


def _loudnorm_measure(input_path: Path, parameters: dict[str, Any]) -> dict[str, float]:
    target = float(parameters.get("integrated_lufs", -16.0))
    peak = float(parameters.get("true_peak_dbtp", -1.5))
    lra = float(parameters.get("lra", 7.0))
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(input_path),
        "-af",
        f"loudnorm=I={target}:TP={peak}:LRA={lra}:print_format=json",
        "-f",
        "null",
        "-",
    ]
    assert_safe_command(command)
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    blocks = re.findall(r"\{\s*\"input_i\".*?\}", completed.stderr, re.DOTALL)
    if not blocks:
        raise ProcessingError("FFmpeg loudnorm did not return measurement JSON")
    raw = json.loads(blocks[-1])
    names = {
        "input_i": "measured_I",
        "input_tp": "measured_TP",
        "input_lra": "measured_LRA",
        "input_thresh": "measured_thresh",
        "target_offset": "offset",
    }
    measured: dict[str, float] = {}
    for source_name, target_name in names.items():
        value = float(raw[source_name])
        if not math.isfinite(value):
            raise ProcessingError(f"Non-finite loudnorm measurement: {source_name}")
        measured[target_name] = value
    return measured


def _run_loudnorm(
    input_path: Path,
    output_path: Path,
    parameters: dict[str, Any],
    sample_rate: int,
    channels: int,
) -> tuple[str, ...]:
    measured = _loudnorm_measure(input_path, parameters)
    target = float(parameters.get("integrated_lufs", -16.0))
    peak = float(parameters.get("true_peak_dbtp", -1.5))
    lra = float(parameters.get("lra", 7.0))
    filter_expression = (
        f"loudnorm=I={target}:TP={peak}:LRA={lra}:"
        f"measured_I={measured['measured_I']}:"
        f"measured_TP={measured['measured_TP']}:"
        f"measured_LRA={measured['measured_LRA']}:"
        f"measured_thresh={measured['measured_thresh']}:"
        f"offset={measured['offset']}:linear=true:print_format=summary"
    )
    return _run_ffmpeg_filter(
        input_path,
        output_path,
        filter_expression,
        sample_rate,
        channels,
    )


def _run_deepfilternet(input_path: Path, output_path: Path) -> tuple[str, ...]:
    executable = shutil.which("deep-filter") or shutil.which("deepFilter")
    if executable is None:
        raise DependencyUnavailable("DeepFilterNet CLI is unavailable")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    before = set(output_path.parent.glob("*.wav"))
    command = [
        executable,
        "--compensate-delay",
        "--output-dir",
        str(output_path.parent),
        str(input_path),
    ]
    subprocess.run(command, check=True)
    candidates = [path for path in output_path.parent.glob("*.wav") if path not in before]
    if len(candidates) != 1:
        raise ProcessingError("DeepFilterNet output could not be identified safely")
    shutil.move(str(candidates[0]), output_path)
    return tuple(command)


def _wpe_block(samples: np.ndarray, sample_rate: int, parameters: dict[str, Any]) -> np.ndarray:
    try:
        from nara_wpe.utils import istft, stft
        from nara_wpe.wpe import wpe
    except ImportError as error:
        raise DependencyUnavailable("NARA-WPE is unavailable") from error

    if samples.ndim != 2 or samples.shape[1] < 2:
        raise ProcessingError("NARA-WPE requires at least two channels")
    original_frames = len(samples)
    fft_size = 1024
    shift = 256
    observed = samples.T.astype(np.float64, copy=False)
    spectrum = stft(
        observed,
        size=fft_size,
        shift=shift,
        fading=True,
        pad=True,
        symmetric_window=False,
    )
    cutoff_hz = float(parameters.get("cutoff_hz", 10000.0))
    cutoff_bin = min(
        spectrum.shape[-1],
        int(math.floor(cutoff_hz * fft_size / sample_rate)) + 1,
    )
    low_band = spectrum[:, :, :cutoff_bin].transpose(2, 0, 1)
    estimated = wpe(
        low_band,
        taps=int(parameters.get("taps", 10)),
        delay=int(parameters.get("delay", 3)),
        iterations=int(parameters.get("iterations", 3)),
        statistics_mode="valid",
    )
    enhanced_spectrum = spectrum.copy()
    enhanced_spectrum[:, :, :cutoff_bin] = estimated.transpose(1, 2, 0)
    enhanced = istft(
        enhanced_spectrum,
        size=fft_size,
        shift=shift,
        fading=True,
        symmetric_window=False,
    ).T
    if len(enhanced) < original_frames:
        raise ProcessingError("NARA-WPE returned fewer samples than its input")
    return np.nan_to_num(enhanced[:original_frames].astype(np.float32), copy=False)


def _cosine_crossfade(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if left.shape != right.shape:
        raise ProcessingError("WPE overlap shapes differ")
    phase = np.linspace(0.0, math.pi / 2.0, len(left), dtype=np.float64)
    fade_out = np.square(np.cos(phase))[:, None]
    fade_in = np.square(np.sin(phase))[:, None]
    return (left * fade_out + right * fade_in).astype(np.float32)


def _run_wpe(
    input_path: Path,
    output_path: Path,
    parameters: dict[str, Any],
) -> tuple[str, ...]:
    info = sf.info(input_path)
    block_frames = round(float(parameters.get("block_seconds", 30.0)) * info.samplerate)
    overlap_frames = round(2.0 * info.samplerate)
    if not (0 < overlap_frames < block_frames):
        raise ProcessingError("Invalid WPE overlap")
    hop_frames = block_frames - overlap_frames
    expected_frames = info.frames
    previous: np.ndarray | None = None
    written = 0

    with sf.SoundFile(input_path) as source, sf.SoundFile(
        output_path,
        mode="w",
        samplerate=info.samplerate,
        channels=info.channels,
        subtype="FLOAT",
    ) as destination:
        source_position = 0
        while source_position < expected_frames:
            source.seek(source_position)
            block = source.read(
                min(block_frames, expected_frames - source_position),
                dtype="float32",
                always_2d=True,
            )
            if len(block) == 0:
                break
            current = _wpe_block(block, info.samplerate, parameters)
            if previous is None:
                previous = current
            else:
                overlap = min(overlap_frames, len(previous), len(current))
                destination.write(previous[:-overlap])
                destination.write(_cosine_crossfade(previous[-overlap:], current[:overlap]))
                written += len(previous)
                previous = current[overlap:]
            source_position += hop_frames
        if previous is not None:
            remaining = expected_frames - written
            destination.write(previous[:remaining])
            written += min(len(previous), remaining)
    if written != expected_frames:
        raise ProcessingError(
            f"WPE wrote {written} frames instead of {expected_frames}; output was not padded or cropped"
        )
    return (
        "nara-wpe",
        f"taps={int(parameters.get('taps', 10))}",
        f"delay={int(parameters.get('delay', 3))}",
        f"iterations={int(parameters.get('iterations', 3))}",
    )


def _write_ab_samples(
    baseline: Path,
    processed: Path,
    intervals: tuple[tuple[float, float], ...],
    work_dir: Path,
) -> tuple[str, ...]:
    paths: list[str] = []
    before_info = sf.info(baseline)
    after_info = sf.info(processed)
    if (
        before_info.frames != after_info.frames
        or before_info.samplerate != after_info.samplerate
        or before_info.channels != after_info.channels
    ):
        raise PolicyError("A/B sources do not share an identical timeline")

    for index, (start, end) in enumerate(intervals, start=1):
        first_frame = max(0, round(start * before_info.samplerate))
        last_frame = min(before_info.frames, round(end * before_info.samplerate))
        frame_count = last_frame - first_frame
        if frame_count <= 0:
            continue
        for label, source_path in (("before", baseline), ("after", processed)):
            with sf.SoundFile(source_path) as source:
                source.seek(first_frame)
                audio = source.read(frame_count, dtype="float32", always_2d=True)
            output = work_dir / f"ab_{index:03d}_{label}.wav"
            sf.write(output, audio, before_info.samplerate, subtype="FLOAT")
            paths.append(str(output))
    return tuple(paths)


def execute_plan(
    baseline: Path,
    plan: ProcessingPlan,
    work_dir: Path,
) -> ProcessResult:
    baseline = baseline.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    info = sf.info(baseline)
    expected_frames = int(info.frames)
    current = baseline
    stage_paths: list[str] = []
    stage_counts: list[int] = []
    commands: list[tuple[str, ...]] = []

    for index, processing_step in enumerate(plan.steps, start=1):
        stage = work_dir / f"stage_{index:02d}_{processing_step.kind}.wav"
        if processing_step.tool == "ffmpeg":
            if processing_step.kind == "loudnorm":
                command = _run_loudnorm(
                    current,
                    stage,
                    processing_step.parameters,
                    info.samplerate,
                    info.channels,
                )
            else:
                filter_expression = build_filter_for_step(processing_step)
                command = _run_ffmpeg_filter(
                    current,
                    stage,
                    filter_expression,
                    info.samplerate,
                    info.channels,
                )
        elif processing_step.tool == "deepfilternet":
            command = _run_deepfilternet(current, stage)
        elif processing_step.tool == "nara-wpe":
            command = _run_wpe(current, stage, processing_step.parameters)
        elif processing_step.tool == "auphonic-free":
            raise ProcessingError(
                "Auphonic-free steps must pass through the guarded cloud adapter"
            )
        else:
            raise ProcessingError(f"Unsupported processing tool: {processing_step.tool}")

        count = validate_stage_sample_count(stage, expected_frames=expected_frames)
        assert_no_added_fades(current, stage)
        commands.append(command)
        stage_paths.append(str(stage))
        stage_counts.append(count)
        current = stage

    master = work_dir / "processed_master.wav"
    assert_safe_output(baseline, master)
    shutil.copy2(current, master)
    master_count = validate_stage_sample_count(master, expected_frames=expected_frames)
    if not stage_counts:
        stage_counts.append(master_count)

    ab_paths = _write_ab_samples(
        baseline,
        master,
        plan.review_intervals if plan.requires_ab_review else (),
        work_dir,
    )
    return ProcessResult(
        master_path=str(master),
        stage_paths=tuple(stage_paths),
        commands=tuple(commands),
        stage_sample_counts=tuple(stage_counts),
        ab_sample_paths=ab_paths,
    )
