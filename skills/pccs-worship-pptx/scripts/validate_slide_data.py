#!/usr/bin/env python3
"""Validate normalized PCCS worship slide-plan data before PPTX generation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from scripture_contract import validate_verse_metadata
from validate_wide_slide_data import validate as validate_wide


LYRIC_PUNCTUATION = re.compile(r"[，。！？；：、,.!?;:\"'“”‘’（）()《》【】\[\]—…]")
REPEAT_SHORTHAND = re.compile(r"\*\s*\d+")
VAGUE_SHORTHAND = ("同上", "再唱", "重复", "repeat", "again")
SONG_ROLES = {"song_first", "song_continuation"}
BODY_ROLES = SONG_ROLES | {"scripture"}
ALLOWED_ROLES = BODY_ROLES | {"transition"}
SECTION_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def validate(payload: Any) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["Slide data must be a JSON object."], {}

    profile = payload.get("template_profile")
    if profile in {"wide-v3", "legacy"}:
        errors, summary = validate_wide(payload)
        for group in ("scriptures", "pages"):
            for index, record in enumerate(payload.get(group, []), 1):
                if isinstance(record, dict) and (group == "scriptures" or record.get("role") == "scripture"):
                    errors.extend(validate_verse_metadata(record, f"{group}[{index}]"))
        summary["status"] = "fail" if errors else "pass"
        return errors, summary
    if profile not in {None, "legacy-refined"}:
        return ["Unknown template_profile"], {"status": "fail"}

    typography = payload.get("typography", {})
    if not isinstance(typography, dict):
        errors.append("typography must be an object.")
        typography = {}
    lyric_pt = typography.get("lyric_font_pt", 40)
    title_pt = typography.get("title_font_pt", 44)
    for field, value in (("lyric_font_pt", lyric_pt), ("title_font_pt", title_pt)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value < float("inf"):
            errors.append(f"typography.{field} must be a finite positive number.")
    if (lyric_pt != 40 or title_pt != 44) and not str(typography.get("override_reason") or "").strip():
        errors.append("typography.override_reason must record the explicit user size override.")

    songs = payload.get("songs")
    scriptures = payload.get("scriptures", [])
    pages = payload.get("pages")
    if not isinstance(songs, list) or not songs:
        errors.append("songs must be a non-empty list.")
        songs = []
    if not isinstance(pages, list) or not pages:
        errors.append("pages must be a non-empty list.")
        pages = []
    if not isinstance(scriptures, list):
        errors.append("scriptures must be a list when supplied.")
        scriptures = []

    song_by_id: dict[str, dict[str, Any]] = {}
    expected_sequences: dict[str, list[str]] = {}

    for position, song in enumerate(songs, start=1):
        label = f"songs[{position}]"
        if not isinstance(song, dict):
            errors.append(f"{label} must be an object.")
            continue
        song_id = song.get("id")
        if not isinstance(song_id, str) or not song_id.strip():
            errors.append(f"{label}.id is required.")
            continue
        if song_id in song_by_id:
            errors.append(f"{label}.id {song_id!r} is duplicated.")
            continue
        title = song.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{label}.title is required.")
        song_by_id[song_id] = song

        if "credit_lines" in song:
            credits = song["credit_lines"]
            if not isinstance(credits, list) or not credits or any(not isinstance(line, str) or not line.strip() for line in credits):
                errors.append(f"{label}.credit_lines must be a non-empty list of attribution text.")

        expanded = song.get("arrangement_expanded")
        if not isinstance(expanded, list) or not expanded:
            errors.append(f"{label}.arrangement_expanded must be a non-empty list.")
            expected_sequences[song_id] = []
            continue
        normalized: list[str] = []
        for section in expanded:
            if not isinstance(section, str):
                errors.append(
                    f"{label}.arrangement_expanded section entries must be strings."
                )
                normalized.append("")
                continue
            token = section.strip()
            lowered = token.lower()
            if (
                not token
                or not SECTION_TOKEN.fullmatch(token)
                or REPEAT_SHORTHAND.search(token)
                or any(item in lowered for item in VAGUE_SHORTHAND)
            ):
                errors.append(
                    f"{label}.arrangement_expanded must be fully expanded; invalid entry {token!r}."
                )
            normalized.append(token)
        expected_sequences[song_id] = normalized

    scripture_by_id: dict[str, dict[str, Any]] = {}
    scripture_source_line_count = 0
    for position, scripture in enumerate(scriptures, start=1):
        label = f"scriptures[{position}]"
        if not isinstance(scripture, dict):
            errors.append(f"{label} must be an object.")
            continue
        errors.extend(validate_verse_metadata(scripture, label))
        scripture_id = scripture.get("id")
        if not isinstance(scripture_id, str) or not scripture_id.strip():
            errors.append(f"{label}.id is required.")
            continue
        if scripture_id in scripture_by_id:
            errors.append(f"{label}.id {scripture_id!r} is duplicated.")
            continue

        source_lines = scripture.get("source_lines")
        if not isinstance(source_lines, list) or not source_lines:
            errors.append(f"{label}.source_lines must be a non-empty list.")
            source_lines = []
        else:
            for line_number, line in enumerate(source_lines, start=1):
                if not isinstance(line, str) or not line.strip():
                    errors.append(
                        f"{label}.source_lines[{line_number}] must be non-empty text."
                    )
        if scripture.get("preserve_line_breaks") is not True:
            errors.append(f"{label}.preserve_line_breaks must be true.")
        if "single_slide" in scripture and not isinstance(
            scripture.get("single_slide"), bool
        ):
            errors.append(f"{label}.single_slide must be true or false when supplied.")

        scripture_by_id[scripture_id] = scripture
        scripture_source_line_count += len(source_lines)

    performance_pages: dict[str, list[tuple[tuple[int, ...], str, int, str]]] = {
        song_id: [] for song_id in song_by_id
    }
    page_song_ids: list[str] = []
    scripture_page_lines: dict[str, list[str]] = {
        scripture_id: [] for scripture_id in scripture_by_id
    }
    scripture_page_counts: Counter[str] = Counter()
    scripture_page_positions: dict[str, list[int]] = {}
    scripture_sizes: dict[str, set[tuple]] = {}

    for position, page in enumerate(pages, start=1):
        label = f"pages[{position}]"
        if not isinstance(page, dict):
            errors.append(f"{label} must be an object.")
            continue

        role = page.get("role")
        if "credit_lines" in page:
            credits = page["credit_lines"]
            if not isinstance(credits, list) or not credits or any(not isinstance(line, str) or not line.strip() for line in credits):
                errors.append(f"{label}.credit_lines must be a non-empty list of attribution text.")
        if role not in ALLOWED_ROLES:
            errors.append(f"{label}.role must be one of {sorted(ALLOWED_ROLES)}.")
        lines = page.get("lines")
        if not isinstance(lines, list) or not lines:
            errors.append(f"{label}.lines must be a non-empty list.")
            lines = []
        if role in SONG_ROLES and len(lines) > 3:
            errors.append(f"{label} must contain at most 3 lines.")
        if role == "song_first" and len(lines) > 2 and lyric_pt == 40 and title_pt == 44:
            errors.append(f"{label}: the default first-page grid fits at most 2 lyric lines in the upper half.")

        font = page.get("font")
        if role in SONG_ROLES and font != "KaiTi":
            errors.append(f"{label}.font must be KaiTi.")
        if role in SONG_ROLES and page.get("body_font_pt") != lyric_pt:
            errors.append(f"{label}.body_font_pt must be exactly {lyric_pt}.")
        if role == "scripture":
            errors.extend(validate_verse_metadata(page, label))
            override = page.get("style_override_reason")
            has_override = isinstance(override, str) and bool(override.strip())
            if override is not None and not has_override:
                errors.append(f"{label}.style_override_reason must record an explicit user instruction.")
            if not isinstance(font, str) or not font.strip():
                errors.append(f"{label}.font must be non-empty text.")
            elif font != "SimSun" and not has_override:
                errors.append(f"{label}.font must be SimSun for formal scripture.")
            alignment = page.get("alignment")
            if alignment not in ("left", "center", "right", "justify"):
                errors.append(f"{label}.alignment is invalid.")
            if alignment != "left" and not has_override:
                errors.append(f"{label}.alignment must be left for formal scripture.")
            body_font_pt = page.get("body_font_pt")
            if (
                not isinstance(body_font_pt, (int, float))
                or isinstance(body_font_pt, bool)
                or not 0 < body_font_pt < float("inf")
                or (body_font_pt > 36 and not has_override)
            ):
                errors.append(f"{label}.body_font_pt must be a positive number at most 36.")
            else:
                scripture_sizes.setdefault(str(page.get("scripture_id")), set()).add((str(font), body_font_pt, str(alignment), str(page.get("body_shadow", False))))
        if role == "song_first" and page.get("title_font_pt") != title_pt:
            errors.append(f"{label}.title_font_pt must be exactly {title_pt}.")

        for line_number, raw_line in enumerate(lines, start=1):
            if not isinstance(raw_line, str) or not raw_line.strip():
                errors.append(f"{label}.lines[{line_number}] must be non-empty text.")
                continue
            if role in SONG_ROLES and "  " in raw_line:
                errors.append(
                    f"{label}.lines[{line_number}] contains repeated spaces; use single spaces."
                )
            if role in SONG_ROLES and LYRIC_PUNCTUATION.search(raw_line):
                errors.append(
                    f"{label}.lines[{line_number}] contains lyric punctuation."
                )

        if role == "scripture":
            scripture_id = page.get("scripture_id")
            if scripture_id not in scripture_by_id:
                errors.append(
                    f"{label}.scripture_id does not reference a declared scripture source."
                )
            else:
                scripture_page_counts[scripture_id] += 1
                scripture_page_lines[scripture_id].extend(lines)
                scripture_page_positions.setdefault(scripture_id, []).append(position)

        if role in SONG_ROLES:
            song_id = page.get("song_id")
            section = page.get("section_code")
            performance_index = page.get("performance_index")
            performance_indexes = page.get("performance_indexes")
            if song_id not in song_by_id:
                errors.append(f"{label}.song_id does not reference a known song.")
                continue
            page_song_ids.append(song_id)
            expected_title = song_by_id[song_id].get("title")
            if page.get("title") != expected_title:
                errors.append(
                    f"{label}.title must match the referenced song title {expected_title!r}."
                )
            if (
                not isinstance(section, str)
                or not section.strip()
                or not SECTION_TOKEN.fullmatch(section.strip())
            ):
                errors.append(
                    f"{label}.section_code must be a valid section token for song pages."
                )
                continue
            indexes: tuple[int, ...]
            if performance_indexes is not None:
                if performance_index is not None:
                    errors.append(
                        f"{label} must use performance_index or performance_indexes, not both."
                    )
                    continue
                if (
                    not isinstance(performance_indexes, list)
                    or len(performance_indexes) < 2
                    or any(
                        not isinstance(item, int)
                        or isinstance(item, bool)
                        or item < 1
                        for item in performance_indexes
                    )
                ):
                    errors.append(
                        f"{label}.performance_indexes must contain at least two positive integers."
                    )
                    continue
                indexes = tuple(performance_indexes)
                if any(right != left + 1 for left, right in zip(indexes, indexes[1:])):
                    errors.append(
                        f"{label}.performance_indexes must be strictly consecutive."
                    )
                if section.strip().lower() != "end":
                    errors.append(
                        f"{label}.performance_indexes grouping is supported only for End sections."
                    )
                if len(lines) != len(indexes) or len(set(lines)) != 1:
                    errors.append(
                        f"{label} grouped End lines must be identical and match the number of performance_indexes."
                    )
            else:
                if (
                    not isinstance(performance_index, int)
                    or isinstance(performance_index, bool)
                    or performance_index < 1
                ):
                    errors.append(
                        f"{label}.performance_index must be a positive integer."
                    )
                    continue
                indexes = (performance_index,)
            performance_pages[song_id].append(
                (indexes, section.strip(), position, role)
            )

    for scripture_id, scripture in scripture_by_id.items():
        expected_lines = scripture.get("source_lines")
        if not isinstance(expected_lines, list):
            expected_lines = []
        actual_lines = scripture_page_lines.get(scripture_id, [])
        if actual_lines != expected_lines:
            errors.append(
                f"Scripture {scripture_id!r} pages must preserve exact text, order, and line boundaries from source_lines."
            )
        if scripture.get("single_slide") is True and scripture_page_counts.get(
            scripture_id, 0
        ) != 1:
            errors.append(
                f"Scripture {scripture_id!r} is marked single_slide and must use exactly one scripture page."
            )

    song_blocks: list[str] = []
    for song_id in page_song_ids:
        if not song_blocks or song_blocks[-1] != song_id:
            song_blocks.append(song_id)
    expected_song_order = list(song_by_id)
    if song_blocks != expected_song_order:
        errors.append(
            f"Global song order {song_blocks} does not match declared song order {expected_song_order}."
        )

    actual_sequences: dict[str, list[str]] = {}
    for scripture_id, sizes in scripture_sizes.items():
        if len(sizes) > 1:
            errors.append(f"Scripture {scripture_id!r} body font must be uniform across its pages.")

    song_ids = list(song_by_id)
    for scripture_id, source in scripture_by_id.items():
        placement = source.get("position")
        if placement is None:
            continue
        match = re.fullmatch(r"(before|after)_song_([1-9]\d*)", str(placement))
        if not match or int(match[2]) > len(song_ids):
            errors.append(f"Scripture {scripture_id!r}.position must name before_song_N or after_song_N in this song list.")
            continue
        anchor = song_ids[int(match[2]) - 1]
        anchor_pages = [i for i, p in enumerate(pages, 1) if isinstance(p, dict) and p.get("role") in SONG_ROLES and p.get("song_id") == anchor]
        reading_pages = scripture_page_positions.get(scripture_id, [])
        if anchor_pages and reading_pages:
            wrong = max(reading_pages) >= min(anchor_pages) if match[1] == "before" else min(reading_pages) <= max(anchor_pages)
            if wrong:
                errors.append(f"Scripture {scripture_id!r} page position does not match {placement}.")

    for song_id, entries in performance_pages.items():
        first_page_count = sum(1 for entry in entries if entry[3] == "song_first")
        if first_page_count != 1:
            errors.append(
                f"Song {song_id!r} must contain exactly one song_first page; found {first_page_count}."
            )
        if entries and entries[0][3] != "song_first":
            errors.append(f"Song {song_id!r} must begin with a song_first page.")
        sequence: list[str] = []
        previous_index = 0
        sections_by_index: dict[int, str] = {}
        for performance_indexes, section, page_position, _ in entries:
            for performance_index in performance_indexes:
                if performance_index in sections_by_index:
                    if section != sections_by_index[performance_index]:
                        errors.append(
                            f"pages[{page_position}] changes section_code within performance_index {performance_index}."
                        )
                    continue
                if performance_index != previous_index + 1:
                    errors.append(
                        f"pages[{page_position}] has non-consecutive performance_index {performance_index}."
                    )
                sequence.append(section)
                sections_by_index[performance_index] = section
                previous_index = performance_index
        actual_sequences[song_id] = sequence
        if sequence != expected_sequences.get(song_id, []):
            errors.append(
                f"Song {song_id!r} page sequence {sequence} does not match expanded arrangement "
                f"{expected_sequences.get(song_id, [])}."
            )

    summary = {
        "status": "pass" if not errors else "fail",
        "song_count": len(songs),
        "scripture_count": len(scriptures),
        "scripture_source_lines": scripture_source_line_count,
        "page_count": len(pages),
        "performance_sections": sum(len(items) for items in actual_sequences.values()),
    }
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slide_json", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.slide_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Unable to read slide JSON: {exc}", file=sys.stderr)
        return 2

    errors, summary = validate(payload)
    if errors:
        print("Slide-data validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
