"""The records tool's writer (spec 2026-11-21-defining-architecture-records-design.md, "`change`": the write)."""

from __future__ import annotations

import json

from arch_delta_support import RECORDS_LIB, call, require_node, unique

require_node()

TEXT = '{\n  "id": "2026-11-21-first"\n}\n'


def write(model_dir, text: str = TEXT) -> dict:
    return call("writer.mjs", "writeChange", str(model_dir), "2026-11-21-first", text, lib=RECORDS_LIB)


def model(tmp_path):
    folder = tmp_path / unique("model")
    folder.mkdir()
    return folder


def test_writer_creates_the_folder_and_writes_lf(tmp_path) -> None:
    folder = model(tmp_path)
    assert write(folder) == {"ok": True, "value": None}
    assert (folder / "changes" / "2026-11-21-first.json").read_bytes() == TEXT.encode()


def test_writer_replaces_a_draft(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").mkdir()
    (folder / "changes" / "2026-11-21-first.json").write_text(json.dumps({"approved": None}), encoding="utf-8")
    assert write(folder)["ok"] is True
    assert (folder / "changes" / "2026-11-21-first.json").read_text(encoding="utf-8") == TEXT
    assert sorted(p.name for p in (folder / "changes").iterdir()) == ["2026-11-21-first.json"]


def test_writer_never_replaces_an_approved_file(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").mkdir()
    target = folder / "changes" / "2026-11-21-first.json"
    target.write_text(json.dumps({"approved": {"by": "owner", "date": "2026-11-21"}}), encoding="utf-8")
    before = target.read_bytes()
    out = write(folder)
    assert (out["ok"], out["token"], out["details"]) == (
        False, "out-error", ["changes/2026-11-21-first.json is approved and is never replaced"])
    assert target.read_bytes() == before
    assert sorted(p.name for p in (folder / "changes").iterdir()) == ["2026-11-21-first.json"]


def test_writer_refuses_a_file_with_no_approved_field(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").mkdir()
    target = folder / "changes" / "2026-11-21-first.json"
    target.write_text("{}", encoding="utf-8")
    assert write(folder)["token"] == "out-error"
    assert target.read_text(encoding="utf-8") == "{}"


def test_writer_removes_left_over_temporary_files(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").mkdir()
    (folder / "changes" / ".architecture-records-17-3").write_text("x", encoding="utf-8")
    (folder / "changes" / ".gitkeep").write_text("", encoding="utf-8")
    assert write(folder)["ok"] is True
    assert sorted(p.name for p in (folder / "changes").iterdir()) == [".gitkeep", "2026-11-21-first.json"]


def test_writer_failure_is_out_error(tmp_path) -> None:
    folder = model(tmp_path)
    (folder / "changes").write_text("not a folder", encoding="utf-8")
    out = write(folder)
    assert (out["ok"], out["token"]) == (False, "out-error")
    assert out["details"][0].startswith("could not create changes: ")
