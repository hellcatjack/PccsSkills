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

## Slide Data

- [ ] `scripts/validate_slide_data.py` passes.
- [ ] No repeat shorthand or vague references remain.
- [ ] Each performed section is represented exactly once in sequence; multipage sections share one performance index.
- [ ] Lyric pages have at most three lines and no punctuation.
- [ ] Single spaces divide phrases.

## Visual and Template Verification

- [ ] Every slide was rendered individually at full size, not checked only in montage form.
- [ ] Text has no clipping, overflow, unintended wrapping, overlap, or bottom-heavy placement.
- [ ] First-song titles are centered `KaiTi` `54pt`.
- [ ] Lyric/scripture body is consistently `KaiTi` `48pt`.
- [ ] Both `Name` and `NameFarEast` are set for editable Chinese runs.
- [ ] Title and continuation song-name colors match the template.
- [ ] Background, PCCS logo, and church identity are correct on every page.
- [ ] Lyrics remain editable text, not rasterized text.

## Microsoft PowerPoint Duplicate Test

Perform this on at least one first-song page and one continuation page:

1. Open the generated PPTX in Microsoft PowerPoint.
2. Duplicate/copy and paste the page.
3. Edit title and lyric text on the copy.
4. Save, close, and reopen the file.
5. Confirm the copied page retains the correct background, logo, church name, colors, fonts, positions, and editable text.

If PowerPoint automation is unavailable, report the unperformed test as a delivery limitation; do not mark it passed from package inspection alone.

## Deliverables

- [ ] `output.pptx`
- [ ] `complete_lyrics.md`
- [ ] `lyrics_audit.md`
- [ ] Source/ASR summary when those sources were used
- [ ] QA result states what was rendered and whether the PowerPoint duplicate test passed
