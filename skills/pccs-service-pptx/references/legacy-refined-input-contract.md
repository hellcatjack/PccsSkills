# Input Contract

## Purpose

Use one structured project input for covers, announcements, scripture, welcome, QR, prayer, baptism, communion, offering, doxology, and other non-lyric service pages.

## Recommended YAML

```yaml
project:
  project_id: pccs-service_YYYY-MM-DD
  service_date: YYYY-MM-DD
  language: 简体中文
  template_pptx: ""
  background_size_pixels: 1920x920
  background_geometry_points: [0, 0, 720, 345]

slides:
  - index: 1
    type: cover
    title: 主日崇拜
    body_lines:
      - 匹兹堡南区基督教会
    asset_files: []
    background_direction: 明亮圣所晨光
    background_reuse_group: cover

  - index: 2
    type: scripture
    scripture_id: reading-1
    title: 诗篇100篇
    source_lines:
      - 普天下当向耶和华欢呼
      - 你们当乐意侍奉耶和华
    preserve_source_lines: true
    source_lines_fixed: true
    body_font: SimSun
    body_font_pt: 36
    alignment: left
    body_shadow: false
    single_slide: true
    background_direction: 宣读经文的安静圣所

  - index: 3
    type: qr
    title: 线上周报
    asset_files:
      - bulletin-qr.png
    background_direction: 明亮纸张与窗影

deliverables:
  output_pptx: PCCS主日流程.pptx
  powerpoint_duplicate_test: true
```

## Allowed Slide Types

`cover`, `announcement`, `scripture`, `welcome`, `qr`, `form`, `photo`, `prayer`, `baptism`, `communion`, `offering`, `doxology`, `transition`, `closing`.

`lyrics` is intentionally invalid. Route worship-song lyric pages to `pccs-worship-pptx`.

## Common Fields

- `index`: required consecutive integer beginning at 1.
- `final_slide_index`: optional positive integer locating this service page in a combined deck. Keep `index` locally consecutive within this non-lyric input; omitted `final_slide_index` means the same value as `index`. Effective final indexes must be unique. The PowerPoint QA checks that each is within the opened deck and every declared page is consumed; it does not require records for intervening lyric pages.
- `type`: required allowed slide type.
- `title`: optional exact visible title.
- `body_lines`: optional ordered visible paragraphs.
- `asset_files`: uploaded or local authentic images used by the page.
- `background_direction`: semantic visual direction, not a request for visible explanatory text.
- `background_reuse_group`: reuse a background only when several pages share the same subject and visual role.
- `background_actual_size_pixels`: optional measured `[width, height]` for this page's asset; may also appear under `project` for a shared background.
- `background_size_audit`: required when measured pixels differ from `[1920, 920]`. Record the actual tool output and full-image placement. The validator permits relative `48:23` ratio error of at most `0.1%`; placement remains exactly `0,0,720,345` with no crop.
- `speaker_notes`: optional exact notes.

## Scripture Fields

- `source_lines`: required non-empty ordered array.
- `preserve_source_lines`: must be `true`.
- `single_slide`: set `true` when all lines must remain on one page.
- `scripture_id`: stable passage id, shared by all its pages. Always include it when paginating a passage so the validator can check uniform body typography.
- `source_lines_fixed`: defaults to `true`. Set `false` only for continuous input whose physical line breaks were not fixed by the user.
- `allow_visual_wrap`: defaults to the inverse of `source_lines_fixed`; cannot be `true` for fixed lines. Visual wrapping never changes the actual text or source record order.
- `body_font`: defaults to `SimSun`; `body_font_pt`: defaults to `36`, normally positive and at most `36`; `alignment`: defaults to `left`; `body_shadow`: defaults to `false`. The same `scripture_id` must use uniform body typography across all pages. Explicit smaller sizes are valid and require render review for readability.
- `style_override_reason`: optional non-empty record of an explicit user typography or template-style instruction. Only that instruction permits departures from the default font, alignment, size cap or shadow policy; the field is not authorization invented by the agent. Same-passage uniformity still applies.
- Name the single editable body text box `PCCS scripture body` or retain the compatible existing name `Scripture body` when using the optional final body checker in `qa_pccs_service_pptx.ps1 -ProjectJson PROJECT.json`. The checker maps each record through `final_slide_index` when present, otherwise its local `index`; input validation alone is not proof of the final typography. `Scripture title` is also an acceptable existing title name; no rename is needed.

Physical line breaks supplied by the user are canonical. Pagination is allowed only between complete `source_lines`, unless `single_slide` is true.

In a mixed deck, for example, two non-lyric records can keep `index: 1` and `index: 2` while declaring `final_slide_index: 7` and `final_slide_index: 32`. Keep lyric records out of this input. Structural/layout/duplication checks still cover the full opened deck, while `-ProjectJson` checks only these declared service pages.

For verified verse-number separation, add these parallel arrays to the scripture page:

```yaml
raw_source_lines: ["1　普天下当向耶和华欢呼。"]
verse_prefixes: ["1　"]
verse_numbers: ["1"]
source_lines: ["普天下当向耶和华欢呼。"]
translation: 按本项目已核实的译本填写
verse_boundaries_verified: true
verse_metadata_audit: 按已核实译本确认节界；原节号和全角空格保存在前缀中
```

The arrays have equal lengths. `verse_prefixes[i] + source_lines[i]` must reconstruct `raw_source_lines[i]` exactly; no trim, pronoun replacement, punctuation change or source-order change is allowed. `verse_numbers` may contain an empty string for a continuation line. A metadata number added to an originally unnumbered line requires a verified translation boundary, an empty prefix, and a recorded explanation. Keep the full canonical reading in the content audit so concatenated pages can be checked against it.

## Asset Fields

`qr`, `form`, and `photo` pages require at least one `asset_files` entry. Use the actual file; do not generate a lookalike.

## Fixed Geometry

- Slide: `720x405pt`.
- Visual background above footer: `0,0,720,345pt`.
- Background asset: `1920x920px`, ratio `48:23`.
- Footer: native template content from `y=345pt` through `405pt`.
