# Visual Style

## Template Authority

- Resolve the **latest effective template** before editing. A newly supplied non-empty template wins; otherwise use the bundled PCCS template.
- Inspect the current template's footer, logo, cross-tip pixels, church names, colors, and layout geometry. Do not copy an older master or theme from the source presentation merely because it is embedded there.
- Build from a working copy of the effective template and preserve the source file.

## Canvas Contract

The PCCS slide is `720x405pt`, but the native purple footer occupies the lower `60pt`.

| Element | Geometry |
|---|---|
| Generated background asset | `1920x920px` |
| Background ratio | `48:23` |
| PowerPoint placement | `Left=0`, `Top=0`, `Width=720`, `Height=345` |
| Native footer | `Top=345`, `Height=60` |

Never place a 16:9 image at `0,-60,720,405`. That crops the intended composition and makes objects appear cut off above the footer.

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
- For bundled PCCS styling, use `KaiTi` for editable Chinese in both `Name` and `NameFarEast`.
- Default body fill: deep aubergine `#302733`.
- Default title fill: muted liturgical violet `#5B3D69`.
- Use restrained font shadows rather than black text or shape-level shadows.
- Keep important text in the upper content area so front-row heads do not block it.
- Do not use automatic font shrinking. Choose an explicit size after rendering.
- Use deep aubergine or another approved dark chromatic neutral instead of default black when the background is light. On dark pages use warm ivory, not pure white.
- Apply shadows to the text range, not to the containing shape. Shadows must remain subtle and consistent across a page family.

## Placeholder Cleanup

Delete unused structural placeholders from final slides and custom layouts, including:

- `Click to add title`
- `Click to add subtitle`
- empty date/footer placeholders
- unused slide-number placeholders

Do not delete native PCCS identity shapes or non-empty content.
