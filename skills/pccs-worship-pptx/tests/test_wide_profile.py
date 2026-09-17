import copy
import unittest
from test_validators import valid_slide_data, run_validator, SLIDE_VALIDATOR


class WideProfileTests(unittest.TestCase):
    def wide_data(self):
        data = valid_slide_data()
        data['template_profile'] = 'wide-v3'
        for page in data['pages']:
            page['body_font_pt'] = 52
            if page['role'] == 'song_first':
                page['title_font_pt'] = 40
        return data

    def test_accepts_wide_52pt_lyrics_and_40pt_title(self):
        result = run_validator(SLIDE_VALIDATOR, self.wide_data())
        self.assertEqual(0, result.returncode, result.stderr)

    def test_rejects_one_page_silently_reduced_to_48pt(self):
        data = self.wide_data()
        data['pages'][1]['body_font_pt'] = 48
        result = run_validator(SLIDE_VALIDATOR, data)
        self.assertNotEqual(0, result.returncode)

    def test_accepts_documented_template_typography(self):
        data = self.wide_data()
        data['typography'] = {'basis': 'user_supplied_template', 'lyric_font_pt': 50, 'title_font_pt': 42, 'lyric_font': 'KaiTi', 'scripture_font': 'SimSun'}
        for page in data['pages']:
            page['body_font_pt'] = 50
            if page['role'] == 'song_first': page['title_font_pt'] = 42
        result = run_validator(SLIDE_VALIDATOR, data)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_rejects_unknown_profile(self):
        data = self.wide_data()
        data['template_profile'] = 'typo'
        self.assertNotEqual(0, run_validator(SLIDE_VALIDATOR, data).returncode)
