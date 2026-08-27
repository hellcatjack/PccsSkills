#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ALLOWED_TYPES = {
    "cover",
    "announcement",
    "scripture",
    "welcome",
    "qr",
    "form",
    "photo",
    "prayer",
    "baptism",
    "communion",
    "offering",
    "doxology",
    "transition",
    "closing",
}
ASSET_REQUIRED_TYPES = {"qr", "form", "photo"}


def fail(message):
    print(f"INVALID: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_nonempty_string(value, label):
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")


def validate_project(data):
    if not isinstance(data, dict):
        fail("root must be an object")

    project = data.get("project")
    if not isinstance(project, dict):
        fail("project must be an object")

    require_nonempty_string(project.get("project_id"), "project.project_id")
    require_nonempty_string(project.get("service_date"), "project.service_date")
    require_nonempty_string(project.get("language"), "project.language")

    if project.get("background_size_pixels") != "1920x920":
        fail("project.background_size_pixels must be 1920x920")
    if project.get("background_geometry_points") != [0, 0, 720, 345]:
        fail("project.background_geometry_points must be [0, 0, 720, 345]")

    slides = data.get("slides")
    if not isinstance(slides, list) or not slides:
        fail("slides must be a non-empty array")

    expected_indexes = list(range(1, len(slides) + 1))
    actual_indexes = [slide.get("index") if isinstance(slide, dict) else None for slide in slides]
    if actual_indexes != expected_indexes:
        fail("slide indexes must be consecutive integers beginning at 1")

    for slide in slides:
        slide_index = slide["index"]
        slide_type = slide.get("type")
        if slide_type == "lyrics":
            fail(f"slide {slide_index} type lyrics belongs to pccs-worship-pptx")
        if slide_type not in ALLOWED_TYPES:
            fail(f"slide {slide_index} has unsupported type: {slide_type}")

        if "title" in slide and not isinstance(slide["title"], str):
            fail(f"slide {slide_index} title must be a string")
        if "body_lines" in slide:
            body_lines = slide["body_lines"]
            if not isinstance(body_lines, list) or not all(isinstance(line, str) for line in body_lines):
                fail(f"slide {slide_index} body_lines must be an array of strings")

        if slide_type == "scripture":
            source_lines = slide.get("source_lines")
            if (
                not isinstance(source_lines, list)
                or not source_lines
                or not all(isinstance(line, str) and line != "" for line in source_lines)
            ):
                fail(f"slide {slide_index} scripture source_lines must be a non-empty array of strings")
            if slide.get("preserve_source_lines") is not True:
                fail(f"slide {slide_index} scripture preserve_source_lines must be true")
            if "single_slide" in slide and not isinstance(slide["single_slide"], bool):
                fail(f"slide {slide_index} single_slide must be boolean")

        if slide_type in ASSET_REQUIRED_TYPES:
            asset_files = slide.get("asset_files")
            if (
                not isinstance(asset_files, list)
                or not asset_files
                or not all(isinstance(item, str) and item.strip() for item in asset_files)
            ):
                fail(f"slide {slide_index} type {slide_type} requires non-empty asset_files")

    deliverables = data.get("deliverables")
    if not isinstance(deliverables, dict):
        fail("deliverables must be an object")
    require_nonempty_string(deliverables.get("output_pptx"), "deliverables.output_pptx")
    if deliverables.get("powerpoint_duplicate_test") is not True:
        fail("deliverables.powerpoint_duplicate_test must be true")

    print(f"VALID: {len(slides)} non-lyric service slides")


def main():
    parser = argparse.ArgumentParser(description="Validate a PCCS non-lyric service PPTX project JSON file.")
    parser.add_argument("project_json", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.project_json.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"project file not found: {args.project_json}")
    except json.JSONDecodeError as error:
        fail(f"invalid JSON: {error}")

    validate_project(data)


if __name__ == "__main__":
    main()
