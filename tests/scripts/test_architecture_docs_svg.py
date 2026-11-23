"""Diagrams drawn as SVG at build time (architecture-docs/svg.mjs): Graphviz flowcharts and drawn sequence diagrams."""

from __future__ import annotations

import re

from arch_delta_support import DOCS_LIB, call, require_node

require_node()

HOSTILE = '<script>"& \\N \\l'
FORBIDDEN = ("<script", "<foreignObject", "href", "<!--", "<title", "<?xml", "<!DOCTYPE", 'fill="white"')


def svg(fn: str, *args) -> str:
    result = call("svg.mjs", fn, *args, lib=DOCS_LIB)
    assert result["ok"], result
    return result["value"]


def assert_drawing_only(text: str) -> None:
    assert text.startswith("<svg") and text.rstrip().endswith("</svg>")
    for word in FORBIDDEN:
        assert word not in text, word
    assert re.search(r"\son\w+=", text) is None


def test_flowchart_draws_frame_nodes_and_three_arrow_styles() -> None:
    nodes = [{"id": "a", "text": "Alpha"}, {"id": "b", "text": "Beta"}, {"id": "c", "text": "Gamma"}]
    arrows = [
        {"from": "a", "to": "b", "dashed": False, "red": False, "text": ""},
        {"from": "b", "to": "c", "dashed": True, "red": False, "text": "http"},
        {"from": "c", "to": "a", "dashed": False, "red": True, "text": "known gap"},
    ]
    text = svg("flowchartSvg", nodes, arrows, {"text": "Front", "ids": ["a", "b"]})
    assert_drawing_only(text)
    for label in ("Alpha", "Beta", "Gamma", "Front", "http", "known gap"):
        assert f">{label}</text>" in text
    assert text.count('class="node"') == 3 and text.count('class="edge"') == 3 and text.count('class="cluster"') == 1
    assert "stroke-dasharray" in text
    assert 'stroke="#d00000"' in text
    assert 'stroke="black"' not in text and 'fill="black"' not in text
    assert 'stroke="currentColor"' in text


def test_flowchart_labels_are_shown_literally() -> None:  # AC-28
    nodes = [{"id": "a", "text": HOSTILE}, {"id": "b", "text": "B"}]
    arrows = [{"from": "a", "to": "b", "dashed": True, "red": False, "text": HOSTILE}]
    text = svg("flowchartSvg", nodes, arrows, {"text": HOSTILE, "ids": ["a"]})
    assert_drawing_only(text)
    assert text.count("&lt;script&gt;&quot;&amp; \\N \\l") == 3


def test_flowchart_is_the_same_on_every_build() -> None:  # AC-8
    nodes = [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]
    arrows = [{"from": "a", "to": "b", "dashed": False, "red": False, "text": ""}]
    assert svg("flowchartSvg", nodes, arrows, None) == svg("flowchartSvg", nodes, arrows, None)


def test_sequence_draws_boxes_in_order_calls_replies_and_a_loop() -> None:  # AC-30
    participants = [{"id": "z", "text": "Zed"}, {"id": "a", "text": "Ay"}]
    messages = [
        {"from": "z", "to": "a", "reply": False, "text": "ask"},
        {"from": "a", "to": "a", "reply": False, "text": "think"},
        {"from": "a", "to": "z", "reply": True, "text": "answer"},
    ]
    text = svg("sequenceSvg", participants, messages)
    assert_drawing_only(text)
    assert text.index(">Zed</text>") < text.index(">Ay</text>")
    assert text.count('class="participant"') == 2 and text.count('class="lifeline"') == 2
    assert text.count('class="call"') == 2 and text.count('class="reply"') == 1
    assert text.count('class="loop"') == 1
    reply = re.search(r'<g class="reply">(.*?)</g>', text, re.S).group(1)
    assert "stroke-dasharray" in reply and ">answer</text>" in reply
    call_group = re.search(r'<g class="call">(.*?)</g>', text, re.S).group(1)
    assert "stroke-dasharray" not in call_group and ">ask</text>" in call_group
    assert text == svg("sequenceSvg", participants, messages)


def test_sequence_labels_are_escaped() -> None:  # AC-28
    text = svg("sequenceSvg", [{"id": "a", "text": HOSTILE}, {"id": "b", "text": "B"}],
               [{"from": "a", "to": "b", "reply": False, "text": HOSTILE}])
    assert_drawing_only(text)
    assert text.count("&lt;script&gt;&quot;&amp; \\N \\l") == 2


def test_figures_fill_each_diagram_block_with_its_svg() -> None:
    figure = {"kind": "sequence", "participants": [{"id": "a", "text": "A"}],
              "messages": [{"from": "a", "to": "a", "reply": False, "text": "x"}]}
    doc = {"title": "T", "blocks": [{"type": "paragraph", "parts": ["p"]},
                                    {"type": "diagram", "text": "sequenceDiagram", "figure": figure}]}
    filled = svg("drawFigures", doc)
    assert filled["blocks"][0] == {"type": "paragraph", "parts": ["p"]}
    block = filled["blocks"][1]
    assert block["text"] == "sequenceDiagram" and block["svg"].startswith("<svg")


def test_drawing_caps_markdown_at_80_arrows_and_svg_at_400() -> None:  # AC-21
    def picture(count: int) -> dict:
        nodes = [{"id": "hub", "text": "Hub"}] + [{"id": f"n{at:03}", "text": f"N{at}"} for at in range(count)]
        arrows = [{"from": f"n{at:03}", "to": "hub", "dashed": False, "red": False, "text": ""} for at in range(count)]
        return {"nodes": nodes, "arrows": arrows, "frame": {"text": "F", "ids": ["hub"]}}

    def block(count: int):
        result = call("area-diagram.mjs", "drawingBlock", picture(count), lib=DOCS_LIB)
        assert result["ok"], result
        return result["value"]

    assert block(80)["text"].startswith("flowchart LR")
    over = block(81)
    assert over["type"] == "diagram" and over["text"] is None and len(over["figure"]["arrows"]) == 81
    assert block(400)["figure"]["kind"] == "flowchart"
    assert block(401) is None
