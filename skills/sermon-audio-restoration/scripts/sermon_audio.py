from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import soundfile as sf

from audio_pipeline.analyze import analyze_audio
from audio_pipeline.cloud import CloudProcessingError, run_auphonic_free
from audio_pipeline.decide import build_plan
from audio_pipeline.models import CloudRequest, ProcessResult, ProcessingPlan
from audio_pipeline.policy import PolicyError, assert_safe_command, assert_safe_output
from audio_pipeline.probe import ProbeError, extract_baseline, probe_source
from audio_pipeline.process import DependencyUnavailable, ProcessingError, execute_plan
from audio_pipeline.sync import remux_replacement_audio
from audio_pipeline.verify import verify_output


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".m4v"}


def _print_result(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")), flush=True)


def _tool_version(command: str) -> str:
    completed = subprocess.run(
        [command, "-version"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.splitlines()[0]


def _new_work_dir(source: Path, source_hash: str) -> Path:
    root = source.parent / "_work" / "audio-restoration"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = root / f"{stamp}-{source_hash[:8]}"
    candidate = base
    suffix = 1
    while candidate.exists():
        candidate = root / f"{base.name}-{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def _write_run_file(work_dir: Path, argv: list[str]) -> None:
    payload = {
        "argv": argv,
        "python": sys.version,
        "python_executable": sys.executable,
        "ffmpeg": _tool_version("ffmpeg"),
        "ffprobe": _tool_version("ffprobe"),
        "created_at": datetime.now().astimezone().isoformat(),
    }
    (work_dir / "run.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _analyze_source(
    source: Path,
    audio_stream: int | None,
    target_lufs: float,
    true_peak: float,
    cloud: str,
    argv: list[str],
):
    manifest = probe_source(source, audio_stream=audio_stream)
    work_dir = _new_work_dir(source, manifest.source_sha256)
    _write_run_file(work_dir, argv)
    manifest.write_json(work_dir / "source_manifest.json")
    baseline = extract_baseline(manifest, work_dir)
    analysis = analyze_audio(baseline, manifest)
    analysis.write_json(work_dir / "analysis.json")
    plan = build_plan(
        analysis,
        target_lufs=target_lufs,
        true_peak=true_peak,
        cloud=cloud,
    )
    plan.write_json(work_dir / "processing_plan.json")
    return manifest, work_dir, baseline, analysis, plan


def _default_output(source: Path, has_video: bool) -> Path:
    extension = source.suffix if has_video else ".wav"
    return source.with_name(f"{source.stem}_audio_restored{extension}")


def _encode_audio_candidate(master: Path, candidate: Path) -> None:
    suffix = candidate.suffix.casefold()
    if suffix == ".wav":
        shutil.copy2(master, candidate)
        return
    codec_by_suffix = {
        ".flac": "flac",
        ".mp3": "libmp3lame",
        ".m4a": "aac",
        ".aac": "aac",
    }
    codec = codec_by_suffix.get(suffix)
    if codec is None:
        raise ProcessingError(f"Unsupported formal audio extension: {candidate.suffix}")
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(master),
        "-c:a",
        codec,
        str(candidate),
    ]
    assert_safe_command(command)
    subprocess.run(command, check=True)


def _execute_with_optional_cloud(
    baseline: Path,
    plan: ProcessingPlan,
    work_dir: Path,
    *,
    allow_upload: bool,
) -> ProcessResult:
    cloud_steps = [step for step in plan.steps if step.tool == "auphonic-free"]
    if not cloud_steps:
        return execute_plan(baseline, plan, work_dir / "processing")

    local_steps = tuple(
        step
        for step in plan.steps
        if step.tool != "auphonic-free" and step.kind != "loudnorm"
    )
    local_plan = replace(
        plan,
        steps=local_steps,
        requires_ab_review=False,
        review_intervals=(),
    )
    local_result = execute_plan(baseline, local_plan, work_dir / "pre_cloud")
    local_master = Path(local_result.master_path)
    cloud_master = work_dir / "cloud_master.wav"
    cloud_request = CloudRequest(
        input_path=str(local_master),
        duration_hours=sf.info(local_master).duration / 3600.0,
        target_lufs=plan.target_lufs,
        true_peak_dbtp=plan.true_peak_dbtp,
        cloud_mode="auphonic-free",
        upload_consent=allow_upload,
        output_path=str(cloud_master),
    )
    run_auphonic_free(cloud_request)
    return ProcessResult(
        master_path=str(cloud_master),
        stage_paths=local_result.stage_paths + (str(cloud_master),),
        commands=local_result.commands + (("auphonic-free", "adaptive-leveler"),),
        stage_sample_counts=local_result.stage_sample_counts + (sf.info(cloud_master).frames,),
        ab_sample_paths=(),
    )


def _analyze_command(args: argparse.Namespace, argv: list[str]) -> int:
    manifest, work_dir, _baseline, analysis, plan = _analyze_source(
        args.input,
        args.audio_stream,
        args.target_lufs,
        args.true_peak,
        "off",
        argv,
    )
    _print_result(
        {
            "status": "analyzed",
            "work_dir": str(work_dir),
            "source_sha256": manifest.source_sha256,
            "integrated_lufs": analysis.integrated_lufs,
            "true_peak_dbtp": analysis.true_peak_dbtp,
            "requires_ab_review": plan.requires_ab_review,
        }
    )
    return 0


def _restore_command(args: argparse.Namespace, argv: list[str]) -> int:
    if args.cloud == "auphonic-free" and not args.allow_upload:
        raise PolicyError("--cloud auphonic-free requires explicit --allow-upload")

    source = args.input.resolve()
    tentative_output = args.output.resolve() if args.output else None
    if tentative_output is not None:
        assert_safe_output(source, tentative_output)

    manifest, work_dir, baseline, _analysis, plan = _analyze_source(
        source,
        args.audio_stream,
        args.target_lufs,
        args.true_peak,
        args.cloud,
        argv,
    )
    output = tentative_output or _default_output(source, bool(manifest.video_streams))
    assert_safe_output(source, output)

    if args.force_ab_review:
        intervals = plan.review_intervals or ((0.0, min(10.0, manifest.duration_seconds)),)
        plan = replace(plan, requires_ab_review=True, review_intervals=intervals)
        plan.write_json(work_dir / "processing_plan.json")

    result = _execute_with_optional_cloud(
        baseline,
        plan,
        work_dir,
        allow_upload=args.allow_upload,
    )
    result.write_json(work_dir / "process_result.json")
    if plan.requires_ab_review:
        _print_result(
            {
                "status": "ab_review_required",
                "work_dir": str(work_dir),
                "ab_samples": list(result.ab_sample_paths),
                "formal_output": None,
            }
        )
        return 2

    candidate = work_dir / f"candidate_output{output.suffix}"
    master = Path(result.master_path)
    if manifest.video_streams:
        remux_replacement_audio(
            source,
            master,
            manifest.stream_index,
            candidate,
            final_integrated_lufs=plan.target_lufs,
            final_true_peak_dbtp=plan.true_peak_dbtp,
        )
    else:
        _encode_audio_candidate(master, candidate)

    candidate_report = verify_output(
        source,
        candidate,
        manifest,
        plan,
        master_path=master,
        reference_baseline=baseline,
    )
    candidate_report.write_json(work_dir / "verification_candidate.json")
    if not candidate_report.passed:
        _print_result(
            {
                "status": "verification_failed",
                "work_dir": str(work_dir),
                "verification_report": str(work_dir / "verification_candidate.json"),
            }
        )
        return 5

    os.replace(candidate, output)
    final_report = verify_output(
        source,
        output,
        manifest,
        plan,
        master_path=master,
        reference_baseline=baseline,
    )
    verification_path = work_dir / "verification.json"
    final_report.write_json(verification_path)
    if not final_report.passed:
        failed_path = work_dir / f"failed_after_promotion{output.suffix}"
        os.replace(output, failed_path)
        _print_result(
            {
                "status": "verification_failed",
                "work_dir": str(work_dir),
                "verification_report": str(verification_path),
                "failed_media": str(failed_path),
            }
        )
        return 5

    _print_result(
        {
            "status": "verified",
            "work_dir": str(work_dir),
            "output": str(output),
            "verification_report": str(verification_path),
        }
    )
    return 0


def _verify_command(args: argparse.Namespace, argv: list[str]) -> int:
    source = args.against.resolve()
    manifest = probe_source(source, audio_stream=args.audio_stream)
    work_dir = _new_work_dir(source, manifest.source_sha256)
    _write_run_file(work_dir, argv)
    plan = ProcessingPlan(
        source_sha256=manifest.source_sha256,
        target_lufs=args.target_lufs,
        true_peak_dbtp=args.true_peak,
        steps=(),
        requires_ab_review=False,
        review_intervals=(),
        warnings=(),
    )
    report = verify_output(source, args.output.resolve(), manifest, plan)
    report_path = work_dir / "verification.json"
    report.write_json(report_path)
    _print_result(
        {
            "status": "verified" if report.passed else "verification_failed",
            "work_dir": str(work_dir),
            "verification_report": str(report_path),
        }
    )
    return 0 if report.passed else 5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Timeline-safe sermon audio restoration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("input", type=Path)
    analyze.add_argument("--audio-stream", type=int)
    analyze.add_argument("--target-lufs", type=float, default=-16.0)
    analyze.add_argument("--true-peak", type=float, default=-1.5)

    restore = subparsers.add_parser("restore")
    restore.add_argument("input", type=Path)
    restore.add_argument("--audio-stream", type=int)
    restore.add_argument("--target-lufs", type=float, default=-16.0)
    restore.add_argument("--true-peak", type=float, default=-1.5)
    restore.add_argument("--output", type=Path)
    restore.add_argument("--cloud", choices=("off", "auphonic-free"), default="off")
    restore.add_argument("--allow-upload", action="store_true")
    restore.add_argument("--force-ab-review", action="store_true")

    verify = subparsers.add_parser("verify")
    verify.add_argument("output", type=Path)
    verify.add_argument("--against", type=Path, required=True)
    verify.add_argument("--audio-stream", type=int)
    verify.add_argument("--target-lufs", type=float, default=-16.0)
    verify.add_argument("--true-peak", type=float, default=-1.5)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(raw_argv)
    try:
        if args.command == "analyze":
            return _analyze_command(args, raw_argv)
        if args.command == "restore":
            return _restore_command(args, raw_argv)
        return _verify_command(args, raw_argv)
    except PolicyError as error:
        _print_result({"status": "policy_rejected", "error": str(error)})
        return 3
    except (DependencyUnavailable, ProbeError) as error:
        _print_result({"status": "capability_failed", "error": str(error)})
        return 4
    except (ProcessingError, CloudProcessingError, subprocess.CalledProcessError) as error:
        _print_result({"status": "verification_failed", "error": str(error)})
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
