from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess

from arch_delta_support import ENGINE, require_node, run_tool, unique

PACKAGE = ENGINE / "skills" / "defining-architecture"
FILES = [
    "SKILL.md",
    "baseline-run.md",
    "ARCH_STANDARDS.md",
    "ARCH_REVIEW_MANIFEST.md",
    "ARCH_RUBRIC.md",
    "review-workflow.md",
    "pressure-test-evidence.md",
]
FIXTURES = ENGINE / "tests" / "fixtures" / "defining-architecture"
EMPTY = FIXTURES / "empty"
MODELLED = FIXTURES / "modelled"
CLI = ENGINE / "skills" / "shared" / "scripts" / "review-log.py"
EVIDENCE = "pressure-test-evidence.md"


def load_cli():
    spec = importlib.util.spec_from_file_location("review_log_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def package_text() -> str:
    """The skill's own files; the evidence file quotes agents and is not package text."""
    paths = sorted(path for path in PACKAGE.glob("*.md") if path.name != EVIDENCE)
    return "".join(path.read_text(encoding="utf-8") for path in paths)


def test_package_files_exist() -> None:
    missing = [name for name in FILES if not (PACKAGE / name).is_file()]
    assert missing == []


def test_description_starts_use_when_and_fits() -> None:
    text = (PACKAGE / "SKILL.md").read_text(encoding="utf-8")
    front = text.split("---", 2)[1]
    fields = dict(line.split(":", 1) for line in front.strip().splitlines())
    assert fields["name"].strip() == "defining-architecture"
    description = fields["description"].strip().strip('"')
    assert description.startswith("Use when")
    assert len(description) <= 500


def test_review_log_names_are_accepted_by_the_cli() -> None:
    cli = load_cli()
    text = package_text()
    skills = set(re.findall(r"--skill[ ]+`?([a-z-]+)", text))
    phases = set(re.findall(r"--phase[ ]+`?([A-Z_]+)", text))
    assert "defining-architecture" in skills
    assert {"ARCH_REVIEW", "INDEPENDENT_AUDIT"} <= phases
    assert skills <= set(cli.SKILLS)
    assert phases <= set(cli.PHASES)


def test_empty_fixture_has_no_model_and_ten_modules(tmp_path) -> None:
    require_node()
    assert not (EMPTY / "docs" / "architecture").exists()
    repo = tmp_path / unique("empty")
    shutil.copytree(EMPTY, repo, ignore=shutil.ignore_patterns("build"))
    overlay = (repo / "ARCHITECTURE_DESIGN.md").read_text(encoding="utf-8")
    command = re.search(r"^deps-command: (.+)$", overlay, re.M).group(1).split()
    subprocess.run(command, cwd=repo, check=True)
    edges = json.loads((repo / "build" / "architecture-deps.json").read_text(encoding="utf-8"))["edges"]
    modules = {source for source, _ in edges}
    assert len(modules) == 10
    assert len({module.split(".")[1] for module in modules}) == 8


def test_modelled_fixture_exports(tmp_path) -> None:
    require_node()
    proc = run_tool("export", "--repo", MODELLED, "--model", "docs/architecture")
    assert proc.returncode == 0, proc.stderr
    ids = {element["id"] for element in json.loads(proc.stdout)["elements"]}
    assert {"shop.events", "shop.refunds", "shop.payments"} <= ids
    assert (MODELLED / "docs" / "architecture" / "architecture.md").is_file()
    assert (MODELLED / "docs" / "architecture" / "known-gap.json").is_file()


def test_modelled_fixture_check_shows_the_drift(tmp_path) -> None:
    require_node()
    repo = tmp_path / unique("modelled")
    shutil.copytree(MODELLED, repo, ignore=shutil.ignore_patterns("build"))
    deps = repo / "deps" / "dependencies.json"
    proc = run_tool("check", "--repo", repo, "--model", "docs/architecture", "--deps", deps, "--format", "json")
    assert proc.returncode == 1, proc.stderr
    report = json.loads(proc.stdout)
    assert report["gap"]["new"] == [{"from": "shop.checkout", "to": "shop.inventory"}]
    assert report["gap"]["stale"] == []
    assert report["unmapped"] == ["shop.returns.flow"]
