---
name: pccs-sermon-pptx
description: Use when revising a PCCS weekly sermon PPTX for video, especially when its cover is low-resolution, scripture sections are cramped, or an animated deck needs cover-matched biblical styling without changing authored content.
---

# PCCS Sermon PPTX

## Overview

Beautify an existing weekly sermon deck as an editable PowerPoint for video. The cover establishes the illustration language; continuous scripture and sermon pages share one typographic grid. Preserve the sermon as authored.

Use the **Presentations** skill for every PPTX inspection, edit, render, and verification task. Do not use subagents in this workflow.

When the cover is visibly soft at the target video size, use **imagegen** as a strict edit target and preserve its basic composition.

## Required References

Read before editing:

1. [references/input-contract.md](references/input-contract.md) for source, video, output, and discovery.
2. [references/preservation-and-layout.md](references/preservation-and-layout.md) for hard line breaks, media replacement, scripture spacing, and capacity exceptions.
3. [references/visual-style.md](references/visual-style.md) for cover-led illustration, STKaiti typography, text shadow, and video-safe geometry.
4. [references/qa-checklist.md](references/qa-checklist.md) before delivery.

## Workflow

1. Discover the exact deck and likely video with `scripts/discover_sermon_inputs.ps1`; a user-named file wins.
2. Inventory the source with `scripts/inventory_sermon_pptx.ps1`.
3. Inspect every slide, group continuous page families, and define one layout-spec rule per family before editing.
4. Edit a new candidate with native PowerPoint automation. Keep text editable, use the cover style, apply text shadow, and use the video-safe height.
5. For a soft cover, preserve camera, people, objects, negative space, palette, and lighting; generate no text. Replace the inventoried picture shape's unique media with `scripts/replace_cover_media.ps1`.
6. For scripture groups, declare `verseStartSpaceBefore` and run `scripts/apply_scripture_spacing.ps1`. Start with `4pt` before later verses and `1pt` after body; use `0pt` after only on dense exceptions.
7. Run `scripts/qa_sermon_pptx.ps1`, render with `scripts/render_sermon_pptx.ps1`, inspect every slide at full size, and rerun QA on the final file.

## Quick Reference

| Need | Source of truth |
|---|---|
| Cover redraw and sacred style | `visual-style.md` |
| Picture ID, media preservation, verse spacing | `preservation-and-layout.md` |
| Layout and structure validation | layout JSON + `qa_sermon_pptx.ps1` |

## Hard Gates

- Do not change slide count, slide order, visible text, punctuation, hard line breaks, pictures, animations, or transitions unless the user explicitly authorizes that exact change.
- Do not replace the deck by rebuilding it in a way that loses PowerPoint object IDs or animations.
- Do not use `Fill.UserPicture` on a PowerPoint picture shape; use the media script on the candidate.
- Scripture spacing must use `LineRuleBefore = 0` and `LineRuleAfter = 0`; `-1` makes `SpaceBefore` a line multiple.
- Do not mix title and body font families. The approved default is `STKaiti`; different title/body sizes are expected.
- Do not change font size or paragraph spacing on an isolated page until rendering proves the standard rule does not fit.
- Do not add busy graphics behind scripture. Deep backgrounds, light text, restrained gold, and quiet negative space create the sacred atmosphere.
- Do not claim completion without source-versus-candidate QA and individual full-size rendering of every slide.

## Common Failures

| Symptom | Stop condition |
|---|---|
| Render still shows the old cover | The picture relationship was not replaced; do not rebuild the shape. |
| Verse gaps become enormous | Spacing is in lines, not points. |
| Wrong shape is edited | `Shapes.Item(number)` used an index; find the shape by `Id`. |
| QA ignores verse gaps | The layout group lacks `verseStartSpaceBefore`. |

## Deliverables

- A newly named editable PPTX; preserve the source.
- The identified sermon video path, or a clear report that no matching video was found.
- A concise QA report: slide count, cover redraw dimensions, font family, layout groups/exceptions, verse-spacing rule, animation/transition preservation, render count, and unresolved issues.
