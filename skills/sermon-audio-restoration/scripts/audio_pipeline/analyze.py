from __future__ import annotations

from collections import defaultdict
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Iterable

import numpy as np
from scipy import ndimage, signal
import soundfile as sf

from .models import AnalysisReport, ChannelMetric, IssueFinding, SourceManifest


def _db(value: float, floor: float = -120.0) -> float:
    if value <= 1e-20:
        return floor
    return float(10.0 * math.log10(value))


def _amplitude_db(value: float, floor: float = -120.0) -> float:
    if value <= 1e-12:
        return floor
    return float(20.0 * math.log10(value))


def _merge_intervals(
    intervals: Iterable[tuple[float, float]], gap: float = 0.25
) -> tuple[tuple[float, float], ...]:
    ordered = sorted((max(0.0, a), max(0.0, b)) for a, b in intervals if b > a)
    merged: list[list[float]] = []
    for start, end in ordered:
        if merged and start <= merged[-1][1] + gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return tuple((start, end) for start, end in merged)


def _energy_vad(path: Path) -> tuple[tuple[float, float], ...]:
    with sf.SoundFile(path) as audio:
        sample_rate = audio.samplerate
        frame_size = max(1, int(sample_rate * 0.5))
        levels: list[float] = []
        for block in audio.blocks(blocksize=frame_size, dtype="float32", always_2d=True):
            mono = block.mean(axis=1, dtype=np.float64)
            rms = float(np.sqrt(np.mean(np.square(mono)) + 1e-20))
            levels.append(_amplitude_db(rms))

    if not levels:
        return ()
    values = np.asarray(levels)
    noise = float(np.percentile(values, 15))
    peak = float(np.percentile(values, 90))
    threshold = min(peak - 12.0, noise + 10.0)
    active = values >= threshold
    intervals = []
    for index, enabled in enumerate(active):
        if enabled:
            intervals.append((index * 0.5, min((index + 1) * 0.5, len(values) * 0.5)))
    return _merge_intervals(intervals, gap=0.6)


def _read_mono_resampled(path: Path, target_rate: int = 16000):
    import torch

    chunks: list[np.ndarray] = []
    with sf.SoundFile(path) as audio:
        source_rate = audio.samplerate
        block_size = max(1, source_rate * 60)
        divisor = math.gcd(source_rate, target_rate)
        up = target_rate // divisor
        down = source_rate // divisor
        for block in audio.blocks(
            blocksize=block_size,
            dtype="float32",
            always_2d=True,
        ):
            mono = block.mean(axis=1, dtype=np.float64).astype(np.float32)
            if source_rate != target_rate:
                mono = signal.resample_poly(mono, up, down).astype(np.float32)
            chunks.append(mono)
    waveform = np.concatenate(chunks) if chunks else np.empty(0, dtype=np.float32)
    return torch.from_numpy(waveform)


def detect_speech_intervals(path: Path) -> tuple[tuple[tuple[float, float], ...], str]:
    if importlib.util.find_spec("silero_vad") is not None:
        try:
            from silero_vad import get_speech_timestamps, load_silero_vad

            model = load_silero_vad()
            waveform = _read_mono_resampled(path, target_rate=16000)
            stamps = get_speech_timestamps(
                waveform,
                model,
                sampling_rate=16000,
                return_seconds=True,
            )
            intervals = tuple(
                (float(stamp["start"]), float(stamp["end"])) for stamp in stamps
            )
            return intervals, "silero-vad"
        except Exception:
            pass
    return _energy_vad(path), "energy-fallback"


def _parse_loudnorm(path: Path) -> tuple[float | None, float | None, float | None]:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json",
        "-f",
        "null",
        "-",
    ]
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
        return None, None, None
    data = json.loads(blocks[-1])

    def parsed(name: str) -> float | None:
        value = str(data.get(name, "-inf"))
        try:
            number = float(value)
        except ValueError:
            return None
        return number if math.isfinite(number) else None

    return parsed("input_i"), parsed("input_tp"), parsed("input_lra")


def _short_term_loudness(path: Path) -> tuple[tuple[float, float], ...]:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "verbose",
        "-i",
        str(path),
        "-filter_complex",
        "ebur128=metadata=1",
        "-f",
        "null",
        "-",
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    pattern = re.compile(
        r"t:\s*([-+0-9.eE]+).*?S:\s*(-?(?:\d+(?:\.\d*)?|\.\d+))",
        re.IGNORECASE,
    )
    points: list[tuple[float, float]] = []
    for match in pattern.finditer(completed.stderr):
        timestamp = float(match.group(1))
        loudness = float(match.group(2))
        if loudness > -70.0:
            points.append((timestamp, loudness))
    return tuple(points)


def _group_loudness_windows(
    points: tuple[tuple[float, float], ...],
    duration: float,
    window_seconds: float,
) -> tuple[dict[str, float], ...]:
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    windows: list[dict[str, float]] = []
    count = max(1, int(math.ceil(duration / window_seconds)))
    for index in range(count):
        start = index * window_seconds
        end = min(duration, start + window_seconds)
        values = [value for timestamp, value in points if start <= timestamp < end]
        if values:
            windows.append(
                {"start": start, "end": end, "lufs": float(np.median(values))}
            )
    return tuple(windows)


def _speech_loudness_percentiles(
    points: tuple[tuple[float, float], ...],
    intervals: tuple[tuple[float, float], ...],
) -> tuple[float | None, float | None, float | None]:
    values = [
        value
        for timestamp, value in points
        if any(start <= timestamp <= end for start, end in intervals)
    ]
    if not values:
        return None, None, None
    p10 = float(np.percentile(values, 10))
    p90 = float(np.percentile(values, 90))
    return p10, p90, p90 - p10


def _boolean_regions(
    mask: np.ndarray,
    frame_seconds: float,
    offset_seconds: float,
) -> list[tuple[float, float]]:
    padded = np.pad(mask.astype(np.int8), (1, 1))
    changes = np.diff(padded)
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return [
        (
            offset_seconds + start * frame_seconds,
            offset_seconds + end * frame_seconds,
        )
        for start, end in zip(starts, ends)
    ]


def _voiced_harmonic_support(
    excess_db: np.ndarray,
    frequencies: np.ndarray,
    candidate_index: int,
    active_columns: list[int],
) -> tuple[float | None, int, int]:
    if not active_columns or len(frequencies) < 2:
        return None, 0, 0

    profile = np.median(excess_db[:, active_columns], axis=1)
    candidate_hz = float(frequencies[candidate_index])
    frequency_step = float(frequencies[1] - frequencies[0])
    tolerance_hz = max(2.0 * frequency_step, 10.0)

    for divisor in range(2, 13):
        fundamental_hz = candidate_hz / divisor
        if not 80.0 <= fundamental_hz <= 300.0:
            continue
        supported = 0
        total = divisor - 1
        for harmonic in range(1, divisor):
            target_hz = harmonic * fundamental_hz
            neighborhood = np.abs(frequencies - target_hz) <= tolerance_hz
            if np.any(neighborhood) and float(np.max(profile[neighborhood])) >= 8.0:
                supported += 1
        if supported >= 2 and supported / total >= 0.5:
            return fundamental_hz, supported, total

    return None, 0, 0


def _block_findings(
    block: np.ndarray,
    sample_rate: int,
    offset_seconds: float,
) -> list[IssueFinding]:
    findings: list[IssueFinding] = []
    mono = block.mean(axis=1, dtype=np.float64)
    peak = np.max(np.abs(block), axis=1)

    clip_frame = max(1, int(sample_rate * 0.01))
    clip_count = int(math.ceil(len(peak) / clip_frame))
    padded_peak = np.pad(peak, (0, clip_count * clip_frame - len(peak)))
    clip_ratio = (padded_peak.reshape(clip_count, clip_frame) >= 0.999).mean(axis=1)
    clip_mask = clip_ratio >= 0.02
    clip_regions = _boolean_regions(clip_mask, clip_frame / sample_rate, offset_seconds)
    for start, end in clip_regions:
        findings.append(
            IssueFinding(
                kind="clipping",
                start=start,
                end=end,
                confidence=min(1.0, 0.75 + (end - start)),
                metrics={"peak_ratio": float(np.max(clip_ratio))},
                reason="flat-top sample density exceeds the conservative threshold",
            )
        )

    difference = np.max(np.abs(np.diff(block, axis=0)), axis=1)
    median = float(np.median(difference))
    mad = float(np.median(np.abs(difference - median))) + 1e-12
    click_threshold = max(0.5, median + 20.0 * mad)
    click_indexes = np.flatnonzero(difference >= click_threshold)
    for index in click_indexes:
        timestamp = offset_seconds + index / sample_rate
        if any(start - 0.01 <= timestamp <= end + 0.01 for start, end in clip_regions):
            continue
        findings.append(
            IssueFinding(
                kind="click",
                start=max(offset_seconds, timestamp - 0.002),
                end=timestamp + 0.002,
                confidence=min(1.0, difference[index] / max(click_threshold, 1e-9)),
                metrics={"derivative": float(difference[index])},
                reason="isolated inter-sample jump exceeds robust transient threshold",
            )
        )

    if len(mono) >= 16384:
        stft_size = 16384
        hop_size = stft_size // 4
        frequencies, times, spectrum = signal.stft(
            mono,
            fs=sample_rate,
            nperseg=stft_size,
            noverlap=stft_size - hop_size,
            boundary=None,
            padded=False,
        )
        magnitude_db = 20.0 * np.log10(np.abs(spectrum) + 1e-12)
        frequency_step = float(frequencies[1] - frequencies[0])
        median_bins = max(31, int(round(300.0 / frequency_step)))
        if median_bins % 2 == 0:
            median_bins += 1
        local_median = ndimage.median_filter(
            magnitude_db,
            size=(median_bins, 1),
            mode="nearest",
        )
        excess = magnitude_db - local_median
        valid = (frequencies >= 500.0) & (frequencies <= 8000.0)
        by_bin: dict[int, list[int]] = defaultdict(list)
        valid_indexes = np.flatnonzero(valid)
        for time_index in range(excess.shape[1]):
            peaks, properties = signal.find_peaks(
                excess[valid, time_index],
                height=15.0,
                distance=max(3, int(round(30.0 / frequency_step))),
            )
            for local_peak in peaks:
                frequency_index = int(valid_indexes[local_peak])
                if float(magnitude_db[frequency_index, time_index]) < -70.0:
                    continue
                by_bin[frequency_index].append(time_index)

        hop_seconds = hop_size / sample_rate
        for frequency_index, indexes in by_bin.items():
            if len(indexes) < 3:
                continue
            mask = np.zeros(excess.shape[1], dtype=bool)
            mask[indexes] = True
            for start, end in _boolean_regions(mask, hop_seconds, offset_seconds):
                if end - start < 0.5:
                    continue
                active_columns = indexes[
                    np.searchsorted(indexes, int((start - offset_seconds) / hop_seconds), side="left") :
                    np.searchsorted(indexes, int((end - offset_seconds) / hop_seconds), side="right")
                ]
                prominence = float(
                    np.max(excess[frequency_index, active_columns])
                    if active_columns
                    else 15.0
                )
                bandwidths = []
                for column in active_columns:
                    width_bins = signal.peak_widths(
                        excess[:, column],
                        [frequency_index],
                        rel_height=0.5,
                    )[0][0]
                    width_hz = float(width_bins * frequency_step)
                    if math.isfinite(width_hz) and width_hz > 0.0:
                        bandwidths.append(width_hz)
                bandwidth_hz = float(np.median(bandwidths)) if bandwidths else math.inf
                frequency_hz = float(frequencies[frequency_index])
                quality_factor = (
                    frequency_hz / bandwidth_hz if math.isfinite(bandwidth_hz) else 0.0
                )
                harmonic_f0, harmonic_count, harmonic_total = _voiced_harmonic_support(
                    excess,
                    frequencies,
                    frequency_index,
                    active_columns,
                )
                metrics = {
                    "frequency_hz": frequency_hz,
                    "prominence_db": prominence,
                    "absolute_level_dbfs": float(
                        np.max(magnitude_db[frequency_index, active_columns])
                    ),
                    "bandwidth_hz": bandwidth_hz,
                    "quality_factor": quality_factor,
                    "harmonic_support_count": float(harmonic_count),
                    "harmonic_support_total": float(harmonic_total),
                }
                if harmonic_f0 is not None:
                    metrics["harmonic_f0_hz"] = harmonic_f0

                if quality_factor < 30.0 or harmonic_f0 is not None:
                    findings.append(
                        IssueFinding(
                            kind="tonal_candidate",
                            start=start,
                            end=end,
                            confidence=min(0.75, 0.4 + prominence / 200.0),
                            metrics=metrics,
                            reason=(
                                "tonal energy is broad or supported by a voiced harmonic series; "
                                "retain for AI review without automatic notch repair"
                            ),
                        )
                    )
                    continue
                findings.append(
                    IssueFinding(
                        kind="howl",
                        start=start,
                        end=end,
                        confidence=min(0.99, 0.65 + prominence / 100.0),
                        metrics=metrics,
                        reason=(
                            "persistent high-Q narrowband peak exceeds its local spectral "
                            "neighborhood without voiced-harmonic support"
                        ),
                    )
                )
    return findings


def _merge_findings(findings: list[IssueFinding]) -> tuple[IssueFinding, ...]:
    ordered = sorted(findings, key=lambda item: (item.kind, item.start, item.end))
    merged: list[IssueFinding] = []
    for item in ordered:
        if not merged or merged[-1].kind != item.kind:
            merged.append(item)
            continue
        previous = merged[-1]
        frequency_matches = True
        if item.kind == "howl":
            frequency_matches = abs(
                previous.metrics.get("frequency_hz", 0.0)
                - item.metrics.get("frequency_hz", 0.0)
            ) < 30.0
        if frequency_matches and item.start <= previous.end + 0.15:
            metrics = dict(previous.metrics)
            for key, value in item.metrics.items():
                metrics[key] = max(metrics.get(key, value), value)
            merged[-1] = IssueFinding(
                kind=previous.kind,
                start=previous.start,
                end=max(previous.end, item.end),
                confidence=max(previous.confidence, item.confidence),
                metrics=metrics,
                reason=previous.reason,
            )
        else:
            merged.append(item)
    return tuple(merged)


def _spectral_and_channel_analysis(
    path: Path,
    sample_rate: int,
    channels: int,
) -> tuple[tuple[IssueFinding, ...], tuple[ChannelMetric, ...]]:
    block_frames = sample_rate * 30
    overlap_frames = sample_rate * 2
    findings: list[IssueFinding] = []
    square_sum = np.zeros(channels, dtype=np.float64)
    sample_count = 0
    psd_sum: np.ndarray | None = None
    psd_count = 0
    frequencies: np.ndarray | None = None

    with sf.SoundFile(path) as audio:
        step = block_frames - overlap_frames
        start_frame = 0
        while start_frame < len(audio):
            audio.seek(start_frame)
            block = audio.read(block_frames, dtype="float32", always_2d=True)
            if len(block) == 0:
                break
            findings.extend(_block_findings(block, sample_rate, start_frame / sample_rate))

            central_start = 0 if start_frame == 0 else overlap_frames // 2
            central_end = len(block)
            if start_frame + len(block) < len(audio):
                central_end -= overlap_frames // 2
            central = block[central_start:central_end]
            square_sum += np.sum(np.square(central, dtype=np.float64), axis=0)
            sample_count += len(central)

            nperseg = min(65536, len(central))
            if nperseg >= 4096:
                current_frequencies, current_psd = signal.welch(
                    central,
                    fs=sample_rate,
                    nperseg=nperseg,
                    axis=0,
                )
                if frequencies is None:
                    frequencies = current_frequencies
                    psd_sum = current_psd
                elif len(current_frequencies) == len(frequencies):
                    assert psd_sum is not None
                    psd_sum += current_psd
                psd_count += 1

            if len(block) < block_frames:
                break
            start_frame += step

    if frequencies is None or psd_sum is None or psd_count == 0:
        average_psd = np.ones((1, channels), dtype=np.float64) * 1e-20
        frequencies = np.zeros(1)
    else:
        average_psd = psd_sum / psd_count

    def band_power(channel: int, low: float, high: float) -> float:
        mask = (frequencies >= low) & (frequencies < high)
        if not np.any(mask):
            return 1e-20
        return float(np.trapezoid(average_psd[mask, channel], frequencies[mask]))

    metrics: list[ChannelMetric] = []
    for channel in range(channels):
        rms = math.sqrt(float(square_sum[channel]) / max(1, sample_count))
        voice_power = band_power(channel, 100.0, 8000.0)
        presence_power = band_power(channel, 1000.0, 5000.0)
        noise_power = band_power(channel, 9000.0, min(20000.0, sample_rate / 2.0))
        presence_ratio = presence_power / max(voice_power, 1e-20)
        clarity = _db(voice_power / max(noise_power, 1e-20)) + presence_ratio
        metrics.append(
            ChannelMetric(
                channel=channel,
                rms_dbfs=_amplitude_db(rms),
                noise_dbfs=_db(noise_power),
                presence_ratio=float(presence_ratio),
                clarity_score=float(clarity),
            )
        )

    if len(frequencies) > 1:
        mono_psd = average_psd.mean(axis=1)

        def prominence_at(target: float) -> float:
            center = int(np.argmin(np.abs(frequencies - target)))
            neighborhood = (
                (frequencies >= target - 15.0)
                & (frequencies <= target + 15.0)
                & (np.abs(frequencies - target) >= 3.0)
            )
            reference = float(np.median(mono_psd[neighborhood])) if np.any(neighborhood) else 1e-20
            return _db(float(mono_psd[center]) / max(reference, 1e-20))

        hum_60 = prominence_at(60.0)
        hum_120 = prominence_at(120.0)
        if min(hum_60, hum_120) >= 8.0:
            duration = sample_count / sample_rate
            findings.append(
                IssueFinding(
                    kind="hum",
                    start=0.0,
                    end=duration,
                    confidence=min(0.99, 0.6 + min(hum_60, hum_120) / 100.0),
                    metrics={
                        "base_frequency_hz": 60.0,
                        "fundamental_prominence_db": hum_60,
                        "harmonic_prominence_db": hum_120,
                    },
                    reason="60 Hz fundamental and harmonic remain above neighboring spectrum",
                )
            )

    return _merge_findings(findings), tuple(metrics)


def analyze_audio(
    baseline: Path,
    manifest: SourceManifest,
    *,
    window_seconds: float = 60.0,
) -> AnalysisReport:
    baseline = baseline.resolve()
    integrated, true_peak, loudness_range = _parse_loudnorm(baseline)
    short_term = _short_term_loudness(baseline)
    speech_intervals, vad_backend = detect_speech_intervals(baseline)
    window_loudness = _group_loudness_windows(
        short_term,
        manifest.duration_seconds,
        window_seconds,
    )
    speech_p10, speech_p90, speech_spread = _speech_loudness_percentiles(
        short_term,
        speech_intervals,
    )
    findings, channel_metrics = _spectral_and_channel_analysis(
        baseline,
        manifest.sample_rate,
        manifest.channels,
    )

    capabilities = {
        "ffmpeg": True,
        "silero_vad": importlib.util.find_spec("silero_vad") is not None,
        "deepfilternet": importlib.util.find_spec("df") is not None,
        "nara_wpe": importlib.util.find_spec("nara_wpe") is not None,
    }
    warnings: list[str] = []
    if vad_backend == "energy-fallback":
        warnings.append(
            "Speech activity used the energy fallback; AI review is required before dynamic leveling."
        )
    if speech_spread is None:
        warnings.append("Active-speech loudness spread could not be measured reliably.")
    if any(finding.kind == "tonal_candidate" for finding in findings):
        warnings.append(
            "Broad or voiced-harmonic tonal candidates were retained for AI review; "
            "automatic notch repair is disabled for them."
        )

    return AnalysisReport(
        source_sha256=manifest.source_sha256,
        integrated_lufs=integrated,
        true_peak_dbtp=true_peak,
        loudness_range_lu=loudness_range,
        window_loudness=window_loudness,
        vad_backend=vad_backend,
        active_speech_intervals=speech_intervals,
        speech_p10_lufs=speech_p10,
        speech_p90_lufs=speech_p90,
        speech_spread_lu=speech_spread,
        findings=findings,
        channel_metrics=channel_metrics,
        capabilities=capabilities,
        warnings=tuple(warnings),
    )
