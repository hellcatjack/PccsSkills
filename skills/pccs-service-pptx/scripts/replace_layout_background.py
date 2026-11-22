#!/usr/bin/env python3
"""Replace only the PNG behind a specified set of slides sharing one layout."""

import argparse
from pathlib import Path
from zipfile import ZipFile

from PIL import Image

from compose_weekly_pptx import NS, Package, picture_box, rel_part, resolve, tag, xml


def swap_background(source, output, image, slide_numbers):
    package = Package(source)
    if output.exists():
        raise FileExistsError(f"Choose a new output file: {output}")
    if not slide_numbers or any(not 1 <= index <= len(package.slides) for index in slide_numbers):
        raise ValueError("Specify valid one-based slide numbers.")
    layouts = [
        resolve(part, next(r.get("Target") for r in package.rels(part)
                           if r.get("Type").endswith("/slideLayout")))
        for part in package.slides
    ]
    chosen = {layouts[i - 1] for i in slide_numbers}
    if len(chosen) != 1:
        raise ValueError("Run separately for each distinct layout.")
    layout, = chosen
    owners = {i for i, part in enumerate(layouts, 1) if part == layout}
    if owners != set(slide_numbers):
        raise ValueError(f"This layout is shared by slides {sorted(owners)}. Duplicate it first for a narrower edit.")
    page = xml(package.parts[layout])
    expected = (0, 0, *map(int, package.size))
    pictures = [pic for pic in page.findall("p:cSld/p:spTree/p:pic", NS)
                if tuple(picture_box(pic)) == expected]
    if len(pictures) != 1:
        raise ValueError("The layout must contain a single full-slide picture.")
    link = pictures[0].find("p:blipFill/a:blip", NS).get(tag("r", "embed"))
    media = resolve(layout, package.find_relationship(package.rels(layout), link).get("Target"))
    refs = []
    for part in package.parts:
        if part == "_rels/.rels" or "/_rels/" not in part or not part.endswith(".rels"):
            continue
        parent, name = part.rsplit("/_rels/", 1)
        owner = f"{parent}/{name[:-5]}"
        for rel in package.rels(owner):
            if rel.get("TargetMode") != "External" and resolve(owner, rel.get("Target")) == media:
                refs.append((rel_part(owner), rel.get("Id")))
    if refs != [(rel_part(layout), link)] or package.content_type(media) != "image/png":
        raise ValueError("The media is shared or is not a PNG. Make an independent picture first.")
    with Image.open(image) as replacement:
        expected_ratio = expected[2] / expected[3]
        if replacement.format != "PNG" or abs(replacement.width / replacement.height / expected_ratio - 1) > .01:
            raise ValueError("Supply a PNG within 1% of the presentation aspect ratio.")
    new_bytes = image.read_bytes()
    with ZipFile(source) as old, ZipFile(output, "x") as result:
        for part in old.infolist():
            result.writestr(part, new_bytes if part.filename == media else old.read(part.filename))
    with ZipFile(output) as result:
        if result.testzip() is not None:
            raise ValueError("The output package failed its CRC check.")
        changed = [name for name, old_data in package.parts.items()
                   if old_data != result.read(name)]
    if changed not in ([], [media]):
        raise ValueError(f"Unexpected package changes: {changed}")
    return media


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--slides", nargs="+", type=int, required=True)
    args = parser.parse_args()
    try:
        part = swap_background(args.source, args.output, args.image, args.slides)
    except (OSError, ValueError, KeyError) as err:
        parser.exit(1, f"Cannot replace background: {err}\n")
    print(f"Verified {args.output}; targeted media {part}")


if __name__ == "__main__":
    main()
