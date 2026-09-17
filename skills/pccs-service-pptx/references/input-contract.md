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
  template_profile: wide-v3
  background_size_pixels: 1920x1080
  background_geometry_points: [0, 0, 960, 540]

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
    title: 诗篇100篇
    source_lines:
      - 普天下当向耶和华欢呼
      - 你们当乐意侍奉耶和华
    preserve_source_lines: true
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
- `type`: required allowed slide type.
- `title`: optional exact visible title.
- `body_lines`: optional ordered visible paragraphs.
- `asset_files`: uploaded or local authentic images used by the page.
- `background_direction`: semantic visual direction, not a request for visible explanatory text.
- `background_reuse_group`: reuse a background only when several pages share the same subject and visual role.
- `speaker_notes`: optional exact notes.

## Scripture Fields

- `source_lines`: required non-empty ordered array.
- `preserve_source_lines`: must be `true`.
- `single_slide`: set `true` when all lines must remain on one page.

Physical line breaks supplied by the user are canonical. Pagination is allowed only between complete `source_lines`, unless `single_slide` is true.

## Asset Fields

`qr`, `form`, and `photo` pages require at least one `asset_files` entry. Use the actual file; do not generate a lookalike.

## Template geometry

Current `wide-v3`:960×540pt, full16:9 background at0,0,960,540pt. Native imagegen dimensions within1% of16:9 are accepted; record actual dimensions, e.g.1672x941. The purple low footer and optional local cloud remain independent template objects.

Select `legacy` explicitly for720×405pt with1920x920 images at0,0,720,345. The validator interprets missing profile only in old saved inputs as legacy. New inputs always include template_profile.

A user-supplied template with different dimensions takes priority: inventory its actual geometry and adapt validation rather than changing the template to satisfy bundled constants. For background-only work use a source/target media inventory instead of inventing new content input.
