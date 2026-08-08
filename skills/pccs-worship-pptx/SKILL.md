---
name: pccs-worship-pptx
description: Use when creating or revising PCCS worship PPTX decks from a template, service song list, V/C/B/End arrangements, optional lyric images, and YouTube video, playlist, or channel sources, including lyric audit and editable slide verification.
---

# PCCS Worship PPTX

## Overview

Build an audited, editable PCCS worship deck from the supplied template and performance order. Support both projects with lyric images and projects that must resolve lyrics from YouTube; never treat unverified OCR, ASR, or search results as final lyrics.

## Required References

Read these before doing project work:

1. `references/input-contract.md` for normalized inputs.
2. `references/source-resolution.md` for matching the correct recording and handling lyric images.
3. `references/lyrics-pipeline.md` for audit, section expansion, simplified Chinese, and divine pronouns.
4. `references/ppt-template-rules.md` before editing a PPTX.
5. `references/qa-checklist.md` before delivery.

Use the **Presentations** skill for every PPTX inspection, edit, render, and verification task.

## Workflow

1. Normalize the user's chat input and run `scripts/validate_project.py PROJECT.json`.
2. Resolve one concrete reference recording per song. When 歌词图片 exist, use direct visual recognition as the baseline and YouTube as verification. Without images, match the correct YouTube video from direct links, playlists, channels, or search hints before extracting lyrics.
3. Build section definitions, interpret repeat signs and alternate endings, then fully expand the user's arrangement. Performance notes such as `C2跳音` change delivery, not visible lyrics, unless the recording proves a textual difference.
4. Create `lyrics_audit.md` first. Record every discrepancy, source, decision, confidence level, and unresolved item.
5. Create `complete_lyrics.md` only from accepted audit decisions. Convert Chinese to simplified Chinese and use `祢`/`祂` for references to God.
6. Plan slide data and run `scripts/validate_slide_data.py SLIDES.json` before generating slides.
7. Generate the deck from the uploaded template. Keep all editable Chinese text in `KaiTi`, set both `Name` and `NameFarEast`, use centered `54pt` first-song titles and fixed `48pt` lyric/scripture text, and split content instead of shrinking it.
8. Render every slide and perform the Microsoft PowerPoint 复制/edit/save/reopen test. Deliver only after all checks pass.

## Hard Gates

- The user-supplied arrangement is authoritative. If absent, follow the verified reference performance and document that choice.
- Stop for confirmation when several plausible recordings remain and matching confidence is low.
- Do not create the PPTX before `lyrics_audit.md` and `complete_lyrics.md` are complete.
- Do not use repeated-section shorthand in final lyrics or slide data.
- Do not exceed three lyric lines, include lyric punctuation, use body text below `48pt`, or hide overflow with automatic shrinking.
- Preserve the template background, PCCS logo, church identity, title color, and continuation-page song-name color.

## Deliverables

Always provide `output.pptx`, `complete_lyrics.md`, and `lyrics_audit.md`. Include a source/ASR summary when used and report any QA exception instead of silently delivering a compromised deck.
