from pathlib import Path
import subprocess

import pytest
import soundfile as sf

from audio_pipeline.policy import sha256_file
from audio_pipeline.probe import (
    AmbiguousAudioStreamError,
    extract_baseline,
    probe_source,
)


def run_ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        check=True,
    )


@pytest.fixture()
def media_fixtures(tmp_path: Path) -> dict[str, Path]:
    wav = tmp_path / "tone.wav"
    run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:sample_rate=48000:duration=10",
        "-ac",
        "2",
        "-c:a",
        "pcm_s24le",
        str(wav),
    )

    single = tmp_path / "single.mp4"
    run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "color=c=blue:s=320x180:r=30:duration=10",
        "-i",
        str(wav),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(single),
    )

    dual = tmp_path / "dual.mp4"
    run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=320x180:r=30:duration=10",
        "-i",
        str(wav),
        "-i",
        str(wav),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-map",
        "2:a:0",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        str(dual),
    )
    return {"wav": wav, "single": single, "dual": dual}


def test_probe_audio_records_exact_decoded_sample_count(media_fixtures):
    source = media_fixtures["wav"]
    manifest = probe_source(source)

    assert manifest.audio_ordinal == 0
    assert manifest.stream_index == 0
    assert manifest.sample_rate == 48000
    assert manifest.channels == 2
    assert manifest.decoded_sample_count == 480000
    assert manifest.source_sha256 == sha256_file(source)


def test_probe_single_audio_video_records_both_stream_indexes(media_fixtures):
    manifest = probe_source(media_fixtures["single"])

    assert manifest.audio_ordinal == 0
    assert manifest.stream_index == 1
    assert len(manifest.video_streams) == 1
    assert "stream:0" in manifest.non_target_stream_hashes


def test_ambiguous_audio_requires_zero_based_audio_ordinal(media_fixtures):
    with pytest.raises(AmbiguousAudioStreamError):
        probe_source(media_fixtures["dual"])

    manifest = probe_source(media_fixtures["dual"], audio_stream=1)
    assert manifest.audio_ordinal == 1
    assert manifest.stream_index == 2


def test_extract_baseline_preserves_frames_and_source_hash(media_fixtures, tmp_path):
    source = media_fixtures["single"]
    manifest = probe_source(source)
    before = sha256_file(source)

    baseline = extract_baseline(manifest, tmp_path / "work")
    info = sf.info(baseline)

    assert info.frames == manifest.decoded_sample_count
    assert info.samplerate == manifest.sample_rate
    assert info.channels == manifest.channels
    assert sha256_file(source) == before
