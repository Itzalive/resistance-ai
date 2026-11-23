"""Least privilege of the architecture docs tool (spec 2026-11-17-architecture-docs-design.md, Threat Model)."""

from __future__ import annotations

import re

from arch_delta_support import DOCS_LIB, DOCS_SCRIPT

CHANGES_FILES = re.compile(
    r"(?<!stdout\.)(?<!stderr\.)\bwrite(Sync)?\s*\("
    r"|\b(writeFile|appendFile|mkdir|rmdir|rm|unlink|rename|copyFile|cp|createWriteStream|symlink|link|truncate"
    r"|chmod|chown|utimes|mkdtemp|writev|ftruncate|futimes|lutimes|lchown|lchmod|fchmod|fchown)(Sync)?\s*\("
)


def sources() -> list:
    # The script exists from Task 6 on; until then only the modules are checked.
    return [p for p in [DOCS_SCRIPT, *sorted(DOCS_LIB.glob("*.mjs"))] if p.exists()]


def test_only_the_writer_changes_files() -> None:
    for source in sources():
        if source.name == "writer.mjs":
            continue
        assert not CHANGES_FILES.search(source.read_text(encoding="utf-8")), source


def test_docs_tool_never_spawns_or_uses_the_network() -> None:
    forbidden = re.compile(r"child_process|worker_threads|fs/promises|node:(http|https|net|tls|dgram)\b")
    for source in sources():
        assert not forbidden.search(source.read_text(encoding="utf-8")), source


def test_files_are_opened_only_for_reading() -> None:
    for source in sources():
        for match in re.finditer(r"openSync\(([^)]*)\)", source.read_text(encoding="utf-8")):
            assert match.group(1).rstrip().endswith("'r'"), source


def test_files_are_never_opened_asynchronously() -> None:
    # `fs.open` (or a bare `open` taken from `fs`) takes its flags out of sight of the `openSync` check above.
    forbidden = re.compile(r"\bfs\.open\s*\(|\bopen\s*\(")
    for source in sources():
        assert not forbidden.search(source.read_text(encoding="utf-8")), source


def test_graphviz_is_loaded_only_through_its_locator() -> None:
    # A static import resolves only from the plugin's folder, so a repository-only install would crash on load.
    static = re.compile(r"""(from|import)\s*\(?\s*['"]@hpcc-js/""")
    for source in sources():
        assert not static.search(source.read_text(encoding="utf-8")), source
