from __future__ import annotations

import math
import statistics
import unicodedata
from collections import OrderedDict
from collections.abc import Iterable


def normalize_characters(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", str(text)).lower()
    return [character for character in normalized if character.isalnum()]


def timed_source_characters(words: Iterable[dict], source_label: str) -> list[dict]:
    characters: list[dict] = []
    for word in words:
        normalized = normalize_characters(str(word.get("word", "")))
        if not normalized:
            continue
        start = float(word["start"])
        end = float(word["end"])
        if end < start:
            raise ValueError(f"ASR word has a negative interval: {word!r}")
        duration = end - start
        for index, character in enumerate(normalized):
            characters.append(
                {
                    "character": character,
                    "start": start + duration * index / len(normalized),
                    "end": start + duration * (index + 1) / len(normalized),
                    "source": source_label,
                    "segment_id": word.get("segment_id"),
                    "probability": word.get("probability"),
                }
            )
    return characters


def _global_alignment(target: list[str], source: list[str]) -> tuple[list[int | None], int]:
    target_count = len(target)
    source_count = len(source)
    costs = [[0] * (source_count + 1) for _ in range(target_count + 1)]
    operations = [[""] * (source_count + 1) for _ in range(target_count + 1)]
    for target_index in range(1, target_count + 1):
        costs[target_index][0] = target_index
        operations[target_index][0] = "insert"
    for source_index in range(1, source_count + 1):
        costs[0][source_index] = source_index
        operations[0][source_index] = "delete"

    for target_index in range(1, target_count + 1):
        for source_index in range(1, source_count + 1):
            is_match = target[target_index - 1] == source[source_index - 1]
            choices = [
                (
                    costs[target_index - 1][source_index - 1] + (0 if is_match else 1),
                    0,
                    "match" if is_match else "substitute",
                ),
                (costs[target_index - 1][source_index] + 1, 1, "insert"),
                (costs[target_index][source_index - 1] + 1, 2, "delete"),
            ]
            best_cost, _, operation = min(choices)
            costs[target_index][source_index] = best_cost
            operations[target_index][source_index] = operation

    mapping: list[int | None] = [None] * target_count
    matches = 0
    target_index = target_count
    source_index = source_count
    while target_index or source_index:
        operation = operations[target_index][source_index]
        if operation in {"match", "substitute"}:
            mapping[target_index - 1] = source_index - 1
            if operation == "match":
                matches += 1
            target_index -= 1
            source_index -= 1
        elif operation == "insert":
            target_index -= 1
        elif operation == "delete":
            source_index -= 1
        else:
            raise RuntimeError("alignment backtrace reached an invalid state")
    return mapping, matches


def _fill_inserted_mappings(mapping: list[int | None], source_count: int) -> list[int]:
    if source_count <= 0:
        raise ValueError("cannot align subtitles without timed ASR characters")
    result = list(mapping)
    previous: int | None = None
    for index, value in enumerate(result):
        if value is not None:
            previous = value
        elif previous is not None:
            result[index] = previous
    following: int | None = None
    for index in range(len(result) - 1, -1, -1):
        value = result[index]
        if value is not None:
            following = value
        elif following is not None:
            result[index] = following
    return [
        0 if value is None else min(max(int(value), 0), source_count - 1)
        for value in result
    ]


def _align_group(cues: list[dict], characters: list[dict]) -> dict:
    target: list[str] = []
    cue_ranges: list[tuple[int, int]] = []
    for cue in cues:
        start = len(target)
        target.extend(normalize_characters(str(cue["text"])))
        cue_ranges.append((start, len(target)))
    if not target:
        raise ValueError("cannot align an empty reviewed cue group")
    if not characters:
        raise ValueError("cannot align reviewed cues without timed ASR characters")

    mapping, matches = _global_alignment(target, [item["character"] for item in characters])
    filled = _fill_inserted_mappings(mapping, len(characters))
    aligned_cues: list[dict] = []
    for cue, (target_start, target_end) in zip(cues, cue_ranges):
        indexes = filled[target_start:target_end]
        if not indexes:
            raise ValueError(f"cue {cue.get('id')} contains no alignable characters")
        first = min(indexes)
        last = max(indexes)
        aligned = dict(cue)
        aligned["start"] = round(float(characters[first]["start"]), 3)
        aligned["end"] = round(float(characters[last]["end"]), 3)
        aligned_cues.append(aligned)
    return {
        "cues": aligned_cues,
        "matched_ratio": matches / max(len(target), 1),
        "target_characters": len(target),
        "source_characters": len(characters),
    }


def _segments(payload: dict) -> list[dict]:
    if "segments" in payload:
        return list(payload.get("segments", []))
    return [
        segment
        for region in payload.get("regions", [])
        for segment in region.get("segments", [])
    ]


def _flatten_words(payload: dict) -> list[dict]:
    words: list[dict] = []
    for segment in _segments(payload):
        for word in segment.get("words", []):
            item = dict(word)
            item["segment_id"] = segment.get("id")
            words.append(item)
    return sorted(words, key=lambda word: (float(word["start"]), float(word["end"])))


def _group_cues(cues: list[dict]) -> list[tuple[str, list[int]]]:
    grouped: OrderedDict[str, list[int]] = OrderedDict()
    for index, cue in enumerate(cues):
        cue_id = str(cue.get("id", "")).strip()
        if not cue_id:
            raise ValueError(f"reviewed cue {index + 1} is missing a stable id")
        group = str(cue.get("alignment_group") or cue_id)
        grouped.setdefault(group, []).append(index)
    return list(grouped.items())


def _window_for_group(
    group_cues: list[dict],
    primary_payload: dict,
) -> tuple[float, float]:
    source_ids = {
        int(source_id)
        for cue in group_cues
        for source_id in cue.get("source_segment_ids", [])
    }
    primary_segments = _segments(primary_payload)
    matched_segments = [
        segment for segment in primary_segments if int(segment.get("id", -1)) in source_ids
    ]
    words = [word for segment in matched_segments for word in segment.get("words", [])]
    if words:
        return (
            min(float(word["start"]) for word in words),
            max(float(word["end"]) for word in words),
        )

    explicit = [cue["alignment_window"] for cue in group_cues if cue.get("alignment_window")]
    if explicit:
        return (
            min(float(window[0]) for window in explicit),
            max(float(window[1]) for window in explicit),
        )
    return (
        min(float(cue["start"]) for cue in group_cues),
        max(float(cue["end"]) for cue in group_cues),
    )


def _candidate_words(
    label: str,
    payload: dict,
    group_cues: list[dict],
    window: tuple[float, float],
) -> list[dict]:
    source_ids = {
        int(source_id)
        for cue in group_cues
        for source_id in cue.get("source_segment_ids", [])
    }
    if label == "primary" and source_ids:
        exact = [
            word
            for segment in _segments(payload)
            if int(segment.get("id", -1)) in source_ids
            for word in segment.get("words", [])
        ]
        if exact:
            return sorted(exact, key=lambda word: (float(word["start"]), float(word["end"])))
    start, end = window
    return [
        word
        for word in _flatten_words(payload)
        if start - 0.20
        <= (float(word["start"]) + float(word["end"])) / 2
        <= end + 0.20
    ]


def _validate_manual_review(review: dict) -> None:
    for key in ("cue_id", "reason", "evidence", "listened_window"):
        if review.get(key) in (None, "", []):
            raise ValueError(f"manual boundary review is missing {key}")
    window = review["listened_window"]
    if not isinstance(window, list) or len(window) != 2 or float(window[1]) <= float(window[0]):
        raise ValueError("manual boundary review has an invalid listened_window")


def _add_risk(risks: list[dict], cue_id: str, reason: str, detail: dict) -> None:
    key = (cue_id, reason)
    if any((risk["cue_id"], risk["reason"]) == key for risk in risks):
        return
    risks.append({"cue_id": cue_id, "reason": reason, "detail": detail})


def retime_reviewed_cues(
    reviewed: dict,
    asr_sources: dict[str, dict],
    manual_reviews: list[dict] | None = None,
    *,
    low_ratio: float = 0.65,
    shift_threshold: float = 1.0,
    max_overlap: float = 0.8,
) -> dict:
    if not asr_sources:
        raise ValueError("at least one word-timestamp ASR source is required")
    cues = [dict(cue) for cue in reviewed.get("cues", [])]
    if not cues:
        raise ValueError("reviewed cue payload is empty")
    ids = [str(cue.get("id", "")) for cue in cues]
    if len(ids) != len(set(ids)):
        raise ValueError("reviewed cue ids must be unique")

    primary_label = "primary" if "primary" in asr_sources else next(iter(asr_sources))
    primary_payload = asr_sources[primary_label]
    output = [dict(cue) for cue in cues]
    group_reports: list[dict] = []
    risks: list[dict] = []
    observed_boundaries = {
        round(float(character[key]), 6)
        for label, payload in asr_sources.items()
        for character in timed_source_characters(_flatten_words(payload), label)
        for key in ("start", "end")
    }

    for group_name, indexes in _group_cues(cues):
        group_cues = [cues[index] for index in indexes]
        window = _window_for_group(group_cues, primary_payload)
        alternatives: dict[str, dict] = {}
        for label, payload in asr_sources.items():
            words = _candidate_words(label, payload, group_cues, window)
            if not words:
                continue
            characters = timed_source_characters(words, label)
            if characters:
                alternatives[label] = _align_group(group_cues, characters)
        if not alternatives:
            raise ValueError(f"alignment group {group_name!r} has no timed ASR candidates")
        label_order = {label: index for index, label in enumerate(asr_sources)}
        chosen_label, chosen = max(
            alternatives.items(),
            key=lambda item: (item[1]["matched_ratio"], -label_order[item[0]]),
        )
        for index, aligned in zip(indexes, chosen["cues"]):
            aligned["timing_source"] = chosen_label
            output[index] = aligned
        group_report = {
            "alignment_group": group_name,
            "cue_ids": [str(cue["id"]) for cue in group_cues],
            "timing_source": chosen_label,
            "matched_ratio": round(float(chosen["matched_ratio"]), 4),
            "alternative_ratios": {
                label: round(float(result["matched_ratio"]), 4)
                for label, result in alternatives.items()
            },
            "source_window": [round(window[0], 3), round(window[1], 3)],
        }
        group_reports.append(group_report)
        if float(chosen["matched_ratio"]) < low_ratio:
            for cue in group_cues:
                _add_risk(
                    risks,
                    str(cue["id"]),
                    "low_match_ratio",
                    {"matched_ratio": round(float(chosen["matched_ratio"]), 4), "group": group_name},
                )

    manual_audit: list[dict] = []
    index_by_id = {str(cue["id"]): index for index, cue in enumerate(output)}
    for review in manual_reviews or []:
        _validate_manual_review(review)
        cue_id = str(review["cue_id"])
        if cue_id not in index_by_id:
            raise ValueError(f"manual boundary review references unknown cue id: {cue_id}")
        cue = output[index_by_id[cue_id]]
        before = {key: cue.get(key) for key in ("start", "end", "text")}
        for key in ("start", "end", "text"):
            if key in review:
                cue[key] = review[key]
        cue["timing_source"] = "manual_review"
        manual_audit.append(
            {
                **review,
                "before": before,
                "after": {key: cue.get(key) for key in ("start", "end", "text")},
            }
        )

    for old, new in zip(cues, output):
        cue_id = str(new["id"])
        start_shift = round(float(new["start"]) - float(old["start"]), 3)
        end_shift = round(float(new["end"]) - float(old["end"]), 3)
        if abs(start_shift) > shift_threshold:
            _add_risk(risks, cue_id, "start_shift_over_1s", {"shift": start_shift})
        if abs(end_shift) > shift_threshold:
            _add_risk(risks, cue_id, "end_shift_over_1s", {"shift": end_shift})
        role = str(new.get("boundary_role", ""))
        if role in {"prayer_start", "prayer_end"}:
            _add_risk(risks, cue_id, "prayer_boundary", {"role": role})

    _add_risk(risks, str(output[0]["id"]), "first_cue", {})
    _add_risk(risks, str(output[-1]["id"]), "last_cue", {})
    scripture_indexes = [index for index, cue in enumerate(output) if cue.get("reference")]
    if scripture_indexes:
        for index in {scripture_indexes[0], scripture_indexes[-1]}:
            _add_risk(
                risks,
                str(output[index]["id"]),
                "scripture_boundary",
                {"reference": output[index].get("reference")},
            )

    overlap_adjustments: list[dict] = []
    for index in range(1, len(output)):
        previous = output[index - 1]
        current = output[index]
        overlap = float(previous["end"]) - float(current["start"])
        if overlap <= 0.0005:
            continue
        if overlap > max_overlap + 0.0005:
            raise ValueError(
                f"cues {previous['id']} and {current['id']} overlap by {overlap:.3f}s, "
                f"above the {max_overlap:.3f}s review threshold"
            )
        boundary = round(float(current["start"]), 3)
        if boundary <= float(previous["start"]):
            raise ValueError(f"trimming cue {previous['id']} would create a nonpositive interval")
        previous["end"] = boundary
        adjustment = {
            "previous_cue_id": str(previous["id"]),
            "next_cue_id": str(current["id"]),
            "overlap": round(overlap, 3),
            "boundary": boundary,
        }
        overlap_adjustments.append(adjustment)
        _add_risk(risks, str(previous["id"]), "overlap_adjustment", adjustment)

    video_duration = float(reviewed.get("video_duration", math.inf))
    for cue in output:
        if float(cue["start"]) < 0 or float(cue["end"]) <= float(cue["start"]):
            raise ValueError(f"cue {cue['id']} has an invalid final interval")
        if float(cue["end"]) > video_duration + 0.0005:
            raise ValueError(f"cue {cue['id']} exceeds video duration")

    ratios = [float(group["matched_ratio"]) for group in group_reports]
    return {
        "video_duration": reviewed.get("video_duration"),
        "language": reviewed.get("language", "zh-Hans"),
        "cues": output,
        "groups": group_reports,
        "risks": risks,
        "manual_reviews": manual_audit,
        "overlap_adjustments": overlap_adjustments,
        "observed_boundaries": sorted(observed_boundaries),
        "statistics": {
            "cue_count": len(output),
            "group_count": len(group_reports),
            "matched_ratio_min": round(min(ratios), 4),
            "matched_ratio_median": round(statistics.median(ratios), 4),
            "risk_count": len(risks),
            "overlap_adjustment_count": len(overlap_adjustments),
        },
    }
