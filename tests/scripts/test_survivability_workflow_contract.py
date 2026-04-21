from __future__ import annotations

from pathlib import Path


def test_executing_plans_invokes_survivability_before_finish() -> None:
    skill_text = Path("skills/executing-plans/SKILL.md").read_text()

    assert "Use resistance-engine:survivability" in skill_text
    assert skill_text.index("Use resistance-engine:survivability") < skill_text.index(
        "Use resistance-engine:finishing-a-development-branch"
    )


def test_subagent_driven_development_invokes_survivability_before_finish() -> None:
    skill_text = Path("skills/subagent-driven-development/SKILL.md").read_text()

    assert "Use resistance-engine:survivability" in skill_text
    assert '"Use resistance-engine:survivability"' in skill_text
    assert skill_text.index("Use resistance-engine:survivability") < skill_text.index(
        "Use resistance-engine:finishing-a-development-branch"
    )
    assert (
        '"Dispatch final code reviewer subagent for entire implementation" -> "Use resistance-engine:finishing-a-development-branch";'
        not in skill_text
    )
