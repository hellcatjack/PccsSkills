---
name: pccs-worship-pptx
description: Use when creating or revising PCCS worship lyric PPTX decks, including song arrangements, lyric images, YouTube lyric sources, pale wide-screen backgrounds, layered subtitle templates, and background-only revisions.
---

# PCCS Worship PPTX

Build editable worship pages from the latest user template and accepted performance order. Use the **Presentations** skill for PPTX work. The default is [assets/pccs-wide-v3.pptx](assets/pccs-wide-v3.pptx), the current 960×540pt layered reference. Keep [assets/pccsworship.pptx](assets/pccsworship.pptx) for explicitly selected legacy work.

## Select the task mode

- **Background-only revision:** use the exact uploaded deck, inspect background relationships and protected layers, and read [references/layered-template-v3.md](references/layered-template-v3.md). Replace only background media. Preserve text, all typography, page count/order, footer, Logo and cloud visibility. Do not redo lyric research, arrange songs or paginate. Extract exact existing text for source comparison and reuse existing audits when available.
- **New lyrics or content changes:** read [references/input-contract.md](references/input-contract.md), [references/source-resolution.md](references/source-resolution.md), and [references/lyrics-pipeline.md](references/lyrics-pipeline.md). Resolve each recording; when 歌词图片 exist, use direct visual recognition as the baseline and recording as verification. If several recordings remain plausible, clarify the match. Complete `lyrics_audit.md` before `complete_lyrics.md`, then generate only from accepted text.

For either mode read [references/ppt-template-rules.md](references/ppt-template-rules.md), [references/visual-style.md](references/visual-style.md) and [references/qa-checklist.md](references/qa-checklist.md). A direct instruction or a newer uploaded template overrides the bundled design profile.

## New lyric/content authoring

1. For new lyrics or content changes, validate normalized inputs with `scripts/validate_project.py`. A blank template selects the new wide-v3 asset relative to this skill. Copy it before editing. It contains sample songs: reuse representative layouts and replace historical lyrics, names and copyright for the new service. Background-only work follows its separate mode above and does not invoke the song-source project validator.
2. Fully expand V/C/B/End arrangement. Keep `End*2` expanded as End End in complete lyrics; consecutive identical one-line endings may share one page with `performance_indexes`. Performance notes such as C2跳音 do not become lyrics.
3. Use simplified Chinese and祢/祂 for newly authored lyrics per the audit. For scripture from TXT or DOCX, preserve the accepted `source_lines` exactly; keep the raw wording separately when the user later authorizes punctuation or quotation changes. A background-only revision does not normalize authored text.
4. Record `template_profile: wide-v3` in slide data: KaiTi40pt song titles, KaiTi52pt lyric body, SimSun scripture with explicit size. Legacy is KaiTi54pt/48pt. Set both Name and NameFarEast for the appropriate role; retain separate church-name fonts. Document user/template typography overrides rather than forcing bundled defaults.
5. Keep lyrics to three lines maximum, preferably two complete musical phrases. Keep fixed size across lyric pages, no automatic shrinking, and top-align the first two-line body below the title.
6. Design pale upper reading space, right-middle scenery, and simple natural gray-purple lower quarter. Never bake a solid purple bottom, Logo, text or subtitle cloud into the generated image. Read the detailed layer and prompt contract before generation.
7. Run `scripts/validate_slide_data.py` and then `scripts/validate_final_pptx.mjs FINAL.pptx SLIDES.json` for content authoring. The final validator checks actual lyric runs, line count and shrinking against the chosen profile; title, scripture, footer and subtitles need separate visual/native checks.
8. Render and review every affected page. For compact scripture, check verse-number baselines visually against their text, as equal shape coordinates can still look misaligned. Test Microsoft PowerPoint 复制/edit/save/reopen for each distinct layout. Check cloud off, cloud on, and two-line subtitle overlays in a QA copy. Preserve intentional empty subtitle fields; remove unused generic title/subtitle placeholders.

## Deliverables

For lyric authoring deliver an editable PPTX, `complete_lyrics.md`, and `lyrics_audit.md`. For background revisions deliver the revised PPTX and, when generating artwork, independent images and prompts. Preserve the source and report meaningful unperformed checks. Never overwrite skill assets during normal deck production.

无上部背景的可复用模板已保存在 [assets/pccs-wide-v3-foreground.pptx](assets/pccs-wide-v3-foreground.pptx)，保留独立前景、完整Logo和可选字幕层。

默认显示当前字幕紫色云雾层，65%透明备选层保持隐藏；无上部背景模板也使用此默认设置。用户仍可在选择窗格中关闭云雾。

Existing repository plans without template_profile keep the earlier refined40pt/44pt rules. Explicit legacy uses48pt/54pt; new work declares wide-v3. Existing verse reconstruction and attribution evidence are retained.
