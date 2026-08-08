from __future__ import annotations

import pytest

from conftest import load_pipeline_module


CONTEXT = {
    "sermon_title": "测试讲道",
    "speaker": "测试牧师",
    "scripture": ["尼希米记4:1-20"],
    "sermon_points": ["隔绝阻拦的声音", "祷告信靠神的带领"],
    "proper_names": ["尼希米", "参巴拉", "PCCS"],
    "hotwords": ["耶路撒冷", "城墙"],
}


def test_transcribe_profiles_match_proven_full_and_regional_settings() -> None:
    module = load_pipeline_module("transcribe")
    assert module is not None, "subtitle_pipeline.transcribe implementation is missing"

    primary = module.build_transcribe_options("primary", CONTEXT)
    precision = module.build_transcribe_options("precision", CONTEXT)
    regional = module.build_transcribe_options("regional", CONTEXT)

    assert primary["beam_size"] == 5
    assert primary["vad_filter"] is True
    assert primary["vad_parameters"] == {
        "min_silence_duration_ms": 500,
        "max_speech_duration_s": 30,
        "speech_pad_ms": 300,
    }
    assert precision["beam_size"] == 8
    assert precision["vad_filter"] is True
    assert precision["vad_parameters"] == {
        "min_silence_duration_ms": 350,
        "max_speech_duration_s": 20,
        "speech_pad_ms": 250,
    }
    assert regional["beam_size"] == 10
    assert regional["vad_filter"] is False
    assert "vad_parameters" not in regional


def test_prompt_and_hotwords_come_only_from_current_context() -> None:
    module = load_pipeline_module("transcribe")
    assert module is not None, "subtitle_pipeline.transcribe implementation is missing"

    options = module.build_transcribe_options("precision", CONTEXT)

    for term in ["测试讲道", "测试牧师", "尼希米记4:1-20", "隔绝阻拦的声音", "尼希米", "PCCS", "城墙"]:
        assert term in options["initial_prompt"] or term in options["hotwords"]
    assert "于成龙" not in options["initial_prompt"]
    assert "帕麦斯顿" not in options["hotwords"]


def test_regional_windows_must_be_absolute_positive_intervals() -> None:
    module = load_pipeline_module("transcribe")
    assert module is not None, "subtitle_pipeline.transcribe implementation is missing"

    assert module.validate_regions([{"id": "r1", "start": 10.0, "end": 20.0, "reason": "经文漏段"}]) == [
        {"id": "r1", "start": 10.0, "end": 20.0, "reason": "经文漏段"}
    ]
    with pytest.raises(ValueError, match="positive absolute interval"):
        module.validate_regions([{"id": "bad", "start": 20.0, "end": 10.0, "reason": "错误"}])


def test_extracted_audio_timestamps_restore_container_audio_start_offset() -> None:
    module = load_pipeline_module("transcribe")
    assert module is not None, "subtitle_pipeline.transcribe implementation is missing"

    class Word:
        start = 0.10
        end = 0.40
        word = "测试"
        probability = 0.9

    class Segment:
        id = 1
        start = 0.10
        end = 0.40
        text = "测试"
        avg_logprob = -0.1
        no_speech_prob = 0.01
        words = [Word()]

    items = module.collect_segments([Segment()], timestamp_offset=0.75)

    assert items[0]["start"] == 0.85
    assert items[0]["end"] == 1.15
    assert items[0]["words"][0]["start"] == 0.85
    assert items[0]["words"][0]["end"] == 1.15
