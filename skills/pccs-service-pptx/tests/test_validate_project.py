import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_project.py"


def valid_project():
    return {
        "project": {
            "project_id": "pccs-service-2026-08-30",
            "service_date": "2026-08-30",
            "language": "简体中文",
            "template_pptx": "",
            "background_size_pixels": "1920x920",
            "background_geometry_points": [0, 0, 720, 345],
        },
        "slides": [
            {
                "index": 1,
                "type": "cover",
                "title": "主日崇拜",
                "body_lines": ["匹兹堡南区基督教会"],
                "background_direction": "圣所晨光",
            },
            {
                "index": 2,
                "type": "scripture",
                "title": "诗篇100篇",
                "source_lines": [
                    "普天下当向耶和华欢呼",
                    "你们当乐意侍奉耶和华",
                ],
                "preserve_source_lines": True,
                "single_slide": True,
            },
            {
                "index": 3,
                "type": "qr",
                "title": "线上周报",
                "asset_files": ["bulletin-qr.png"],
                "background_direction": "明亮纸张与窗影",
            },
        ],
        "deliverables": {
            "output_pptx": "PCCS主日流程.pptx",
            "powerpoint_duplicate_test": True,
        },
    }


class ValidateProjectTests(unittest.TestCase):
    def run_validator(self, project):
        self.assertTrue(VALIDATOR.is_file(), f"Missing validator: {VALIDATOR}")
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "project.json"
            project_path.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(project_path)],
                text=True,
                capture_output=True,
                encoding="utf-8",
            )

    def test_accepts_valid_non_lyric_service_project(self):
        result = self.run_validator(valid_project())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("VALID", result.stdout)

    def test_rejects_lyric_slide_type(self):
        project = valid_project()
        project["slides"][0]["type"] = "lyrics"
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("lyrics", result.stderr)

    def test_rejects_wrong_background_geometry(self):
        project = valid_project()
        project["project"]["background_geometry_points"] = [0, -60, 720, 405]
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("background_geometry_points", result.stderr)

    def test_scripture_requires_preserved_source_lines(self):
        project = valid_project()
        project["slides"][1].pop("preserve_source_lines")
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("preserve_source_lines", result.stderr)

    def test_indexes_must_be_consecutive(self):
        project = valid_project()
        project["slides"][2]["index"] = 4
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("consecutive", result.stderr)


if __name__ == "__main__":
    unittest.main()
