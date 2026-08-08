from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np
import soundfile as sf

from .policy import PolicyError


@dataclass(frozen=True)
class EdgeGainMeasurement:
    start_change_db: float
    end_change_db: float
    start_windows: int
    end_windows: int


def _rms_db(samples: np.ndarray) -> float:
    rms = math.sqrt(float(np.mean(np.square(samples, dtype=np.float64))) + 1e-30)
    return 20.0 * math.log10(max(rms, 1e-12))


def _edge_gain_change(
    reference: sf.SoundFile,
    candidate: sf.SoundFile,
    starts: range,
    window_frames: int,
    activity_floor_dbfs: float,
) -> tuple[float, int]:
    times: list[float] = []
    gains: list[float] = []
    for start in starts:
        frames = min(window_frames, reference.frames - start)
        if frames <= 0:
            continue
        reference.seek(start)
        candidate.seek(start)
        before = reference.read(frames, dtype="float32", always_2d=True)
        after = candidate.read(frames, dtype="float32", always_2d=True)
        before_db = _rms_db(before)
        if before_db < activity_floor_dbfs:
            continue
        times.append((start + frames / 2.0) / reference.samplerate)
        gains.append(_rms_db(after) - before_db)

    if len(gains) < 4:
        return 0.0, len(gains)
    positions = np.asarray(times, dtype=np.float64)
    positions -= positions[0]
    values = np.asarray(gains, dtype=np.float64)
    slope = float(np.polyfit(positions, values, 1)[0])
    return slope * float(positions[-1]), len(gains)


def measure_edge_gain(
    reference_path: Path,
    candidate_path: Path,
    *,
    edge_seconds: float = 15.0,
    window_seconds: float = 0.5,
    activity_floor_dbfs: float = -70.0,
) -> EdgeGainMeasurement:
    with sf.SoundFile(reference_path) as reference, sf.SoundFile(candidate_path) as candidate:
        if (
            reference.frames != candidate.frames
            or reference.samplerate != candidate.samplerate
            or reference.channels != candidate.channels
        ):
            raise PolicyError("Fade verification requires identical audio timelines")
        window_frames = max(1, round(window_seconds * reference.samplerate))
        edge_frames = min(reference.frames, round(edge_seconds * reference.samplerate))
        head_starts = range(0, edge_frames, window_frames)
        tail_start = max(0, reference.frames - edge_frames)
        tail_starts = range(tail_start, reference.frames, window_frames)
        start_change, start_windows = _edge_gain_change(
            reference,
            candidate,
            head_starts,
            window_frames,
            activity_floor_dbfs,
        )
        end_change, end_windows = _edge_gain_change(
            reference,
            candidate,
            tail_starts,
            window_frames,
            activity_floor_dbfs,
        )
    return EdgeGainMeasurement(
        start_change_db=start_change,
        end_change_db=end_change,
        start_windows=start_windows,
        end_windows=end_windows,
    )


def assert_no_added_fades(
    reference_path: Path,
    candidate_path: Path,
    *,
    max_edge_change_db: float = 5.0,
) -> EdgeGainMeasurement:
    result = measure_edge_gain(reference_path, candidate_path)
    failures = []
    if abs(result.start_change_db) > max_edge_change_db:
        failures.append(f"start={result.start_change_db:.2f} dB")
    if abs(result.end_change_db) > max_edge_change_db:
        failures.append(f"end={result.end_change_db:.2f} dB")
    if failures:
        raise PolicyError(
            "Processing added a fade-like edge gain trend: " + ", ".join(failures)
        )
    return result
