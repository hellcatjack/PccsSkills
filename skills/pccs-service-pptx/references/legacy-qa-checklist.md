# QA Checklist

Delivery is blocked until all applicable checks pass.

## Content

- [ ] Slide count and order match the approved input.
- [ ] User-supplied text is character-for-character preserved unless an explicit edit was approved.
- [ ] Scripture `source_lines` retain exact characters, punctuation, order, and fixed line boundaries.
- [ ] Dates, names, email addresses, phone numbers, prices, and account information are unchanged.
- [ ] QR codes, forms, and photos are authentic uploaded assets.

## Visual

- [ ] Every slide is rendered individually at full size.
- [ ] The **latest effective template** was inspected and used; no obsolete embedded master, footer, logo, or church-name artwork replaced it.
- [ ] Backgrounds are `1920x920`, composed for `48:23`, and placed at `0,0,720,345`.
- [ ] No background is shifted to negative Y or cropped by the native footer.
- [ ] Every page has a content-appropriate visual direction within one coherent palette.
- [ ] The **first slide** received the **highest visual scrutiny** and establishes a deliberate hierarchy, alignment grid, palette, and illustration language.
- [ ] Important cover and vision text uses editable typography or **editable emphasis shapes**, not text baked into a bitmap.
- [ ] The deck does not reuse one **dominant dark-purple block** across unrelated pages; deep plum remains a controlled accent or localized panel.
- [ ] Reading areas are quiet and high contrast.
- [ ] Essential text is positioned for **front-row sightlines**, normally in the upper or upper-middle content area rather than near the footer.
- [ ] No title, paragraph, QR code, form, or photo overlaps another object or leaves the slide bounds.
- [ ] Dense announcements remain readable from the sanctuary screen.
- [ ] The PCCS logo tip sits over a uniform warm-ivory safe zone without a color blob.
- [ ] The PCCS logo, Chinese church name, English church name, and purple footer are intact.

## Structure

- [ ] Every distinct scene uses one custom layout with unique `Name` and `MatchingName`.
- [ ] Each custom layout has one background and one exact `PCCS logo tip overlay`.
- [ ] Background geometry is exactly `0,0,720,345pt`.
- [ ] Text remains editable; the slide is not flattened into a screenshot.
- [ ] No empty title, subtitle, date, footer, or slide-number placeholder remains.
- [ ] Generated background assets are stored in the project workspace.
- [ ] Speaker notes include `[Sources]` for externally sourced or generated assets when required by the presentation workflow.

## PowerPoint Duplication Test

When Microsoft PowerPoint is available:

1. Duplicate at least one slide from every distinct custom layout.
2. Edit visible text on each duplicate.
3. Save, close, and reopen the QA copy.
4. Confirm the correct background, footer, logo, logo-tip overlay, text style, and editable objects remain.
5. Render the duplicates and inspect them.

Use `scripts/qa_pccs_service_pptx.ps1` for structural checks and automated duplication. If PowerPoint is unavailable, report that limitation instead of marking the test passed.

## In-Place Revisions

- [ ] Preserve the original file as a clearly named backup.
- [ ] Write the verified result to the user-requested path only after QA passes.
- [ ] Re-run QA against the final path after replacement.
