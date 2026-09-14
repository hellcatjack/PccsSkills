from pathlib import Path
import re


SKILL_ROOT = Path(__file__).resolve().parents[1]


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
        "references/camera-denoising.md",
        "references/gpt6-execution.md",
        "references/publication-assets.md",
        "scripts/plan_camera_processing.py",
        "scripts/validate_composition_plan.py",
        "scripts/build_dynamic_filter.py",
        "agents/openai.yaml",
    ):
        assert (SKILL_ROOT / relative).is_file(), relative


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
