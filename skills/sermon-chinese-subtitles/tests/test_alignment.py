from __future__ import annotations

import pytest

from conftest import load_pipeline_module


def _segment(segment_id: int, words: list[tuple[float, float, str]]) -> dict:
    return {
        "id": segment_id,
        "start": min(start for start, _, _ in words),
        "end": max(end for _, end, _ in words),
        "text": "".join(word for _, _, word in words),
        "words": [
            {"start": start, "end": end, "word": word, "probability": 0.9}
            for start, end, word in words
        ],
    }


def test_retime_selects_better_precision_source_and_observed_boundaries() -> None:
    module = load_pipeline_module("alignment")
    assert module is not None, "subtitle_pipeline.alignment implementation is missing"

    reviewed = {
        "video_duration": 5.0,
        "cues": [
            {
                "id": "c1",
                "start": 0.0,
                "end": 2.2,
                "text": "尼希米修造城墙",
                "source_segment_ids": [10],
                "alignment_group": "g1",
                "source": "ai_semantic_review",
                "confidence": "high",
                "reason": "按讲章和经文专名校正香港口音。",
            }
        ],
    }
    asr_sources = {
        "primary": {
            "segments": [
                _segment(10, [(0.2, 0.8, "黎西米"), (0.9, 1.3, "修造"), (1.4, 2.1, "城墅")])
            ]
        },
        "precision": {
            "segments": [
                _segment(20, [(0.25, 0.85, "尼希米"), (0.95, 1.35, "修造"), (1.45, 2.05, "城墙")])
            ]
        },
    }

    result = module.retime_reviewed_cues(reviewed, asr_sources)

    assert result["groups"][0]["timing_source"] == "precision"
    assert result["cues"][0]["start"] == 0.25
    assert result["cues"][0]["end"] == 2.05
    assert 0.25 in result["observed_boundaries"]
    assert 2.05 in result["observed_boundaries"]


def test_low_match_ratio_creates_mandatory_review_risk() -> None:
    module = load_pipeline_module("alignment")
    assert module is not None, "subtitle_pipeline.alignment implementation is missing"

    reviewed = {
        "video_duration": 4.0,
        "cues": [
            {
                "id": "c-low",
                "start": 0.1,
                "end": 2.0,
                "text": "我们的神必为我们争战",
                "alignment_window": [0.0, 2.5],
                "alignment_group": "g-low",
                "source": "ai_semantic_review",
                "confidence": "low",
                "reason": "两路转写冲突。",
            }
        ],
    }
    asr_sources = {
        "primary": {
            "segments": [_segment(1, [(0.2, 0.8, "完全"), (0.9, 1.5, "不同"), (1.6, 2.1, "字句")])]
        }
    }

    result = module.retime_reviewed_cues(reviewed, asr_sources)

    assert result["groups"][0]["matched_ratio"] < 0.65
    assert any(
        risk["cue_id"] == "c-low" and risk["reason"] == "low_match_ratio"
        for risk in result["risks"]
    )


def test_overlap_above_review_threshold_is_rejected() -> None:
    module = load_pipeline_module("alignment")
    assert module is not None, "subtitle_pipeline.alignment implementation is missing"

    reviewed = {
        "video_duration": 5.0,
        "cues": [
            {
                "id": "c1",
                "start": 0.0,
                "end": 2.0,
                "text": "第一句",
                "alignment_window": [0.0, 2.5],
                "alignment_group": "g1",
                "source": "ai_semantic_review",
                "confidence": "high",
                "reason": "第一句。",
            },
            {
                "id": "c2",
                "start": 1.0,
                "end": 3.0,
                "text": "第二句",
                "alignment_window": [0.5, 3.5],
                "alignment_group": "g2",
                "source": "ai_semantic_review",
                "confidence": "high",
                "reason": "第二句。",
            },
        ],
    }
    asr_sources = {
        "primary": {
            "segments": [
                _segment(1, [(0.1, 2.1, "第一句")]),
                _segment(2, [(1.0, 3.0, "第二句")]),
            ]
        }
    }

    with pytest.raises(ValueError, match="above the 0.800s review threshold"):
        module.retime_reviewed_cues(reviewed, asr_sources)
