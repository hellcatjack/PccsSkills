---
name: producing-single-camera-sermon-video
description: Use when producing a sermon from a fixed-camera recording with finalized embedded audio and a local PPTX, especially landscape 4K footage, inset PPT/pastor layouts, camera-only denoising, semantic slide timing, or requested branding in unused margins.
---

# Produce a Single-Camera Sermon Video

Let the complete sermon and PPT determine every page, animation and composition change. Programs extract, calculate, render and verify; they do not author an edit from page counts or keyword hits.

## Scope and defaults

- Future PCCS capture defaults to **landscape 4K**, normally 3840×2160. Probe actual dimensions, rotation, frame timestamps, color and audio; 4K does not imply 30 fps, SDR or sharp focus. Default delivery remains 1920×1080 H.264, constant 30 fps, with the accepted master's audio codec copied unchanged when supported.
- Use `presentations:Presentations` before reading, modifying, rendering or validating PPTX. Preserve native PowerPoint animations and their trigger relationships.
- Explicit user choices override layout/processing defaults. Carry forward accepted audio, synchronization tolerances and selected layouts. Do not reopen a millisecond sync adjustment the user has declined. Acceptance is not proof of mathematically zero offset.
- Preserve source files and previous formal outputs. Work under the requested date directory's `_work`; deliver a new, clearly named file in that date directory.

## Lock audio; identify picture separately

The input video's audio stream is the sole authoritative formal audio. Record its path, hash and selected stream as `audioSourceVideo`. It has passed the dedicated audio workflow before composition starts.

- Do not invoke `replacing-video-audio-track` or `sermon-audio-restoration` **during composition**. If the user has already requested those stages, finish them as separate upstream tasks, verify the resulting master, then lock it here. Existing authorization does not require another permission question.
- Audio may be decoded only for transcription and timing analysis. Analysis WAV, proxy audio and cropped-video audio must never become delivery sources.
- In the final mux, map the audio stream from the same input video recorded as `audioSourceVideo`, using exact stream copy. No audio filtering, fading, trimming, padding, delay, stretching, resampling, channel remixing or re-encoding.
- For improved denoising, `pictureSourceVideo` may be the original 4K recording of the **same take**, instead of an already softened derivative. Prove the mapping to the accepted timeline using provenance, dimensions, duration, frame count, timestamps and beginning/middle/end visual anchors. Similar duration alone is insufficient. This does not authorize a different take or new alignment.
- A new audio defect or unsupported copy source blocks final mux. Continue independent PPT/picture work; resolve the specific upstream defect or ask only for genuinely missing input. A user-accepted residual offset alone is not such a defect.

## Workflow and reference routing

1. Inventory input roles, existing evidence and hashes. Read [production-workflow.md](references/production-workflow.md). Reuse eligible full-transcript evidence by exact audio identity and ASR configuration.
2. Read every slide, note, object, animation and the complete transcript. Resolve verse/name errors and uncertain boundaries by local re-listening. Represent every repeated slide appearance explicitly, including a second pass.
3. Inspect pastor frames throughout the recording, including posture and gesture extremes. Use one fixed crop. Read [composition-policy.md](references/composition-policy.md) for the landscape inset preset, full-screen focus and opening exclusions. Prepare a composition preview; an already approved layout needs no renewed approval.
4. Author the JSON plan with semantic reasons, native animation evidence and frame boundaries. Run `scripts/validate_composition_plan.py` before encoding. A numeric pass never substitutes for semantic review.
5. When picture noise needs treatment, read [camera-denoising.md](references/camera-denoising.md). Crop the real camera picture, scale to its largest approved visible size, benchmark short candidates, then denoise visible intervals with temporal context. **PPT pixels never enter a denoiser.**
6. Use PowerPoint native output when animations/transitions require it; reopen timed copies to verify saved settings. Static native slide images are allowed only after proving there are no effects to preserve and checking every page.
7. Build the graph with `scripts/build_dynamic_filter.py`. Its inset path supports original camera input or a processed panel on the complete timeline; never crop a processed panel twice. Encode the visual program once, then stream-copy locked audio without `-shortest`.
8. Apply [verification-contract.md](references/verification-contract.md) to the exact candidate. Correct failures and rerun affected checks. Deliver only after every applicable gate has fresh evidence.

For multiple camera files, head/tail trimming or an external recording, first use `preparing-multiclip-sermon-master` to produce one verified finished master. This Skill starts only after that master is locked. For optional church identity or sermon information in unused margins, read [branding-overlays.md](references/branding-overlays.md). For long jobs and GPT-6 behavior, read [gpt6-execution.md](references/gpt6-execution.md). For requested titles, descriptions or thumbnails, read [publication-assets.md](references/publication-assets.md).

## Delivery

Report the absolute output link, duration, dimensions, frame rate, codecs, SHA-256, material layout/denoising changes and measured limitations. Keep progress concise and in the user's language. Intermediate files stay under `_work`; include them only for requested audit or unresolved failures. Source softness and motion blur must not be described as recovered detail.
