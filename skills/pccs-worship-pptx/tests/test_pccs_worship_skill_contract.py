import unittest
import zipfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/input-contract.md",
            "references/source-resolution.md",
            "references/lyrics-pipeline.md",
            "references/ppt-template-rules.md",
            "references/qa-checklist.md",
            "scripts/validate_project.py",
            "scripts/validate_slide_data.py",
            "scripts/validate_final_pptx.mjs",
            "assets/pccsworship.pptx",
        ]
        missing = [item for item in required if not (SKILL_DIR / item).is_file()]
        self.assertEqual([], missing, f"Missing skill files: {missing}")

    def test_skill_links_references_and_hard_requirements(self):
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.is_file(), f"Missing {skill_path}")
        skill = skill_path.read_text(encoding="utf-8")
        required_terms = [
            "references/input-contract.md",
            "references/source-resolution.md",
            "references/lyrics-pipeline.md",
            "references/ppt-template-rules.md",
            "references/qa-checklist.md",
            "lyrics_audit.md",
            "complete_lyrics.md",
            "Presentations",
            "44pt",
            "40pt",
            "NameFarEast",
            "YouTube",
            "\u6b4c\u8bcd\u56fe\u7247",
            "\u590d\u5236",
            "performance_indexes",
            "End*2",
            "source_lines",
            "TXT",
            "assets/pccsworship.pptx",
            "validate_final_pptx.mjs",
        ]
        missing = [term for term in required_terms if term not in skill]
        self.assertEqual([], missing, f"Missing SKILL.md terms: {missing}")

    def test_bundled_default_template_is_a_valid_two_slide_pptx(self):
        template_path = SKILL_DIR / "assets" / "pccsworship.pptx"
        self.assertTrue(template_path.is_file(), f"Missing {template_path}")
        self.assertGreater(template_path.stat().st_size, 0)

        with zipfile.ZipFile(template_path) as package:
            entries = set(package.namelist())

        required_entries = {
            "[Content_Types].xml",
            "ppt/presentation.xml",
            "ppt/slides/slide1.xml",
            "ppt/slides/slide2.xml",
        }
        self.assertTrue(required_entries.issubset(entries))
        slide_entries = {
            entry
            for entry in entries
            if entry.startswith("ppt/slides/slide") and entry.endswith(".xml")
        }
        self.assertEqual(2, len(slide_entries))

    def test_openai_yaml_has_explicit_invocation(self):
        metadata_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(metadata_path.is_file(), f"Missing {metadata_path}")
        metadata = metadata_path.read_text(encoding="utf-8")
        self.assertIn("PCCS Worship PPTX", metadata)
        self.assertIn("$pccs-worship-pptx", metadata)
        self.assertIn("bundled", metadata.lower())

    def test_visual_style_captures_recent_beautification_contract(self):
        style = (SKILL_DIR / "references" / "visual-style.md").read_text(
            encoding="utf-8"
        )
        style_terms = [
            "1920x920",
            "48:23",
            "720x345",
            "x=80..300px",
            "y=760..920px",
            "warm pearl-white",
            "front-row sightlines",
            "two lyric lines",
            "top-align",
            "PCCS logo tip overlay",
            "TextFrame2.TextRange.Font.Shadow",
        ]
        missing_style = [term for term in style_terms if term not in style]
        self.assertEqual([], missing_style, f"Missing visual-style terms: {missing_style}")

        checklist = (SKILL_DIR / "references" / "qa-checklist.md").read_text(
            encoding="utf-8"
        )
        checklist_terms = [
            "1920x920",
            "48:23",
            "front-row sightlines",
            "two-line first page",
            "top-aligned",
            "warm pearl-white",
        ]
        missing_checklist = [term for term in checklist_terms if term not in checklist]
        self.assertEqual(
            [], missing_checklist, f"Missing QA checklist terms: {missing_checklist}"
        )

    def test_score_aware_pagination_and_actual_font_audit_are_documented(self):
        template_rules = (
            SKILL_DIR / "references" / "ppt-template-rules.md"
        ).read_text(encoding="utf-8")
        rule_terms = [
            "musical phrase",
            "breath",
            "two lyric lines",
            "actual rendered runs",
            "44pt",
        ]
        missing_rules = [term for term in rule_terms if term not in template_rules]
        self.assertEqual([], missing_rules, f"Missing pagination rules: {missing_rules}")

        checklist = (SKILL_DIR / "references" / "qa-checklist.md").read_text(
            encoding="utf-8"
        )
        checklist_terms = [
            "validate_final_pptx.mjs",
            "actual PPTX",
            "pixel-identical",
        ]
        missing_checklist = [
            term for term in checklist_terms if term not in checklist
        ]
        self.assertEqual(
            [], missing_checklist, f"Missing final-deck QA terms: {missing_checklist}"
        )

    def test_repository_copy_has_no_personal_install_path(self):
        forbidden_markers = [
            "C:" + "\\Users\\",
            "/" + "Users" + "/",
            "/" + "home" + "/",
            "AppData" + "\\",
        ]
        text_suffixes = {".md", ".py", ".yaml", ".yml", ".json", ".txt"}
        for source_file in SKILL_DIR.rglob("*"):
            if not source_file.is_file() or source_file.suffix.lower() not in text_suffixes:
                continue
            content = source_file.read_text(encoding="utf-8")
            for marker in forbidden_markers:
                self.assertNotIn(marker, content, f"Personal path in {source_file}")


if __name__ == "__main__":
    unittest.main()
