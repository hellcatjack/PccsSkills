# QA Checklist

Delivery is blocked until all applicable checks pass.

## Source and Lyrics

- [ ] Every song has a matched recording, accepted image baseline, or verified official lyric material with an explicit user arrangement. Official lyrics plus a known arrangement do not require an unrelated recording merely to satisfy QA.
- [ ] Playlist/channel matches were verified song by song.
- [ ] Match confidence and sources actually accessed are recorded.
- [ ] Official author/copyright text and applicable permission evidence are retained separately from lyrics; no attribution was discarded during transcription.
- [ ] Repeat signs, alternate endings, and cross-line carry-over words were reviewed semantically.
- [ ] User arrangement is fully expanded; absent arrangement follows the verified performance.
- [ ] Performance notes are not visible as lyrics.
- [ ] Song lyrics use simplified Chinese and `祢`/`祂` correctly; scripture quotations retain their approved wording.
- [ ] `lyrics_audit.md` exists and every correction has evidence and a reason.
- [ ] `complete_lyrics.md` contains canonical sections and every performed instance.
- [ ] Explicit scripture from TXT/guide input is stored as ordered `source_lines`; any authorized character normalization is audited without changing line boundaries.

## Slide Data

- [ ] `scripts/validate_slide_data.py` passes.
- [ ] No repeat shorthand or vague references remain.
- [ ] Each performed section is represented exactly once in sequence; multipage sections share one `performance_index`, while a grouped ending page uses consecutive `performance_indexes`.
- [ ] Consecutive one-line `End*2` or `End*3` repetitions are combined on one page when they fit, with one identical visible line per performance.
- [ ] Lyric pages have at most three lines and no punctuation.
- [ ] When score evidence is available, page breaks follow complete musical phrases, breath points, rests, or cadences; two-line pages are preferred when they better match singing rhythm.
- [ ] Single spaces divide phrases.
- [ ] Concatenating the ordered `lines` from every page for each `scripture_id` reproduces its canonical `source_lines` exactly.
- [ ] `single_slide: true` scripture uses exactly one slide.

## Visual and Template Verification

- [ ] The effective template is recorded as either `user_supplied` or `skill_default`; an omitted template resolves to `<skill-dir>/assets/pccsworship.pptx`.
- [ ] The bundled template remains unchanged because generation used a working copy.
- [ ] Every slide was rendered individually at full size, not checked only in montage form.
- [ ] `scripts/validate_final_pptx.mjs FINAL.pptx SLIDES.json` passes against the actual PPTX; slide-plan declarations alone are not accepted as font evidence.
- [ ] Text has no clipping, overflow, unintended wrapping, overlap, or bottom-heavy placement.
- [ ] First-song titles are centered `KaiTi` at the active `typography.title_font_pt`, default `44pt`.
- [ ] Every non-empty lyric run in the actual PPTX is `KaiTi` at the active `typography.lyric_font_pt`, default `40pt`. Any departure from the defaults is backed by the explicit user request and matching `override_reason`; inherited old template sizes do not count as an override.
- [ ] Every author/copyright box is right aligned, editable, normally `9pt`, and fully inside the purple bar (`y=345..405pt`), clear of the left identity and the `22pt` continuation song name. No credit appears in the upper formal region.
- [ ] Scripture uses the current formal profile: left aligned `SimSun`, uniform through the passage and no larger than `36pt`, with left-aligned `Microsoft YaHei 28pt` headings and no body shadow. If a later explicit user instruction replaces that profile, verify its recorded `style_override_reason` and actual declared style. Decoration between heading and text is restrained and does not reduce reading clarity.
- [ ] Every planned lyric line remains one rendered line; the rendered line count exactly matches the slide plan and no automatic shrinking is active.
- [ ] Each fixed scripture source line is one visible paragraph with no automatic wrap, merge, split, reorder, or missing text. For explicitly non-fixed continuous input (`source_lines_fixed: false`, `allow_visual_wrap: true`), verify exact paragraph text while allowing rendered wrapping.
- [ ] Both `Name` and `NameFarEast` are set for editable Chinese runs.
- [ ] Template-faithful decks preserve template title and continuation song-name colors; refined decks use the fills and text shadows defined in `visual-style.md` or an explicit user override.
- [ ] Refined decks use a distinct content-appropriate background for each song while keeping one coherent palette, medium, and lighting treatment.
- [ ] Refined backgrounds were requested at `1920x920`, measured on return, and composed for `48:23`; actual-size exceptions meet the `0.1%` ratio tolerance in `visual-style.md`. Full images occupy `0,0,720,345pt`, with no negative-Y placement or cropping behind the footer.
- [ ] The upper-center lyric area remains quiet and low contrast, with no dense artwork or bright highlight interfering with text.
- [ ] Lyric placement accounts for **front-row sightlines**, with actual text ink in the upper half (`y<=202.5pt`). Inspect native text bounds as well as boxes. Scripture may use the upper-middle region for complete paragraphs.
- [ ] A **two-line first page** is **top-aligned** beneath the title rather than vertically centered in the remaining content region.
- [ ] Every distinct song background uses the intended custom layout, and each such layout has a unique `Name` and `MatchingName`.
- [ ] Background, PCCS logo, and church identity are correct on every page.
- [ ] No background obscures the PCCS logo cross tip or another protruding identity element; any restoration overlay uses the exact original pixels and is aligned correctly.
- [ ] The PCCS cross tip sits above a softly blended **warm pearl-white** safe field with no lavender, gray, or saturated color blob behind its halo.
- [ ] No generated slide contains an empty title or subtitle placeholder, including `Click to add title` and `Click to add subtitle` boxes.
- [ ] Lyrics remain editable text, not rasterized text.
- [ ] For a scoped revision, same-renderer hashes or image comparison confirm unchanged slides are pixel-identical to an already reviewed reference; visually inspect changed pages and preserved identity regions. Record intentional differences.

## Microsoft PowerPoint Duplicate Test

Perform this on at least one first-song page and one continuation page:

1. Open the generated PPTX in Microsoft PowerPoint.
2. Duplicate/copy and paste the page.
3. Edit title and lyric text on the copy.
4. Save, close, and reopen the file.
5. Confirm the copied page retains the correct song-specific background, PCCS logo and any logo-tip overlay, church name, colors, text shadows, fonts, positions, and editable text.

For refined decks, repeat the duplicate test for at least one first page and one continuation page from every distinct song-specific custom layout.

Use a QA copy and a real visible character edit. After saving and reopening, verify text style, exact backgrounds, footer, and editability. Close only presentations opened by the test; never call `PowerPoint.Application.Quit()` on a possibly user-owned application. PowerPoint may split text runs when editing; do not mistake run segmentation for loss of formatting or claim pixel identity in edited glyph regions.

The final delivered file must match the validated/rendered candidate by hash. Record the final path and hash. Rendering and contrast checks support readability; do not claim on-site sanctuary visibility testing without an actual venue check.

If PowerPoint automation is unavailable, or the user explicitly declines visual testing for a revision, report the unperformed test as a delivery limitation; do not mark it passed from package inspection alone.

## Deliverables

- [ ] `output.pptx`
- [ ] `complete_lyrics.md`
- [ ] `lyrics_audit.md`
- [ ] Source/ASR summary when those sources were used
- [ ] QA result states what was rendered and whether the PowerPoint duplicate test passed
