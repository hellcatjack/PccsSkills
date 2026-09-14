---
name: pccs-worship-pptx
description: Use when creating or revising PCCS worship PPTX decks from a template, service song list, V/C/B/End arrangements, lyric images, or YouTube sources, including lyric audit and editable slide verification.
---

# PCCS Worship PPTX

Build an audited, editable worship deck in the user's performance order. Use a supplied template, otherwise [assets/pccsworship.pptx](assets/pccsworship.pptx), and edit a project copy. Current instructions and already accepted revisions take priority over defaults.

Use **Presentations** for PPTX inspection, authoring, rendering, and verification. Use `pccs-service-pptx` for non-song pages in a mixed deck. Scripture uses its formal reading layout; the song typography rules below apply only to lyrics.

## Workflow and References

1. Normalize chat, 歌词图片, links, and any TXT guide using [input-contract.md](references/input-contract.md). Run `scripts/validate_project.py PROJECT.json`.
2. Match each song to a concrete recording or accepted source using [source-resolution.md](references/source-resolution.md). Actively locate official lyric materials and retain author/copyright details separately from lyrics. Record what was actually accessed.
3. Follow [lyrics-pipeline.md](references/lyrics-pipeline.md): resolve section variants, audit wording, and fully expand the arrangement. Create `lyrics_audit.md`, then `complete_lyrics.md`, then slide data. The user's arrangement overrides the recording; clarify only a material ambiguity such as which verse an unnumbered `V` means. Reuse earlier answers.
4. Run `scripts/validate_slide_data.py SLIDES.json`. Keep musical phrases intact. Repeated one-line endings such as `End*2` remain fully expanded but may share one page using consecutive `performance_indexes`, with one visible line per occurrence.
5. Inspect the selected template, then author following [ppt-template-rules.md](references/ppt-template-rules.md) and [visual-style.md](references/visual-style.md). Preserve the native purple footer and exact PCCS identity, including the protruding logo tip. Each background layout needs a unique `Name` and `MatchingName`.
6. Follow [qa-checklist.md](references/qa-checklist.md). Run `scripts/validate_final_pptx.mjs FINAL.pptx SLIDES.json` against actual editable runs and geometry. Render every slide and perform the PowerPoint 复制/edit/save/close/reopen test for every distinct layout. Keep the user's other open presentations intact.

## Current Production Defaults

| Role | Typography and placement |
|---|---|
| Lyrics | Centered `KaiTi` **40pt**, fixed `50pt` line spacing; main block in the upper half |
| First-song title | Centered `KaiTi` **44pt** |
| Continuation song name | `KaiTi` **22pt**, right aligned in the purple footer |
| Author/copyright | Editable `KaiTi` **9pt**, right aligned in the bottom purple bar, clear of church identity |
| Formal scripture | Left aligned `SimSun` **36pt maximum**, uniform through a passage; heading `Microsoft YaHei` **28pt**, no lyric shadow |

The detailed coordinate grid is in `visual-style.md`. Set both `Name` and `NameFarEast`. Balance spacing, line length, and negative space before changing size; visual composition and congregational reading both matter.

## Content and Delivery Gates

- Keep lyrics to at most three lines, with no lyric punctuation or automatic shrinking. The default first-page grid holds two lines. Paginate by musical phrase when it does not fit.
- Keep **all copyright information in the purple bar**, never in the upper formal reading area.
- For scripture, preserve canonical `source_lines`, punctuation, intentional spaces, and order. Never apply lyric punctuation or pronoun rules to scripture. Separate verse-number metadata only with an auditable source mapping. Prefer pagination over smaller type; retain the **36pt ceiling and left alignment**.
- Official sources and permissions must be recorded; unverified OCR, ASR, or search snippets are not accepted final lyrics. Resolve uncertain text before producing the final deck.
- No flattened text, hidden overflow, obscured identity, or empty title/subtitle placeholders.
- Report any unavailable or expressly declined QA step accurately. A passing slide plan alone does not prove the final PPTX is correct.

Deliver the final PPTX, `complete_lyrics.md`, `lyrics_audit.md`, and a source summary when external sources were used. Preserve the source and link the verified final file.
