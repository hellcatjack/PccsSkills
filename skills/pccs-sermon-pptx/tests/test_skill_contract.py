import base64
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


def run_powershell_file(script: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            *map(str, arguments),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )


def create_spacing_fixture(root: Path) -> tuple[Path, dict]:
    deck = root / "spacing-fixture.pptx"
    metadata_path = root / "spacing-metadata.json"
    setup_script = root / "create-spacing-fixture.ps1"
    setup_script.write_text(
        r'''param([string]$Deck, [string]$Metadata)
$ErrorActionPreference = 'Stop'
$ppt = New-Object -ComObject PowerPoint.Application
try {
    $presentation = $ppt.Presentations.Add()
    try {
        $slide = $presentation.Slides.Add(1, 12)
        $shape = $slide.Shapes.AddTextbox(1, 52, 55, 655, 325)
        $shape.TextFrame2.MarginLeft = 0
        $shape.TextFrame2.MarginRight = 0
        $shape.TextFrame2.MarginTop = 0
        $shape.TextFrame2.MarginBottom = 0
        $shape.TextFrame2.VerticalAnchor = 1
        $shape.TextFrame2.WordWrap = -1
        $range = $shape.TextFrame2.TextRange
        $range.Text = "尼希米記 6`r1 第一節`r續行`r2 第二節"
        for ($index = 1; $index -le $range.Paragraphs().Count; $index++) {
            $paragraph = $range.Paragraphs($index, 1)
            $paragraph.Font.Name = 'STKaiti'
            $paragraph.Font.Size = if ($index -eq 1) { 32 } else { 22 }
            $paragraph.ParagraphFormat.LineRuleBefore = 0
            $paragraph.ParagraphFormat.LineRuleAfter = 0
            $paragraph.ParagraphFormat.SpaceBefore = if ($index -eq 4) { 2 } else { 0 }
            $paragraph.ParagraphFormat.SpaceAfter = if ($index -eq 1) { 10 } else { 1 }
        }
        $presentation.SaveAs($Deck, 24)
        [pscustomobject]@{
            shapeId = $shape.Id
            slideWidth = [double]$presentation.PageSetup.SlideWidth
            slideHeight = [double]$presentation.PageSetup.SlideHeight
            left = [double]$shape.Left
            top = [double]$shape.Top
            width = [double]$shape.Width
            height = [double]$shape.Height
            verticalAnchor = $shape.TextFrame2.VerticalAnchor
            wordWrap = $shape.TextFrame2.WordWrap
        } | ConvertTo-Json | Set-Content -LiteralPath $Metadata -Encoding utf8
    }
    finally {
        $presentation.Close()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation)
    }
}
finally {
    $ppt.Quit()
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($ppt)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
''',
        encoding="utf-8",
    )
    result = run_powershell_file(setup_script, "-Deck", deck, "-Metadata", metadata_path)
    if result.returncode != 0:
        raise AssertionError(f"PowerPoint fixture creation failed:\n{result.stdout}\n{result.stderr}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    return deck, metadata


def write_spacing_layout(path: Path, metadata: dict) -> None:
    layout = {
        "slideWidth": metadata["slideWidth"],
        "slideHeight": metadata["slideHeight"],
        "groups": [
            {
                "name": "scripture",
                "slides": [1],
                "shapeId": metadata["shapeId"],
                "left": metadata["left"],
                "top": metadata["top"],
                "width": metadata["width"],
                "height": metadata["height"],
                "verticalAnchor": metadata["verticalAnchor"],
                "wordWrap": metadata["wordWrap"],
                "titleSize": 32,
                "bodySize": 22,
                "blankSize": 8,
                "titleSpaceAfter": 10,
                "bodySpaceAfter": 1,
                "blankSpaceAfter": 2,
                "verseStartSpaceBefore": 4,
                "firstVerseSpaceBefore": 0,
                "continuationSpaceBefore": 0,
            }
        ],
    }
    path.write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")


def inspect_spacing(root: Path, deck: Path, shape_id: int) -> list[dict]:
    output_path = root / "spacing-output.json"
    inspect_script = root / "inspect-spacing.ps1"
    inspect_script.write_text(
        r'''param([string]$Deck, [int]$ShapeId, [string]$Output)
$ErrorActionPreference = 'Stop'
$ppt = New-Object -ComObject PowerPoint.Application
try {
    $presentation = $ppt.Presentations.Open($Deck, $true, $false, $false)
    try {
        $slide = $presentation.Slides.Item(1)
        $shape = $null
        foreach ($candidate in @($slide.Shapes)) {
            if ($candidate.Id -eq $ShapeId) { $shape = $candidate; break }
        }
        if ($null -eq $shape) { throw "Shape ID $ShapeId not found" }
        $range = $shape.TextFrame2.TextRange
        $items = @()
        for ($index = 1; $index -le $range.Paragraphs().Count; $index++) {
            $paragraph = $range.Paragraphs($index, 1)
            $items += [pscustomobject]@{
                index = $index
                text = [string]$paragraph.Text
                spaceBefore = [double]$paragraph.ParagraphFormat.SpaceBefore
                spaceAfter = [double]$paragraph.ParagraphFormat.SpaceAfter
                lineRuleBefore = $paragraph.ParagraphFormat.LineRuleBefore
                lineRuleAfter = $paragraph.ParagraphFormat.LineRuleAfter
            }
        }
        $items | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $Output -Encoding utf8
    }
    finally {
        $presentation.Close()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation)
    }
}
finally {
    $ppt.Quit()
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($ppt)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
''',
        encoding="utf-8",
    )
    result = run_powershell_file(
        inspect_script,
        "-Deck",
        deck,
        "-ShapeId",
        shape_id,
        "-Output",
        output_path,
    )
    if result.returncode != 0:
        raise AssertionError(f"Spacing inspection failed:\n{result.stdout}\n{result.stderr}")
    return json.loads(output_path.read_text(encoding="utf-8-sig"))


class SermonSkillContractTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/input-contract.md",
            "references/preservation-and-layout.md",
            "references/visual-style.md",
            "references/qa-checklist.md",
            "scripts/discover_sermon_inputs.ps1",
            "scripts/inventory_sermon_pptx.ps1",
            "scripts/apply_scripture_spacing.ps1",
            "scripts/replace_cover_media.ps1",
            "scripts/qa_sermon_pptx.ps1",
            "scripts/render_sermon_pptx.ps1",
            "assets/reference-cover.jpg",
            "assets/reference-scripture.jpg",
            "assets/reference-section.jpg",
            "assets/reference-photo.jpg",
        ]
        missing = [item for item in required if not (SKILL_DIR / item).is_file()]
        self.assertEqual([], missing, f"Missing skill files: {missing}")

    def test_skill_declares_sermon_scope_and_hard_gates(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        required_terms = [
            "Use the **Presentations** skill",
            "discover_sermon_inputs.ps1",
            "inventory_sermon_pptx.ps1",
            "qa_sermon_pptx.ps1",
            "render_sermon_pptx.ps1",
            "STKaiti",
            "slide count",
            "animations",
            "transitions",
            "hard line breaks",
            "text shadow",
            "video",
            "cover",
            "Do not use subagents",
        ]
        missing = [term for term in required_terms if term not in skill]
        self.assertEqual([], missing, f"Missing SKILL.md terms: {missing}")

    def test_visual_style_has_approved_defaults(self):
        style = (SKILL_DIR / "references" / "visual-style.md").read_text(
            encoding="utf-8"
        )
        required_terms = [
            "deep",
            "warm sepia",
            "ivory",
            "muted gold",
            "STKaiti",
            "32pt",
            "22pt",
            "38pt",
            "28pt",
            "20–21pt",
            "52pt",
            "55pt",
            "655pt",
            "325pt",
            "28%",
            "4pt",
            "1.5pt",
        ]
        missing = [term for term in required_terms if term not in style]
        self.assertEqual([], missing, f"Missing visual-style terms: {missing}")

    def test_qa_script_checks_preservation_and_layout_spec(self):
        script = (SKILL_DIR / "scripts" / "qa_sermon_pptx.ps1").read_text(
            encoding="utf-8-sig"
        )
        required_terms = [
            "$SourceDeck",
            "$CandidateDeck",
            "$LayoutSpecPath",
            "Animation-Signature",
            "Transition-Signature",
            "text or hard line breaks changed",
            "VALIDATION PASSED",
        ]
        missing = [term for term in required_terms if term not in script]
        self.assertEqual([], missing, f"Missing QA script terms: {missing}")

    def test_metadata_is_discoverable(self):
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("PCCS Sermon PPTX", metadata)
        self.assertIn("$pccs-sermon-pptx", metadata)
        self.assertIn("sermon", metadata.lower())

    def test_reference_images_are_real_jpegs(self):
        for name in [
            "reference-cover.jpg",
            "reference-scripture.jpg",
            "reference-section.jpg",
            "reference-photo.jpg",
        ]:
            path = SKILL_DIR / "assets" / name
            self.assertGreater(path.stat().st_size, 20_000)
            self.assertEqual(b"\xff\xd8", path.read_bytes()[:2])

    def test_no_personal_paths_are_embedded(self):
        forbidden = [
            "C:" + "\\Users\\",
            "/" + "Users" + "/",
            "/" + "home" + "/",
            "AppData" + "\\",
        ]
        suffixes = {".md", ".py", ".ps1", ".yaml", ".yml", ".json", ".txt"}
        for source_file in SKILL_DIR.rglob("*"):
            if not source_file.is_file() or source_file.suffix.lower() not in suffixes:
                continue
            content = source_file.read_text(encoding="utf-8-sig")
            for marker in forbidden:
                self.assertNotIn(marker, content, f"Personal path in {source_file}")

    @unittest.skipUnless(POWERSHELL, "PowerShell is required")
    def test_cover_media_replacement_preserves_picture_relationship(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            deck = root / "cover-fixture.pptx"
            redraw = root / "redraw.png"
            slide_xml = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:pic><p:nvPicPr><p:cNvPr id="3" name="Cover"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId2"/></p:blipFill><p:spPr/></p:pic></p:spTree></p:cSld></p:sld>'''
            rels_xml = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.tiff"/></Relationships>'''
            old_media = b"old-low-resolution-cover"
            with zipfile.ZipFile(deck, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", slide_xml)
                archive.writestr("ppt/slides/_rels/slide1.xml.rels", rels_xml)
                archive.writestr("ppt/media/image1.tiff", old_media)
            redraw.write_bytes(
                base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAQSURBVBhXY7i1VOE/AzIAACiuAp/fJpBWAAAAAElFTkSuQmCC"
                )
            )

            script = SKILL_DIR / "scripts" / "replace_cover_media.ps1"
            result = run_powershell_file(
                script,
                "-Deck",
                deck,
                "-Redraw",
                redraw,
                "-SlideNumber",
                "1",
                "-ShapeId",
                "3",
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            with zipfile.ZipFile(deck) as archive:
                self.assertEqual(slide_xml, archive.read("ppt/slides/slide1.xml"))
                self.assertEqual(rels_xml, archive.read("ppt/slides/_rels/slide1.xml.rels"))
                new_media = archive.read("ppt/media/image1.tiff")
            self.assertNotEqual(old_media, new_media)
            self.assertIn(new_media[:4], (b"II*\x00", b"MM\x00*"))

    @unittest.skipUnless(POWERSHELL, "PowerShell is required")
    def test_scripture_spacing_is_applied_in_points(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            deck, metadata = create_spacing_fixture(root)
            layout_path = root / "layout.json"
            write_spacing_layout(layout_path, metadata)

            script = SKILL_DIR / "scripts" / "apply_scripture_spacing.ps1"
            result = run_powershell_file(
                script,
                "-Deck",
                deck,
                "-LayoutSpecPath",
                layout_path,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            paragraphs = inspect_spacing(root, deck, metadata["shapeId"])
            self.assertEqual(0, paragraphs[1]["spaceBefore"])
            self.assertEqual(0, paragraphs[2]["spaceBefore"])
            self.assertEqual(4, paragraphs[3]["spaceBefore"])
            for paragraph in paragraphs[1:]:
                self.assertEqual(1, paragraph["spaceAfter"])
                self.assertEqual(0, paragraph["lineRuleBefore"])
                self.assertEqual(0, paragraph["lineRuleAfter"])

    @unittest.skipUnless(POWERSHELL, "PowerShell is required")
    def test_qa_rejects_wrong_verse_spacing_declared_by_layout(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            candidate, metadata = create_spacing_fixture(root)
            source = root / "source.pptx"
            shutil.copy2(candidate, source)
            layout_path = root / "layout.json"
            write_spacing_layout(layout_path, metadata)

            result = run_powershell_file(
                SKILL_DIR / "scripts" / "qa_sermon_pptx.ps1",
                "-SourceDeck",
                source,
                "-CandidateDeck",
                candidate,
                "-LayoutSpecPath",
                layout_path,
                "-ExpectedFont",
                "",
            )
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("verse spacing", (result.stdout + result.stderr).lower())


if __name__ == "__main__":
    unittest.main()
