from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
import json
import os
from pathlib import Path
import types
from typing import Any, Mapping, TypeVar, Union, get_args, get_origin, get_type_hints


T = TypeVar("T", bound="JsonRecord")


def _coerce(annotation: Any, value: Any) -> Any:
    if value is None:
        return None

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in (Union, types.UnionType):
        for option in args:
            if option is type(None):
                continue
            try:
                return _coerce(option, value)
            except (TypeError, ValueError):
                continue
        return value

    if origin is tuple:
        item_type = args[0] if args else Any
        return tuple(_coerce(item_type, item) for item in value)

    if origin is list:
        item_type = args[0] if args else Any
        return [_coerce(item_type, item) for item in value]

    if origin in (dict, Mapping):
        key_type, value_type = args if args else (Any, Any)
        return {
            _coerce(key_type, key): _coerce(value_type, item)
            for key, item in value.items()
        }

    if isinstance(annotation, type) and is_dataclass(annotation):
        if issubclass(annotation, JsonRecord):
            return annotation.from_dict(value)
        return annotation(**value)

    if annotation in (int, float, str, bool):
        return annotation(value)

    return value


@dataclass(frozen=True)
class JsonRecord:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls: type[T], data: Mapping[str, Any]) -> T:
        hints = get_type_hints(cls)
        values = {}
        for field in fields(cls):
            if field.name not in data:
                continue
            values[field.name] = _coerce(hints.get(field.name, Any), data[field.name])
        return cls(**values)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.tmp")
        temporary.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, path)


@dataclass(frozen=True)
class PacketTiming(JsonRecord):
    pts: int | None
    pts_time: float | None
    duration: int | None
    duration_time: float | None


@dataclass(frozen=True)
class StreamSummary(JsonRecord):
    index: int
    codec_type: str
    codec_name: str | None
    time_base: str | None
    start_pts: int | None
    start_time: float | None
    duration_ts: int | None
    duration: float | None
    tags: dict[str, str]
    disposition: dict[str, int]


@dataclass(frozen=True)
class SourceManifest(JsonRecord):
    source_path: str
    source_sha256: str
    format_name: str
    format_duration: float | None
    audio_ordinal: int
    stream_index: int
    codec_name: str
    sample_rate: int
    channels: int
    channel_layout: str | None
    time_base: str
    start_pts: int | None
    start_time: float
    duration_ts: int | None
    duration_seconds: float
    decoded_sample_count: int
    first_packet: PacketTiming | None
    last_packet: PacketTiming | None
    packet_gaps: tuple[tuple[float, float], ...]
    video_streams: tuple[StreamSummary, ...]
    other_streams: tuple[StreamSummary, ...]
    non_target_stream_hashes: dict[str, str]
    tags: dict[str, str]
    disposition: dict[str, int]


@dataclass(frozen=True)
class IssueFinding(JsonRecord):
    kind: str
    start: float
    end: float
    confidence: float
    metrics: dict[str, float]
    reason: str


@dataclass(frozen=True)
class ChannelMetric(JsonRecord):
    channel: int
    rms_dbfs: float
    noise_dbfs: float | None
    presence_ratio: float
    clarity_score: float


@dataclass(frozen=True)
class AnalysisReport(JsonRecord):
    source_sha256: str
    integrated_lufs: float | None
    true_peak_dbtp: float | None
    loudness_range_lu: float | None
    window_loudness: tuple[dict[str, float], ...]
    vad_backend: str
    active_speech_intervals: tuple[tuple[float, float], ...]
    speech_p10_lufs: float | None
    speech_p90_lufs: float | None
    speech_spread_lu: float | None
    findings: tuple[IssueFinding, ...]
    channel_metrics: tuple[ChannelMetric, ...]
    capabilities: dict[str, bool]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ProcessingStep(JsonRecord):
    kind: str
    tool: str
    parameters: dict[str, Any]
    evidence: tuple[IssueFinding, ...]
    reason: str
    confidence: float


@dataclass(frozen=True)
class ProcessingPlan(JsonRecord):
    source_sha256: str
    target_lufs: float
    true_peak_dbtp: float
    steps: tuple[ProcessingStep, ...]
    requires_ab_review: bool
    review_intervals: tuple[tuple[float, float], ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ProcessResult(JsonRecord):
    master_path: str
    stage_paths: tuple[str, ...]
    commands: tuple[tuple[str, ...], ...]
    stage_sample_counts: tuple[int, ...]
    ab_sample_paths: tuple[str, ...]


@dataclass(frozen=True)
class CloudRequest(JsonRecord):
    input_path: str
    duration_hours: float
    target_lufs: float
    true_peak_dbtp: float
    cloud_mode: str
    upload_consent: bool
    output_path: str


@dataclass(frozen=True)
class LatencyResult(JsonRecord):
    global_offset_samples: int
    anchor_offsets_samples: tuple[int, ...]
    drift_slope_samples: float
    confidence: float


@dataclass(frozen=True)
class VerificationItem(JsonRecord):
    name: str
    passed: bool
    expected: str
    actual: str
    evidence: str


@dataclass(frozen=True)
class VerificationReport(JsonRecord):
    source_path: str
    output_path: str
    passed: bool
    items: tuple[VerificationItem, ...]
    warnings: tuple[str, ...]
