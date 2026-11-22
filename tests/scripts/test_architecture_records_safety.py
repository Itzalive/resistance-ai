"""Least privilege of the architecture records tool (spec 2026-11-21-defining-architecture-records-design.md, Scope
and Threat Model)."""

from __future__ import annotations

import re

from arch_delta_support import RECORDS_LIB, RECORDS_SCRIPT

CHANGES_FILES = re.compile(
    r"(?<!stdout\.)(?<!stderr\.)\bwrite(Sync)?\s*\("
    r"|\b(writeFile|appendFile|mkdir|rmdir|rm|unlink|rename|copyFile|cp|createWriteStream|symlink|link|truncate"
    r"|chmod|chown|utimes|mkdtemp|writev|ftruncate|futimes|lutimes|lchown|lchmod|fchmod|fchown)(Sync)?\s*\("
)


def sources() -> list:
    return [RECORDS_SCRIPT, *sorted(RECORDS_LIB.glob("*.mjs"))]


def test_only_the_writer_changes_files() -> None:
    checked = [source for source in sources() if source.name != "writer.mjs"]
    assert len(checked) >= 4
    for source in checked:
        assert not CHANGES_FILES.search(source.read_text(encoding="utf-8")), source


def test_records_tool_never_spawns_or_uses_the_network() -> None:
    forbidden = re.compile(r"child_process|worker_threads|fs/promises|node:(http|https|net|tls|dgram)\b")
    for source in sources():
        assert not forbidden.search(source.read_text(encoding="utf-8")), source


def test_files_are_opened_only_for_reading() -> None:
    for source in sources():
        assert not re.search(r"\bfs\.open\s*\(|\bopen\s*\(|openSync\(", source.read_text(encoding="utf-8")), source
