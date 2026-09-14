# QA Checklist

Delivery is blocked until all applicable checks pass.

## Content

- [ ] Slide count and order match the approved input.
- [ ] User-supplied text is character-for-character preserved unless an explicit edit was approved.
- [ ] Scripture `source_lines` retain exact characters, punctuation, order, and fixed line boundaries.
- [ ] Scripture translation and verse boundaries are verified; separated verse numbers have `raw_source_lines`, exact prefixes and a reconstruction audit. Full-width spaces survive exactly.
- [ ] Dates, names, email addresses, phone numbers, prices, and account information are unchanged.
- [ ] QR codes, forms, and photos are authentic uploaded assets.

## Visual

- [ ] Every slide is rendered individually at full size.
- [ ] The **latest effective template** was inspected and used; no obsolete embedded master, footer, logo, or church-name artwork replaced it.
- [ ] Backgrounds target `1920x920`, composed for `48:23`, and placed at `0,0,720,345`. Accepted nearby tool outputs have measured pixels, a recorded ratio error at most `0.1%`, and complete-image placement without cropping.
- [ ] No background is shifted to negative Y or cropped by the native footer.
- [ ] Every page has a content-appropriate visual direction within one coherent palette.
- [ ] The **first slide** received the **highest visual scrutiny** and establishes a deliberate hierarchy, alignment grid, palette, and illustration language.
- [ ] Important cover and vision text uses editable typography or **editable emphasis shapes**, not text baked into a bitmap.
- [ ] The deck does not reuse one **dominant dark-purple block** across unrelated pages; deep plum remains a controlled accent or localized panel.
- [ ] Reading areas are quiet and high contrast.
- [ ] Essential text is positioned for **front-row sightlines**, normally in the upper or upper-middle content area rather than near the footer.
- [ ] No title, paragraph, QR code, form, or photo overlaps another object or leaves the slide bounds.
- [ ] Dense announcements remain readable from the sanctuary screen.
- [ ] Formal scripture body is left-aligned `SimSun`, normally `36pt`, no larger than `36pt` under this profile, without text shadow or automatic shrinking. Any explicit user style override is recorded and checked against its effective values.
- [ ] Every page of the same reading uses one body size; smaller single-slide exceptions were rendered and remain readable. Fixed source lines do not wrap; non-fixed input wraps only visually.
- [ ] Scripture titles use left-aligned bold `Microsoft YaHei 28pt`; verse numbers use a separate `Microsoft YaHei 17pt` left column; the `KaiTi 20pt` right-aligned footer reference clears native identity content.
- [ ] The scripture body uses the upper grid (`78,90,588,n*49+5pt`, normal line spacing `49pt`), normally two or three rendered lines and at most four. Additional lines paginate unless an explicit single-slide adjustment was rendered and verified clear of the protruding logo tip. `y=345pt` is not a safe text bottom. Any optional gold rule/outlined diamond is static and editable.
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

Use `scripts/qa_pccs_service_pptx.ps1` for structural checks and automated duplication. It copies the source to a new QA path before opening it, refuses source/existing-output replacement, and never quits the shared application or closes pre-existing presentations. A real visible character replacement must preserve text styles; after save/reopen, compare the edited text, fonts, geometry, and layout with the expected copy. Appending a space or an invisible marker does not demonstrate this.

Pass `-ProjectJson PROJECT.json` to check actual named scripture bodies against the plan: exact characters and paragraphs (including full-width spaces), selected font and size, horizontal alignment, no unintended shadow, and no automatic shrinking. Validate the JSON first. For mixed decks, service records keep locally consecutive `index` values and use optional `final_slide_index` values for their actual positions; no lyric records are needed. The QA requires unique effective final indexes within the deck and consumes every declared service page, while structural, layout and duplication checks still cover the whole deck. This optional check does not verify the title, verse metadata boxes, reference, scripture source authenticity, or visual legibility; inspect those in the render. Without `-ProjectJson`, report that only structural and duplication QA ran. For mixed decks, select a `-BackgroundNamePattern` covering all intended custom backgrounds; do not mistake a naming-pattern mismatch for lost artwork. Layouts may belong to any master and are identified by master/layout index; distinct layouts must have unique `Name` and `MatchingName`.

If PowerPoint is unavailable, report that limitation instead of marking the test passed.

## In-Place Revisions

- [ ] Preserve the original file as a clearly named backup.
- [ ] Write the verified result to the user-requested path only after QA passes.
- [ ] Re-run QA against the final path after replacement.
