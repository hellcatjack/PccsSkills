#!/usr/bin/env python3
"""Build a native weekly PPTX from the PCCS template and same-size PPTX sources."""

import argparse
import base64
from copy import deepcopy
import json
import math
from pathlib import Path, PurePosixPath
import posixpath
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree as ET
from PIL import Image


NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
    "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
}
PRESENTATION = "ppt/presentation.xml"
CONTENT_TYPES = "[Content_Types].xml"
TEMPLATE = Path(__file__).resolve().parents[1] / "assets/pccs-weekly-720.pptx"
AUDIO_TEMPLATE = TEMPLATE.with_name("autoplay-audio.xml")
MEDIA_REL = "http://schemas.microsoft.com/office/2007/relationships/media"
TRANSPARENT_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQABpfZFQAAAAABJRU5ErkJggg=="
)


def tag(prefix, name):
    return f"{{{NS[prefix]}}}{name}"


def xml(data):
    parser = ET.XMLParser(resolve_entities=False, no_network=True)
    return ET.fromstring(data, parser)


def encode(node):
    return ET.tostring(node, encoding="UTF-8", xml_declaration=True, standalone=True)


def rel_part(part):
    parent, name = posixpath.split(part)
    return posixpath.join(parent, "_rels", f"{name}.rels")


def resolve(part, target):
    if target.startswith("/"):
        return target[1:]
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def relationship_target(part, target):
    return posixpath.relpath(target, posixpath.dirname(part) or ".")


class Package:
    def __init__(self, file):
        self.path = file
        with ZipFile(file) as archive:
            self.parts = {item.filename: archive.read(item) for item in archive.infolist()}
        self.types = xml(self.parts[CONTENT_TYPES])
        self.defaults = {x.get("Extension"): x.get("ContentType")
                         for x in self.types.findall("ct:Default", NS)}
        self.overrides = {x.get("PartName")[1:]: x.get("ContentType")
                          for x in self.types.findall("ct:Override", NS)}
        presentation = xml(self.parts[PRESENTATION])
        slide_list = presentation.find("p:sldIdLst", NS)
        if slide_list is None:
            raise ValueError(f"{file.name} has no slides.")
        presentation_rels = self.rels(PRESENTATION)
        self.slides = [
            resolve(PRESENTATION, self.find_relationship(presentation_rels, entry.get(tag("r", "id"))).get("Target"))
            for entry in slide_list
        ]
        size = presentation.find("p:sldSz", NS)
        self.size = (size.get("cx"), size.get("cy"))

    def rels(self, part):
        data = self.parts.get(rel_part(part))
        return xml(data) if data else ET.Element(tag("rel", "Relationships"), nsmap={None: NS["rel"]})

    @staticmethod
    def find_relationship(rels, rid):
        return next(rel for rel in rels if rel.get("Id") == rid)

    def content_type(self, part):
        return self.overrides.get(part) or self.defaults[PurePosixPath(part).suffix[1:]]

    def put(self, part, content, content_type=None):
        self.parts[part] = content
        if content_type is not None:
            self.overrides[part] = content_type

    def unique_part(self, source):
        path = PurePosixPath(source)
        for i in range(1, len(self.parts) + 2):
            target = str(path.with_name(f"{path.stem}_pccs{i}{path.suffix}"))
            if target not in self.parts:
                return target
        raise ValueError(f"Could not allocate {source}.")

    def add_relationship(self, owner, target, kind):
        rels = self.rels(owner)
        ids = {rel.get("Id") for rel in rels}
        rid = next(f"rId{i}" for i in range(1, len(ids) + 2) if f"rId{i}" not in ids)
        rel_type = kind if kind.startswith("http://") else f"{NS['r']}/{kind}"
        ET.SubElement(rels, tag("rel", "Relationship"), {
            "Id": rid, "Type": rel_type, "Target": relationship_target(owner, target)
        })
        self.put(rel_part(owner), encode(rels))
        return rid

    def write(self, file):
        live = {"_rels/.rels"}
        pending = [""]
        while pending:
            owner = pending.pop()
            for rel in self.rels(owner):
                if rel.get("TargetMode") == "External":
                    continue
                part = resolve(owner, rel.get("Target"))
                if part not in self.parts:
                    raise ValueError(f"Missing package part {part} referenced by {owner or 'root'}.")
                if part in live:
                    continue
                live.add(part)
                if rel_part(part) in self.parts:
                    live.add(rel_part(part))
                    pending.append(part)
        result_types = ET.Element(tag("ct", "Types"), nsmap={None: NS["ct"]})
        for ext, content_type in sorted(self.defaults.items()):
            ET.SubElement(result_types, tag("ct", "Default"), Extension=ext, ContentType=content_type)
        for part in sorted(live & self.overrides.keys()):
            ET.SubElement(result_types, tag("ct", "Override"),
                          PartName=f"/{part}", ContentType=self.overrides[part])
        self.put(CONTENT_TYPES, encode(result_types))
        file.parent.mkdir(parents=True, exist_ok=True)
        if file.exists():
            raise FileExistsError(f"Choose a new output file: {file}")
        with ZipFile(file, "x", compression=ZIP_DEFLATED) as archive:
            for part in sorted(live | {CONTENT_TYPES}):
                info = ZipInfo(part, date_time=(2000, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, self.parts[part])


class Importer:
    """Copy a source slide's OPC dependencies while keeping theme and layout parts native."""

    def __init__(self, source, output, selected):
        self.source, self.output = source, output
        self.selected = selected
        self.mapping = {}

    def copy(self, part):
        if part in self.mapping:
            return self.mapping[part]
        if part in self.source.slides and part not in self.selected:
            raise ValueError(f"{self.source.path.name} links to a slide outside the selected pages.")
        content_type = self.source.content_type(part)
        if content_type.endswith(".notesMaster+xml"):
            # The presentation has one notes master. Keep each imported notes
            # slide and its text, attaching it to the deck's common notes master.
            notes_master = next(r for r in self.output.rels(PRESENTATION)
                                if r.get("Type").endswith("/notesMaster"))
            self.mapping[part] = resolve(PRESENTATION, notes_master.get("Target"))
            return self.mapping[part]
        dest = self.output.unique_part(part)
        self.mapping[part] = dest
        self.output.put(dest, self.source.parts[part], content_type)
        if rel_part(part) in self.source.parts:
            rels = self.source.rels(part)
            for rel in rels:
                if rel.get("TargetMode") != "External":
                    target = self.copy(resolve(part, rel.get("Target")))
                    rel.set("Target", relationship_target(dest, target))
            self.output.put(rel_part(dest), encode(rels))
        return dest


def clone_prototype(package, src):
    """Give each slide independent notes while sharing its layout and immutable artwork."""
    dest = package.unique_part(src)
    package.put(dest, package.parts[src], package.content_type(src))
    rels = package.rels(src)
    for rel in rels:
        if rel.get("Type").endswith("/notesSlide"):
            notes = resolve(src, rel.get("Target"))
            new_notes = package.unique_part(notes)
            package.put(new_notes, package.parts[notes], package.content_type(notes))
            note_rels = package.rels(notes)
            for note_rel in note_rels:
                if note_rel.get("Type").endswith("/slide"):
                    note_rel.set("Target", relationship_target(new_notes, dest))
            package.put(rel_part(new_notes), encode(note_rels))
            rel.set("Target", relationship_target(dest, new_notes))
    package.put(rel_part(dest), encode(rels))
    return dest


def shape(slide, name, kind="sp"):
    matches = slide.xpath(f"./p:cSld/p:spTree/p:{kind}[*/p:cNvPr/@name = $name]",
                          namespaces=NS, name=name)
    if len(matches) != 1:
        raise ValueError(f"Expected one `{name}` shape in the prototype; found {len(matches)}.")
    return matches[0]


def replace_text(frame, value):
    paragraphs = [value] if isinstance(value, str) else value
    if not isinstance(paragraphs, list) or not paragraphs or any(not isinstance(p, str) for p in paragraphs):
        raise ValueError("Text slots take a string or a non-empty array of paragraph strings.")
    old = frame.findall("a:p", NS)
    for p in old:
        frame.remove(p)
    for index, text in enumerate(paragraphs):
        template = old[min(index, len(old) - 1)]
        new = ET.SubElement(frame, tag("a", "p"))
        style = template.find("a:pPr", NS)
        end_style = template.find("a:endParaRPr", NS)
        run_style = template.find("a:r/a:rPr", NS)
        if style is not None:
            new.append(deepcopy(style))
        if run_style is None and end_style is not None:
            run_style = deepcopy(end_style)
            run_style.tag = tag("a", "rPr")
        for line_index, line in enumerate(text.split("\n")):
            if line_index:
                ET.SubElement(new, tag("a", "br"))
            run = ET.SubElement(new, tag("a", "r"))
            if run_style is not None:
                run.append(deepcopy(run_style))
            ET.SubElement(run, tag("a", "t")).text = line
        if end_style is not None:
            new.append(deepcopy(end_style))


def fit_picture(picture, bounds, original_size):
    x, y, width, height = bounds
    ratio = min(width / original_size[0], height / original_size[1])
    fitted_width = round(original_size[0] * ratio)
    fitted_height = round(original_size[1] * ratio)
    transform = picture.find("p:spPr/a:xfrm", NS)
    offset = transform.find("a:off", NS)
    size = transform.find("a:ext", NS)
    offset.set("x", str(x + (width - fitted_width) // 2))
    offset.set("y", str(y + (height - fitted_height) // 2))
    size.set("cx", str(fitted_width))
    size.set("cy", str(fitted_height))


def apply_orientation(picture, orientation):
    # DrawingML leaves JPEG bytes intact. PowerPoint needs the EXIF transform in
    # the shape because a directly embedded JPEG is decoded in storage order.
    transform = picture.find("p:spPr/a:xfrm", NS)
    rotation = {3: 180, 5: 90, 6: 90, 7: 90, 8: 270}.get(orientation, 0)
    for key in ("rot", "flipH", "flipV"):
        transform.attrib.pop(key, None)
    if orientation in {2, 7}:
        transform.set("flipH", "1")
    if orientation in {4, 5}:
        transform.set("flipV", "1")
    if rotation:
        transform.set("rot", str(rotation * 60000))
    if orientation in {5, 6, 7, 8}:
        x, y, width, height = picture_box(picture)
        offset = transform.find("a:off", NS)
        size = transform.find("a:ext", NS)
        offset.set("x", str(x + (width - height) // 2))
        offset.set("y", str(y + (height - width) // 2))
        size.set("cx", str(height))
        size.set("cy", str(width))


def picture_box(picture):
    transform = picture.find("p:spPr/a:xfrm", NS)
    offset = transform.find("a:off", NS)
    size = transform.find("a:ext", NS)
    return tuple(int(item) for item in (offset.get("x"), offset.get("y"), size.get("cx"), size.get("cy")))


def place_picture(package, part, root, name, path):
    picture = shape(root, name, "pic")
    with Image.open(path) as image:
        extension = {"PNG": "png", "JPEG": "jpg"}.get(image.format)
        if extension is None:
            raise ValueError(f"{path.name}: use a PNG or JPEG.")
        size = image.size
        orientation = image.getexif().get(274, 1)
        if orientation in {5, 6, 7, 8}:
            size = size[::-1]
    fit_picture(picture, picture_box(picture), size)
    apply_orientation(picture, orientation)
    mime = "image/png" if extension == "png" else "image/jpeg"
    asset = package.unique_part(f"ppt/media/weekly.{extension}")
    package.put(asset, path.read_bytes(), mime)
    blip = picture.find("p:blipFill/a:blip", NS)
    blip.set(tag("r", "embed"), package.add_relationship(part, asset, "image"))
    for source_rect in picture.findall("p:blipFill/a:srcRect", NS):
        source_rect.attrib.clear()


def populate(package, part, page, base):
    slide = xml(package.parts[part])
    if page.get("name"):
        slide.find("p:cSld", NS).set("name", page["name"])
    for name, text in page.get("text", {}).items():
        frame = shape(slide, name).find("p:txBody", NS)
        replace_text(frame, text)
    for name, path in page.get("pictures", {}).items():
        place_picture(package, part, slide, name, base / path)
    if "notes" in page:
        note_rel = next(rel for rel in package.rels(part) if rel.get("Type").endswith("/notesSlide"))
        note_part = resolve(part, note_rel.get("Target"))
        notes = xml(package.parts[note_part])
        frame, = notes.xpath(".//p:sp[p:nvSpPr/p:nvPr/p:ph/@type='body']/p:txBody", namespaces=NS)
        replace_text(frame, page["notes"])
        package.put(note_part, encode(notes))
    package.put(part, encode(slide))


def source_indices(source, entry):
    pages = entry.get("pages", list(range(1, len(source.slides) + 1)))
    if (not isinstance(pages, list) or not pages
            or any(type(i) is not int or i < 1 or i > len(source.slides) for i in pages)):
        raise ValueError(f"{source.path.name}: pages must be valid one-based slide numbers.")
    return [source.slides[i - 1] for i in pages]


def configure_audio(package, slides, cues, base, imported_parts):
    if not cues:
        return
    if not isinstance(cues, list):
        raise ValueError("audio_cues must be an array.")
    icon = package.unique_part("ppt/media/hidden-audio.png")
    package.put(icon, TRANSPARENT_PNG, "image/png")
    used = set()
    for cue in cues:
        start, seconds = cue["start_slide"], cue["advance_seconds"]
        if type(start) is not int or not isinstance(seconds, list) or not seconds:
            raise ValueError("Audio requires a one-based start_slide and per-slide advance_seconds.")
        stop = start + len(seconds) - 1
        if not 1 <= start <= stop <= len(slides) or used.intersection(range(start, stop + 1)):
            raise ValueError("Audio ranges must fit the deck and cannot overlap.")
        used.update(range(start, stop + 1))
        clip = base / cue["mp3"]
        if clip.suffix.lower() != ".mp3" or not clip.stat().st_size:
            raise ValueError(f"{clip.name}: use a non-empty MP3.")
        asset = package.unique_part("ppt/media/accompaniment.mp3")
        package.put(asset, clip.read_bytes(), "audio/mpeg")
        for index, duration in enumerate(seconds, start):
            part = slides[index - 1]
            slide = xml(package.parts[part])
            if part in imported_parts or slide.find("p:timing", NS) is not None or any(
                ET.QName(child).localname == "AlternateContent" for child in slide
            ):
                raise ValueError(f"Slide {index} already has native cues or is an imported slide.")
            previous = slide.find("p:transition", NS)
            if previous is not None:
                slide.remove(previous)
            if duration is not None:
                if (type(duration) not in {int, float} or not math.isfinite(duration)
                        or not 0.001 <= duration <= 3600):
                    raise ValueError(f"Invalid slide duration at slide {index}.")
                transition = ET.Element(tag("p", "transition"), advClick="0", advTm=str(round(duration * 1000)))
                extension = slide.find("p:extLst", NS)
                slide.insert(slide.index(extension) if extension is not None else len(slide), transition)
            if index == start:
                insert_autoplay(package, part, slide, asset, icon, len(seconds))
            package.put(part, encode(slide))
    part = "ppt/presProps.xml"
    props = xml(package.parts[part])
    show = props.find("p:showPr", NS)
    if show is None:
        show = ET.Element(tag("p", "showPr"))
        props.insert(0, show)
    show.set("loop", "0")
    show.set("useTimings", "1")
    package.put(part, encode(props))


def insert_autoplay(package, part, slide, asset, icon, slide_count):
    sample = xml(AUDIO_TEMPLATE.read_bytes())
    picture, timing = sample
    tree = slide.find("p:cSld/p:spTree", NS)
    shape_id = str(max(map(int, tree.xpath(".//p:cNvPr/@id", namespaces=NS)), default=0) + 1)
    picture.find("p:nvPicPr/p:cNvPr", NS).set("id", shape_id)
    picture.find(".//a:hlinkClick", NS).attrib.pop(tag("r", "id"), None)
    off = picture.find("p:spPr/a:xfrm/a:off", NS)
    off.set("x", str(int(package.size[0]) + 127000))
    off.set("y", str(int(package.size[1]) + 127000))
    picture.find(".//a:audioFile", NS).set(tag("r", "link"), package.add_relationship(part, asset, "audio"))
    picture.find(".//p14:media", NS).set(tag("r", "embed"), package.add_relationship(part, asset, MEDIA_REL))
    picture.find(".//a:blip", NS).set(tag("r", "embed"), package.add_relationship(part, icon, "image"))
    for target in timing.findall(".//p:spTgt", NS):
        target.set("spid", shape_id)
    timing.find(".//p:cMediaNode", NS).set("numSld", str(slide_count))
    tree.append(picture)
    extension = slide.find("p:extLst", NS)
    slide.insert(slide.index(extension) if extension is not None else len(slide), timing)


def make_deck(plan_path, output, template_path):
    base = plan_path.resolve().parent
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    pages = plan["slides"]
    if not isinstance(pages, list) or not pages:
        raise ValueError("Provide a non-empty slides array.")
    package = Package(template_path)
    prototypes = {
        xml(package.parts[part]).find("p:cSld", NS).get("name"): part for part in package.slides
    }
    sources, selection = {}, {}
    for page in pages:
        if ("template" in page) == ("source" in page):
            raise ValueError("Each entry must specify exactly one of template or source.")
        if "source" not in page:
            continue
        path = (base / page["source"]).resolve()
        if path not in sources:
            sources[path] = Package(path)
            selection[path] = set()
        source = sources[path]
        if source.size != package.size:
            raise ValueError(f"{path.name}: slide size {source.size} differs from template {package.size}.")
        new_parts = source_indices(source, page)
        if len(set(new_parts)) != len(new_parts) or selection[path].intersection(new_parts):
            raise ValueError(f"{path.name}: external source slides may appear only once per output.")
        selection[path].update(new_parts)
    imports = {path: Importer(source, package, selection[path]) for path, source in sources.items()}
    final_slides, imported_parts = [], set()
    for page in pages:
        if "template" in page:
            try:
                src = prototypes[page["template"]]
            except KeyError as error:
                raise ValueError(f"Unknown prototype {page['template']}. See weekly-production.md.") from error
            part = clone_prototype(package, src)
            populate(package, part, page, base)
            final_slides.append(part)
        else:
            path = (base / page["source"]).resolve()
            importer = imports[path]
            copied = [importer.copy(part) for part in source_indices(importer.source, page)]
            imported_parts.update(copied)
            final_slides.extend(copied)
    configure_audio(package, final_slides, plan.get("audio_cues", []), base, imported_parts)
    presentation = xml(package.parts[PRESENTATION])
    slide_list = presentation.find("p:sldIdLst", NS)
    slide_list.clear()
    rels = package.rels(PRESENTATION)
    for rel in list(rels):
        if rel.get("Type").endswith("/slide"):
            rels.remove(rel)
    package.put(rel_part(PRESENTATION), encode(rels))
    for index, part in enumerate(final_slides, 256):
        rid = package.add_relationship(PRESENTATION, part, "slide")
        ET.SubElement(slide_list, tag("p", "sldId"), {"id": str(index), tag("r", "id"): rid})
    master_list = presentation.find("p:sldMasterIdLst", NS)
    master_ids = {int(m.get("id")) for m in master_list}
    for part in package.parts:
        if (part.startswith("ppt/slideMasters/") and "/_rels/" not in part
                and part.endswith(".xml")):
            master = xml(package.parts[part])
            master_ids.update(map(int, master.xpath("p:sldLayoutIdLst/p:sldLayoutId/@id", namespaces=NS)))
    next_id = max(master_ids, default=2147483647) + 1
    for importer in imports.values():
        for old, dest in importer.mapping.items():
            if importer.source.content_type(old).endswith(".slideMaster+xml"):
                rid = package.add_relationship(PRESENTATION, dest, "slideMaster")
                ET.SubElement(master_list, tag("p", "sldMasterId"),
                              {"id": str(next_id), tag("r", "id"): rid})
                next_id += 1
                master = xml(package.parts[dest])
                for layout in master.findall("p:sldLayoutIdLst/p:sldLayoutId", NS):
                    layout.set("id", str(next_id))
                    next_id += 1
                package.put(dest, encode(master))
    package.put(PRESENTATION, encode(presentation))
    app = xml(package.parts["docProps/app.xml"])
    slide_count = next(part for part in app if ET.QName(part).localname == "Slides")
    slide_count.text = str(len(final_slides))
    package.put("docProps/app.xml", encode(app))
    package.write(output)
    return len(final_slides)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    args = parser.parse_args()
    try:
        count = make_deck(args.plan, args.output, args.template)
    except (ValueError, OSError, KeyError) as err:
        parser.exit(1, f"Cannot build PPTX: {err}\n")
    print(f"Saved {count} slides to {args.output}")


if __name__ == "__main__":
    sys.exit(main())
