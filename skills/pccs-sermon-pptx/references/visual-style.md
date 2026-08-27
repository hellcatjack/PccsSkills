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

Use one family throughout: `STKaiti` for both Chinese and Latin characters. Titles and body may use different sizes.

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

## Composition

- Keep the reading area darker and quieter than the illustrative focal area.
- Use one main subject or small narrative group; do not scatter decorative graphics.
- Maintain adequate contrast over faces, walls, scrolls, and architectural details.
- Keep titles on one shared baseline across continuous pages.
- Use the full safe height when content is dense, but keep visible text inside approximately `x=52–707pt` and `y=55–380pt` unless an authentic photo/diagram requires a documented exception.
- Preserve existing muted-gold emphasis within body text.
