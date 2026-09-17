# Visual Style

## Template Authority

- Resolve the **latest effective template** before editing. A newly supplied non-empty template wins; otherwise use the bundled PCCS template.
- Inspect the current template's footer, logo, cross-tip pixels, church names, colors, and layout geometry. Do not copy an older master or theme from the source presentation merely because it is embedded there.
- Build from a working copy of the effective template and preserve the source file.

## Canvas Contract

The PCCS slide is `720x405pt`, but the native purple footer occupies the lower `60pt`.

| Element | Geometry |
|---|---|
| Generated background target | `1920x920px` |
| Background ratio | `48:23` |
| PowerPoint placement | `Left=0`, `Top=0`, `Width=720`, `Height=345` |
| Native footer | `Top=345`, `Height=60` |

Never place a 16:9 image at `0,-60,720,405`. That crops the intended composition and makes objects appear cut off above the footer.

When the image tool returns a nearby resolution, measure its actual width and height. Accept `abs((width / height) / (48 / 23) - 1) <= 0.001` only with a recorded pixel-size audit. Place the complete image into `720x345pt` without cropping or a negative Y offset. Regenerate if the ratio differs by more than `0.1%`; the target remains `1920x920`, not an arbitrary size. Map logo-safe pixels proportionally for an accepted alternate resolution.

## Background Direction

- Design each page or semantic page group around its content: sanctuary for welcome, paper/window light for QR, water for baptism, bread/wheat for communion, envelope/cross for offering, journey/arch for prayer, and luminous sanctuary for doxology.
- Keep one coherent family: ivory, pearl white, pale lavender, muted gold, limestone gray, and restrained desaturated olive.
- Keep the upper-center and central reading area quiet, low contrast, and free of detailed objects.
- Place meaningful objects near the far right, outer edges, or lower-right area.
- Do not generate text, logos, watermarks, QR codes, forms, prominent people, or fake church assets inside backgrounds.
- Do not include the purple footer in generated art.

## Cover and Page Hierarchy

- Treat the **first slide** as the page receiving the **highest visual scrutiny**. It must establish the deck's palette, illustration language, alignment grid, and hierarchy without looking like a generic title placeholder.
- Keep the service name, church name, vision statement, date, and other important wording editable. Use **editable emphasis shapes**, rules, restrained translucent panels, or typographic grouping when they improve hierarchy; do not rasterize this text into the background.
- Design later pages from the first slide's visual language, but vary composition according to content. A scripture page, QR page, welcome page, and communion page should not be the same background with different words.
- Do not repeat one **dominant dark-purple block** on every page. Deep plum may be an accent, title band, thin rule, or localized translucent panel, but large repeated slabs create excessive contrast against the light PCCS footer and make unrelated pages feel identical.
- When two consecutive pages serve different functions, vary image placement, negative space, and accent geometry while retaining the same palette, lighting, and typography.

## Sanctuary Visibility

- Compose for **front-row sightlines**. Keep essential titles and primary text in the **top half** or upper-middle of the content canvas whenever the amount of content permits.
- Use the lower content area for supporting imagery and secondary detail, not for the only copy of a date, instruction, scripture reference, QR caption, or call to action.
- A short two-line body should be top-aligned within its text region rather than vertically centered low on the slide.

## PCCS Logo Safety

The PCCS cross tip protrudes above the footer and contains a translucent warm halo. Colored background pixels behind it produce a visible blob.

For every `1920x920` background:

- Reserve approximately `x=80..300px`, `y=760..920px` as a uniform warm pearl-white or ivory field.
- Feather the safe field into the surrounding image; do not leave a rectangular patch or hard ellipse.
- Keep architecture edges, water ripples, foliage, photographs, lavender ribbons, and shadows out of that zone.
- If image generation leaves color in the zone, apply a large soft ivory blend before using the asset.

Extract the exact PCCS tip pixels from the selected template. Do not redraw them. Put the transparent asset on the custom layout at the template-mapped position and name it `PCCS logo tip overlay`.

For the current template, the mapped geometry is approximately:

```text
Left=48.0pt Top=316.4pt Width=45.8pt Height=29.7pt
```

Keep the overlay above the background and below no slide-local object that enters the logo area.

## Layout Ownership

- Add each distinct background once to a custom layout.
- Assign a unique layout `Name` and unique `MatchingName`.
- Put the `PCCS logo tip overlay` on that layout.
- Keep editable title/body/scripture text on the slide.
- Preserve the native footer, PCCS logo, church Chinese name, and English name from the template.

## Typography

- Match a user-supplied template when one is provided.
- For bundled PCCS non-scripture styling, use `KaiTi` for editable Chinese in both `Name` and `NameFarEast`. Formal scripture uses the reading profile below; never inherit the lyric typography merely because it shares a deck.
- Default body fill: deep aubergine `#302733`.
- Default title fill: muted liturgical violet `#5B3D69`.
- Non-scripture pages may use restrained font shadows rather than black text or shape-level shadows. Formal scripture body has no shadow.
- Keep important text in the upper content area so front-row heads do not block it.
- Do not use automatic font shrinking. Choose an explicit size after rendering.
- Use deep aubergine or another approved dark chromatic neutral instead of default black when the background is light. On dark pages use warm ivory, not pure white.
- Apply shadows to the text range, not to the containing shape. Shadows must remain subtle and consistent across a page family.

## Formal Scripture Reading Profile

These defaults are for the current `720x405pt` PCCS template. Record explicit user overrides instead of rejecting them as lyric-style violations. Keep every scripture text element editable and set both `Name` and `NameFarEast` to its selected font.

| Element | Typography | Position in points |
|---|---|---|
| Body, shape name `PCCS scripture body` or `Scripture body` | `SimSun` (宋体), `36pt`, left-aligned, no shadow; maximum `36pt` under this profile | `x=78, y=90, w=588`; height `n*49+5` for `n` rendered lines |
| Title | `Microsoft YaHei`, `28pt`, bold, left-aligned | `x=58, y=20, w=604, h=39` |
| Separate verse numbers | `Microsoft YaHei`, `17pt`, left column; align each number with its verse baseline | Place left of body without consuming its width |
| Reference in the native footer | `KaiTi`, `20pt`, right-aligned | `x=385, y=358, w=310, h=30` |

Use fixed `49pt` line spacing for the normal `36pt` body grid; set paragraph spacing before/after to zero and allow enough text-box inset space to avoid clipping. In PowerPoint's legacy paragraph API, set `LineRuleWithin = msoFalse` before `SpaceWithin = 49` to express points rather than multiples of a line. Body starts in the upper reading area; do not move a short passage downward for vertical centering. `n` means the actual rendered line count, including authorized visual wraps, not simply the number of source records.

Prefer **two or three rendered lines** per scripture page; the default grid allows **at most four**. A fifth line would extend the body toward `y=340pt`, overlapping the logo-tip region near `x=48..94pt, y=316..346pt` because the body begins at `x=78pt`. The footer edge `y=345pt` is **not a safe text boundary**. More than four lines should paginate first. Only an explicit single-slide requirement permits a separately adjusted geometry/grid after rendering confirms that every glyph clears the actual logo and sanctuary sightline areas. Check the latest template's protruding identity bounds rather than relying solely on the rectangular footer.

An optional thin muted-gold rule with an outlined diamond between the title and body can establish hierarchy. Keep it static, editable, and clear of text. Match each reading's independent background to its imagery while keeping a calm, quiet upper reading field and the shared light PCCS palette. No particular Psalm, fixed page count, decorative object, or scene is a universal default.

Prefer pagination at complete source-line or verse boundaries while retaining their order and punctuation. Only sources without fixed line breaks may wrap visually. Keep one body font size throughout each passage; never use automatic font shrinking or reduce one crowded page alone. If the user explicitly requires a single slide, first adjust safe geometry, then choose one smaller size at or below `36pt` for that passage and verify the actual render. If the intact text still cannot remain readable, report the single-slide/readability conflict instead of making unreadable text or changing the wording. Reduced-size exceptions may adjust line spacing explicitly; record the effective grid.

Place the footer reference only in the inspected clear right-side area; preserve native purple footer pixels, logo, cross tip, and church names. If the latest template uses that area for identity content, adjust the reference placement explicitly rather than covering it.

## Placeholder Cleanup

Delete unused structural placeholders from final slides and custom layouts, including:

- `Click to add title`
- `Click to add subtitle`
- empty date/footer placeholders
- unused slide-number placeholders

Do not delete native PCCS identity shapes or non-empty content.
