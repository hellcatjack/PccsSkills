import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PROJECT_VALIDATOR = SKILL_DIR / "scripts" / "validate_project.py"
SLIDE_VALIDATOR = SKILL_DIR / "scripts" / "validate_slide_data.py"


def run_validator(script: Path, payload: dict) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as temp_dir:
        fixture = Path(temp_dir) / "fixture.json"
        fixture.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script), str(fixture)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )


def image_project() -> dict:
    return {
        "project": {
            "project_id": "pccs_2026-08-09",
            "service_date": "2026-08-09",
            "template_pptx": "pccsworship.pptx",
        },
        "songs": [
            {
                "index": 1,
                "title": "Song One",
                "source_mode": "images",
                "image_files": ["01_song.png"],
                "youtube_urls": [],
                "youtube_search_hint": "",
                "arrangement": "V C V C End*2",
            }
        ],
    }


def youtube_search_project() -> dict:
    payload = image_project()
    payload["songs"][0].update(
        {
            "source_mode": "youtube_search",
            "image_files": [],
            "youtube_urls": [],
            "youtube_search_hint": "Song One official worship",
            "arrangement": "",
        }
    )
    return payload


def valid_slide_data() -> dict:
    return {
        "songs": [
            {
                "id": "song-1",
                "title": "Song One",
                "arrangement_expanded": ["V", "C", "End", "End"],
            }
        ],
        "pages": [
            {
                "role": "song_first",
                "title": "Song One",
                "lines": ["Hallelujah", "There is glory here"],
                "font": "KaiTi",
                "title_font_pt": 54,
                "body_font_pt": 48,
                "song_id": "song-1",
                "section_code": "V",
                "performance_index": 1,
            },
            {
                "role": "song_continuation",
                "title": "Song One",
                "lines": ["Worship with all your heart", "Shout aloud"],
                "font": "KaiTi",
                "title_font_pt": 28,
                "body_font_pt": 48,
                "song_id": "song-1",
                "section_code": "C",
                "performance_index": 2,
            },
            {
                "role": "song_continuation",
                "title": "Song One",
                "lines": ["There is glory here"],
                "font": "KaiTi",
                "title_font_pt": 28,
                "body_font_pt": 48,
                "song_id": "song-1",
                "section_code": "End",
                "performance_index": 3,
            },
            {
                "role": "song_continuation",
                "title": "Song One",
                "lines": ["There is glory here"],
                "font": "KaiTi",
                "title_font_pt": 28,
                "body_font_pt": 48,
                "song_id": "song-1",
                "section_code": "End",
                "performance_index": 4,
            },
        ],
    }


class ProjectValidatorTests(unittest.TestCase):
    def test_accepts_image_source_with_explicit_arrangement(self):
        result = run_validator(PROJECT_VALIDATOR, image_project())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("pass", json.loads(result.stdout)["status"])

    def test_accepts_youtube_search_without_arrangement_and_warns(self):
        result = run_validator(PROJECT_VALIDATOR, youtube_search_project())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["warnings"])

    def test_rejects_song_without_any_source(self):
        payload = image_project()
        payload["songs"][0].update(
            {
                "source_mode": "auto",
                "image_files": [],
                "youtube_urls": [],
                "youtube_search_hint": "",
            }
        )
        result = run_validator(PROJECT_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("source", result.stderr.lower())

    def test_rejects_blank_or_null_source_entries(self):
        payload = image_project()
        payload["songs"][0].update(
            {
                "source_mode": "images",
                "image_files": ["", "   ", None],
                "youtube_urls": [],
                "youtube_search_hint": "",
            }
        )
        result = run_validator(PROJECT_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("source", result.stderr.lower())

    def test_warns_when_url_needs_concrete_video_matching(self):
        payload = image_project()
        payload["songs"][0].update(
            {
                "source_mode": "youtube",
                "image_files": [],
                "youtube_urls": ["https://www.youtube.com/channel/UC123"],
            }
        )
        result = run_validator(PROJECT_VALIDATOR, payload)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(
            any("match" in warning.lower() for warning in json.loads(result.stdout)["warnings"])
        )

    def test_warns_when_playlist_needs_song_by_song_matching(self):
        payload = image_project()
        payload["songs"][0].update(
            {
                "source_mode": "youtube",
                "image_files": [],
                "youtube_urls": ["https://www.youtube.com/playlist?list=PL123"],
            }
        )
        result = run_validator(PROJECT_VALIDATOR, payload)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(
            any("match" in warning.lower() for warning in json.loads(result.stdout)["warnings"])
        )

    def test_rejects_performance_note_inside_arrangement_token(self):
        payload = image_project()
        payload["songs"][0]["arrangement"] = "V C2\u8df3\u97f3 End"
        result = run_validator(PROJECT_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("special_notes", result.stderr)


class SlideDataValidatorTests(unittest.TestCase):
    def test_accepts_fully_expanded_valid_slide_data(self):
        result = run_validator(SLIDE_VALIDATOR, valid_slide_data())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(4, json.loads(result.stdout)["performance_sections"])

    def test_rejects_four_body_lines(self):
        payload = valid_slide_data()
        payload["pages"][0]["lines"] = ["One", "Two", "Three", "Four"]
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("at most 3 lines", result.stderr.lower())

    def test_rejects_body_font_below_48pt(self):
        payload = valid_slide_data()
        payload["pages"][0]["body_font_pt"] = 47
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("48", result.stderr)

    def test_rejects_lyric_punctuation(self):
        payload = valid_slide_data()
        payload["pages"][0]["lines"] = ["Hallelujah\uff0c", "There is glory here"]
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("punctuation", result.stderr.lower())

    def test_rejects_repeat_shorthand_in_expanded_arrangement(self):
        payload = valid_slide_data()
        payload["songs"][0]["arrangement_expanded"] = ["V", "C", "End*2"]
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("expanded", result.stderr.lower())

    def test_rejects_non_string_section_in_expanded_arrangement(self):
        payload = valid_slide_data()
        payload["songs"][0]["arrangement_expanded"] = ["V", None, "End", "End"]
        payload["pages"][1]["section_code"] = "None"
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("section", result.stderr.lower())

    def test_accepts_multiple_pages_for_one_performed_section(self):
        payload = valid_slide_data()
        continuation = copy.deepcopy(payload["pages"][1])
        continuation["lines"] = ["Second page of the same chorus"]
        payload["pages"].insert(2, continuation)
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(4, json.loads(result.stdout)["performance_sections"])

    def test_rejects_page_sequence_that_disagrees_with_expansion(self):
        payload = valid_slide_data()
        payload["pages"][1]["section_code"] = "B"
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("does not match expanded arrangement", result.stderr)

    def test_rejects_reversed_song_order(self):
        payload = valid_slide_data()
        second_song = copy.deepcopy(payload["songs"][0])
        second_song.update(
            {"id": "song-2", "title": "Song Two", "arrangement_expanded": ["V"]}
        )
        second_page = copy.deepcopy(payload["pages"][0])
        second_page.update(
            {
                "title": "Song Two",
                "song_id": "song-2",
                "section_code": "V",
                "performance_index": 1,
            }
        )
        payload["songs"].append(second_song)
        payload["pages"] = [second_page] + payload["pages"]
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("song order", result.stderr.lower())

    def test_rejects_song_without_exactly_one_first_page(self):
        payload = valid_slide_data()
        payload["pages"][0]["role"] = "song_continuation"
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("song_first", result.stderr)

    def test_rejects_unknown_page_role(self):
        payload = valid_slide_data()
        payload["pages"][0]["role"] = "lyrics"
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("role", result.stderr.lower())

    def test_rejects_missing_or_mismatched_song_title(self):
        payload = valid_slide_data()
        payload["pages"][1]["title"] = "Wrong Song"
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("title", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
