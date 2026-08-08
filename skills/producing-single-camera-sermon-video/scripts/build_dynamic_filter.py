#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_composition_plan import load_plan, validate_plan


def smoothstep(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3.0 - 2.0 * progress)


def focus_at(plan: dict[str, Any], seconds: float) -> float:
    intro = plan["intro"]
    if seconds < intro["fullUntil"]:
        return 1.0
    if seconds < intro["splitComplete"]:
        progress = (seconds - intro["fullUntil"]) / plan["transitions"]["intro"]
        return 1.0 - smoothstep(progress)

    transition = plan["transitions"]["ordinary"]
    for block in plan["fullScreenBlocks"]:
        start, end = block["start"], block["end"]
        if start <= seconds < start + transition:
            return smoothstep((seconds - start) / transition)
        if start + transition <= seconds < end - transition:
            return 1.0
        if end - transition <= seconds <= end:
            return 1.0 - smoothstep((seconds - (end - transition)) / transition)
    return 0.0


def _number(value: float | int) -> str:
    return f"{float(value):.9f}".rstrip("0").rstrip(".")


def _smoothstep_expression(progress: str) -> str:
    return f"(({progress})*({progress})*(3-2*({progress})))"


def build_focus_expression(plan: dict[str, Any], variable: str = "t") -> str:
    transition = plan["transitions"]["ordinary"]
    pulses: list[str] = []
    for block in plan["fullScreenBlocks"]:
        start = _number(block["start"])
        ramp_up_end = _number(block["start"] + transition)
        ramp_down_start = _number(block["end"] - transition)
        end = _number(block["end"])
        ramp_up = _smoothstep_expression(f"({variable}-{start})/{_number(transition)}")
        ramp_down = _smoothstep_expression(
            f"({variable}-{ramp_down_start})/{_number(transition)}"
        )
        pulses.append(
            f"if(between({variable},{start},{ramp_up_end}),{ramp_up},"
            f"if(between({variable},{ramp_up_end},{ramp_down_start}),1,"
            f"if(between({variable},{ramp_down_start},{end}),1-{ramp_down},0)))"
        )
    pulse_sum = "+".join(f"({pulse})" for pulse in pulses) or "0"
    intro_start = _number(plan["intro"]["fullUntil"])
    intro_end = _number(plan["intro"]["splitComplete"])
    intro_duration = _number(plan["transitions"]["intro"])
    intro_progress = f"({variable}-{intro_start})/{intro_duration}"
    intro_ramp = _smoothstep_expression(intro_progress)
    return (
        f"if(lt({variable},{intro_start}),1,"
        f"if(lt({variable},{intro_end}),1-{intro_ramp},{pulse_sum}))"
    )


def _ppt_segment_lines(plan: dict[str, Any]) -> list[str]:
    segments = plan["pptSegments"]
    count = len(segments)
    source_labels = "".join(f"[s{index}]" for index in range(count))
    lines = [f"[0:v]split={count}{source_labels}"]
    for index, segment in enumerate(segments):
        source_duration = segment["sourceEnd"] - segment["sourceStart"]
        target_duration = segment["targetEnd"] - segment["targetStart"]
        multiplier = target_duration / source_duration
        lines.append(
            f"[s{index}]trim=start={_number(segment['sourceStart'])}:"
            f"end={_number(segment['sourceEnd'])},"
            f"setpts=(PTS-STARTPTS)*{multiplier:.12f}[p{index}]"
        )
    concat_inputs = "".join(f"[p{index}]" for index in range(count))
    lines.append(
        f"{concat_inputs}concat=n={count}:v=1:a=0,"
        "fps=fps=30:round=near,setpts=N/(30*TB),format=yuv420p,"
        "split=2[pbgsrc][pfgsrc]"
    )
    return lines


def build_filter(plan: dict[str, Any]) -> str:
    errors = validate_plan(plan)
    if errors:
        raise ValueError("Invalid composition plan: " + "; ".join(errors))

    duration = _number(plan["duration"])
    frames = int(plan["expectedFrames"])
    layout = plan["layout"]
    canvas_width = int(layout["canvasWidth"])
    canvas_height = int(layout["canvasHeight"])
    ppt_width = int(layout["pptSplitWidth"])
    ppt_height = int(layout["pptSplitHeight"])
    ppt_y = int(layout["pptSplitY"])
    pastor_width = int(layout["pastorPanelWidth"])
    crop = layout["pastorCrop"]
    focus_time = build_focus_expression(plan, "t")
    focus_frame = build_focus_expression(plan, "N/30")
    width_expression = f"trunc(({ppt_width}+{pastor_width}*({focus_time}))/2)*2"
    ending = plan["endingCover"]

    lines = _ppt_segment_lines(plan)
    lines.extend(
        [
            f"[pbgsrc]scale=160:90,gblur=sigma=5,scale={canvas_width}:{canvas_height},"
            f"crop={ppt_width}:{canvas_height},eq=brightness=-0.10[pbg]",
            f"color=c=black:s={canvas_width}x{canvas_height}:r=30:d={duration}[canvas]",
            "[canvas][pbg]overlay=x=0:y=0:shortest=1[leftbase]",
            f"[1:v]trim=start=0:end={duration},setpts=PTS-STARTPTS,"
            "tpad=stop_mode=clone:stop_duration=0.1,"
            f"crop={int(crop['width'])}:{int(crop['height'])}:"
            f"{int(crop['x'])}:{int(crop['y'])},"
            f"scale={pastor_width}:{canvas_height}:flags=lanczos,"
            f"fps=30,trim=end={duration},format=rgb24[pastorrgb]",
            f"color=c=white:s=2x2:r=30:d={duration},format=gray,"
            f"geq=lum='255*(1-({focus_frame}))',"
            f"scale={pastor_width}:{canvas_height}:flags=neighbor[pmask]",
            "[pastorrgb][pmask]alphamerge[pastor]",
            f"[leftbase][pastor]overlay=x={ppt_width}:y=0:shortest=1:eof_action=pass[base]",
            f"[pfgsrc]scale=w='{width_expression}':h=-2:eval=frame:flags=lanczos,"
            f"format=rgba,pad={canvas_width}:{canvas_height}:x=0:y='(oh-ih)/2':"
            "color=black@0:eval=frame[pfg]",
            "[base][pfg]overlay=x=0:y=0:shortest=1[dynamic]",
            f"[2:v]trim=start=0:end={duration},setpts=PTS-STARTPTS,"
            "fps=30,split=2[coverbgsrc][coverfgsrc]",
            f"[coverbgsrc]scale=160:90,gblur=sigma=5,scale={canvas_width}:{canvas_height},"
            f"crop={ppt_width}:{canvas_height},eq=brightness=-0.10,format=rgba[coverbg]",
            f"[coverfgsrc]scale={ppt_width}:{ppt_height}:flags=lanczos,format=rgba[coverfg]",
            f"[coverbg][coverfg]overlay=x=0:y={ppt_y}:shortest=1,format=rgba,"
            f"fade=t=in:st={_number(ending['start'])}:"
            f"d={_number(plan['transitions']['endingCover'])}:alpha=1[coverleft]",
            "[dynamic][coverleft]overlay=x=0:y=0:shortest=1,"
            "tpad=stop_mode=clone:stop_duration=0.1,"
            f"fps=fps=30:round=near,trim=end_frame={frames},"
            "setpts=N/(30*TB),format=yuv420p[outv]",
        ]
    )
    return ";\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a dynamic sermon-video FFmpeg filter graph")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    graph = build_filter(load_plan(args.plan))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(graph, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
