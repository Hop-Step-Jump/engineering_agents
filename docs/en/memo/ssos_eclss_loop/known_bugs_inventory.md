# ECLSS known bugs inventory (units, dynamics, closed loop)

**Status**: Investigation complete; fixes require per-item approval  
**Date**: 2026-07-12  
**Scope**: Primarily `ssos_eclss_loop`, partly `scrubber_degradation`  
**Policy**: Implement fixes **only after explicit OK per bug ID**. This memo tracks sharing and progress.

Related: [backlog.md](../backlog.md) BL-008, [physical phenomena overview](ssos_eclss_physical_phenomena_overview.md), [E2E records](e2e_records/README.md)

Japanese: [known_bugs_inventory.md](../../../ja/memo/ssos_eclss_loop/known_bugs_inventory.md)

---

## Progress summary

| ID | Kind | Summary | Severity | Status |
| --- | --- | --- | --- | --- |
| A | Units | Plant **g** vs EA **kg** (~1000×) | Critical | open |
| B | Units | `input_water_mass` subtracted from L tank without conversion | High | open |
| C | Units | Goal/Service argument units undefined / doc conflict | High | open |
| D | Docs | Product water mislabeled as kg (should be L) | Low | open |
| E | Dynamics | `request_co2` **increases** storage (should withdraw) | Critical | open |
| F | Dynamics | OGS water use not reflected in loop `_water` | High | open |
| G | Dynamics | ARS/OGS ignore goals; fixed offsets only | High | open |
| H | Config | Mock initial CO₂/O₂ disagree across three sources | Low | open |
| I | Agents | Failures still recorded as `operational_applied` | Medium | open |
| J | Agents | `co2_critical` in health only; unused by labeled | Medium | open |
| K | Loop | Scrubber design proposals not re-injected (known) | High | open (known) |
| L | Scrubber | Power `*_w` names vs ad-hoc 0.01/0.05 scale | Medium | open |
| M | Scrubber | Dashboard 1000 ppm line ≠ health 800/1200 | Low | open |

Suggested order: **A → E → F → B → G → C → I → J → H → L → M → D → K**

---

## A — Plant grams vs EA kilograms

**Status**: open  
**Key files**: physical phenomena overview (`(g)` caps), `scenario.yaml` / `health.py` (`*_kg`), `types.py` field names, api-reference (claims kg).

**Evidence (ros2 E2E)**: `input_water_mass: 10` → `total_o2_generated ≈ 8.9` (= 10×0.89, gram scale). `final_o2 ≈ 26.7` with `o2_status: critical` against 450 “kg” threshold.

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

## D — Overview product-water kg typo

**Status**: open  
**Files**: `docs/en/overview.md`, `docs/ja/overview.md`

---

## E — `request_co2` sign inverted

**Status**: open  
**File**: `loop_mock_backend.py` — `self._co2 += amount`  
Overview: OGS **fetches** CO₂ from ARS. `request_o2` correctly subtracts.

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

**Status**: open (also BL-004)  
**File**: `ssos_eclss_loop_team.py` — always `operational_applied`.

---

## J — `co2_critical` unused by labeled

**Status**: open (BL-004)  
Health evaluates critical; labeled uses `co2_storage_high_kg` only.

---

## K — Scrubber proposals not re-injected

**Status**: open (documented in `AGENTS.md`)  
Dashboard Before/After is preview only.

---

## L — Scrubber power scale

**Status**: open  
**File**: `mock_eclss.py` — `*_w * 0.01` / `* 0.05` vs EPS boost in raw W.

---

## M — Dashboard CO₂ reference line

**Status**: open  
Health 800/1200; plot `axhline(1000)` (policy recovery only).

---

## Fix workflow

1. Reviewer names **one ID** and says OK  
2. Implement only that ID + tests  
3. Mark status `fixed` in this memo  
4. Proceed to the next ID  

Do not land code fixes before per-ID approval.
