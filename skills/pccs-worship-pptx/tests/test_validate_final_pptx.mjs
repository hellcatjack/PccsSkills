import assert from "node:assert/strict";
import test from "node:test";

import * as validator from "../scripts/validate_final_pptx.mjs";
const { validateLyricPage } = validator;


function layoutFor({
  lines = ["主 我们同心在祢面前", "以祷告寻求祢面"],
  renderedLineCount = lines.length,
  fontSize = 40 * 4 / 3,
  typeface = "KaiTi",
  autoFit = "none",
} = {}) {
  return {
    elements: [
      {
        kind: "shape",
        name: "lyric body",
        bbox: [40 * 4 / 3, 42 * 4 / 3, 640 * 4 / 3, 104 * 4 / 3],
        text: lines.join("\n"),
        resolvedTextStyle: { autoFit },
        textLayout: { lineCount: renderedLineCount },
        paragraphs: lines.map((line) => ({
          text: line,
          resolvedTextStyle: { alignment: "center" },
          runs: [{ text: line, fontSize, typeface }],
        })),
      },
    ],
  };
}


function pageFor(lines = ["主 我们同心在祢面前", "以祷告寻求祢面"]) {
  return {
    role: "song_continuation",
    lines,
    body_font_pt: 40,
  };
}


test("accepts lyric runs that render as KaiTi 40pt without wrapping", () => {
  assert.doesNotThrow(() => validateLyricPage(layoutFor(), pageFor(), 12));
});


test("rejects an inherited 44pt lyric body even when slide data says 40pt", () => {
  assert.throws(
    () => validateLyricPage(layoutFor({ fontSize: 58.67 }), pageFor(), 12),
    /40pt.*44pt/i,
  );
});


test("rejects a two-line plan that renders as three wrapped lines", () => {
  assert.throws(
    () => validateLyricPage(layoutFor({ renderedLineCount: 3 }), pageFor(), 12),
    /planned 2.*rendered 3/i,
  );
});


test("rejects automatic shrinking on lyric text", () => {
  assert.throws(
    () => validateLyricPage(layoutFor({ autoFit: "shrinkText" }), pageFor(), 12),
    /automatic shrinking/i,
  );
});

function creditLayout(top = 377) {
  const layout = layoutFor();
  layout.elements.push({
    name: "Copyright", text: "© Example publisher",
    bbox: [460, top * 4 / 3, 466.67, 30.67],
    resolvedTextStyle: { autoFit: "none" },
    textLayout: { lineCount: 1 },
    paragraphs: [{ text: "© Example publisher", resolvedTextStyle: { alignment: "right" },
      runs: [{ text: "© Example publisher", fontSize: 12, typeface: "KaiTi" }] }],
  });
  return layout;
}

test("accepts editable credits inside purple footer", () => {
  assert.doesNotThrow(() => validateLyricPage(creditLayout(), pageFor(), 1));
});

test("rejects a copyright box placed above the purple footer", () => {
  assert.throws(() => validateLyricPage(creditLayout(300), pageFor(), 1), /copyright.*footer/i);
});

test("rejects omitted declared credits", () => {
  const page = { ...pageFor(), credit_lines: ["© Example publisher"] };
  assert.throws(() => validateLyricPage(layoutFor(), page, 1), /credit.*missing/i);
});

test("rejects empty declared credits instead of disabling attribution checks", () => {
  assert.throws(() => validateLyricPage(layoutFor(), { ...pageFor(), credit_lines: [] }, 1), /credit_lines/i);
});

test("rejects an old 54pt first-song title", () => {
  const layout = layoutFor();
  const title = structuredClone(layout.elements[0]);
  title.text = "Song";
  title.paragraphs = [{text: "Song", resolvedTextStyle: {alignment: "center"}, runs: [{text: "Song", fontSize: 72, typeface: "KaiTi"}]}];
  layout.elements.push(title);
  assert.throws(() => validateLyricPage(layout, { ...pageFor(), role: "song_first", title: "Song" }, 1), /title.*44pt/i);
});

test("rejects a lyric block placed below the upper half", () => {
  const layout = layoutFor();
  layout.elements[0].bbox[1] = 260;
  assert.throws(() => validateLyricPage(layout, pageFor(), 1), /upper half/i);
});

function scriptureLayout({ size = 48, alignment = "left" } = {}) {
  const layout = layoutFor({ lines: ["第一段。", "第二段。"], fontSize: size, typeface: "SimSun" });
  layout.elements[0].name = "Scripture body";
  layout.elements[0].paragraphs.forEach(p => p.resolvedTextStyle.alignment = alignment);
  return layout;
}
const scripturePage = { role: "scripture", lines: ["第一段。", "第二段。"], font: "SimSun", body_font_pt: 36, alignment: "left" };

test("accepts formal 36pt left aligned scripture", () => {
  assert.equal(typeof validator.validateScripturePage, "function");
  assert.doesNotThrow(() => validator.validateScripturePage(scriptureLayout(), scripturePage, 2));
});

test("rejects scripture over 36pt in actual runs", () => {
  assert.equal(typeof validator.validateScripturePage, "function");
  assert.throws(() => validator.validateScripturePage(scriptureLayout({ size: 64 }), scripturePage, 2), /36pt/i);
});

test("rejects actual centered scripture and altered fullwidth spaces", () => {
  assert.equal(typeof validator.validateScripturePage, "function");
  assert.throws(() => validator.validateScripturePage(scriptureLayout({ alignment: "center" }), scripturePage, 2), /left/i);
  const layout = scriptureLayout();
  layout.elements[0].text = "第一段。\n　第二段。";
  assert.throws(() => validator.validateScripturePage(layout, scripturePage, 2), /matching/i);
});

test("validates an explicit new lyric size against actual runs", () => {
  const profile = { lyric_font_pt: 42, title_font_pt: 44, override_reason: "User requested 42pt lyrics" };
  const page = { ...pageFor(), body_font_pt: 42 };
  assert.doesNotThrow(() => validateLyricPage(layoutFor({ fontSize: 56 }), page, 1, profile));
  assert.throws(() => validateLyricPage(layoutFor(), page, 1, profile), /42pt.*40pt/i);
});

test("rejects undeclared profile deviations", () => {
  assert.throws(() => validateLyricPage(layoutFor(), pageFor(), 1, { lyric_font_pt: 42 }), /override_reason/i);
});

test("requires a continuation song name when the plan declares the title", () => {
  assert.throws(() => validateLyricPage(layoutFor(), { ...pageFor(), title: "Song" }, 1), /song footer/i);
});

test("rejects scripture placed inside the purple footer", () => {
  const layout = scriptureLayout();
  layout.elements[0].bbox[1] = 460;
  assert.throws(() => validator.validateScripturePage(layout, scripturePage, 2), /reading area/i);
});

test("accepts visual wrap only for a declared continuous scripture paragraph", () => {
  const layout = scriptureLayout();
  layout.elements[0].textLayout.lineCount = 3;
  assert.doesNotThrow(() => validator.validateScripturePage(layout, { ...scripturePage, source_lines_fixed: false, allow_visual_wrap: true }, 2));
});

test("requires declared verse markers as editable gutter text", () => {
  assert.throws(() => validator.validateScripturePage(scriptureLayout(), { ...scripturePage, verse_numbers: ["1", ""] }, 2), /verse marker/i);
});

test("honors an explicit scripture font override shared with the service skill", () => {
  const layout = scriptureLayout();
  layout.elements[0].paragraphs.forEach(p => p.runs.forEach(r => r.typeface = "SimHei"));
  const page = { ...scripturePage, font: "SimHei", style_override_reason: "User explicitly requested SimHei scripture" };
  assert.doesNotThrow(() => validator.validateScripturePage(layout, page, 2));
});
