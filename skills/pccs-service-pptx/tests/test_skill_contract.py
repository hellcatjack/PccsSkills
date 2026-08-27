import unittest
import zipfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "assets/pccsworship.pptx",
            "references/input-contract.md",
            "references/content-rules.md",
            "references/visual-style.md",
            "references/qa-checklist.md",
            "scripts/validate_project.py",
            "scripts/qa_pccs_service_pptx.ps1",
        ]
        missing = [item for item in required if not (SKILL_DIR / item).is_file()]
        self.assertEqual([], missing, f"Missing skill files: {missing}")

    def test_skill_declares_non_lyric_scope_and_visual_invariants(self):
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.is_file(), f"Missing {skill_path}")
        skill = skill_path.read_text(encoding="utf-8")
        required_terms = [
            "pccs-worship-pptx",
            "Presentations",
            "references/input-contract.md",
            "references/content-rules.md",
            "references/visual-style.md",
            "references/qa-checklist.md",
            "assets/pccsworship.pptx",
            "1920x920",
            "48:23",
            "0,0,720,345",
            "PCCS logo tip overlay",
            "MatchingName",
            "Click to add title",
            "Click to add subtitle",
            "复制",
            "经文",
            "二维码",
            "非歌词",
        ]
        missing = [term for term in required_terms if term not in skill]
        self.assertEqual([], missing, f"Missing SKILL.md terms: {missing}")

    def test_bundled_template_is_a_valid_two_slide_pptx(self):
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

    def test_openai_yaml_exposes_service_slide_skill(self):
        metadata_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(metadata_path.is_file(), f"Missing {metadata_path}")
        metadata = metadata_path.read_text(encoding="utf-8")
        self.assertIn("PCCS Service PPTX", metadata)
        self.assertIn("$pccs-service-pptx", metadata)
        self.assertIn("non-lyric", metadata.lower())

    def test_powerpoint_qa_accepts_a_layout_background_name_pattern(self):
        script_path = SKILL_DIR / "scripts" / "qa_pccs_service_pptx.ps1"
        self.assertTrue(script_path.is_file(), f"Missing {script_path}")
        script = script_path.read_text(encoding="utf-8-sig")
        self.assertIn("BackgroundNamePattern", script)
        self.assertGreaterEqual(script.count("-like $BackgroundNamePattern"), 2)

    def test_visual_style_captures_recent_cover_and_hierarchy_contract(self):
        style = (SKILL_DIR / "references" / "visual-style.md").read_text(
            encoding="utf-8"
        )
        style_terms = [
            "first slide",
            "highest visual scrutiny",
            "front-row sightlines",
            "top half",
            "editable emphasis shapes",
            "dominant dark-purple block",
            "latest effective template",
        ]
        missing_style = [term for term in style_terms if term not in style]
        self.assertEqual([], missing_style, f"Missing visual-style terms: {missing_style}")

        checklist = (SKILL_DIR / "references" / "qa-checklist.md").read_text(
            encoding="utf-8"
        )
        checklist_terms = [
            "first slide",
            "highest visual scrutiny",
            "front-row sightlines",
            "editable emphasis shapes",
            "dominant dark-purple block",
            "latest effective template",
        ]
        missing_checklist = [term for term in checklist_terms if term not in checklist]
        self.assertEqual(
            [], missing_checklist, f"Missing QA checklist terms: {missing_checklist}"
        )

    def test_repository_copy_has_no_personal_install_path(self):
        forbidden_markers = [
            "C:" + "\\Users\\",
            "/" + "Users" + "/",
            "/" + "home" + "/",
            "AppData" + "\\",
        ]
        text_suffixes = {".md", ".py", ".ps1", ".yaml", ".yml", ".json", ".txt"}
        for source_file in SKILL_DIR.rglob("*"):
            if not source_file.is_file() or source_file.suffix.lower() not in text_suffixes:
                continue
            content = source_file.read_text(encoding="utf-8")
            for marker in forbidden_markers:
                self.assertNotIn(marker, content, f"Personal path in {source_file}")

    def test_repository_readme_lists_the_skill(self):
        readme_path = SKILL_DIR.parents[1] / "README.md"
        if not readme_path.is_file():
            self.skipTest("Repository README is not included in an installed skill copy")
        readme = readme_path.read_text(encoding="utf-8")
        self.assertIn("pccs-service-pptx", readme)


if __name__ == "__main__":
    unittest.main()
