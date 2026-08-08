from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path

from .srt import parse_srt


DISPLAY_PUNCTUATION = set("，。！？；：、‘’“”《》〈〉（）()【】[]…—-,.!?;:'\"")
DIVINE_TITLES = ("耶稣基督", "耶和华", "天父", "圣灵", "耶稣", "基督", "神", "主")
PHRASE_ENDINGS = set("。！？；.!?;\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _load(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalized_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text)).lower()
    return "".join(character for character in normalized if character.isalnum())


def _visible_count(text: str) -> int:
    return sum(
        1
        for character in str(text)
        if not character.isspace()
        and character not in DISPLAY_PUNCTUATION
        and not unicodedata.category(character).startswith("P")
    )


def _complete_review(review: dict) -> bool:
    if any(review.get(key) in (None, "", []) for key in ("cue_id", "reason", "evidence", "listened_window")):
        return False
    window = review["listened_window"]
    return (
        isinstance(window, list)
        and len(window) == 2
        and float(window[0]) >= 0
        and float(window[1]) > float(window[0])
    )


def _phrase_bounds(text: str, index: int) -> tuple[int, int]:
    start = 0
    for position in range(index - 1, -1, -1):
        if text[position] in PHRASE_ENDINGS:
            start = position + 1
            break
    end = len(text)
    for position in range(index + 1, len(text)):
        if text[position] in PHRASE_ENDINGS:
            end = position
            break
    return start, end


def _candidate_for_pronoun(text: str, pronoun_match: re.Match[str]) -> dict | None:
    pronoun_start = pronoun_match.start()
    phrase_start, phrase_end = _phrase_bounds(text, pronoun_start)
    candidates: list[tuple[int, int, str, str]] = []
    for title in DIVINE_TITLES:
        for title_match in re.finditer(re.escape(title), text[phrase_start:phrase_end]):
            title_start = phrase_start + title_match.start()
            title_end = phrase_start + title_match.end()
            if title_end <= pronoun_start:
                distance = _visible_count(text[title_end:pronoun_start])
                if distance <= 24:
                    candidates.append((distance, -len(title), title, "after_divine_title"))
            elif pronoun_match.end() <= title_start:
                distance = _visible_count(text[pronoun_match.end():title_start])
                if distance <= 12:
                    candidates.append((distance, -len(title), title, "before_divine_title"))
    if not candidates:
        return None
    distance, _, title, direction = min(candidates)
    return {
        "pronoun": pronoun_match.group(0),
        "title": title,
        "distance": distance,
        "reason": direction,
    }


def _deity_pronoun_audit(cues: list[dict], context: dict) -> dict:
    cue_by_id = {str(cue.get("id")): str(cue.get("text", "")) for cue in cues}
    invalid_plural_honorifics: list[dict] = []
    candidates: list[dict] = []
    candidate_keys: set[tuple[str, str]] = set()

    for cue in cues:
        cue_id = str(cue.get("id"))
        text = str(cue.get("text", ""))
        for match in re.finditer(r"[祢祂]们", text):
            invalid_plural_honorifics.append(
                {"cue_id": cue_id, "text": text, "form": match.group(0)}
            )
        for match in re.finditer(r"[你他](?!们)", text):
            candidate = _candidate_for_pronoun(text, match)
            if candidate is None:
                continue
            candidate.update({"cue_id": cue_id, "text": text})
            candidates.append(candidate)
            candidate_keys.add((cue_id, text))

    invalid_exceptions: list[dict] = []
    valid_exception_keys: set[tuple[str, str]] = set()
    exceptions = context.get("deity_pronoun_exceptions", [])
    if not isinstance(exceptions, list):
        invalid_exceptions.append(
            {"index": None, "reason": "deity_pronoun_exceptions must be a list"}
        )
        exceptions = []
    for index, exception in enumerate(exceptions):
        if not isinstance(exception, dict):
            invalid_exceptions.append(
                {"index": index, "reason": "exception must be an object", "value": exception}
            )
            continue
        cue_id = str(exception.get("cue_id", "")).strip()
        text = str(exception.get("text", ""))
        reason = str(exception.get("reason", "")).strip()
        key = (cue_id, text)
        problem = None
        if not cue_id or not text or not reason:
            problem = "cue_id, exact text, and semantic reason are required"
        elif cue_by_id.get(cue_id) != text:
            problem = "exception does not exactly match the current cue"
        elif key not in candidate_keys:
            problem = "exception does not correspond to a detected candidate"
        if problem:
            invalid_exceptions.append(
                {"index": index, "cue_id": cue_id, "text": text, "reason": problem}
            )
        else:
            valid_exception_keys.add(key)

    if context.get("deity_pronoun_style", "祢/祂") != "祢/祂":
        invalid_exceptions.append(
            {
                "index": None,
                "reason": "deity_pronoun_style must be 祢/祂",
                "value": context.get("deity_pronoun_style"),
            }
        )

    unreviewed_candidates = [
        candidate
        for candidate in candidates
        if (candidate["cue_id"], candidate["text"]) not in valid_exception_keys
    ]
    return {
        "invalid_plural_honorifics": invalid_plural_honorifics,
        "candidates": candidates,
        "invalid_exceptions": invalid_exceptions,
        "unreviewed_candidates": unreviewed_candidates,
    }


def _add_check(checks: list[dict], name: str, passed: bool, detail: object) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def _resolve_duration(config: dict, cues_payload: dict) -> float:
    if config.get("video_duration") is not None:
        return float(config["video_duration"])
    if cues_payload.get("video_duration") is not None:
        return float(cues_payload["video_duration"])
    if config.get("video_path"):
        from .media import probe_media

        return float(probe_media(Path(config["video_path"]))["format_duration"])
    raise ValueError("validation requires video_duration or video_path")


def _scripture_errors(cues: list[dict], payload: dict) -> list[dict]:
    entries = payload.get("entries")
    if entries is None:
        entries = []
        for item in payload.get("verses", []):
            reference = item.get("reference")
            if not reference and payload.get("reference") and item.get("verse") is not None:
                book_chapter = str(payload["reference"]).split(":", 1)[0]
                reference = f"{book_chapter}:{item['verse']}"
            text = item.get("text")
            if text is None:
                text = "".join(item.get("cues", []))
            entries.append(
                {
                    "reference": reference,
                    "text": text,
                    "spoken": item.get("spoken", True),
                }
            )
    reconstructed: dict[str, str] = {}
    for cue in cues:
        reference = cue.get("reference")
        if reference:
            reconstructed[str(reference)] = reconstructed.get(str(reference), "") + str(cue["text"])
    errors: list[dict] = []
    for entry in entries:
        reference = str(entry.get("reference", ""))
        expected = _normalized_text(str(entry.get("text", "")))
        actual = _normalized_text(reconstructed.get(reference, ""))
        spoken = bool(entry.get("spoken", True))
        if spoken and (not actual or actual != expected):
            errors.append(
                {"reference": reference, "spoken": True, "expected": expected, "actual": actual}
            )
        if not spoken and actual:
            errors.append(
                {"reference": reference, "spoken": False, "expected": "", "actual": actual}
            )
    return errors


def _manifest_errors(payload: dict) -> list[dict]:
    records = payload.get("inputs") or payload.get("files") or []
    errors: list[dict] = []
    for record in records:
        path = Path(record["path"])
        if not path.is_file():
            errors.append({"path": str(path), "error": "missing"})
            continue
        current = sha256(path)
        expected = str(record["sha256"]).upper()
        if current != expected:
            errors.append(
                {"path": str(path), "expected": expected, "current": current, "error": "hash_changed"}
            )
    return errors


def validate_delivery(config: dict) -> dict:
    srt_path = Path(config["srt_path"])
    cues_payload = _load(config["cues_path"])
    cues = list(cues_payload.get("cues", []))
    alignment = _load(config["alignment_report_path"])
    review_payload = _load(config["boundary_reviews_path"])
    context = _load(config["context_path"])
    duration = _resolve_duration(config, cues_payload)
    checks: list[dict] = []
    hard_errors: list[dict] = []

    raw = srt_path.read_bytes()
    try:
        parsed = parse_srt(raw)
        parse_error = None
    except (UnicodeDecodeError, ValueError) as error:
        parsed = []
        parse_error = str(error)
    format_ok = parse_error is None and not raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in raw
    _add_check(
        checks,
        "UTF-8 SubRip without BOM using LF",
        format_ok,
        parse_error or {"bytes": len(raw), "lf_only": b"\r\n" not in raw},
    )
    if not format_ok:
        hard_errors.append({"check": "srt_format", "detail": parse_error or "BOM or CRLF present"})

    cue_mismatches: list[dict] = []
    timeline_errors: list[dict] = []
    readability_errors: list[dict] = []
    previous_end = 0.0
    if len(parsed) != len(cues):
        cue_mismatches.append({"srt_count": len(parsed), "json_count": len(cues)})
    for index, (subtitle, cue) in enumerate(zip(parsed, cues), start=1):
        cue_id = str(cue.get("id", index))
        start = float(subtitle["start"])
        end = float(subtitle["end"])
        canonical_start = round(float(cue["start"]), 3)
        canonical_end = round(float(cue["end"]), 3)
        canonical_text = re.sub(r"\s+", "", str(cue["text"]))
        if (
            not math.isclose(start, canonical_start, abs_tol=0.0005)
            or not math.isclose(end, canonical_end, abs_tol=0.0005)
            or subtitle["text"] != canonical_text
        ):
            cue_mismatches.append(
                {
                    "cue_id": cue_id,
                    "srt": {"start": start, "end": end, "text": subtitle["text"]},
                    "json": {"start": canonical_start, "end": canonical_end, "text": canonical_text},
                }
            )
        if start < 0 or end <= start or start < previous_end - 0.0005 or end > duration + 0.0005:
            timeline_errors.append(
                {"cue_id": cue_id, "start": start, "end": end, "previous_end": previous_end}
            )
        cue_duration = end - start
        visible = _visible_count(subtitle["text"])
        cps = visible / cue_duration if cue_duration > 0 else math.inf
        if (
            len(subtitle["lines"]) > 2
            or any(len(line) > 18 for line in subtitle["lines"])
            or len(subtitle["text"]) > 32
            or cue_duration < 0.099
            or cue_duration > 8.001
            or cps > 12.01
        ):
            readability_errors.append(
                {
                    "cue_id": cue_id,
                    "lines": subtitle["lines"],
                    "duration": round(cue_duration, 3),
                    "cps": round(cps, 2),
                }
            )
        previous_end = end

    _add_check(checks, "SRT matches aligned cue JSON", not cue_mismatches, cue_mismatches or "exact")
    _add_check(checks, "monotonic nonoverlapping timeline within video", not timeline_errors, timeline_errors or "valid")
    _add_check(
        checks,
        "two lines, 18 chars/line, 32 chars/cue, 0.1-8s, <=12 chars/s",
        not readability_errors,
        readability_errors or "valid",
    )
    for name, errors in (
        ("cue_json_mismatch", cue_mismatches),
        ("timeline", timeline_errors),
        ("readability", readability_errors),
    ):
        if errors:
            hard_errors.append({"check": name, "detail": errors})

    reviews = [review for review in review_payload.get("reviews", []) if _complete_review(review)]
    reviewed_ids = {str(review["cue_id"]) for review in reviews}
    incomplete_reviews = [
        review for review in review_payload.get("reviews", []) if not _complete_review(review)
    ]
    if incomplete_reviews:
        hard_errors.append({"check": "incomplete_boundary_reviews", "detail": incomplete_reviews})
    required_review_ids = {str(risk["cue_id"]) for risk in alignment.get("risks", [])}
    missing_reviews = sorted(required_review_ids - reviewed_ids)
    _add_check(
        checks,
        "all timing risks have listening evidence",
        not missing_reviews,
        missing_reviews or f"reviewed={len(required_review_ids)}",
    )

    observed = [float(value) for value in alignment.get("observed_boundaries", [])]
    boundary_errors: list[dict] = []
    for cue in cues:
        cue_id = str(cue.get("id"))
        if cue_id in reviewed_ids:
            continue
        for key in ("start", "end"):
            value = float(cue[key])
            residual = min((abs(value - boundary) for boundary in observed), default=math.inf)
            if residual > 0.0011:
                boundary_errors.append(
                    {"cue_id": cue_id, "boundary": key, "value": value, "residual": residual}
                )
    _add_check(
        checks,
        "automatic timing lies on observed ASR boundaries",
        not boundary_errors,
        boundary_errors or "all automatic boundaries within 1.1ms",
    )
    if boundary_errors:
        hard_errors.append({"check": "unobserved_boundaries", "detail": boundary_errors})

    full_text = "".join(str(cue.get("text", "")) for cue in cues)
    missing_terms = [term for term in context.get("required_terms", []) if term not in full_text]
    forbidden_terms = [term for term in context.get("forbidden_terms", []) if term in full_text]
    term_errors = {"missing": missing_terms, "forbidden_found": forbidden_terms}
    _add_check(checks, "context-specific required/forbidden terms", not missing_terms and not forbidden_terms, term_errors)
    if missing_terms or forbidden_terms:
        hard_errors.append({"check": "context_terms", "detail": term_errors})

    deity_audit = _deity_pronoun_audit(cues, context)
    deity_hard_errors = {
        "invalid_plural_honorifics": deity_audit["invalid_plural_honorifics"],
        "invalid_exceptions": deity_audit["invalid_exceptions"],
    }
    missing_deity_reviews = sorted(
        {candidate["cue_id"] for candidate in deity_audit["unreviewed_candidates"]}
    )
    deity_ok = not any(deity_hard_errors.values()) and not missing_deity_reviews
    _add_check(
        checks,
        "divine singular pronouns use 祢/祂 with audited human-reference exceptions",
        deity_ok,
        {
            **deity_hard_errors,
            "unreviewed_candidates": deity_audit["unreviewed_candidates"],
        }
        if not deity_ok
        else f"candidates={len(deity_audit['candidates'])}, all resolved",
    )
    if any(deity_hard_errors.values()):
        hard_errors.append({"check": "deity_pronouns", "detail": deity_hard_errors})

    scripture_errors: list[dict] = []
    if config.get("scripture_reference_path"):
        scripture_errors = _scripture_errors(cues, _load(config["scripture_reference_path"]))
    _add_check(
        checks,
        "spoken scripture matches canonical reference and unspoken text is absent",
        not scripture_errors,
        scripture_errors or "not supplied or exact",
    )
    if scripture_errors:
        hard_errors.append({"check": "scripture", "detail": scripture_errors})

    manifest_errors: list[dict] = []
    if config.get("manifest_path"):
        manifest_errors = _manifest_errors(_load(config["manifest_path"]))
    _add_check(checks, "immutable source hashes unchanged", not manifest_errors, manifest_errors or "not supplied or unchanged")
    if manifest_errors:
        hard_errors.append({"check": "source_hashes", "detail": manifest_errors})

    status = (
        "FAIL"
        if hard_errors
        else ("REVIEW_REQUIRED" if missing_reviews or missing_deity_reviews else "PASS")
    )
    return {
        "status": status,
        "subtitle": str(srt_path.resolve()),
        "subtitle_sha256": sha256(srt_path),
        "video_duration": duration,
        "cue_count": len(parsed),
        "first_start": parsed[0]["start"] if parsed else None,
        "last_end": parsed[-1]["end"] if parsed else None,
        "hard_failures": len(hard_errors),
        "hard_errors": hard_errors,
        "missing_boundary_reviews": missing_reviews,
        "deity_pronoun_candidates": deity_audit["candidates"],
        "missing_deity_pronoun_reviews": missing_deity_reviews,
        "checks": checks,
    }
