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


def test_brainstorming_hard_gate_includes_vendor_no_implementation_line() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    assert (
        "Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it."
        in skill_text
    )


def test_brainstorming_description_uses_vendor_pre_implementation_wording() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    assert (
        'description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."'
        in skill_text
    )


def test_brainstorming_quick_reference_forbids_retrofitting_spec_around_existing_code() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    quick_reference = _section_text(skill_text, "Quick Reference")

    assert (
        "If implementation already exists before design, stop. Do not retrofit a minimal spec around the current solution."
        in quick_reference
    )


def test_brainstorming_initial_gate_allows_narrow_visual_offer() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    initial_gate = _section_text(skill_text, "Initial gate")

    assert (
        "For clearly visual layout/mockup/comparison requests, you may send the standalone visual-companion offer before `## Assumptions surface`."
        in initial_gate
    )
    assert (
        "If the request already exposes security, privacy, permissions, data-sharing, source-of-truth, or approval blockers, skip the visual offer and start with `## Assumptions surface`."
        in initial_gate
    )


def test_brainstorming_visual_companion_preserves_gates() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    visual_companion = _section_text(skill_text, "Visual Companion")

    assert (
        "Some of what we're working on might be easier to explain if I can show it to you in a web browser."
        in visual_companion
    )
    assert (
        "This offer MUST be its own message."
        in visual_companion
    )
    assert (
        "accepting the companion does not waive repository inspection, blocker handling, or section-approval gates."
        in visual_companion.lower()
    )
