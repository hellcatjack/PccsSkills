import json
import copy
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

    def test_scripture_accepts_explicit_left_aligned_simsun_36(self):
        project = valid_project()
        project["slides"][1].update(body_font="SimSun", body_font_pt=36, alignment="left", body_shadow=False)
        result = self.run_validator(project)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_scripture_rejects_oversize_centered_or_shadowed_body(self):
        for field, value in [("body_font_pt", 48), ("alignment", "center"), ("body_shadow", True)]:
            with self.subTest(field=field):
                project = valid_project()
                project["slides"][1][field] = value
                result = self.run_validator(project)
                self.assertNotEqual(0, result.returncode, f"Accepted {field}={value}")
                self.assertIn(field, result.stderr)

    def test_scripture_explicit_user_style_override_is_recorded(self):
        project = valid_project()
        project["slides"][1].update(body_font="KaiTi", alignment="center", style_override_reason="User explicitly requested this template style.")
        result = self.run_validator(project)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_scripture_rejects_mixed_sizes_within_one_passage(self):
        project = valid_project()
        project["slides"][1].update(scripture_id="reading-1", body_font_pt=36, single_slide=False)
        continuation = copy.deepcopy(project["slides"][1])
        continuation.update(index=4, body_font_pt=32)
        project["slides"].append(continuation)
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("uniform", result.stderr)

    def test_scripture_accepts_audited_verse_metadata_with_exact_raw_text(self):
        project = valid_project()
        project["slides"][1].update(
            source_lines=["普天下当向耶和华欢呼。", "你们当乐意侍奉耶和华。"],
            raw_source_lines=["1　普天下当向耶和华欢呼。", "2　你们当乐意侍奉耶和华。"],
            verse_numbers=["1", "2"], verse_prefixes=["1　", "2　"],
            verse_metadata_audit="Checked verse boundaries against the supplied edition.",
            translation="User-supplied edition", verse_boundaries_verified=True,
        )
        result = self.run_validator(project)
        self.assertEqual(0, result.returncode, result.stderr)
        project["slides"][1]["source_lines"][0] = "普天下当向耶和华欢呼！"
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("raw_source_lines", result.stderr)

    def test_scripture_verse_metadata_requires_audit_and_boundary_verification(self):
        project = valid_project()
        project["slides"][1]["verse_numbers"] = ["1", "2"]
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("raw_source_lines", result.stderr)

    def test_non_fixed_source_lines_allow_visual_wrapping(self):
        project = valid_project()
        project["slides"][1].update(source_lines_fixed=False, allow_visual_wrap=True)
        result = self.run_validator(project)
        self.assertEqual(0, result.returncode, result.stderr)
        project["slides"][1]["source_lines_fixed"] = True
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("allow_visual_wrap", result.stderr)

    def test_accepts_measured_near_ratio_background_without_cropping(self):
        project = valid_project()
        project["project"].update(background_size_pixels="1920x920", background_actual_size_pixels=[2048, 981], background_size_audit="Measured output; placed complete at 0,0,720,345.")
        result = self.run_validator(project)
        self.assertEqual(0, result.returncode, result.stderr)
        project["project"]["background_actual_size_pixels"] = [1920, 1080]
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("ratio", result.stderr)

    def test_measured_non_target_background_requires_audit(self):
        project = valid_project()
        project["project"]["background_actual_size_pixels"] = [2048, 981]
        result = self.run_validator(project)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("background_size_audit", result.stderr)

    def test_service_pages_can_map_to_nonconsecutive_mixed_deck_positions(self):
        project = valid_project()
        for slide, final_index in zip(project["slides"], [2, 17, 42]):
            slide["final_slide_index"] = final_index
        result = self.run_validator(project)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_mixed_deck_mapping_rejects_duplicate_and_noninteger_final_indexes(self):
        for invalid_index in [2, 0, -1, True, 2.5, "17"]:
            with self.subTest(final_slide_index=invalid_index):
                project = valid_project()
                project["slides"][0]["final_slide_index"] = invalid_index
                result = self.run_validator(project)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("final_slide_index", result.stderr)


if __name__ == "__main__":
    unittest.main()
