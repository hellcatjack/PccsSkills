# QA Checklist

Delivery is blocked until all applicable checks pass.

## Source and Lyrics

- [ ] Every song has a concrete source recording or an explicitly accepted image-only baseline.
- [ ] Playlist/channel matches were verified song by song.
- [ ] Match confidence and sources actually accessed are recorded.
- [ ] Repeat signs, alternate endings, and cross-line carry-over words were reviewed semantically.
- [ ] User arrangement is fully expanded; absent arrangement follows the verified performance.
- [ ] Performance notes are not visible as lyrics.
- [ ] Chinese is simplified and divine pronouns use `祢`/`祂` correctly.
- [ ] `lyrics_audit.md` exists and every correction has evidence and a reason.
- [ ] `complete_lyrics.md` contains canonical sections and every performed instance.
- [ ] Explicit scripture from TXT/guide input is stored as ordered `source_lines`; any authorized character normalization is audited without changing line boundaries.

## Slide Data

- [ ] `scripts/validate_slide_data.py` passes.
- [ ] No repeat shorthand or vague references remain.
- [ ] Each performed section is represented exactly once in sequence; multipage sections share one `performance_index`, while a grouped ending page uses consecutive `performance_indexes`.
- [ ] Consecutive one-line `End*2` or `End*3` repetitions are combined on one page when they fit, with one identical visible line per performance.
- [ ] Lyric pages have at most three lines and no punctuation.
- [ ] Single spaces divide phrases.
- [ ] Concatenating the ordered `lines` from every page for each `scripture_id` reproduces its canonical `source_lines` exactly.
- [ ] `single_slide: true` scripture uses exactly one slide.

## Visual and Template Verification

- [ ] The effective template is recorded as either `user_supplied` or `skill_default`; an omitted template resolves to `<skill-dir>/assets/pccsworship.pptx`.
- [ ] The bundled template remains unchanged because generation used a working copy.
- [ ] Every slide was rendered individually at full size, not checked only in montage form.
- [ ] Text has no clipping, overflow, unintended wrapping, overlap, or bottom-heavy placement.
- [ ] First-song titles are centered `KaiTi` `54pt`.
- [ ] Lyric body is consistently `KaiTi` `48pt`; scripture is `KaiTi` and uses `48pt` unless a documented fit exception applies.
- [ ] Each scripture source line is one visible paragraph with no automatic wrap, merge, split, reorder, or missing text.
- [ ] Both `Name` and `NameFarEast` are set for editable Chinese runs.
- [ ] Template-faithful decks preserve template title and continuation song-name colors; refined decks use the fills and text shadows defined in `visual-style.md` or an explicit user override.
- [ ] Refined decks use a distinct content-appropriate background for each song while keeping one coherent palette, medium, and lighting treatment.
- [ ] The upper-center lyric area remains quiet and low contrast, with no dense artwork or bright highlight interfering with text.
- [ ] Every distinct song background uses the intended custom layout, and each such layout has a unique `Name` and `MatchingName`.
- [ ] Background, PCCS logo, and church identity are correct on every page.
- [ ] No background obscures the PCCS logo cross tip or another protruding identity element; any restoration overlay uses the exact original pixels and is aligned correctly.
- [ ] No generated slide contains an empty title or subtitle placeholder, including `Click to add title` and `Click to add subtitle` boxes.
- [ ] Lyrics remain editable text, not rasterized text.

## Microsoft PowerPoint Duplicate Test

Perform this on at least one first-song page and one continuation page:

1. Open the generated PPTX in Microsoft PowerPoint.
2. Duplicate/copy and paste the page.
3. Edit title and lyric text on the copy.
4. Save, close, and reopen the file.
5. Confirm the copied page retains the correct song-specific background, PCCS logo and any logo-tip overlay, church name, colors, text shadows, fonts, positions, and editable text.

For refined decks, repeat the duplicate test for at least one first page and one continuation page from every distinct song-specific custom layout.

If PowerPoint automation is unavailable, or the user explicitly declines visual testing for a revision, report the unperformed test as a delivery limitation; do not mark it passed from package inspection alone.

## Deliverables

- [ ] `output.pptx`
- [ ] `complete_lyrics.md`
- [ ] `lyrics_audit.md`
- [ ] Source/ASR summary when those sources were used
- [ ] QA result states what was rendered and whether the PowerPoint duplicate test passed
