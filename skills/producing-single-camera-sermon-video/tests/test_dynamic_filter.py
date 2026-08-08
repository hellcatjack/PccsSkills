import importlib.util
import json
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "build_dynamic_filter.py"
SPEC = importlib.util.spec_from_file_location("dynamic_filter", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_plan() -> dict:
    fixture = Path(__file__).parent / "fixtures" / "valid_plan.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_intro_transitions_from_full_to_split():
    plan = valid_plan()
    assert MODULE.focus_at(plan, 4.9) == 1.0
    assert MODULE.focus_at(plan, 5.4) == pytest.approx(0.5)
    assert MODULE.focus_at(plan, 5.9) == 0.0


def test_each_semantic_block_reaches_full_and_returns_to_split():
    plan = valid_plan()
    transition = plan["transitions"]["ordinary"]
    for block in plan["fullScreenBlocks"]:
        assert MODULE.focus_at(plan, block["start"] - 0.01) == 0.0
        assert MODULE.focus_at(plan, block["start"] + transition / 2) == pytest.approx(0.5)
        assert MODULE.focus_at(plan, block["start"] + transition + 0.01) == 1.0
        assert MODULE.focus_at(plan, block["end"] - transition / 2) == pytest.approx(0.5)
        assert MODULE.focus_at(plan, block["end"] + 0.01) == 0.0


def test_filter_uses_plan_crop_and_fixed_right_panel():
    graph = MODULE.build_filter(valid_plan())
    assert "crop=900:2700:700:1140" in graph
    assert "scale=360:1080" in graph
    assert "overlay=x=1560:y=0" in graph


def test_ending_cover_only_replaces_left_region():
    graph = MODULE.build_filter(valid_plan())
    assert "scale=1560:878" in graph
    assert "[dynamic][coverleft]overlay=x=0:y=0" in graph
    assert "left-cover-right-pastor" not in graph


def test_filter_contains_no_audio_processing():
    graph = MODULE.build_filter(valid_plan()).casefold()
    for forbidden in ("[0:a", "[1:a", "afade", "acrossfade", "loudnorm", "speechnorm"):
        assert forbidden not in graph


def test_filter_is_not_bound_to_a_previous_task_date():
    graph = MODULE.build_filter(valid_plan())
    assert "20260802" not in graph
