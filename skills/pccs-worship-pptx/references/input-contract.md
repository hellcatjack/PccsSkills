# Project Input Contract

Normalize free-form chat, uploaded files, or YAML into a project object before lyric work. Preserve the user's wording in notes, but use the normalized fields below for validation and generation.

## Required Project Fields

```json
{
  "project": {
    "project_id": "pccs_2026-08-09",
    "service_date": "2026-08-09",
    "template_pptx": "pccsworship.pptx",
    "language": "简体中文",
    "font": "KaiTi",
    "title_font_pt": 54,
    "body_font_pt": 48,
    "max_lines": 3,
    "pronoun_policy": "祢/祂"
  },
  "songs": []
}
```

Require a non-empty `template_pptx`, at least one song, and either `project_id` or `service_date`.

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
- Preserve the number, order, and boundaries of those lines. Only an explicitly required project-wide text policy may change characters within a line; record such changes in the audit and never move text across a line boundary.
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
  "font": "KaiTi",
  "body_font_pt": 48
}
```

Across all pages for one `scripture_id`, concatenated `lines` must equal `source_lines` exactly. This permits pagination only between source lines and prevents merging, splitting, or reordering.

## Compact Chat Input

Accept this style without requiring the user to rewrite it as YAML:

```text
模板：pccsworship.pptx
日期：2026-08-09
1 这里有荣耀 G调
顺序：V V C1 C2 V C1 C2 C1 C2 End*2
图片：无
来源：https://www.youtube.com/channel/...
备注：C2跳音只是演唱方式
```

Normalize it, show only material ambiguities, and continue without asking for fields that can be inferred safely.
