from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = REPO_ROOT / "AGENTS.md"


def test_agents_does_not_inline_survivability_phase_contract() -> None:
    agents_text = AGENTS_PATH.read_text()

    assert "## Lifecycle Phase 4: Resilience & Mutation Testing" not in agents_text
    assert "3 representative probes for a small change" not in agents_text
    assert "2 for dependency-touching changes" not in agents_text
    assert 'Record the "Survivability Score" in your Phase 6 Retrospective.' not in agents_text


def test_agents_does_not_inline_survivability_score_language() -> None:
    agents_text = AGENTS_PATH.read_text()

    assert 'Record the "Survivability Score" in your Phase 6 Retrospective.' not in agents_text
    assert 'Log any "survived mutations" as CRITICAL FRICTION' not in agents_text
