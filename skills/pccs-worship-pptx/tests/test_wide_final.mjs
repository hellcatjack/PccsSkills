import assert from 'node:assert/strict';
import test from 'node:test';
import { validateLyricPage } from '../scripts/validate_final_pptx.mjs';
const page = {lines:['祢的创造奇妙','祢的能力无限'],body_font_pt:52};
const policy = {template_profile:'wide-v3',lyric_font_pt:52,lyric_font:'KaiTi'};
function layout(size) {return {unit:'pt',elements:[{text:page.lines.join('\n'),resolvedTextStyle:{autoFit:'none'},textLayout:{lineCount:2},paragraphs:page.lines.map(text=>({text,runs:[{text,fontSize:size,typeface:'KaiTi'}]}))}]};}
test('wide profile verifies actual 52pt runs',()=>assert.doesNotThrow(()=>validateLyricPage(layout(52),page,1,policy)));
test('wide profile rejects actual inherited 48pt despite declared 52pt',()=>assert.throws(()=>validateLyricPage(layout(48),page,1,policy),/52pt.*48pt/));
