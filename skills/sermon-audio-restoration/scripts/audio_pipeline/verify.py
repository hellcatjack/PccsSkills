from __future__ import annotations

import json
import math
from pathlib import Path
import re
import subprocess

import soundfile as sf

from .integrity import measure_edge_gain
from .models import (
    ProcessingPlan,
    SourceManifest,
    VerificationItem,
    VerificationReport,
)
from .policy import sha256_file
from .probe import probe_source
from .sync import assert_zero_latency, measure_latency


def _item(name: str, passed: bool, expected: str, actual: str, evidence: str) -> VerificationItem:
    return VerificationItem(
        name=name,
        passed=passed,
        expected=expected,
        actual=actual,
        evidence=evidence,
    )


def _media_loudness(path: Path, audio_ordinal: int) -> tuple[float | None, float | None]:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-map",
        f"0:a:{audio_ordinal}",
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json",
        "-f",
        "null",
        "-",
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    blocks = re.findall(r"\{\s*\"input_i\".*?\}", completed.stderr, re.DOTALL)
    if not blocks:
        return None, None
    data = json.loads(blocks[-1])

    def parsed(name: str) -> float | None:
        try:
            value = float(data[name])
        except (KeyError, TypeError, ValueError):
            return None
        return value if math.isfinite(value) else None

    return parsed("input_i"), parsed("input_tp")


def _full_decode(path: Path) -> tuple[bool, str]:
    completed = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-i",
            str(path),
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode == 0, completed.stderr.strip()


def _video_frame_tolerance(path: Path, sample_rate: int) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=avg_frame_rate",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    rate = completed.stdout.strip()
    if rate and rate != "0/0":
        numerator, denominator = rate.split("/", 1)
        fps = float(numerator) / float(denominator)
        if fps > 0:
            return 1.0 / fps
    return 1.0 / sample_rate


def verify_output(
    source: Path,
    output: Path,
    manifest: SourceManifest,
    plan: ProcessingPlan,
    *,
    master_path: Path | None = None,
    reference_baseline: Path | None = None,
) -> VerificationReport:
    items: list[VerificationItem] = []
    current_source_hash = sha256_file(source)
    items.append(
        _item(
            "source_sha256",
            current_source_hash == manifest.source_sha256,
            manifest.source_sha256,
            current_source_hash,
            "SHA-256 recalculated after processing",
        )
    )

    try:
        output_manifest = probe_source(output, audio_stream=manifest.audio_ordinal)
    except Exception as error:
        items.append(_item("output_probe", False, "readable media", repr(error), "ffprobe/FFmpeg"))
        return VerificationReport(
            source_path=str(source),
            output_path=str(output),
            passed=False,
            items=tuple(items),
            warnings=plan.warnings,
        )

    items.append(
        _item(
            "decoded_sample_count",
            output_manifest.decoded_sample_count == manifest.decoded_sample_count,
            str(manifest.decoded_sample_count),
            str(output_manifest.decoded_sample_count),
            "full selected-stream decode",
        )
    )
    start_error = abs(output_manifest.start_time - manifest.start_time)
    items.append(
        _item(
            "audio_start_time",
            start_error <= 1.0 / manifest.sample_rate,
            f"{manifest.start_time:.9f}",
            f"{output_manifest.start_time:.9f}",
            f"absolute error {start_error:.9f} seconds",
        )
    )

    if master_path is not None:
        master_info = sf.info(master_path)
        items.append(
            _item(
                "lossless_master_samples",
                master_info.frames == manifest.decoded_sample_count,
                str(manifest.decoded_sample_count),
                str(master_info.frames),
                "SoundFile frame count",
            )
        )
    if master_path is not None and reference_baseline is not None:
        try:
            latency = measure_latency(
                reference_baseline,
                master_path,
                repair_intervals=plan.review_intervals,
            )
            assert_zero_latency(latency)
            items.append(
                _item(
                    "lossless_latency",
                    True,
                    "0 samples at every anchor",
                    str(latency.anchor_offsets_samples),
                    f"confidence={latency.confidence:.6f}; drift={latency.drift_slope_samples:.6f}",
                )
            )
        except Exception as error:
            items.append(
                _item(
                    "lossless_latency",
                    False,
                    "0 samples at every anchor",
                    repr(error),
                    "multi-anchor FFT cross-correlation",
                )
            )
        try:
            edge_gain = measure_edge_gain(reference_baseline, master_path)
            no_fade = (
                abs(edge_gain.start_change_db) <= 5.0
                and abs(edge_gain.end_change_db) <= 5.0
            )
            items.append(
                _item(
                    "no_added_fades",
                    no_fade,
                    "absolute start/end gain trend <= 5.00 dB over 15 seconds",
                    (
                        f"start={edge_gain.start_change_db:.2f} dB "
                        f"({edge_gain.start_windows} windows); "
                        f"end={edge_gain.end_change_db:.2f} dB "
                        f"({edge_gain.end_windows} windows)"
                    ),
                    "source-relative 0.5-second RMS regression at both program edges",
                )
            )
        except Exception as error:
            items.append(
                _item(
                    "no_added_fades",
                    False,
                    "measurable source-relative edge gain without fade trend",
                    repr(error),
                    "source-relative edge gain analysis",
                )
            )

    non_target_mismatches = []
    for name, expected_hash in manifest.non_target_stream_hashes.items():
        actual_hash = output_manifest.non_target_stream_hashes.get(name)
        if actual_hash != expected_hash:
            non_target_mismatches.append(f"{name}:{expected_hash}->{actual_hash}")
    items.append(
        _item(
            "non_target_stream_hashes",
            not non_target_mismatches,
            "all unchanged",
            "all unchanged" if not non_target_mismatches else "; ".join(non_target_mismatches),
            "packet-level FFmpeg SHA-256",
        )
    )

    tolerance = _video_frame_tolerance(source, manifest.sample_rate)
    duration_error = abs(output_manifest.duration_seconds - manifest.duration_seconds)
    items.append(
        _item(
            "duration",
            duration_error <= tolerance + 1e-9,
            f"error <= {tolerance:.9f}s",
            f"error={duration_error:.9f}s",
            "decoded duration compared at one video-frame or one-sample tolerance",
        )
    )

    decode_ok, decode_error = _full_decode(output)
    items.append(
        _item(
            "full_decode",
            decode_ok,
            "exit code 0 and no decode error",
            "pass" if decode_ok else decode_error,
            "FFmpeg full media decode",
        )
    )

    integrated, true_peak = _media_loudness(output, manifest.audio_ordinal)
    loudness_ok = integrated is not None and abs(integrated - plan.target_lufs) <= 0.5
    peak_ok = true_peak is not None and true_peak <= plan.true_peak_dbtp + 0.05
    items.append(
        _item(
            "integrated_loudness",
            loudness_ok,
            f"{plan.target_lufs:.1f} ±0.5 LUFS",
            "unavailable" if integrated is None else f"{integrated:.2f} LUFS",
            "FFmpeg loudnorm measurement pass",
        )
    )
    items.append(
        _item(
            "true_peak",
            peak_ok,
            f"<= {plan.true_peak_dbtp:.1f} dBTP",
            "unavailable" if true_peak is None else f"{true_peak:.2f} dBTP",
            "FFmpeg four-times oversampled true-peak measurement",
        )
    )

    if output_manifest.codec_name == "aac":
        padding_ok = output_manifest.decoded_sample_count == manifest.decoded_sample_count
        items.append(
            _item(
                "aac_priming_padding",
                padding_ok,
                "decoded content count preserved after skip-samples/padding",
                str(output_manifest.decoded_sample_count),
                "FFmpeg decoder applies AAC packet side-data semantics",
            )
        )

    passed = all(item.passed for item in items)
    return VerificationReport(
        source_path=str(source),
        output_path=str(output),
        passed=passed,
        items=tuple(items),
        warnings=plan.warnings,
    )
