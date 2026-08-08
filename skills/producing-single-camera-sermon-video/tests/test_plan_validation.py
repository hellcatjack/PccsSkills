from copy import deepcopy
import importlib.util
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "validate_composition_plan.py"
SPEC = importlib.util.spec_from_file_location("composition_plan", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_plan() -> dict:
    fixture = Path(__file__).parent / "fixtures" / "valid_plan.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_valid_plan_has_no_errors():
    assert MODULE.validate_plan(valid_plan()) == []


def test_rejects_page_gap():
    plan = valid_plan()
    plan["pptSegments"][1]["targetStart"] += 1.0
    assert any("contiguous" in error for error in MODULE.validate_plan(plan))


def test_rejects_bad_frame_contract():
    plan = valid_plan()
    plan["expectedFrames"] -= 1
    assert any("expectedFrames" in error for error in MODULE.validate_plan(plan))


def test_rejects_overlapping_fullscreen_blocks():
    plan = valid_plan()
    plan["fullScreenBlocks"][1]["start"] = 34.0
    assert any("overlap" in error for error in MODULE.validate_plan(plan))


def test_rejects_missing_semantic_reason():
    plan = valid_plan()
    plan["fullScreenBlocks"][0]["reason"] = ""
    assert any("reason" in error for error in MODULE.validate_plan(plan))


def test_rejects_ending_that_hides_pastor():
    plan = valid_plan()
    plan["endingCover"]["mode"] = "full-cover"
    assert any("left-cover-right-pastor" in error for error in MODULE.validate_plan(plan))


def test_rejects_layout_that_does_not_fill_canvas():
    plan = deepcopy(valid_plan())
    plan["layout"]["pastorPanelWidth"] = 300
    assert any("canvas width" in error for error in MODULE.validate_plan(plan))
