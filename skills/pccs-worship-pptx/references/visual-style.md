# PCCS Visual Style

## Scope and Priority

Use this visual system when the user requests a refined, themed, or content-adapted deck, or when revising a deck that already uses this system. A direct user instruction or a newly supplied template always overrides these defaults. For a strictly template-faithful request, preserve the selected template instead of introducing new artwork.

Once this system is active for a deck, keep it active for later revisions unless the user explicitly changes direction.

## Song Backgrounds

- Design one distinct background scene for each song. Derive the scene from the song's central image, message, and emotional direction rather than reusing one generic image.
- Keep every song in one coherent visual family. The bundled refined PCCS family uses ivory, pearl white, pale lavender, muted gold, and limestone gray, with soft natural light and restrained texture.
- Keep the upper-center and central lyric region quiet, low contrast, and free of detailed objects. Concentrate visual detail near the edges and lower-right area.
- Do not place text, logos, watermarks, prominent faces, hands, crowds, or high-contrast objects in generated backgrounds unless the user explicitly requests them.
- Avoid busy texture, hard horizons, and bright highlights directly behind lyrics. The background must support the text rather than compete with it.
- Copy generated or edited background assets into the project workspace so the deck can be rebuilt reproducibly.
- Add each background once to a song-specific custom layout. Do not repeat the same full-slide image on every slide and do not flatten the complete slide into a bitmap.
- Give every distinct custom layout a unique `Name` and a unique `MatchingName`. PowerPoint can render duplicated layouts with the wrong song background when their `MatchingName` values collide, even when the OOXML relationships appear correct.

## PCCS Logo and Church Identity

- Preserve the original PCCS logo, church name, footer, and all other identity elements from the selected template.
- Inspect whether the custom background covers any part of a logo or mark that protrudes beyond the footer band, including the PCCS cross tip.
- Prefer the original native or vector logo element when it is available separately.
- If the protruding element exists only inside the template bitmap, crop the exact original pixels, remove only the surrounding background to transparency, and reuse that result. Do not redraw, trace, recolor, or approximate the mark.
- Map the source-image crop to slide coordinates proportionally. Keep its size and position aligned to the untouched template pixels beneath it.
- Place the transparent overlay above the song background on every affected custom layout. Keep it on the layout rather than copying it onto every slide.
- Give the overlay a descriptive shape name such as `PCCS logo tip overlay` so later revisions can identify it safely.

## Refined Typography

These colors and shadows are the defaults for the bundled refined ivory/lavender/gold style. Explicit user colors or a newly supplied template override them.

| Element | Fill | Text shadow |
|---|---|---|
| Lyric body | deep aubergine `#302733` | warm gray-purple `#756A78`, 55% transparency, 2.2pt blur, 0.8pt X offset, 1.2pt Y offset |
| First-page song title | muted liturgical violet `#5B3D69` | muted gold-gray `#B7A886`, 72% transparency, 1.8pt blur, 0.7pt X offset, 1.0pt Y offset |
| Continuation-page song name | softened violet `#62486C` | gray-purple `#8F8094`, 68% transparency, 1.2pt blur, 0.5pt X offset, 0.7pt Y offset |

- Apply shadow to `TextFrame2.TextRange.Font.Shadow`, not to the text box shape.
- Keep the existing `KaiTi` and size rules from `ppt-template-rules.md` unless the user explicitly changes them.
- Use one typography treatment consistently across all songs in the same deck.
- Do not simulate shadows with duplicate text layers.
- Do not add gradients, glow, outlines, bevels, or heavy black shadows to lyrics.
- Check contrast against every song background. If a background prevents the standard palette from remaining legible, adjust the background first; change text colors only as a documented last resort.

## Placeholder Cleanup

- Before final save, remove empty title and subtitle placeholders from every generated slide, including placeholders that display `Click to add title` or `Click to add subtitle` in PowerPoint.
- In PowerPoint automation these normally use placeholder types `3` and `4`, but confirm that the placeholder text is empty before deletion.
- Never delete a non-empty title, lyric, scripture, footer song name, or church identity shape.
- Do not remove placeholders from the bundled template asset itself; clean only the generated working deck.

## Duplication Safety

- Keep custom backgrounds and logo overlays on custom layouts so a copied slide retains the complete visual identity.
- Keep lyrics, titles, scripture, and continuation song names as editable slide text.
- Test at least one first page and one continuation page for every distinct song-specific layout when Microsoft PowerPoint is available.
- After duplication and reopen, confirm that the copied slide retained the correct song background, logo overlay, footer identity, typography, and editable text.
