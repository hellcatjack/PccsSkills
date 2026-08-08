from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audio_pipeline.models import ProcessingPlan, ProcessingStep
from audio_pipeline.policy import PolicyError, assert_safe_command
from audio_pipeline.process import (
    build_filter_for_step,
    execute_plan,
    validate_stage_sample_count,
)


@pytest.fixture()
def baseline(tmp_path: Path) -> Path:
    sample_rate = 48000
    frames = sample_rate * 10
    time = np.arange(frames, dtype=np.float64) / sample_rate
    envelope = np.where(time < 5.0, 0.04, 0.20)
    tone = envelope * np.sin(2 * np.pi * 330 * time)
    stereo = np.column_stack([tone, tone * 0.98]).astype(np.float32)
    output = tmp_path / "baseline.wav"
    sf.write(output, stereo, sample_rate, subtype="FLOAT")
    return output


def step(kind: str, parameters: dict) -> ProcessingStep:
    return ProcessingStep(
        kind=kind,
        tool="ffmpeg",
        parameters=parameters,
        evidence=(),
        reason=f"test {kind}",
        confidence=1.0,
    )


def test_filter_builder_never_emits_forbidden_timeline_operations():
    filters = [
        build_filter_for_step(step("declick", {})),
        build_filter_for_step(step("declip", {})),
        build_filter_for_step(
            step(
                "notch",
                {
                    "frequency_hz": 3150.0,
                    "width_hz": 12.0,
                    "gain_db": -12.0,
                    "start": 2.0,
                    "end": 4.0,
                },
            )
        ),
        build_filter_for_step(
            step(
                "level",
                {
                    "frame_ms": 1000,
                    "gaussian_size": 31,
                    "max_gain_db": 6.0,
                    "threshold": 0.02,
                    "couple_channels": True,
                },
            )
        ),
    ]
    assert_safe_command(["ffmpeg", "-i", "in.wav", "-af", ",".join(filters), "out.wav"])


def test_level_filter_uses_speech_normalizer_without_boundary_fades():
    expression = build_filter_for_step(
        step(
            "level",
            {
                "max_gain_db": 6.0,
                "raise_per_half_cycle": 0.00001,
                "couple_channels": True,
            },
        )
    )

    assert expression.startswith("speechnorm=")
    assert "e=1.9952623" in expression
    assert "r=1e-05" in expression
    assert "l=true" in expression
    assert "dynaudnorm" not in expression


def test_execute_plan_preserves_every_sample_and_edges(baseline: Path, tmp_path: Path):
    plan = ProcessingPlan(
        source_sha256="a" * 64,
        target_lufs=-16.0,
        true_peak_dbtp=-1.5,
        steps=(
            step(
                "level",
                {
                    "frame_ms": 1000,
                    "gaussian_size": 31,
                    "max_gain_db": 6.0,
                    "threshold": 0.02,
                    "couple_channels": True,
                },
            ),
            step(
                "loudnorm",
                {
                    "integrated_lufs": -16.0,
                    "true_peak_dbtp": -1.5,
                    "lra": 7.0,
                    "two_pass": True,
                },
            ),
        ),
        requires_ab_review=False,
        review_intervals=(),
        warnings=(),
    )
    result = execute_plan(baseline, plan, tmp_path / "work")
    processed, sample_rate = sf.read(result.master_path, always_2d=True)

    assert len(processed) == 480000
    assert all(count == 480000 for count in result.stage_sample_counts)
    edge = int(sample_rate * 0.1)
    assert np.max(np.abs(processed[:edge])) > 0.001
    assert np.max(np.abs(processed[-edge:])) > 0.001


def test_processor_padding_is_rejected_instead_of_trimmed(baseline: Path, tmp_path: Path):
    audio, sample_rate = sf.read(baseline, always_2d=True)
    padded = tmp_path / "padded.wav"
    sf.write(
        padded,
        np.pad(audio, ((0, 240), (0, 0))),
        sample_rate,
        subtype="FLOAT",
    )
    with pytest.raises(PolicyError):
        validate_stage_sample_count(padded, expected_frames=len(audio))


def test_ab_samples_are_review_only_and_do_not_feed_master(baseline: Path, tmp_path: Path):
    plan = ProcessingPlan(
        source_sha256="a" * 64,
        target_lufs=-16.0,
        true_peak_dbtp=-1.5,
        steps=(),
        requires_ab_review=True,
        review_intervals=((2.0, 4.0),),
        warnings=(),
    )
    result = execute_plan(baseline, plan, tmp_path / "review")
    assert len(result.ab_sample_paths) == 2
    assert sf.info(result.master_path).frames == sf.info(baseline).frames
    assert all(sf.info(path).frames == 96000 for path in result.ab_sample_paths)
