# Production workflow

## 1. Inventory and preserve sources

Enumerate the task directory and resolve exactly one input video and one PPTX. Do not select a separate audio file: the input video's embedded audio is already the finished audio master. Probe every media stream and record SHA-256 before work. Keep sources and previous formal outputs immutable; place generated material under the task `_work` directory.

## 2. Lock the input-video audio

The input video's audio stream is the sole authoritative formal audio. The same input video supplies the camera picture, timing reference, and final audio packets.

- Audio may be decoded only for transcription and timing analysis; extracted WAV, PCM, AAC, proxy, or speech-recognition files are analysis evidence only and must never be muxed into the deliverable.
- Do not search for, align, substitute, or prefer any external audio recording.
- Do not invoke `replacing-video-audio-track` or `sermon-audio-restoration`.
- If the embedded audio is missing, wrong, damaged, out of sync, or unsupported for direct MP4 stream copy, stop and request a newly audio-treated input video.

Never use `atrim`, `asetpts`, `adelay`, `apad`, resampling compensation, channel remixing, normalization, compression, limiting, restoration, denoising, dereverberation, declipping, fades, or an audio encoder anywhere in this workflow. Never change audio timestamps, start time, duration, sample rate, channel layout, metadata, or packet payloads.

## 3. Read the sermon and presentation

Use `presentations:Presentations`. Extract all visible text, notes, masters/layouts, page order, dimensions, media, and animation sequences. Render reference PNGs for every final slide state.

Create a complete transcript with paragraph and word timing. Correct scripture, names, and church terms from the PPT and Bible context. Read the complete transcript; programmatic search only locates evidence.

Build page boundaries at the first sentence that genuinely enters the page's topic. Trigger an animation when its object is first explicitly introduced. Preserve `With Previous`, `After Previous`, delays, durations, and effect order.

## 4. Build the composition plan

The JSON plan contains:

- `duration`, `fps`, and `expectedFrames`;
- intro and transition durations;
- source/canvas/crop geometry in `layout`;
- one `pptSegments` entry per page instance with `slide`, source range, target range, and `reason`;
- semantic `fullScreenBlocks`, each with `start`, `end`, and `reason`;
- an `endingCover` boundary using `left-cover-right-pastor`.

The source ranges refer to the PowerPoint native video. The target ranges cover the complete sermon continuously, including every repeated page instance.

Validate before encoding:

```powershell
python scripts/validate_composition_plan.py <plan.json>
python scripts/build_dynamic_filter.py --plan <plan.json> --output <filter.txt>
```

These tools validate and render declared decisions. They never choose the decisions.

## 5. Render PowerPoint

Write timings only into a copy of the PPTX, reopen it, and re-read the saved settings. Use Microsoft PowerPoint `CreateVideo` for PowerPoint native animation, transitions, fonts, and layout. Target 1920×1080 at constant 30 fps. If the deck repeats, make the native source contain or expose every required page instance with its correct background.

If the deck has no animation, a static alternative is allowed only after every page render matches the source. Static rendering is never a fallback for an animated deck.

## 6. Compose video

The generated filter expects:

- input 0: timed PPT video;
- input 1: camera video;
- input 2: a duration-matched cover clip derived from the authentic first slide.

Map only `[outv]` into the visual intermediate. Encode H.264, 1920×1080, constant 30 fps, `yuv420p`, with exactly `expectedFrames`. Use a high-quality source or lossless intermediate; do not repeatedly transcode an earlier compressed deliverable.

## 7. Mux the immutable input-video audio

Add audio only after the visual program passes a probe. Map the visual stream from the composition and map the audio stream from the same input video used throughout the task. Use `-c:a copy` without an audio filter, audio encoder, or timestamp transform. Never add `-shortest`; preserve every source audio packet, start time, language tag, disposition, metadata, and the complete ending.

A representative final-mux shape is:

```powershell
ffmpeg -i <visual-intermediate.mp4> -i <input-video.mp4> -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy <new-output.mp4>
```

Record the executed command. The audit must prove that input 1 is the original task video, that `1:a:0` is the mapped audio, and that no command before or during final mux modifies the audio.
