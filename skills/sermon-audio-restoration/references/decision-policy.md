# Decision Policy

Use this lookup after full-file measurement. An issue is actionable only when its detection evidence is consistent across time/frequency checks and AI review finds it relevant to intelligible speech. The safest valid result may be no processing.

| Issue | Required detection evidence | Preferred repair | Guardrail or fallback |
| --- | --- | --- | --- |
| Digital clipping | Flat-top runs, near-full-scale sample ratio, local spectral distortion | Mild FFmpeg `adeclip` | Severe or prolonged clipping requires A/B; do not claim lost waveform recovery |
| Click or isolated pop | Very short derivative/peak outlier distinct from speech attacks | FFmpeg `adeclick` | Reject if it softens consonants, applause, or lectern impacts |
| Plosive/low-frequency blast | Local LF surge with speech timing, not a click | Time-bounded high-pass/equalizer attenuation | Never thin the whole sermon or remove male fundamentals globally |
| Narrow feedback/howl | Stable high-Q spectral peak above neighboring bins, with measured bandwidth/Q and no voiced-harmonic support | Localized high-Q notch, then harmonics only if measured | Broad formants, harmonic series, and short uncertain tones remain `tonal_candidate`; multiple/uncertain bands require A/B; never broad static cutting |
| 50/60 Hz hum | Fundamental plus stable integer harmonics | Measured de-hum notch set | Choose the detected mains family, not both; retain voice body |
| Stationary light noise | Stable noise floor in non-speech evidence | Conservative FFmpeg `afftdn` | Back off at metallic, watery, gated, or consonant damage |
| Complex broadband noise | Low SNR/nonstationary spectrum and speech masking | DeepFilterNet with delay compensation | If unavailable, report capability gap; no aggressive generic fallback |
| Room reverberation | Tail decay/clarity evidence plus sufficiently different microphone channels | NARA-WPE | Requires suitable multichannel reflection diversity; mono or dual-mono falls back to no WPE |
| Microphone-distance level drift | Active-speech short-term spread over about 3 LU and sustained gain trend | Bounded slow FFmpeg `speechnorm`, or explicitly authorized free Auphonic leveler | Limit expansion to 6 dB before A/B approval, link channels, preserve prayer and emphasis, and reject any source-relative edge trend above 5 dB; do not use `dynaudnorm` as the default because its documented boundary behavior can add fades |
| Whole-program loudness | ITU-R BS.1770 integrated loudness or true peak outside the project target | Measured two-pass FFmpeg `loudnorm` last | This does not replace drift correction; target is -16 ±0.5 LUFS, ceiling -1.5 dBTP. For lossy AAC delivery, calibrate against a temporary AAC encode and apply only peak-safe makeup before the final mux. |
| Channel quality mismatch | Per-channel clarity, noise, loudness, correlation, and delay | Select the demonstrably clearer channel only for confirmed dual-mono, then preserve layout intentionally | Louder alone is not clearer; ambiguous channel choice stops for review |
| Already compliant | No supported defect; loudness and peak pass | No repair step | Avoid generation loss and processing for its own sake |

## Decision gates

- Analysis fallback matters: if Silero VAD is unavailable and energy detection was used, any material speech gain increase needs AI review and gains over 6 dB require A/B.
- Run defect repair before speech-level stabilization, and final loudness normalization last.
- Reject explicit `afade` and `acrossfade` filters. Run source-relative edge-gain validation after every stage so implicit processor boundary fades cannot hide behind later loudness normalization.
- Each processing-plan entry must name the issue finding, time/frequency region when applicable, parameters, reason, expected benefit, and risk.
- Stop before formal promotion when the plan requests strong denoising, uncertain dereverberation, severe de-clipping, multiple howl repairs, or `--force-ab-review`.
- Cloud is not an automatic quality tier. Auphonic is permitted only by explicit mode plus upload consent, authenticated recurring free credit, and the free-plan cap. One-time or paid credit is ignored. All cough, filler-word, music, and silence cutters remain false.

## AI review checklist

- Compare anomalies against neighboring speech and the sermon context; avoid classifying normal sibilants, breath, applause, music, or lectern contact as defects.
- Review beginning, middle, end, every repair interval, quiet prayer, and the loudest passage.
- Prefer fewer modules and gentler parameters when two plans solve the same audible problem.
- Record uncertainty. Numeric detection nominates evidence; it does not decide perceived quality by itself.
