"""Tests for scripts/import_superpowers_catalog.py."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = str(Path(__file__).parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _fixture_vendor(tmp_path: Path) -> Path:
    source_root = tmp_path / "vendor" / "obra-superpowers"
    _write(
        source_root / "skills" / "brainstorming" / "SKILL.md",
        "---\nname: brainstorming\n---\n",
    )
    _write(
        source_root / "skills" / "brainstorming" / "scripts" / "helper.js",
        "console.log('helper');\n",
    )
    _write(
        source_root / "agents" / "code-reviewer.md",
        "# code-reviewer\n",
    )
    _write(
        source_root / "README.md",
        "# vendor readme\n",
    )
    _write(
        source_root / "docs" / "overview.md",
        "# docs\n",
    )
    return source_root


def test_import_superpowers_catalog_copies_skill_and_agent(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"

    result = import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    skill_root = output_root / "skills" / "brainstorming"
    agent_path = output_root / "agents" / "code-reviewer.md"

    assert (skill_root / "SKILL.md").read_text() == "---\nname: brainstorming\n---\n"
    assert (skill_root / "scripts" / "helper.js").read_text() == "console.log('helper');\n"
    assert agent_path.read_text() == "# code-reviewer\n"

    assert result["catalog_index"] == [
        {
            "entry_type": "skill",
            "name": "brainstorming",
            "source_repo": "vendor/obra-superpowers",
            "source_path": "skills/brainstorming",
            "local_path": "skills/brainstorming",
            "imported_files": ["SKILL.md", "scripts/helper.js"],
            "source_revision": "fixture-rev",
            "imported_at": "2026-04-15T00:00:00Z",
        },
        {
            "entry_type": "agent",
            "name": "code-reviewer",
            "source_repo": "vendor/obra-superpowers",
            "source_path": "agents/code-reviewer.md",
            "local_path": "agents/code-reviewer.md",
            "imported_files": ["code-reviewer.md"],
            "source_revision": "fixture-rev",
            "imported_at": "2026-04-15T00:00:00Z",
        },
    ]
    assert result["non_skill_inventory"] == [
        {"source_path": "README.md", "surface_kind": "file", "decision": "defer"},
        {"source_path": "docs", "surface_kind": "directory", "decision": "defer"},
    ]


def test_import_superpowers_catalog_builds_provenance_manifest(
    tmp_path: Path
) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"

    result = import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert result["provenance_manifest"] == [
        {
            "entry_id": "skill:brainstorming",
            "entry_type": "skill",
            "name": "brainstorming",
            "source_repo": "vendor/obra-superpowers",
            "source_path": "skills/brainstorming",
            "local_path": "skills/brainstorming",
            "manifest_state": "imported",
            "source_revision": "fixture-rev",
            "last_imported_at": "2026-04-15T00:00:00Z",
            "last_verified_at": "2026-04-15T00:00:00Z",
            "files": [
                {
                    "source_file": "skills/brainstorming/SKILL.md",
                    "local_file": "skills/brainstorming/SKILL.md",
                    "file_state": "imported",
                    "local_sync_policy": "required",
                    "source_digest": "sha256:99694ffe2b46a3ac37ad2a4c501fa795b5aa723e255aa1f5b99ebe198efb5f73",
                    "local_digest": "sha256:99694ffe2b46a3ac37ad2a4c501fa795b5aa723e255aa1f5b99ebe198efb5f73",
                    "last_verified_at": "2026-04-15T00:00:00Z",
                },
                {
                    "source_file": "skills/brainstorming/scripts/helper.js",
                    "local_file": "skills/brainstorming/scripts/helper.js",
                    "file_state": "imported",
                    "local_sync_policy": "required",
                    "source_digest": "sha256:080aa3dd805c3665de0e06f0267ef9f71c06bbd62ff9a8a17afeceadf635a0be",
                    "local_digest": "sha256:080aa3dd805c3665de0e06f0267ef9f71c06bbd62ff9a8a17afeceadf635a0be",
                    "last_verified_at": "2026-04-15T00:00:00Z",
                },
            ],
        },
        {
            "entry_id": "agent:code-reviewer",
            "entry_type": "agent",
            "name": "code-reviewer",
            "source_repo": "vendor/obra-superpowers",
            "source_path": "agents/code-reviewer.md",
            "local_path": "agents/code-reviewer.md",
            "manifest_state": "imported",
            "source_revision": "fixture-rev",
            "last_imported_at": "2026-04-15T00:00:00Z",
            "last_verified_at": "2026-04-15T00:00:00Z",
            "files": [
                {
                    "source_file": "agents/code-reviewer.md",
                    "local_file": "agents/code-reviewer.md",
                    "file_state": "imported",
                    "local_sync_policy": "required",
                    "source_digest": "sha256:bca5dc168dad2bb212e430262dd973adf0c16c96315e876831e7a7983d051902",
                    "local_digest": "sha256:bca5dc168dad2bb212e430262dd973adf0c16c96315e876831e7a7983d051902",
                    "last_verified_at": "2026-04-15T00:00:00Z",
                }
            ],
        },
    ]


def test_import_superpowers_catalog_preserves_local_authoring_defaults_when_output_root_is_local_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import import_superpowers_catalog as module

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    local_skills_root = output_root / "skills"

    _write(
        local_skills_root / "brainstorming" / "SKILL.md",
        "---\nname: brainstorming\nlocal: true\n---\n",
    )
    _write(
        local_skills_root / "brainstorming" / "SPEC_REVIEW_MANIFEST.md",
        "# local manifest\n",
    )
    _write(
        local_skills_root / "brainstorming" / "SPEC_RUBRIC.md",
        "# local rubric\n",
    )
    _write(
        local_skills_root / "brainstorming" / "SPEC_STANDARDS.md",
        "# local standards\n",
    )
    _write(
        local_skills_root / "brainstorming" / "spec-document-reviewer-prompt.md",
        "# local prompt\n",
    )
    _write(
        local_skills_root / "writing-plans" / "SKILL.md",
        "---\nname: writing-plans\nlocal: true\n---\n",
    )

    monkeypatch.setattr(module, "_LOCAL_AUTHORING_SKILLS_ROOT", local_skills_root)
    monkeypatch.setattr(module, "_is_real_vendor_source", lambda _: True)

    result = module.import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert (output_root / "skills" / "brainstorming" / "SKILL.md").read_text() == (
        "---\nname: brainstorming\nlocal: true\n---\n"
    )
    assert (
        output_root / "skills" / "brainstorming" / "SPEC_REVIEW_MANIFEST.md"
    ).read_text() == "# local manifest\n"
    assert (output_root / "skills" / "brainstorming" / "SPEC_STANDARDS.md").read_text() == (
        "# local standards\n"
    )

    brainstorming_entry = next(
        entry for entry in result["provenance_manifest"] if entry["entry_id"] == "skill:brainstorming"
    )
    skill_record = next(
        file_record
        for file_record in brainstorming_entry["files"]
        if file_record["local_file"] == "skills/brainstorming/SKILL.md"
    )
    assert skill_record["source_file"] == "resistance-engine/skills/brainstorming/SKILL.md"
    assert skill_record["source_repo"] == "."


def test_import_superpowers_catalog_rejects_name_collision(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = tmp_path / "vendor" / "obra-superpowers"
    _write(source_root / "skills" / "My Skill" / "SKILL.md", "---\nname: a\n---\n")
    _write(source_root / "skills" / "my-skill" / "SKILL.md", "---\nname: b\n---\n")
    _write(source_root / "agents" / "code-reviewer.md", "# code-reviewer\n")

    with pytest.raises(ValueError, match="normalized path collision for skill 'my-skill'"):
        import_superpowers_catalog(
            source_root=source_root,
            output_root=tmp_path / "resistance-engine",
            source_repo="vendor/obra-superpowers",
            source_revision="fixture-rev",
            imported_at="2026-04-15T00:00:00Z",
        )


def test_import_superpowers_catalog_rejects_output_escape(tmp_path: Path) -> None:
    from import_superpowers_catalog import _safe_output_path

    with pytest.raises(ValueError, match="resolved output path escapes repo root"):
        _safe_output_path(tmp_path / "resistance-engine", Path("../escape.txt"))


def test_import_superpowers_catalog_preserves_non_generated_repo_surfaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import import_superpowers_catalog as module

    source_root = _fixture_vendor(tmp_path / "source")
    output_root = tmp_path / "canonical-repo"
    monkeypatch.setattr(module, "REPO_ROOT", output_root)
    _write(output_root / "README.md", "# canonical\n")
    _write(output_root / ".gitmodules", "[submodule \"vendor/obra-superpowers\"]\n")
    _write(output_root / "package.json", '{"name":"resistance-engine"}\n')
    _write(output_root / "tests" / "keep.txt", "keep\n")
    _write(output_root / "scripts" / "helper.py", "print('keep')\n")
    _write(output_root / "vendor" / "obra-superpowers" / "README.md", "# vendor\n")

    module.import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert (output_root / "README.md").read_text() == "# canonical\n"
    assert (output_root / ".gitmodules").read_text() == '[submodule "vendor/obra-superpowers"]\n'
    assert (output_root / "package.json").read_text() == '{"name":"resistance-engine"}\n'
    assert (output_root / "tests" / "keep.txt").read_text() == "keep\n"
    assert (output_root / "scripts" / "helper.py").read_text() == "print('keep')\n"
    assert (output_root / "vendor" / "obra-superpowers" / "README.md").read_text() == "# vendor\n"
    assert (output_root / "skills" / "brainstorming" / "SKILL.md").read_text() == (
        "---\nname: brainstorming\n---\n"
    )


def test_main_writes_catalog_and_provenance_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from import_superpowers_catalog import main

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"

    exit_code = main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "fixture-rev",
            "--imported-at",
            "2026-04-15T00:00:00Z",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "imported 2 entries into" in captured.out

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )

    assert [entry["entry_id"] for entry in manifest] == [
        "skill:brainstorming",
        "agent:code-reviewer",
    ]


def test_import_superpowers_catalog_resets_existing_output_root(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "stale.txt").write_text("stale\n")

    import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert not (output_root / "stale.txt").exists()


def test_import_superpowers_catalog_preserves_workspace_readme(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    output_root.mkdir(parents=True, exist_ok=True)
    readme_path = output_root / "README.md"
    readme_path.write_text("# workspace readme\n")

    import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert readme_path.read_text() == "# workspace readme\n"


def test_import_superpowers_catalog_defaults_local_sync_policy_to_required(
    tmp_path: Path,
) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"

    result = import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    brainstorming = next(
        entry for entry in result["provenance_manifest"] if entry["entry_id"] == "skill:brainstorming"
    )

    assert [file_record["local_sync_policy"] for file_record in brainstorming["files"]] == [
        "required",
        "required",
    ]


def test_import_superpowers_catalog_applies_pruned_override(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    override_path = output_root / "consolidation" / "consolidation_overrides.json"
    _write(
        override_path,
        json.dumps(
            [
                {
                    "entry_id": "skill:brainstorming",
                    "source_file": "skills/brainstorming/scripts/helper.js",
                    "local_sync_policy": "pruned",
                }
            ],
            indent=2,
        )
        + "\n",
    )

    result = import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    brainstorming = next(
        entry for entry in result["provenance_manifest"] if entry["entry_id"] == "skill:brainstorming"
    )
    helper_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "skills/brainstorming/scripts/helper.js"
    )

    assert helper_record["local_sync_policy"] == "pruned"


def test_import_superpowers_catalog_preserves_override_file(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    override_path = output_root / "consolidation" / "consolidation_overrides.json"
    override_text = (
        '[{"entry_id":"skill:brainstorming","source_file":"skills/brainstorming/scripts/helper.js",'
        '"local_sync_policy":"pruned"}]\n'
    )
    _write(override_path, override_text)

    import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="fixture-rev",
        imported_at="2026-04-15T00:00:00Z",
    )

    assert override_path.read_text() == override_text


def test_import_superpowers_catalog_rejects_unknown_override_target(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    _write(
        output_root / "consolidation" / "consolidation_overrides.json",
        json.dumps(
            [
                {
                    "entry_id": "skill:brainstorming",
                    "source_file": "skills/brainstorming/scripts/missing.js",
                    "local_sync_policy": "pruned",
                }
            ],
            indent=2,
        )
        + "\n",
    )

    with pytest.raises(
        ValueError,
        match="override references unknown imported file: skill:brainstorming -> skills/brainstorming/scripts/missing.js",
    ):
        import_superpowers_catalog(
            source_root=source_root,
            output_root=output_root,
            source_repo="vendor/obra-superpowers",
            source_revision="fixture-rev",
            imported_at="2026-04-15T00:00:00Z",
        )


def test_import_superpowers_catalog_rejects_non_list_override_payload(tmp_path: Path) -> None:
    from import_superpowers_catalog import import_superpowers_catalog

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    _write(
        output_root / "consolidation" / "consolidation_overrides.json",
        '{"entry_id":"skill:brainstorming"}\n',
    )

    with pytest.raises(ValueError, match="consolidation overrides must be a JSON list"):
        import_superpowers_catalog(
            source_root=source_root,
            output_root=output_root,
            source_repo="vendor/obra-superpowers",
            source_revision="fixture-rev",
            imported_at="2026-04-15T00:00:00Z",
        )


def test_import_superpowers_catalog_marks_source_missing_entry(tmp_path: Path) -> None:
    from import_superpowers_catalog import main

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"

    first_exit = main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "first-rev",
            "--imported-at",
            "2026-04-15T00:00:00Z",
        ]
    )
    assert first_exit == 0

    shutil.rmtree(source_root / "skills" / "brainstorming")

    second_exit = main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "second-rev",
            "--imported-at",
            "2026-04-16T00:00:00Z",
        ]
    )
    assert second_exit == 0

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )

    assert brainstorming["manifest_state"] == "source-missing"
    assert brainstorming["source_revision"] == "second-rev"
    assert brainstorming["files"][0]["file_state"] == "source-missing"


def test_import_superpowers_catalog_carries_forward_pruned_policy_for_source_missing_entry(
    tmp_path: Path,
) -> None:
    from import_superpowers_catalog import main

    source_root = _fixture_vendor(tmp_path)
    output_root = tmp_path / "resistance-engine"
    _write(
        output_root / "consolidation" / "consolidation_overrides.json",
        json.dumps(
            [
                {
                    "entry_id": "skill:brainstorming",
                    "source_file": "skills/brainstorming/scripts/helper.js",
                    "local_sync_policy": "pruned",
                }
            ],
            indent=2,
        )
        + "\n",
    )

    first_exit = main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "first-rev",
            "--imported-at",
            "2026-04-15T00:00:00Z",
        ]
    )
    assert first_exit == 0

    shutil.rmtree(source_root / "skills" / "brainstorming")

    second_exit = main(
        [
            "--source-root",
            str(source_root),
            "--output-root",
            str(output_root),
            "--source-repo",
            "vendor/obra-superpowers",
            "--source-revision",
            "second-rev",
            "--imported-at",
            "2026-04-16T00:00:00Z",
        ]
    )
    assert second_exit == 0

    manifest = json.loads(
        (output_root / "provenance" / "provenance_manifest.json").read_text()
    )
    brainstorming = next(
        entry for entry in manifest if entry["entry_id"] == "skill:brainstorming"
    )
    helper_record = next(
        file_record
        for file_record in brainstorming["files"]
        if file_record["source_file"] == "skills/brainstorming/scripts/helper.js"
    )

    assert brainstorming["manifest_state"] == "source-missing"
    assert helper_record["local_sync_policy"] == "pruned"
    assert helper_record["file_state"] == "source-missing"


def test_import_superpowers_catalog_matches_live_vendor_repo_shape(
    tmp_path: Path, section_text
) -> None:
    from import_superpowers_catalog import import_superpowers_catalog, normalize_name

    repo_root = Path(__file__).parents[2]
    source_root = repo_root / "vendor" / "obra-superpowers"
    output_root = tmp_path / "resistance-engine"

    result = import_superpowers_catalog(
        source_root=source_root,
        output_root=output_root,
        source_repo="vendor/obra-superpowers",
        source_revision="test-live-revision",
        imported_at="2026-04-15T00:00:00Z",
    )

    skill_entries = [entry for entry in result["catalog_index"] if entry["entry_type"] == "skill"]
    agent_entries = [entry for entry in result["catalog_index"] if entry["entry_type"] == "agent"]
    inventory_paths = {entry["source_path"] for entry in result["non_skill_inventory"]}
    manifest_entry_ids = {entry["entry_id"] for entry in result["provenance_manifest"]}
    expected_manifest_entry_ids = {
        f"skill:{normalize_name(path.name)}"
        for path in (source_root / "skills").iterdir()
        if path.is_dir()
    } | {
        f"agent:{normalize_name(path.stem)}"
        for path in (source_root / "agents").iterdir()
        if path.is_file()
    }

    assert manifest_entry_ids == expected_manifest_entry_ids
    assert {entry["entry_id"] for entry in result["provenance_manifest"]} == {
        f"{entry['entry_type']}:{entry['name']}" for entry in result["catalog_index"]
    }
    assert skill_entries
    assert agent_entries
    assert "docs" in inventory_paths
    assert "commands" in inventory_paths
    assert "hooks" in inventory_paths

    brainstorming_root = output_root / "skills" / "brainstorming"
    writing_plans_root = output_root / "skills" / "writing-plans"

    assert (
        brainstorming_root / "SPEC_REVIEW_MANIFEST.md"
    ).is_file(), "expected skill-local SPEC_REVIEW_MANIFEST.md to be imported"
    assert (
        brainstorming_root / "SPEC_RUBRIC.md"
    ).is_file(), "expected skill-local SPEC_RUBRIC.md to be imported"
    assert (
        brainstorming_root / "SPEC_STANDARDS.md"
    ).is_file(), "expected skill-local SPEC_STANDARDS.md to be imported"

    brainstorming_skill = (brainstorming_root / "SKILL.md").read_text()
    assert '## Anti-Pattern: "This Is Too Simple To Need A Design"' in brainstorming_skill
    assert "## Checklist" in brainstorming_skill
    assert "## Threat Model (CIA)" in brainstorming_skill
    assert "cite repository proof" in brainstorming_skill
    assert "emit a blocker" in brainstorming_skill
    assert "## Process Flow" in brainstorming_skill
    process_flow_text = section_text(brainstorming_skill, "Process Flow")
    assert '"Ask blocking question" -> "Assumptions / blockers" [label="answered"]' in process_flow_text
    assert "Revise design (pre-spec)" in process_flow_text
    assert "Revise design (post-review)" in process_flow_text
    assert "## Quick Reference" in brainstorming_skill
    assert "Planning gate. Only specs with `APPROVED - CROSS-MODEL AUDIT` may proceed to" in brainstorming_skill
    assert ".review_log.jsonl" in brainstorming_skill
    checklist_text = section_text(brainstorming_skill, "Checklist")
    quick_reference_text = section_text(brainstorming_skill, "Quick Reference")
    assert "APPROVED - CROSS-MODEL AUDIT" in checklist_text
    assert ".review_log.jsonl" in checklist_text
    assert "[SPEC-APPROVED]" in quick_reference_text
    assert ".review_log.jsonl" in quick_reference_text
    assert '"Cross-model spec audit" -> "User review" [label="[SPEC-APPROVED]"]' in process_flow_text
    assert '"User review" ->  "Checklist Retrospective" [label="approved"]' in process_flow_text
    assert '"Checklist Retrospective" -> "Invoke writing-plans"' in process_flow_text
    assert "## Checklist Retrospective" in brainstorming_skill

    rubric_text = (brainstorming_root / "SPEC_RUBRIC.md").read_text()
    assert "No Hallucinated Dependencies" in rubric_text
    standards_text = (brainstorming_root / "SPEC_STANDARDS.md").read_text()
    assert "## 1. The CIA+ Threat Model" in standards_text
    assert "## 4. Post-Fix Consistency Check" in standards_text

    writing_plans_skill = (writing_plans_root / "SKILL.md").read_text()
    assert "## Scope Check" in writing_plans_skill
    assert "## File Structure" in writing_plans_skill
    assert "## Task Structure" in writing_plans_skill
    assert "## No Placeholders" in writing_plans_skill
    assert "## Execution Handoff" in writing_plans_skill
    assert "## Process Flow" in writing_plans_skill
    assert "subagent-driven-development" in writing_plans_skill
    assert "executing-plans" in writing_plans_skill
    assert "### Risk & Confidence Assessment" in writing_plans_skill
    assert "RED / GREEN / REFACTOR" in writing_plans_skill
    assert "[APPROVED - READY FOR EXECUTION]" in writing_plans_skill
    assert "[REJECTED - PLAN DRIFT]" in writing_plans_skill
    assert "[REJECTED - SPEC INCOMPLETE]" in writing_plans_skill
    task_structure_text = section_text(writing_plans_skill, "Task Structure")
    handoff_text = section_text(writing_plans_skill, "Execution Handoff")
    no_placeholders_text = section_text(writing_plans_skill, "No Placeholders")
    assert "### Task N: [single execution goal]" in task_structure_text
    assert "**Files:**" in task_structure_text
    assert "Step 1: write RED tests for the happy path AND at least two failure modes." in task_structure_text
    assert "Step 6: commit the finished slice" in task_structure_text
    assert "subagent-driven-development" in handoff_text
    assert "executing-plans" in handoff_text
    assert "Tabula Rasa" in handoff_text
    assert "RED/GREEN/REFACTOR" in handoff_text
    assert "exact `pytest` command" in no_placeholders_text

    brainstorming_manifest = next(
        entry for entry in result["provenance_manifest"] if entry["entry_id"] == "skill:brainstorming"
    )
    writing_plans_manifest = next(
        entry for entry in result["provenance_manifest"] if entry["entry_id"] == "skill:writing-plans"
    )
    overlay_records = {
        file_record["local_file"]: file_record
        for file_record in brainstorming_manifest["files"] + writing_plans_manifest["files"]
        if file_record["local_file"]
        in {
            "skills/brainstorming/SKILL.md",
            "skills/brainstorming/SPEC_REVIEW_MANIFEST.md",
            "skills/brainstorming/SPEC_RUBRIC.md",
            "skills/brainstorming/SPEC_STANDARDS.md",
            "skills/brainstorming/spec-document-reviewer-prompt.md",
            "skills/writing-plans/SKILL.md",
            "skills/writing-plans/plan-document-reviewer-prompt.md",
        }
    }
    assert overlay_records["skills/brainstorming/SKILL.md"]["source_file"] == "skills/brainstorming/SKILL.md"
    assert overlay_records["skills/brainstorming/SKILL.md"]["source_repo"] == "."
    assert overlay_records["skills/brainstorming/SPEC_REVIEW_MANIFEST.md"]["source_file"] == (
        "skills/brainstorming/SPEC_REVIEW_MANIFEST.md"
    )
    assert overlay_records["skills/brainstorming/SPEC_REVIEW_MANIFEST.md"]["source_repo"] == "."
    assert overlay_records["skills/brainstorming/SPEC_RUBRIC.md"]["source_file"] == (
        "skills/brainstorming/SPEC_RUBRIC.md"
    )
    assert overlay_records["skills/brainstorming/SPEC_RUBRIC.md"]["source_repo"] == "."
    assert overlay_records["skills/brainstorming/SPEC_STANDARDS.md"]["source_file"] == (
        "skills/brainstorming/SPEC_STANDARDS.md"
    )
    assert overlay_records["skills/brainstorming/SPEC_STANDARDS.md"]["source_repo"] == "."
    assert overlay_records["skills/writing-plans/SKILL.md"]["source_file"] == "skills/writing-plans/SKILL.md"
    assert overlay_records["skills/writing-plans/SKILL.md"]["source_repo"] == "."
