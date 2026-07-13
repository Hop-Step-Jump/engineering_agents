"""Tests for scrubber_degradation design_proposals apply path."""

from __future__ import annotations

import json
from pathlib import Path

from scenario.runner import build_eclss, run_scenario
from scenario.scrubber_degradation.design_proposals import (
    DESIGN_DOMAIN,
    apply_design_proposals,
    load_design_proposals,
    validate_design_proposals,
)
from scenario.scrubber_degradation.scenario_run import ScrubberDegradationScenario


def test_validate_scrubber_design_proposals_accepts_topology_kinds():
    errors = validate_design_proposals(
        {
            "design_domain": DESIGN_DOMAIN,
            "changes": [
                {
                    "change_kind": "add_edge",
                    "payload": {"node_a": "manifold", "node_b": "scrubber", "kind": "bypass"},
                },
                {"change_kind": "set_parameter", "payload": {"key": "scrubber_base_efficiency", "value": 0.99}},
            ],
        }
    )
    assert errors == []


def test_validate_scrubber_design_proposals_rejects_ssos_kinds():
    errors = validate_design_proposals(
        {
            "design_domain": DESIGN_DOMAIN,
            "changes": [{"change_kind": "graph_rewire", "payload": {}}],
        }
    )
    assert any("change_kind" in err for err in errors)


def test_apply_design_proposals_merges_topology_and_parameters():
    config = {
        "design_parameters": {"scrubber_base_efficiency": 0.95},
    }
    proposals = {
        "design_domain": DESIGN_DOMAIN,
        "changes": [
            {
                "change_kind": "add_edge",
                "payload": {"node_a": "manifold", "node_b": "scrubber", "kind": "bypass"},
            },
            {"change_kind": "set_parameter", "payload": {"key": "scrubber_base_efficiency", "value": 0.99}},
        ],
    }
    merged = apply_design_proposals(config, proposals)
    assert merged["design_parameters"]["scrubber_base_efficiency"] == 0.99
    assert any(edge["kind"] == "bypass" for edge in merged["design_topology"]["edges"])

    eclss = build_eclss(merged)
    assert eclss.design.has_bypass_edge()
    assert eclss.scrubber_efficiency == 0.99


def test_scrubber_degradation_apply_proposals(tmp_path: Path):
    first = run_scenario(
        "scrubber_degradation",
        output_dir=tmp_path / "first",
        overrides={"agents": {"mode": "labeled_rule_base"}},
        recreate_output=True,
    )
    proposals_path = first / "design_proposals.json"
    assert proposals_path.exists()
    proposals = load_design_proposals(proposals_path)
    assert proposals.get("design_domain") == DESIGN_DOMAIN
    assert any(c.get("change_kind") == "add_edge" for c in proposals.get("changes", []))

    second = ScrubberDegradationScenario().run(
        output_dir=tmp_path / "second",
        overrides={"agents": {"mode": "none"}, "simulation": {"steps": 5}},
        apply_proposals_path=proposals_path,
        recreate_output=True,
    )
    design_state = [
        json.loads(line)
        for line in (second / "design_state.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert design_state
    edges = design_state[0]["topology"]["edges"]
    assert any(edge.get("kind") == "bypass" for edge in edges)
