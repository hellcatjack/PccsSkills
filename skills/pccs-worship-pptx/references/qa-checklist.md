# QA Checklist

## Scope and content

- Use the latest effective template and record its hash, size and profile. User-supplied files win.
- For background-only revisions keep source page count/order, text, punctuation, fixed line breaks, typography, layout IDs and all foreground/Logo/cloud content. Compare package parts and record only intentional background-media changes.
- For new lyrics verify accepted audit, expanded performance order, phrase-based pagination, at most three lines, exact source_lines for scripture, and actual editable runs. A source-preserving background edit does not require new lyric research.
- New wide-v3 plans explicitly select the profile. Lyrics are52pt KaiTi, title40pt KaiTi; legacy48pt/54pt remains scoped to its template. Check typography overrides against their source, not declarations alone. Set NameFarEast and Name per role; preserve separate church-name and scripture fonts.

## Visual checks

- Render every affected slide individually at full size. Identical repeated renders may share visual review only after exact pixel equivalence is verified.
- The first slide receives highest visual scrutiny; carry the alignment and content hierarchy across the deck. Use editable emphasis shapes when they serve meaning, not a dominant dark-purple block on every page.
- Current background geometry is0,0,960,540pt and native16:9. Upper reading space stays pale and quiet; right-middle scenery clears longest lines. Lower quarter retains low-saturation gray-purple natural texture. No painted solid purple bottom, hard seam or additional subtitle mist.
- Keep main text in the upper half/upper middle for front-row sightlines; two-line first pages top-align. Check longest lyrics, three-line pages and dense scripture for wrapping, collision, clipping, soft shadows and stable anchors.
- For single-slide scripture, compare the rendered baseline of every verse number with its verse, not only PowerPoint `Top` values. Confirm a compact row rhythm without accidental blank rows, the longest line is intact, and the last row ends above the subtitle cloud. Recheck after PowerPoint save/reopen.
- Logo is complete and uppercase, with its original transparent tip light and base shadow. Names are compact, aligned, each language one line, and readable. No decorative name icons. Footer remains low and independently editable.
- Check cloud off, cloud on and two-line English subtitles in a QA copy. Confirm no dirty color blob, sharp edge, enlarged footer or collision with logo/copyright. Keep tested example subtitles out of final files unless requested.
- Delete unused generic placeholders, preserving the intentional named subtitle field. Retain authentic QR codes/forms/photos and editable text.

## Structure and native PowerPoint

- Each distinct scene has a unique layout Name and MatchingName; backgrounds are independent from foreground identity.
- Perform 复制/edit/save/close/reopen on representative pages of every layout and both first/continuation lyric roles. Confirm background, Logo, footer, text font/size, cloud visibility and editability after reopening.
- Run applicable validators. Worship final validator checks actual lyrics only; verify title/scripture/subtitles separately. Service COM QA uses `-Profile wide-v3` for the current bundle and `-Profile legacy` for older custom refined layouts. Faithful legacy layouts retain their original artwork and require checks against that original structure rather than the custom-background/tip-overlay script contract.
- If a layout exporter omits `textLayout.lineCount`, treat a validator's `rendered undefined` result as an unverified check, not a layout failure or a pass. In native PowerPoint, compare each editable lyric text range with the slide plan, inspect `TextRange.Lines().Count` and `TextFrame2.TextRange.BoundWidth/BoundHeight` against its box, then render every affected page. Record that the exporter-dependent check could not run.
- Compare source and final after a scoped revision. Never infer image generation provenance, alpha quality, aesthetic success or native duplication success from ZIP validity alone.
- Keep the source and skill assets unchanged during project use. Deliver independent generated background originals and complete prompts when backgrounds were made. Report unperformed native/visual checks accurately.

Legacy-only geometry and tip-overlay checks are in [legacy-qa-checklist.md](legacy-qa-checklist.md); do not apply them to wide-v3.
