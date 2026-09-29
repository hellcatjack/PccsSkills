# PPT Template Rules

Use the Presentations skill and bundled workspace runtime for inspection, editing and rendering. Work on a copy.

## Template and scope

1. Use the latest explicit user source/template.
2. Otherwise use `assets/pccs-wide-v3.pptx`; `assets/pccsworship.pptx` is retained for explicitly selected legacy work.
3. Read [layered-template-v3.md](layered-template-v3.md) for current assets, representative pages, precise geometry, identity and cloud controls. This is a 64-page reference asset; new service decks are built from selected representative pages, with historical content replaced.

Inspect slide size, slides, layouts, masters, editable runs, picture relationships, groups and visibility before editing. Background-only revisions preserve page count/order, all text and font styling, object geometry/IDs and cloud visibility. Do not rerun lyric discovery or rebuild pages for that scope. For content changes, use accepted audit and expanded arrangement.

## Typography profiles

Record `template_profile: wide-v3` in new slide data. Current titles are KaiTi40pt, lyrics KaiTi52pt, scripture SimSun with38pt as the representative sample. Legacy uses54pt/48pt KaiTi. Both Name and NameFarEast must match the appropriate role. Do not apply the lyric font to church identity.

Existing user typography wins. Declare an override with `typography.basis: user_supplied_template` or `user_request`, and `lyric_font`, `lyric_font_pt`, `title_font_pt`, `scripture_font`; record where it came from in the audit. The actual final runs must match this explicit policy. No per-slide lyric shrinking or automatic shrink-to-fit. Saved plans without template_profile retain the earlier repository refined40pt/44pt validation; explicitly use legacy for the original48pt/54pt bundle, and wide-v3 for new work.

## Content and layout

Use at most three lyric lines, preferably two when musical phrasing supports it. Keep complete musical phrases, breath points, rests and cadences together. Repeated sections use identical pagination. Remove lyric punctuation in new lyric authoring, retain single spaces, and place each planned line in one paragraph without accidental wrapping. When a line does not fit the chosen lyric size, revise the phrase-based page break instead of shrinking an isolated page.

Scripture preserves exact supplied source_lines and punctuation. Each fixed source line is one paragraph; paginate only between lines. If single_slide is true, choose the largest fitting scripture size without changing those boundaries. When user allows up to two pages, set single_slide false and document a maximum of two; this is not a blanket permission for other projects.

For a one-slide passage with separate verse-number shapes, keep consecutive verses on a consistent row grid above the subtitle area. If cloning a number shape in PowerPoint, explicitly reset both `Left` and `Top`: `Duplicate()` can offset the new shape. Match the visible digit baseline to the Chinese body after rendering; identical shape tops do not guarantee optical alignment when fonts or sizes differ. Check that the longest verse stays on its intended row and that no orphaned character wraps beneath it.

Use stable upper anchors and top-align two-line first pages. Song title, lyrics, identity and subtitles must not overlap. Preserve the subtle short title separator when present, without adding ornaments to the church-name block.

## Structure and QA

Keep one replaceable background on each scene layout, with unique Name and MatchingName. Current Logo and editable foreground may remain slide-local as authored; do not move them into masters merely for tidiness. Keep the independent optional cloud layer and named empty subtitle text box. The complete current logo already contains its tip and halo.

Run validate_slide_data.py for newly authored arrangements and validate_final_pptx.mjs against actual editable lyrics. Render every affected page, check longest and three-line text, and test copying/editing/saving/reopening each distinct layout. For background-only changes compare source/final package entries: only the approved background media should differ. Do not claim a full typography/title/subtitle check from the lyric-only final validator.
