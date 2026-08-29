#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";


const PX_PER_PT = 4 / 3;
const REQUIRED_LYRIC_PT = 48;


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


export function validateLyricPage(layout, page, slideNumber) {
  const expectedLines = Array.isArray(page?.lines) ? page.lines.map(String) : [];
  if (!expectedLines.length) {
    throw new Error(`Slide ${slideNumber}: lyric page has no planned lines`);
  }
  if (page.body_font_pt !== REQUIRED_LYRIC_PT) {
    throw new Error(
      `Slide ${slideNumber}: slide data must declare lyric body as ${REQUIRED_LYRIC_PT}pt`,
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
    if (!Number.isFinite(runPt) || Math.abs(runPt - REQUIRED_LYRIC_PT) > 0.05) {
      const actual = Number.isFinite(runPt) ? formatPt(runPt) : "an unknown size";
      throw new Error(
        `Slide ${slideNumber}: lyric run requires ${REQUIRED_LYRIC_PT}pt but actual run is ${actual}`,
      );
    }
    if (String(run.typeface ?? "").toLowerCase() !== "kaiti") {
      throw new Error(
        `Slide ${slideNumber}: lyric run requires KaiTi but actual typeface is ${run.typeface ?? "unknown"}`,
      );
    }
  }

  return {
    slide: slideNumber,
    lineCount: expectedLines.length,
    lyricRunCount: runs.length,
    fontPt: REQUIRED_LYRIC_PT,
    typeface: "KaiTi",
  };
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
  for (let index = 0; index < pages.length; index += 1) {
    const page = pages[index];
    if (page.role !== "song_first" && page.role !== "song_continuation") {
      continue;
    }
    const exported = await slides[index].export({ format: "layout" });
    const layout = JSON.parse(await exported.text());
    results.push(validateLyricPage(layout, page, index + 1));
  }

  return {
    status: "pass",
    slideCount: slides.length,
    lyricPageCount: results.length,
    lyricFontPt: REQUIRED_LYRIC_PT,
    lyricTypeface: "KaiTi",
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
