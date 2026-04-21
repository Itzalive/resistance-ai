from __future__ import annotations

from pathlib import Path


def _section_text(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = text.index(marker) + len(marker)
    rest = text[start:]
    next_heading = rest.find("\n## ")
    if next_heading == -1:
        return rest
    return rest[:next_heading]


def test_survivability_skill_defines_bounded_mutation_slate() -> None:
    skill_text = Path("skills/survivability/SKILL.md").read_text()

    mutation_lane = _section_text(skill_text, "Mutation Probe Lane")

    assert "3 representative probes" in mutation_lane
    assert "capped at 5 total" in mutation_lane
    assert "meaningful decision point" in mutation_lane
    assert "route the work back to implementation hardening" in mutation_lane


def test_survivability_skill_defines_chaos_thresholds() -> None:
    skill_text = Path("skills/survivability/SKILL.md").read_text()

    chaos_lane = _section_text(skill_text, "Chaos Probe Lane")

    assert "For local-only changes, run 1 chaos probe minimum." in chaos_lane
    assert "For dependency-touching changes, run 2 chaos probes minimum" in chaos_lane
    assert "capped at 3 total" in chaos_lane
    assert "abort/restore steps" in chaos_lane
    assert "route the work back to implementation hardening" in chaos_lane


def test_survivability_skill_uses_generic_review_log_contract() -> None:
    skill_text = Path("skills/survivability/SKILL.md").read_text()

    review_log = _section_text(skill_text, "Review Log Submission")

    assert ".review_log.jsonl" in review_log
    assert "bounded experiment summary" in review_log
    assert "generic append template" in review_log
    assert "survivability score" in review_log
