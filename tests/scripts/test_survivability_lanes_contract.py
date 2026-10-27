from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = REPO_ROOT / "skills" / "survivability" / "SKILL.md"


def section(text: str, heading: str) -> str:
    assert heading in text, f"missing {heading}"
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_mutation_lane_skips_only_what_checkpoints_already_mutated() -> None:
    selection = section(SKILL_PATH.read_text(encoding="utf-8"), "## Lane Selection")

    assert "CHECKPOINT_REVIEW" in selection
    assert "every changed decision point" in selection
    assert "after the last checkpoint" in selection
    assert "uncovered-only" in selection
    assert "skipped" in selection
    for path in ("inline fast path", "executing-plans", "no checkpoints"):
        assert path in selection, path
    assert "chaos lane always runs" in selection


def test_first_slate_is_logged_and_survivors_mean_fail_then_hardened() -> None:
    log = section(SKILL_PATH.read_text(encoding="utf-8"), "## Review Log Submission")

    assert "--first-slate" in log
    assert "--mutation-lane" in log
    assert "--verdict FAIL" in log
    assert "FAIL -> hardened" in log
    assert "never log the hardened rerun as round 1" in log.lower()
