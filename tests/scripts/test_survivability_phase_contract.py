from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
PHASE_4_HEADING = "## Lifecycle Phase 4: Resilience & Mutation Testing"


def _phase_4_section() -> str:
    agents_text = AGENTS_PATH.read_text()
    start = agents_text.index(PHASE_4_HEADING)
    end = agents_text.find("\n## ", start + len(PHASE_4_HEADING))
    if end == -1:
        end = len(agents_text)
    return agents_text[start:end]


def test_agents_phase4_points_to_survivability_skill() -> None:
    phase_4_text = _phase_4_section()

    assert phase_4_text.startswith(PHASE_4_HEADING)
    assert "Use the `survivability` skill" in phase_4_text
    assert "3 representative probes" in phase_4_text
    assert "capped at 5 total" in phase_4_text
    assert "1 chaos probe minimum for local-only changes" in phase_4_text
    assert "2 for dependency-touching changes" in phase_4_text
    assert "capped at 3 total" in phase_4_text


def test_agents_phase4_preserves_review_log_and_retrospective_handoff() -> None:
    phase_4_text = _phase_4_section()

    assert phase_4_text.startswith(PHASE_4_HEADING)
    assert "Survivability Score" in phase_4_text
    assert "CRITICAL FRICTION" in phase_4_text
    assert ".review_log.jsonl" in phase_4_text
