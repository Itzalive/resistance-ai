"""Finding Graphviz for the docs tool (architecture-docs/graphviz.mjs): the repository's copy first, then the plugin's,
each at the pinned version, since the SVG bytes `check` compares depend on it."""

from __future__ import annotations

import os
import re
from pathlib import Path

from arch_delta_support import DOCS_LIB, ENGINE, call, link_dir, require_node, unique, write_json

require_node()

INSTALLED = ENGINE / "node_modules" / "@hpcc-js" / "wasm-graphviz"


def locate(repo: Path, engine: Path) -> dict:
    return call("graphviz.mjs", "locateGraphviz", str(repo), str(engine), lib=DOCS_LIB)


def shim(node_modules: Path, version: str) -> Path:
    """A fake Graphviz package that re-exports the engine's installed copy."""
    pkg = node_modules / "@hpcc-js" / "wasm-graphviz"
    (pkg / "dist").mkdir(parents=True)
    write_json(pkg / "package.json", {"name": "@hpcc-js/wasm-graphviz", "version": version,
                                      "exports": {".": {"default": "./dist/index.js"}}, "type": "module"})
    (pkg / "dist" / "index.js").write_text(f"export * from {(INSTALLED / 'dist' / 'index.js').as_uri()!r};\n",
                                           encoding="utf-8")
    return pkg


def same(a: str, b: Path) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def test_installed_graphviz_matches_the_pin() -> None:
    assert '"version": "1.29.2"' in (INSTALLED / "package.json").read_text(encoding="utf-8")


def test_plugin_copy_when_the_repo_has_none(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    repo.mkdir()
    result = locate(repo, ENGINE)
    assert result["ok"], result
    assert result["value"]["source"] == "plugin" and result["value"]["version"] == "1.29.2"
    assert same(result["value"]["dir"], INSTALLED)


def test_repo_copy_at_the_pin_wins(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    shim(repo / "node_modules", "1.29.2")
    assert locate(repo, ENGINE)["value"]["source"] == "repo"


def test_repo_copy_at_another_version_is_passed_over(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    shim(repo / "node_modules", "1.28.0")
    assert locate(repo, ENGINE)["value"]["source"] == "plugin"


def test_repo_copy_that_resolves_outside_the_repo_is_not_used(tmp_path) -> None:
    outside = shim(tmp_path / unique("outside") / "node_modules", "1.29.2")
    repo = tmp_path / unique("repo")
    link_dir(outside, repo / "node_modules" / "@hpcc-js" / "wasm-graphviz")
    assert locate(repo, ENGINE)["value"]["source"] == "plugin"


def test_missing_or_wrong_everywhere_gives_an_install_hint(tmp_path) -> None:
    repo = tmp_path / unique("repo")
    shim(repo / "node_modules", "1.28.0")
    engine = tmp_path / unique("engine")
    engine.mkdir()
    result = locate(repo, engine)
    assert result["ok"] is False and result["token"] == "graphviz-missing"
    assert "npm install --save-dev --ignore-scripts @hpcc-js/wasm-graphviz@1.29.2" in result["details"][0]
    assert "found repo 1.28.0" in result["details"][0]


def test_installed_graphviz_never_spawns_or_uses_the_network() -> None:  # Threat Model, Supply chain
    text = (INSTALLED / "dist" / "index.js").read_text(encoding="utf-8")
    assert not re.search(r"child_process|worker_threads|node:(http|https|net|tls|dgram)\b", text)
