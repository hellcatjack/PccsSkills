#!/usr/bin/env python3
"""Validate normalized PCCS worship slide-plan data before PPTX generation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


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

    songs = payload.get("songs")
    pages = payload.get("pages")
    if not isinstance(songs, list) or not songs:
        errors.append("songs must be a non-empty list.")
        songs = []
    if not isinstance(pages, list) or not pages:
        errors.append("pages must be a non-empty list.")
        pages = []

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

    performance_pages: dict[str, list[tuple[int, str, int, str]]] = {
        song_id: [] for song_id in song_by_id
    }
    page_song_ids: list[str] = []

    for position, page in enumerate(pages, start=1):
        label = f"pages[{position}]"
        if not isinstance(page, dict):
            errors.append(f"{label} must be an object.")
            continue

        role = page.get("role")
        if role not in ALLOWED_ROLES:
            errors.append(f"{label}.role must be one of {sorted(ALLOWED_ROLES)}.")
        lines = page.get("lines")
        if not isinstance(lines, list) or not lines:
            errors.append(f"{label}.lines must be a non-empty list.")
            lines = []
        if len(lines) > 3:
            errors.append(f"{label} must contain at most 3 lines.")

        font = page.get("font")
        if role in BODY_ROLES and font != "KaiTi":
            errors.append(f"{label}.font must be KaiTi.")
        if role in BODY_ROLES and page.get("body_font_pt") != 48:
            errors.append(f"{label}.body_font_pt must be exactly 48.")
        if role == "song_first" and page.get("title_font_pt") != 54:
            errors.append(f"{label}.title_font_pt must be exactly 54.")

        for line_number, raw_line in enumerate(lines, start=1):
            if not isinstance(raw_line, str) or not raw_line.strip():
                errors.append(f"{label}.lines[{line_number}] must be non-empty text.")
                continue
            if "  " in raw_line:
                errors.append(
                    f"{label}.lines[{line_number}] contains repeated spaces; use single spaces."
                )
            if role in SONG_ROLES and LYRIC_PUNCTUATION.search(raw_line):
                errors.append(
                    f"{label}.lines[{line_number}] contains lyric punctuation."
                )

        if role in SONG_ROLES:
            song_id = page.get("song_id")
            section = page.get("section_code")
            performance_index = page.get("performance_index")
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
            if (
                not isinstance(performance_index, int)
                or isinstance(performance_index, bool)
                or performance_index < 1
            ):
                errors.append(
                    f"{label}.performance_index must be a positive integer."
                )
                continue
            performance_pages[song_id].append(
                (performance_index, section.strip(), position, role)
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
        previous_section = ""
        for performance_index, section, page_position, _ in entries:
            if performance_index == previous_index:
                if section != previous_section:
                    errors.append(
                        f"pages[{page_position}] changes section_code within performance_index {performance_index}."
                    )
                continue
            if performance_index != previous_index + 1:
                errors.append(
                    f"pages[{page_position}] has non-consecutive performance_index {performance_index}."
                )
            sequence.append(section)
            previous_index = performance_index
            previous_section = section
        actual_sequences[song_id] = sequence
        if sequence != expected_sequences.get(song_id, []):
            errors.append(
                f"Song {song_id!r} page sequence {sequence} does not match expanded arrangement "
                f"{expected_sequences.get(song_id, [])}."
            )

    summary = {
        "status": "pass" if not errors else "fail",
        "song_count": len(songs),
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
