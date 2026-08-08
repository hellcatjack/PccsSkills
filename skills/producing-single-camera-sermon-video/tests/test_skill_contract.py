from pathlib import Path
import re


SKILL_ROOT = Path(__file__).resolve().parents[1]


def test_skill_contract_uses_presentation_capability_and_forbids_audio_subskills():
    skill = SKILL_ROOT / "SKILL.md"
    assert skill.is_file()
    text = skill.read_text(encoding="utf-8")
    assert "presentations:Presentations" in text
    assert (
        "Do not invoke `replacing-video-audio-track` or "
        "`sermon-audio-restoration`."
    ) in text


def test_audio_is_an_immutable_input_video_stream_with_no_fallback():
    paths = (
        SKILL_ROOT / "SKILL.md",
        SKILL_ROOT / "references" / "production-workflow.md",
        SKILL_ROOT / "references" / "verification-contract.md",
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    required = (
        "The input video's audio stream is the sole authoritative formal audio.",
        "Audio may be decoded only for transcription and timing analysis",
        "map the audio stream from the same input video",
        "audio packet hash must match exactly",
        "No PCM-hash fallback",
        "stop and request a newly audio-treated input video",
    )
    for token in required:
        assert token in combined, token

    obsolete_permissions = (
        "Longer or shifted external recording",
        "Audio repair requested",
        "unless a separate audio task says otherwise",
        "unless a separately authorized audio workflow requires it",
        "When unchanged audio was requested",
        "If container repacketization",
    )
    for token in obsolete_permissions:
        assert token not in combined, token


def test_frontmatter_is_trigger_only_and_discoverable():
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    assert match is not None
    assert match.group(1).startswith("Use when ")
    assert "fixed-camera" in match.group(1)
    assert "PPTX" in match.group(1)


def test_required_references_and_tools_exist():
    for relative in (
        "references/composition-policy.md",
        "references/production-workflow.md",
        "references/verification-contract.md",
        "scripts/validate_composition_plan.py",
        "scripts/build_dynamic_filter.py",
        "agents/openai.yaml",
    ):
        assert (SKILL_ROOT / relative).is_file(), relative


def test_contract_covers_semantic_visual_audio_and_verification_rules():
    paths = [SKILL_ROOT / "SKILL.md", *sorted((SKILL_ROOT / "references").glob("*.md"))]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    required = (
        "complete transcript",
        "PowerPoint native",
        "fixed crop",
        "full-screen",
        "second pass",
        "left-cover-right-pastor",
        "stream copy",
        "packet hash",
        "full decode",
        "composition preview",
    )
    for token in required:
        assert token in combined, token


def test_production_resources_have_no_placeholders_or_old_task_constants():
    resources = [
        SKILL_ROOT / "SKILL.md",
        *sorted((SKILL_ROOT / "references").glob("*.md")),
        *sorted((SKILL_ROOT / "scripts").glob("*.py")),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in resources)
    assert "TODO" not in combined
    assert "TBD" not in combined
    assert "20260802" not in combined


def test_ui_metadata_invokes_the_skill_explicitly():
    text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "$producing-single-camera-sermon-video" in text
