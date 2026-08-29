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

- Set every editable Chinese run to `KaiTi` in both `Name` and `NameFarEast`.
- First page of each song: centered song title at exactly `54pt`.
- Lyric body: exactly `48pt`.
- Scripture body: default `48pt`. If the user explicitly requires one scripture slide, or one intact source line cannot fit at `48pt`, choose the largest fitting scripture size and record the exception. This exception never changes lyric sizing.
- Continuation-page song-name size, weight, and position come from the template unless the user supplies a newer rule.
- Do not switch lyric body sizes between slides.
- Never use automatic font shrinking. Select scripture exceptions explicitly and verify them by rendering.
- Do not trust slide-plan declarations or inherited template styles as proof of lyric sizing. Inspect the actual rendered runs in the final PPTX: every non-empty lyric run must resolve to `KaiTi` at exactly `48pt`. An inherited `44pt` run is a failure even when `body_font_pt` says `48`.
- Preserve template text colors in template-faithful mode. In refined mode, use the element-specific fills and text shadows from `visual-style.md`; apply text shadow to the font, not to the text-box shape.

## Content Layout

- Put lyric/scripture content in the upper safe area so heads in the front rows do not block it.
- Use at most three lyric lines per slide. This limit does not apply to an explicitly requested scripture slide.
- Keep each logical line as one paragraph and disable unwanted automatic wrapping.
- Remove lyric punctuation; retain single spaces between lyric phrases.
- When a score or lyric image is available, treat complete musical phrases, breath points, rests, and cadences as the primary pagination boundaries. Prefer two lyric lines per slide when that follows the musical phrase and improves breathing; use three only when the phrase structure still reads naturally and every actual rendered run remains `48pt`. One-line pages are allowed for a meaningful ending or when combining would harm legibility.
- Keep repeated instances of the same section on the same phrase-based pagination unless the verified performance changes the phrasing.
- If a 48pt line does not fit, split at a semantic phrase boundary. Do not reduce the font.
- Song title, lyric body, logo, and church identity must not overlap or leave their intended bounds.

For scripture, every canonical `source_lines` item must become exactly one PowerPoint paragraph. Do not merge, split, reorder, paraphrase, or silently re-punctuate source lines. Disable automatic wrapping; pagination may occur only between complete source lines. If `single_slide: true`, place all source lines on that one slide and fit them by adjusting scripture-specific geometry and then the scripture font size, never by changing the lines.

## Slide Sequence

Follow the user's requested service order, including scripture and communion transitions. For each song, use the complete expanded arrangement from `complete_lyrics.md`; never regenerate repetitions from memory while writing slides.

Store a machine-readable slide plan before PPT generation. Each song page should include `song_id`, `section_code`, and `performance_index` so the validator can reconstruct the performance order.

For consecutive one-line ending repetitions that share one page, replace `performance_index` with consecutive `performance_indexes`. Repeat the visible End lyric once per covered performance; `End*2` therefore appears as two identical lines on one page, not two one-line pages.
