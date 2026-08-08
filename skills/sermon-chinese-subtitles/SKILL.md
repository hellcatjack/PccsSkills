---
name: sermon-chinese-subtitles
description: Use when creating, correcting, retiming, or validating Simplified-Chinese SRT subtitles for an explicitly specified sermon video, especially when Hong Kong-accented Mandarin, Bible quotations, proper names, VAD omissions, or inaccurate subtitle timelines require complete word-level ASR, regional re-transcription, semantic review, and auditable boundary evidence.
---

# Sermon High-Precision Chinese Subtitles

Create YouTube-ready Simplified-Chinese subtitles whose wording and timing are independently defensible. Formatting success is not timing proof: a structurally valid SRT can still be seconds early or late.

## Non-negotiable rules

- Start from one explicitly specified sermon video. If more than one video or audio track is plausible, resolve it from context or stop; never guess.
- Treat the video, selected audio track, PPTX, optional alignment audio, and prior subtitles as read-only. Record SHA-256 before work and compare it again before delivery.
- Never cut, concatenate, time-stretch, offset, replace, or silence-strip the source audio. Regional ASR reads absolute time windows from the full selected track.
- Run two complete full-sermon Faster-Whisper passes with word timestamps before semantic authorship. Excerpts are additional evidence, not a substitute.
- Read both complete transcripts from beginning to end and read the available PPT. Do not turn raw ASR or a correction table directly into final subtitles.
- Correct Hong Kong accent errors, Bible names, historical names, and church terms from the current sermon's context. Never reuse a previous sermon's global replacement map.
- During semantic review, use `祢` for singular direct address to God and `祂` for singular third-person reference to God. Preserve human `你、他、你们、他们`, reject `祢们、祂们`, and never apply a global pronoun replacement; ambiguous antecedents require full-context review and an auditable exception when the ordinary pronoun is intentional.
- For direct scripture reading, use reliable PPT/Bible wording only for the range actually spoken. Do not add an unspoken verse because a cover or passage range includes it. Preserve paraphrase and exposition as the pastor said them.
- Require a listening review for alignment ratio below 0.65, any start or end shift over 1.0 second, scripture span boundaries, opening/final cues, prayer boundaries, and every overlap repair.
- A missing review is `REVIEW_REQUIRED`, not `PASS`. Do not call the subtitle complete while review evidence is absent.
- The formal filename ends with `_YouTube简体中文字幕_高精度校订版.srt`. Never overwrite an existing formal subtitle; allocate `_v2`, `_v3`, and so on.
- Keep processing local. Do not upload sermon media or buy a transcription service. Model-weight download is separate from media upload and requires an explicit local setup decision.

## Required references

Read these before production work:

1. [workflow-contract.md](references/workflow-contract.md) for exact phases, commands, output locations, and rerun behavior.
2. [artifact-schemas.md](references/artifact-schemas.md) before authoring context, regional-review, scripture, cue, or boundary-review JSON.
3. [semantic-review-policy.md](references/semantic-review-policy.md) before correcting wording or choosing regional ASR windows.
4. [verification-contract.md](references/verification-contract.md) before rendering or claiming delivery.

## Workflow

### 1. Freeze the specified media

Inventory the video's streams and any user-specified PPTX. If a PPTX is used, first follow the available Presentations Skill to read its complete text, notes, and metadata. Then run:

```powershell
$subtitleSkill = ".\.agents\skills\sermon-chinese-subtitles"
$subtitlePython = ".\.subtitle-skill-venv\Scripts\python.exe"
& "$subtitleSkill\scripts\bootstrap.ps1"
& $subtitlePython "$subtitleSkill\scripts\sermon_subtitles.py" prepare "<absolute-video-path>" --pptx "<absolute-pptx-path>"
```

Pass `--audio-stream <zero-based-ordinal>` when the video has multiple audio tracks. The command prints `source_manifest.json`; use its run directory for all work artifacts. Do not edit the source media.

### 2. Build current-sermon context

Create `context.json` from the PPT and user-provided facts. Include the title, speaker, actual passage, sermon points, proper names, church terms, prompt hotwords, protected display terms, and current-sermon required/forbidden spellings. Follow [artifact-schemas.md](references/artifact-schemas.md). Do not copy another sermon's name list.

### 3. Run full dual ASR

Use the same manifest and context for both complete passes:

```powershell
& $subtitlePython "$subtitleSkill\scripts\sermon_subtitles.py" transcribe "<manifest>" --pass primary --context "<context.json>" --model-dir "<local-model-cache>"
& $subtitlePython "$subtitleSkill\scripts\sermon_subtitles.py" transcribe "<manifest>" --pass precision --context "<context.json>" --model-dir "<local-model-cache>"
```

The primary profile favors stable context; the precision profile uses shorter VAD segments for boundary evidence. GPU may fall back to CPU. Default model loading is local-only; if the model is absent, stop and report it rather than uploading media.

### 4. Review the entire sermon and run regional evidence passes

Read both `.txt` and word-level JSON files fully. Mark VAD omissions, two-pass disagreement, low word probability, dense scripture/proper names, implausible pauses, and uncertain openings/endings in `regional_review.json`. Run only those absolute windows with VAD disabled:

```powershell
& $subtitlePython "$subtitleSkill\scripts\sermon_subtitles.py" transcribe "<manifest>" --pass regional --context "<context.json>" --regions "<regional_review.json>" --model-dir "<local-model-cache>"
```

Use [semantic-review-policy.md](references/semantic-review-policy.md) to decide wording. Regional output is evidence; AI semantic judgment remains mandatory.

### 5. Author reviewed cues and scripture evidence

Write `scripture_reference.json` for the direct reading/quotation actually heard. Write `reviewed_cues.json` for the whole sermon with stable cue ids, semantic reasons, primary source segment ids or explicit alignment windows, alignment groups, confidence, references, and prayer boundary roles. Segment by spoken meaning and audible pauses; never split solely by character count.

### 6. Align to observed word boundaries

Run alignment against every available source:

```powershell
& $subtitlePython "$subtitleSkill\scripts\sermon_subtitles.py" align "<reviewed_cues.json>" `
  --asr "primary=<asr_primary.json>" `
  --asr "precision=<asr_precision.json>" `
  --asr "regional=<regional_asr.json>" `
  --output "<aligned_cues.json>" `
  --report "<alignment_report.json>"
```

Inspect every risk in the alignment report. Listen to the original video around each risk and write `boundary_reviews.json`. If an independently observed override is needed, include the new start/end and rerun alignment to new filenames with `--manual-reviews`; never overwrite the first alignment evidence.

### 7. Render, compare, and validate

Render only after all risk decisions are documented:

```powershell
& $subtitlePython "$subtitleSkill\scripts\sermon_subtitles.py" render "<final-aligned-cues.json>" --context "<context.json>" --manifest "<manifest>"
```

If an earlier SRT exists, quantify the revision:

```powershell
& $subtitlePython "$subtitleSkill\scripts\sermon_subtitles.py" compare "<earlier.srt>" "<candidate.srt>" --report "<comparison_report.json>"
```

Run the mandatory validator:

```powershell
& $subtitlePython "$subtitleSkill\scripts\sermon_subtitles.py" validate `
  --srt "<candidate.srt>" `
  --cues "<final-aligned-cues.json>" `
  --alignment-report "<final-alignment-report.json>" `
  --boundary-reviews "<boundary_reviews.json>" `
  --context "<context.json>" `
  --video "<absolute-video-path>" `
  --manifest "<manifest>" `
  --scripture-reference "<scripture_reference.json>" `
  --report "<validation_report.json>"
```

Exit code 0 means `PASS`, 2 means `REVIEW_REQUIRED`, and 1 means `FAIL`. Fix the evidence or subtitle and rerun; do not lower thresholds.

## Judgment boundaries

- Prefer faithful spoken wording over polished prose. Remove recognition noise, not the pastor's theology, tone, or meaningful repetition.
- Keep the deliverable in Simplified Chinese while treating `祢/祂` as intentional divine-honorific display characters. Apply the same display form to reviewed cues, rendered SRT text, and spoken entries in `scripture_reference.json`.
- Treat direct scripture, paraphrase, exposition, and accidental misstatement as different cases; [semantic-review-policy.md](references/semantic-review-policy.md) defines the correction boundary.
- A higher lexical alignment score cannot override a wrong semantic window.
- Do not extend a cue to hide bad segmentation. Short exact-word cues may be under one second; the next sentence must not appear before it is spoken.
- Use diagnostic snippets only for review if necessary; they remain work artifacts and never become a timing origin or delivery audio.

## Delivery

Report the final SRT absolute path, corresponding video, Simplified-Chinese language, cue count, first/last timestamp, primary/precision/regional ASR use, number of risk reviews, validator status, and SRT SHA-256. Do not claim completion unless the fresh report is `PASS` and all immutable hashes match.
