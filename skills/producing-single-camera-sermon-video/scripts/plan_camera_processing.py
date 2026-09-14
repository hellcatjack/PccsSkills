#!/usr/bin/env python3
"""Plan expensive denoising on visible panel frames; does not process media."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_composition_plan import load_plan, validate_plan


def _frame(seconds: float) -> int:
    value = float(seconds) * 30
    nearest = round(value)
    if abs(value - nearest) > 1e-5:
        raise ValueError("camera visibility boundaries must be on the 30 fps frame grid")
    return nearest


def plan_processing(plan: dict, context_frames: int) -> dict:
    errors = validate_plan(plan)
    if errors:
        raise ValueError("Invalid composition plan: " + "; ".join(errors))
    if type(context_frames) is not int or context_frames < 0:
        raise ValueError("context_frames must be a nonnegative integer")
    count = int(plan["expectedFrames"])
    # Half-open frame intervals. At the precise first/last ramp frame, focus=1
    # still means zero camera opacity; only fully hidden frames may be omitted.
    hidden = [(0, min(count, _frame(plan["intro"]["fullUntil"]) + 1))]
    ramp = _frame(plan["transitions"]["ordinary"])
    _frame(plan["transitions"]["intro"])
    for block in plan["fullScreenBlocks"]:
        start, end = _frame(block["start"]), _frame(block["end"])
        hidden.append((start + ramp, min(count, end - ramp + 1)))
    visible = []
    cursor = 0
    for start, end in sorted(hidden):
        if start > cursor:
            visible.append([cursor, start])
        cursor = max(cursor, end)
    if cursor < count:
        visible.append([cursor, count])
    chunks = []
    for start, end in visible:
        decode_start, decode_end = max(0, start-context_frames), min(count, end+context_frames)
        if chunks and decode_start <= chunks[-1]["decodeEnd"]:
            chunks[-1]["decodeEnd"] = max(chunks[-1]["decodeEnd"], decode_end)
            chunks[-1]["outputRanges"].append([start, end])
        else:
            chunks.append({"decodeStart": decode_start, "decodeEnd": decode_end,
                           "outputRanges": [[start, end]]})
    return {
        "fps": 30, "expectedFrames": count, "intervalConvention": "[start,end)",
        "contextFrames": context_frames, "visibleRanges": visible, "chunks": chunks,
        "visibleFrames": sum(b-a for a, b in visible),
        "decodeFrames": sum(c["decodeEnd"]-c["decodeStart"] for c in chunks),
        "assembly": "Retain absolute frame indexes; fill only omitted hidden frames. Never concatenate visible cores without their original gaps.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--context-frames", type=int, required=True,
                        help="Combined temporal radius of every chained model/filter")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = plan_processing(load_plan(args.plan), args.context_frames)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("expectedFrames", "visibleFrames", "decodeFrames")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
