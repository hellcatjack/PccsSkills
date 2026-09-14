#!/usr/bin/env python3
import argparse
import json
import math
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


def validate_background_measurement(record, label):
    actual = record.get("background_actual_size_pixels")
    if actual is None:
        return
    if (not isinstance(actual, list) or len(actual) != 2
            or any(type(value) is not int or value <= 0 for value in actual)):
        fail(f"{label}.background_actual_size_pixels must be two positive integers")
    if abs(actual[0] / actual[1] / (48 / 23) - 1) > 0.001:
        fail(f"{label} background ratio differs from 48:23 by more than 0.1%; regenerate")
    if actual != [1920, 920]:
        require_nonempty_string(record.get("background_size_audit"), f"{label}.background_size_audit")


def validate_scripture_style(slide, passage_styles):
    label = f"slide {slide['index']} scripture"
    override = slide.get("style_override_reason")
    if override is not None:
        require_nonempty_string(override, f"{label}.style_override_reason")
    size = slide.get("body_font_pt", 36)
    if (isinstance(size, bool) or not isinstance(size, (int, float))
            or not math.isfinite(size) or size <= 0):
        fail(f"{label}.body_font_pt must be a finite positive number")
    font = slide.get("body_font", "SimSun")
    alignment = slide.get("alignment", "left")
    shadow = slide.get("body_shadow", False)
    require_nonempty_string(font, f"{label}.body_font")
    if alignment not in {"left", "center", "right", "justify"}:
        fail(f"{label}.alignment is invalid")
    if not isinstance(shadow, bool):
        fail(f"{label}.body_shadow must be boolean")
    if not override:
        if size > 36:
            fail(f"{label}.body_font_pt must be at most 36")
        if font != "SimSun":
            fail(f"{label}.body_font defaults to SimSun; record an explicit user style override")
        if alignment != "left":
            fail(f"{label}.alignment must be left")
        if shadow:
            fail(f"{label}.body_shadow must be false")
    scripture_id = slide.get("scripture_id")
    if scripture_id is not None:
        require_nonempty_string(scripture_id, f"{label}.scripture_id")
        style = (font, size, alignment, shadow)
        if scripture_id in passage_styles and passage_styles[scripture_id] != style:
            fail(f"{label} requires uniform body typography across scripture_id {scripture_id!r}")
        passage_styles[scripture_id] = style
    fixed = slide.get("source_lines_fixed", True)
    wrap = slide.get("allow_visual_wrap", not fixed)
    if not isinstance(fixed, bool) or not isinstance(wrap, bool):
        fail(f"{label}.source_lines_fixed and allow_visual_wrap must be boolean")
    if fixed and wrap:
        fail(f"{label}.allow_visual_wrap cannot be true for fixed source lines")


def validate_verse_metadata(slide):
    label = f"slide {slide['index']} scripture"
    lines = slide["source_lines"]
    metadata_fields = {"raw_source_lines", "verse_numbers", "verse_prefixes"}
    if not metadata_fields.intersection(slide):
        return
    raw = slide.get("raw_source_lines")
    if (not isinstance(raw, list) or len(raw) != len(lines)
            or any(not isinstance(line, str) for line in raw)):
        fail(f"{label}.raw_source_lines must preserve one raw entry per source line")
    numbers = slide.get("verse_numbers")
    prefixes = slide.get("verse_prefixes")
    if numbers is None and prefixes is None:
        if raw != lines:
            fail(f"{label}.raw_source_lines changed without audited verse metadata")
        return
    for value, field in [(numbers, "verse_numbers"), (prefixes, "verse_prefixes")]:
        if (not isinstance(value, list) or len(value) != len(lines)
                or any(not isinstance(item, str) for item in value)):
            fail(f"{label}.{field} must have one string per source line")
    if [prefix + line for prefix, line in zip(prefixes, lines)] != raw:
        fail(f"{label}.raw_source_lines cannot be reconstructed exactly from verse_prefixes + source_lines")
    require_nonempty_string(slide.get("translation"), f"{label}.translation")
    require_nonempty_string(slide.get("verse_metadata_audit"), f"{label}.verse_metadata_audit")
    if slide.get("verse_boundaries_verified") is not True:
        fail(f"{label}.verse_boundaries_verified must be true before separating verse metadata")


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
    validate_background_measurement(project, "project")

    slides = data.get("slides")
    if not isinstance(slides, list) or not slides:
        fail("slides must be a non-empty array")

    expected_indexes = list(range(1, len(slides) + 1))
    actual_indexes = [slide.get("index") if isinstance(slide, dict) else None for slide in slides]
    if actual_indexes != expected_indexes:
        fail("slide indexes must be consecutive integers beginning at 1")

    final_indexes = set()
    for slide in slides:
        final_index = slide.get("final_slide_index", slide["index"])
        if type(final_index) is not int or final_index < 1:
            fail(f"slide {slide['index']} final_slide_index must be a positive integer")
        if final_index in final_indexes:
            fail(f"slide {slide['index']} final_slide_index maps more than one service record to final slide {final_index}")
        final_indexes.add(final_index)

    passage_styles = {}
    for slide in slides:
        slide_index = slide["index"]
        slide_type = slide.get("type")
        validate_background_measurement(slide, f"slide {slide_index}")
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
            validate_scripture_style(slide, passage_styles)
            validate_verse_metadata(slide)

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
