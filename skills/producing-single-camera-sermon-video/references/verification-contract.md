# Verification contract

A formal output passes only with fresh evidence for every applicable item, tied to the exact candidate hash. Reusable source evidence must be linked to matching immutable input hashes. A structural plan pass or successful encode is not acceptance.

## Media, clock and source roles

1. Probe MP4/H.264, 1920×1080, CFR 30, SAR 1, `yuv420p`, expected channels/color and program start zero. The audio codec must match the locked master by stream copy; AAC and ALAC are both possible when the selected container supports them.
2. Confirm `videoFrames == expectedFrames == round(duration*30)`; inspect all frame timestamps for CFR and cumulative drift, not only the average-rate metadata.
3. Compare video/audio/container durations with the locked audio. Each difference must be within one frame. Never use `-shortest` to hide a mismatch.
4. Run a full decode with FFmpeg `-xerror`; require zero exit status and no decode errors.
5. Verify `pictureSourceVideo` provenance and frame mapping against the accepted master at beginning/middle/end and any cuts. Different take, source fps or start offset cannot be accepted merely because durations resemble each other.
6. Verify a processed panel's dimensions, complete frame count, timebase, no-audio state, chunk core/context ranges and absolute-index assembly. Hidden placeholders must never enter a positive-opacity pastor frame.

## Audio identity

Compare selected input-video audio packets with final audio packets: the audio packet hash must match exactly, including payload order and packet count. No PCM-hash fallback is permitted: decoded equality alone does not prove stream copy.

Check codec, sample rate, channels/layout, start, duration, language, disposition and metadata. Compare packet PTS/DTS/duration in normalized time units when time bases differ. Audit that the final command maps the locked `audioSourceVideo` stream and uses `-c:a copy`, with no audio filter/encoder, restoration, gain, fade, trim, padding, delay, tempo, channel conversion or resampling.

If exact identity cannot be established, fail this gate and diagnose the mismatch. A missing measurement is not an audio defect: collect the missing evidence before requesting a replacement source. Unsupported copy input requires an explicitly resolved upstream audio master. Preserve a user-accepted residual camera/audio offset; do not label it a newly measured zero offset or silently adjust it.

## PPT, opening and composition

1. Compare a stable frame from **every page instance**, including repeated slides, with the correct native PowerPoint final-state reference. Verify backgrounds, masters, text, fonts and images.
2. Inspect before/after frames at every page boundary; check the complete spoken sentence and avoid cutting a verse early.
3. Inspect before/after frames at every independent animation trigger; verify object identity, order, duration and `With Previous`/`After Previous` grouping.
4. Verify the whole initial exclusion interval frame by frame against the authentic cover and check the first permitted camera transition. No camera-setup pixels may leak through. Continue audio from zero.
5. Inspect **every consecutive frame** across each intro, focus and ending transition, plus stable frames before/after. Confirm no flash, stretched slide, moving crop, missing background, clipped heading or unexpected half-visible text. A sparse contact sheet alone does not cover all transition frames.
6. Inspect pastor framing across representative posture/gesture extremes, even for a fixed camera. Preserve recorded lectern detail and intended gestures without inventing unrecorded objects. Check the crop and uniform scaling against the plan.
7. Check `left-cover-right-pastor` before/during/after the final cover transition, throughout prayer and near the last frame. Preserve the complete tail.
8. Re-listen to all low-confidence semantic boundaries and record the decision. A number computed from ASR cannot replace that review.
9. If branding was added, inspect every information phase, all overlay fade boundaries, full-screen slide passages and the ending. Confirm the overlays occupy only unused margins, show only approved content, leave the slide/pastor picture clear, and preserve the final audio packet identity.

## Denoising and visual comparison

Compare source and selected candidate motion clips at identical timestamps, display size, color conversion and compression settings. Check skin, eyes, moving hands and lectern edges for smear, ghosting, flicker or detail loss. Review processed-chunk entries/exits with temporal context.

In the final composite, compare visible pastor viewports with the selected processed reference; compare PPT separately with native slides. Skip intentionally covered pastor pixels during full-screen focus; do not substitute a different timestamp silently. Record sample time and visibility.

For quantitative comparisons, align crop, resolution, SAR and colorspace first. Convert both images consistently **before** downscaling; RGB-versus-YUV scaling can otherwise create misleading errors. Record thresholds and rationale before judging results. Investigate mismatches; do not lower thresholds merely to pass. A wall-patch noise reduction is a local measurement, not a whole-video sharpness score.

## Integrity and report

Recompute hashes for all source media, source PPTX and protected prior formal outputs against baseline. Record native render and selected panel hashes when those become verification references. Preserve originals and previous versions.

Write JSON with each check's expected/measured values, evidence path, candidate hash and `PASS`, `FAIL` or `REVIEW_REQUIRED`; use `NOT_APPLICABLE` only with a supported reason (for example, a deck proven to contain no animations). Cast library scalars into real JSON values. Missing evidence or any required failure blocks final promotion.

After a repair, rerun affected visual/semantic gates and all final-file media/audio/integrity gates when encoding or mux changed. Once the exact candidate passes, do not repeat unrelated checks or rerender the sermon for a metadata-only change.
