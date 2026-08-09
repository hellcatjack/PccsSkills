# Lyrics Pipeline

## Source Priority

Use this decision priority:

1. User corrections and explicit performance arrangement.
2. Semantically reviewed lyric-image transcription.
3. Official lyrics or a verified video's description/captions.
4. Clearly readable video lyric frames.
5. Audio listening, ASR, or secondary lyric pages.

Lower-priority evidence may repair missing or obviously wrong characters, but every change needs an audit entry.

## Build Section Definitions

Create canonical sections such as `V`, `V1`, `V2`, `C`, `C1`, `C2`, `B`, and `End`. Preserve meaningful phrase boundaries and spaces. Resolve repeat signs, first/second endings, and cross-line carry-over words before expanding the performance order.

Example of a carry-over error: two characters printed near the end of C1 may fill the beginning of C2. Assign them by complete sentence meaning and repeat structure, not nearest OCR coordinates.

## Expand the Arrangement

Fully expand all repeats:

```text
Input:  V C End*2
Output: V C End End
```

Never use `同上`, `再唱`, `副歌重复`, or `End*2` in the complete expansion. If one section spans multiple slides, give those slides the same `performance_index`; increment the index only when the next performed section begins.

### Group repeated endings in the slide plan

The complete lyrics must still write every performance separately, but consecutive one-line End repetitions should share one slide when they fit the three-line limit:

```text
Arrangement input:     V C End*2
Complete expansion:    V C End End
Visible ending slide:  [ending line, ending line]
Slide metadata:        performance_indexes: [3, 4]
```

Use `performance_indexes` only for consecutive occurrences of the same `End` section. Do not also set `performance_index` on that page. The number of identical visible ending lines must equal the number of grouped indexes. For `End*3`, place three identical one-line endings on one page. If one End occurrence contains multiple lines or grouping would exceed three lines, use the fewest pages that preserve complete End instances. An explicit user request for separate ending pages overrides this default.

Performance annotations such as `跳音`, `轻唱`, `渐强`, or `男女轮唱` are not lyrics. Preserve them in project/audit notes and do not put them in visible lyric text unless explicitly requested.

## Normalize Text

- Convert Chinese lyrics to simplified Chinese.
- Replace references to God with respectful `祢` and `祂`; do not change pronouns referring to people.
- Preserve song-specific proper names and intentional non-Chinese words such as `Hi-Ne-Ni`.
- Remove lyric punctuation only for final PPT lines.
- Use single spaces to divide phrases; do not create repeated spaces.
- Do not cut a semantic phrase merely to fill a slide.

## Preserve Scripture Lines

Scripture supplied explicitly in a TXT or guide file is not processed like lyrics. Capture the source as ordered `source_lines` before pagination. Keep every source line intact and in the same position; do not merge short lines, split long lines, reorder phrases, or remove punctuation for visual balance.

Explicit project-wide character policies may be applied within a line, but they must be audited and must not change line boundaries. Carry the canonical `source_lines` unchanged into the slide plan. If multiple scripture pages are allowed, split only between array items. If `single_slide: true`, keep every item on one slide and solve fit through scripture-specific layout or font sizing.

## Create `lyrics_audit.md`

This file must exist before `complete_lyrics.md` or PPT generation. For each song record:

```markdown
## Song title

- User arrangement:
- Expanded arrangement:
- Baseline source:
- Reference recording and match confidence:
- Sources actually accessed:

| Location | Baseline | Evidence | Final | Reason | Status |
|---|---|---|---|---|---|

### Repeat and carry-over review
### Unresolved items
### Rejected ASR or link noise
```

Write `未发现需要修正的问题` when no differences exist. Do not silently omit an audit section.

## Create `complete_lyrics.md`

Generate it only from accepted audit decisions. Include both canonical section definitions and the fully expanded performance sequence. Write every performed instance in order; do not refer back to a previous instance.

Before slide generation, verify that every expanded instance maps to exactly one canonical section and exactly one slide-plan index. A page may cover several consecutive End instances through `performance_indexes`. No audit item may remain unresolved without explicit user acceptance.

## Correction Backflow

If rendering or rehearsal reveals a lyric error, correct the audit decision first, regenerate `complete_lyrics.md`, regenerate slide data, and then regenerate the PPTX. Never patch only the visible slide while leaving the source documents inconsistent.
