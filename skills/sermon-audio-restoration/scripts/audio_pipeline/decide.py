from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .models import AnalysisReport, IssueFinding, ProcessingPlan, ProcessingStep


def _by_kind(findings: Iterable[IssueFinding]) -> dict[str, list[IssueFinding]]:
    grouped: dict[str, list[IssueFinding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.kind].append(finding)
    return grouped


def _step(
    *,
    kind: str,
    tool: str,
    parameters: dict,
    evidence: Iterable[IssueFinding],
    reason: str,
    confidence: float,
) -> ProcessingStep:
    return ProcessingStep(
        kind=kind,
        tool=tool,
        parameters=parameters,
        evidence=tuple(evidence),
        reason=reason,
        confidence=confidence,
    )


def _expanded_interval(finding: IssueFinding) -> tuple[float, float]:
    return max(0.0, finding.start - 3.0), finding.end + 3.0


def _deduplicate_intervals(
    intervals: Iterable[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return tuple((start, end) for start, end in merged)


def build_plan(
    report: AnalysisReport,
    target_lufs: float = -16.0,
    true_peak: float = -1.5,
    cloud: str = "off",
) -> ProcessingPlan:
    if cloud not in {"off", "auphonic-free"}:
        raise ValueError(f"Unsupported cloud mode: {cloud}")

    grouped = _by_kind(report.findings)
    steps: list[ProcessingStep] = []
    warnings = list(report.warnings)
    review_intervals: list[tuple[float, float]] = []
    requires_ab_review = False

    clipping = grouped.get("clipping", [])
    if clipping:
        steps.append(
            _step(
                kind="declip",
                tool="ffmpeg",
                parameters={"window": 55, "overlap": 75, "method": "add"},
                evidence=clipping,
                reason="repair confirmed flat-top sample regions before level processing",
                confidence=min(item.confidence for item in clipping),
            )
        )
        severe = [
            item
            for item in clipping
            if item.metrics.get("peak_ratio", 0.0) >= 0.10
            or item.end - item.start >= 0.25
        ]
        if severe:
            requires_ab_review = True
            review_intervals.extend(_expanded_interval(item) for item in severe)

    clicks = grouped.get("click", [])
    if clicks:
        steps.append(
            _step(
                kind="declick",
                tool="ffmpeg",
                parameters={"window": 55, "overlap": 75, "method": "add"},
                evidence=clicks,
                reason="remove isolated impulsive discontinuities",
                confidence=min(item.confidence for item in clicks),
            )
        )
        uncertain = [item for item in clicks if item.confidence < 0.75]
        if uncertain:
            requires_ab_review = True
            review_intervals.extend(_expanded_interval(item) for item in uncertain)

    plosives = grouped.get("plosive", [])
    for item in plosives:
        steps.append(
            _step(
                kind="plosive-control",
                tool="ffmpeg",
                parameters={
                    "start": item.start,
                    "end": item.end,
                    "cutoff_hz": min(140.0, item.metrics.get("dominant_hz", 100.0) + 40.0),
                },
                evidence=(item,),
                reason="apply localized low-frequency control without thinning the full sermon",
                confidence=item.confidence,
            )
        )
        if item.confidence < 0.80:
            requires_ab_review = True
            review_intervals.append(_expanded_interval(item))

    hum = grouped.get("hum", [])
    if hum:
        base_frequency = hum[0].metrics.get("base_frequency_hz", 60.0)
        steps.append(
            _step(
                kind="dehum",
                tool="ffmpeg",
                parameters={
                    "base_frequency_hz": base_frequency,
                    "harmonics": 4,
                    "width_hz": 3.0,
                },
                evidence=hum,
                reason="remove measured mains fundamental and harmonics with narrow notches",
                confidence=min(item.confidence for item in hum),
            )
        )

    howls = grouped.get("howl", [])
    for item in howls:
        steps.append(
            _step(
                kind="notch",
                tool="ffmpeg",
                parameters={
                    "frequency_hz": item.metrics["frequency_hz"],
                    "width_hz": max(4.0, min(30.0, item.metrics.get("bandwidth_hz", 12.0))),
                    "gain_db": -12.0,
                    "start": item.start,
                    "end": item.end,
                },
                evidence=(item,),
                reason="attenuate only the measured feedback tone and affected time range",
                confidence=item.confidence,
            )
        )
    if len(howls) > 3:
        requires_ab_review = True
        review_intervals.extend(_expanded_interval(item) for item in howls)

    stationary_noise = grouped.get("stationary_noise", [])
    if stationary_noise:
        steps.append(
            _step(
                kind="denoise-light",
                tool="ffmpeg",
                parameters={"reduction_db": 6.0, "noise_floor_db": -50.0},
                evidence=stationary_noise,
                reason="use conservative stationary-noise reduction",
                confidence=min(item.confidence for item in stationary_noise),
            )
        )

    broadband_noise = grouped.get("broadband_noise", [])
    if broadband_noise:
        if report.capabilities.get("deepfilternet", False):
            steps.append(
                _step(
                    kind="denoise-speech",
                    tool="deepfilternet",
                    parameters={"compensate_delay": True, "post_filter": False},
                    evidence=broadband_noise,
                    reason="use a mature full-band speech enhancer for confirmed broadband noise",
                    confidence=min(item.confidence for item in broadband_noise),
                )
            )
            if any(item.metrics.get("snr_db", 99.0) < 10.0 for item in broadband_noise):
                requires_ab_review = True
                review_intervals.extend(_expanded_interval(item) for item in broadband_noise)
        else:
            warnings.append(
                "DeepFilterNet is unavailable; confirmed broadband noise was not silently substituted with a stronger generic filter."
            )

    reverb = grouped.get("reverb", [])
    if reverb:
        reflection_diversity = max(
            item.metrics.get("reflection_diversity", 0.0) for item in reverb
        )
        if len(report.channel_metrics) < 2:
            warnings.append("WPE was not selected because the source is mono.")
        elif reflection_diversity < 0.10:
            warnings.append(
                "WPE was not selected because the channels lack sufficient reflection diversity."
            )
        elif not report.capabilities.get("nara_wpe", False):
            warnings.append("NARA-WPE is unavailable; reverberation remains for AI review.")
        else:
            steps.append(
                _step(
                    kind="dereverb",
                    tool="nara-wpe",
                    parameters={
                        "taps": 10,
                        "delay": 3,
                        "iterations": 3,
                        "block_seconds": 30,
                    },
                    evidence=reverb,
                    reason="use multichannel WPE only after reflection-diversity gating",
                    confidence=min(item.confidence for item in reverb),
                )
            )

    requested_gain = 0.0
    if report.speech_p10_lufs is not None:
        requested_gain = max(0.0, min(6.0, -19.0 - report.speech_p10_lufs))
    if report.speech_spread_lu is not None and report.speech_spread_lu > 3.0:
        if cloud == "auphonic-free":
            steps.append(
                _step(
                    kind="level",
                    tool="auphonic-free",
                    parameters={
                        "leveler_strength": 70,
                        "max_lra": 7,
                        "cutters": False,
                    },
                    evidence=(),
                    reason="explicitly requested free adaptive speech leveling",
                    confidence=0.85,
                )
            )
            warnings.append(
                "Auphonic remains blocked until upload consent and free recurring-credit checks pass."
            )
        else:
            steps.append(
                _step(
                    kind="level",
                    tool="ffmpeg",
                    parameters={
                        "max_gain_db": requested_gain,
                        "raise_per_half_cycle": 0.00001,
                        "couple_channels": True,
                    },
                    evidence=(),
                    reason="correct sustained active-speech drift with bounded, slow speech expansion",
                    confidence=0.90 if report.vad_backend == "silero-vad" else 0.65,
                )
            )
        if report.vad_backend == "energy-fallback" and requested_gain >= 6.0:
            requires_ab_review = True
            review_intervals.extend(report.active_speech_intervals[:1])
            review_intervals.extend(report.active_speech_intervals[-1:])

    upstream_processing = bool(steps)
    loudness_outside = (
        report.integrated_lufs is None
        or abs(report.integrated_lufs - target_lufs) > 0.5
        or report.true_peak_dbtp is None
        or report.true_peak_dbtp > true_peak
    )
    if upstream_processing or loudness_outside:
        steps.append(
            _step(
                kind="loudnorm",
                tool="ffmpeg",
                parameters={
                    "integrated_lufs": target_lufs,
                    "true_peak_dbtp": true_peak,
                    "lra": 7.0,
                    "two_pass": True,
                },
                evidence=(),
                reason="finish with measured two-pass program loudness and true-peak control",
                confidence=1.0,
            )
        )

    return ProcessingPlan(
        source_sha256=report.source_sha256,
        target_lufs=target_lufs,
        true_peak_dbtp=true_peak,
        steps=tuple(steps),
        requires_ab_review=requires_ab_review,
        review_intervals=_deduplicate_intervals(review_intervals),
        warnings=tuple(dict.fromkeys(warnings)),
    )
