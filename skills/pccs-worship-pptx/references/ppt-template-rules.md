# PPT Template Rules

## Required Tooling

Use the **Presentations** skill for template inspection, PPTX modification, rendering, and validation. Load the workspace presentation dependencies before editing. Follow its render-and-verify workflow and use native editable shapes and text.

## Template Selection

1. If the user supplies a non-empty `template_pptx`, use that file.
2. Otherwise use `<skill-dir>/assets/pccsworship.pptx`.

Resolve the bundled path from the skill directory, not from the current working directory. Copy the selected template into the project workspace and edit the copy. Never overwrite the bundled asset.

## Inspect Before Editing

Inspect the complete selected template, including slide size, all template slides, masters, layouts, placeholders, background inheritance, theme colors, fonts, logo/church identity shapes, and text-box geometry. Do not assume slide 1 and slide 2 are interchangeable.

Use the template's first-song page for the first page of each song and its continuation style for later lyric pages. Preserve the current template's title color and continuation-page song-name color exactly.

## Template Integrity

- Keep background, PCCS logo, and church name as native template/master/layout content where possible.
- Do not replace editable lyrics with screenshots.
- Do not flatten the whole slide into a background image.
- If copying a slide loses its background or church identity, repair the master/layout relationship before generating the deck.
- If native inheritance cannot be repaired reliably, use self-contained editable/template shapes as a documented fallback and verify duplication again.

## Typography

- Set every editable Chinese run to `KaiTi` in both `Name` and `NameFarEast`.
- First page of each song: centered song title at exactly `54pt`.
- Lyric body: exactly `48pt`.
- Scripture body: default `48pt`. If the user explicitly requires one scripture slide, or one intact source line cannot fit at `48pt`, choose the largest fitting scripture size and record the exception. This exception never changes lyric sizing.
- Continuation-page song-name size, weight, and position come from the template unless the user supplies a newer rule.
- Do not switch lyric body sizes between slides.
- Never use automatic font shrinking. Select scripture exceptions explicitly and verify them by rendering.

## Content Layout

- Put lyric/scripture content in the upper safe area so heads in the front rows do not block it.
- Use at most three lyric lines per slide. This limit does not apply to an explicitly requested scripture slide.
- Keep each logical line as one paragraph and disable unwanted automatic wrapping.
- Remove lyric punctuation; retain single spaces between lyric phrases.
- Prefer two or three balanced lines. One-line pages are allowed for a meaningful ending or when combining would harm legibility.
- If a 48pt line does not fit, split at a semantic phrase boundary. Do not reduce the font.
- Song title, lyric body, logo, and church identity must not overlap or leave their intended bounds.

For scripture, every canonical `source_lines` item must become exactly one PowerPoint paragraph. Do not merge, split, reorder, paraphrase, or silently re-punctuate source lines. Disable automatic wrapping; pagination may occur only between complete source lines. If `single_slide: true`, place all source lines on that one slide and fit them by adjusting scripture-specific geometry and then the scripture font size, never by changing the lines.

## Slide Sequence

Follow the user's requested service order, including scripture and communion transitions. For each song, use the complete expanded arrangement from `complete_lyrics.md`; never regenerate repetitions from memory while writing slides.

Store a machine-readable slide plan before PPT generation. Each song page should include `song_id`, `section_code`, and `performance_index` so the validator can reconstruct the performance order.

For consecutive one-line ending repetitions that share one page, replace `performance_index` with consecutive `performance_indexes`. Repeat the visible End lyric once per covered performance; `End*2` therefore appears as two identical lines on one page, not two one-line pages.
