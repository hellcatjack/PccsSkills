import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import soundfile as sf


SKILL_ROOT = Path(__file__).parents[1]
CLI = SKILL_ROOT / "scripts" / "sermon_audio.py"


@pytest.fixture()
def clean_audio(tmp_path: Path) -> Path:
    sample_rate = 48000
    time = np.arange(sample_rate * 6, dtype=np.float64) / sample_rate
    source = tmp_path / "sermon.wav"
    sf.write(source, 0.03 * np.sin(2 * np.pi * 330 * time), sample_rate, subtype="FLOAT")
    return source


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def result_json(completed: subprocess.CompletedProcess[str]) -> dict:
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return json.loads(lines[-1])


def test_analyze_writes_all_audit_artifacts(clean_audio: Path):
    completed = run_cli("analyze", str(clean_audio))
    assert completed.returncode == 0, completed.stderr
    result = result_json(completed)
    work_dir = Path(result["work_dir"])
    assert result["status"] == "analyzed"
    assert (work_dir / "source_manifest.json").is_file()
    assert (work_dir / "analysis.json").is_file()
    assert (work_dir / "processing_plan.json").is_file()
    assert (work_dir / "run.json").is_file()


def test_restore_prints_machine_readable_json_for_non_ascii_paths(clean_audio: Path):
    output = clean_audio.with_name("讲道优化.wav")
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "cp1252"
    completed = subprocess.run(
        [sys.executable, str(CLI), "restore", str(clean_audio), "--output", str(output)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
    )

    assert completed.returncode == 0, completed.stderr
    result = result_json(completed)
    assert result["status"] == "verified"
    assert result["output"].endswith("讲道优化.wav")


def test_restore_promotes_only_a_verified_new_output(clean_audio: Path):
    output = clean_audio.with_name("sermon_audio_restored.wav")
    completed = run_cli("restore", str(clean_audio), "--output", str(output))
    assert completed.returncode == 0, completed.stderr
    result = result_json(completed)
    assert result["status"] == "verified"
    assert output.is_file()
    assert Path(result["verification_report"]).is_file()
    assert sf.info(output).frames == sf.info(clean_audio).frames


def test_force_ab_review_stops_before_formal_output(clean_audio: Path):
    output = clean_audio.with_name("review_should_not_exist.wav")
    completed = run_cli(
        "restore",
        str(clean_audio),
        "--output",
        str(output),
        "--force-ab-review",
    )
    assert completed.returncode == 2
    result = result_json(completed)
    assert result["status"] == "ab_review_required"
    assert not output.exists()
    assert result["ab_samples"]


def test_cloud_without_upload_consent_fails_before_processing(clean_audio: Path):
    completed = run_cli(
        "restore",
        str(clean_audio),
        "--cloud",
        "auphonic-free",
    )
    assert completed.returncode == 3
    assert result_json(completed)["status"] == "policy_rejected"


def test_source_path_cannot_be_the_output(clean_audio: Path):
    completed = run_cli(
        "restore",
        str(clean_audio),
        "--output",
        str(clean_audio),
    )
    assert completed.returncode == 3
    assert result_json(completed)["status"] == "policy_rejected"
