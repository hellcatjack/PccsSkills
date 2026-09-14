# Production workflow

## 1. Inventory, immutable sources and timeline

Resolve the date directory's PPTX, `audioSourceVideo`, selected audio ordinal and `pictureSourceVideo`. Default picture source equals audio source; use original same-take footage only with verified provenance when reprocessing is justified. Hash inputs and protected old outputs. Keep generated material under `_work`.

Probe dimensions, rotation, SAR, codec, pixel format, color primaries/transfer/range, frame rate/timestamps/counts, duration and stream starts. Landscape 4K is the capture expectation, not permission to assume 3840×2160/30 SDR. Normalize the **picture only** when 25/29.97/60 fps, rotation or HDR requires 1080p/30 SDR delivery. Write and verify the source-to-output frame mapping. The visibility helper uses output-frame indexes; source indexes match only for a proven 1:1 timeline. Do not change playback speed to force 30 fps.

The input video's audio stream is the sole authoritative formal audio. Audio may be decoded only for transcription and timing analysis. Lock its path, stream and hash; extracted audio, proxies and denoise chunks are never formal sources. No audio transforms or re-encoding after this lock. Preserve a user-accepted sync discrepancy and record acceptance separately from measured zero-latency evidence.

If an upstream audio stage is already authorized, complete and verify it before locking composition audio. Do not start new alignment/restoration merely because the visual source is noisy or subtitles are requested.

## 2. Full semantic evidence

Use `presentations:Presentations`. Read text, notes, masters, layouts, objects, order, dimensions and all animation sequences. Export final-state PNGs through native PowerPoint.

Generate and read the complete transcript with paragraph/word timestamps. Existing evidence is reusable only when selected audio identity, timestamp origin, ASR model/settings and full coverage are verified; record the match. One complete qualified pass plus uncertain-region review suffices for composition. The separate high-precision subtitle skill still requires its two full passes.

Use AI context to distinguish opening, reading, prayer, theme transitions, points, examples, recap and closing. PPT wording helps correct names/verses but does not prove an unspoken verse was read. Review uncertain ranges locally with adjacent sentences. Place boundaries at the sentence entering the new topic, not a late keyword or preceding preview.

## 3. Auditable plan

Include `duration`, `fps: 30`, `expectedFrames: round(duration*30)`, source-role evidence, crop inspection, intro exclusions, transitions, `layout`, `pptSegments`, `fullScreenBlocks` and `endingCover`.

- Each page instance has `slide`, `sourceStart`, `sourceEnd`, `targetStart`, `targetEnd`, `reason` and spoken evidence/confidence. Source ranges refer to native PPT video; target ranges are contiguous and cover complete audio.
- Each animation records original ID, object, effect, order, trigger group, duration and planned absolute/relative onset. Preserve `With Previous`. For `After Previous`, subtract the previous effect's duration when computing relative delay.
- Geometry uses integer even-pixel `pptRect`/`pastorRect`, actual source dimensions and `pastorCrop`. The inset renderer requires a 16:9 PPT canvas; other ratios need a separately verified letterbox adaptation.
- Opening uses `coverSlide`, `coverUntil`, `cameraForbiddenBefore`, `fullUntil`, `splitComplete`. Focus blocks cannot overlap intro/ending. Generated transitions and visibility boundaries must be on the 30 fps grid; retain original spoken times before rounding.
- `cameraInput.mode` is `source` or `processed-panel`. A processed panel declares width/height matching `pastorRect`, contains the complete output timeline and has no audio.

From the installed skill directory (use real task paths):

```powershell
python scripts/validate_composition_plan.py <plan.json>
python scripts/plan_camera_processing.py --plan <plan.json> --context-frames <combined-radius> --output <camera-plan.json>
python scripts/build_dynamic_filter.py --plan <plan.json> --output <filter.txt>
```

The validator checks geometry/time structure, not media identity, animations, visual correctness or semantic truth. Its pass is not full acceptance. The camera planner declares work; it does not run a denoiser or assemble clips. Read [camera-denoising.md](camera-denoising.md) for processing and reconstruction.

## 4. Native PPT and camera processing

Write automatic timings only into a PPTX copy, close/reopen and verify saved page durations/animation groups against the plan. Use PowerPoint native `CreateVideo` for effects and transitions. A static alternative requires proof that no effects need preservation and every page matches. Do not replace an animated deck with screenshots when COM is unavailable.

Adjust native PPT **video timing only** for export rounding, and recheck animations on the final clock. Verify repeated-page backgrounds. Camera processing and PPT work can run independently when resources allow. Avoid simultaneous GPU ASR, neural denoising and heavy GPU encoding when they contend for memory.

## 5. Compose, then mux

Filter inputs: 0 native timed PPT video; 1 original picture source or processed panel; 2 duration-matched authentic cover clip. Map only `[outv]` into the visual intermediate. Panel mode does not re-crop or denoise input 1. Optional headings need a reviewed graph extension.

Encode H.264, 1920×1080, CFR 30, `yuv420p`, SAR 1 and exactly `expectedFrames`. Start from reliable native/raw assets and a lossless or visually verified high-quality panel intermediate. Do not repeatedly transcode old deliverables. Probe the visual stream before mux.

In the final mux, map the audio stream from the same input video locked as `audioSourceVideo`:

```powershell
ffmpeg -i <visual.mp4> -i <audioSourceVideo.mp4> -map 0:v:0 -map 1:a:<selected-ordinal> -c:v copy -c:a copy <new-candidate.mp4>
```

Preserve metadata/disposition explicitly where needed and audit the actual command/result. Never add `-shortest`, audio filters, trimming, resampling or timestamp shifts. The audio packet hash must match exactly. Compare normalized timestamps, not raw integer ticks when container time bases differ.

## 6. Verify and promote

Run the complete [verification contract](verification-contract.md) on the immutable candidate. Numerical checks and visual/semantic review can run independently against that same file. A changed candidate invalidates affected evidence. Promote only after every gate passes and report its exact hash. An older report cannot certify a new encode.
