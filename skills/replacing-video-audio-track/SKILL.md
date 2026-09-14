---
name: replacing-video-audio-track
description: Use when a video has unusable camera audio and a longer or differently timed external recording must be matched, trimmed, and substituted without changing the video timeline or non-target streams.
---

# Replace and synchronize a video audio track

## Core rule

Treat the video timeline as authoritative: **视频时间轴是唯一基准**. Locate the corresponding interval in the external recording from actual signal evidence, then replace only the confirmed target audio stream.

This skill intentionally permits trimming the external recording to the matching video interval. It does not permit trimming, extending, slowing, speeding, or re-encoding the video.

## Landscape 4K handoff and continuing work

- Future PCCS recordings normally use landscape 4K. Probe actual fps, timestamps, rotation and streams; preserve the original 4K video packets, dimensions and color metadata through this audio-only stage. Do not downscale or denoise the picture here.
- Keep alignment and restoration as separate verified stages. When both are already requested, complete the authorized sequence without asking again; pass the final accepted video path, selected audio stream, hashes, alignment evidence and unchanged picture timeline to composition.
- If the user accepts a small existing offset and says to stop adjusting, retain that decision and continue the downstream task. Do not launch another millisecond search. Record user acceptance separately from measured synchronization; never change a failed measurement into PASS.
- Reuse full alignment evidence only when both input hashes, selected stream, timing origin and analysis settings match. During a long tool run, continue independent source/PPT inventory if available; retain job IDs and bounded waits. A correction during work changes the relevant decision, not all completed evidence. After interruption, verify saved jobs/results before resuming.
- Transcription and sampled video frames support AI judgment; do not assume a GPT-6 host directly ingests raw audio/video or that an asynchronous tool has completed before its result arrives.

## Required workflow

1. Inventory the requested directory. Resolve the exact video, external audio, target video-audio ordinal, and output path. If more than one candidate remains plausible, stop and ask.
2. Record SHA-256 and `ffprobe` stream metadata for every input. Treat raw AAC duration estimates as untrusted until full decode supplies the exact sample count.
3. Run full-recording alignment:

   ```powershell
   python .agents/skills/replacing-video-audio-track/scripts/replace_video_audio.py analyze `
     --video <video> --audio <external-audio> --work-dir <work-dir>
   ```

4. Review the ranked global match and all local anchors. Use AI judgment and local listening when the candidate gap is small, correlation is weak, speech is repetitive, or the report is not `pass`. A single keyword, filename, file timestamp, or one waveform peak is never sufficient.
5. Confirm the multi-anchor result has no material clock drift. If drift exceeds one video frame over the full duration, stop. Do not silently apply `atempo`, resampling compensation, padding, or video cuts.
6. Run replacement only after alignment passes:

   ```powershell
   python .agents/skills/replacing-video-audio-track/scripts/replace_video_audio.py run `
     --video <video> --audio <external-audio> --output <new-video> --work-dir <work-dir>
   ```

7. Deliver only when every mandatory verification item passes. Read [verification-contract.md](references/verification-contract.md) before running or reviewing a formal replacement. Read [alignment-method.md](references/alignment-method.md) when confidence or drift is unclear.

## Non-negotiable safety constraints

- **禁止淡入淡出**: never add `afade`, `acrossfade`, automatic gain ramps, or envelope shaping.
- Do not run denoise, dereverb, loudness normalization, compression, or restoration unless the user separately requests it.
- Use stream copy for video and every non-target stream. Preserve stream order, metadata, dispositions, subtitles, attachments, and chapters.
- Never use `-shortest`; never change the video duration or frame count.
- **不得覆盖**源媒体或已有交付文件。Always write a new output.
- Recheck source hashes after processing.
- Validate with multi-anchor correlation, non-target packet hashes, duration/frame checks, and **完整解码**.
- Any ambiguous target stream, low-confidence alignment, material 时钟漂移, source mutation, packet-hash mismatch, or decode error is a hard stop.

## Quick reference

| Evidence | Pass condition |
|---|---|
| Global match | One clearly dominant candidate |
| 多锚点 alignment | Stable offset from beginning through ending |
| Clock drift | Absolute accumulated drift no more than one video frame |
| Video/non-target streams | Packet payload hashes unchanged |
| Audio/video duration | Difference no more than one video frame |
| Command audit | No fades, `-shortest`, video filter, or video encoder |
| Final media | Full decode exits successfully with no errors |

## Common mistakes

- Trusting `ffprobe`'s estimated duration for raw ADTS AAC: use decoded sample count.
- Matching only the beginning: measure anchors across the entire video.
- Assuming different device clocks are identical: fit offset versus video time and inspect accumulated drift.
- Mapping only video plus replacement audio: preserve every non-target stream in original order.
- Treating a successful FFmpeg exit as delivery proof: probe, hash, align, and fully decode the result.
