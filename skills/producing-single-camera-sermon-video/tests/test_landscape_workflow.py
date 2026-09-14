"""Behavior checks for inset composition and frame-exact camera processing."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_composition_plan import validate_plan
from build_dynamic_filter import build_filter


def inset_plan():
    plan = json.loads((ROOT / "tests/fixtures/valid_plan.json").read_text(encoding="utf-8"))
    plan["transitions"]["ordinary"] = 0.8
    plan["intro"] = {"fullUntil": 16, "splitComplete": 16.8,
                     "cameraForbiddenBefore": 16, "coverUntil": 16, "coverSlide": 1}
    plan["layout"] = {
        "canvasWidth": 1920, "canvasHeight": 1080,
        "pptRect": {"x": 40, "y": 198, "width": 1216, "height": 684},
        "pastorRect": {"x": 1280, "y": 198, "width": 600, "height": 684},
        "sourceVideoWidth": 3840, "sourceVideoHeight": 2160,
        "pastorCrop": {"x": 1400, "y": 450, "width": 1500, "height": 1710},
    }
    return plan


def test_inset_rectangles_support_margins_without_stretching():
    assert validate_plan(inset_plan()) == []
    graph = build_filter(inset_plan())
    assert "scale=600:684" in graph
    assert "overlay=x=1280:y=198" in graph
    assert "crop=1500:1710:1400:450" in graph
    assert "scale=360:1080" not in graph


@pytest.mark.parametrize("mutation, expected", [
    (lambda p: p["layout"]["pastorRect"].update(x=1240), "overlap"),
    (lambda p: p["layout"]["pastorRect"].update(width=602), "aspect"),
    (lambda p: p["layout"]["pptRect"].update(x=-2), "inside"),
    (lambda p: p["intro"].update(coverUntil=15), "cameraForbiddenBefore"),
    (lambda p: p["intro"].update(fullUntil=15, splitComplete=15.8), "coverUntil"),
    (lambda p: p["pptSegments"][0].update(slide=2), "coverSlide"),
    (lambda p: p["fullScreenBlocks"][0].update(start=16), "intro"),
    (lambda p: p["layout"]["pastorCrop"].update(x=1400.5), "integer"),
    (lambda p: p["intro"].update(fullUntil=101, splitComplete=101.8), "endingCover"),
])
def test_rejects_unsafe_inset_plans(mutation, expected):
    plan = inset_plan()
    mutation(plan)
    assert any(expected in error for error in validate_plan(plan))


def test_preprocessed_camera_is_not_cropped_or_denoised_twice():
    plan = inset_plan()
    plan["cameraInput"] = {"mode": "processed-panel", "width": 600, "height": 684}
    assert validate_plan(plan) == []
    graph = build_filter(plan)
    assert "crop=1500:1710:1400:450" not in graph
    assert "[1:v]" in graph
    for forbidden in ("atadenoise", "nlmeans", "[1:a", "loudnorm"):
        assert forbidden not in graph
    plan["cameraInput"]["width"] = 900
    assert any("processed-panel" in e for e in validate_plan(plan))


def camera_module():
    path = ROOT / "scripts/plan_camera_processing.py"
    assert path.is_file(), "camera visibility planner is missing"
    spec = importlib.util.spec_from_file_location("camera_processing", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_camera_planner_omits_only_fully_hidden_frames_and_adds_context():
    result = camera_module().plan_processing(inset_plan(), context_frames=6)
    # At ramp start/end the pastor opacity is exactly zero; preserve every
    # positive-opacity frame, including transition tails and the final word.
    cores = result["visibleRanges"]
    assert cores == [[481, 624], [1027, 1974], [2377, 3600]]
    chunks = result["chunks"]
    assert [(c["decodeStart"], c["decodeEnd"]) for c in chunks] == [
        (475, 630), (1021, 1980), (2371, 3600)]
    assert chunks[-1]["outputRanges"] == [[2377, 3600]]
    assert result["visibleFrames"] == sum(b-a for a, b in cores)
    assert result["decodeFrames"] < 3600


def test_context_overlap_merges_decode_work_but_preserves_core_ranges():
    result = camera_module().plan_processing(inset_plan(), context_frames=250)
    assert len(result["chunks"]) == 1
    assert result["chunks"][0]["outputRanges"] == result["visibleRanges"]
    assert result["chunks"][0]["decodeStart"] == 231
    assert result["chunks"][0]["decodeEnd"] == 3600


def test_visibility_planner_rejects_unknown_timing_instead_of_guessing():
    module = camera_module()
    with pytest.raises(ValueError, match="context"):
        module.plan_processing(inset_plan(), context_frames=-1)
    plan = inset_plan()
    plan["fullScreenBlocks"][0]["start"] += 0.001
    with pytest.raises(ValueError, match="frame"):
        module.plan_processing(plan, context_frames=6)
