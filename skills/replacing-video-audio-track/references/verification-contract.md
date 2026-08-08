# Verification contract

A formal replacement passes only when all applicable checks below have fresh evidence.

1. Record source SHA-256 before work and prove the hashes are unchanged afterward.
2. Probe input and output streams. Confirm video duration, frame rate, frame count, codec, dimensions, and start time are unchanged.
3. Confirm the external segment start comes from a dominant full-file match plus distributed local anchors.
4. Confirm accumulated clock drift is no more than one video frame. A larger value requires a new user-approved retiming decision.
5. Audit the executed FFmpeg command: it must contain stream copy for video/non-target streams and must not contain `afade`, `acrossfade`, `-shortest`, a video filter, or a video encoder.
6. Hash copied packet payloads for every non-target stream and compare source with output.
7. Confirm output audio, video, and container durations differ by no more than one video frame.
8. Re-align the final encoded audio against the complete external recording at multiple anchors.
9. Decode the entire output container with FFmpeg `-xerror`; any corrupt packet, timestamp failure, early termination, or nonzero exit fails.
10. Write an audit JSON containing inputs, hashes, probes, offset, candidates, anchor correlations, drift, executed command, stream hashes, durations, full-decode result, and an overall pass/fail status.

Do not deliver an output with a missing measurement or failed item. Do not overwrite an earlier formal output to make a failed run appear successful.
