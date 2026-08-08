#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _reason(item: dict[str, Any], label: str, errors: list[str]) -> None:
    if not str(item.get("reason", "")).strip():
        errors.append(f"{label} requires a nonempty semantic reason")


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    duration = _number(plan.get("duration"))
    fps = _number(plan.get("fps"))
    expected_frames = _number(plan.get("expectedFrames"))
    if duration is None or duration <= 0:
        errors.append("duration must be positive")
        return errors
    if fps != 30:
        errors.append("fps must be exactly 30")
    if expected_frames != round(duration * 30):
        errors.append("expectedFrames must equal round(duration * 30)")

    transitions = plan.get("transitions", {})
    intro_transition = _number(transitions.get("intro"))
    ordinary_transition = _number(transitions.get("ordinary"))
    ending_transition = _number(transitions.get("endingCover"))
    for name, value in (
        ("intro", intro_transition),
        ("ordinary", ordinary_transition),
        ("endingCover", ending_transition),
    ):
        if value is None or value <= 0:
            errors.append(f"transitions.{name} must be positive")

    intro = plan.get("intro", {})
    full_until = _number(intro.get("fullUntil"))
    split_complete = _number(intro.get("splitComplete"))
    if full_until is None or full_until < 0:
        errors.append("intro.fullUntil must be nonnegative")
    if split_complete is None or split_complete > duration:
        errors.append("intro.splitComplete must be within duration")
    if (
        full_until is not None
        and split_complete is not None
        and intro_transition is not None
        and not math.isclose(split_complete - full_until, intro_transition, abs_tol=1e-6)
    ):
        errors.append("intro transition duration must match splitComplete - fullUntil")

    layout = plan.get("layout", {})
    canvas_width = _number(layout.get("canvasWidth"))
    canvas_height = _number(layout.get("canvasHeight"))
    ppt_width = _number(layout.get("pptSplitWidth"))
    ppt_height = _number(layout.get("pptSplitHeight"))
    ppt_y = _number(layout.get("pptSplitY"))
    pastor_width = _number(layout.get("pastorPanelWidth"))
    if canvas_width != 1920 or canvas_height != 1080:
        errors.append("canvas must be 1920x1080")
    if None not in (ppt_width, pastor_width, canvas_width) and not math.isclose(
        ppt_width + pastor_width, canvas_width, abs_tol=1e-6
    ):
        errors.append("PPT and pastor widths must fill the canvas width")
    if (
        ppt_height is None
        or ppt_y is None
        or canvas_height is None
        or ppt_height <= 0
        or ppt_y < 0
        or ppt_y + ppt_height > canvas_height
    ):
        errors.append("PPT split viewport must fit within the canvas")

    crop = layout.get("pastorCrop", {})
    crop_values = {name: _number(crop.get(name)) for name in ("x", "y", "width", "height")}
    source_width = _number(layout.get("sourceVideoWidth"))
    source_height = _number(layout.get("sourceVideoHeight"))
    if any(crop_values[name] is None for name in crop_values) or any(
        crop_values[name] <= 0 for name in ("width", "height") if crop_values[name] is not None
    ):
        errors.append("pastorCrop must contain a positive rectangle")
    elif (
        source_width is None
        or source_height is None
        or crop_values["x"] < 0
        or crop_values["y"] < 0
        or crop_values["x"] + crop_values["width"] > source_width
        or crop_values["y"] + crop_values["height"] > source_height
    ):
        errors.append("pastorCrop must stay inside the source video")

    segments = plan.get("pptSegments")
    if not isinstance(segments, list) or not segments:
        errors.append("pptSegments must be a nonempty list")
    else:
        previous_end = 0.0
        for index, segment in enumerate(segments):
            label = f"pptSegments[{index}]"
            _reason(segment, label, errors)
            source_start = _number(segment.get("sourceStart"))
            source_end = _number(segment.get("sourceEnd"))
            target_start = _number(segment.get("targetStart"))
            target_end = _number(segment.get("targetEnd"))
            if None in (source_start, source_end) or source_end <= source_start:
                errors.append(f"{label} source range must be positive")
            if None in (target_start, target_end) or target_end <= target_start:
                errors.append(f"{label} target range must be positive")
                continue
            if not math.isclose(target_start, previous_end, abs_tol=1e-6):
                errors.append("pptSegments target ranges must be contiguous")
            previous_end = target_end
            if not isinstance(segment.get("slide"), int) or segment["slide"] < 1:
                errors.append(f"{label}.slide must be a positive integer")
        if not math.isclose(previous_end, duration, abs_tol=1e-6):
            errors.append("pptSegments must cover the complete duration")

    blocks = plan.get("fullScreenBlocks", [])
    if not isinstance(blocks, list):
        errors.append("fullScreenBlocks must be a list")
        blocks = []
    previous_end = -math.inf
    for index, block in enumerate(blocks):
        label = f"fullScreenBlocks[{index}]"
        _reason(block, label, errors)
        start = _number(block.get("start"))
        end = _number(block.get("end"))
        if None in (start, end) or start < 0 or end > duration or end <= start:
            errors.append(f"{label} must stay inside duration")
            continue
        if start < previous_end:
            errors.append("fullScreenBlocks must not overlap")
        if ordinary_transition is not None and end - start <= 2 * ordinary_transition:
            errors.append(f"{label} is too short for both transitions")
        previous_end = end

    ending = plan.get("endingCover", {})
    ending_start = _number(ending.get("start"))
    ending_complete = _number(ending.get("complete"))
    ending_end = _number(ending.get("end"))
    if ending.get("mode") != "left-cover-right-pastor":
        errors.append("endingCover.mode must be left-cover-right-pastor")
    if not isinstance(ending.get("coverSlide"), int) or ending.get("coverSlide", 0) < 1:
        errors.append("endingCover.coverSlide must be a positive integer")
    if (
        None in (ending_start, ending_complete, ending_end)
        or ending_start < 0
        or ending_complete > ending_end
        or not math.isclose(ending_end, duration, abs_tol=1e-6)
    ):
        errors.append("endingCover must run from a valid boundary through duration")
    elif ending_transition is not None and not math.isclose(
        ending_complete - ending_start, ending_transition, abs_tol=1e-6
    ):
        errors.append("endingCover transition duration must match complete - start")
    if blocks and ending_start is not None:
        last_end = _number(blocks[-1].get("end"))
        if last_end is not None and last_end > ending_start:
            errors.append("fullScreenBlocks must end before endingCover starts")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a single-camera sermon composition plan")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    plan = load_plan(args.plan)
    errors = validate_plan(plan)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
