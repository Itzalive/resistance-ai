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


def test_brainstorming_quick_reference_blocks_one_shot_designs() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    quick_reference = _section_text(skill_text, "Quick Reference")

    assert (
        "Before the first approved section, output only `## Assumptions surface` or blockers, then stop."
        in quick_reference
    )
    assert (
        "Do not emit downstream sections such as goals, user stories, architecture, or implementation steps before the first approved section."
        in quick_reference
    )


def test_brainstorming_common_mistakes_forbids_made_up_headings() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    common_mistakes = _section_text(skill_text, "Common Mistakes")

    assert (
        'Inventing headings such as "Rapid Spec Drafting", "Pressure-Test Protocol", or "Plan-Gate Protocol".'
        in common_mistakes
    )


def test_brainstorming_quick_reference_forbids_draft_specs_under_ambiguity() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    quick_reference = _section_text(skill_text, "Quick Reference")

    assert (
        "Do not output `Draft Spec`, `MVP`, or any proposed solution while ambiguity remains unresolved."
        in quick_reference
    )


def test_brainstorming_initial_gate_blocks_full_outline() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    first_response = _section_text(skill_text, "Initial gate")

    assert (
        "Before the spec body, return only the current gate output: `## Assumptions surface` plus blockers or blocking questions."
        in first_response
    )
    assert (
        "Do not emit downstream sections such as goals, user stories, architecture, or implementation steps before the first approved section."
        in first_response
    )
