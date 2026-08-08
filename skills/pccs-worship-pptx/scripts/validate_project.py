#!/usr/bin/env python3
"""Validate normalized PCCS worship project input."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ALLOWED_SOURCE_MODES = {"auto", "images", "youtube", "youtube_search"}
ARRANGEMENT_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(?:\*[1-9]\d*)?$")


def nonempty_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def arrangement_tokens(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [
            token
            for token in re.split(r"[\s,，、;；]+", value.strip())
            if token
        ]
    return []


def validate(payload: Any) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return ["Project input must be a JSON object."], warnings, {}

    project = payload.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object.")
        project = {}

    if not project.get("project_id") and not project.get("service_date"):
        errors.append("project requires project_id or service_date.")
    if not isinstance(project.get("template_pptx"), str) or not project.get(
        "template_pptx", ""
    ).strip():
        errors.append("project.template_pptx is required.")

    songs = payload.get("songs")
    if not isinstance(songs, list) or not songs:
        errors.append("songs must be a non-empty list.")
        songs = []

    seen_indexes: set[int] = set()
    source_modes: Counter[str] = Counter()

    for position, song in enumerate(songs, start=1):
        label = f"songs[{position}]"
        if not isinstance(song, dict):
            errors.append(f"{label} must be an object.")
            continue

        index = song.get("index")
        if not isinstance(index, int) or isinstance(index, bool) or index < 1:
            errors.append(f"{label}.index must be a positive integer.")
        elif index in seen_indexes:
            errors.append(f"{label}.index {index} is duplicated.")
        else:
            seen_indexes.add(index)

        title = song.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{label}.title is required.")

        mode = song.get("source_mode", "auto")
        if mode not in ALLOWED_SOURCE_MODES:
            errors.append(
                f"{label}.source_mode must be one of {sorted(ALLOWED_SOURCE_MODES)}."
            )
            mode = "auto"
        source_modes[mode] += 1

        images = nonempty_list(song.get("image_files"))
        youtube_urls = nonempty_list(song.get("youtube_urls"))
        audio_files = nonempty_list(song.get("audio_files"))
        search_hint = str(song.get("youtube_search_hint") or "").strip()
        official_url = str(song.get("official_lyrics_url") or "").strip()

        has_any_source = bool(
            images or youtube_urls or audio_files or search_hint or official_url
        )
        if not has_any_source:
            errors.append(
                f"{label} requires at least one source: lyric image, YouTube URL, "
                "audio, official lyrics URL, or YouTube search hint."
            )
        if mode == "images" and not images:
            errors.append(f"{label} uses source_mode images but has no image_files.")
        if mode == "youtube" and not youtube_urls:
            errors.append(f"{label} uses source_mode youtube but has no youtube_urls.")
        if mode == "youtube_search" and not search_hint:
            errors.append(
                f"{label} uses source_mode youtube_search but has no search hint."
            )

        for url in youtube_urls:
            url_text = str(url)
            if "/channel/" in url_text or "playlist?list=" in url_text:
                warnings.append(
                    f"{label}: match this channel/playlist to one concrete video before lyric extraction."
                )

        raw_arrangement = song.get("arrangement")
        if raw_arrangement not in (None, "") and not isinstance(
            raw_arrangement, (str, list)
        ):
            errors.append(f"{label}.arrangement must be a string, list, or empty.")
        tokens = arrangement_tokens(raw_arrangement)
        invalid_tokens = [token for token in tokens if not ARRANGEMENT_TOKEN.fullmatch(token)]
        if invalid_tokens:
            errors.append(
                f"{label}.arrangement has invalid section tokens: {invalid_tokens}. "
                "Move performance notes such as 跳音 to special_notes."
            )
        if not tokens:
            warnings.append(
                f"{label}: arrangement is absent; derive it from the matched YouTube performance and audit the decision."
            )

    summary = {
        "status": "pass" if not errors else "fail",
        "song_count": len(songs),
        "source_modes": dict(sorted(source_modes.items())),
        "warnings": warnings,
    }
    return errors, warnings, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_json", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.project_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Unable to read project JSON: {exc}", file=sys.stderr)
        return 2

    errors, _, summary = validate(payload)
    if errors:
        print("Project validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
