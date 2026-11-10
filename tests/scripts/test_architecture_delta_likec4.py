from __future__ import annotations

import json
import os
from pathlib import Path

from arch_delta_support import (
    ENGINE, LIKEC4_DIR, call, lib_url, link_dir, make_shim, require_node, run_module, unique, write_json,
)

require_node()


def locate(repo: Path, engine: Path) -> dict:
    return call("likec4.mjs", "locateLikeC4", str(repo), str(engine))


def same(a: str, b: Path) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def test_plugin_copy_when_the_repo_has_none(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    result = locate(repo, ENGINE)
    assert result["ok"], result
    assert result["value"]["source"] == "plugin"
    assert result["value"]["version"] == "1.60.0"
    assert same(result["value"]["dir"], LIKEC4_DIR)
    assert result["value"]["entry"].replace("\\", "/").endswith("likec4/dist/index.mjs")


def test_repo_copy_wins_at_any_version(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    make_shim(repo / "node_modules", version="1.59.0")
    result = locate(repo, ENGINE)
    assert result["value"]["source"] == "repo"
    assert result["value"]["version"] == "1.59.0"


def test_parent_folders_are_never_searched(tmp_path) -> None:
    outer_repo = tmp_path / unique("a")
    make_shim(outer_repo / "node_modules")
    repo = outer_repo / "repo"
    repo.mkdir()
    outer_engine = tmp_path / unique("b")
    make_shim(outer_engine / "node_modules")
    engine = outer_engine / "engine"
    engine.mkdir()
    result = locate(repo, engine)
    assert result["ok"] is False
    assert result["token"] == "likec4-missing"


def test_missing_everywhere_gives_an_install_hint(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    engine = tmp_path / unique("engine")
    engine.mkdir()
    result = locate(repo, engine)
    assert result["token"] == "likec4-missing"
    assert "npm" in result["details"][0]


def test_repo_copy_that_resolves_outside_the_repo_is_not_used(tmp_path) -> None:
    outside = tmp_path / unique("outside")
    shim = make_shim(outside / "node_modules", version="9.9.9")
    repo = tmp_path / unique("repo")
    link_dir(shim, repo / "node_modules" / "likec4")
    result = locate(repo, ENGINE)
    assert result["value"]["source"] == "plugin"


def test_missing_or_non_string_version_is_unknown(tmp_path) -> None:
    for version_field in ({}, {"version": 3}):
        repo = tmp_path / unique("repo")
        make_shim(repo / "node_modules", package={"name": "likec4", "main": "./index.mjs", **version_field})
        assert locate(repo, ENGINE)["value"]["version"] == "unknown"


def test_entry_field_order(tmp_path) -> None:
    cases = [
        ({"exports": {".": {"import": "./a.mjs", "default": {"import": "./b.mjs"}}}, "main": "./c.mjs"}, "a.mjs"),
        ({"exports": {".": {"default": {"import": "./b.mjs"}}}, "module": "./d.mjs", "main": "./c.mjs"}, "b.mjs"),
        ({"exports": {".": {"default": "./e.mjs"}}, "main": "./c.mjs"}, "e.mjs"),
        ({"module": "./d.mjs", "main": "./c.mjs"}, "d.mjs"),
        ({"main": "./c.mjs"}, "c.mjs"),
    ]
    for fields, expected in cases:
        repo = tmp_path / unique("repo")
        pkg = make_shim(repo / "node_modules", package={"name": "likec4", "version": "1.0.0", **fields})
        for name in ("a.mjs", "b.mjs", "c.mjs", "d.mjs", "e.mjs"):
            (pkg / name).write_text("export const x = 1;\n", encoding="utf-8")
        assert locate(repo, ENGINE)["value"]["entry"].endswith(expected), fields


def test_no_entry_is_internal(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    make_shim(repo / "node_modules", package={"name": "likec4", "version": "1.0.0"})
    result = locate(repo, ENGINE)
    assert result["token"] == "internal"


def test_entry_outside_the_copy_is_internal(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    (repo / "node_modules").mkdir(parents=True)
    (repo / "node_modules" / "x.mjs").write_text("export const x = 1;\n", encoding="utf-8")
    make_shim(repo / "node_modules", package={"name": "likec4", "version": "1.0.0", "main": "../x.mjs"})
    result = locate(repo, ENGINE)
    assert result["token"] == "internal"


def test_import_requires_fromworkspace(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    make_shim(repo / "node_modules", source="export const nothing = 1;\n")
    code = (
        f"import {{ locateLikeC4, importLikeC4 }} from {json.dumps(lib_url('likec4.mjs'))};\n"
        f"const located = locateLikeC4({json.dumps(str(repo))}, {json.dumps(str(ENGINE))});\n"
        "try { await importLikeC4(located); process.stdout.write('loaded'); }\n"
        "catch (err) { process.stdout.write(err.token); }\n"
    )
    assert run_module(code).stdout == "internal"


def test_import_loads_the_real_class() -> None:
    code = (
        f"import {{ locateLikeC4, importLikeC4 }} from {json.dumps(lib_url('likec4.mjs'))};\n"
        f"const located = locateLikeC4({json.dumps(str(ENGINE / 'tests'))}, {json.dumps(str(ENGINE))});\n"
        "const LikeC4 = await importLikeC4(located);\n"
        "process.stdout.write(typeof LikeC4.fromWorkspace);\n"
    )
    assert run_module(code).stdout == "function"


def test_version_note() -> None:
    assert call("likec4.mjs", "versionNote", {"version": "1.59.0", "source": "repo"})["value"] == (
        "note: likec4 1.59.0 from repo; tested with 1.60.0"
    )
    assert call("likec4.mjs", "versionNote", {"version": "1.60.0", "source": "plugin"})["value"] is None


def test_is_inside(tmp_path) -> None:
    base = tmp_path / unique("root")
    cases = [
        (base, True),
        (base / "a" / "b", True),
        (base / "..foo", True),
        (base.parent / (base.name + "-x"), False),
        (base.parent, False),
        (base.parent / "other" / "x", False),
    ]
    if os.name == "nt":
        other_drive = "Z:" if str(base)[0].upper() != "Z" else "Y:"
        cases.append((Path(other_drive + "\\x"), False))
    for child, expected in cases:
        assert call("paths.mjs", "isInside", str(child), str(base))["value"] is expected, child


def test_entry_through_a_link_out_of_the_copy_is_internal(tmp_path) -> None:
    outside = tmp_path / unique("outside")
    outside.mkdir()
    (outside / "index.mjs").write_text("export const x = 1;\n", encoding="utf-8")
    repo = tmp_path / unique("repo")
    pkg = make_shim(repo / "node_modules", package={"name": "likec4", "version": "1.0.0", "main": "./sub/index.mjs"})
    link_dir(outside, pkg / "sub")
    assert call("likec4.mjs", "locateLikeC4", str(repo), str(ENGINE))["token"] == "internal"


def test_unreadable_package_json_is_internal(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    pkg = make_shim(repo / "node_modules")
    (pkg / "package.json").write_text("{not json", encoding="utf-8")
    assert call("likec4.mjs", "locateLikeC4", str(repo), str(ENGINE))["token"] == "internal"


def test_version_note_cleans_the_version() -> None:
    note = call("likec4.mjs", "versionNote", {"version": "1.0\x1b[31m\u202e", "source": "repo"})["value"]
    assert note == "note: likec4 1.0 from repo; tested with 1.60.0"


# --- model.py additions ----------------------------------------------------------------


def test_empty_entry_field_is_skipped(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    pkg = make_shim(repo / "node_modules", package={
        "name": "likec4", "version": "1.0.0", "exports": {".": {"import": ""}}, "main": "./c.mjs"})
    (pkg / "c.mjs").write_text("export const x = 1;\n", encoding="utf-8")
    assert call("likec4.mjs", "locateLikeC4", str(repo), str(ENGINE))["value"]["entry"].endswith("c.mjs")
