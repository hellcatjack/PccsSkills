from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audio_pipeline.models import ProcessingPlan, ProcessingStep
from audio_pipeline.policy import PolicyError
from audio_pipeline.probe import probe_source
from audio_pipeline.process import execute_plan
from audio_pipeline.sync import assert_zero_latency, measure_latency
from audio_pipeline.verify import verify_output


def write_signal(path: Path, samples: np.ndarray, sample_rate: int = 48000) -> None:
    sf.write(path, samples.astype(np.float32), sample_rate, subtype="FLOAT")


def test_one_sample_delay_is_rejected(tmp_path: Path):
    rng = np.random.default_rng(7)
    reference = rng.normal(0.0, 0.1, 48000 * 4)
    delayed = np.concatenate(([0.0], reference[:-1]))
    source = tmp_path / "source.wav"
    shifted = tmp_path / "shifted.wav"
    write_signal(source, reference)
    write_signal(shifted, delayed)

    result = measure_latency(source, shifted)
    assert abs(result.global_offset_samples) == 1
    with pytest.raises(PolicyError):
        assert_zero_latency(result)


def test_verified_loudness_master_passes_all_audio_checks(tmp_path: Path):
    sample_rate = 48000
    time = np.arange(sample_rate * 8, dtype=np.float64) / sample_rate
    source = tmp_path / "source.wav"
    write_signal(source, 0.03 * np.sin(2 * np.pi * 330 * time))
    manifest = probe_source(source)
    plan = ProcessingPlan(
        source_sha256=manifest.source_sha256,
        target_lufs=-16.0,
        true_peak_dbtp=-1.5,
        steps=(
            ProcessingStep(
                kind="loudnorm",
                tool="ffmpeg",
                parameters={
                    "integrated_lufs": -16.0,
                    "true_peak_dbtp": -1.5,
                    "lra": 7.0,
                    "two_pass": True,
                },
                evidence=(),
                reason="test loudness",
                confidence=1.0,
            ),
        ),
        requires_ab_review=False,
        review_intervals=(),
        warnings=(),
    )
    result = execute_plan(source, plan, tmp_path / "work")
    report = verify_output(
        source,
        Path(result.master_path),
        manifest,
        plan,
        master_path=Path(result.master_path),
        reference_baseline=source,
    )

    assert report.passed is True
    assert all(item.passed for item in report.items)


def test_verification_rejects_an_added_fade_out(tmp_path: Path):
    sample_rate = 48000
    seconds = 40
    time = np.arange(sample_rate * seconds, dtype=np.float64) / sample_rate
    samples = 0.03 * np.sin(2 * np.pi * 330 * time)
    source = tmp_path / "source.wav"
    faded = tmp_path / "faded.wav"
    write_signal(source, samples)

    fade_frames = sample_rate * 15
    fade = np.ones_like(samples)
    fade[-fade_frames:] = np.linspace(1.0, 0.1, fade_frames)
    write_signal(faded, samples * fade)

    manifest = probe_source(source)
    plan = ProcessingPlan(
        source_sha256=manifest.source_sha256,
        target_lufs=-16.0,
        true_peak_dbtp=-1.5,
        steps=(),
        requires_ab_review=False,
        review_intervals=(),
        warnings=(),
    )
    report = verify_output(
        source,
        faded,
        manifest,
        plan,
        master_path=faded,
        reference_baseline=source,
    )
    items = {item.name: item for item in report.items}

    assert "no_added_fades" in items
    assert items["no_added_fades"].passed is False
