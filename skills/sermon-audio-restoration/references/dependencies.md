# Dependencies and Provenance

Install dependencies only in the project virtual environment created by `scripts/bootstrap.ps1`. Core versions are pinned in `requirements-core.txt`; optional versions are pinned separately so a difficult model install cannot break safe diagnosis and verification.

## Required local stack

| Component | Role | Version/license note | Failure behavior |
| --- | --- | --- | --- |
| [FFmpeg / ffprobe](https://ffmpeg.org/documentation.html) | Decode, probe, mature filters, speech normalization, loudness measurement, mux, full decode | Use the installed binary; FFmpeg licensing depends on its build configuration | Hard stop if missing |
| [NumPy](https://numpy.org/) | Streaming numeric analysis and correlation | 2.5.1, BSD-3-Clause | Bootstrap installs pinned version |
| [SciPy](https://scipy.org/) | Spectral analysis and signal operations | 1.18.0, BSD-3-Clause | Bootstrap installs pinned version |
| [python-soundfile](https://python-soundfile.readthedocs.io/) | Lossless block I/O and exact frame accounting | 0.14.0, BSD-3-Clause; uses libsndfile | Hard stop for lossless master operations |
| [PyYAML](https://pyyaml.org/) | Skill/tests metadata parsing | 6.0.3, MIT | Bootstrap installs pinned version |
| [Requests](https://requests.readthedocs.io/) | Explicit optional Auphonic API calls | 2.34.2, Apache-2.0 | No effect while cloud mode is off |
| [pytest](https://docs.pytest.org/) | Regression and integration tests | 8.4.2, MIT | Required for Skill acceptance, not runtime processing |

FFmpeg filters are selected from the official [filter documentation](https://ffmpeg.org/ffmpeg-filters.html), including `adeclick`, `adeclip`, `afftdn`, bounded slow `speechnorm`, equalizer/high-pass filters, and two-pass `loudnorm`. These processors are composed only when analysis supports them. Do not use `dynaudnorm` as the default: FFmpeg documents a fade-in/fade-out in its default boundary mode, and the alternative boundary mode is not accepted without stage-level edge proof.

## Optional local backends

| Component | Trigger | Safety requirement | Fallback |
| --- | --- | --- | --- |
| [Silero VAD](https://github.com/snakers4/silero-vad) 6.2.1 | Active-speech segmentation | Keep original timeline; VAD only measures regions | Energy VAD with explicit lower-confidence warning |
| [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) 0.5.6 | Confirmed complex broadband noise | Invoke delay compensation; exact-frame and zero-latency verification still mandatory | Stop/defer the module; do not replace it with strong generic denoising |
| [NARA-WPE](https://nara-wpe.readthedocs.io/en/latest/) 0.0.11 | Suitable multichannel late reverberation | Require stereo/multichannel reflection diversity and block-overlap output with unchanged channel/frame count | No WPE for mono, dual-mono, or unsuitable channels |

Install them only when required:

```powershell
.\.agents\skills\sermon-audio-restoration\scripts\bootstrap.ps1 -IncludeOptional
```

An installed backend is not automatically enabled. Its issue detector, policy gate, delay test, exact sample count, and full verification must all pass.

## Optional free cloud backend

[Auphonic](https://auphonic.com/help/api/) is disabled by default and is never a fallback that the Skill may choose silently. A run requires `--cloud auphonic-free`, `--allow-upload`, an existing API key, and a live account query proving sufficient recurring free credit within the documented [free-plan allowance](https://auphonic.com/pricing). Ignore one-time credits and any paid balance; never purchase, upgrade, or continue when billing status is unclear. Disable all silence, cough, filler-word, and music cutters. Download lossless WAV and require checksum, exact frames, channel count, sample rate, and zero-latency verification before it can enter the local pipeline.

## Standards versus project target

- [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770/) defines the loudness/true-peak measurement method, and [EBU R 128](https://tech.ebu.ch/publications/r128) supplies broadcast loudness practice.
- The **-16 LUFS / -1.5 dBTP** values are this PCCS project's streaming-delivery choice. They are not presented as a universal EBU, YouTube, or Spotify mandate.
- The project accepts ±0.5 LU around the integrated target and prioritizes intelligibility/natural dynamics over forcing a short-term spread number.

## Project regression lesson

The 20260802 source historically measured near -21 LUFS integrated, with roughly 8.8 LU one-minute spread and later distant speech near -28 LUFS. A prior generic `dynaudnorm` plus `loudnorm` attempt improved aggregate numbers but its alternative boundary mode produced a severe final-region level collapse; WPE/declick/light denoise improved clarity without solving the long-term level drift. Keep these as regression evidence for diagnosis-first behavior, never as hard-coded dates, thresholds, or processing presets for new media.
