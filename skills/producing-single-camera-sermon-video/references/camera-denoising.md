# Camera-only denoising

## Scope and quality decision

Use the original same-take camera picture after proving its timeline matches the locked audio-source video. Keep the audio master untouched. PPT, scripture, graphics and cover images bypass every camera denoiser. Do not apply a denoising filter after final composition.

Inspect native source crops and actual delivery-size motion clips. Distinguish random sensor/chroma noise, compression, defocus and motion blur. Denoising cannot restore absent optical detail. Preserve facial identity, skin texture, eyes, hands, microphone and lectern edges; do not generate face/detail replacements. A stationary wall blemish is not temporal noise and does not justify a blanket removal filter.

## Spend work on the actual visible picture

1. Lock the composition and a fixed crop from this recording. Crop first, then downscale to the largest size at which the pastor will actually appear, using a high-quality uniform scaler. For the inset preset, that is 600×684, not the complete 3840×2160 frame. If the pastor will appear larger elsewhere, use that larger size or a separately verified branch.
2. Freeze the output-frame timebase. Run `plan_camera_processing.py` with the combined temporal context radius. It omits only fully hidden frames, preserves fade ramps and includes the final visible frame. It merges overlapping decode contexts but retains distinct visible output ranges.
3. Reuse already cut clips only when their exact global frame ranges, crop, resolution and provenance are known. Retain context frames from the original neighboring timeline; a tightly cut clip without temporal handles cannot be denoised as if it were an independent scene.
4. Process with a bounded sliding window. Keep the output corresponding to each **center frame**, then discard context-only outputs by index. Clamp/reflect at true recording boundaries according to the chosen model; do not replicate artificial chunk edges where real neighboring frames exist.
5. Reconstruct a full-length silent panel stream at its absolute frame indexes. Fill omitted hidden intervals cheaply, for example with black frames. Never concatenate visible cores back-to-back: this shifts every later picture against the fixed audio. Gaps must be exactly the originally hidden frame ranges, including any zero-opacity boundary frame.

The planner's `[start,end)` ranges are **output** frames. If source fps differs from 30, either normalize the cropped silent picture to the verified output timeline first, or implement an explicit source-frame mapping and temporal-context conversion. Do not treat 29.97/60 source frames as 30 fps frames by changing timestamps.

## Bounded candidate comparison

Choose two or three short regions with dim flat surfaces, face detail and moving hands/head; typically 6–12 seconds each. Compare at equal size, time, color conversion and encoding quality:

- crop/downscale only as the baseline;
- a conservative supported temporal/non-local denoiser;
- a pretrained multi-frame method when the baseline remains poor.

FastDVDnet is a tested candidate family, not a universal winner. Its five-frame center-frame model and implementation are documented in the [authors' repository](https://github.com/m-tassano/fastdvdnet) and [CVPR paper](https://openaccess.thecvf.com/content_CVPR_2020/papers/Tassano_FastDVDnet_Towards_Real-Time_Deep_Video_Denoising_Without_Flow_Estimation_CVPR_2020_paper.pdf). Use trustworthy matching weights and record their hash, variant, input normalization and noise parameter units. Bracket a few mild strengths; never copy the prior recording's selected sigma blindly. A mild additional temporal stage is justified only when motion comparison demonstrates benefit.

For a five-frame model followed by a centered nine-frame temporal filter, context radius is 2+4=6 output frames on each side. Other networks, chained passes, recurrent state or fps conversions require their own context calculation. The helper does not infer model radius, install weights or perform neural inference.

Record actual frames/second, memory peak, startup time and expected total work after warm-up. Inspect motion for trails, ghost faces, skin smoothing, waxy hands, flicker and edge loss. A flat-wall noise statistic can support a local result; it cannot establish whole-frame sharpness or overall improvement. Do not explore many expensive full-resolution variants after a clear acceptable candidate is found.

## Runtime and reuse

- Use an isolated environment; record dependency versions, model hashes and device/provider. Check the actual execution provider and a small inference profile; an installed GPU package is not proof of GPU execution. Verify CUDA/cuDNN compatibility using [ONNX Runtime CUDA documentation](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html).
- Test FP16 against a FP32 sample before using it. Where implementing FastDVDnet's staged pipeline, cache overlapping first-stage results and confirm cached outputs match the uncached graph on a test clip. Fall back visibly if the backend cannot meet quality or memory needs.
- Keep the source decoder, rolling inference buffers and silent panel encoder streaming. Avoid writing all 4K frames to disk or keeping the sermon in RAM. Do not run competing GPU ASR and denoising jobs merely to claim parallelism.
- Cache by picture-source hash, frame mapping, global frame ranges, crop, scale/color operations, model/weight hashes, precision, parameters and context policy. A layout/crop change invalidates dependent camera results; a title/description edit does not.
- Save each completed chunk atomically with frame count, range, hash and decode result. Resume only validated matching chunks. A nonempty output file or an encoder progress value is not completion evidence.

Use a lossless or visually verified high-quality panel intermediate and encode the final composite once. In `cameraInput.mode: processed-panel`, the panel has the exact declared dimensions, complete timeline and no audio; the compositor must not crop or denoise it again.

## Required evidence

Save source/candidate motion comparisons, chosen parameters with reasons, performance measurements, source-role mapping, core/context ranges and frame assembly checks. Inspect every processed-chunk re-entry for temporal seams. In final verification compare the visible pastor viewport with the selected processed reference, and compare PPT separately with native slides. Do not test a pastor panel that is intentionally covered by full-screen PPT or mistake expected denoising differences for a crop error.
