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
DEFAULT_TEMPLATE_PPTX = "assets/pccsworship.pptx"


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

    requested_template = project.get("template_pptx")
    if requested_template is None or (
        isinstance(requested_template, str) and not requested_template.strip()
    ):
        effective_template = DEFAULT_TEMPLATE_PPTX
        template_source = "skill_default"
        default_template_path = Path(__file__).resolve().parents[1] / DEFAULT_TEMPLATE_PPTX
        if not default_template_path.is_file():
            errors.append(
                f"Bundled default template is missing: {DEFAULT_TEMPLATE_PPTX}."
            )
    elif isinstance(requested_template, str):
        effective_template = requested_template.strip()
        template_source = "user_supplied"
    else:
        errors.append("project.template_pptx must be text, blank, or omitted.")
        effective_template = DEFAULT_TEMPLATE_PPTX
        template_source = "invalid"

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

    scriptures = payload.get("scripture", [])
    if not isinstance(scriptures, list):
        errors.append("scripture must be a list when supplied.")
        scriptures = []

    seen_scripture_ids: set[str] = set()
    for position, scripture in enumerate(scriptures, start=1):
        label = f"scripture[{position}]"
        if not isinstance(scripture, dict):
            errors.append(f"{label} must be an object.")
            continue

        scripture_id = scripture.get("id")
        if not isinstance(scripture_id, str) or not scripture_id.strip():
            errors.append(f"{label}.id is required.")
        elif scripture_id in seen_scripture_ids:
            errors.append(f"{label}.id {scripture_id!r} is duplicated.")
        else:
            seen_scripture_ids.add(scripture_id)

        reference = scripture.get("reference")
        if not isinstance(reference, str) or not reference.strip():
            errors.append(f"{label}.reference is required.")

        source_file = scripture.get("source_file")
        if source_file is not None and (
            not isinstance(source_file, str) or not source_file.strip()
        ):
            errors.append(f"{label}.source_file must be non-empty text when supplied.")

        source_lines = scripture.get("source_lines")
        if not isinstance(source_lines, list) or not source_lines:
            errors.append(
                f"{label}.source_lines must be a non-empty list preserving the source line boundaries."
            )
        else:
            for line_number, line in enumerate(source_lines, start=1):
                if not isinstance(line, str) or not line.strip():
                    errors.append(
                        f"{label}.source_lines[{line_number}] must be non-empty text."
                    )

        if scripture.get("preserve_line_breaks") is not True:
            errors.append(
                f"{label}.preserve_line_breaks must be true; scripture source lines may not be merged, split, or reordered."
            )

        if "single_slide" in scripture and not isinstance(
            scripture.get("single_slide"), bool
        ):
            errors.append(f"{label}.single_slide must be true or false when supplied.")

    summary = {
        "status": "pass" if not errors else "fail",
        "song_count": len(songs),
        "scripture_count": len(scriptures),
        "effective_template_pptx": effective_template,
        "template_source": template_source,
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
