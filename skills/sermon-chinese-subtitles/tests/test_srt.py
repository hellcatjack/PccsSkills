from __future__ import annotations

import pytest

from conftest import load_pipeline_module


def test_round_trip_preserves_millisecond_timing() -> None:
    module = load_pipeline_module("srt")
    assert module is not None, "subtitle_pipeline.srt implementation is missing"

    cues = [
        {
            "id": "c1",
            "start": 65.4326,
            "end": 67.2,
            "text": "我们的神必为我们争战。",
        }
    ]
    rendered = module.render_srt(cues)
    parsed = module.parse_srt(rendered)

    assert rendered.startswith("1\n00:01:05,433 --> 00:01:07,200\n")
    assert parsed[0]["start"] == 65.433
    assert parsed[0]["end"] == 67.2
    assert parsed[0]["text"] == "我们的神必为我们争战。"


def test_wrap_rejects_more_than_two_eighteen_character_lines() -> None:
    module = load_pipeline_module("srt")
    assert module is not None, "subtitle_pipeline.srt implementation is missing"

    with pytest.raises(ValueError, match="two 18-character lines"):
        module.wrap_text("尼希米" * 13)


def test_parser_rejects_nonsequential_indices() -> None:
    module = load_pipeline_module("srt")
    assert module is not None, "subtitle_pipeline.srt implementation is missing"

    malformed = "2\n00:00:00,100 --> 00:00:01,000\n测试\n"
    with pytest.raises(ValueError, match="nonsequential"):
        module.parse_srt(malformed)


def test_wrap_uses_caller_protected_terms() -> None:
    module = load_pipeline_module("srt")
    assert module is not None, "subtitle_pipeline.srt implementation is missing"

    wrapped = module.wrap_text(
        "弟兄姐妹要一同记念亚达薛西王所许可的工程",
        protected_terms=["亚达薛西王"],
    )
    assert "亚达\n薛西王" not in wrapped
    assert max(map(len, wrapped.splitlines())) <= 18
