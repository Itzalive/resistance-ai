"""The overview document (spec 2026-11-17-architecture-docs-design.md, "Overview")."""

from __future__ import annotations

import json
import re
from pathlib import Path

from arch_delta_support import DOCS_LIB, DOCS_SCRIPT, call, make_repo, require_node, run_tool

require_node()

MODEL = """specification {
  relationship http
}
model {
  shop = system 'Shop' {
    description 'Sells things'
    web = container 'Web'
    api = container 'API'
  }
  pay = system 'Pay'
  bank = system 'Bank'
  shop.web -> pay 'charges'
  shop.api -> pay
  shop.api -[http]-> pay 'notifies'
  pay -[http]-> bank 'settles'
}
views {
  view area-front of shop {
    include *
  }
  dynamic view capability-buy {
    title 'Buy'
    shop.web -> pay
  }
}
"""


def write(folder: Path, rel: str, data: object) -> None:
    target = folder / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data), encoding="utf-8")


def decision(id_: str, **over) -> dict:
    record = {"id": id_, "decision": "Decide " + id_ + ".", "reason": "Because.", "rejected": [], "binds": ["shop.web"],
              "status": "current", "evidence": "spec", "sources": ["docs/x.md"]}
    record.update(over)
    return record


def change(id_: str, summary: str, approved: object) -> dict:
    lists = {"added": [], "changed": [], "removed": []}
    return {"id": id_, "date": id_[:10], "run": "baseline", "asked_by": "#1", "summary": summary, "rejected": [],
            "elements": lists, "decisions": lists, "holes": lists, "contracts": lists, "gap": {"added": [], "removed": []},
            "check": {"exit": 0, "summary": "ok", "output": "ok\n"}, "approved": approved}


def build(tmp_path: Path) -> Path:
    repo = make_repo(tmp_path, MODEL)
    folder = repo / "docs" / "architecture"
    write(folder, "decisions/core.json", {"title": "Core", "holes": [{"id": "H-1", "what": "Why a bank?", "binds": ["bank"], "evidence": "search"}],
                                          "decisions": [decision("D-1"), decision("D-2", binds=["bank"]),
                                                        decision("P-1", binds=[], obligations=["Data stays in the EU."])]})
    write(folder, "contracts/edge.json", {"title": "Edge", "contracts": [
        {"id": "C-1", "name": "Card API", "owner": "pay", "bound": ["shop.web"], "obligations": ["Ids"], "compatibility": None}]})
    write(folder, "changes/2026-11-01-baseline.json", change("2026-11-01-baseline", "Baseline.", {"by": "Owner", "date": "2026-11-02"}))
    write(folder, "changes/2026-11-05-more.json", change("2026-11-05-more", "More.", None))
    write(folder, "known-gap.json", {"entries": [{"from": "pay", "to": "shop.api", "reason": "cycle in current code"}]})
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    return folder / "generated"


def test_overview_sections(tmp_path) -> None:  # AC-18, AC-20 (overview parts)
    text = (build(tmp_path) / "README.md").read_text(encoding="utf-8")
    sections = text.split("\n\n")
    assert sections[1] == "# Architecture"
    assert "## System" in sections
    assert ('```mermaid\nflowchart LR\n  n1["Bank"]\n  n2["Pay"]\n  n3["Shop"]\n'
            '  n2 -.->|"http"| n1\n  n3 --> n2\n```') in sections
    assert "| Area | Description | Elements |\n| --- | --- | --- |\n| [front](areas/front.md) \\(Shop\\) |  | 3 |" in sections
    assert ("| Capability | Description | Areas |\n| --- | --- | --- |\n"
            "| [buy](capabilities/buy.md) \\(Buy\\) |  | [front](areas/front.md) \\(Shop\\) |") in sections
    principles = sections[sections.index("## Principles"):sections.index("## Contracts")]
    assert principles[1:3] == ["### P\\-1", "Decide P\\-1\\."]
    assert ("| Contract | Owner | Bound | Compatibility |\n| --- | --- | --- | --- |\n"
            "| [C\\-1: Card API](areas/front.md) | [pay](README.md) \\(Pay\\) | [shop\\.web](areas/front.md) \\(Web\\) | No rule stated |") in sections
    changes = sections[sections.index("## Changes") + 1]
    assert changes == ("- [2026\\-11\\-05\\-more](changes/2026-11-05-more.md) \\(2026\\-11\\-05\\): More\\. \\(not yet approved\\)\n"
                       "- [2026\\-11\\-01\\-baseline](changes/2026-11-01-baseline.md) \\(2026\\-11\\-01\\): Baseline\\. "
                       "\\(approved by Owner on 2026\\-11\\-02\\)")
    health = sections[sections.index("## Model health") + 1]
    assert health.startswith("- Known\\-gap entries: 1, see [the improvement list](improvements.md)\n")
    assert "- Coverage: No coverage file" in health
    loose = sections[sections.index("## Not in any area") + 1]
    assert loose == "| Element | Title | Description |\n| --- | --- | --- |\n| bank | Bank |  |\n| pay | Pay |  |"
    after = sections[sections.index("## Not in any area"):]
    assert "### D\\-2" in after and "### H\\-1" in after and "### P\\-1" not in after and "### D\\-1" not in after


def test_overview_lifts_sorts_and_counts(tmp_path) -> None:  # Overview: lifting and kinds; model health; no-area records
    model = MODEL.replace("relationship http\n", "relationship http\n  relationship event\n").replace(
        "  pay -[http]-> bank 'settles'\n",
        "  pay -[http]-> bank 'settles'\n  shop.web -> shop.api\n  shop.api -[http]-> bank\n  shop.web -[event]-> bank\n")
    repo = make_repo(tmp_path, model)
    folder = repo / "docs" / "architecture"
    write(folder, "decisions/core.json", {"title": "Core", "holes": [], "decisions": [decision("D-3", binds=[])]})
    write(folder, "contracts/edge.json", {"title": "Edge", "contracts": [
        {"id": "C-2", "name": "Bank feed", "owner": "bank", "bound": ["pay"], "obligations": ["Daily"], "compatibility": "Additive."}]})
    write(folder, "coverage.json", {"answer": "Most code is mapped.", "baselined": [], "edge_nodes": [],
                                    "counts": {"modules": 3, "groups": 1},
                                    "unmapped": [{"module": "a", "reason": "r"}, {"module": "b", "reason": "r"}]})
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    sections = (folder / "generated" / "README.md").read_text(encoding="utf-8").split("\n\n")
    assert ('```mermaid\nflowchart LR\n  n1["Bank"]\n  n2["Pay"]\n  n3["Shop"]\n'
            '  n2 -.->|"http"| n1\n  n3 -.->|"event#44; http"| n1\n  n3 --> n2\n```') in sections
    see = ", see [the improvement list](improvements.md)"
    assert sections[sections.index("## Model health") + 1] == (
        f"- Known\\-gap entries: 0{see}\n- Open questions: 0{see}\n- Coverage: Most code is mapped\\.{see}\n- Unmapped modules: 2{see}")
    assert ("| [C\\-2: Bank feed](README.md) | [bank](README.md) \\(Bank\\) | [pay](README.md) \\(Pay\\) | Additive\\. |"
            in sections[sections.index("## Contracts") + 1])
    after = sections[sections.index("## Not in any area"):]
    assert "### D\\-3" in after and "### C\\-2: Bank feed" in after


def test_overview_areas_capabilities_changes_and_area_records(tmp_path) -> None:  # Overview: tables, change order, no-area filter
    model = MODEL.replace("  view area-front of shop {\n", "  view area-front of shop {\n    description 'Front desk'\n").replace(
        "    title 'Buy'\n", "    title 'Buy'\n    description 'Buying'\n").replace("views {\n", (
            "views {\n  dynamic view capability-refund {\n    title 'Refund'\n    pay -> shop.api\n  }\n"
            "  dynamic view capability-settle {\n    title 'Settle'\n    pay -> bank\n  }\n"))
    repo = make_repo(tmp_path, model)
    folder = repo / "docs" / "architecture"
    write(folder, "decisions/core.json", {"title": "Core", "decisions": [],
                                          "holes": [{"id": "H-2", "what": "Why a web?", "binds": ["shop.web"], "evidence": "search"}]})
    write(folder, "contracts/edge.json", {"title": "Edge", "contracts": [
        {"id": "C-1", "name": "Card API", "owner": "pay", "bound": ["shop.web"], "obligations": ["Ids"], "compatibility": None}]})
    write(folder, "changes/2026-11-05-a.json", change("2026-11-05-a", "A.", None))
    write(folder, "changes/2026-11-05-b.json", change("2026-11-05-b", "B.", None))
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    sections = (folder / "generated" / "README.md").read_text(encoding="utf-8").split("\n\n")
    assert sections[sections.index("## Areas") + 1].endswith("\n| [front](areas/front.md) \\(Shop\\) | Front desk | 3 |")
    assert sections[sections.index("## Capabilities") + 1].split("\n")[2:] == [
        "| [buy](capabilities/buy.md) \\(Buy\\) | Buying | [front](areas/front.md) \\(Shop\\) |",
        "| [refund](capabilities/refund.md) \\(Refund\\) |  | [front](areas/front.md) \\(Shop\\) |",
        "| [settle](capabilities/settle.md) \\(Settle\\) |  | None |",
    ]
    assert [line.split("]")[0] for line in sections[sections.index("## Changes") + 1].split("\n")] == [
        "- [2026\\-11\\-05\\-a", "- [2026\\-11\\-05\\-b"]
    after = sections[sections.index("## Not in any area"):]
    assert not any(part.startswith(("### C\\-1", "### H\\-2")) for part in after)


def test_overview_empty_sections(tmp_path) -> None:  # Overview: an empty section says so
    repo = make_repo(tmp_path, "model {\n}\n")
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    sections = (repo / "docs" / "architecture" / "generated" / "README.md").read_text(encoding="utf-8").split("\n\n")
    after = {title: sections[sections.index("## " + title) + 1] for title in (
        "System", "Areas", "Capabilities", "Principles", "Contracts", "Changes", "Not in any area")}
    assert after == {
        "System": "The model has no elements\\.", "Areas": "The model has no area views\\.",
        "Capabilities": "The model has no capability views\\.", "Principles": "No principles\\.",
        "Contracts": "No contracts\\.", "Changes": "No change records\\.",
        "Not in any area": "Every element and record is in an area\\.\n",
    }


def test_overview_names_the_arrow_limit(tmp_path) -> None:  # Overview: a system diagram over the arrow limit is not drawn
    names = [f"s{i}" for i in range(10)]
    systems = "".join(f"  {name} = system '{name}'\n" for name in names)
    links = "".join(f"  {a} -> {b}\n" for a in names for b in names if a != b)
    repo = make_repo(tmp_path, "model {\n" + systems + links + "}\n")
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    sections = (repo / "docs" / "architecture" / "generated" / "README.md").read_text(encoding="utf-8").split("\n\n")
    assert sections[sections.index("## System") + 1] == (
        "The Markdown diagram has more than 80 arrows and is not drawn; the HTML page draws it\\.")
    page = (repo / "docs" / "architecture" / "generated" / "index.html").read_text(encoding="utf-8")
    assert page.count('<div class="diagram"><svg') == 1


def test_overview_over_400_arrows_is_drawn_nowhere(tmp_path) -> None:  # Overview: the SVG cap
    names = [f"s{i:02}" for i in range(21)]
    systems = "".join(f"  {name} = system '{name}'\n" for name in names)
    links = "".join(f"  {a} -> {b}\n" for a in names for b in names if a != b)
    repo = make_repo(tmp_path, "model {\n" + systems + links + "}\n")
    proc = run_tool("build", "--repo", repo, script=DOCS_SCRIPT)
    assert proc.returncode == 0, proc.stderr
    folder = repo / "docs" / "architecture" / "generated"
    note = "The system diagram has more than 400 arrows and is not drawn; the tables list every element"
    assert note + "\\." in (folder / "README.md").read_text(encoding="utf-8")
    page = (folder / "index.html").read_text(encoding="utf-8")
    assert note + "." in page and "<svg" not in page


def test_overview_page_matches_and_is_marked(tmp_path) -> None:  # AC-13
    folder = build(tmp_path)
    page = (folder / "index.html").read_text(encoding="utf-8")
    assert page.startswith("<!-- Generated by architecture-docs from the architecture model. Do not edit. -->\n<!doctype html>\n")
    assert '<a href="areas/front.html">front</a> (Shop)' in page and "<script" not in page


def test_overview_page_holds_the_diagram(tmp_path) -> None:  # Writers: the page is built from the same tree as README.md
    page = (build(tmp_path) / "index.html").read_text(encoding="utf-8")
    svg = page[page.index('<div class="diagram"><svg'):page.index("</svg></div>")]
    for label in ("Bank", "Pay", "Shop", "http"):
        assert f">{label}</text>" in svg
    assert svg.count('class="node"') == 3 and svg.count('class="edge"') == 2 and svg.count("stroke-dasharray") == 1


def test_overview_escapes_hostile_model_text(tmp_path) -> None:  # AC-12
    hostile = "[x](javascript:alert(1)) <script> | ` %%{init}%% ;"
    repo = make_repo(tmp_path, "model {\n  a = system '" + hostile + "' {\n    description '" + hostile + "'\n  }\n}\n")
    assert run_tool("build", "--repo", repo, script=DOCS_SCRIPT).returncode == 0
    folder = repo / "docs" / "architecture" / "generated"
    text = (folder / "README.md").read_text(encoding="utf-8")
    page = (folder / "index.html").read_text(encoding="utf-8")
    escaped = "\\[x\\]\\(javascript:alert\\(1\\)\\) &lt;script&gt; \\| \\` %%\\{init\\}%% ;"
    assert f"| a | {escaped} | {escaped} |" in text.split("\n")
    assert "](javascript" not in text and "<script" not in text
    assert "<script" not in page and '<a href="javascript' not in page and "&lt;script&gt;" in page
    node = [line for line in text.split("\n") if line.startswith('  n1["')][0]
    label = node[len('  n1["'):-len('"]')]
    assert '"' not in label and "%%" not in label and "#37;#37;" in label
    assert ";" not in re.sub(r"#[0-9]+;", "", label)
