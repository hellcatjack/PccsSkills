from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from subtitle_pipeline.alignment import retime_reviewed_cues
from subtitle_pipeline.compare import compare_srt
from subtitle_pipeline.media import create_run, extract_selected_audio
from subtitle_pipeline.srt import render_srt
from subtitle_pipeline.transcribe import run_transcription
from subtitle_pipeline.validation import validate_delivery


def _read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict, *, refuse_existing: bool = False) -> Path:
    path = Path(path).resolve()
    if refuse_existing and path.exists():
        raise FileExistsError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def _parse_asr(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("ASR source must use label=path")
    label, raw_path = value.split("=", 1)
    if not label.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("ASR source must use nonempty label=path")
    return label.strip(), Path(raw_path)


def _prepare(args: argparse.Namespace) -> int:
    result = create_run(
        args.video,
        pptx=args.pptx,
        audio_stream=args.audio_stream,
        work_root=args.work_root,
    )
    print(result["manifest_path"])
    return 0


def _transcribe(args: argparse.Namespace) -> int:
    manifest = _read_json(args.manifest)
    context = _read_json(args.context)
    run_dir = Path(manifest["run_dir"])
    extracted_audio = run_dir / "full_selected_audio.wav"
    if not extracted_audio.exists():
        extract_selected_audio(manifest, extracted_audio)
    output = args.output or run_dir / f"asr_{args.pass_name}.json"
    text_output = args.text_output or run_dir / f"asr_{args.pass_name}.txt"
    regions = None
    if args.regions:
        region_payload = _read_json(args.regions)
        regions = region_payload if isinstance(region_payload, list) else region_payload.get("regions", [])
    run_transcription(
        extracted_audio,
        output,
        pass_name=args.pass_name,
        context=context,
        model_name=args.model,
        model_dir=args.model_dir,
        allow_model_download=args.allow_model_download,
        regions=regions,
        output_text=text_output,
        timestamp_offset=float(manifest["selected_audio"].get("start_time") or 0.0),
    )
    print(str(Path(output).resolve()))
    return 0


def _align(args: argparse.Namespace) -> int:
    reviewed = _read_json(args.reviewed_cues)
    asr_sources = {label: _read_json(path) for label, path in args.asr}
    reviews: list[dict] | None = None
    if args.manual_reviews:
        review_payload = _read_json(args.manual_reviews)
        reviews = review_payload.get("reviews", [])
    result = retime_reviewed_cues(
        reviewed,
        asr_sources,
        reviews,
        low_ratio=args.low_ratio,
        shift_threshold=args.shift_threshold,
        max_overlap=args.max_overlap,
    )
    output = args.output or Path(args.reviewed_cues).with_name("aligned_cues.json")
    report = args.report or Path(args.reviewed_cues).with_name("alignment_report.json")
    _write_json(output, result, refuse_existing=True)
    _write_json(report, result, refuse_existing=True)
    print(str(Path(output).resolve()))
    print(str(Path(report).resolve()))
    return 0


def _render(args: argparse.Namespace) -> int:
    payload = _read_json(args.aligned_cues)
    context = _read_json(args.context) if args.context else {}
    if args.output:
        output = Path(args.output).resolve()
    elif args.manifest:
        output = Path(_read_json(args.manifest)["formal_output"]).resolve()
    else:
        raise ValueError("render requires --output or --manifest")
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_srt(
            payload["cues"],
            width=18,
            protected_terms=context.get("protected_terms", []),
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(str(output))
    return 0


def _compare(args: argparse.Namespace) -> int:
    report = compare_srt(
        args.before,
        args.after,
        allow_resegmentation=args.allow_resegmentation,
    )
    if args.report:
        _write_json(args.report, report, refuse_existing=True)
        print(str(Path(args.report).resolve()))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _validate(args: argparse.Namespace) -> int:
    config = {
        "srt_path": args.srt,
        "cues_path": args.cues,
        "alignment_report_path": args.alignment_report,
        "boundary_reviews_path": args.boundary_reviews,
        "context_path": args.context,
        "video_duration": args.video_duration,
        "video_path": args.video,
        "manifest_path": args.manifest,
        "scripture_reference_path": args.scripture_reference,
    }
    report = validate_delivery(config)
    report_path = _write_json(args.report, report)
    print(str(report_path))
    print(
        json.dumps(
            {
                "status": report["status"],
                "cue_count": report["cue_count"],
                "hard_failures": report["hard_failures"],
                "missing_boundary_reviews": len(report["missing_boundary_reviews"]),
            },
            ensure_ascii=False,
        )
    )
    return {"PASS": 0, "FAIL": 1, "REVIEW_REQUIRED": 2}[report["status"]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, align, render, compare, and validate high-precision Chinese sermon subtitles"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="freeze an explicitly specified sermon video")
    prepare.add_argument("video", type=Path)
    prepare.add_argument("--pptx", type=Path)
    prepare.add_argument("--audio-stream", type=int, help="zero-based audio ordinal")
    prepare.add_argument("--work-root", type=Path)
    prepare.set_defaults(handler=_prepare)

    transcribe = subparsers.add_parser("transcribe", help="run one local word-timestamp ASR pass")
    transcribe.add_argument("manifest", type=Path)
    transcribe.add_argument("--pass", dest="pass_name", required=True, choices=["primary", "precision", "regional"])
    transcribe.add_argument("--context", required=True, type=Path)
    transcribe.add_argument("--regions", type=Path)
    transcribe.add_argument("--output", type=Path)
    transcribe.add_argument("--text-output", type=Path)
    transcribe.add_argument("--model", default="large-v3")
    transcribe.add_argument("--model-dir", type=Path)
    transcribe.add_argument("--allow-model-download", action="store_true")
    transcribe.set_defaults(handler=_transcribe)

    align = subparsers.add_parser("align", help="align AI-reviewed cues to observed ASR boundaries")
    align.add_argument("reviewed_cues", type=Path)
    align.add_argument("--asr", action="append", required=True, type=_parse_asr, metavar="LABEL=PATH")
    align.add_argument("--manual-reviews", type=Path)
    align.add_argument("--output", type=Path)
    align.add_argument("--report", type=Path)
    align.add_argument("--low-ratio", type=float, default=0.65)
    align.add_argument("--shift-threshold", type=float, default=1.0)
    align.add_argument("--max-overlap", type=float, default=0.8)
    align.set_defaults(handler=_align)

    render = subparsers.add_parser("render", help="render aligned cues as a non-overwriting SRT")
    render.add_argument("aligned_cues", type=Path)
    render.add_argument("--context", type=Path)
    render.add_argument("--manifest", type=Path)
    render.add_argument("--output", type=Path)
    render.set_defaults(handler=_render)

    compare = subparsers.add_parser("compare", help="quantify timing changes between two SRT files")
    compare.add_argument("before", type=Path)
    compare.add_argument("after", type=Path)
    compare.add_argument("--allow-resegmentation", action="store_true")
    compare.add_argument("--report", type=Path)
    compare.set_defaults(handler=_compare)

    validate = subparsers.add_parser("validate", help="enforce format, timing evidence, semantics, and hashes")
    validate.add_argument("--srt", required=True, type=Path)
    validate.add_argument("--cues", required=True, type=Path)
    validate.add_argument("--alignment-report", required=True, type=Path)
    validate.add_argument("--boundary-reviews", required=True, type=Path)
    validate.add_argument("--context", required=True, type=Path)
    validate.add_argument("--video", type=Path)
    validate.add_argument("--video-duration", type=float)
    validate.add_argument("--manifest", type=Path)
    validate.add_argument("--scripture-reference", type=Path)
    validate.add_argument("--report", required=True, type=Path)
    validate.set_defaults(handler=_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
