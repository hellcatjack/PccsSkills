from dataclasses import replace

import pytest

from audio_pipeline.decide import build_plan
from audio_pipeline.models import AnalysisReport, ChannelMetric, IssueFinding


def finding(kind: str, **metrics: float) -> IssueFinding:
    return IssueFinding(
        kind=kind,
        start=8.0,
        end=12.0,
        confidence=0.92,
        metrics=metrics,
        reason=f"synthetic {kind}",
    )


def clean_report() -> AnalysisReport:
    return AnalysisReport(
        source_sha256="a" * 64,
        integrated_lufs=-16.1,
        true_peak_dbtp=-2.0,
        loudness_range_lu=4.0,
        window_loudness=({"start": 0.0, "end": 30.0, "lufs": -16.0},),
        vad_backend="silero-vad",
        active_speech_intervals=((0.0, 20.0),),
        speech_p10_lufs=-18.0,
        speech_p90_lufs=-16.0,
        speech_spread_lu=2.0,
        findings=(),
        channel_metrics=(
            ChannelMetric(0, -18.0, -55.0, 0.25, 34.0),
            ChannelMetric(1, -18.1, -56.0, 0.26, 35.0),
        ),
        capabilities={
            "ffmpeg": True,
            "deepfilternet": True,
            "nara_wpe": True,
            "silero_vad": True,
        },
        warnings=(),
    )


def test_compliant_clean_audio_has_no_processing_steps():
    plan = build_plan(clean_report())
    assert plan.steps == ()
    assert plan.requires_ab_review is False


def test_mono_reverb_never_selects_wpe():
    report = replace(
        clean_report(),
        findings=(finding("reverb", reflection_diversity=0.8),),
        channel_metrics=(ChannelMetric(0, -18.0, -55.0, 0.25, 34.0),),
    )
    plan = build_plan(report)
    assert all(step.tool != "nara-wpe" for step in plan.steps)
    assert any("WPE" in warning for warning in plan.warnings)


def test_decorrelated_stereo_reverb_can_select_wpe():
    report = replace(
        clean_report(),
        findings=(finding("reverb", reflection_diversity=0.25),),
    )
    plan = build_plan(report)
    assert any(step.tool == "nara-wpe" for step in plan.steps)


def test_localized_howl_selects_time_scoped_notch():
    report = replace(
        clean_report(),
        findings=(finding("howl", frequency_hz=3150.0, prominence_db=24.0),),
    )
    plan = build_plan(report)
    step = next(item for item in plan.steps if item.kind == "notch")
    assert step.parameters["frequency_hz"] == 3150.0
    assert step.parameters["start"] == 8.0
    assert step.parameters["end"] == 12.0


def test_severe_clipping_requires_ab_review():
    report = replace(
        clean_report(),
        findings=(finding("clipping", peak_ratio=0.25),),
    )
    plan = build_plan(report)
    assert any(step.kind == "declip" for step in plan.steps)
    assert plan.requires_ab_review is True
    assert plan.review_intervals


def test_large_speech_spread_selects_bounded_leveling():
    report = replace(
        clean_report(),
        integrated_lufs=-22.0,
        speech_p10_lufs=-28.0,
        speech_p90_lufs=-19.0,
        speech_spread_lu=9.0,
    )
    plan = build_plan(report)
    leveling = next(item for item in plan.steps if item.kind == "level")
    assert 0 < leveling.parameters["max_gain_db"] <= 6.0
    assert leveling.parameters["raise_per_half_cycle"] <= 0.00001
    assert any(item.kind == "loudnorm" for item in plan.steps)


def test_energy_vad_with_large_gain_escalates_to_ab_review():
    report = replace(
        clean_report(),
        integrated_lufs=-24.0,
        vad_backend="energy-fallback",
        speech_p10_lufs=-30.0,
        speech_p90_lufs=-19.0,
        speech_spread_lu=11.0,
    )
    assert build_plan(report).requires_ab_review is True


def test_missing_optional_denoiser_is_reported_without_substitution():
    report = replace(
        clean_report(),
        findings=(finding("broadband_noise", snr_db=8.0),),
        capabilities={**clean_report().capabilities, "deepfilternet": False},
    )
    plan = build_plan(report)
    assert all(step.tool != "deepfilternet" for step in plan.steps)
    assert any("DeepFilterNet" in warning for warning in plan.warnings)


def test_unknown_cloud_mode_is_rejected():
    with pytest.raises(ValueError):
        build_plan(clean_report(), cloud="paid")
