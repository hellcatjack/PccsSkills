# Alignment method

## Evidence chain

1. Decode both candidate tracks completely to 8 kHz mono analysis PCM. Apply the same 100–3800 Hz analysis-only band-pass to both.
2. Build 100 ms log-energy features for total energy and seven speech bands.
3. Use sliding normalized cross-correlation over the complete external recording. Retain the best candidate and the best non-adjacent runner-up.
4. Refine the coarse offset with waveform correlation in evenly distributed local windows.
5. Fit `external_offset = intercept + slope × video_time`. The intercept is the external-audio cut point; `slope × video_duration` is accumulated clock drift.
6. Repeat alignment on the encoded output audio against the full external recording.

## Interpretation

- Strong agreement means every local anchor selects the same offset path and residuals remain small.
- A high global score with inconsistent anchors is not a pass; repetitive music, silence, applause, and liturgical responses can create false matches.
- A stable but sloped offset indicates separate-device clock drift. Do not hide it by moving only the start point.
- If acoustic correlation is weak, inspect/listen around the top candidates and use speech transcription as secondary evidence. Record the semantic anchors used.
- If the external recording ends less than one video frame before the video because of codec framing, do not cut the video. Report the measured shortage; do not invent audible content.
