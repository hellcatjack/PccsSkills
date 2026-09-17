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


def project_with_scripture() -> dict:
    payload = image_project()
    payload["scripture"] = [
        {
            "id": "scripture-1",
            "position": "before_song_1",
            "reference": "诗篇 62:5-8",
            "source_file": "guide.txt",
            "source_lines": [
                "我的心哪，你当默默无声，专等候神，",
                "因为我的盼望是从他而来。",
            ],
            "preserve_line_breaks": True,
            "single_slide": True,
        }
    ]
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
                "title_font_pt": 44,
                "body_font_pt": 40,
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
                "body_font_pt": 40,
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
                "body_font_pt": 40,
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
                "body_font_pt": 40,
                "song_id": "song-1",
                "section_code": "End",
                "performance_index": 4,
            },
        ],
    }


def valid_slide_data_with_scripture() -> dict:
    payload = valid_slide_data()
    source_lines = [
        "我的心哪，你当默默无声，专等候神，",
        "因为我的盼望是从他而来。",
        "惟独他是我的磐石，我的拯救；",
        "他是我的高台，我必不动摇。",
        "我的拯救、我的荣耀都在乎神；",
        "我力量的磐石、我的避难所都在乎神。",
        "你们众民当时时倚靠他，",
        "在他面前倾心吐意；",
        "神是我们的避难所。",
    ]
    payload["scriptures"] = [
        {
            "id": "scripture-1",
            "reference": "诗篇 62:5-8",
            "source_file": "guide.txt",
            "source_lines": source_lines,
            "preserve_line_breaks": True,
            "single_slide": True,
        }
    ]
    payload["pages"].insert(
        0,
        {
            "role": "scripture",
            "scripture_id": "scripture-1",
            "lines": list(source_lines),
            "font": "SimSun",
            "alignment": "left",
            "body_font_pt": 30,
        },
    )
    return payload


class ProjectValidatorTests(unittest.TestCase):
    def test_rejects_empty_or_non_array_project_credits(self):
        for value in ([], "Publisher", [""]):
            payload = image_project()
            payload["songs"][0]["credit_lines"] = value
            result = run_validator(PROJECT_VALIDATOR, payload)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("credit_lines", result.stderr)

    def test_rejects_unreconstructable_scripture_number_metadata(self):
        payload = project_with_scripture()
        scripture = payload["scripture"][0]
        scripture.update(raw_source_lines=["wrong", "source"], verse_prefixes=["1", ""], verse_numbers=["1", ""], translation="Provided edition", verse_boundaries_verified=True, verse_metadata_audit="Verified source")
        result = run_validator(PROJECT_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("reconstruct", result.stderr)

    def test_accepts_image_source_with_explicit_arrangement(self):
        result = run_validator(PROJECT_VALIDATOR, image_project())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("pass", json.loads(result.stdout)["status"])

    def test_uses_bundled_template_when_project_does_not_specify_one(self):
        payload = image_project()
        payload["project"].pop("template_pptx")

        result = run_validator(PROJECT_VALIDATOR, payload)

        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual("assets/pccs-wide-v3.pptx", summary["effective_template_pptx"])
        self.assertEqual("wide-v3", summary["template_profile"])
        self.assertEqual("skill_default", summary["template_source"])

    def test_user_template_overrides_bundled_default(self):
        payload = image_project()
        payload["project"]["template_pptx"] = "custom-template.pptx"

        result = run_validator(PROJECT_VALIDATOR, payload)

        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual("custom-template.pptx", summary["effective_template_pptx"])
        self.assertEqual("user_supplied", summary["template_source"])

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

    def test_accepts_scripture_normalized_as_exact_source_lines(self):
        result = run_validator(PROJECT_VALIDATOR, project_with_scripture())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, json.loads(result.stdout)["scripture_count"])

    def test_rejects_scripture_without_source_lines(self):
        payload = project_with_scripture()
        payload["scripture"][0].pop("source_lines")
        payload["scripture"][0]["text"] = "第一行 第二行"

        result = run_validator(PROJECT_VALIDATOR, payload)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("source_lines", result.stderr)

    def test_rejects_scripture_when_line_break_preservation_is_disabled(self):
        payload = project_with_scripture()
        payload["scripture"][0]["preserve_line_breaks"] = False

        result = run_validator(PROJECT_VALIDATOR, payload)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("preserve_line_breaks", result.stderr)


class SlideDataValidatorTests(unittest.TestCase):
    def test_default_first_song_page_has_room_for_only_two_lines(self):
        payload = valid_slide_data()
        payload["pages"][0]["lines"] = ["First line", "Second line", "Third line"]
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("first-page", result.stderr)

    def test_accepts_an_explicit_service_style_override_in_a_mixed_deck(self):
        payload = valid_slide_data_with_scripture()
        payload["pages"][0].update(font="SimHei", body_font_pt=32, style_override_reason="User explicitly requested SimHei scripture")
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_rejects_scripture_after_songs_when_before_song_is_requested(self):
        payload = valid_slide_data_with_scripture()
        payload["scriptures"][0]["position"] = "before_song_1"
        payload["pages"].append(payload["pages"].pop(0))
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("position", result.stderr)

    def test_rejects_unverified_verse_metadata_in_slide_plan(self):
        payload = valid_slide_data_with_scripture()
        source = payload["scriptures"][0]
        source["raw_source_lines"] = source["source_lines"]
        source["verse_prefixes"] = [""] * len(source["source_lines"])
        source["verse_numbers"] = [""] * len(source["source_lines"])
        source["verse_boundaries_verified"] = False
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("verse_boundaries_verified", result.stderr)

    def test_rejects_empty_declared_song_credits(self):
        payload = valid_slide_data()
        payload["songs"][0]["credit_lines"] = [" "]
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("credit_lines", result.stderr)

    def test_accepts_explicit_lyric_size_override_without_editing_validator(self):
        payload = valid_slide_data()
        payload["typography"] = {"lyric_font_pt": 42, "title_font_pt": 46, "override_reason": "User requested 42pt lyrics and 46pt titles"}
        for page in payload["pages"]:
            page["body_font_pt"] = 42
        payload["pages"][0]["title_font_pt"] = 46
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_rejects_unexplained_lyric_size_override(self):
        payload = valid_slide_data()
        payload["typography"] = {"lyric_font_pt": 42}
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("override_reason", result.stderr)

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

    def test_rejects_old_lyric_size(self):
        payload = valid_slide_data()
        payload["pages"][0]["body_font_pt"] = 48
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("40", result.stderr)

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

    def test_accepts_two_consecutive_end_performances_on_one_page(self):
        payload = valid_slide_data()
        grouped_end = copy.deepcopy(payload["pages"][2])
        grouped_end.pop("performance_index")
        grouped_end["performance_indexes"] = [3, 4]
        grouped_end["lines"] = ["There is glory here", "There is glory here"]
        payload["pages"] = payload["pages"][:2] + [grouped_end]

        result = run_validator(SLIDE_VALIDATOR, payload)

        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(3, summary["page_count"])
        self.assertEqual(4, summary["performance_sections"])

    def test_rejects_nonconsecutive_grouped_end_indexes(self):
        payload = valid_slide_data()
        grouped_end = copy.deepcopy(payload["pages"][2])
        grouped_end.pop("performance_index")
        grouped_end["performance_indexes"] = [3, 5]
        grouped_end["lines"] = ["There is glory here", "There is glory here"]
        payload["pages"] = payload["pages"][:2] + [grouped_end]

        result = run_validator(SLIDE_VALIDATOR, payload)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("consecutive", result.stderr.lower())

    def test_rejects_grouped_end_when_lines_do_not_match_repetitions(self):
        payload = valid_slide_data()
        grouped_end = copy.deepcopy(payload["pages"][2])
        grouped_end.pop("performance_index")
        grouped_end["performance_indexes"] = [3, 4]
        grouped_end["lines"] = ["There is glory here", "Different ending"]
        payload["pages"] = payload["pages"][:2] + [grouped_end]

        result = run_validator(SLIDE_VALIDATOR, payload)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("identical", result.stderr.lower())

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

    def test_accepts_single_slide_scripture_with_exact_txt_line_boundaries(self):
        payload = valid_slide_data_with_scripture()

        result = run_validator(SLIDE_VALIDATOR, payload)

        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(1, summary["scripture_count"])
        self.assertEqual(9, summary["scripture_source_lines"])

    def test_rejects_scripture_above_36pt(self):
        payload = valid_slide_data_with_scripture()
        payload["pages"][0]["body_font_pt"] = 40
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("36", result.stderr)

    def test_rejects_centered_scripture(self):
        payload = valid_slide_data_with_scripture()
        payload["pages"][0]["alignment"] = "center"
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("left", result.stderr)

    def test_rejects_font_changes_within_one_passage(self):
        payload = valid_slide_data_with_scripture()
        payload["scriptures"][0]["single_slide"] = False
        first = payload["pages"][0]
        second = copy.deepcopy(first)
        first["lines"], second["lines"] = first["lines"][:4], first["lines"][4:]
        second["body_font_pt"] = 36
        payload["pages"].insert(1, second)
        result = run_validator(SLIDE_VALIDATOR, payload)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("uniform", result.stderr)

    def test_rejects_scripture_lines_merged_from_txt_source(self):
        payload = valid_slide_data_with_scripture()
        payload["pages"][0]["lines"] = [
            "我的心哪，你当默默无声，专等候神，因为我的盼望是从他而来。",
            *payload["pages"][0]["lines"][2:],
        ]

        result = run_validator(SLIDE_VALIDATOR, payload)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("exact text, order, and line boundaries", result.stderr.lower())

    def test_rejects_scripture_lines_reordered_from_txt_source(self):
        payload = valid_slide_data_with_scripture()
        payload["pages"][0]["lines"][0:2] = reversed(
            payload["pages"][0]["lines"][0:2]
        )

        result = run_validator(SLIDE_VALIDATOR, payload)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("exact text, order, and line boundaries", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
