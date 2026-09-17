# PPT Template Rules

## Required Tooling

Use the **Presentations** skill for template inspection, PPTX modification, rendering, and validation. Load the workspace presentation dependencies before editing. Follow its render-and-verify workflow and use native editable shapes and text.

## Template Selection

1. If the user supplies a non-empty `template_pptx`, use that file.
2. Otherwise use `<skill-dir>/assets/pccsworship.pptx`.

Resolve the bundled path from the skill directory, not from the current working directory. Copy the selected template into the project workspace and edit the copy. Never overwrite the bundled asset.

## Inspect Before Editing

Inspect the complete selected template, including slide size, all template slides, masters, layouts, placeholders, background inheritance, theme colors, fonts, logo/church identity shapes, and text-box geometry. Do not assume slide 1 and slide 2 are interchangeable.

Use the template's first-song page for the first page of each song and its continuation style for later lyric pages. For a strictly template-faithful request, preserve the current template's title color and continuation-page song-name color exactly. When refined or content-adapted styling is requested or already present, follow `visual-style.md` instead.

## Template Integrity

- Keep background, PCCS logo, and church name as native template/master/layout content where possible.
- Do not replace editable lyrics with screenshots.
- Do not flatten the whole slide into a background image.
- If copying a slide loses its background or church identity, repair the master/layout relationship before generating the deck.
- If native inheritance cannot be repaired reliably, use self-contained editable/template shapes as a documented fallback and verify duplication again.
- When songs use different custom backgrounds, create one custom layout per distinct scene and give each layout a unique `Name` and `MatchingName`.
- Inspect protruding logo elements such as the PCCS cross tip. If a new background covers them, restore the exact original element as a transparent layout overlay according to `visual-style.md`; do not redraw it.
- Remove empty title and subtitle placeholders from generated slides before the final save. Never remove non-empty content or alter the bundled template asset.

## Visual Styling

For a refined, themed, or content-adapted deck, apply `visual-style.md` in addition to this file. It defines song-specific background composition, the shared PCCS palette, logo-tip extraction and overlay, text colors and shadows, placeholder cleanup, and duplication safety. Explicit user instructions and newly supplied template rules remain authoritative.

## Typography

- Set song text to `KaiTi` in both `Name` and `NameFarEast`. Formal scripture uses `SimSun`; its heading uses `Microsoft YaHei`.
- First page of each song: centered song title at exactly `44pt`.
- Lyric body: exactly `40pt`.
- Scripture body: default and maximum `36pt`, left aligned, uniform within a passage, with no text shadow. Use the formal scripture grid in `pccs-service-pptx`. Prefer pagination at complete source lines; an explicitly required single page may use a documented smaller uniform size, never automatic shrinking.
- Continuation song name: right aligned `22pt` in the purple bar. Author/copyright text: right aligned `9pt` in that bar. Exact geometry is in `visual-style.md`.
- Do not switch lyric body sizes between slides.
- Never use automatic font shrinking. Select scripture exceptions explicitly and verify them by rendering.
- Do not trust slide-plan declarations or inherited template styles as proof of lyric sizing. Inspect the actual rendered runs in the final PPTX: every non-empty lyric run must resolve to `KaiTi` at exactly `40pt`. An inherited `44pt` or `48pt` lyric run fails this profile even when `body_font_pt` says `40`.
- Preserve template text colors in template-faithful mode. In refined mode, use the element-specific fills and text shadows from `visual-style.md`; apply text shadow to the font, not to the text-box shape.

## Content Layout

- Put lyrics in the upper half of the full slide (`y<=202.5pt`), with a balanced title/body relationship. Scripture can use the upper-middle area to preserve complete readable paragraphs.
- Use at most three lyric lines per slide. This limit does not apply to an explicitly requested scripture slide.
- Keep each logical line as one paragraph and disable unwanted automatic wrapping.
- Remove lyric punctuation; retain single spaces between lyric phrases.
- When a score or lyric image is available, treat complete musical phrases, breath points, rests, and cadences as the primary pagination boundaries. Prefer two lyric lines per slide when that follows the musical phrase and improves breathing; use three only when the phrase structure still reads naturally and every actual rendered run remains `40pt`. One-line pages are allowed for a meaningful ending or when combining would harm legibility.
- Keep repeated instances of the same section on the same phrase-based pagination unless the verified performance changes the phrasing.
- If a 40pt line does not fit, split at a semantic phrase boundary. Do not reduce the font.
- Song title, lyric body, logo, and church identity must not overlap or leave their intended bounds.

For fixed-line scripture, every canonical `source_lines` item becomes exactly one PowerPoint paragraph. Do not merge, split, reorder, paraphrase, or silently re-punctuate it. The mixed-deck validator checks this fixed-line contract. Continuous scripture supplied without fixed breaks belongs to the service skill's paragraph/wrapping workflow. If `single_slide: true`, adjust scripture geometry and choose a smaller uniform size at or below `36pt`; report a genuine capacity conflict instead of silently abandoning legibility.

Keep raw scripture input separately when normalizing verse markers. Verify chapter/verse boundaries against the selected edition, record the source and every correction, and move verified numbers to editable gutter text without changing the passage wording. The canonical body and marker mapping must reconstruct the source.

## Import and Export Preservation

Inspect the exported package and a native PowerPoint render before accepting a library round trip. If custom-layout images or identity elements disappear, repair the template relationships or transplant only the intended editable text/geometry changes into a preserved template copy. Do not rebuild unrelated slides. Re-run native rendering and duplication checks on the repaired candidate.

## Slide Sequence

Follow the user's requested service order, including scripture and communion transitions. For each song, use the complete expanded arrangement from `complete_lyrics.md`; never regenerate repetitions from memory while writing slides.

Store a machine-readable slide plan before PPT generation. Each song page should include `song_id`, `section_code`, and `performance_index` so the validator can reconstruct the performance order.

For consecutive one-line ending repetitions that share one page, replace `performance_index` with consecutive `performance_indexes`. Repeat the visible End lyric once per covered performance; `End*2` therefore appears as two identical lines on one page, not two one-line pages.
