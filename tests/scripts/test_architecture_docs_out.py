"""The docs tool's output folder: write rules 1 and 2 (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from arch_delta_support import DOCS_LIB, call, link_dir, require_node, unique

require_node()


def layout(tmp_path: Path) -> tuple[Path, Path]:
    repo = Path(os.path.realpath(tmp_path)) / unique("r")
    model = repo / "docs" / "architecture"
    (model / "decisions").mkdir(parents=True)
    return repo, model


def resolve(repo: Path, model: Path, value: str | None) -> dict:
    return call("out.mjs", "resolveOut", str(repo), str(model), value, lib=DOCS_LIB)


def test_resolve_out_defaults_to_the_generated_folder(tmp_path) -> None:
    repo, model = layout(tmp_path)
    assert resolve(repo, model, None)["value"] == str(model / "generated")


def test_resolve_out_accepts_a_folder_elsewhere_in_the_repo(tmp_path) -> None:
    repo, model = layout(tmp_path)
    assert resolve(repo, model, "site/docs")["value"] == str(repo / "site" / "docs")


def test_resolve_out_accepts_generated_in_any_case(tmp_path) -> None:
    repo, model = layout(tmp_path)
    assert resolve(repo, model, "docs/architecture/Generated")["value"] == str(model / "Generated")


@pytest.mark.parametrize(("value", "detail"), [
    pytest.param("../elsewhere", "--out lies outside --repo", id="outside"),
    pytest.param(".", "--out must not hold the model folder", id="repo-root"),
    pytest.param("docs", "--out must not hold the model folder", id="docs"),
    pytest.param("docs/architecture", "--out must not hold the model folder", id="model"),
    pytest.param("docs/architecture/decisions", "--out inside the model folder must be its generated folder", id="decisions"),
    pytest.param("docs/architecture/docs-out", "--out inside the model folder must be its generated folder", id="docs-out"),
    pytest.param("docs/architecture/generated/x", "--out inside the model folder must be its generated folder", id="generated-child"),
])
def test_resolve_out_refuses(tmp_path, value: str, detail: str) -> None:
    repo, model = layout(tmp_path)
    result = resolve(repo, model, value)
    assert (result["token"], result["details"]) == ("out-error", [detail])


def test_resolve_out_refuses_a_link_on_the_way(tmp_path) -> None:
    repo, model = layout(tmp_path)
    (repo / "site").mkdir()
    target = tmp_path / unique("t")
    target.mkdir()
    link_dir(target, repo / "site" / "via")
    result = resolve(repo, model, "site/via/out")
    assert (result["token"], result["details"]) == ("out-error", ["--out passes through a link: site/via"])


def other_spelling(repo: Path, model: Path) -> str | None:
    """Another spelling of the model folder, relative to the repository: its Windows short name, or its upper case."""
    rel = model.relative_to(repo)
    if sys.platform == "win32":
        import ctypes
        buffer = ctypes.create_unicode_buffer(1024)
        if not ctypes.windll.kernel32.GetShortPathNameW(str(model), buffer, 1024):
            return None
        short = Path(*Path(buffer.value).parts[-len(rel.parts):])
        return None if str(short).lower() == str(rel).lower() else str(short)
    upper = Path(str(rel).upper())
    return str(upper) if (repo / upper).exists() and os.path.samefile(repo / upper, model) else None


def test_resolve_out_refuses_another_spelling_of_the_model_folder(tmp_path) -> None:
    repo, model = layout(tmp_path)
    alternate = other_spelling(repo, model)
    if alternate is None:
        pytest.skip("no other spelling of the model folder on this file system")
    result = resolve(repo, model, str(Path(alternate) / "notes"))
    assert (result["token"], result["details"]) == ("out-error", ["--out inside the model folder must be its generated folder"])


def test_resolve_out_returns_the_real_path(tmp_path) -> None:
    repo, model = layout(tmp_path)
    alternate = other_spelling(repo, model)
    if alternate is None:
        pytest.skip("no other spelling of the model folder on this file system")
    assert resolve(repo, model, str(Path(alternate) / "generated"))["value"] == str(model / "generated")


def test_resolve_out_before_the_model_folder_exists(tmp_path) -> None:
    repo, model = layout(tmp_path)
    assert resolve(repo, repo / "missing", "site")["value"] == str(repo / "site")


def test_resolve_out_refuses_a_file_on_the_way_or_as_the_folder(tmp_path) -> None:
    repo, model = layout(tmp_path)
    (repo / "f").write_text("x", encoding="utf-8")
    on_the_way = resolve(repo, model, "f/out")
    as_folder = resolve(repo, model, "f")
    assert (on_the_way["token"], on_the_way["details"]) == ("out-error", ["--out passes through a file: f"])
    assert (as_folder["token"], as_folder["details"]) == ("out-error", ["--out is not a folder"])
