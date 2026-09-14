"""Exercise the documented existing-module handoff without repeating restore."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf

from audio_pipeline.integrity import assert_no_added_fades
from audio_pipeline.models import SourceManifest, ProcessingPlan, ProcessResult
from audio_pipeline.verify import verify_output


def test_reviewed_master_can_be_verified_without_reprocessing(tmp_path):
    sample_rate = 48000
    time = np.arange(sample_rate * 6, dtype=np.float64) / sample_rate
    source = tmp_path / "source.wav"
    sf.write(source, .03 * np.sin(2 * np.pi * 330 * time), sample_rate, subtype="FLOAT")
    cli = Path(__file__).resolve().parents[1] / "scripts/sermon_audio.py"
    process = subprocess.run([sys.executable, str(cli), "restore", str(source),
                              "--force-ab-review"], capture_output=True, text=True,
                             encoding="utf-8", timeout=60)
    assert process.returncode == 2, process.stderr
    run_dir = Path(json.loads(process.stdout.splitlines()[-1])["work_dir"])

    def record(name, kind):
        return kind.from_dict(json.loads((run_dir / name).read_text(encoding="utf-8")))

    manifest = record("source_manifest.json", SourceManifest)
    plan = record("processing_plan.json", ProcessingPlan)
    result = record("process_result.json", ProcessResult)
    master, baseline = Path(result.master_path), run_dir / "baseline.wav"
    assert plan.requires_ab_review  # no flag manipulation to unblock the API
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest.source_sha256
    master_hash = hashlib.sha256(master.read_bytes()).hexdigest()
    stage_hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in result.stage_paths}
    previous = baseline
    for stage in result.stage_paths:
        assert sf.info(stage).frames == manifest.decoded_sample_count
        assert_no_added_fades(previous, Path(stage))
        previous = Path(stage)
    candidate = run_dir / "reviewed_candidate.wav"
    shutil.copy2(master, candidate)
    report = verify_output(source, candidate, manifest, plan,
                           master_path=master, reference_baseline=baseline)
    assert report.passed, report.to_dict()
    items = {item.name: item for item in report.items}
    for name in ("lossless_master_samples", "lossless_latency", "no_added_fades"):
        assert name in items and items[name].passed, report.to_dict()
    assert hashlib.sha256(master.read_bytes()).hexdigest() == master_hash
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in stage_hashes.items())
