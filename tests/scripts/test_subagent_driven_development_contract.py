from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SDD_DIR = REPO_ROOT / "skills" / "subagent-driven-development"
SKILL_PATH = SDD_DIR / "SKILL.md"
IMPLEMENTER_PATH = SDD_DIR / "implementer-prompt.md"
CHECKPOINT_PATH = SDD_DIR / "checkpoint-reviewer-prompt.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    assert heading in text, f"missing {heading}"
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_per_task_two_stage_review_is_gone() -> None:
    assert not (SDD_DIR / "spec-reviewer-prompt.md").exists()
    assert not (SDD_DIR / "code-quality-reviewer-prompt.md").exists()
    skill_text = read(SKILL_PATH)
    assert "two-stage review" not in skill_text.lower()
    assert "TodoWrite" not in skill_text
    for path in REPO_ROOT.joinpath("skills").rglob("*.md"):
        text = read(path)
        assert "spec-reviewer-prompt.md" not in text, path
        assert "code-quality-reviewer-prompt.md" not in text, path


def test_executor_tier_comes_from_the_plan_with_escalation() -> None:
    tiers = section(read(SKILL_PATH), "## Tiered executors")

    assert "**Tier:**" in tiers
    assert "fast" in tiers and "standard" in tiers and "strong" in tiers
    assert "Two failed attempts" in tiers
    assert "one tier up" in tiers


def test_checkpoint_reviewer_mutates_every_reviewer_looks_at_item() -> None:
    checkpoint_text = read(CHECKPOINT_PATH)

    assert "Reviewer looks at" in checkpoint_text
    assert "git archive HEAD | tar -x" in checkpoint_text
    assert "killed" in checkpoint_text and "survived" in checkpoint_text
    assert "verified test code" in checkpoint_text
    assert "deviation" in checkpoint_text
    skill_text = read(SKILL_PATH)
    assert "same reviewer" in section(skill_text, "## Checkpoint reviews")
    assert "--phase CHECKPOINT_REVIEW" in skill_text


def test_plan_end_runs_suites_then_code_review_then_survivability() -> None:
    plan_end = section(read(SKILL_PATH), "## Plan end")

    suites = plan_end.index("full suites")
    review = plan_end.index("requesting-code-review")
    survivability = plan_end.index("survivability")
    assert suites < review < survivability


def test_implementer_prompt_carries_executor_hygiene_rules() -> None:
    implementer_text = read(IMPLEMENTER_PATH)

    hygiene = section(implementer_text, "## Hygiene rules")
    assert "git stash" in hygiene
    assert "heredoc" in hygiene
    assert "RED" in hygiene
    assert "between" in hygiene
    assert "after committing" in hygiene


def test_coordinator_rules_and_inline_fast_path_are_named() -> None:
    skill_text = read(SKILL_PATH)

    coordinator = section(skill_text, "## Coordinator rules")
    assert "small verified fix" in coordinator
    assert "Resume" in coordinator

    fast_path = section(skill_text, "## Inline fast path")
    assert "three tasks or fewer" in fast_path
    assert "no trust-boundary change" in fast_path
    assert "mutation" in fast_path
