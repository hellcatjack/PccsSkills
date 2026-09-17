# PCCS Visual Style

## Scope and Priority

Use this visual system when the user requests a refined, themed, or content-adapted deck, or when revising a deck that already uses this system. A direct user instruction or a newly supplied template always overrides these defaults. For a strictly template-faithful request, preserve the selected template instead of introducing new artwork.

Once this system is active for a deck, keep it active for later revisions unless the user explicitly changes direction.

## Template and Canvas Contract

- Resolve the **latest effective template** before designing. A newly supplied non-empty template is authoritative for the current project; otherwise use the bundled template. Do not inherit an older embedded layout merely because it exists inside a source deck.
- The current PCCS slide is `720x405pt`, with a native footer occupying the lower `60pt`. Refined artwork covers only the upper `720x345pt` content region.
- Request each worship background natively at `1920x920` with a `48:23` ratio, then place the full image at `Left=0`, `Top=0`, `Width=720`, `Height=345` points. Record actual returned pixels. A tool-returned size with relative aspect-ratio error at most `0.1%` may fill this rectangle without cropping; record the small scaling. Regenerate larger ratio mismatches. Do not report the requested size as the measured size.
- Do not place a `16:9` image at a negative Y offset. That crops the intended scene, weakens the composition, and causes objects to disappear behind the footer.
- Keep the native footer, PCCS logo, church name, and other identity elements from the latest effective template rather than baking them into generated artwork.

## Song Backgrounds

- Design one distinct background scene for each song. Derive the scene from the song's central image, message, and emotional direction rather than reusing one generic image.
- Keep every song in one coherent visual family. The bundled refined PCCS family uses ivory, pearl white, pale lavender, muted gold, and limestone gray, with soft natural light and restrained texture.
- Keep the upper-center and central lyric region quiet, low contrast, and free of detailed objects. Concentrate visual detail near the edges and lower-right area.
- Do not place text, logos, watermarks, prominent faces, hands, crowds, or high-contrast objects in generated backgrounds unless the user explicitly requests them.
- Avoid busy texture, hard horizons, and bright highlights directly behind lyrics. The background must support the text rather than compete with it.
- Copy generated or edited background assets into the project workspace so the deck can be rebuilt reproducibly.
- Add each background once to a song-specific custom layout. Do not repeat the same full-slide image on every slide and do not flatten the complete slide into a bitmap.
- Give every distinct custom layout a unique `Name` and a unique `MatchingName`. PowerPoint can render duplicated layouts with the wrong song background when their `MatchingName` values collide, even when the OOXML relationships appear correct.

## Sanctuary Visibility and First-Page Balance

- Compose for **front-row sightlines**. Keep the main lyric block in the upper half of the full slide (`y<=202.5pt`). Balance line length, margins, spacing, and quiet negative space; larger text is not automatically a better composition.
- Preserve a quiet upper-center reading field. Do not place a bright window, horizon, face, architecture edge, or high-frequency texture directly behind the first two lyric lines.
- On a song's first page, a title plus **two lyric lines** must **top-align** within the body region. Do not vertically center those two lines in the remaining space; the result sits too low in the sanctuary and looks visually detached from the title.
- For three lyric lines, use the established lyric grid and balanced line spacing. Do not switch font size merely to force visual centering.
- Keep title, lyric block, and continuation song name on stable shared anchors so repeated pages do not jump vertically.

## PCCS Logo and Church Identity

- Preserve the original PCCS logo, church name, footer, and all other identity elements from the selected template.
- Inspect whether the custom background covers any part of a logo or mark that protrudes beyond the footer band, including the PCCS cross tip.
- Prefer the original native or vector logo element when it is available separately.
- If the protruding element exists only inside the template bitmap, crop the exact original pixels, remove only the surrounding background to transparency, and reuse that result. Do not redraw, trace, recolor, or approximate the mark.
- Map the source-image crop to slide coordinates proportionally. Keep its size and position aligned to the untouched template pixels beneath it.
- Place the transparent overlay above the song background on every affected custom layout. Keep it on the layout rather than copying it onto every slide.
- Give the overlay a descriptive shape name such as `PCCS logo tip overlay` so later revisions can identify it safely.

The PCCS cross tip contains a translucent warm halo. A colored or textured background directly behind that halo creates a visible color blob even when the crop itself is correct. For every `1920x920` background:

- Reserve approximately `x=80..300px`, `y=760..920px` as a uniform **warm pearl-white** or ivory field.
- Feather the field into the surrounding artwork; do not use a visible rectangle, hard ellipse, lavender ribbon, or isolated white patch.
- Keep architecture edges, foliage, water texture, shadows, photographs, and saturated color outside this zone.
- If the generated artwork contains color in the zone, blend it to warm ivory before inserting the exact `PCCS logo tip overlay`.

## Refined Typography

These colors and shadows are the defaults for the bundled refined ivory/lavender/gold style. Explicit user colors or a newly supplied template override them.

| Element | Fill | Text shadow |
|---|---|---|
| Lyric body | deep aubergine `#302733` | warm gray-purple `#756A78`, 55% transparency, 2.2pt blur, 0.8pt X offset, 1.2pt Y offset |
| First-page song title | muted liturgical violet `#5B3D69` | muted gold-gray `#B7A886`, 72% transparency, 1.8pt blur, 0.7pt X offset, 1.0pt Y offset |
| Continuation-page song name | softened violet `#62486C` | gray-purple `#8F8094`, 68% transparency, 1.2pt blur, 0.5pt X offset, 0.7pt Y offset |
| Author/copyright | muted plum `#51415D` | none |

- Apply shadow to `TextFrame2.TextRange.Font.Shadow`, not to the text box shape.
- Keep the existing `KaiTi` and size rules from `ppt-template-rules.md` unless the user explicitly changes them.
- Use one typography treatment consistently across all songs in the same deck.
- Do not simulate shadows with duplicate text layers.
- Do not add gradients, glow, outlines, bevels, or heavy black shadows to lyrics.
- Check contrast against every song background. If a background prevents the standard palette from remaining legible, adjust the background first; change text colors only as a documented last resort.
- Keep body text out of the lowest part of the content canvas when the same composition fits higher. This is a visibility requirement, not a reason to change the fixed lyric font size.

## Song Grid and Copyright Bar

All coordinates are PowerPoint points on `720x405pt`; sizes are explicit, with zero text-box insets and no auto-fit.

| Editable element | Font | x, y, width, height | Paragraph treatment |
|---|---|---|---|
| First-song title | KaiTi 44pt | `35,14,650,58` | centered, 52pt fixed line spacing |
| First-page lyrics | KaiTi 40pt | `40,92,640,n*50+4` | centered, top aligned, 50pt fixed line spacing |
| Continuation lyrics | KaiTi 40pt | `40,42,640,n*50+4` | same treatment |
| Continuation song name | KaiTi 22pt | `350,347,345,29` | right aligned, 26pt fixed line spacing |
| Author/copyright | KaiTi 9pt | `345,377,350,23` | right aligned, normally two lines, 10.5pt fixed line spacing |

The first-page grid fits at most two lyric lines in the upper half; continuation pages fit three. Use musical phrase boundaries to paginate, retaining every repetition. Do not push a third first-page line beneath the reading zone.

All author, composer, publisher, license, and copyright information belongs in the **bottom purple bar**, never in the upper formal region. Keep the left church identity clear and leave a gap under the continuation song name. Store exact `credit_lines` on each song in the slide plan and keep the visible text editable. If required credit text exceeds this grid, reflow it within the footer and verify it; do not omit attribution or let it enter the lyrics.

## Formal Scripture in Mixed Decks

Use `pccs-service-pptx` for the detailed scripture grid: left aligned `SimSun 36pt` body (maximum 36), `Microsoft YaHei 28pt` heading, and separate 17pt verse markers. Keep one body size through a passage, preserve punctuation and spaces, and avoid lyric shadows. Scripture may occupy the upper-middle region; do not fragment its paragraphs into centered song lines.

Artwork may be specific to the passage while preserving the identical purple-bar style. A restrained thin gold rule and small hollow diamond between heading and body are approved decorative options. Ornament supports the reading hierarchy and remains secondary to the text; it does not determine pagination.

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
