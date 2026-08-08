from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import audio_pipeline.analyze as analyze_module
from audio_pipeline.analyze import analyze_audio
from audio_pipeline.models import AnalysisReport
from audio_pipeline.probe import probe_source


@pytest.fixture()
def defective_audio(tmp_path: Path) -> Path:
    sample_rate = 48000
    duration = 16.0
    frames = int(sample_rate * duration)
    time = np.arange(frames, dtype=np.float64) / sample_rate

    voice = (
        0.65 * np.sin(2 * np.pi * 180 * time)
        + 0.25 * np.sin(2 * np.pi * 350 * time)
        + 0.10 * np.sin(2 * np.pi * 900 * time)
    )
    envelope = np.where(time < 5, 0.20, np.where(time < 10, 0.045, 0.28))
    signal = voice * envelope
    signal += 0.014 * np.sin(2 * np.pi * 60 * time)
    signal += 0.010 * np.sin(2 * np.pi * 120 * time)

    howl_mask = (time >= 8.0) & (time < 12.0)
    signal[howl_mask] += 0.11 * np.sin(2 * np.pi * 3150 * time[howl_mask])

    rng = np.random.default_rng(20260807)
    left = signal + rng.normal(0.0, 0.025, frames)
    right = signal + rng.normal(0.0, 0.004, frames)

    click_frame = int(2.0 * sample_rate)
    left[click_frame] = 1.0
    right[click_frame] = 1.0

    clip_start = int(6.0 * sample_rate)
    clip_end = int(6.2 * sample_rate)
    left[clip_start:clip_end] = np.clip(
        left[clip_start:clip_end] * 30.0, -1.0, 1.0
    )
    right[clip_start:clip_end] = np.clip(
        right[clip_start:clip_end] * 30.0, -1.0, 1.0
    )

    output = tmp_path / "defective.wav"
    sf.write(output, np.column_stack([left, right]), sample_rate, subtype="FLOAT")
    return output


def mocked_vad(_path: Path):
    return ((0.0, 5.0), (5.0, 10.0), (10.0, 16.0)), "mock-vad"


def test_full_analysis_detects_synthetic_defects(
    defective_audio: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(analyze_module, "detect_speech_intervals", mocked_vad)
    manifest = probe_source(defective_audio)
    report = analyze_audio(defective_audio, manifest, window_seconds=5.0)

    assert report.integrated_lufs is not None
    assert report.true_peak_dbtp is not None
    assert report.speech_spread_lu is not None
    assert report.speech_spread_lu > 3.0

    kinds = {finding.kind for finding in report.findings}
    assert {"click", "clipping", "howl", "hum"} <= kinds

    howl = [item for item in report.findings if item.kind == "howl"]
    assert any(abs(item.metrics["frequency_hz"] - 3150.0) < 40.0 for item in howl)
    assert any(item.start < 8.5 and item.end > 11.5 for item in howl)

    assert len(report.channel_metrics) == 2
    assert report.channel_metrics[1].clarity_score > report.channel_metrics[0].clarity_score


def test_analysis_json_round_trip_is_deterministic(
    defective_audio: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(analyze_module, "detect_speech_intervals", mocked_vad)
    manifest = probe_source(defective_audio)
    report = analyze_audio(defective_audio, manifest, window_seconds=5.0)
    output = tmp_path / "analysis.json"
    report.write_json(output)

    restored = AnalysisReport.from_dict(__import__("json").loads(output.read_text("utf-8")))
    assert restored == report


def test_energy_vad_fallback_requires_ai_review(
    defective_audio: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        analyze_module,
        "detect_speech_intervals",
        lambda _path: (((0.0, 16.0),), "energy-fallback"),
    )
    report = analyze_audio(defective_audio, probe_source(defective_audio))
    assert report.vad_backend == "energy-fallback"
    assert any("AI review" in warning for warning in report.warnings)


def test_voiced_harmonic_series_is_not_misclassified_as_feedback():
    sample_rate = 48000
    duration = 8.0
    time = np.arange(int(sample_rate * duration), dtype=np.float64) / sample_rate
    fundamental = 158.807
    voice = sum(
        (0.06 / harmonic)
        * np.sin(2.0 * np.pi * harmonic * fundamental * time)
        for harmonic in range(1, 11)
    )
    voice += 0.12 * np.sin(2.0 * np.pi * 4.0 * fundamental * time)
    voice *= 0.7 + 0.3 * np.sin(2.0 * np.pi * 1.2 * time) ** 2

    findings = analyze_module._block_findings(
        np.column_stack([voice, voice]),
        sample_rate,
        0.0,
    )

    assert not [finding for finding in findings if finding.kind == "howl"]


def test_silero_vad_does_not_depend_on_torchaudio_file_io(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    silero_vad = pytest.importorskip("silero_vad")
    sample_rate = 48000
    source = tmp_path / "silence.wav"
    sf.write(source, np.zeros(sample_rate, dtype=np.float32), sample_rate, subtype="FLOAT")

    def unavailable_read_audio(*_args, **_kwargs):
        raise RuntimeError("torchaudio file I/O is unavailable")

    monkeypatch.setattr(silero_vad, "read_audio", unavailable_read_audio)

    intervals, backend = analyze_module.detect_speech_intervals(source)

    assert backend == "silero-vad"
    assert intervals == ()
