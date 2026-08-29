import assert from "node:assert/strict";
import test from "node:test";

import { validateLyricPage } from "../scripts/validate_final_pptx.mjs";


function layoutFor({
  lines = ["主 我们同心在祢面前", "以祷告寻求祢面"],
  renderedLineCount = lines.length,
  fontSize = 64,
  typeface = "KaiTi",
  autoFit = "none",
} = {}) {
  return {
    elements: [
      {
        kind: "shape",
        name: "lyric body",
        text: lines.join("\n"),
        resolvedTextStyle: { autoFit },
        textLayout: { lineCount: renderedLineCount },
        paragraphs: lines.map((line) => ({
          text: line,
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
    body_font_pt: 48,
  };
}


test("accepts lyric runs that render as KaiTi 48pt without wrapping", () => {
  assert.doesNotThrow(() => validateLyricPage(layoutFor(), pageFor(), 12));
});


test("rejects an inherited 44pt lyric body even when slide data says 48pt", () => {
  assert.throws(
    () => validateLyricPage(layoutFor({ fontSize: 58.67 }), pageFor(), 12),
    /48pt.*44pt/i,
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
