# Continue from a reviewed plan or A/B candidate

## Current CLI boundary

`restore` performs a new analysis and processing run. It does not consume an edited `processing_plan.json`, and it has no resume flag. Re-running it after A/B review recreates work and may return `ab_review_required` again. Do not invent a CLI option or set `requires_ab_review=False` merely to bypass review.

The standalone `verify` command probes a candidate but does not receive its lossless master or baseline. It therefore cannot alone certify the mandatory `lossless_latency` and `no_added_fades` checks. Require those named items in the complete report, rather than trusting an overall `verified` label with missing items.

## Supported module route

Use a small task-specific Python driver under `_work` with the installed skill's `scripts` on `sys.path`. The existing modules support the following route; this is not a built-in CLI resume command.

1. Load `source_manifest.json`, `processing_plan.json` and, after processing, `process_result.json` with `SourceManifest.from_dict`, `ProcessingPlan.from_dict` and `ProcessResult.from_dict` from `audio_pipeline.models`.
2. Recompute the original source hash and compare it with the saved manifest and plan. Bind the review record to exact source, plan, baseline, process-result and selected master hashes. Record reviewer, review intervals, observations and the decision. Recompute these hashes immediately before reusing the selected master; mismatches invalidate the review. A filename or an accepted older candidate is insufficient.
3. If AI review changes the automatically proposed processing plan, save a distinct reviewed plan with reasons before running it. Keep analysis/initial plan intact. Execute the reviewed local plan via `audio_pipeline.process.execute_plan(baseline, reviewed_plan, new_processing_dir)`. Cloud steps must use the existing guarded cloud adapter and explicit upload authorization; never send them directly through local execution.
   In all following steps, `plan` and `result` mean this final reviewed plan and its corresponding `ProcessResult`, including the reviewed loudness targets and repair intervals.
4. If an A/B master already exists, inspect all required source/candidate intervals and the opening/final edges. An accepted candidate can reuse `ProcessResult.master_path`; do **not** execute the same plan again. Missing review remains `REVIEW_REQUIRED`.
5. Before continuing, verify baseline/master/stage sample rate, channels and exact sample counts. Recheck each consecutive stage's edge-gain behavior with `audio_pipeline.integrity.assert_no_added_fades` and the final master against baseline. Require the originally saved commands and plan to remain available.
6. Create a new candidate under `_work`. For WAV delivery copy the selected lossless master. For video use `audio_pipeline.sync.remux_replacement_audio(source, master, manifest.stream_index, candidate, final_integrated_lufs=plan.target_lufs, final_true_peak_dbtp=plan.true_peak_dbtp)` so the established AAC calibration and non-target stream protections still apply. Use the existing encoder path for other supported audio containers; do not cut or retime audio.
7. Call `audio_pipeline.verify.verify_output(source, candidate, manifest, plan, master_path=master, reference_baseline=run_dir / 'baseline.wav')`. Save the full report. Require its normal contract **and the presence/pass of** `lossless_master_samples`, `lossless_latency` and `no_added_fades`.
8. Only after all checks pass, allocate a non-existing formal path, promote the candidate, verify the final file with the same master/baseline arguments, and report its hash. Preserve original media, prior outputs, plan/review evidence and the master. If verification fails, keep the candidate under `_work` and resolve the specific failure.

This route is exercised by the skill's reviewed-handoff test on synthetic audio. It does not prove that any real sermon has been listened to or that an optional restoration backend is available. The actual task still needs its own review and media evidence.
