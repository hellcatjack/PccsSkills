---
name: pccs-service-pptx
description: Use when creating or revising PCCS non-lyric service PowerPoint decks such as covers, announcements, scripture, welcome, QR, prayer, baptism, communion, offering, and doxology slides; excludes worship-song lyric sequencing.
---

# PCCS Service PPTX

## Overview

Create or revise editable PCCS weekly-service slides that are not worship-song lyric pages, including封面、家讯、经文、欢迎页、二维码、祷告、洗礼、圣餐、奉献和三一颂。Preserve supplied wording and authentic church assets while using the current PCCS template, content-adapted backgrounds, and duplication-safe PowerPoint layouts.

Use `pccs-worship-pptx` for song lyrics, V/C/B/End arrangements, lyric images, or YouTube-based lyric resolution. For a mixed service deck, build lyric pages with that skill and non-lyric pages with this skill, then combine them without flattening either layout system.

## Required References

Read these before authoring:

1. [references/input-contract.md](references/input-contract.md) for normalized weekly inputs.
2. [references/content-rules.md](references/content-rules.md) for exact text, scripture, QR, form, and photo handling.
3. [references/visual-style.md](references/visual-style.md) for `48:23` backgrounds, PCCS identity protection, typography, and page-specific design.
4. [references/qa-checklist.md](references/qa-checklist.md) before delivery.

Use the **Presentations** skill for every PPTX inspection, edit, render, and verification task.

## Workflow

1. Select the template. A non-empty user-supplied PPTX wins; otherwise use [assets/pccsworship.pptx](assets/pccsworship.pptx). Copy it into the project before editing.
2. Normalize the request to the schema in `references/input-contract.md` and run `scripts/validate_project.py PROJECT.json`.
3. Preserve all supplied text. Treat scripture `source_lines` and explicitly fixed line breaks as canonical; do not paraphrase, modernize pronouns, repunctuate, merge, split, or reorder them.
4. Inspect every source/template slide, master, layout, placeholder, footer, PCCS logo, church name, and protruding cross tip before editing.
5. Choose one content-appropriate visual direction per page or reusable page group. Give the first slide the highest visual scrutiny, then carry its palette and alignment logic through the deck without repeating one dominant dark-purple block everywhere. Keep all pages in the same ivory, pearl white, pale lavender, muted gold, and limestone-gray family; use editable emphasis shapes for important cover, church-name, and vision text.
6. Generate each custom background natively at `1920x920` (`48:23`). Place it at exactly `0,0,720,345` points. Never use a 16:9 background shifted to `y=-60`, and never bake the purple footer into the image.
7. Keep the lyric/content region quiet and reserve the logo-safe area defined in `references/visual-style.md`. Restore the exact template pixels as a transparent `PCCS logo tip overlay` on the custom layout.
8. Give every distinct custom layout a unique `Name` and unique `MatchingName`. Put the background and logo-tip overlay on the layout; keep titles, body text, scripture, and captions as editable slide text.
9. Use authentic uploaded QR codes, forms, photos, and church assets. Do not regenerate, redraw, or approximate them.
10. Remove unused PowerPoint placeholders, including `Click to add title`, `Click to add subtitle`, empty footer/date fields, and unused page-number placeholders.
11. Render every slide at full size. Run `scripts/qa_pccs_service_pptx.ps1` when Microsoft PowerPoint is available, and perform the 复制/edit/save/reopen test for every distinct custom layout.

## Hard Gates

- This is a **非歌词** skill. Do not interpret arrangements or create worship lyric pages here.
- User wording is authoritative. Do not silently improve, shorten, translate, simplify, or correct it.
- Scripture characters and canonical line order must remain exact.
- The usable background area is `720x345pt`, not the full `720x405pt` slide.
- Background assets must be `1920x920` and natively composed for `48:23`.
- A generated background may not obscure the PCCS logo, cross tip, church name, QR code, form, or photos.
- Essential text must remain visible above front-row sightlines; do not place the only title, instruction, reference, or call to action near the footer when the content fits higher.
- Every distinct layout must have a unique `Name` and `MatchingName`.
- Do not deliver with empty title/subtitle placeholders or default prompts such as `Click to add title` and `Click to add subtitle`.
- Do not claim the PowerPoint duplication test passed unless the copied pages were edited, saved, closed, and reopened successfully.

## Deliverables

- Final editable PPTX.
- Short QA summary stating slide count, distinct layouts, rendered pages, placeholder result, and duplication-test result.
- Preserve the source as a backup when the user requests an in-place revision.
