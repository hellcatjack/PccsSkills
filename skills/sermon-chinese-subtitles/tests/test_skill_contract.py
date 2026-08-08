from __future__ import annotations

from conftest import SKILL_DIR


def test_skill_instruction_contract_covers_semantic_and_timing_gates() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    required = [
        "explicitly specified",
        "two complete",
        "word timestamps",
        "regional",
        "Hong Kong",
        "actually spoken",
        "0.65",
        "1.0 second",
        "REVIEW_REQUIRED",
        "SHA-256",
        "never overwrite",
        "_YouTube简体中文字幕_高精度校订版.srt",
    ]
    missing = [phrase for phrase in required if phrase not in skill]
    assert not missing, f"SKILL.md is missing required workflow gates: {missing}"


def test_all_referenced_contract_documents_exist_and_are_linked() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    names = [
        "workflow-contract.md",
        "semantic-review-policy.md",
        "verification-contract.md",
        "artifact-schemas.md",
    ]
    missing_files = [name for name in names if not (SKILL_DIR / "references" / name).is_file()]
    missing_links = [name for name in names if f"references/{name}" not in skill]
    assert not missing_files, f"missing reference files: {missing_files}"
    assert not missing_links, f"SKILL.md does not link references: {missing_links}"


def test_production_instructions_do_not_hardcode_prior_sermon() -> None:
    production_files = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "scripts" / "subtitle_pipeline" / "transcribe.py",
        SKILL_DIR / "scripts" / "subtitle_pipeline" / "validation.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in production_files)
    for forbidden in ("20260802", "于成龙", "帕麦斯顿", "朱仙镇"):
        assert forbidden not in combined
