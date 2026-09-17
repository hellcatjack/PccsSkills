import hashlib
import json
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SKILL = Path(__file__).resolve().parents[1]


class TemplateAssetsTests(unittest.TestCase):
    def test_wide_reference_and_extracted_layers_are_intact(self):
        folder = SKILL / 'assets/pccs-wide-v3'
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        reference = (folder / manifest['reference']).resolve()
        self.assertEqual(manifest['reference_sha256'], hashlib.sha256(reference.read_bytes()).hexdigest())
        ns = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
        with zipfile.ZipFile(reference) as package:
            self.assertIsNone(package.testzip())
            presentation = ET.fromstring(package.read('ppt/presentation.xml'))
            size = presentation.find('p:sldSz', ns)
            self.assertEqual((12192000,6858000), (int(size.attrib['cx']),int(size.attrib['cy'])))
            self.assertEqual(64, len(presentation.findall('p:sldIdLst/p:sldId',ns)))
            for layer in manifest['layers']:
                actual = (folder / layer['file']).read_bytes()
                self.assertEqual(package.read(layer['source_part']), actual)
                self.assertEqual(layer['sha256'], hashlib.sha256(actual).hexdigest())
        self.assertTrue((folder/'preview.png').is_file())
        self.assertTrue((SKILL/'references/background-prompts-v3.md').is_file())

    def test_foreground_template_is_blank_and_layers_remain_optional(self):
        folder = SKILL / 'assets/pccs-wide-v3'
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        record = manifest['foreground_template']
        file = folder / record['file']
        self.assertEqual(record['sha256'], hashlib.sha256(file.read_bytes()).hexdigest())
        ns = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
        with zipfile.ZipFile(file) as package:
            doc = ET.fromstring(package.read('ppt/presentation.xml'))
            self.assertEqual(1,len(doc.findall('p:sldIdLst/p:sldId',ns)))
            slide = ET.fromstring(package.read('ppt/slides/slide1.xml'))
            visible_text = [e.text for e in slide.findall('.//a:t',ns) if e.text]
            self.assertEqual(['匹兹堡南区基督教会','Pittsburgh Christian Church South'], visible_text)
            props = {p.attrib['name']:p for p in slide.findall('.//p:cNvPr',ns)}
            self.assertIn('PCCS_完整Logo_新模板原件', props)
            self.assertNotEqual('1',props['字幕云雾_新模板当前设置_可单独隐藏'].attrib.get('hidden'))
            self.assertEqual('1',props['可选_字幕薄雾_65%透明_默认隐藏'].attrib.get('hidden'))
            for part in package.namelist():
                if part.startswith('ppt/notesSlides/notesSlide') and part.endswith('.xml'):
                    notes=ET.fromstring(package.read(part))
                    self.assertFalse(any((t.text or '').strip() for t in notes.findall('.//a:t',ns)), 'Blank template must not retain historical speaker notes')
                if part.startswith('ppt/slideLayouts/slideLayout') and part.endswith('.xml'):
                    layout=ET.fromstring(package.read(part))
                    self.assertFalse(any(p.attrib.get('name','').startswith('背景_') for p in layout.findall('.//p:cNvPr',ns)))
