# Verification Contract

Formal output is an atomic promotion from `_work` only after every applicable check passes. If a final-path recheck fails, move the generated file back into the work area and report failure; never overwrite the source or an existing deliverable.

## Immutable baseline

Before processing, record source SHA-256, selected zero-based audio ordinal and global stream index, codec, sample rate, channel layout, time base, start PTS/time, packet timing, decoded exact sample count, container duration, and all stream identities. For video, also record packet hashes for every non-target stream.

The source SHA-256 must be identical at delivery. Decode the complete selected track without seeking or trimming; timestamp gaps are positions to preserve, not silence to collapse.

## Mandatory audio checks

1. The lossless master has the exact sample count, sample rate, and channel count of the decoded baseline. A mismatch of one sample fails.
2. FFT correlation at 5%, 25%, 50%, 75%, 95%, and every repair region reports zero latency. Any nonzero anchor or changing offset fails; padding one end and cutting the other is not repair.
3. The beginning, final speech, room tail, and final silence are retained. No cutter, tempo change, concatenation, timeline-selecting filter, `afade`, or `acrossfade` appears in the executed command audit.
4. The entire candidate decodes successfully with no corrupt packet, non-monotonic timestamp, or early termination.
5. Integrated loudness is -16 ±0.5 LUFS and true peak is at or below -1.5 dBTP, unless a user-approved target was explicitly recorded.
6. Source/output decoded durations differ by no more than one audio sample for a lossless master.
7. AAC or another delayed codec must account for encoder priming/skip-samples and padding. Container packet count alone cannot prove content alignment.
8. Source-relative 0.5-second RMS regression across the first and final 15 seconds must remain within 5 dB at every processing stage and in the final lossless master. Any larger trend is an added fade-like boundary change and fails, even if duration, sample count, loudness, and latency pass.
9. A lossy AAC delivery must be calibrated from a temporary encode of the final lossless master. Measure that encode's integrated loudness and true peak, choose only makeup gain that retains at least 0.1 dB of peak margin, and still verify the finished container independently.

## Video and container checks

- Restore the selected audio stream's start-time relationship. Final audio, video, and container duration differences must not exceed one video frame or one audio sample, whichever is the relevant tighter check.
- Use stream copy for video and all non-target streams. Verify their packet hashes are unchanged.
- Preserve original stream order, metadata, language tags, dispositions, subtitles, attachments, and chapters. A chapter-backed MP4 data track must not be duplicated during remux.
- Replace only the confirmed audio ordinal; an ambiguous multi-audio input is a hard stop.
- Decode the final container from beginning to end and probe its actual streams and duration after muxing.

## Report requirements

Include a mandatory `no_added_fades` item with the measured start and end edge-gain trends and window counts.

The JSON verification report must list every item as pass or fail with measured and expected values. It must include source/output SHA-256, exact sample counts, anchor offsets, loudness, true peak, start times, duration tolerance, decode result, non-target stream hashes, and source recheck. A missing required measurement is a failure, not “not applicable,” unless the media type genuinely lacks that feature.

Any failed check prevents formal delivery. A/B approval addresses perceived-quality risk only; it never waives exact sample count, zero latency, immutable-source, decode, or stream-preservation requirements.
