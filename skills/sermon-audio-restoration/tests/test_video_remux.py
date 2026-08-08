import json
from pathlib import Path
import subprocess

import numpy as np
import pytest
import soundfile as sf

from audio_pipeline import sync
from audio_pipeline.probe import extract_baseline, hash_stream_packets, probe_source
from audio_pipeline.sync import remux_replacement_audio
from audio_pipeline.verify import _media_loudness


def run_ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        check=True,
    )


def ffprobe(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_chapters",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def make_multistream_video(tmp_path: Path) -> Path:
    subtitle = tmp_path / "caption.srt"
    subtitle.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nTest caption\n",
        encoding="utf-8",
    )
    metadata = tmp_path / "chapters.ffmeta"
    metadata.write_text(
        ";FFMETADATA1\n"
        "title=Preservation Test\n"
        "[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=2000\ntitle=Opening\n"
        "[CHAPTER]\nTIMEBASE=1/1000\nSTART=2000\nEND=4000\ntitle=Closing\n",
        encoding="utf-8",
    )
    output = tmp_path / "source.mp4"
    run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc2=s=320x180:r=30:duration=4",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:sample_rate=48000:duration=4",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=660:sample_rate=48000:duration=4",
        "-i",
        str(subtitle),
        "-f",
        "ffmetadata",
        "-i",
        str(metadata),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-map",
        "2:a:0",
        "-map",
        "3:s:0",
        "-map_metadata",
        "4",
        "-map_chapters",
        "4",
        "-metadata:s:a:0",
        "language=eng",
        "-metadata:s:a:1",
        "language=zho",
        "-disposition:a:0",
        "default",
        "-disposition:a:1",
        "0",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-c:s",
        "mov_text",
        str(output),
    )
    return output


def test_remux_changes_only_selected_audio_stream(tmp_path: Path):
    source = make_multistream_video(tmp_path)
    manifest = probe_source(source, audio_stream=1)
    baseline = extract_baseline(manifest, tmp_path / "work")
    audio, sample_rate = sf.read(baseline, always_2d=True)
    master = tmp_path / "processed.wav"
    sf.write(master, audio * 0.75, sample_rate, subtype="FLOAT")
    output = tmp_path / "restored.mp4"

    remux_replacement_audio(source, master, manifest.stream_index, output)

    source_probe = ffprobe(source)
    output_probe = ffprobe(output)
    assert len(source_probe["streams"]) == len(output_probe["streams"])
    assert len(source_probe["chapters"]) == len(output_probe["chapters"])
    assert output_probe["format"]["tags"]["title"] == "Preservation Test"

    for stream in source_probe["streams"]:
        index = int(stream["index"])
        if index == manifest.stream_index:
            assert hash_stream_packets(source, index) != hash_stream_packets(output, index)
        else:
            assert hash_stream_packets(source, index) == hash_stream_packets(output, index)

    source_audio = source_probe["streams"][manifest.stream_index]
    output_audio = output_probe["streams"][manifest.stream_index]
    assert source_audio.get("tags", {}).get("language") == output_audio.get("tags", {}).get("language")
    assert source_audio["disposition"]["default"] == output_audio["disposition"]["default"]
    assert abs(float(source_audio.get("start_time", 0)) - float(output_audio.get("start_time", 0))) <= 1 / 48000


def test_remux_reserves_true_peak_headroom_for_aac(tmp_path: Path):
    source = make_multistream_video(tmp_path)
    manifest = probe_source(source, audio_stream=0)
    baseline = extract_baseline(manifest, tmp_path / "headroom-work")
    frames = sf.info(baseline).frames
    rng = np.random.default_rng(20260807)
    audio = rng.normal(0.0, 1.0, frames).astype(np.float32)
    audio *= (10 ** (-1.45 / 20)) / np.max(np.abs(audio))
    master = tmp_path / "transient-master.wav"
    sf.write(master, audio, manifest.sample_rate, subtype="FLOAT")
    output = tmp_path / "headroom-restored.mp4"

    remux_replacement_audio(source, master, manifest.stream_index, output)

    master_integrated_lufs, _master_true_peak = _media_loudness(master, 0)
    integrated_lufs, true_peak_dbtp = _media_loudness(output, 0)
    assert master_integrated_lufs is not None
    assert integrated_lufs is not None
    assert true_peak_dbtp is not None
    assert true_peak_dbtp <= -1.5
    assert -16.5 <= integrated_lufs <= -15.5


def test_aac_calibration_selects_makeup_with_peak_margin():
    gain_db = sync._choose_aac_makeup_gain(
        measured_lufs=-16.60,
        measured_true_peak_dbtp=-2.21,
        target_lufs=-16.0,
        target_true_peak_dbtp=-1.5,
    )

    assert gain_db == pytest.approx(0.35)


def test_aac_precondition_uses_calibrated_makeup():
    filter_expression = sync._aac_precondition_filter(-1.5, makeup_gain_db=0.35)

    assert "limit=0.749894209" in filter_expression
    assert "level_out=1.041118108" in filter_expression
    assert "level=false" in filter_expression
    assert "latency=true" in filter_expression
    assert "afade" not in filter_expression
