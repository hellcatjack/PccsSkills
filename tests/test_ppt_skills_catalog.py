import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / "skills"


class PccsPptSkillsCatalogTests(unittest.TestCase):
    def test_all_pccs_ppt_skills_are_publishable(self):
        required_by_skill = {
            "pccs-worship-pptx": [
                "SKILL.md",
                "agents/openai.yaml",
                "references/qa-checklist.md",
                "tests/test_pccs_worship_skill_contract.py",
            ],
            "pccs-service-pptx": [
                "SKILL.md",
                "agents/openai.yaml",
                "references/qa-checklist.md",
                "tests/test_skill_contract.py",
            ],
            "pccs-sermon-pptx": [
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
                "tests/test_skill_contract.py",
            ],
        }

        missing = []
        for skill_name, relative_paths in required_by_skill.items():
            for relative_path in relative_paths:
                path = SKILLS / skill_name / relative_path
                if not path.is_file():
                    missing.append(path.relative_to(REPOSITORY).as_posix())

        self.assertEqual([], missing, f"Missing publishable PPT skill files: {missing}")

    def test_readme_catalogs_all_pccs_ppt_skills(self):
        readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
        missing = [
            skill_name
            for skill_name in (
                "pccs-worship-pptx",
                "pccs-service-pptx",
                "pccs-sermon-pptx",
            )
            if f"`{skill_name}`" not in readme
        ]
        self.assertEqual([], missing, f"README omits PPT skills: {missing}")


if __name__ == "__main__":
    unittest.main()
