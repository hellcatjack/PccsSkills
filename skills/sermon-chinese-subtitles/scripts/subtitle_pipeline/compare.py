from __future__ import annotations

import hashlib
import math
import re
import statistics
from pathlib import Path

from .srt import parse_srt


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = int(round((len(ordered) - 1) * fraction))
    return ordered[position]


def _stats(values: list[float]) -> dict:
    if not values:
        return {"median": 0.0, "p95_abs": 0.0, "min": 0.0, "max": 0.0}
    return {
        "median": round(statistics.median(values), 3),
        "p95_abs": round(_percentile([abs(value) for value in values], 0.95), 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
    }


def _text_hash(cues: list[dict]) -> str:
    text = "".join(re.sub(r"\s+", "", cue["text"]) for cue in cues)
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def compare_srt(
    before_path: Path,
    after_path: Path,
    *,
    allow_resegmentation: bool = False,
) -> dict:
    before = parse_srt(Path(before_path).read_bytes())
    after = parse_srt(Path(after_path).read_bytes())
    report = {
        "before": str(Path(before_path).resolve()),
        "after": str(Path(after_path).resolve()),
        "before_cues": len(before),
        "after_cues": len(after),
        "before_text_sha256": _text_hash(before),
        "after_text_sha256": _text_hash(after),
    }
    if len(before) != len(after):
        if not allow_resegmentation:
            raise ValueError(
                "cannot compare cue timing index-by-index when cue counts differ; "
                "use allow_resegmentation=True"
            )
        return {
            **report,
            "resegmented": True,
            "text_changed": None,
            "start_changed": None,
            "end_changed": None,
            "start_shift_seconds": None,
            "end_shift_seconds": None,
            "over_one_second": [],
        }

    start_shifts: list[float] = []
    end_shifts: list[float] = []
    text_changed = 0
    start_changed = 0
    end_changed = 0
    over_one_second: list[dict] = []
    for index, (old, new) in enumerate(zip(before, after), start=1):
        start_shift = round(float(new["start"]) - float(old["start"]), 3)
        end_shift = round(float(new["end"]) - float(old["end"]), 3)
        start_shifts.append(start_shift)
        end_shifts.append(end_shift)
        if not math.isclose(start_shift, 0.0, abs_tol=0.0005):
            start_changed += 1
        if not math.isclose(end_shift, 0.0, abs_tol=0.0005):
            end_changed += 1
        if re.sub(r"\s+", "", old["text"]) != re.sub(r"\s+", "", new["text"]):
            text_changed += 1
        if abs(start_shift) > 1.0 or abs(end_shift) > 1.0:
            over_one_second.append(
                {
                    "cue": index,
                    "start_shift": start_shift,
                    "end_shift": end_shift,
                    "before_text": old["text"],
                    "after_text": new["text"],
                }
            )
    return {
        **report,
        "resegmented": False,
        "text_changed": text_changed,
        "start_changed": start_changed,
        "end_changed": end_changed,
        "start_shift_seconds": _stats(start_shifts),
        "end_shift_seconds": _stats(end_shifts),
        "over_one_second": over_one_second,
    }
