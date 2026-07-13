# ECLSS 既知バグ一覧（単位・力学・閉ループ）

**ステータス**: 調査完了・修正は個別承認制  
**日付**: 2026-07-12  
**対象**: 主に `ssos_eclss_loop`、一部 `scrubber_degradation`  
**方針**: 修正は **1 件ずつ確認 OK 後に実装**する。本メモは共有・進捗トラック用。

関連: [backlog.md](../backlog.md) BL-008、[現象 overview](ssos_eclss_physical_phenomena_overview.md)、[E2E 記録](e2e_records/README.md)

---

## 進捗サマリ

| ID | 種別 | 概要 | 深刻度 | 状態 |
| --- | --- | --- | --- | --- |
| A | 単位 | プラント **g** vs EA 誤ラベル **kg**（数値は g スケール） | Critical | **fixed** |
| B | 単位 | `input_water_mass` を L タンクから無変換減算 | High | open |
| C | 単位 | Goal/Service 引数の単位未定義・文書矛盾 | High | open |
| D | 文書 | 製品水を質量単位と誤記（正は L） | Low | **fixed** |
| E | 力学 | `request_co2` が貯蔵を増やす（取り出しと逆） | Critical | **fixed** |
| F | 力学 | OGS 水消費がループ用 `_water` に未反映 | High | open |
| G | 力学 | ARS/OGS が goal を無視し固定オフセット | High | open |
| H | 設定 | mock 初期値（CO₂/O₂）の三者不一致 | Low | open |
| I | エージェント | 失敗でも `operational_applied` → 再試行なし | Medium | **fixed** |
| J | エージェント | `co2_critical` は health のみ、labeled 未使用 | Medium | open |
| K | 閉ループ | scrubber 設計提案の次ラン再注入なし（既知） | High | **fixed** |
| L | scrubber | 電力 `*_w` 名と実効スケール（×0.01/0.05）不一致 | Medium | open |
| M | scrubber | ダッシュボード基準線 1000 ≠ ヘルス 800/1200 | Low | open |
| N | 文書 | OGS `sabatier_temp` を (K) と誤記（値 300 は °C 相当）；`electrolysis_temp` 単位欠落 | Low | **fixed** |

推奨着手順（案）: **A → E → F → B → G → C → I → J → H → L → M → D → K → N**

---

## A — SSOS プラント g vs EA kg

**状態**: **fixed**（2026-07-13）  
**方針**: 数値はもともとプラント容量（g）と整合していたため、**正単位を g と確定**し、字段・閾値キー・文書の誤ラベル `*_kg` を `*_g` に改名。値の 1/1000 スケール変換は行わない。

**主な変更**:

- `EclssTelemetrySnapshot.co2_storage_g` / `o2_storage_g`
- `scenario.yaml` の `initial_*_storage_g`、`thresholds.*_g`、`mock_dynamics.*_g*`
- health / policy / summary / dashboard / docs（api-reference 単位列を g）

**残件（別 ID）**: Goal フィールド（`initial_co2_mass` 等）の単位注釈は **C**。

---

## B — mass ↔ L 無変換減算

**状態**: open  
**主なファイル**: `src/environment/ssos/eclss/mock/backend.py`、`src/scenario/ssos_eclss_loop/agents.yaml`

OGS で `product_water_reserve_l -= input_water_mass`。フィールド名は質量、タンクは L。プラントが g なら 1000 倍ズレ。

---

## C — Goal / Service 単位の未注釈

**状態**: open  
**主なファイル**: `src/environment/ssos/eclss/types.py`、`src/scenario/agents/ssos_eclss_loop_team.py`（LLM 向け「kg」断定）

`initial_co2_mass` / `input_water_mass` / `iodine_concentration` / `request_co2(amount)` に単位サフィックスまたは明示契約がない。現象 overview はヨウ素 **2 mg/L**、質量は **g**。

---

## D — overview の製品水単位誤記

**状態**: **fixed**（2026-07-13）  
**方針**: 製品水は `product_water_reserve_l`（**L**）。CO₂/O₂（g）と一括して質量単位で書かない。overview / scenario / architecture 等の表記を **g / L** に分離。

---

## E — `request_co2` 符号逆

**状態**: **fixed**（2026-07-13）  
**主なファイル**: `src/scenario/ssos_eclss_loop/loop_mock_backend.py`

`request_co2` を `request_o2` と同様、成功時に貯蔵から減算するよう修正（Sabatier 用の ARS からの取り出し）。

---

## F — OGS 水消費が `_water` に未反映

**状態**: open  
**主なファイル**: `src/scenario/ssos_eclss_loop/loop_mock_backend.py`

`poll_telemetry` は `self._water` を返す。親 mock の OGS は `_telemetry.product_water_reserve_l` のみ更新。`product_water_low_l` 診断が実質無効。

---

## G — ARS/OGS が goal を無視

**状態**: open  
**主なファイル**: `loop_mock_backend.py`、`environment/ssos/eclss/mock/backend.py`

ARS 常時 −350 kg、OGS 常時 +100 O₂ / CO₂ −30。親の `total_o2_generated: 120` は水量・gain と不一致。`--apply-proposals` のパラメータ変更を mock で検証できない。

---

## H — mock 初期値の三者不一致

**状態**: open  

| ソース | CO₂ | O₂ |
| --- | --- | --- |
| `scenario.yaml` | 1500 | 480 |
| `LoopMock` デフォルト | 1650 | 480 |
| `MockEclssBackend` | 1800 | 500 |

---

## I — コマンド失敗を成功扱い

**状態**: **fixed**（2026-07-13）  
**主なファイル**: `src/scenario/agents/ssos_eclss_loop_team.py`、`scenario_run.py`

- `result.success` が False のとき `/eclss/events/operational_rejected` を記録
- 失敗時に labeled ワンショットフラグをクリアして再試行可能に
- summary の `*_invoked_step` は applied のみをカウント

---

## J — `co2_critical` が labeled 未使用

**状態**: open（BL-004）  
**主なファイル**: `health.py`、`ssos_eclss_loop_team.py`

health は critical を評価、labeled は `co2_storage_high_g` のみ。

---

## K — scrubber 設計提案の再注入なし

**状態**: **fixed**（2026-07-13）  
**主なファイル**: `scenario/scrubber_degradation/design_proposals.py`、`scenario_run.py`、`jobs/executor.py`、`runner.build_eclss`

`--apply-proposals` で次ラン開始前に `add_edge` / `add_node` / `set_parameter` を config（`design_topology` / `design_parameters`）へマージ。ダッシュボード Before/After は引き続き preview。

---

## L — scrubber 電力スケール

**状態**: open  
**主なファイル**: `src/environment/scrubber/mock_eclss.py`

`base_power_draw_w * 0.01`、`fan_power_w * 0.05`。EPS boost は W をそのまま加算。名前と実効が不一致。

---

## M — ダッシュボード CO₂ 基準線

**状態**: open  
**主なファイル**: `src/tools/dashboard/app.py`、`eclss_ops/telemetry.py`

ヘルス: safe &lt; 800 / critical ≥ 1200。プロット: `axhline(1000)`（policy recovery のみ）。

---

## N — OGS 温度単位の誤記 / 欠落

**状態**: **fixed**（2026-07-13）  
**主なファイル**: `docs/*/memo/ssos_eclss_loop/ssos_eclss_physical_phenomena_overview.md`

- `sabatier_temp` を **(K)** と記載していたが、デフォルト **300.0** は 300 K（≈27°C）では触媒温度として非現実。同文書の ARS/WRS 限界は °C。**°C** に訂正（値は変更なし）。
- `electrolysis_temp`（100.0）は単位なし → **°C** を明記。

---

## 修正ワークフロー

1. レビュアが上表から **1 ID** を指定して OK
2. 当該 ID のみ実装 + テスト
3. 本メモの「状態」を `fixed` に更新
4. 次の ID へ

コード修正はこのメモの承認前には入れない。
