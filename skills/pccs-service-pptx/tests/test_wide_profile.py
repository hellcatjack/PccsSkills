import unittest
from test_validate_project import ValidateProjectTests, valid_project


class WideProfileTests(ValidateProjectTests):
    def test_accepts_wide_template_and_native_generated_ratio(self):
        data = valid_project()
        data['project'].update(template_profile='wide-v3', background_size_pixels='1672x941', background_geometry_points=[0,0,960,540])
        result = self.run_validator(data)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_wide_profile_rejects_legacy_crop_geometry(self):
        data = valid_project()
        data['project']['template_profile'] = 'wide-v3'
        result = self.run_validator(data)
        self.assertNotEqual(0, result.returncode)
