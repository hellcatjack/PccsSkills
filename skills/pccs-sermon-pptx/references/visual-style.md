# Visual Style

## Direction

Follow the weekly cover. The approved default is a deep, warm sepia biblical illustration style with painterly/cinematic lighting, quiet negative space, ivory text, muted gold titles and highlights, and restrained sacred atmosphere. Avoid modern clip-art, decorative icons, bright gradients, and busy diagrams behind scripture.

Reference images:

- [cover](../assets/reference-cover.jpg)
- [scripture](../assets/reference-scripture.jpg)
- [section divider](../assets/reference-section.jpg)
- [text with authentic photo](../assets/reference-photo.jpg)

If a weekly cover uses a different coherent illustration language, match that cover rather than forcing the sepia references. Reuse authentic uploaded photos, maps, and diagrams; do not regenerate them.

## Cover Redraw Contract

Redraw only when the exported cover is visibly soft at the target video size or has insufficient native pixels. Use the existing cover picture as the image-edit target. Keep the basic content unchanged: camera, crop, horizon, people, gestures, wall and construction elements, focal lighting, palette, and negative space for the title. Generate no lettering, symbols, logos, or extra characters.

A useful prompt has this order: lock camera and composition; enumerate the existing subjects and their positions; lock the architectural/object layout; preserve the empty title area and sepia lighting; request sharper stone, fabric, face, dust, and atmospheric detail; forbid text and new elements. Aim for at least `1600×900` for a `1600×900` video.

## Approved Default Typography

Use one family throughout ordinary scripture and sermon-content slides: `STKaiti` for both Chinese and Latin characters. Titles and body may use different sizes.

When the user explicitly authorizes a more suitable Chinese cover display font, choose one installed Song/Ming display family for the cover title and scripture, such as `Noto Serif SC`, `Source Han Serif SC`, or `STZhongsong`. Use the same cover display font family for both lines; size and weight may differ. Keep `STKaiti` on ordinary content slides unless the user separately authorizes a deck-wide change.

| Page type | `720×405pt` reference | `960×540pt` proportional range |
|---|---:|---:|
| Standard scripture/content | `32pt` title / `22pt` body | about `42–43pt` / `29–31pt` |
| Section divider | `38pt` title / `28pt` list | about `50–51pt` / `37pt` |
| Cover/closing title block | `38pt` / `24pt` subtitle | about `50–51pt` / `32pt` |
| Dense capacity exception | unchanged title / `20–21pt` body | unchanged title / `27–29pt` body |

Default continuous-content box on a `720×405pt` slide: left `52pt`, top `55pt`, width `655pt`, height `325pt`. Scale geometry and typography by `slideWidth / 720` when the deck uses a larger canvas, then render and make only measured capacity exceptions. Use top anchoring, word wrap, and zero text-frame margins. This uses the lower half of the video frame instead of compressing all text above the midpoint.

Recommended paragraph spacing:

- title: `8–10pt` after;
- ordinary body: `1pt` after;
- each verse after the first: `4pt` before, measured in points;
- dense exception: `0pt` after ordinary body while retaining the verse gap when it fits;
- intentionally blank paragraph: `8pt` font size and `2pt` after.

## Text Shadow

Apply a subtle black text shadow to all visible text:

- transparency `28%`;
- blur `4pt`;
- X/Y offset `1.5pt`;
- size `100%`.

The shadow supports video compression and textured backgrounds; it must not become a visible glow or heavy outline.

## Cover Title Contrast Gate

Render the real background and title together before choosing the final title treatment. Check the brightest and darkest representative areas behind the actual glyph region; a center-only sample is insufficient when the sky, clouds, walls, or light rays change luminance across the title.

- First relocate the title into a naturally quiet, locally uniform background region while preserving horizontal centering, safe margins, and balanced composition. Typography and placement are the primary contrast tools.
- Target at least `4.5:1` standard sRGB/WCAG contrast between the main glyph fill and its local visual backing.
- Choose a clean light or dark fill for that local region and add only the prescribed subtle shadow. Shadow supports compression but is not the sole contrast mechanism over mixed-luminance imagery.
- If no balanced placement produces sufficient contrast, use a restrained quiet backing surface that reads as part of the composition. Visible outline is a last resort; when unavoidable, keep it optically subtle and reject any poster-like, mechanical, or sticker-like edge.
- Apply the same check to the scripture reference; it may use a smaller size but must remain immediately readable.
- Inspect the full `1280×720` render and a `640×360` downscaled view. Passing a numeric contrast test does not approve typography that feels heavy, outlined, or visually disconnected from the sacred atmosphere.

## Composition

- Keep the reading area darker and quieter than the illustrative focal area.
- Use one main subject or small narrative group; do not scatter decorative graphics.
- Maintain adequate contrast over faces, walls, scrolls, and architectural details.
- Keep titles on one shared baseline across continuous pages.
- Use the full safe height when content is dense, but keep visible text inside approximately `x=52–707pt` and `y=55–380pt` unless an authentic photo/diagram requires a documented exception.
- Preserve existing muted-gold emphasis within body text.
