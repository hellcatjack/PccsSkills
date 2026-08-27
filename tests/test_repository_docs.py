import re
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / "skills"
README = REPOSITORY / "README.md"


class RepositoryDocumentationTests(unittest.TestCase):
    def test_readme_links_every_published_skill(self):
        readme = README.read_text(encoding="utf-8")
        skill_names = sorted(path.name for path in SKILLS.iterdir() if path.is_dir())

        missing_links = [
            skill_name
            for skill_name in skill_names
            if f"[`{skill_name}`](skills/{skill_name}/SKILL.md)" not in readme
        ]

        self.assertEqual([], missing_links, f"README omits skill links: {missing_links}")

    def test_readme_documents_catalog_installation_and_validation(self):
        readme = README.read_text(encoding="utf-8")
        required_sections = [
            "## 技能目录",
            "### PowerPoint 制作",
            "### 讲道视频制作",
            "### 音频与字幕",
            "## 安装与调用",
            "## 验证与维护",
        ]
        missing_sections = [section for section in required_sections if section not in readme]

        self.assertEqual([], missing_sections, f"README omits sections: {missing_sections}")

        required_commands = [
            ".\\skills\\sermon-audio-restoration\\scripts\\bootstrap.ps1",
            ".\\.audio-skill-venv\\Scripts\\python.exe",
        ]
        missing_commands = [command for command in required_commands if command not in readme]
        self.assertEqual([], missing_commands, f"README omits commands: {missing_commands}")

    def test_all_local_markdown_links_resolve(self):
        missing_links = []
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

        markdown_files = [README, *sorted(SKILLS.rglob("*.md"))]
        for markdown_file in markdown_files:
            text = markdown_file.read_text(encoding="utf-8")
            for raw_target in link_pattern.findall(text):
                target = raw_target.split("#", 1)[0].strip()
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (markdown_file.parent / target).resolve()
                if not resolved.exists():
                    missing_links.append(
                        f"{markdown_file.relative_to(REPOSITORY).as_posix()} -> {raw_target}"
                    )

        self.assertEqual([], missing_links, f"Broken local Markdown links: {missing_links}")

    def test_documented_bootstrap_environment_is_ignored(self):
        gitignore = (REPOSITORY / ".gitignore").read_text(encoding="utf-8")

        self.assertIn(
            ".audio-skill-venv/",
            gitignore.splitlines(),
            "sermon-audio-restoration bootstrap output must stay out of Git",
        )

    def test_audio_bootstrap_resolves_to_repository_root(self):
        bootstrap = (
            SKILLS / "sermon-audio-restoration" / "scripts" / "bootstrap.ps1"
        )
        script = bootstrap.read_text(encoding="utf-8")
        match = re.search(
            r"\$projectRoot\s*=\s*\(Resolve-Path\s+\(Join-Path\s+\$PSScriptRoot\s+'([^']+)'\)\)\.Path",
            script,
        )
        self.assertIsNotNone(match, "Cannot identify bootstrap project-root expression")

        relative_root = Path(match.group(1).replace("\\", "/"))
        resolved_root = (bootstrap.parent / relative_root).resolve()
        self.assertEqual(
            REPOSITORY.resolve(),
            resolved_root,
            "audio bootstrap must create its virtual environment inside this repository",
        )


if __name__ == "__main__":
    unittest.main()
