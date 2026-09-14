"""PowerShell safety and pure-helper checks; never starts PowerPoint."""
import shutil
import subprocess
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "qa_pccs_service_pptx.ps1"
HELPERS = SKILL_DIR / "scripts" / "qa_pccs_service_helpers.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(POWERSHELL, "PowerShell is unavailable")
class QaSafetyTests(unittest.TestCase):
    def run_ps(self, source):
        result = subprocess.run([POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", source], text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_script_parses_and_never_calls_application_quit(self):
        script = str(SCRIPT).replace("'", "''")
        self.run_ps(f"""
        $tokens=$null; $errors=$null
        $ast=[System.Management.Automation.Language.Parser]::ParseFile('{script}',[ref]$tokens,[ref]$errors)
        if ($errors.Count) {{ throw ($errors | Out-String) }}
        $quit=$ast.FindAll({{param($node) $node -is [System.Management.Automation.Language.InvokeMemberExpressionAst] -and $node.Member.Value -eq 'Quit'}},$true)
        if ($quit.Count) {{ throw 'QA must never quit the shared PowerPoint application.' }}
        """)

    def test_layout_registration_distinguishes_masters_and_rejects_duplicate_names(self):
        self.assertTrue(HELPERS.is_file(), "Missing tested layout identity helper")
        helpers = str(HELPERS).replace("'", "''")
        self.run_ps(f"""
        . '{helpers}'
        $registry=@{{}}
        $one=[pscustomobject]@{{Design=[pscustomobject]@{{Index=1}};CustomLayout=[pscustomobject]@{{Index=1;Name='A';MatchingName='M1'}};SlideIndex=1}}
        $two=[pscustomobject]@{{Design=[pscustomobject]@{{Index=2}};CustomLayout=[pscustomobject]@{{Index=1;Name='B';MatchingName='M2'}};SlideIndex=2}}
        Register-PccsLayout $registry $one
        Register-PccsLayout $registry $two
        Register-PccsLayout $registry $one
        if ($registry.Count -ne 2) {{ throw 'Distinct masters were collapsed or repeated layout counted twice.' }}
        $three=[pscustomobject]@{{Design=[pscustomobject]@{{Index=3}};CustomLayout=[pscustomobject]@{{Index=1;Name='A';MatchingName='M1'}};SlideIndex=3}}
        $caught=$false
        try {{ Register-PccsLayout $registry $three }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw 'Duplicate layout identities were accepted.' }}
        """)

    def test_qa_output_paths_cannot_replace_source_or_existing_files(self):
        self.assertTrue(HELPERS.is_file(), "Missing tested output path guard")
        helpers = str(HELPERS).replace("'", "''")
        self.run_ps(f"""
        . '{helpers}'
        $source=[IO.Path]::GetFullPath('{str(SCRIPT).replace("'", "''")}')
        $caught=$false
        try {{ Assert-PccsNewOutputPath $source $source }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw 'Source replacement was allowed.' }}
        $caught=$false
        try {{ Assert-PccsNewOutputPath $source '{helpers}' }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw 'Existing file replacement was allowed.' }}
        """)

    def test_visible_edit_replaces_one_visible_character_and_keeps_its_font(self):
        self.assertTrue(HELPERS.is_file())
        helpers = str(HELPERS).replace("'", "''")
        self.run_ps(f"""
        . '{helpers}'
        $font=[pscustomobject]@{{Name='SimSun';Size=36}}
        $range=[pscustomobject]@{{Length=2;Items=@([pscustomobject]@{{Text=' ';Font=$font}},[pscustomobject]@{{Text='A';Font=$font}})}}
        $range | Add-Member ScriptMethod Characters {{param($offset,$count) $this.Items[$offset-1]}}
        $shape=[pscustomobject]@{{Visible=-1;HasTextFrame=-1;TextFrame=[pscustomobject]@{{HasText=-1}};TextFrame2=[pscustomobject]@{{TextRange=$range}}}}
        $slide=[pscustomobject]@{{Shapes=@($shape);CustomLayout=[pscustomobject]@{{Name='Reading'}}}}
        Set-PccsVisibleQaEdit $slide
        if ($range.Items[0].Text -cne ' ' -or $range.Items[1].Text -cne 'Q') {{ throw 'Expected visible character replacement, not whitespace append.' }}
        if ($range.Items[1].Font.Name -ne 'SimSun' -or $range.Items[1].Font.Size -ne 36) {{ throw 'Edit changed the existing font.' }}
        """)

    def test_reopen_snapshot_detects_background_geometry_drift(self):
        self.assertTrue(HELPERS.is_file())
        helpers = str(HELPERS).replace("'", "''")
        self.run_ps(f"""
        . '{helpers}'
        $background=[pscustomobject]@{{Name='Scene background';Type=13;Left=0;Top=0;Width=720;Height=345;ZOrderPosition=1}}
        $layout=[pscustomobject]@{{Name='Reading';MatchingName='Reading';Shapes=@($background)}}
        $slide=[pscustomobject]@{{Shapes=@();CustomLayout=$layout}}
        $before=Get-PccsSlideTextState $slide
        $background.Top=-60
        $after=Get-PccsSlideTextState $slide
        if ($before -ceq $after) {{ throw 'Moved layout background was absent from reopen snapshot.' }}
        """)

    def test_mixed_deck_map_checks_only_declared_service_pages(self):
        self.assertTrue(HELPERS.is_file())
        helpers = str(HELPERS).replace("'", "''")
        self.run_ps(f"""
        . '{helpers}'
        $plan=[pscustomobject]@{{slides=@(
          [pscustomobject]@{{index=1;final_slide_index=7;type='scripture'}},
          [pscustomobject]@{{index=2;final_slide_index=32;type='announcement'}}
        )}}
        if (-not (Get-Command Get-PccsServiceSlideMap -ErrorAction SilentlyContinue)) {{ throw 'Mixed-deck service map is missing.' }}
        $map=Get-PccsServiceSlideMap $plan 58
        if ($map.Count -ne 2 -or $map[7].type -ne 'scripture' -or $map[32].type -ne 'announcement' -or $map.ContainsKey(1)) {{ throw 'Service-only mapping requires fake lyric records or maps the wrong pages.' }}
        $consumed=New-Object 'System.Collections.Generic.HashSet[int]'
        [void]$consumed.Add(7); $caught=$false
        try {{ Assert-PccsConsumedServiceSlides $map $consumed }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw 'An unconsumed declared service page passed.' }}
        [void]$consumed.Add(32)
        Assert-PccsConsumedServiceSlides $map $consumed
        $plan.slides[1].final_slide_index=7; $caught=$false
        try {{ Get-PccsServiceSlideMap $plan 58 }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw 'Duplicate final slide mapping passed.' }}
        $plan.slides[1].final_slide_index=59; $caught=$false
        try {{ Get-PccsServiceSlideMap $plan 58 }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw 'Out-of-deck service mapping passed.' }}
        """)

    def test_final_scripture_checker_rejects_text_size_and_alignment_drift(self):
        self.assertTrue(HELPERS.is_file())
        helpers = str(HELPERS).replace("'", "''")
        self.run_ps(f"""
        . '{helpers}'
        $font=[pscustomobject]@{{Name='SimSun';NameFarEast='SimSun';Size=36;Shadow=[pscustomobject]@{{Visible=0}}}}
        $char=[pscustomobject]@{{Text='A';Font=$font;ParagraphFormat=[pscustomobject]@{{Alignment=1}}}}
        $range=[pscustomobject]@{{Text='A';Length=1;Item=$char}}
        $range | Add-Member ScriptMethod Characters {{param($offset,$count) $this.Item}}
        $body=[pscustomobject]@{{Name='PCCS scripture body';TextFrame2=[pscustomobject]@{{TextRange=$range;AutoSize=0;WordWrap=0}}}}
        $slide=[pscustomobject]@{{Shapes=@($body);SlideIndex=1}}
        $plan=[pscustomobject]@{{source_lines=@('A');body_font='SimSun';body_font_pt=36;alignment='left';body_shadow=$false}}
        Assert-PccsScriptureBody $slide $plan
        $body.Name='Scripture body'
        Assert-PccsScriptureBody $slide $plan
        $range.Text='B'; $caught=$false
        try {{ Assert-PccsScriptureBody $slide $plan }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw 'Changed scripture text passed.' }}
        $range.Text='A'; $font.Size=48; $caught=$false
        try {{ Assert-PccsScriptureBody $slide $plan }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw '48pt scripture passed.' }}
        $font.Size=36; $char.ParagraphFormat.Alignment=2; $caught=$false
        try {{ Assert-PccsScriptureBody $slide $plan }} catch {{ $caught=$true }}
        if (-not $caught) {{ throw 'Centered scripture passed.' }}
        """)


if __name__ == "__main__":
    unittest.main()
