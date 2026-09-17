---
name: pccs-service-pptx
description: Use when creating or revising PCCS non-lyric service PPTX pages, including covers, announcements, scripture, welcome, QR, prayer, baptism, communion, offering, and layered pale-background templates; excludes worship-song sequencing.
---

# PCCS Service PPTX

Create editable PCCS 非歌词 service slides, including封面、家讯、经文、欢迎页、二维码和礼仪页面. Use **Presentations** for PPTX work and `pccs-worship-pptx` for song lyrics and sequencing. Mixed decks preserve both systems.

## References

- [references/input-contract.md](references/input-contract.md): exact weekly input and template profile.
- [references/content-rules.md](references/content-rules.md): wording, scripture, authentic QR/forms/photos.
- [references/visual-style.md](references/visual-style.md) and [references/layered-template-v3.md](references/layered-template-v3.md): current background, typography, low footer, complete Logo and optional local subtitle mist.
- [references/qa-checklist.md](references/qa-checklist.md): preservation, rendering and duplication.

## Workflow

1. Use the latest supplied template; otherwise copy [assets/pccs-wide-v3.pptx](assets/pccs-wide-v3.pptx). This is the 64-page design reference; use its scripture pages16/17 or adapt another representative page, replacing historical content and removing unused pages. [assets/pccsworship.pptx](assets/pccsworship.pptx) remains the explicit legacy option.
2. Inspect slide size, every relevant page, master/layout, picture relation, identity group and cloud visibility. Distinguish a background-only revision from content/layout work. For background-only work preserve all text, fonts, order, positions and non-background media; replace only designated background image parts.
3. For new content normalize and run `scripts/validate_project.py`. Supply `template_profile: wide-v3`, 16:9 background dimensions and `background_geometry_points: [0,0,960,540]`. Keep all supplied wording and canonical scripture lines unchanged. Condense scripture to one page only when requested; use two if the user allows it and one becomes too small.
4. Use pale upper reading space and right-middle subjects. Keep the lower quarter simple natural gray-purple texture, with no solid purple block or extra cloud painted into the image. Fresh redraws start from complete prompts with no old-image input. Keep the independent foreground #E7DFED footer, complete PCCS Logo and editable church names.
5. Keep essential text high for front-row sightlines. Use deliberate first-slide hierarchy and content-specific scenes in a coherent pearl/ivory/lilac family. Preserve authentic QR codes, forms and photos. Keep text and hierarchy accents editable.
6. Give every custom layout a unique Name and MatchingName. Preserve the current slide-local identity layers and named empty subtitle field. Clean only unused generic placeholders, including Click to add title and Click to add subtitle.
7. Render individual pages and test 复制/edit/save/reopen for every layout. Use `scripts/qa_pccs_service_pptx.ps1 -Profile wide-v3` for the bundled current structure. Check two-line subtitle overlays and cloud on/off separately. User templates with different structure require adapted checks, not forced geometry.

## Legacy profile

Only for the old720×405 asset: 1920x920 artwork,48:23, placement0,0,720,345 and an exact PCCS logo tip overlay. Read `references/legacy-visual-style.md`. Use `-Profile legacy` only for custom refined legacy layouts with the named background and tip-overlay structure. For a faithful untouched legacy background, inventory and test its original layout structure directly; do not add a custom background or tip merely to satisfy this specialized QA script. These rules do not apply to the current complete-logo wide template.

## Deliverables

Return the editable deck and concise requested QA information. Keep source files intact; for a requested in-place revision back up the source and replace it only after verification. Never modify skill assets during normal deck production.

无上部背景的可复用模板已保存在 [assets/pccs-wide-v3-foreground.pptx](assets/pccs-wide-v3-foreground.pptx)，保留独立前景、完整Logo和可选字幕层。

默认显示当前字幕紫色云雾层，65%透明备选层保持隐藏；无上部背景模板也使用此默认设置。用户仍可在选择窗格中关闭云雾。
