# QA Checklist

Delivery is blocked until all applicable checks pass.

## Inputs and Source

- [ ] The exact requested source PPTX was used.
- [ ] The likely sermon video was identified, or its absence was reported.
- [ ] The source remains unchanged and the output has a new name.
- [ ] A pre-edit inventory exists.

## Content and PowerPoint Structure

- [ ] Slide count and order match the source.
- [ ] Every text shape matches character-for-character, including punctuation, spaces, tabs, and hard line breaks.
- [ ] Shape IDs/types and picture counts are unchanged.
- [ ] A redrawn cover retains the original picture shape ID, relationship, crop, geometry, and z-order.
- [ ] The redrawn cover meets the target video dimensions and preserves the original composition without generated text.
- [ ] Every animation effect retains its target, type, trigger, duration, and delay.
- [ ] Every slide transition retains its effect and advance behavior.
- [ ] The deck remains editable and was not flattened.

## Typography and Layout

- [ ] One font family is used throughout; default `STKaiti`.
- [ ] Titles and body use the approved sizes for their page family.
- [ ] Continuous scripture pages share one exact title/body geometry.
- [ ] Continuous sermon-content pages share one exact title/body geometry.
- [ ] Top vertical anchoring prevents title drift.
- [ ] Paragraph spacing is consistent within each family.
- [ ] Scripture verse starts use the declared point-based `SpaceBefore`; continuation lines use `0pt` before.
- [ ] Scripture paragraphs have `LineRuleBefore = 0` and `LineRuleAfter = 0`; no value is being interpreted as line multiples.
- [ ] Any `20–21pt` body or spacing exception is caused by verified capacity and documented.
- [ ] Text shadow is present and subtle on all visible text.

## Visual and Video

- [ ] Every background matches the weekly cover's illustration language.
- [ ] Deep backgrounds, ivory text, muted gold, and sacred atmosphere remain coherent.
- [ ] Graphics do not interfere with scripture or sermon text.
- [ ] Text uses the available vertical frame and is not unnecessarily compressed into the upper half.
- [ ] No text, shadow, photo, map, or diagram is clipped or outside the video-safe frame.
- [ ] Authentic photos, maps, and diagrams are preserved.

## Commands

```powershell
& '<skill-dir>/scripts/replace_cover_media.ps1' -Deck '<candidate>' -Redraw '<cover.png>' -SlideNumber 1 -ShapeId '<picture-shape-id>'
& '<skill-dir>/scripts/apply_scripture_spacing.ps1' -Deck '<candidate>' -LayoutSpecPath '<layout.json>'
& '<skill-dir>/scripts/qa_sermon_pptx.ps1' -SourceDeck '<source>' -CandidateDeck '<output>' -LayoutSpecPath '<layout.json>' -ExpectedFont 'STKaiti' -RequireShadow
& '<skill-dir>/scripts/render_sermon_pptx.ps1' -Deck '<output>' -RenderDir '<empty-render-dir>'
```

Inspect every rendered slide individually at full size. Pay extra attention to the densest scripture/content page, every photo/text page, every section divider, and the final summary page. Rerun QA after the last edit.
