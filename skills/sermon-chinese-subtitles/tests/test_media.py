from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import load_pipeline_module


def _synthetic_video(path: Path) -> None:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is unavailable")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x180:r=30:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        check=True,
    )


def test_probe_and_create_run_freeze_explicit_video(tmp_path) -> None:
    module = load_pipeline_module("media")
    assert module is not None, "subtitle_pipeline.media implementation is missing"

    video = tmp_path / "指定讲道.mp4"
    pptx = tmp_path / "讲道资料.pptx"
    _synthetic_video(video)
    pptx.write_bytes(b"pptx-fixture")

    probe = module.probe_media(video)
    run = module.create_run(video, pptx=pptx)

    assert len(probe["video_streams"]) == 1
    assert len(probe["audio_streams"]) == 1
    assert 0.95 <= probe["format_duration"] <= 1.05
    assert Path(run["run_dir"]).is_dir()
    assert Path(run["run_dir"]).is_relative_to(tmp_path / "_work" / "subtitles")
    assert Path(run["manifest_path"]).is_file()
    assert run["manifest"]["selected_audio"]["ordinal"] == 0
    assert {item["role"] for item in run["manifest"]["inputs"]} == {"specified_video", "source_pptx"}
    assert all(len(item["sha256"]) == 64 for item in run["manifest"]["inputs"])


def test_formal_output_allocation_never_overwrites(tmp_path) -> None:
    module = load_pipeline_module("media")
    assert module is not None, "subtitle_pipeline.media implementation is missing"

    video = tmp_path / "讲道.mp4"
    video.write_bytes(b"video")
    first = module.allocate_output_path(video)
    first.write_text("existing", encoding="utf-8")
    second = module.allocate_output_path(video)
    second.write_text("existing-v2", encoding="utf-8")
    third = module.allocate_output_path(video)

    assert first.name == "讲道_YouTube简体中文字幕_高精度校订版.srt"
    assert second.name == "讲道_YouTube简体中文字幕_高精度校订版_v2.srt"
    assert third.name == "讲道_YouTube简体中文字幕_高精度校订版_v3.srt"


def test_multiple_audio_tracks_require_explicit_ordinal(monkeypatch, tmp_path) -> None:
    module = load_pipeline_module("media")
    assert module is not None, "subtitle_pipeline.media implementation is missing"
    video = tmp_path / "multi.mp4"
    video.write_bytes(b"fixture")
    fake_probe = {
        "path": str(video.resolve()),
        "format_duration": 10.0,
        "streams": [],
        "video_streams": [{"index": 0, "codec_type": "video"}],
        "audio_streams": [
            {"index": 1, "codec_type": "audio", "codec_name": "aac"},
            {"index": 2, "codec_type": "audio", "codec_name": "aac"},
        ],
    }
    monkeypatch.setattr(module, "probe_media", lambda _: fake_probe)

    with pytest.raises(ValueError, match="multiple audio tracks"):
        module.create_run(video, work_root=tmp_path / "work")

    run = module.create_run(video, audio_stream=1, work_root=tmp_path / "work")
    assert run["manifest"]["selected_audio"]["ordinal"] == 1
    assert run["manifest"]["selected_audio"]["stream_index"] == 2
