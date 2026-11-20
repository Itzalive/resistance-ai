"""The docs tool's writer: write rule 3 (spec 2026-11-17-architecture-docs-design.md, "The tool")."""

from __future__ import annotations

from pathlib import Path

from arch_delta_support import DOCS_LIB, call, require_node

require_node()


def write(folder: Path, files: dict, listed: dict) -> dict:
    return call("writer.mjs", "writeOutput", str(folder), files, listed, lib=DOCS_LIB)


def test_write_output_writes_replaces_and_deletes(tmp_path) -> None:
    folder = tmp_path / "out"
    (folder / "areas").mkdir(parents=True)
    (folder / "areas" / "old.md").write_text("old", encoding="utf-8")
    (folder / "README.md").write_text("before", encoding="utf-8")
    (folder / ".architecture-docs-9-0").write_text("partial", encoding="utf-8")
    result = write(folder, {"README.md": "after\n", "pack/model.json": "{}\n"},
                   {"files": ["README.md", "areas/old.md"], "temps": [".architecture-docs-9-0"]})
    assert result["value"] == {"wrote": 2, "removed": 1}
    assert (folder / "README.md").read_bytes() == b"after\n"
    assert (folder / "pack" / "model.json").read_bytes() == b"{}\n"
    assert sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")) == ["README.md", "pack", "pack/model.json"]


def test_write_output_keeps_a_listed_file_that_differs_only_in_case(tmp_path) -> None:
    # On a case-insensitive file system `pack/Model.json` is the produced file; deleting it would delete the new one.
    folder = tmp_path / "out"
    (folder / "pack").mkdir(parents=True)
    (folder / "pack" / "Model.json").write_text('{"generated": "architecture-docs"}', encoding="utf-8")
    result = write(folder, {"pack/model.json": "new\n"}, {"files": ["pack/Model.json"], "temps": []})
    assert result["value"] == {"wrote": 1, "removed": 0}
    assert (folder / "pack" / "model.json").read_bytes() == b"new\n"


def test_write_output_creates_the_folder_and_its_parents(tmp_path) -> None:
    folder = tmp_path / "a" / "b" / "out"
    assert write(folder, {"README.md": "x\n"}, {"files": [], "temps": []})["value"] == {"wrote": 1, "removed": 0}
    assert (folder / "README.md").is_file()


def test_write_output_removes_empty_folders(tmp_path) -> None:
    folder = tmp_path / "out"
    (folder / "pack" / "areas").mkdir(parents=True)
    (folder / "pack" / "areas" / "x.md").write_text("x", encoding="utf-8")
    write(folder, {"README.md": "x\n"}, {"files": ["pack/areas/x.md"], "temps": []})
    assert sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")) == ["README.md"]


def test_write_output_creates_nested_named_folders(tmp_path) -> None:
    folder = tmp_path / "out"
    folder.mkdir()
    assert write(folder, {"pack/areas/a.md": "x\n"}, {"files": [], "temps": []})["value"] == {"wrote": 1, "removed": 0}
    assert (folder / "pack" / "areas" / "a.md").read_bytes() == b"x\n"


def test_write_output_deletes_nothing_when_a_write_fails(tmp_path) -> None:
    folder = tmp_path / "out"
    (folder / "README.md").mkdir(parents=True)
    (folder / "README.md" / "inner").write_text("x", encoding="utf-8")
    (folder / "areas").mkdir()
    (folder / "areas" / "old.md").write_text("old", encoding="utf-8")
    result = write(folder, {"README.md": "x\n"}, {"files": ["areas/old.md"], "temps": []})
    assert result["token"] == "out-error"
    assert (folder / "areas" / "old.md").read_text(encoding="utf-8") == "old"


def test_write_output_names_a_failed_replace(tmp_path) -> None:
    folder = tmp_path / "out"
    (folder / "README.md").mkdir(parents=True)
    (folder / "README.md" / "inner").write_text("x", encoding="utf-8")
    result = write(folder, {"README.md": "x\n"}, {"files": [], "temps": []})
    assert result["token"] == "out-error"
    assert result["details"][0].startswith("could not replace README.md: ")
