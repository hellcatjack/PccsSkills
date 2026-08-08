---
name: producing-single-camera-sermon-video
description: Use when a sermon video must be produced from one fixed-camera pastor recording whose embedded audio is already final and one local PPTX, especially with slide synchronization, repeated slide passes, stable pastor framing, or dynamic slide emphasis.
---

# Produce a Single-Camera Sermon Video

## Core principle

Let the sermon meaning drive every page, animation, and composition change. Use programs for extraction, rendering, calculation, encoding, and verification; never let page counts, fixed intervals, or keyword matches author the edit. Treat the input video's embedded audio as immutable.

## Required capability routing

- **REQUIRED SUB-SKILL:** Use `presentations:Presentations` before reading, modifying, rendering, or validating a PPTX.

## Non-negotiable audio boundary

- The input video's audio stream is the sole authoritative formal audio. It has already passed the dedicated audio workflow before this Skill starts.
- Do not invoke `replacing-video-audio-track` or `sermon-audio-restoration`.
- Audio may be decoded only for transcription and timing analysis. Any extracted or decoded analysis file is temporary evidence and must never become a delivery source.
- In the final mux, map the audio stream from the same input video and use audio stream copy.
- Never filter, gain-stage, normalize, compress, limit, denoise, dereverberate, declip, fade, trim, pad, delay, stretch, resample, remix channels, or re-encode the audio.
- If the embedded audio is wrong, damaged, out of sync, unsupported for direct MP4 stream copy, or otherwise unsuitable, stop and request a newly audio-treated input video. Do not repair or substitute it in this Skill.

## Workflow

1. Inventory all candidate video, PPTX, and existing deliverables. Resolve exactly one input video and one PPTX. Record source hashes and exact media parameters; stop if input selection is ambiguous.
2. Read every slide, note, layout, object, and animation. Decode the embedded audio only as needed to create and read the complete transcript, then map the real sermon structure: opening, scripture reading, prayer, points, examples, summary, and closing prayer.
3. Decide whether the deck plays once or repeats. Represent every appearance as its own `pptSegments` entry with a semantic reason; a second pass is never inferred from filenames.
4. Select one fixed crop for the pastor and lectern. Preserve gestures and sightline, keep the pastor on the side favored by the source framing, and give the PPT the largest readable region.
5. Create a composition preview unless the user has already approved the same crop/layout or granted standing authority to apply the recommended layout.
6. Build an auditable JSON plan. Run `scripts/validate_composition_plan.py`; fix every error before encoding.
7. Render the presentation with PowerPoint native output whenever it contains animations, transitions, or layout-sensitive text. Build the dynamic video graph with `scripts/build_dynamic_filter.py`.
8. Encode the visual program to 1920×1080 H.264 at constant 30 fps. In the final mux, map the original embedded audio from the same input video with `-c:a copy`; do not use `-shortest`.
9. Apply every gate in [verification-contract.md](references/verification-contract.md). Deliver only when all checks pass.

Read [composition-policy.md](references/composition-policy.md) before choosing the crop or full-screen blocks. Read [production-workflow.md](references/production-workflow.md) before creating the timed PPT video or running FFmpeg.

## Quick reference

| Decision | Required result |
| --- | --- |
| Normal layout | PPT maximized; pastor remains in a narrow fixed side panel |
| Opening | Full-screen cover, audio starts at zero, then a smooth move to split view |
| Emphasis | Full-screen PPT only at high-value semantic passages |
| Repeated deck | Explicit page instances; verify every second pass background |
| Ending | `left-cover-right-pastor` through the final word and room tail |
| Audio | Input-video stream is immutable; final mux uses exact packet-preserving stream copy |

## Hard stops

Stop rather than improvise when PowerPoint native rendering is unavailable for an animated deck, the crop cannot preserve the pastor/lectern/gestures, the input audio cannot be copied unchanged, a page or animation cannot be mapped semantically, or any mandatory verification fails.

## Common mistakes

- Averaging time across slides instead of reading the sermon.
- Moving the pastor panel merely to create variety.
- Keeping the PPT permanently small or switching full-screen on a timer.
- Reusing the first-pass slide bitmap in a way that drops the second-pass background.
- Hiding the pastor when returning to the cover for the closing prayer.
- Treating a decoded transcription copy as output audio instead of remuxing the original input-video packets.
- Calling an audio replacement or restoration workflow because the embedded audio appears defective; this Skill must stop instead.
