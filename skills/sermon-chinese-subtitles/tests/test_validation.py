from __future__ import annotations

import json

from conftest import load_pipeline_module


def _write_fixture(
    tmp_path,
    reviews: list[dict],
    *,
    cue_texts: list[str] | None = None,
    context_overrides: dict | None = None,
    scripture_reference: dict | None = None,
    cue_overrides: list[dict] | None = None,
    include_timing_risk: bool = True,
) -> dict:
    cue_texts = cue_texts or ["第一句", "第二句"]
    cue_overrides = cue_overrides or [{}, {}]
    srt_path = tmp_path / "sermon.srt"
    srt_path.write_text(
        f"1\n00:00:00,500 --> 00:00:01,500\n{cue_texts[0]}\n\n"
        f"2\n00:00:02,500 --> 00:00:03,500\n{cue_texts[1]}\n",
        encoding="utf-8",
        newline="\n",
    )
    cues = [
        {"id": "c1", "start": 0.5, "end": 1.5, "text": cue_texts[0]},
        {"id": "c2", "start": 2.5, "end": 3.5, "text": cue_texts[1]},
    ]
    for cue, overrides in zip(cues, cue_overrides, strict=True):
        cue.update(overrides)
    cues_path = tmp_path / "aligned_cues.json"
    cues_path.write_text(
        json.dumps(
            {
                "video_duration": 10.0,
                "language": "zh-Hans",
                "cues": cues,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    alignment_path = tmp_path / "alignment_report.json"
    alignment_path.write_text(
        json.dumps(
            {
                "observed_boundaries": [0.5, 1.5, 2.5, 3.5],
                "risks": [
                    {
                        "cue_id": "c2",
                        "reason": "start_shift_over_1s",
                        "detail": {"shift": 1.4},
                    }
                ]
                if include_timing_risk
                else [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    reviews_path = tmp_path / "boundary_reviews.json"
    reviews_path.write_text(json.dumps({"reviews": reviews}, ensure_ascii=False), encoding="utf-8")
    context_path = tmp_path / "context.json"
    context = {
        "required_terms": [],
        "forbidden_terms": [],
        "protected_terms": [],
        "deity_pronoun_style": "祢/祂",
        "deity_pronoun_exceptions": [],
    }
    context.update(context_overrides or {})
    context_path.write_text(
        json.dumps(context, ensure_ascii=False),
        encoding="utf-8",
    )
    config = {
        "srt_path": srt_path,
        "cues_path": cues_path,
        "alignment_report_path": alignment_path,
        "boundary_reviews_path": reviews_path,
        "context_path": context_path,
        "video_duration": 10.0,
    }
    if scripture_reference is not None:
        scripture_path = tmp_path / "scripture_reference.json"
        scripture_path.write_text(
            json.dumps(scripture_reference, ensure_ascii=False), encoding="utf-8"
        )
        config["scripture_reference_path"] = scripture_path
    return config


def test_format_pass_but_missing_timing_review_requires_review(tmp_path) -> None:
    module = load_pipeline_module("validation")
    assert module is not None, "subtitle_pipeline.validation implementation is missing"

    report = module.validate_delivery(_write_fixture(tmp_path, []))

    assert report["hard_failures"] == 0
    assert report["status"] == "REVIEW_REQUIRED"
    assert report["missing_boundary_reviews"] == ["c2"]


def test_complete_timing_review_allows_pass(tmp_path) -> None:
    module = load_pipeline_module("validation")
    assert module is not None, "subtitle_pipeline.validation implementation is missing"

    reviews = [
        {
            "cue_id": "c2",
            "reason": "高精度版起点移动超过一秒。",
            "evidence": "复听原视频，第一可听词在 2.500 秒。",
            "listened_window": [1.0, 5.0],
        }
    ]
    report = module.validate_delivery(_write_fixture(tmp_path, reviews))

    assert report["hard_failures"] == 0
    assert report["missing_boundary_reviews"] == []
    assert report["status"] == "PASS"


def test_divine_honorific_pronouns_pass_without_review(tmp_path) -> None:
    module = load_pipeline_module("validation")
    config = _write_fixture(
        tmp_path,
        [],
        cue_texts=["主啊，我们感谢祢", "神将祂赐给他们"],
        include_timing_risk=False,
    )

    report = module.validate_delivery(config)

    assert report["deity_pronoun_candidates"] == []
    assert report["missing_deity_pronoun_reviews"] == []
    assert report["status"] == "PASS"


def test_plain_singular_pronoun_near_divine_title_requires_review(tmp_path) -> None:
    module = load_pipeline_module("validation")
    config = _write_fixture(
        tmp_path,
        [],
        cue_texts=["主啊，我们感谢你", "第二句"],
        include_timing_risk=False,
    )

    report = module.validate_delivery(config)

    assert [candidate["cue_id"] for candidate in report["deity_pronoun_candidates"]] == ["c1"]
    assert report["missing_deity_pronoun_reviews"] == ["c1"]
    assert report["hard_failures"] == 0
    assert report["status"] == "REVIEW_REQUIRED"


def test_exact_human_reference_exception_closes_candidate(tmp_path) -> None:
    module = load_pipeline_module("validation")
    text = "主耶稣告诉你要彼此相爱"
    config = _write_fixture(
        tmp_path,
        [],
        cue_texts=[text, "第二句"],
        context_overrides={
            "deity_pronoun_exceptions": [
                {"cue_id": "c1", "text": text, "reason": "这里的“你”指听众。"}
            ]
        },
        include_timing_risk=False,
    )

    report = module.validate_delivery(config)

    assert [candidate["cue_id"] for candidate in report["deity_pronoun_candidates"]] == ["c1"]
    assert report["missing_deity_pronoun_reviews"] == []
    assert report["status"] == "PASS"


def test_stale_deity_pronoun_exception_is_a_hard_failure(tmp_path) -> None:
    module = load_pipeline_module("validation")
    config = _write_fixture(
        tmp_path,
        [],
        context_overrides={
            "deity_pronoun_exceptions": [
                {"cue_id": "c1", "text": "不是当前字幕", "reason": "过期记录。"}
            ]
        },
        include_timing_risk=False,
    )

    report = module.validate_delivery(config)

    assert report["status"] == "FAIL"
    assert any(error["check"] == "deity_pronouns" for error in report["hard_errors"])


def test_human_pronouns_do_not_create_candidates(tmp_path) -> None:
    module = load_pipeline_module("validation")
    config = _write_fixture(
        tmp_path,
        [],
        cue_texts=["弟兄，你们要彼此相爱", "保罗说他要去耶路撒冷"],
        include_timing_risk=False,
    )

    report = module.validate_delivery(config)

    assert report["deity_pronoun_candidates"] == []
    assert report["missing_deity_pronoun_reviews"] == []
    assert report["status"] == "PASS"


def test_plural_deity_honorifics_are_hard_failures(tmp_path) -> None:
    module = load_pipeline_module("validation")
    config = _write_fixture(
        tmp_path,
        [],
        cue_texts=["祢们来到这里", "祂们来到这里"],
        include_timing_risk=False,
    )

    report = module.validate_delivery(config)

    assert report["status"] == "FAIL"
    deity_error = next(error for error in report["hard_errors"] if error["check"] == "deity_pronouns")
    assert [item["form"] for item in deity_error["detail"]["invalid_plural_honorifics"]] == [
        "祢们",
        "祂们",
    ]


def test_scripture_reference_rejects_mixed_deity_pronoun_style(tmp_path) -> None:
    module = load_pipeline_module("validation")
    config = _write_fixture(
        tmp_path,
        [],
        cue_texts=["神将祂赐给世人", "第二句"],
        cue_overrides=[{"reference": "约3:16"}, {}],
        scripture_reference={
            "entries": [
                {"reference": "约3:16", "text": "神将他赐给世人", "spoken": True}
            ]
        },
        include_timing_risk=False,
    )

    report = module.validate_delivery(config)

    assert report["status"] == "FAIL"
    assert any(error["check"] == "scripture" for error in report["hard_errors"])
