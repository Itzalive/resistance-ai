"""The architecture records tool, `change` (spec 2026-11-21-defining-architecture-records-design.md, "The helper
tool", "`change`")."""

from __future__ import annotations

import json
import shutil

import pytest

from arch_delta_support import RECORDS_SCRIPT, error_lines, make_repo, require_node, run_tool, unique, write_json

require_node()


def component(name: str, title: str) -> str:
    return f"    {name} = component '{title}' {{\n      metadata {{\n        code 'shop.{name}'\n      }}\n    }}\n"


def shop(parts: str, links: str) -> str:
    return f"model {{\n  shop = system 'Shop' {{\n{parts}{links}  }}\n}}\n"


BEFORE_MODEL = shop(component("a", "A") + component("b", "B") + component("c", "C"), "    a -> b\n")
AFTER_MODEL = shop(component("a", "A2") + component("b", "B") + component("d", "D"), "    a -> b\n    d -> b\n")
DEPS = [["shop.a.m", "shop.b.m"], ["shop.b.m", "shop.a.m"]]


def decision(id_: str, binds: list, reason: str = "Because.") -> dict:
    return {"id": id_, "decision": f"Decision {id_}.", "reason": reason, "rejected": [], "binds": binds,
            "status": "current", "evidence": "checked", "sources": ["src"]}


D1 = decision("D-1", ["shop.a"])
D2 = decision("D-2", ["shop.b"])
H1 = {"id": "H-1", "what": "Why does b call a?", "binds": ["shop.b"], "evidence": "search"}
C1 = {"id": "C-1", "name": "API", "owner": "shop.a", "bound": ["shop.b"], "obligations": ["O."], "compatibility": None}
KEYS = ["id", "date", "run", "asked_by", "summary", "rejected", "elements", "decisions", "holes", "contracts", "gap",
        "check", "approved"]


def change_repo(tmp_path):
    """A repository whose before copy is in build/before and whose model is the run's draft."""
    repo = make_repo(tmp_path, BEFORE_MODEL)
    folder = repo / "docs" / "architecture"
    write_json(folder / "decisions" / "x.json", {"title": "X", "decisions": [D1, D2], "holes": []})
    write_json(folder / "contracts" / "api.json", {"title": "API", "contracts": [C1]})
    shutil.copytree(folder, repo / "build" / "before")
    (folder / "model.c4").write_text(AFTER_MODEL, encoding="utf-8")
    write_json(folder / "decisions" / "x.json", {"title": "X", "decisions": [decision("D-1", ["shop.a"], "Changed.")],
                                                 "holes": [H1]})
    write_json(folder / "decisions" / "y.json", {"title": "Y", "decisions": [D2], "holes": []})
    (folder / "contracts" / "api.json").unlink()
    write_json(folder / "known-gap.json", {"entries": [{"from": "shop.b", "to": "shop.a", "reason": "b reads a."}]})
    write_json(repo / "build" / "deps.json", {"edges": DEPS})
    return repo


def change(repo, *extra: str, name: str = "first", before: str | None = "build/before", text: bool = True):
    args = ["change", "--repo", repo, "--deps", "build/deps.json", "--name", name, "--date", "2026-11-21",
            "--run", "epic"]
    if text:
        args += ["--asked-by", "#1", "--summary", "Did a thing."]
    if before is not None:
        args += ["--before", before]
    return run_tool(*args, *extra, script=RECORDS_SCRIPT)


def written(repo, name: str = "first") -> dict:
    return json.loads((repo / "docs" / "architecture" / "changes" / f"2026-11-21-{name}.json").read_text(encoding="utf-8"))


def test_change_lists_what_the_run_changed(tmp_path) -> None:  # AC-1
    repo = change_repo(tmp_path)
    proc = change(repo, "--rejected", "Keep c.")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "wrote changes/2026-11-21-first.json\n"
    data = written(repo)
    assert list(data) == KEYS
    assert data["elements"] == {"added": ["shop.d"], "changed": ["shop.a", "shop.b"], "removed": ["shop.c"]}
    assert data["decisions"] == {"added": [], "changed": ["D-1"], "removed": []}
    assert data["holes"] == {"added": ["H-1"], "changed": [], "removed": []}
    assert data["contracts"] == {"added": [], "changed": [], "removed": ["C-1"]}
    assert data["gap"] == {"added": [["shop.b", "shop.a"]], "removed": []}
    assert (data["run"], data["asked_by"], data["summary"], data["rejected"]) == ("epic", "#1", "Did a thing.", ["Keep c."])
    raw = (repo / "docs" / "architecture" / "changes" / "2026-11-21-first.json").read_bytes()
    assert b"\r" not in raw
    assert raw.startswith(b'{\n  "id": "2026-11-21-first",\n')
    assert raw.endswith(b"\n}\n")


def test_change_without_before_adds_everything(tmp_path) -> None:  # AC-2
    repo = change_repo(tmp_path)
    proc = change(repo, before=None)
    assert proc.returncode == 0, proc.stderr
    data = written(repo)
    assert data["elements"]["added"] == ["shop", "shop.a", "shop.b", "shop.d"]
    assert data["decisions"]["added"] == ["D-1", "D-2"]
    assert data["holes"]["added"] == ["H-1"]
    assert data["gap"]["added"] == [["shop.b", "shop.a"]]


def test_change_quotes_the_delta_check(tmp_path) -> None:  # AC-3
    repo = change_repo(tmp_path)
    write_json(repo / "build" / "deps.json", {"edges": [*DEPS, ["shop.d.m", "shop.a.m"]]})
    proc = change(repo)
    assert proc.returncode == 0, proc.stderr
    delta = run_tool("check", "--repo", repo, "--deps", "build/deps.json")
    assert delta.returncode == 1
    data = written(repo)
    assert data["check"] == {"exit": 1, "summary": delta.stdout.rstrip("\n").splitlines()[-1], "output": delta.stdout}


def test_written_change_exports_as_a_draft(tmp_path) -> None:  # AC-4
    repo = change_repo(tmp_path)
    assert change(repo).returncode == 0
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    [record] = json.loads(proc.stdout)["changes"]
    assert (record["id"], record["approved"]) == ("2026-11-21-first", None)


@pytest.mark.parametrize(("extra", "name"), [
    ([], "Bad_Name"),
    ([], "n" * 54),
    (["--rejected", ""], "first"),
], ids=["name", "long", "rejected"])
def test_change_refuses_bad_values_and_writes_nothing(tmp_path, extra: list, name: str) -> None:  # AC-5
    repo = change_repo(tmp_path)
    proc = change(repo, *extra, name=name)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: bad-input: changes/")
    assert not (repo / "docs" / "architecture" / "changes").exists()


@pytest.mark.parametrize(("flag", "value", "line"), [
    ("--date", "2026-02-30", "error: bad-input: changes/2026-02-30-first.json: date: not a real date"),
    ("--summary", "", "error: bad-input: changes/2026-11-21-first.json: summary: must be a non-empty string"),
    ("--asked-by", "", "error: bad-input: changes/2026-11-21-first.json: asked_by: must be a non-empty string"),
], ids=["date", "summary", "asked-by"])
def test_change_refuses_bad_text_and_dates(tmp_path, flag: str, value: str, line: str) -> None:  # AC-5
    repo = change_repo(tmp_path)
    args = ["change", "--repo", repo, "--deps", "build/deps.json", "--name", "first", "--run", "epic",
            "--before", "build/before"]
    values = {"--date": "2026-11-21", "--asked-by": "#1", "--summary": "S.", flag: value}
    proc = run_tool(*args, *[part for pair in values.items() for part in pair], script=RECORDS_SCRIPT)
    assert proc.returncode == 2
    assert line in error_lines(proc)
    assert not (repo / "docs" / "architecture" / "changes").exists()


def test_change_accepts_a_64_character_id(tmp_path) -> None:  # AC-5
    repo = change_repo(tmp_path)
    proc = change(repo, name="n" * 53)
    assert proc.returncode == 0, proc.stderr
    assert written(repo, "n" * 53)["id"] == "2026-11-21-" + "n" * 53


def test_change_stops_when_check_fails(tmp_path) -> None:  # AC-5
    repo = change_repo(tmp_path)
    (repo / "build" / "deps.json").write_text("{not json", encoding="utf-8")
    proc = change(repo)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith("error: bad-input: --deps is not valid JSON")
    assert not (repo / "docs" / "architecture" / "changes").exists()


def test_change_replaces_its_draft_but_never_an_approved_file(tmp_path) -> None:  # AC-6
    repo = change_repo(tmp_path)
    assert change(repo).returncode == 0
    assert change(repo, "--rejected", "Second thoughts.").returncode == 0
    assert written(repo)["rejected"] == ["Second thoughts."]
    target = repo / "docs" / "architecture" / "changes" / "2026-11-21-first.json"
    data = written(repo)
    data["approved"] = {"by": "owner", "date": "2026-11-21"}
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    before = target.read_bytes()
    proc = change(repo)
    assert proc.returncode == 2
    assert error_lines(proc) == ["error: out-error: changes/2026-11-21-first.json is not a draft and is never replaced"]
    assert target.read_bytes() == before


def test_flag_text_is_cleaned_by_export(tmp_path) -> None:  # AC-7
    repo = change_repo(tmp_path)
    esc = chr(27)
    args = ["change", "--repo", repo, "--deps", "build/deps.json", "--name", "first", "--date", "2026-11-21",
            "--run", "epic", "--asked-by", "#1", "--summary", f"{esc}[31mred{esc}[0m{chr(10)}line"]
    assert run_tool(*args, script=RECORDS_SCRIPT).returncode == 0
    [record] = json.loads(run_tool("export", "--repo", repo).stdout)["changes"]
    assert record["summary"] == f"red{chr(10)}line"


@pytest.mark.parametrize(("before", "token"), [
    ("outside", "outside-repo"),
    ("build/nothing", "bad-input"),
    ("docs/architecture", "bad-input"),
    ("docs/architecture/old", "bad-input"),
    ("docs", "bad-input"),
], ids=["outside", "missing", "model", "inside", "contains"])
def test_before_must_be_inside_the_repo_and_apart_from_the_model(tmp_path, before: str, token: str) -> None:  # AC-8
    repo = change_repo(tmp_path)
    (repo / "docs" / "architecture" / "old").mkdir()
    if before == "outside":
        elsewhere = tmp_path / unique("elsewhere")
        elsewhere.mkdir()
        before = str(elsewhere)
    proc = change(repo, before=before)
    assert proc.returncode == 2
    assert error_lines(proc)[0].startswith(f"error: {token}: --before")
    assert not (repo / "docs" / "architecture" / "changes").exists()


def test_a_traversal_name_is_refused_before_any_path_is_read(tmp_path) -> None:  # trust boundary: --name
    repo = change_repo(tmp_path)
    # Where the name would lead: docs/architecture/changes/2026-11-21-x/../../../outside.json is docs/outside.json
    (repo / "docs" / "outside.json").write_text("{not json", encoding="utf-8")
    proc = change(repo, name="x/../../../outside")
    assert proc.returncode == 2
    assert error_lines(proc) == [
        "error: bad-input: changes/2026-11-21-x/../../../outside.json: -: not a valid file name here"]
    assert not (repo / "docs" / "architecture" / "changes").exists()


def snapshot(repo) -> dict:
    folder = repo / "docs" / "architecture" / "changes"
    return {p.name: p.read_bytes() for p in sorted(folder.iterdir())}


def test_compare_reports_same_differs_and_missing(tmp_path) -> None:  # AC-9
    repo = change_repo(tmp_path)
    assert change(repo, "--rejected", "Keep c.").returncode == 0
    files = snapshot(repo)
    same = change(repo, "--compare", text=False)
    assert (same.returncode, same.stdout) == (0, "same changes/2026-11-21-first.json\n"), same.stderr
    folder = repo / "docs" / "architecture"
    (folder / "model.c4").write_text(
        shop(component("a", "A2") + component("b", "B") + component("d", "D") + component("e", "E"), "    a -> b\n    d -> b\n"),
        encoding="utf-8")
    differs = change(repo, "--compare", text=False)
    assert (differs.returncode, differs.stdout) == (1, "differs changes/2026-11-21-first.json\n"), differs.stderr
    missing = change(repo, "--compare", name="other", text=False)
    assert (missing.returncode, missing.stdout) == (1, "missing changes/2026-11-21-other.json\n"), missing.stderr
    assert snapshot(repo) == files
