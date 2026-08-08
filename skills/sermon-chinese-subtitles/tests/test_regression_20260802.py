from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT, load_pipeline_module


BEFORE = PROJECT_ROOT / "20260802" / "20260802_如何战胜阻拦_YouTube简体中文字幕.srt"
AFTER = PROJECT_ROOT / "20260802" / "20260802_如何战胜阻拦_YouTube简体中文字幕_高精度校订版.srt"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.skipif(not BEFORE.is_file() or not AFTER.is_file(), reason="project regression fixtures absent")
def test_high_precision_revision_exposes_format_valid_timing_failure() -> None:
    module = load_pipeline_module("compare")
    assert module is not None, "subtitle_pipeline.compare implementation is missing"
    before_hash = _sha256(BEFORE)
    after_hash = _sha256(AFTER)

    report = module.compare_srt(BEFORE, AFTER)

    assert report["before_cues"] == 470
    assert report["after_cues"] == 470
    assert report["text_changed"] == 1
    assert report["start_changed"] >= 300
    assert len(report["over_one_second"]) > 30
    assert report["start_shift_seconds"]["p95_abs"] >= 1.0
    assert max(abs(report["start_shift_seconds"][key]) for key in ("min", "max")) > 2.0
    assert _sha256(BEFORE) == before_hash
    assert _sha256(AFTER) == after_hash
