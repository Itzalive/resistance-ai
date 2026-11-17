"""Area and capability views in export (spec 2026-11-17-architecture-docs-design.md, plan 1)."""

from __future__ import annotations

import json
from pathlib import Path

from arch_delta_support import error_lines, make_repo, require_node, run_tool, write_json

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
