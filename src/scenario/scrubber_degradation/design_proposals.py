"""design_proposals.json — post-run scrubber design for the next scrubber_degradation run.

Unified with ssos_eclss_loop naming (``design_proposals.json``). Scrubber uses
topology kinds (``add_edge``, ``add_node``, ``set_parameter``). SSOS graph kinds
belong to ``ssos_eclss_loop`` only.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List

from environment.protocol import TopologyEdge, TopologyGraph, TopologyNode
from environment.scrubber.eclss_ops.design_state import (
    DesignStateManager,
    default_parameters,
    default_topology,
)

DESIGN_DOMAIN = "scrubber"

SCRUBBER_CHANGE_KINDS = frozenset(
    {
        "add_edge",
        "add_node",
        "set_parameter",
    }
)


def load_design_proposals(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("design_proposals.json must be a JSON object")
    return data


def validate_design_proposals(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    domain = data.get("design_domain")
    if domain is not None and domain != DESIGN_DOMAIN:
        errors.append(f"design_domain must be {DESIGN_DOMAIN!r}, got {domain!r}")

    changes = data.get("changes")
    if not isinstance(changes, list):
        return errors + ["changes must be a list"]

    for index, change in enumerate(changes):
        if not isinstance(change, dict):
            errors.append(f"changes[{index}] must be an object")
            continue
        kind = change.get("change_kind")
        if kind not in SCRUBBER_CHANGE_KINDS:
            errors.append(
                f"changes[{index}].change_kind must be one of {sorted(SCRUBBER_CHANGE_KINDS)}"
            )
        payload = change.get("payload")
        if payload is not None and not isinstance(payload, dict):
            errors.append(f"changes[{index}].payload must be an object")
    return errors


def topology_from_dict(data: Dict[str, Any]) -> TopologyGraph:
    return TopologyGraph(
        nodes=[
            TopologyNode(
                id=str(node["id"]),
                name=str(node.get("name", node["id"])),
                kind=str(node.get("kind", "volume")),
            )
            for node in data.get("nodes", [])
        ],
        edges=[
            TopologyEdge(
                source=str(edge["source"]),
                target=str(edge["target"]),
                kind=str(edge.get("kind", "flow")),
            )
            for edge in data.get("edges", [])
        ],
    )


def _design_manager_from_config(config: Dict[str, Any]) -> DesignStateManager:
    params = dict(default_parameters())
    raw_params = config.get("design_parameters") or {}
    for key, value in raw_params.items():
        params[key] = float(value)
    topo_data = config.get("design_topology")
    topology = topology_from_dict(topo_data) if topo_data else default_topology()
    return DesignStateManager(topology=topology, parameters=params)


def apply_design_proposals(config: Dict[str, Any], proposals: Dict[str, Any]) -> Dict[str, Any]:
    """Merge scrubber design_proposals into scenario config (pre-run only)."""
    errors = validate_design_proposals(proposals)
    if errors:
        raise ValueError("; ".join(errors))

    merged = copy.deepcopy(config)
    design = _design_manager_from_config(merged)
    for change in proposals.get("changes") or []:
        kind = str(change.get("change_kind", ""))
        payload = change.get("payload") or {}
        if not isinstance(payload, dict):
            raise ValueError(f"change payload must be an object for {kind!r}")
        design.apply_dict_change(kind, payload)

    merged["design_topology"] = design.topology.to_dict()
    merged["design_parameters"] = dict(design.parameters)
    return merged


def write_design_proposals(path: Path, proposals: Dict[str, Any]) -> None:
    payload = dict(proposals)
    payload.setdefault("design_domain", DESIGN_DOMAIN)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
