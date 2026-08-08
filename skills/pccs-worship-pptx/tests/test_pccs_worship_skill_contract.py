import unittest
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
            "54pt",
            "48pt",
            "NameFarEast",
            "YouTube",
            "\u6b4c\u8bcd\u56fe\u7247",
            "\u590d\u5236",
        ]
        missing = [term for term in required_terms if term not in skill]
        self.assertEqual([], missing, f"Missing SKILL.md terms: {missing}")

    def test_openai_yaml_has_explicit_invocation(self):
        metadata_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(metadata_path.is_file(), f"Missing {metadata_path}")
        metadata = metadata_path.read_text(encoding="utf-8")
        self.assertIn("PCCS Worship PPTX", metadata)
        self.assertIn("$pccs-worship-pptx", metadata)

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
