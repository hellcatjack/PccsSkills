from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "replace_video_audio.py"


def load_module():
    spec = importlib.util.spec_from_file_location("replace_video_audio", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def speech_like_noise(rng, sample_rate, seconds):
    samples = rng.normal(0.0, 0.15, sample_rate * seconds).astype(np.float32)
    frame = sample_rate // 10
    envelope = rng.uniform(0.15, 1.0, len(samples) // frame + 1)
    return samples * np.repeat(envelope, frame)[: len(samples)]


def test_skill_contract_is_explicit_about_sync_and_safety():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "name: replacing-video-audio-track" in text
    assert "description: Use when" in text
    for required in (
        "视频时间轴是唯一基准",
        "禁止淡入淡出",
        "多锚点",
        "时钟漂移",
        "完整解码",
        "不得覆盖",
    ):
        assert required in text


def test_alignment_finds_the_external_recording_offset():
    module = load_module()
    sample_rate = 8000
    rng = np.random.default_rng(20260807)
    external = speech_like_noise(rng, sample_rate, 120)
    expected_offset = 37.25
    start = round(expected_offset * sample_rate)
    video = external[start : start + 40 * sample_rate].copy()
    video += rng.normal(0.0, 0.002, len(video)).astype(np.float32)

    report = module.estimate_alignment_arrays(video, external, sample_rate, anchor_count=5)

    assert abs(report["external_start_seconds"] - expected_offset) < 0.002
    assert abs(report["drift_over_video_seconds"]) < 0.002
    assert report["minimum_anchor_correlation"] > 0.95


def test_alignment_ignores_subframe_external_tail_shortage():
    module = load_module()
    sample_rate = 8000
    rng = np.random.default_rng(19)
    expected_offset = 37.25
    missing_samples = 8
    full = speech_like_noise(rng, sample_rate, 78)
    external_length = round((expected_offset + 40) * sample_rate) - missing_samples
    external = full[:external_length]
    start = round(expected_offset * sample_rate)
    video = np.pad(external[start:], (0, missing_samples))

    report = module.estimate_alignment_arrays(video, external, sample_rate, anchor_count=7)

    assert abs(report["external_start_seconds"] - expected_offset) < 0.002
    assert abs(report["drift_over_video_seconds"]) < 0.002
    assert report["minimum_anchor_correlation"] > 0.95


def test_short_clip_uses_widely_distributed_anchors():
    module = load_module()
    sample_rate = 8000
    rng = np.random.default_rng(4)
    external = speech_like_noise(rng, sample_rate, 12)
    expected_offset = 3.25
    video = external[round(expected_offset * sample_rate) : round((expected_offset + 4) * sample_rate)]

    report = module.estimate_alignment_arrays(video, external, sample_rate, anchor_count=5)
    centers = [anchor["video_center_seconds"] for anchor in report["anchors"]]

    assert centers[-1] - centers[0] > 2.5
    assert abs(report["external_start_seconds"] - expected_offset) < 0.002
    assert abs(report["drift_over_video_seconds"]) < 0.002


def test_mux_command_copies_non_target_streams_and_never_adds_fades():
    module = load_module()
    streams = [
        {"index": 0, "codec_type": "video"},
        {"index": 1, "codec_type": "audio"},
        {"index": 2, "codec_type": "subtitle"},
    ]
    command = module.build_mux_command(
        ffmpeg="ffmpeg",
        video_path=Path("camera.mp4"),
        external_audio_path=Path("recorder.flac"),
        output_path=Path("camera_replaced.mp4"),
        streams=streams,
        target_audio_stream_index=1,
        external_start_seconds=12.345678,
        video_duration_seconds=60.0,
        audio_bitrate="192k",
        sample_rate=48000,
        channels=2,
    )
    joined = " ".join(command)

    assert "-c copy" in joined
    assert "-map 0:0" in joined
    assert "-map [replacement_audio]" in joined
    assert "-map 0:2" in joined
    assert "atrim=start=12.345678000:duration=60.000000000" in joined
    assert "asetpts=PTS-STARTPTS" in joined
    assert "afade" not in joined
    assert "acrossfade" not in joined
