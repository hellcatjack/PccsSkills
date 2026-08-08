import hashlib
from pathlib import Path

import pytest

from audio_pipeline.models import IssueFinding, ProcessingPlan, ProcessingStep
from audio_pipeline.policy import (
    PolicyError,
    assert_cloud_free_allowed,
    assert_safe_command,
    assert_safe_output,
    assert_source_unchanged,
    validate_auphonic_algorithms,
)


@pytest.mark.parametrize(
    "args",
    [
        ["ffmpeg", "-i", "in.wav", "-af", "atrim=start=1", "out.wav"],
        ["ffmpeg", "-i", "in.wav", "-af", "silenceremove=start_periods=1", "out.wav"],
        ["ffmpeg", "-i", "in.wav", "-shortest", "out.mp4"],
        ["ffmpeg", "-ss", "1", "-i", "in.wav", "out.wav"],
        ["ffmpeg", "-i", "in.wav", "-to", "5", "out.wav"],
        ["ffmpeg", "-i", "in.wav", "-t", "5", "out.wav"],
        ["ffmpeg", "-i", "in.wav", "-af", "atempo=1.01", "out.wav"],
        ["ffmpeg", "-i", "in.wav", "-af", "afade=t=in:d=2", "out.wav"],
        ["ffmpeg", "-i", "in.wav", "-af", "afade=t=out:st=10:d=2", "out.wav"],
        ["ffmpeg", "-i", "a.wav", "-i", "b.wav", "-filter_complex", "acrossfade=d=1", "out.wav"],
        ["ffmpeg", "-i", "a.wav", "-i", "b.wav", "-filter_complex", "[0][1]concat=n=2:v=0:a=1", "out.wav"],
    ],
)
def test_forbidden_timeline_operations_are_rejected(args):
    with pytest.raises(PolicyError):
        assert_safe_command(args)


def test_safe_filter_names_do_not_trigger_short_option_false_positive():
    assert_safe_command(
        [
            "ffmpeg",
            "-i",
            "in.wav",
            "-af",
            "dynaudnorm=f=500:g=9:t=0.02,loudnorm=I=-16:TP=-1.5",
            "out.wav",
        ]
    )


def test_only_documented_free_recurring_credits_are_eligible():
    assert_cloud_free_allowed(
        duration_hours=0.5,
        recurring_credits=0.75,
        recurring_cap=2.0,
    )
    with pytest.raises(PolicyError):
        assert_cloud_free_allowed(
            duration_hours=0.5,
            recurring_credits=0.0,
            recurring_cap=2.0,
        )
    with pytest.raises(PolicyError):
        assert_cloud_free_allowed(
            duration_hours=0.5,
            recurring_credits=5.0,
            recurring_cap=10.0,
        )


def test_auphonic_cutters_are_permanently_disabled():
    algorithms = {
        "silence_cutter": False,
        "filler_cutter": False,
        "cough_cutter": False,
        "music_cutter": False,
    }
    validate_auphonic_algorithms(algorithms)
    algorithms["silence_cutter"] = True
    with pytest.raises(PolicyError):
        validate_auphonic_algorithms(algorithms)


def test_source_cannot_be_used_as_output(tmp_path: Path):
    source = tmp_path / "source.wav"
    source.write_bytes(b"source")
    with pytest.raises(PolicyError):
        assert_safe_output(source, source)


def test_source_hash_mutation_is_detected(tmp_path: Path):
    source = tmp_path / "source.wav"
    source.write_bytes(b"source")
    baseline = hashlib.sha256(b"source").hexdigest()
    assert_source_unchanged(source, baseline)
    source.write_bytes(b"changed")
    with pytest.raises(PolicyError):
        assert_source_unchanged(source, baseline)


def test_nested_models_round_trip():
    plan = ProcessingPlan(
        source_sha256="a" * 64,
        target_lufs=-16.0,
        true_peak_dbtp=-1.5,
        steps=(
            ProcessingStep(
                kind="notch",
                tool="ffmpeg",
                parameters={"frequency": 3150.0},
                evidence=(
                    IssueFinding(
                        kind="howl",
                        start=8.0,
                        end=12.0,
                        confidence=0.95,
                        metrics={"frequency": 3150.0},
                        reason="persistent narrow peak",
                    ),
                ),
                reason="localized feedback",
                confidence=0.95,
            ),
        ),
        requires_ab_review=False,
        review_intervals=(),
        warnings=(),
    )
    assert ProcessingPlan.from_dict(plan.to_dict()) == plan
