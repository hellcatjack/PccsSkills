# Preservation and Layout

## Pre-edit Snapshot

Inventory the source before any mutation:

- slide size, count, order, names, masters, and layouts;
- shape IDs, types, names, geometry, and z-order;
- exact text including `\r`, `\n`, vertical tabs, spaces, and hard line breaks;
- font runs, paragraph sizes, spacing, bullets, indentation, color, and highlights;
- pictures and media;
- `TimeLine.MainSequence` effects and slide transitions.

Use `scripts/inventory_sermon_pptx.ps1` for the machine-readable baseline.

## Editing Method

For an existing animated deck, prefer native Microsoft PowerPoint automation and edit shapes in place by ID. Avoid round-tripping through a library that imports or rebuilds slides when that can drop animations, transitions, shape IDs, theme relationships, or media.

Open the source, save to a new candidate path, and never use destructive Git or filesystem operations to replace the original.

## Low-Resolution Cover Replacement

Export and inspect the cover picture alone, without the PowerPoint title text. If it is visibly soft at the target video frame or smaller than that frame, use **imagegen** with the exported image as the strict edit target. The prompt contract is: same camera and composition, same people and relationships, same wall/object layout, same negative space, same warm sacred palette, no text, and only higher material, clothing, face, and lighting detail.

A PowerPoint picture shape is not a normal fill. `Shape.Fill.UserPicture()` can add a new package image without changing the `p:pic/a:blip` relationship that PowerPoint renders. On the candidate copy, replace the unique media part while retaining the existing relationship:

```powershell
& '<skill-dir>/scripts/replace_cover_media.ps1' `
  -Deck '<candidate.pptx>' -Redraw '<redrawn-cover.png>' `
  -SlideNumber 1 -ShapeId 3
```

The script converts the redraw to the embedded media part's existing format and changes only that media payload. It aborts if the media is shared, the shape is not a picture, or the embedded format is unsupported. Do not delete and recreate the shape to bypass a stop.

## Page Families

Create a layout specification before editing. Consecutive pages in one family must share the same title position, body origin, width, vertical anchor, margins, title size, body size, and paragraph spacing.

Typical families:

- cover and closing;
- speaker introduction;
- scripture sequence;
- sermon section dividers;
- sermon explanation/content;
- text plus authentic photo;
- image-only maps, charts, or diagrams.

Section dividers may use larger title/list sizes. Photo and diagram pages may use narrower text widths, but their title baseline should still align with the related sermon family.

## Text Rules

- Keep every character and hard line break exact. Do not paraphrase, repunctuate, merge, split, translate, or normalize whitespace.
- Let PowerPoint create soft wrapping by changing text-box width; do not insert new hard line breaks to force a visual result.
- Use top vertical anchoring so title position does not drift when a page contains more or less text.
- Preserve bullets, indentation, bold, color, and emphasis runs.
- Keep title and body in one font family. Different sizes are allowed and expected.

## Scripture Section Spacing

Use paragraph spacing, not inserted blank lines or new hard breaks. A scripture layout group declares:

- `verseStartSpaceBefore: 4` for every verse-number paragraph after the first;
- `firstVerseSpaceBefore: 0`;
- `continuationSpaceBefore: 0` for hard-wrapped continuation paragraphs;
- `bodySpaceAfter: 1`, or `0` on a verified dense exception;
- `blankSpaceAfter: 2`.

Before assigning these values, set `LineRuleBefore = 0` and `LineRuleAfter = 0`. PowerPoint uses `-1` for line-multiple spacing, so `SpaceBefore = 4` with `LineRuleBefore = -1` means four lines rather than four points.

Apply the declared rule to the candidate:

```powershell
& '<skill-dir>/scripts/apply_scripture_spacing.ps1' `
  -Deck '<candidate.pptx>' -LayoutSpecPath '<layout.json>'
```

## Capacity Decision Order

Apply the standard group rule first and render it. If a page does not fit:

1. Use the available video-safe width or height without moving the title baseline.
2. Change `bodySpaceAfter` from `1pt` to `0pt` only on the affected page.
3. Reduce `verseStartSpaceBefore` from `4pt` to `3pt` only if the rendered page still does not fit.
4. Reduce body text by one point at a time; on the `720×405pt` reference use `22pt`, then `21pt`, then `20pt`.
5. Record the page as a capacity exception in the layout spec and handoff.

Do not shrink the entire group because one page is dense. Do not reduce a title unless the title itself cannot fit.

## Layout Spec

`scripts/qa_sermon_pptx.ps1` accepts a JSON file:

```json
{
  "slideWidth": 720,
  "slideHeight": 405,
  "groups": [
    {
      "name": "scripture",
      "slides": [3, 4, 5],
      "shapeId": 3,
      "left": 52,
      "top": 55,
      "width": 655,
      "height": 325,
      "verticalAnchor": 1,
      "wordWrap": -1,
      "titleSize": 32,
      "bodySize": 22,
      "blankSize": 8,
      "titleSpaceAfter": 10,
      "bodySpaceAfter": 1,
      "blankSpaceAfter": 2,
      "verseStartSpaceBefore": 4,
      "firstVerseSpaceBefore": 0,
      "continuationSpaceBefore": 0
    }
  ]
}
```

Place exceptions in their own group. The QA script treats paragraph 1 as the title and blank paragraphs separately.
