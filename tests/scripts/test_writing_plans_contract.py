from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = REPO_ROOT / "skills" / "writing-plans"
SKILL_PATH = PLANS_DIR / "SKILL.md"
REVIEWER_PATH = PLANS_DIR / "plan-document-reviewer-prompt.md"
EVIDENCE_PATH = PLANS_DIR / "alignment-check-evidence.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def task_template(skill_text: str) -> str:
    match = re.search(r"^## Task Structure\n(.*?)(?=\n## )", skill_text, re.DOTALL | re.MULTILINE)
    assert match, "missing Task Structure section"
    return match.group(1)


def test_plan_has_required_caller_and_test_sweep_table() -> None:
    skill_text = read(SKILL_PATH)

    assert "## Caller and test sweep" in skill_text
    assert "| Changed | Caller, test, fake, mock or assert | Kind | Task | Literal edit |" in skill_text
    for directory in ("scripts", "evals"):
        assert directory in skill_text.split("## Caller and test sweep")[1].split("\n## ")[0]


def test_every_task_names_tier_callers_reviewer_items_and_pinning() -> None:
    template = task_template(read(SKILL_PATH))

    assert "**Tier:** fast | standard | strong" in template
    assert "**Callers that move with this task:**" in template
    assert "**Reviewer looks at:**" in template
    assert "**Pinned by:**" in template


def test_sizing_is_by_rule_with_no_line_target() -> None:
    skill_text = read(SKILL_PATH)

    assert "## Sizing by rule" in skill_text
    sizing = skill_text.split("## Sizing by rule")[1].split("\n## ")[0]
    assert "one behaviour per task" in sizing
    assert "at most two entry paths" in sizing
    assert "never a target" in sizing
    assert "## Chunking and context protection" not in skill_text
    assert not re.search(r"\b\d[\d,]*[- ]line (cap|limit|target)", skill_text)


def test_trust_boundary_table_and_open_decisions_go_back_to_spec() -> None:
    skill_text = read(SKILL_PATH)

    assert "## Trust-boundary table" in skill_text
    assert "## Open decisions go back to the spec" in skill_text
    assert "amend" in skill_text.split("## Open decisions go back to the spec")[1].split("\n## ")[0]


def test_checkpoints_are_planned_for_the_execution_model() -> None:
    skill_text = read(SKILL_PATH)

    assert "## Checkpoints" in skill_text
    assert "| Checkpoint | After task | Tasks covered | Reviewer looks at |" in skill_text


def test_unified_coherence_check_is_renamed_to_alignment_check() -> None:
    assert EVIDENCE_PATH.exists()
    assert not (PLANS_DIR / "unified-coherence-check-evidence.md").exists()
    assert "## Alignment check" in read(SKILL_PATH)

    for path in [*REPO_ROOT.joinpath("skills").rglob("*.md"), REPO_ROOT / "README.md"]:
        assert "Unified Coherence" not in read(path), path


def test_reviewer_checks_per_task_rule_and_completeness_not_length() -> None:
    reviewer_text = read(REVIEWER_PATH)

    assert "Caller and test sweep" in reviewer_text
    assert "per-task rule" in reviewer_text
    assert "Never reject a plan for its length" in reviewer_text


def test_writing_plans_names_no_superpowers_paths() -> None:
    for path in PLANS_DIR.rglob("*.md"):
        assert "superpowers" not in read(path).lower(), path
