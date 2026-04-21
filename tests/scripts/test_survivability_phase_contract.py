from __future__ import annotations

from pathlib import Path


def test_agents_phase4_points_to_survivability_skill() -> None:
    agents_text = Path("AGENTS.md").read_text()

    assert "Use the `survivability` skill" in agents_text
    assert "3 representative probes" in agents_text
    assert "2 for dependency-touching changes" in agents_text


def test_agents_phase4_preserves_review_log_and_retrospective_handoff() -> None:
    agents_text = Path("AGENTS.md").read_text()

    assert "Survivability Score" in agents_text
    assert "CRITICAL FRICTION" in agents_text
    assert ".review_log.jsonl" in agents_text
