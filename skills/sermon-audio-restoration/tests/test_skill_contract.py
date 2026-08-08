from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def test_skill_metadata_and_required_resources():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata_path = ROOT / "agents" / "openai.yaml"

    assert "description: Use when" in skill
    assert len(skill.splitlines()) < 500
    assert metadata_path.is_file()

    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    interface = metadata["interface"]
    assert 25 <= len(interface["short_description"]) <= 64
    assert "$sermon-audio-restoration" in interface["default_prompt"]

    references = {}
    for name in (
        "decision-policy.md",
        "verification-contract.md",
        "dependencies.md",
    ):
        path = ROOT / "references" / name
        assert path.is_file()
        references[name] = path.read_text(encoding="utf-8")

    required_skill_terms = (
        "SHA-256",
        "full-file",
        "AI review",
        "A/B",
        "-16 LUFS",
        "-1.5 dBTP",
        "zero latency",
        "stream copy",
        "verification fails",
    )
    for term in required_skill_terms:
        assert term in skill

    prohibited_timeline_changes = (
        "atrim",
        "silenceremove",
        "-shortest",
        "atempo",
    )
    for term in prohibited_timeline_changes:
        assert term in skill

    assert "Do not deliver" in skill
    assert "decision-policy.md" in skill
    assert "verification-contract.md" in skill
    assert "dependencies.md" in skill

    combined_references = "\n".join(references.values())
    for required in (
        "issue",
        "detection",
        "repair",
        "fallback",
        "exact sample count",
        "non-target stream",
        "FFmpeg",
        "DeepFilterNet",
        "NARA-WPE",
        "Silero VAD",
        "Auphonic",
    ):
        assert required.lower() in combined_references.lower()

    # The main workflow belongs in SKILL.md; references must remain lookup material.
    for content in references.values():
        assert "## Initial workflow" not in content
