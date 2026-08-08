# Artifact Schemas

All JSON is UTF-8, uses absolute seconds, and is written under the current run directory unless it is the formal SRT.

## context.json

```json
{
  "language": "zh-Hans",
  "deity_pronoun_style": "祢/祂",
  "deity_pronoun_exceptions": [
    {
      "cue_id": "cue-0123",
      "text": "主耶稣告诉你要彼此相爱。",
      "reason": "这里的“你”指听众，不是指神。"
    }
  ],
  "sermon_title": "本讲题目",
  "speaker": "讲员姓名",
  "scripture": ["经卷章:节-节"],
  "scripture_version": "PPT wording; version not labeled",
  "sermon_points": ["第一分点", "第二分点"],
  "proper_names": ["本讲圣经人物", "本讲历史人物"],
  "church_terms": ["本讲出现的教会名称或缩写"],
  "hotwords": ["容易误识别但本讲会出现的词"],
  "required_terms": ["最终字幕必须正确出现的词"],
  "forbidden_terms": ["已确认的本讲 ASR 或口音错误写法"],
  "protected_terms": ["换行时不得拆开的词"],
  "prompt_prefix": "这是一篇华语基督教讲道。"
}
```

`required_terms` and `forbidden_terms` are generated after full review. A common word is not forbidden merely because it was wrong once.

`deity_pronoun_style` is fixed to `祢/祂` for final display. `deity_pronoun_exceptions` contains current-sermon, exact-cue audit records for validator candidates whose ordinary `你/他` genuinely refers to a human. Each exception must match the current cue id and full cue text and contain a specific semantic reason; it is not a replacement map.

## regional_review.json

```json
{
  "regions": [
    {
      "id": "region-001",
      "start": 600.0,
      "end": 645.0,
      "reason": "两路全文转写在直接读经处均出现 VAD 漏段。",
      "evidence": ["primary gap", "precision disagreement", "PPT scripture page"]
    }
  ]
}
```

Times are absolute on the specified video. `end` must be later than `start`; regions are selected by evidence, not copied from a previous sermon.

## scripture_reference.json

```json
{
  "passage": "经卷章:节-节",
  "source": "PPT wording; version not labeled",
  "entries": [
    {
      "reference": "经卷章:节",
      "text": "牧师直接读出的该节规范文字。",
      "spoken": true,
      "evidence": "PPT page and original video interval"
    },
    {
      "reference": "经卷章:下一节",
      "text": "PPT 中存在但没有读出的文字。",
      "spoken": false,
      "evidence": "reading ends before this verse"
    }
  ]
}
```

Every cue `reference` must exactly match an entry key. Do not merge paraphrase or exposition into direct-reading entries.

For `spoken: true` entries, use the same reviewed `祢/祂` display style as the corresponding cues and SRT. Preserve the source/version label even when this display convention differs from the printed source's pronoun glyph.

## reviewed_cues.json

```json
{
  "video_duration": 2700.0,
  "language": "zh-Hans",
  "method": "AI full-sermon semantic review of dual full ASR, regional ASR, PPT, and scripture evidence",
  "cues": [
    {
      "id": "cue-0001",
      "start": 0.8,
      "end": 3.6,
      "text": "按实际发言定稿的简体中文字幕。",
      "source_segment_ids": [0],
      "alignment_group": "primary-segment-0",
      "source": "ai_semantic_review",
      "confidence": "high",
      "reason": "两路 ASR 一致，并按可听停顿切句。"
    },
    {
      "id": "cue-0090",
      "start": 600.0,
      "end": 605.2,
      "text": "按实际读经范围校正的文字。",
      "alignment_window": [598.0, 607.0],
      "alignment_group": "scripture-reading-01",
      "source": "ppt_scripture_verified",
      "confidence": "medium",
      "reason": "全文 VAD 漏段；使用区域词级证据和 PPT 文字。",
      "reference": "经卷章:节",
      "boundary_role": "scripture_start"
    }
  ]
}
```

Each cue requires either nonempty `source_segment_ids` or an `alignment_window`. Cues split from the same primary segment share an alignment group. Accepted confidence values are `high`, `medium`, and `low`. `boundary_role` may be `scripture_start`, `scripture_end`, `prayer_start`, or `prayer_end` when applicable.

## boundary_reviews.json

```json
{
  "reviews": [
    {
      "cue_id": "cue-0090",
      "reason": "起点相对初稿移动 1.42 秒，且该条是读经起点。",
      "evidence": "复听原视频；首个可听词与 precision/regional 的 600.240 秒词首一致。",
      "listened_window": [594.0, 611.0],
      "decision": "采用 600.240 秒词首；文字按 PPT 中实际读出的范围。",
      "start": 600.24
    }
  ]
}
```

`cue_id`, `reason`, `evidence`, and a valid two-number `listened_window` are mandatory. `start`, `end`, and `text` are optional reviewed overrides. Do not add an override when automatic alignment is already correct; the review record can document acceptance without those fields.

## Alignment and validation reports

The alignment command writes final cues, per-group timing source, alternative ratios, source windows, risks, observed boundaries, manual audit, and overlap adjustments. The validator consumes that report and writes:

```json
{
  "status": "PASS",
  "subtitle": "absolute path",
  "subtitle_sha256": "64 hexadecimal characters",
  "video_duration": 2700.0,
  "cue_count": 600,
  "first_start": 0.8,
  "last_end": 2697.4,
  "hard_failures": 0,
  "hard_errors": [],
  "missing_boundary_reviews": [],
  "deity_pronoun_candidates": [],
  "missing_deity_pronoun_reviews": [],
  "checks": []
}
```

Only `PASS`, `REVIEW_REQUIRED`, and `FAIL` are valid delivery states.
