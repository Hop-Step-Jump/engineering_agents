# API Contracts — SimulatorProtocol & Event Logs

Living document for Week-1 MVP. Update when protocol or log schemas change.

## SimulatorProtocol

Implementations: `MockEclssSimulator` (Week-1), `SsosAdapter` (deferred).

| Method | Returns | Description |
| --- | --- | --- |
| `step()` | `TelemetrySnapshot` | Advance physics one tick |
| `apply_command(cmd)` | `CommandResult` | Temporary recovery action |
| `apply_design_change(change)` | `DesignState` | Permanent topology/parameter mutation |
| `get_topology()` | `TopologyGraph` | Current node/edge graph |
| `get_design_parameters()` | `dict[str, float]` | Mutable design parameters |
| `get_design_state()` | `DesignState` | Topology + parameters snapshot |
| `inject_anomaly(spec)` | `None` | Schedule composite anomaly |

### TelemetrySnapshot

```json
{
  "step": 20,
  "co2_ppm": 1240.5,
  "scrubber_efficiency": 0.72,
  "power_margin_w": 45.0,
  "fan_speed": 0.7,
  "bypass_enabled": false,
  "load_reduced": false,
  "anomaly_flags": ["scrubber_degradation"]
}
```

### RecoveryCommand

```json
{
  "kind": "set_fan_speed",
  "value": 0.9,
  "issued_by": "operator"
}
```

Supported `kind` values: `set_fan_speed`, `enable_bypass`, `reduce_load`.

### DesignChange

```json
{
  "kind": "add_edge",
  "payload": {"node_a": "manifold", "node_b": "scrubber", "kind": "bypass"},
  "proposed_by": "design_engineer"
}
```

Supported `kind` values: `add_edge`, `set_parameter`.

### Health thresholds

| Metric | safe | warning | critical |
| --- | --- | --- | --- |
| CO2 (ppm) | < 1000 | 1000–2000 | ≥ 2000 |
| Power margin (W) | > 0 | 0 to −100 | ≤ −100 |

## ROS2-like topics (`environment/ssos/topics.py`)

| Topic | Direction | Payload |
| --- | --- | --- |
| `/eclss/telemetry/co2_ppm` | pub | float |
| `/eclss/telemetry/scrubber_efficiency` | pub | float |
| `/eclss/telemetry/power_margin_w` | pub | float |
| `/eclss/command/set_fan_speed` | sub | float 0–1 |
| `/eclss/command/enable_bypass` | sub | bool |
| `/eclss/command/reduce_load` | sub | bool |

## JSONL event streams

All runs write under `src/experiments/results/<run_id>/`.

### messages.jsonl

Agent chat (Day 4+).

```json
{"step": 5, "from_role": "monitor", "to_role": "diagnostician", "message": "...", "message_type": "alert", "reasoning": "..."}
```

### telemetry.jsonl

Raw physics snapshot per step (same fields as `TelemetrySnapshot`).

### health_metrics.jsonl

```json
{"step": 5, "co2_status": "safe", "power_status": "safe", "overall": "safe"}
```

### events.jsonl

Commands, anomalies, design changes.

```json
{"step": 20, "kind": "/eclss/events/anomaly", "flags": ["scrubber_degradation"]}
{"step": 25, "kind": "/eclss/events/recovery_applied", "command": {"kind": "set_fan_speed", "value": 0.95}, "message": "fan_speed set to 0.95"}
```

### design_state.jsonl

```json
{"step": 30, "topology": {"nodes": [...], "edges": [...]}, "parameters": {"scrubber_base_efficiency": 0.95}}
```

### summary.json

Run-level KPIs written once at end.

```json
{
  "simulator": "mock_eclss",
  "steps": 50,
  "peak_co2_ppm": 1850.0,
  "final_co2_ppm": 920.0,
  "final_health": {"co2_status": "safe", "power_status": "warning", "overall": "warning"}
}
```

## Day 2 demo

```bash
python src/scripts/run_mock_eclss.py --steps 50
# → src/experiments/results/mock_eclss_demo/telemetry.jsonl
```

Recovery smoke test:

```python
from environment.protocol import CommandKind, RecoveryCommand
from environment.ssos.mock_eclss import MockEclssSimulator

sim = MockEclssSimulator()
sim.apply_command(RecoveryCommand(kind=CommandKind.SET_FAN_SPEED, value=1.0))
```
