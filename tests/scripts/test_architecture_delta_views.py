"""Area and capability views in export (spec 2026-11-17-architecture-docs-design.md, plan 1)."""

from __future__ import annotations

import json
from pathlib import Path

from arch_delta_support import call, error_lines, make_repo, require_node, run_tool, write_json

require_node()

BASE = """specification {
  relationship http
}
model {
  shop = system 'Shop' {
    web = container 'Web'
    api = container 'API' {
      db = component 'DB'
    }
  }
  pay = system 'Pay'
  shop.web -> shop.api 'places order'
  shop.api -[http]-> pay 'charges'
  pay -[http]-> shop.api.db 'settles'
}
"""


def repo_with(tmp_path: Path, views: str) -> Path:
    return make_repo(tmp_path, BASE + "views {\n" + views + "}\n")


def export(repo: Path) -> dict:
    proc = run_tool("export", "--repo", repo)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def both_commands(repo: Path) -> list[list[str]]:
    deps = write_json(repo / "deps.json", {"edges": []})
    return [error_lines(run_tool("export", "--repo", repo)), error_lines(run_tool("check", "--repo", repo, "--deps", deps))]


AREAS = """  view area-shop of shop {
    include *
  }
  view area-two {
    title 'Two'
    description 'Front and back'
    include shop.web, pay
    group 'G' {
      include shop.api
    }
  }
  view area-plain {
    include pay
  }
  view other {
    include *
  }
"""


def test_area_views_are_exported(tmp_path) -> None:  # AC-1 (areas), AC-6
    data = export(repo_with(tmp_path, AREAS))
    assert data["areas"] == [
        {"name": "plain", "title": "area-plain", "description": None, "elements": ["pay"]},
        {"name": "shop", "title": "Shop", "description": None, "elements": ["shop", "shop.api", "shop.api.db", "shop.web"]},
        {"name": "two", "title": "Two", "description": "Front and back", "elements": ["pay", "shop", "shop.api", "shop.web"]},
    ]


LONG = "a" * 65

BAD_VIEWS = f"""  dynamic view area-flow {{
    shop.web -> shop.api
  }}
  view capability-Box {{
    include *
  }}
  view area-Shop {{
    include *
  }}
  view area-con {{
    include *
  }}
  view area-{LONG} {{
    include *
  }}
"""


def test_bad_view_types_and_names_are_model_errors(tmp_path) -> None:  # AC-3 (types and names)
    expected = [
        "error: model-error: view area-Shop: Shop is not a valid name",
        f"error: model-error: view area-{LONG}: {LONG} is not a valid name",
        "error: model-error: view area-con: con is not a valid name",
        "error: model-error: view area-flow: an area view must be an element view",
        "error: model-error: view capability-Box: a capability view must be a dynamic view",
    ]
    assert both_commands(repo_with(tmp_path, BAD_VIEWS)) == [expected, expected]


CAPS = """  dynamic view capability-order {
    title 'Place an order'
    shop.web -> shop.api 'sends order'
    parallel {
      shop.api -> pay 'charges card'
      shop.api -> shop.web 'confirms'
    }
    pay -> shop.api
  }
  dynamic view capability-quiet {
    shop.web -> shop.api
    shop.api -> shop.web
  }
"""


def test_capability_steps_are_calls_and_replies(tmp_path) -> None:  # AC-1 (capabilities), AC-2
    data = export(repo_with(tmp_path, CAPS))
    assert data["capabilities"] == [
        {"name": "order", "title": "Place an order", "description": None, "steps": [
            {"from": "shop.web", "to": "shop.api", "label": "sends order", "reply": False, "kinds": ["uses"]},
            {"from": "shop.api", "to": "pay", "label": "charges card", "reply": False, "kinds": ["http"]},
            {"from": "shop.api", "to": "shop.web", "label": "confirms", "reply": True, "kinds": ["uses"]},
            {"from": "pay", "to": "shop.api", "label": "settles", "reply": False, "kinds": ["http"]},
        ]},
        {"name": "quiet", "title": "capability-quiet", "description": None, "steps": [
            {"from": "shop.web", "to": "shop.api", "label": "places order", "reply": False, "kinds": ["uses"]},
            {"from": "shop.api", "to": "shop.web", "label": None, "reply": True, "kinds": ["uses"]},
        ]},
    ]


def test_a_step_with_no_relationship_is_a_model_error(tmp_path) -> None:  # AC-3 (steps)
    views = CAPS + """  dynamic view capability-bad {
    shop.web -> shop.api
    parallel {
      shop.web -> shop.api
      shop.api -> pay
    }
    shop.web -> pay
    shop.api.db -> shop.web
  }
  dynamic view area-x {
    shop.web -> pay
  }
"""
    expected = [
        "error: model-error: view area-x: an area view must be an element view",
        "error: model-error: view capability-bad: step 4: shop.web -> pay follows no relationship",
        "error: model-error: view capability-bad: step 5: shop.api.db -> shop.web follows no relationship",
    ]
    assert both_commands(repo_with(tmp_path, views)) == [expected, expected]


def test_view_text_is_not_cut(tmp_path) -> None:  # spec, format 4: text values are not cut
    long = "t" * 250
    views = f"""  view area-long {{
    title '{long}'
    description '{long}'
    include pay
  }}
  dynamic view capability-long {{
    title '{long}'
    description '{long}'
    shop.web -> shop.api '{long}'
  }}
"""
    data = export(repo_with(tmp_path, views))
    area, capability = data["areas"][0], data["capabilities"][0]
    assert [area["title"], area["description"], capability["title"], capability["description"]] == [long] * 4
    assert capability["steps"][0]["label"] == long


def test_view_ids_are_cut(tmp_path) -> None:  # spec, format 4: id values are cut at 200
    name, kind = "e" * 201, "k" * 201
    model = f"""specification {{
  relationship {kind}
}}
model {{
  {name} = component 'E'
  b = component 'B'
  {name} -[{kind}]-> b
}}
views {{
  view area-x {{
    include {name}
  }}
  dynamic view capability-x {{
    {name} -> b
  }}
}}
"""
    data = export(make_repo(tmp_path, model))
    cut = lambda value: value[:199] + "…"
    assert data["areas"][0]["elements"] == [cut(name)]
    assert data["capabilities"][0]["steps"] == [{"from": cut(name), "to": "b", "label": None, "reply": False, "kinds": [cut(kind)]}]


def test_step_kinds_are_those_of_its_own_direction_sorted(tmp_path) -> None:  # AC-2 (kinds)
    model = """specification {
  relationship http
  relationship event
  relationship push
}
model {
  a = component 'A'
  b = component 'B'
  a -[http]-> b
  a -[event]-> b
  b -[push]-> a
}
views {
  dynamic view capability-k {
    a -> b
  }
}
"""
    data = export(make_repo(tmp_path, model))
    assert data["capabilities"][0]["steps"] == [{"from": "a", "to": "b", "label": None, "reply": False, "kinds": ["event", "http"]}]


MB = 1024 * 1024


def test_generated_folder_counts_apart(tmp_path) -> None:  # AC-7
    repo = make_repo(tmp_path)
    folder = repo / "docs" / "architecture"
    for i in range(600):
        (folder / f"f{i}.txt").write_text("x", encoding="utf-8")
    generated = folder / "generated"
    generated.mkdir()
    for i in range(1500):
        (generated / f"g{i}.md").write_text("x", encoding="utf-8")
    assert run_tool("export", "--repo", repo).returncode == 0
    for i in range(1500, 2001):
        (generated / f"g{i}.md").write_text("x", encoding="utf-8")
    assert error_lines(run_tool("export", "--repo", repo)) == ["error: model-size: generated: more than 2000 files"]


def test_generated_bytes_count_apart(tmp_path) -> None:
    folder = tmp_path / "m"
    (folder / "generated").mkdir(parents=True)
    (folder / "big.bin").write_bytes(b"\0" * (30 * MB))
    (folder / "generated" / "big.bin").write_bytes(b"\0" * (30 * MB))
    assert call("walk.mjs", "walkModelDir", str(folder))["ok"] is True


def test_likec4_source_in_generated_is_refused(tmp_path) -> None:  # AC-7
    repo = make_repo(tmp_path)
    areas = repo / "docs" / "architecture" / "generated" / "areas"
    areas.mkdir(parents=True)
    (areas / "x.c4").write_text("model {\n}\n", encoding="utf-8")
    assert error_lines(run_tool("export", "--repo", repo)) == [
        "error: model-error: generated/areas/x.c4 is a LikeC4 source file in the generated folder",
    ]


def test_generated_byte_limit_names_the_folder(tmp_path) -> None:  # AC-7
    folder = tmp_path / "m"
    (folder / "generated").mkdir(parents=True)
    (folder / "generated" / "big.bin").write_bytes(b"\0" * (50 * MB + 1))
    result = call("walk.mjs", "walkModelDir", str(folder))
    assert (result["token"], result["details"]) == ("model-size", ["generated: more than 50 MB in total"])


def test_likec4_extension_in_generated_is_refused(tmp_path) -> None:  # AC-7
    areas = tmp_path / "m" / "generated" / "areas"
    areas.mkdir(parents=True)
    (areas / "x.likec4").write_text("model {\n}\n", encoding="utf-8")
    result = call("walk.mjs", "walkModelDir", str(tmp_path / "m"))
    assert (result["token"], result["details"]) == (
        "model-error", ["generated/areas/x.likec4 is a LikeC4 source file in the generated folder"])


def test_a_root_file_named_generated_counts_with_the_model(tmp_path) -> None:
    folder = tmp_path / "m"
    folder.mkdir()
    (folder / "generated").write_bytes(b"\0" * (30 * MB))
    (folder / "big.bin").write_bytes(b"\0" * (30 * MB))
    result = call("walk.mjs", "walkModelDir", str(folder))
    assert (result["token"], result["details"]) == ("model-size", ["more than 50 MB in total"])
