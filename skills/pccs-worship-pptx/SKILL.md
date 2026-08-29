---
name: pccs-worship-pptx
description: Use when creating or revising PCCS worship PPTX decks from a template, service song list, V/C/B/End arrangements, optional lyric images, and YouTube video, playlist, or channel sources, including lyric audit and editable slide verification.
---

# PCCS Worship PPTX

## Overview

Build an audited, editable PCCS worship deck from the selected template and performance order. Prefer a user-supplied template; otherwise use the bundled PCCS template. Support both projects with lyric images and projects that must resolve lyrics from YouTube; never treat unverified OCR, ASR, or search results as final lyrics.

## Required References

Read these before doing project work:

1. `references/input-contract.md` for normalized inputs.
2. `references/source-resolution.md` for matching the correct recording and handling lyric images.
3. `references/lyrics-pipeline.md` for audit, section expansion, simplified Chinese, and divine pronouns.
4. `references/ppt-template-rules.md` before editing a PPTX.
5. `references/visual-style.md` for content-adapted backgrounds, PCCS logo protection, refined typography, and placeholder cleanup.
6. `references/qa-checklist.md` before delivery.

Use the **Presentations** skill for every PPTX inspection, edit, render, and verification task.

## Workflow

1. Select the template: use a non-empty user-supplied `template_pptx`; otherwise resolve `assets/pccsworship.pptx` relative to this skill directory. Normalize the user's chat input and run `scripts/validate_project.py PROJECT.json`. When a TXT guide explicitly includes scripture, capture its physical lines as canonical `source_lines`; keep their order and boundaries unchanged.
2. Resolve one concrete reference recording per song. When 歌词图片 exist, use direct visual recognition as the baseline and YouTube as verification. Without images, match the correct YouTube video from direct links, playlists, channels, or search hints before extracting lyrics.
3. Build section definitions, interpret repeat signs and alternate endings, then fully expand the user's arrangement. Keep `End*2` as `End End` in the complete lyrics, but place consecutive one-line End repetitions together on one slide when they fit the three-line limit. Record grouped occurrences with `performance_indexes`. Performance notes such as `C2跳音` change delivery, not visible lyrics, unless the recording proves a textual difference.
4. Create `lyrics_audit.md` first. Record every discrepancy, source, decision, confidence level, and unresolved item.
5. Create `complete_lyrics.md` only from accepted audit decisions. Convert Chinese to simplified Chinese and use `祢`/`祂` for references to God.
6. Plan slide data and run `scripts/validate_slide_data.py SLIDES.json` before generating slides. For scripture, the validator must reconstruct the canonical `source_lines` exactly from the ordered pages.
7. Copy the selected template to a project working file and generate the deck from that copy; never edit the bundled asset in place. Keep all editable Chinese text in `KaiTi`, set both `Name` and `NameFarEast`, use centered `54pt` first-song titles and fixed `48pt` lyric text. When a score or lyric image exposes musical phrasing, plan pages from complete musical phrases, breath points, rests, and cadences; prefer two lyric lines when that improves singability, and use three only when every line remains at the fixed lyric size. Scripture defaults to `48pt`; when the user explicitly requires one slide or an intact source line cannot fit, choose the largest fitting scripture size without changing source line boundaries. When refined or content-adapted styling is requested or already present, apply `references/visual-style.md`: use native `1920x920` (`48:23`) artwork in the `720x345pt` content area, one coherent background family with a song-specific layout for each scene, unique layout `Name` and `MatchingName`, exact PCCS logo-tip protection, refined text colors/shadows, upper-biased sanctuary-safe placement, top-aligned two-line first pages, and removal of empty title/subtitle placeholders.
8. After generation, run `scripts/validate_final_pptx.mjs FINAL.pptx SLIDES.json` with the Presentations runtime. This validates the actual editable lyric runs, rendered line counts, `KaiTi`, fixed `48pt`, and disabled shrinking; declared slide data is not final-output evidence. Then render every slide and perform the Microsoft PowerPoint 复制/edit/save/reopen test, including every distinct background layout. Deliver only after all applicable checks pass. If the user explicitly declines visual testing for a revision, record that exception instead of claiming it passed.

## Hard Gates

- The user-supplied arrangement is authoritative. If absent, follow the verified reference performance and document that choice.
- A user-supplied template overrides the bundled default. When no template is specified, use `<skill-dir>/assets/pccsworship.pptx`; do not search the project root for an implicit substitute.
- Stop for confirmation when several plausible recordings remain and matching confidence is low.
- Do not create the PPTX before `lyrics_audit.md` and `complete_lyrics.md` are complete.
- Do not use repeated-section shorthand in final lyrics or slide data.
- Do not turn `End*2` into two one-line slides when both identical ending lines fit one page. The complete arrangement remains expanded as `End End`; only the slide plan groups them with `performance_indexes`.
- Do not exceed three lyric lines, include lyric punctuation, use body text below `48pt`, or hide overflow with automatic shrinking.
- A declared `48pt` in slide data does not prove the final deck is `48pt`; reject any final lyric run that inherits another size, including `44pt`.
- When scripture is explicitly present in a TXT guide, do not merge, split, reorder, paraphrase, or silently re-punctuate its canonical `source_lines`. Pagination may occur only between source lines; `single_slide: true` forbids pagination.
- A direct user instruction and a newly supplied template override the bundled refined visual defaults. For a strictly template-faithful request, preserve the template colors; for refined or content-adapted styling, use `references/visual-style.md` consistently.
- Never allow a custom background to obscure the PCCS logo, its protruding cross tip, the church name, or other identity information.
- Do not vertically center a first-page body containing only two lyric lines; keep it top-aligned beneath the title and clear of front-row sightline risk.
- Final generated slides must not contain empty title or subtitle placeholders.

## Deliverables

Always provide `output.pptx`, `complete_lyrics.md`, and `lyrics_audit.md`. Include a source/ASR summary when used and report any QA exception instead of silently delivering a compromised deck.
