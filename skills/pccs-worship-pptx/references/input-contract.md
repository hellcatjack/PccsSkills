# Project Input Contract

Normalize free-form chat, uploaded files, or YAML into a project object before lyric work. Preserve the user's wording in notes, but use the normalized fields below for validation and generation.

## Project Fields

```json
{
  "project": {
    "project_id": "pccs_2026-08-09",
    "service_date": "2026-08-09",
    "template_pptx": "",
    "language": "简体中文",
    "font": "KaiTi",
    "title_font_pt": 44,
    "body_font_pt": 40,
    "max_lines": 3,
    "pronoun_policy": "祢/祂"
  },
  "songs": []
}
```

Require at least one song and either `project_id` or `service_date`. `template_pptx` is optional:

- A non-empty value selects the user-supplied template and overrides the skill default.
- A missing, empty, or whitespace-only value selects `assets/pccsworship.pptx` from the installed skill directory.
- Resolve the default relative to `SKILL.md`, not the current working directory or project root.
- Copy the selected template to the project workspace before editing; never modify the bundled asset in place.

## Song Fields

```json
{
  "index": 1,
  "title": "这里有荣耀",
  "key": "G",
  "source_mode": "auto",
  "image_files": ["01_这里有荣耀.png"],
  "youtube_urls": ["https://www.youtube.com/watch?v=..."],
  "youtube_search_hint": "这里有荣耀 赞美之泉",
  "official_lyrics_url": "",
  "credit_lines": ["词曲：作者", "© 出版方 版权所有"],
  "permission_source_url": "",
  "audio_files": [],
  "arrangement": "V V C1 C2 V C1 C2 C1 C2 End*2",
  "special_notes": ["C2跳音仅表示演唱方式"]
}
```

`source_mode` accepts `auto`, `images`, `youtube`, or `youtube_search`:

- `auto`: choose from available images, URLs, audio, and search hints.
- `images`: lyric images are the baseline; a YouTube source may verify them.
- `youtube`: one or more direct video, playlist, or channel URLs are supplied.
- `youtube_search`: resolve a concrete recording from the title and search hint.

At least one source must exist per song: an image, YouTube URL, audio file, official lyrics URL, or search hint. An empty `arrangement` is allowed; it means use the verified video's actual performance order and record that decision in the audit.

`credit_lines` contains the exact visible author/copyright text, separate from canonical lyrics. Copy it to each corresponding song record in `SLIDES.json`; every song page uses these lines in the bottom purple bar. A page-level `credit_lines` can specify an explicitly audited variant. `permission_source_url` records the actual publisher permission or license evidence when used. Do not invent an author or infer permission solely from nonprofit use.

A supplied `credit_lines` must be a non-empty array of nonblank strings; an empty value cannot disable credit checking. Omit the field only when no visible attribution is applicable and record that source decision in the audit.

## Explicit Song Size Overrides

The default is 40pt lyrics and 44pt first-song titles. If the user explicitly requests other song sizes, record the request in the audit and add this top-level object to `SLIDES.json`:

```json
{
  "typography": {
    "lyric_font_pt": 42,
    "title_font_pt": 46,
    "override_reason": "User explicitly requested these sizes"
  }
}
```

Both slide-plan and final-PPTX validators use these values. Copy the active sizes into the page fields too; every page must match. Do not alter validator source code or invent an override reason to make overflow pass. Recalculate geometry and inspect the composition. This override changes only the two song sizes; the formal-scripture ceiling, footer placement, and other invariants remain unchanged.

## Optional Service Content

```json
{
  "scripture": [
    {
      "id": "scripture-1",
      "position": "before_song_2",
      "reference": "诗篇 62:5-8",
      "source_file": "guide.txt",
      "source_lines": [
        "我的心哪，你当默默无声，专等候神，",
        "因为我的盼望是从他而来。"
      ],
      "preserve_line_breaks": true,
      "single_slide": true
    }
  ],
  "deliverables": {
    "output_pptx": true,
    "complete_lyrics_md": true,
    "lyrics_audit_md": true,
    "source_summary": true,
    "powerpoint_duplicate_test": true
  }
}
```

When the request explicitly includes scripture, normalize it into `source_lines` before slide planning:

- For a TXT or guide file, read each physical scripture line in order. Do not replace the array with one continuous `text` string.
- Preserve the number, order, and boundaries of those lines. Scripture-specific user corrections may change characters within a line; record them in the audit. Song pronoun and punctuation policies do not authorize changing a scripture quotation.
- Keep scripture punctuation and intentional spacing. Lyric punctuation removal applies only to song lyrics.
- Set `single_slide: true` only when the user explicitly requires the whole passage on one slide.
- Copy the same scripture records into the slide plan's top-level `scriptures` array. Every scripture page must reference one record through `scripture_id`.

Example slide-plan page:

```json
{
  "role": "scripture",
  "scripture_id": "scripture-1",
  "lines": [
    "我的心哪，你当默默无声，专等候神，",
    "因为我的盼望是从他而来。"
  ],
  "font": "SimSun",
  "body_font_pt": 36,
  "alignment": "left"
}
```

Across all pages for one `scripture_id`, concatenated `lines` must equal `source_lines` exactly. This permits pagination only between source lines and prevents merging, splitting, or reordering.

Keep one scripture body size through each passage, at most `36pt`. When verse numbers are separated into a gutter, use parallel `raw_source_lines`, `verse_prefixes`, and `verse_numbers` arrays on the source record and copy the relevant slices to each page. Empty strings mark lines without a number. For each item, `verse_prefixes[i] + source_lines[i]` must reconstruct the raw line exactly. Record `translation`, `verse_boundaries_verified: true`, and a nonempty `verse_metadata_audit` documenting the source and any corrected placement. Final pages use `lines` for the canonical body; their `verse_numbers` must match editable gutter shapes named `Verse marker` or `Scripture verse marker`. Do not silently delete or relocate numbers.

Carry `position` into the top-level scripture record in the slide plan: `before_song_N` or `after_song_N`, where N is the one-based song order. The validator checks that all pages of the reading obey that anchor.

For continuous input without fixed line boundaries, use the service skill's paragraph workflow and copy `source_lines_fixed: false` and `allow_visual_wrap: true` to the mixed-deck page. The canonical paragraph text remains exact; only rendered wrapping is flexible. Fixed source lines cannot use this flag to hide overflow.

If a later explicit user instruction replaces the scripture style, carry the service skill's `style_override_reason` into every affected page along with the requested `font`, `body_font_pt`, and `alignment`. Both worship validators then check that declared style; preserve same-passage uniformity. A song-size override never changes scripture. Shadow, boldness, fixed spacing, and actual ink overflow still need native PowerPoint QA; the artifact layout export does not expose every native property reliably.

## Compact Chat Input

Accept this style without requiring the user to rewrite it as YAML:

```text
模板：可省略；省略时使用 skill 内置模板
日期：2026-08-09
1 这里有荣耀 G调
顺序：V V C1 C2 V C1 C2 C1 C2 End*2
图片：无
来源：https://www.youtube.com/channel/...
备注：C2跳音只是演唱方式
```

Normalize it, show only material ambiguities, and continue without asking for fields that can be inferred safely.
