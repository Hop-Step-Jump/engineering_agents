# ECLSS known bugs inventory (units, dynamics, closed loop)

**Status**: Investigation complete; fixes require per-item approval  
**Date**: 2026-07-12  
**Scope**: Primarily `ssos_eclss_loop`, partly `scrubber_degradation`  
**Policy**: Implement fixes **only after explicit OK per bug ID**. This memo tracks sharing and progress.

Related: [backlog.md](../backlog.md) BL-008, [physical phenomena overview](ssos_eclss_physical_phenomena_overview.md), [E2E records](e2e_records/README.md)

Japanese: [known_bugs_inventory.md](../../../ja/memo/ssos_eclss_loop/known_bugs_inventory.md)

---

## Progress summary

**Landed (fixed)**: 9 · **Not yet landed (open)**: 8 · Total A–Q.

### Landed (fixed)

| ID | Kind | Summary | Severity |
| --- | --- | --- | --- |
| A | Units | Plant **g** vs EA mislabel **kg** (values already gram-scale) | Critical |
| D | Docs | Product water mislabeled as mass unit (should be L) | Low |
| E | Dynamics | `request_co2` **increases** storage (should withdraw) | Critical |
| I | Agents | Failures still recorded as `operational_applied` | Medium |
| K | Loop | Scrubber design proposals not re-injected (known) | High |
| N | Docs | OGS `sabatier_temp` mislabeled (K); `electrolysis_temp` unit missing | Low |
| O | Docs | E2E README `total_o2_generated: ~8.9 kg` (should be **g**) | Low |
| P | Docs | Stale source paths in `ssos/api-reference.md` | Low |
| Q | Docs | Phenomena overview §10 still says WRS/OGS “not connected / `SsosAdapter`” | Low |

### Not yet landed (open)

| ID | Kind | Summary | Severity |
| --- | --- | --- | --- |
| B | Units | `input_water_mass` subtracted from L tank without conversion | High |
| C | Units | Goal/Service argument units undefined / doc conflict | High |
| F | Dynamics | OGS water use not reflected in loop `_water` | High |
| G | Dynamics | ARS/OGS ignore goals; fixed offsets only | High |
| H | Config | Mock initial CO₂/O₂ disagree across three sources | Low |
| J | Agents | `co2_critical` in health only; unused by labeled | Medium |
| L | Scrubber | Power `*_w` names vs ad-hoc 0.01/0.05 scale | Medium |
| M | Scrubber | Dashboard 1000 ppm line ≠ health 800/1200 | Low |

Suggested order for remaining opens: **F → B → G → C → J → H → L → M**

---

## A — Plant grams vs EA kilograms

**Status**: **fixed** (2026-07-13)  
**Resolution**: Canonical unit is **grams** (matches SSOS plant caps). Renamed mislabeled `*_kg` storage fields/keys/docs to `*_g`. No numeric rescale.

Remaining: Goal field unit annotations → **C**.

---

## B — mass ↔ L without conversion

**Status**: open  
**Files**: `environment/ssos/eclss/mock/backend.py`, `agents.yaml`  
`product_water_reserve_l -= input_water_mass`.

---

## C — Unannotated Goal/Service units

**Status**: open  
**Files**: `types.py`, LLM prompt text in `ssos_eclss_loop_team.py` asserting “kg”.  
Plant docs: masses in **g**, iodine **2 mg/L**.

---

## D — Overview product-water unit typo

**Status**: **fixed** (2026-07-13)  
**Resolution**: Product water is **L** (`product_water_reserve_l`). Separated from CO₂/O₂ (**g**) in overview / scenario / architecture wording.

---

## E — `request_co2` sign inverted

**Status**: **fixed** (2026-07-13)  
**File**: `loop_mock_backend.py` — withdraw CO₂ on success (same pattern as `request_o2`).

---

## F — OGS water not applied to `_water`

**Status**: open  
**File**: `loop_mock_backend.py` — poll returns `_water`; parent OGS mutates only `_telemetry.product_water_reserve_l`.

---

## G — ARS/OGS ignore goals

**Status**: open  
**Files**: `loop_mock_backend.py`, `mock/backend.py`  
Fixed −350 / +100 / −30; parent `total_o2_generated: 120` unrelated to water. Mock cannot verify `--apply-proposals` parameter changes.

---

## H — Three-way mock initial mismatch

**Status**: open  

| Source | CO₂ | O₂ |
| --- | --- | --- |
| `scenario.yaml` | 1500 | 480 |
| `LoopMock` default | 1650 | 480 |
| `MockEclssBackend` | 1800 | 500 |

---

## I — Command failures treated as applied

**Status**: **fixed** (2026-07-13)  
**Files**: `ssos_eclss_loop_team.py`, `scenario_run.py`  
Emit `operational_rejected` when `result.success` is false; clear one-shot flags for retry; count summary invoke steps only for applied events.

---

## J — `co2_critical` unused by labeled

**Status**: open (BL-004)  
Health evaluates critical; labeled uses `co2_storage_high_g` only.

---

## K — Scrubber proposals not re-injected

**Status**: **fixed** (2026-07-13)  
`--apply-proposals` merges scrubber `add_edge` / `add_node` / `set_parameter` into config before the next run. Dashboard Before/After remains preview-only.

---

## L — Scrubber power scale

**Status**: open  
**File**: `mock_eclss.py` — `*_w * 0.01` / `* 0.05` vs EPS boost in raw W.

---

## M — Dashboard CO₂ reference line

**Status**: open  
Health 800/1200; plot `axhline(1000)` (policy recovery only).

---

## N — OGS temperature unit mislabel / missing unit

**Status**: **fixed** (2026-07-13)  
**Files**: `docs/*/memo/ssos_eclss_loop/ssos_eclss_physical_phenomena_overview.md`

- `sabatier_temp` was labeled **(K)** with default **300.0** (≈27°C if Kelvin — unrealistic for Sabatier). ARS/WRS limits in the same memo use °C. Corrected label to **°C** (value unchanged).
- `electrolysis_temp` (100.0) had no unit → annotated **°C**.

---

## O — E2E README O₂ generation unit typo

**Status**: **fixed** (2026-07-13)  
**Files**: `docs/*/memo/ssos_eclss_loop/e2e_records/README.md`

ros2 E2E note said `total_o2_generated: ~8.9 **kg**`, but the same record uses **g** for CO₂/O₂ storage, the events value is ≈8.9, and stoichiometry from `input_water_mass: 10` matches **g**. Corrected to **g** (same mislabel family as A).

---

## P — Stale api-reference source paths

**Status**: **fixed** (2026-07-13)  
**Files**: `docs/*/ssos/api-reference.md`

Paths from the flat `environment/ssos/` layout (`eclss_backend.py`, `eclss_types.py`, `mock_eclss_backend` imports, etc.) remained. Updated to current `ssos/eclss/`, `scrubber/eps/`, and `scenario/ssos_eclss_loop/` layout plus matching import examples.

---

## Q — Phenomena overview §10 WRS/OGS “not connected” typo

**Status**: **fixed** (2026-07-13)  
**Files**: `docs/*/memo/ssos_eclss_loop/ssos_eclss_physical_phenomena_overview.md`

§10 mapping still said WRS/OGS were “not connected (future `SsosAdapter`…)”, but `ssos_eclss_loop` already connects them via `MockEclssBackend` / `Ros2EclssBridge`. Also clarified ARS row for scrubber vs loop roles.

---

## Fix workflow

1. Reviewer names **one ID** and says OK  
2. Implement only that ID + tests  
3. Mark status `fixed` in this memo  
4. Proceed to the next ID  

Do not land code fixes before per-ID approval.
