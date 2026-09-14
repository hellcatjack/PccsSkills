#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";


const PX_PER_PT = 4 / 3;

function resolveTypography(value = {}) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("typography must be an object");
  const result = { lyric_font_pt: 40, title_font_pt: 44, ...value };
  for (const key of ["lyric_font_pt", "title_font_pt"]) {
    if (!Number.isFinite(result[key]) || result[key] <= 0) throw new Error(`typography.${key} must be finite and positive`);
  }
  if ((result.lyric_font_pt !== 40 || result.title_font_pt !== 44) &&
      !String(result.override_reason ?? "").trim()) {
    throw new Error("typography.override_reason must record the explicit user size override");
  }
  return result;
}


function normalizeText(value) {
  return String(value ?? "")
    .replace(/\r\n?/g, "\n")
    .replace(/[ \t]+$/gm, "")
    .trim();
}


function elementText(element) {
  if (typeof element?.text === "string") {
    return normalizeText(element.text);
  }
  if (Array.isArray(element?.paragraphs)) {
    return normalizeText(element.paragraphs.map((paragraph) => paragraph.text ?? "").join("\n"));
  }
  return "";
}


function formatPt(value) {
  const rounded = Math.round(value);
  return Math.abs(value - rounded) <= 0.01
    ? `${rounded}pt`
    : `${value.toFixed(2)}pt`;
}


function actualRunPt(fontSize, unit) {
  if (!Number.isFinite(fontSize)) {
    return Number.NaN;
  }
  return unit === "pt" ? fontSize : fontSize / PX_PER_PT;
}

function boxPt(element, layout, label) {
  const box = element?.bbox;
  if (!Array.isArray(box) || box.length !== 4 || !box.every(Number.isFinite)) {
    throw new Error(`${label}: missing inspectable geometry`);
  }
  return box.map(value => actualRunPt(value, layout?.unit ?? "px"));
}

function checkTextStyle(element, layout, fontPt, typeface, alignment, label) {
  if (element?.resolvedTextStyle?.autoFit === "shrinkText") {
    throw new Error(`${label}: automatic shrinking is active`);
  }
  const paragraphs = (element.paragraphs ?? []).filter(p => String(p.text ?? "").trim());
  const runs = paragraphs.flatMap(p => p.runs ?? []).filter(r => String(r.text ?? "").trim());
  if (!runs.length) throw new Error(`${label}: missing inspectable editable runs`);
  for (const run of runs) {
    const pt = actualRunPt(run.fontSize, layout?.unit ?? "px");
    if (!Number.isFinite(pt) || Math.abs(pt - fontPt) > 0.05 ||
        String(run.typeface ?? "").toLowerCase() !== typeface.toLowerCase()) {
      throw new Error(`${label}: expected ${typeface} ${fontPt}pt in every actual run`);
    }
  }
  for (const paragraph of paragraphs) {
    // Paragraph style overrides the containing shape's inherited alignment.
    const actual = paragraph.resolvedTextStyle?.alignment ?? element.resolvedTextStyle?.alignment;
    if (actual !== alignment) throw new Error(`${label}: expected ${alignment} alignment`);
  }
}

function exactElementText(element) {
  return String(element?.text ?? (element?.paragraphs ?? []).map(p => p.text ?? "").join("\n"))
    .replace(/\r\n?/g, "\n");
}

function checkSongFurniture(layout, page, slideNumber, typography) {
  const elements = layout.elements ?? [];
  if (page.credit_lines !== undefined && (!Array.isArray(page.credit_lines) || !page.credit_lines.length ||
      page.credit_lines.some(line => typeof line !== "string" || !line.trim()))) {
    throw new Error(`Slide ${slideNumber}: credit_lines must contain non-empty attribution text`);
  }
  if (page.role === "song_first" && page.title) {
    const title = elements.find(e => elementText(e) === page.title);
    if (!title) throw new Error(`Slide ${slideNumber}: missing editable song title`);
    checkTextStyle(title, layout, typography.title_font_pt, "KaiTi", "center", `Slide ${slideNumber} title`);
  }
  const expectedCredit = Array.isArray(page.credit_lines) ? page.credit_lines.join("\n") : "";
  const credits = elements.filter(e => elementText(e) && (/copyright|credits|版权|署名/i.test(e.name ?? "") ||
    /©|词曲[：:]|作词[：:]|作曲[：:]/.test(elementText(e)) ||
    (expectedCredit && exactElementText(e) === expectedCredit)));
  if (expectedCredit && !credits.some(e => exactElementText(e) === expectedCredit)) {
    throw new Error(`Slide ${slideNumber}: declared credit text is missing or changed`);
  }
  for (const credit of credits) {
    const [x, y, w, h] = boxPt(credit, layout, `Slide ${slideNumber} copyright`);
    if (x < 330 || y < 345 - 0.05 || x + w > 720.05 || y + h > 405.05) {
      throw new Error(`Slide ${slideNumber}: copyright must fit the purple footer clear of church identity`);
    }
    checkTextStyle(credit, layout, 9, "KaiTi", "right", `Slide ${slideNumber} copyright`);
  }
  const footer = elements.find(e => /song footer/i.test(e.name ?? "") ||
    (page.role === "song_continuation" && page.title && elementText(e) === page.title));
  if (page.role === "song_continuation" && page.title && (!footer || elementText(footer) !== page.title)) {
    throw new Error(`Slide ${slideNumber}: missing or changed song footer`);
  }
  if (footer) {
    checkTextStyle(footer, layout, 22, "KaiTi", "right", `Slide ${slideNumber} song footer`);
    const [, y, , h] = boxPt(footer, layout, `Slide ${slideNumber} song footer`);
    if (y < 345 - 0.05 || y + h > 405.05 || credits.some(c => y + h > boxPt(c, layout, "copyright")[1] + 0.05)) {
      throw new Error(`Slide ${slideNumber}: song footer overlaps copyright or leaves the footer`);
    }
  }
}


export function validateLyricPage(layout, page, slideNumber, profile = {}) {
  const typography = resolveTypography(profile);
  const requiredLyricPt = typography.lyric_font_pt;
  const expectedLines = Array.isArray(page?.lines) ? page.lines.map(String) : [];
  if (!expectedLines.length) {
    throw new Error(`Slide ${slideNumber}: lyric page has no planned lines`);
  }
  if (page.body_font_pt !== requiredLyricPt) {
    throw new Error(
      `Slide ${slideNumber}: slide data must declare lyric body as ${requiredLyricPt}pt`,
    );
  }

  const expectedText = normalizeText(expectedLines.join("\n"));
  const elements = Array.isArray(layout?.elements) ? layout.elements : [];
  const body = elements.find((element) => elementText(element) === expectedText);
  if (!body) {
    throw new Error(`Slide ${slideNumber}: cannot find editable lyric body matching slide data`);
  }

  const renderedLineCount = body?.textLayout?.lineCount;
  if (renderedLineCount !== expectedLines.length) {
    throw new Error(
      `Slide ${slideNumber}: planned ${expectedLines.length} lyric lines but rendered ${renderedLineCount}`,
    );
  }

  if (body?.resolvedTextStyle?.autoFit === "shrinkText") {
    throw new Error(`Slide ${slideNumber}: lyric body uses automatic shrinking`);
  }

  const runs = (body.paragraphs ?? [])
    .flatMap((paragraph) => paragraph.runs ?? [])
    .filter((run) => normalizeText(run.text));
  if (!runs.length) {
    throw new Error(`Slide ${slideNumber}: lyric body has no inspectable text runs`);
  }

  for (const run of runs) {
    const runPt = actualRunPt(run.fontSize, layout?.unit ?? "px");
    if (!Number.isFinite(runPt) || Math.abs(runPt - requiredLyricPt) > 0.05) {
      const actual = Number.isFinite(runPt) ? formatPt(runPt) : "an unknown size";
      throw new Error(
        `Slide ${slideNumber}: lyric run requires ${requiredLyricPt}pt but actual run is ${actual}`,
      );
    }
    if (String(run.typeface ?? "").toLowerCase() !== "kaiti") {
      throw new Error(
        `Slide ${slideNumber}: lyric run requires KaiTi but actual typeface is ${run.typeface ?? "unknown"}`,
      );
    }
  }

  checkTextStyle(body, layout, requiredLyricPt, "KaiTi", "center", `Slide ${slideNumber} lyrics`);
  const [, top, , height] = boxPt(body, layout, `Slide ${slideNumber} lyrics`);
  if (top < 0 || top + height > 202.55) {
    throw new Error(`Slide ${slideNumber}: lyric box must fit in the upper half`);
  }
  checkSongFurniture(layout, page, slideNumber, typography);

  return {
    slide: slideNumber,
    lineCount: expectedLines.length,
    lyricRunCount: runs.length,
    fontPt: requiredLyricPt,
    typeface: "KaiTi",
  };
}

export function validateScripturePage(layout, page, slideNumber) {
  const override = typeof page.style_override_reason === "string" && page.style_override_reason.trim();
  const typeface = override ? (page.font ?? page.body_font ?? "SimSun") : "SimSun";
  const alignment = override ? (page.alignment ?? "left") : "left";
  const expected = (page.lines ?? []).join("\n");
  const body = (layout.elements ?? []).find(e => exactElementText(e) === expected);
  if (!expected || !body) throw new Error(`Slide ${slideNumber}: cannot find editable scripture matching exact source lines`);
  if (!Number.isFinite(page.body_font_pt) || page.body_font_pt <= 0 || (page.body_font_pt > 36 && !override)) {
    throw new Error(`Slide ${slideNumber}: scripture must declare a positive size at most 36pt`);
  }
  checkTextStyle(body, layout, page.body_font_pt, typeface, alignment, `Slide ${slideNumber} scripture (default maximum 36pt)`);
  const visualWrap = page.source_lines_fixed === false && page.allow_visual_wrap === true;
  if (!visualWrap && body.textLayout?.lineCount !== page.lines.length) {
    throw new Error(`Slide ${slideNumber}: scripture rendered lines do not match fixed source lines`);
  }
  const [x, y, w, h] = boxPt(body, layout, `Slide ${slideNumber} scripture`);
  if (x < 0 || y < 0 || x + w > 720.05 || y + h > 316.4) {
    throw new Error(`Slide ${slideNumber}: scripture must fit the reading area above the logo tip and footer`);
  }
  if (Array.isArray(page.verse_numbers)) {
    const expectedNumbers = page.verse_numbers.filter(Boolean);
    const markers = (layout.elements ?? []).filter(e => /verse (number|marker)/i.test(e.name ?? "") && elementText(e));
    if (JSON.stringify(markers.map(elementText)) !== JSON.stringify(expectedNumbers)) {
      throw new Error(`Slide ${slideNumber}: missing or changed editable verse marker`);
    }
    for (const marker of markers) {
      checkTextStyle(marker, layout, 17, "Microsoft YaHei", "left", `Slide ${slideNumber} verse marker`);
      const [mx, my, mw, mh] = boxPt(marker, layout, "verse marker");
      if (mx < 0 || mx + mw > x || my < 0 || my + mh > 316.4) throw new Error(`Slide ${slideNumber}: verse marker must fit the left gutter`);
    }
  }
  const title = (layout.elements ?? []).find(e => /scripture (title|heading)/i.test(e.name ?? ""));
  if (title) checkTextStyle(title, layout, 28, "Microsoft YaHei", "left", `Slide ${slideNumber} scripture heading`);
  return { slide: slideNumber, lineCount: page.lines.length, fontPt: page.body_font_pt, typeface };
}


function loadArtifactTool() {
  const runtimeModules = process.env.RUNTIME_NODE_MODULES || process.env.NODE_PATH;
  if (!runtimeModules) {
    throw new Error(
      "RUNTIME_NODE_MODULES (or NODE_PATH) is required; load the Presentations workspace dependencies first",
    );
  }
  const runtimeRequire = createRequire(path.join(runtimeModules, "__pccs_worship_validator__.cjs"));
  return runtimeRequire("@oai/artifact-tool");
}


export async function validateFinalPptx(pptxPath, slideDataPath) {
  const { FileBlob, PresentationFile } = loadArtifactTool();
  const slideData = JSON.parse(fs.readFileSync(slideDataPath, "utf8"));
  const typography = resolveTypography(slideData.typography);
  const pages = Array.isArray(slideData?.pages) ? slideData.pages : [];
  if (!pages.length) {
    throw new Error("Slide data must contain a non-empty pages array");
  }

  const presentation = await PresentationFile.importPptx(await FileBlob.load(pptxPath));
  const slides = presentation.slides.items;
  if (slides.length !== pages.length) {
    throw new Error(
      `Final PPTX has ${slides.length} slides but slide data plans ${pages.length}`,
    );
  }

  const results = [];
  const scriptureResults = [];
  const scriptureSizes = new Map();
  for (let index = 0; index < pages.length; index += 1) {
    const page = pages[index];
    if (!["song_first", "song_continuation", "scripture"].includes(page.role)) {
      continue;
    }
    const exported = await slides[index].export({ format: "layout" });
    const layout = JSON.parse(await exported.text());
    if (page.role === "scripture") {
      const previous = scriptureSizes.get(page.scripture_id);
      const style = JSON.stringify([page.body_font_pt, page.font ?? page.body_font ?? "SimSun", page.alignment ?? "left", page.body_shadow ?? false]);
      if (previous !== undefined && previous !== style) {
        throw new Error(`Scripture ${page.scripture_id}: use uniform typography across pages`);
      }
      scriptureSizes.set(page.scripture_id, style);
      scriptureResults.push(validateScripturePage(layout, page, index + 1));
    } else {
      const song = (slideData.songs ?? []).find(s => s.id === page.song_id);
      results.push(validateLyricPage(layout, { ...page, credit_lines: page.credit_lines ?? song?.credit_lines }, index + 1, typography));
    }
  }

  return {
    status: "pass",
    slideCount: slides.length,
    lyricPageCount: results.length,
    scripturePageCount: scriptureResults.length,
    lyricFontPt: typography.lyric_font_pt,
    lyricTypeface: "KaiTi",
    sha256: createHash("sha256").update(fs.readFileSync(pptxPath)).digest("hex"),
  };
}


async function main() {
  const [pptxPath, slideDataPath] = process.argv.slice(2);
  if (!pptxPath || !slideDataPath) {
    console.error("Usage: validate_final_pptx.mjs FINAL.pptx SLIDE_DATA.json");
    process.exitCode = 2;
    return;
  }
  const result = await validateFinalPptx(pptxPath, slideDataPath);
  console.log(JSON.stringify(result, null, 2));
}


const isCli = process.argv[1]
  && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  main().catch((error) => {
    console.error(error?.stack ?? String(error));
    process.exitCode = 1;
  });
}
