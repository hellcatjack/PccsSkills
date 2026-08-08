# Workflow Contract

## Purpose

This contract defines the reproducible mechanics around AI subtitle authorship. The scripts do not decide sermon meaning, scripture scope, or accent corrections.

## Dependencies and setup

- Windows PowerShell and Python 3.12.
- FFmpeg and FFprobe on `PATH`.
- Local Faster-Whisper `large-v3` weights for production ASR.
- The bootstrap creates `.subtitle-skill-venv` and installs Faster-Whisper 1.x. It installs no cloud SDK.

Run from the project root:

```powershell
$skill = ".\.agents\skills\sermon-chinese-subtitles"
& "$skill\scripts\bootstrap.ps1"
$python = ".\.subtitle-skill-venv\Scripts\python.exe"
$cli = "$skill\scripts\sermon_subtitles.py"
```

`--allow-model-download` permits the Faster-Whisper library to retrieve model weights; it never authorizes uploading sermon media. Do not use it when network/model-download authorization is absent.

## Phase 1: prepare

```powershell
& $python $cli prepare "C:\path\sermon.mp4" --pptx "C:\path\sermon.pptx"
```

Optional arguments:

- `--audio-stream N`: zero-based audio ordinal. Required when more than one audio stream exists.
- `--work-root PATH`: explicit work root, normally omitted.

The command rejects missing video/audio streams and ambiguous multiple audio tracks. It writes:

`<video-dir>/_work/subtitles/<video-stem>/<YYYYMMDD-HHmmss>/source_manifest.json`

The manifest contains absolute input paths, source SHA-256, FFprobe stream information, the selected audio ordinal and real stream index, the run directory, and a non-overwriting formal SRT path.

Formal output allocation is:

1. `<video-stem>_YouTube简体中文字幕_高精度校订版.srt`
2. `<video-stem>_YouTube简体中文字幕_高精度校订版_v2.srt`
3. Continue incrementing without overwriting an existing file.

## Phase 2: context and ASR

Author `context.json` using [artifact-schemas.md](artifact-schemas.md). The ASR prompt and hotwords are built only from this file.

Primary full pass:

```powershell
& $python $cli transcribe "<manifest>" --pass primary --context "<context>" --model-dir "<model-cache>"
```

Settings: `beam_size=5`, VAD enabled, `min_silence_duration_ms=500`, `max_speech_duration_s=30`, `speech_pad_ms=300`, temperature 0, word timestamps enabled.

Precision full pass:

```powershell
& $python $cli transcribe "<manifest>" --pass precision --context "<context>" --model-dir "<model-cache>"
```

Settings: `beam_size=8`, VAD enabled, `min_silence_duration_ms=350`, `max_speech_duration_s=20`, `speech_pad_ms=250`, temperature 0, word timestamps enabled.

The CLI extracts the selected full audio track as `full_selected_audio.wav` in the run directory. It does not use `-ss`, `-to`, `-t`, `atrim`, `atempo`, silence removal, or any operation that changes the source timeline. Because WAV begins at zero, the CLI restores the selected stream's FFprobe `start_time` to every segment and word timestamp so subtitle times remain on the video's container timeline.

After reading both complete transcripts, create evidence-driven regional windows. Then run:

```powershell
& $python $cli transcribe "<manifest>" --pass regional --context "<context>" --regions "<regional-review>" --model-dir "<model-cache>"
```

Regional settings: `beam_size=10`, VAD disabled, word timestamps enabled, and absolute `clip_timestamps`. Each region needs a stable id, nonnegative start, later end, and semantic reason.

## Phase 3: alignment

`reviewed_cues.json` is authored by AI after full review. Align it with labeled sources:

```powershell
& $python $cli align "<reviewed-cues>" `
  --asr "primary=<primary-json>" `
  --asr "precision=<precision-json>" `
  --asr "regional=<regional-json>" `
  --output "<aligned-cues>" `
  --report "<alignment-report>"
```

Alignment uses explicit groups, primary segment ids or semantic windows, Unicode-normalized character matching, and observed word/character times. It compares all candidates within the same semantic window and records alternative ratios. It flags ratios below 0.65, boundary shifts over 1.0 second, scripture span boundaries, prayer boundaries, first/last cues, and overlap repair.

Manual review does not mean arbitrary timing. A review must contain the original-video listening window, evidence, reason, and stable cue id. Optional `start`, `end`, or `text` overrides must reflect independently observed speech boundaries. Rerun to new paths:

```powershell
& $python $cli align "<reviewed-cues>" `
  --asr "primary=<primary-json>" --asr "precision=<precision-json>" --asr "regional=<regional-json>" `
  --manual-reviews "<boundary-reviews>" `
  --output "<aligned-cues-reviewed>" `
  --report "<alignment-report-reviewed>"
```

Overlaps no larger than 0.8 seconds may be closed at the next observed start and remain a review risk. Larger overlaps fail.

## Phase 4: render, compare, validate

Render accepts `--output` or the non-overwriting formal path in `--manifest`. It refuses an existing path.

Comparison requires equal cue counts for timing metrics. Use `--allow-resegmentation` only when segmentation intentionally changed; it then reports counts and text hashes without inventing index-to-index shifts.

Validation requires SRT, aligned cues, alignment report, boundary reviews, context, and a video duration or path. Manifest and scripture reference are required for formal delivery even though the CLI makes them optional for isolated tests.

Exit statuses:

- `PASS` / 0: no hard error and every timing risk has complete listening evidence.
- `REVIEW_REQUIRED` / 2: deterministic checks pass, but one or more risk cues lack evidence.
- `FAIL` / 1: format, timeline, readability, scripture, term, boundary, media, or hash check failed.

## Resume and failure behavior

- Do not overwrite a prior work artifact to hide a failed attempt; write a clearly suffixed replacement inside the same run directory.
- Reuse the full selected-track extraction only within the same immutable manifest.
- If PPT and sermon content conflict, stop using the PPT as correction authority until the mismatch is resolved.
- If a local model or FFmpeg dependency is missing, retain the run manifest and report the missing capability.
- If wording or timing remains uncertain after dual/regional ASR and listening, keep `REVIEW_REQUIRED`; do not guess.
