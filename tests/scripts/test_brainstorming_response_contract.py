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


def test_brainstorming_quick_reference_limits_first_pass_inspection_scope() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    quick_reference = _section_text(skill_text, "Quick Reference")

    assert (
        "Before the first approved section, inspect only the files needed to verify the currently exposed blockers, scope, or current-stage instructions."
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


def test_brainstorming_repository_verification_forbids_broad_first_pass_reads() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    verification = _section_text(skill_text, "Repository-grounded verification")

    assert (
        "Before the first approved section, do not widen inspection to tests, scripts, repo guides, or historical design docs unless one is the direct source of truth for the claim being checked."
        in verification
    )


def test_brainstorming_repository_verification_forbids_experiment_history_first_pass() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    verification = _section_text(skill_text, "Repository-grounded verification")

    assert (
        "Do not treat experiment reports, round logs, or investigation writeups as first-pass grounding unless the user explicitly asks for that history or a benchmark claim cannot be verified from live source."
        in verification
    )


def test_brainstorming_overview_does_not_keep_broad_standards_loader() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    overview = _section_text(skill_text, "Overview")

    assert "- load `SPEC_STANDARDS.md` for risk analysis or spec drafting" not in overview
    assert (
        "- load `SPEC_STANDARDS.md` during `## Assumptions surface` for explicit early-risk signals; otherwise load it before drafting a spec body"
        in overview
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


def test_brainstorming_initial_gate_sends_visual_offer_before_standards_for_clear_visual_requests() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    initial_gate = _section_text(skill_text, "Initial gate")

    assert (
        "For clearly visual layout/mockup/comparison requests with no visible blocker, no external fetch/dependency assumption, and no untrusted-input ingestion, send the standalone visual-companion offer before loading `SPEC_STANDARDS.md` or widening repository inspection."
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


def test_brainstorming_quick_reference_stages_companion_loading() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    quick_reference = _section_text(skill_text, "Quick Reference")

    assert "Load only the companion files needed for the current stage." in quick_reference
    assert (
        "Load `SPEC_STANDARDS.md` during `## Assumptions surface` when the request already exposes auth, privacy, data-sharing, external fetches, new dependency assumptions, untrusted-input ingestion, or retention/storage concerns. Otherwise load it before drafting a spec body."
        in quick_reference
    )
    assert (
        "`SPEC_REVIEW_MANIFEST.md` and `SPEC_RUBRIC.md` are required only after a written spec exists."
        in quick_reference
    )


def test_brainstorming_later_stage_review_workflow_moves_to_support_file() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    assert "Load `review-workflow.md` after a written spec exists." in skill_text
    assert Path("skills/brainstorming/review-workflow.md").exists()


def test_brainstorming_checklist_delays_standards_until_spec_body() -> None:
    skill_text = Path("skills/brainstorming/SKILL.md").read_text()

    checklist = _section_text(skill_text, "Checklist").replace("\n    ", " ")

    assert (
        "Ingest Standards: Load `SPEC_STANDARDS.md` during `## Assumptions surface` when the request already exposes auth, privacy, data-sharing, external fetches, new dependency assumptions, untrusted-input ingestion, or retention/storage concerns; otherwise load it before drafting a spec body."
        in checklist
    )
