---
name: preparing-multiclip-sermon-master
description: Use when a sermon camera recording spans multiple video files and needs ordered joining, head/tail trimming, external-audio replacement, or loudness treatment before slide-based video production.
---

# Prepare a multiclip sermon master

Produce one verified video master whose picture timeline and audio are final. Keep camera originals and the independent recording unchanged. This Skill coordinates timeline preparation with the dedicated audio skills; it does not relax their alignment or restoration checks.

## Workflow

1. Inventory all camera files, external recordings, and previous outputs. Determine chronological camera order from recording continuity and media evidence, not lexical filenames alone. Record source hashes, time bases, frame rates, dimensions, audio streams, and decoded durations. Resolve ambiguous candidates before editing.
2. Express the edit as one timeline: ordered source ranges, exact head/tail cuts, expected source and output frame counts, and every join boundary. Convert requested times to source frame/sample boundaries deliberately; a time such as 2:30 may not equal exactly 150 seconds at 30000/1001 fps.
3. Join the camera picture and apply the requested outer trims. Use stream copy only when stream parameters and timestamp behavior permit a clean frame-accurate join; otherwise make a high-quality intermediate with explicit frame rate, color metadata, and no unplanned gaps or duplicate frames. Inspect picture and embedded camera-audio continuity on both sides of every seam. Treat the resulting picture timeline as locked.
4. If an independent recording will replace camera audio, use `replacing-video-audio-track` on that locked video. Its video-preservation rule begins here: replacement must not recut, retime, or encode the prepared picture. Require a dominant full-recording alignment, distributed anchors including join neighborhoods, clock-drift evidence, and the dedicated skill's verification contract. Preserve an inconclusive automated score as `review_required`; only documented independent listening and signal evidence can resolve it, and never rewrite the measured score as a pass.
5. If audio level or restoration is requested, use `sermon-audio-restoration` on the replacement output. Diagnose before choosing modules. Measure integrated LUFS and true peak, preserve the exact decoded sample count and zero latency, inspect the first and last source-relative gain behavior, and keep picture packets unchanged. Avoid extra denoising, dereverberation, compression, or fades without evidence and authorization.
6. Probe and fully decode the final master. Verify ordered camera frames, each seam, exact requested trims, picture packet identity across audio-only stages, audio/video end difference within one frame, final audio alignment across the sermon, requested loudness/peak targets, and all source hashes. Write an audit with measured values, commands, evidence paths, and explicit pass/fail results.
7. Hand the verified master to `producing-single-camera-sermon-video` when slides or composition are requested. That downstream Skill copies the master's audio packets unchanged.

## Stops

Stop on uncertain source order, an unexplained timestamp discontinuity, material audio drift, a seam that loses speech or frames, or a failed dedicated audio verification. Keep provisional outputs under the work directory and do not label them as a finished master.
