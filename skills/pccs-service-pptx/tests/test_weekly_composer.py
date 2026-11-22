import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from PIL import Image
import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from compose_weekly_pptx import NS, Package, TEMPLATE, shape, xml
from replace_layout_background import swap_background


def run_composer(tmp_path, name, pages):
    plan = tmp_path / f"{name}.json"
    plan.write_text(json.dumps({"slides": pages}, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / f"{name}.pptx"
    subprocess.run([sys.executable, str(SCRIPTS / "compose_weekly_pptx.py"),
                    str(plan), str(output)], check=True, capture_output=True)
    return output


def test_native_prototypes_and_foreign_master_ids(tmp_path):
    original = run_composer(tmp_path, "source", [
        {"template": "welcome", "text": {"Welcome title": "原稿标题"}, "notes": "原稿备注"}])
    combined = run_composer(tmp_path, "weekly", [
        {"template": "opening"},
        {"template": "scripture", "text": {"Scripture body": ["甲\n乙", "丙"]}},
        {"source": original.name, "pages": [1]},
    ])
    deck = Package(combined)
    assert len(deck.slides) == 3
    scripture = shape(xml(deck.parts[deck.slides[1]]), "Scripture body")
    paragraphs = scripture.xpath("p:txBody/a:p", namespaces=NS)
    assert [p.xpath(".//a:t/text()", namespaces=NS) for p in paragraphs] == [["甲", "乙"], ["丙"]]
    assert len(paragraphs[0].findall("a:br", NS)) == 1
    imported = xml(deck.parts[deck.slides[2]])
    assert imported.xpath(".//a:t[text()='原稿标题']", namespaces=NS)
    assert any("原稿备注".encode() in d for p, d in deck.parts.items() if p.startswith("ppt/notesSlides/"))
    assert sum(
        part.startswith("ppt/notesMasters/notesMaster") and part.endswith(".xml")
        for part in deck.parts
    ) == 1
    ids = xml(deck.parts["ppt/presentation.xml"]).xpath("p:sldMasterIdLst/p:sldMasterId/@id", namespaces=NS)
    for part, data in deck.parts.items():
        if part.startswith("ppt/slideMasters/slideMaster") and part.endswith(".xml"):
            ids += xml(data).xpath("p:sldLayoutIdLst/p:sldLayoutId/@id", namespaces=NS)
    assert len(ids) == len(set(ids))


def test_gallery_jpeg_keeps_bytes_and_applies_exif_orientation(tmp_path):
    image_path = tmp_path / "portrait.jpg"
    with Image.new("RGB", (400, 300), "navy") as image:
        exif = image.getexif()
        exif[274] = 6
        image.save(image_path, exif=exif)
    output = run_composer(tmp_path, "gallery", [
        {"template": "gallery", "pictures": {"gallery-1": image_path.name}}])
    deck = Package(output)
    picture = shape(xml(deck.parts[deck.slides[0]]), "gallery-1", "pic")
    transform = picture.find("p:spPr/a:xfrm", NS)
    assert transform.get("rot") == "5400000"
    size = transform.find("a:ext", NS)
    assert int(size.get("cx")) * 3 == int(size.get("cy")) * 4
    assert image_path.read_bytes() in deck.parts.values()


def test_only_targeted_background_part_is_modified(tmp_path):
    deck = run_composer(tmp_path, "base", [
        {"template": "opening"}, {"template": "scripture"}, {"template": "scripture"}])
    image_path = tmp_path / "background.png"
    Image.new("RGB", (160, 90), "ivory").save(image_path)
    output = tmp_path / "new-background.pptx"
    with pytest.raises(ValueError, match="shared by slides"):
        swap_background(deck, output, image_path, [2])
    part = swap_background(deck, output, image_path, [2, 3])
    with ZipFile(deck) as src, ZipFile(output) as dest:
        assert [n for n in src.namelist() if src.read(n) != dest.read(n)] == [part]


def test_public_template_has_no_weekly_private_payload():
    with ZipFile(TEMPLATE) as deck:
        assert deck.testzip() is None
        assert not any(name.endswith((".mp3", ".mp4", ".wav")) for name in deck.namelist())
        for part in deck.namelist():
            if part.endswith(".rels"):
                assert all(item.get("TargetMode") != "External" for item in xml(deck.read(part)))
        assert list(xml(deck.read("docProps/core.xml"))) == []
