from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import SCRIPTS_DIR


CLI = SCRIPTS_DIR / "sermon_subtitles.py"


def test_help_lists_the_six_workflow_commands() -> None:
    completed = subprocess.run(
        [sys.executable, str(CLI), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 0, completed.stderr
    for command in ("prepare", "transcribe", "align", "render", "compare", "validate"):
        assert command in completed.stdout


def test_render_writes_lf_srt_and_refuses_overwrite(tmp_path) -> None:
    cues = tmp_path / "aligned.json"
    cues.write_text(
        json.dumps(
            {
                "video_duration": 5.0,
                "language": "zh-Hans",
                "cues": [
                    {"id": "c1", "start": 0.2, "end": 2.0, "text": "尼希米修造城墙。"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    context = tmp_path / "context.json"
    context.write_text(
        json.dumps({"protected_terms": ["尼希米", "城墙"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    output = tmp_path / "final.srt"

    first = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "render",
            str(cues),
            "--context",
            str(context),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    second = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "render",
            str(cues),
            "--context",
            str(context),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert first.returncode == 0, first.stderr
    assert output.read_bytes().startswith(b"1\n00:00:00,200")
    assert b"\r\n" not in output.read_bytes()
    assert second.returncode == 1
    assert "already exists" in second.stderr


def test_validate_uses_exit_code_two_for_missing_reviews(tmp_path) -> None:
    srt = tmp_path / "sermon.srt"
    srt.write_text("1\n00:00:00,500 --> 00:00:01,500\n测试\n", encoding="utf-8", newline="\n")
    cues = tmp_path / "cues.json"
    cues.write_text(
        json.dumps(
            {
                "video_duration": 2.0,
                "cues": [{"id": "c1", "start": 0.5, "end": 1.5, "text": "测试"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    alignment = tmp_path / "alignment.json"
    alignment.write_text(
        json.dumps(
            {
                "observed_boundaries": [0.5, 1.5],
                "risks": [{"cue_id": "c1", "reason": "first_cue", "detail": {}}],
            }
        ),
        encoding="utf-8",
    )
    reviews = tmp_path / "reviews.json"
    reviews.write_text('{"reviews": []}', encoding="utf-8")
    context = tmp_path / "context.json"
    context.write_text('{"required_terms": [], "forbidden_terms": []}', encoding="utf-8")
    report = tmp_path / "report.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "validate",
            "--srt",
            str(srt),
            "--cues",
            str(cues),
            "--alignment-report",
            str(alignment),
            "--boundary-reviews",
            str(reviews),
            "--context",
            str(context),
            "--video-duration",
            "2.0",
            "--report",
            str(report),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 2, completed.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "REVIEW_REQUIRED"
    assert payload["hard_failures"] == 0
