"""Structure and machine interfaces of the two feature skills. Never their wording."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[2]
CLI = ENGINE / "skills" / "shared" / "scripts" / "review-log.py"
EVIDENCE = "field-evidence.md"
MAX_SKILL_WORDS = 1000
MAX_DESCRIPTION = 500

PACKAGES = {
    "planning-features": {
        "files": [
            "SKILL.md",
            "replan-run.md",
            "FEATURES_STANDARDS.md",
            "FEATURES_REVIEW_MANIFEST.md",
            "FEATURES_RUBRIC.md",
            "review-workflow.md",
            EVIDENCE,
        ],
        "phase": "FEATURES_PLAN_REVIEW",
    },
    "specifying-features": {
        "files": [
            "SKILL.md",
            "close-run.md",
            "FEATURE_STANDARDS.md",
            "FEATURE_REVIEW_MANIFEST.md",
            "FEATURE_RUBRIC.md",
            "review-workflow.md",
            EVIDENCE,
        ],
        "phase": "FEATURE_REVIEW",
    },
}

skill = pytest.mark.parametrize("name", sorted(PACKAGES))


def load_cli():
    spec = importlib.util.spec_from_file_location("review_log_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def package(name: str) -> Path:
    return ENGINE / "skills" / name


def package_text(name: str) -> str:
    """The skill's own files; the evidence file is a record, not instructions."""
    paths = sorted(path for path in package(name).glob("*.md") if path.name != EVIDENCE)
    return "".join(path.read_text(encoding="utf-8") for path in paths)


def skill_parts(name: str) -> tuple[dict[str, str], str]:
    text = (package(name) / "SKILL.md").read_text(encoding="utf-8")
    _, front, body = text.split("---", 2)
    fields = dict(line.split(":", 1) for line in front.strip().splitlines())
    return {key.strip(): value.strip().strip('"') for key, value in fields.items()}, body


@skill
def test_package_files_exist(name: str) -> None:
    missing = [file for file in PACKAGES[name]["files"] if not (package(name) / file).is_file()]
    assert missing == []


@skill
def test_frontmatter_names_the_folder_and_says_when_to_use(name: str) -> None:
    fields, _ = skill_parts(name)
    assert fields["name"] == name
    assert fields["description"].startswith("Use when")
    assert len(fields["description"]) <= MAX_DESCRIPTION


@skill
def test_skill_md_fits_the_word_cap(name: str) -> None:
    text = (package(name) / "SKILL.md").read_text(encoding="utf-8")
    assert len(text.split()) <= MAX_SKILL_WORDS


@skill
def test_review_log_names_are_accepted_by_the_cli(name: str) -> None:
    cli = load_cli()
    text = package_text(name)
    skills = set(re.findall(r"--skill[ ]+`?([A-Za-z0-9_-]+)", text))
    phases = set(re.findall(r"--phase[ ]+`?([A-Za-z0-9_-]+)", text))
    assert skills == {name}
    assert {PACKAGES[name]["phase"], "INDEPENDENT_AUDIT"} <= phases
    assert skills <= set(cli.SKILLS)
    assert phases <= set(cli.PHASES)
