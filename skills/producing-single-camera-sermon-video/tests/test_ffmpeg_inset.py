"""Render real FFmpeg output: catch geometry, opacity and ending regressions."""
import json
import shutil
import subprocess

import pytest

from test_landscape_workflow import inset_plan
from build_dynamic_filter import build_filter


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg and ffprobe are required for render integration")
@pytest.mark.parametrize("processed", [False, True])
def test_rendered_panels_focus_and_ending_have_correct_pixels(tmp_path, processed):
    plan = inset_plan()
    plan.update(duration=8, expectedFrames=240)
    plan["transitions"] = {"intro": .4, "ordinary": .4, "endingCover": .4}
    plan["intro"] = {"fullUntil": 1, "splitComplete": 1.4,
                     "cameraForbiddenBefore": 1, "coverUntil": 1, "coverSlide": 1}
    plan["pptSegments"] = [{"slide": 1, "sourceStart": 0, "sourceEnd": 8,
                            "targetStart": 0, "targetEnd": 8, "reason": "synthetic slide"}]
    plan["fullScreenBlocks"] = [{"start": 2, "end": 4, "reason": "synthetic focus"}]
    plan["endingCover"].update(start=6, complete=6.4, end=8)
    size = "3840x2160"
    if processed:
        plan["cameraInput"] = {"mode": "processed-panel", "width": 600, "height": 684}
        size = "600x684"
    graph = tmp_path / "graph.txt"
    graph.write_text(build_filter(plan), encoding="utf-8")
    output = tmp_path / "render.mp4"
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-filter_complex_threads", "2"]
    for color, dimensions in (("blue", "1920x1080"), ("red", size), ("gold", "1920x1080")):
        command += ["-f", "lavfi", "-i", f"color=c={color}:s={dimensions}:r=30:d=8"]
    command += ["-filter_complex_script", str(graph), "-map", "[outv]", "-an",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16",
                "-threads", "2", str(output)]
    result = subprocess.run(command, capture_output=True, timeout=90)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams",
                            "-of", "json", str(output)], capture_output=True, check=True)
    streams = json.loads(probe.stdout)["streams"]
    assert len(streams) == 1
    assert streams[0]["nb_read_frames"] == "240"
    assert streams[0]["r_frame_rate"] == "30/1"
    assert streams[0]["width"] == 1920 and streams[0]["height"] == 1080
    result = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output),
        "-vf", "select='eq(n,15)+eq(n,54)+eq(n,84)+eq(n,135)+eq(n,210)'",
        "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
        capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    frame_bytes = 1920*1080*3
    assert len(result.stdout) == 5*frame_bytes

    def pixel(frame, x, y):
        start = frame*frame_bytes + (y*1920+x)*3
        return tuple(result.stdout[start:start+3])

    def close(actual, expected):
        assert all(abs(a-b) <= 5 for a, b in zip(actual, expected)), (actual, expected)

    for frame in (0, 2):  # protected opening and stable full-screen PPT
        close(pixel(frame, 1500, 500), (0, 0, 255))
        close(pixel(frame, 10, 10), (0, 0, 255))
    for frame in (1, 3):  # split and restored split
        close(pixel(frame, 500, 500), (0, 0, 255))
        close(pixel(frame, 1500, 500), (255, 0, 0))
        close(pixel(frame, 10, 10), (23, 27, 31))
    close(pixel(4, 500, 500), (255, 215, 0))
    close(pixel(4, 1500, 500), (255, 0, 0))
