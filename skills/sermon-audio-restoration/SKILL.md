---
name: sermon-audio-restoration
description: Use when sermon or speech audio from an audio file or video track needs diagnosis, feedback or clipping repair, speech-level stabilization, streaming loudness normalization, or strict audio-video synchronization preservation.
---

# Sermon Audio Restoration

Restore speech with evidence-driven local tools while treating every source sample and timestamp as immutable content. The default delivery target is **-16 LUFS** integrated loudness (tolerance ±0.5 LU) and no higher than **-1.5 dBTP** true peak.

## Non-negotiable rules

- Treat every source as read-only. Record its SHA-256 before work and compare it again before delivery.
- Run full-file analysis. Never infer a whole sermon from a short excerpt.
- Never cut, concatenate, time-stretch, or silence-strip the formal audio. Reject `-ss`, `-to`, `-t`, `-shortest`, `atrim`, `silenceremove`, `atempo`, and equivalent operations.
- Never add a fade-in or fade-out. Reject `afade`, `acrossfade`, editor fades, automation ramps used as program fades, and processors whose boundary behavior creates a fade-like gain trend.
- Require exact decoded sample-count preservation and zero latency at multiple anchors. Do not hide delay by dropping source samples or padding content.
- Compare every processing stage with its input and compare the final master with the immutable baseline. Reject an absolute source-relative gain trend above 5 dB across either the first or final 15 seconds; sample-count preservation alone cannot prove the edges are intact.
- For video input, replace only the selected audio track. Use stream copy for video and every non-target stream, preserving their packet hashes, order, metadata, dispositions, subtitles, and chapters.
- Keep cloud processing off by default. The only supported cloud path is an explicitly requested Auphonic free-plan run with upload consent and verified recurring free credit; never buy credit or use a paid plan.
- Do not deliver when A/B review is required, when verification fails, or when an optional backend is unavailable for a defect that has no safe fallback.

## Workflow

1. Inventory candidate media. If more than one source or audio track is plausible, resolve it from context or stop for user selection. Never guess.
2. Read [decision-policy.md](references/decision-policy.md), [verification-contract.md](references/verification-contract.md), and [dependencies.md](references/dependencies.md) before production processing.
3. Bootstrap the isolated environment if needed:

   ```powershell
   .\.agents\skills\sermon-audio-restoration\scripts\bootstrap.ps1
   ```

   Add `-IncludeOptional` only when the analysis justifies an optional backend.
4. Run diagnosis first:

   ```powershell
   .\.audio-skill-venv\Scripts\python.exe .\.agents\skills\sermon-audio-restoration\scripts\sermon_audio.py analyze <input> --target-lufs -16 --true-peak -1.5
   ```

   For ambiguous multi-audio media, pass the confirmed zero-based audio ordinal with `--audio-stream`.
5. Perform AI review of the complete report, time trends, channel metrics, every flagged region, and the source-relative gain at both program edges. Distinguish speech defects from intentional pauses, consonants, music, applause, lectern noise, and room character. State why each proposed module is necessary; remove unsupported modules. Never apply a fixed filter chain merely because it worked on an earlier sermon.
6. Run restoration only after that review:

   ```powershell
   .\.audio-skill-venv\Scripts\python.exe .\.agents\skills\sermon-audio-restoration\scripts\sermon_audio.py restore <input> --target-lufs -16 --true-peak -1.5
   ```

   Use `--output` for a new, non-source path. Use `--cloud auphonic-free --allow-upload` only after the user explicitly authorizes both the free backend and the upload.
7. If the command returns the A/B-review state, inspect identical source/candidate regions for intelligibility, timbre, pumping, metallic or watery artifacts, and damaged consonants. Resume only after a documented choice; otherwise keep all results under `_work`.
8. Independently verify the candidate against the immutable source:

   ```powershell
   .\.audio-skill-venv\Scripts\python.exe .\.agents\skills\sermon-audio-restoration\scripts\sermon_audio.py verify <output> --against <input> --target-lufs -16 --true-peak -1.5
   ```

   Require the `no_added_fades` item to pass. Inspect the opening and final A/B regions even when loudness, peak, sample count, and latency already pass.

9. Report source/output paths, hashes, measured loudness and peak, exact sample counts, zero latency result, stream-copy evidence for video, applied modules with reasons, A/B disposition, and every verification item. Do not describe a partial or failed run as complete.

## Judgment boundaries

- Prefer no processing when the source already passes and no audible defect is supported by evidence.
- Favor localized, minimal repair for clicks, plosives, hum, or feedback. Preserve natural sermon dynamics and quiet prayer.
- Treat speech-level drift and final loudness as different problems: stabilize sustained microphone-distance changes first, then run measured two-pass loudness normalization.
- Do not use `dynaudnorm` as the default speech leveler: its documented default boundary mode adds a smooth fade-in/fade-out, while its alternative boundary mode still requires source-specific proof. Prefer a bounded, slow `speechnorm` pass and reject it if stage-level edge-gain verification fails.
- Escalate irreversible clipping, multiple uncertain howl bands, strong denoising, questionable dereverberation, or large gain recovery to A/B review.
- Missing capability is a visible stop or downgrade, never permission to substitute an aggressive generic filter.
