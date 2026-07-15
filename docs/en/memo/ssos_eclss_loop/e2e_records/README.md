
# ssos_eclss_loop — Container ros2 E2E Records

**Date**: 2026-06-14  
**Environment**: Docker `ssos`, SSOS headless running, `ea-loop` (after `d62ca77` sync)

## labeled_rule_base + ros2

Command:

```bash
ea-loop --agents-mode labeled_rule_base --output-dir /tmp/e2e_labeled_ros2
```

| Item | Result |
|------|------|
| `backend` | `ros2` |
| `operational_command_count` | **2** |
| `ogs_invoked_step` | 0 |
| `co2_requested_step` | 0 |
| telemetry topics | `/co2_storage`, `/o2_storage`, `/wrs/product_water_reserve` |

**events.jsonl (step 0)**:

- `request_co2` — applied (SSOS: `Insufficient CO₂ in storage` — live plant CO₂=0 g)
- `oxygen_generation` — **SUCCEEDED** (`total_o2_generated: ~8.9 g`)

**Note**: Live SSOS had CO₂ storage=0, O₂=26.7 g, so the **OGS path** fired. This was not the mock-expected CO₂≥1500 → ARS path.

Artifacts: `labeled_rule_base_ros2_summary.json`, `labeled_rule_base_ros2_events.jsonl`

## llm + ros2

Command:

```bash
ea-loop --agents-mode llm --output-dir /tmp/e2e_llm_ros2 --steps 3
```

| Item | Result |
|------|------|
| `backend` | `ros2` |
| Ollama | `host.docker.internal:11434` / `gemma4:e4b` — **connection OK** |
| `message_count` | 12 (deliberation ×3 + action skip ×3) |
| `operational_command_count` | 0 (LLM chose hold — situational judgment with CO₂=0) |
| `design_proposals` | `decision_source: llm`, valid JSON (`changes: []`) |

**Note**: Infrastructure E2E succeeded (ros2 telemetry + Ollama + deliberation + post-run design). Operational firing depends on plant state.

Artifacts: `llm_ros2_summary.json`, `llm_ros2_design_proposals.json`
