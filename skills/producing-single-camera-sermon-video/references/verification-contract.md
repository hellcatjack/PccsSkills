# Verification contract

A formal output passes only with fresh evidence for every applicable item.

## Media and timeline

1. Probe the final MP4: H.264, 1920×1080, constant 30 fps, `yuv420p`, AAC, expected channel layout, and start time zero.
2. Confirm `videoFrames == expectedFrames == round(duration × 30)`.
3. Keep video, audio, and container duration differences within one frame. Do not hide a mismatch with `-shortest`.
4. Run a full decode with FFmpeg `-xerror`; require exit code zero and empty error output.

## Audio identity

Compare the input-video audio packet hash with the final audio packet hash. The audio packet hash must match exactly; this is mandatory for every output made by this Skill. No PCM-hash fallback is permitted because decoded equality cannot prove that the workflow avoided processing or re-encoding.

Probe both streams and confirm codec, sample rate, channel count/layout, start time, duration, language tag, disposition, metadata, packet count, and packet payload order are unchanged. Audit the final mux command: it must map the audio stream from the same input video, use `-c:a copy`, and contain no audio filter, audio encoder, fade, gain, normalization, compressor, limiter, restoration, denoising, dereverberation, declipping, tempo, trim, padding, delay, timestamp transform, channel conversion, or resampling operation.

If exact packet identity cannot be established, or direct stream copy is unsupported, fail verification and stop and request a newly audio-treated input video. Do not substitute a decoded file or relax the comparison.

## PPT and composition

1. Extract stable frames for every `pptSegments` instance, not merely every unique slide. Compare each frame with the correct PowerPoint reference.
2. Compare all repeated page pairs and explicitly verify the second pass background, master graphics, fonts, and images.
3. At every page boundary, extract before/after frames and confirm the planned semantic page change.
4. At every animation trigger, extract before/after frames and confirm the intended object and trigger grouping.
5. At the opening transition and every full-screen block, extract frames before, during, stable, during exit, and after. Confirm smooth motion, correct page identity, readable frames, and no black/white flash.
6. Compare the output pastor panel with the planned fixed crop from the camera source. Require the lectern and intended gesture area to remain visible.
7. Check the ending before, during, and after the cover transition and near the final frame. Confirm the left cover remains correct and the right pastor remains continuously visible in `left-cover-right-pastor` mode.

## Integrity

- Recalculate the input video, PPTX, PowerPoint native video, and preserved prior outputs against their baseline hashes.
- Preserve every original and prior formal output.
- Write a JSON report listing each check, expected value, measured value, evidence path, and pass/fail state.

Any missing measurement or failed check blocks delivery. A successful encoder exit, a contact sheet, or “looks correct” is not a substitute for the required evidence.
