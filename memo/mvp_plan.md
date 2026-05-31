# ECLSS Resilience Loop — ディレクトリ構成 & 1週間 MVP 計画

> 設計プロセス記録。Cursor プラン `ECLSS Agent Directory MVP` から export（2026-05-30）。  
> **2026-05-30 更新**: Day 1–2 完了後の振り返りに基づきロードマップを修正。

## ゴール

**本質**: 精緻な物理モデルより「構造化されたエージェント関係」と「シミュレーターとの確実な API 契約」。

**現在のフェーズ（Phase 1）**: ECLSS 向け `src/` レイヤー上で、**scrubber_degradation ベースラインシナリオ**を常に実行可能な状態で維持しながら、エージェント・UI・設計変更トラックを足していく。

### 前提（ユーザー確認済み）

- **リポジトリ方針**: 既存 bar sim は `src/materials/` に退避。`src/` 配下に `core`, `environment`, `experiments`, `scenario`, `scripts`, `tools`。`src` と同レベルに `docs`, `memo`, `tests`。
- **SSOS 連携**: Mock アダプタ先行（ROS2 topic / command API 互換）。後から real SSOS に差し替え。
- **開発ブランチ**: `feature/eclss-mvp`

---

## Day 1–2 振り返り（完了）

| 項目 | 状態 | メモ |
| --- | --- | --- |
| `src/` レイヤー分離 + materials 退避 | ✅ | Day 1 |
| `core/`（sim loop, LLM, event_log） | ✅ | Day 1 で前倒し完了（旧 Day 3 項目） |
| `SimulatorProtocol` + Mock ECLSS | ✅ | Day 2 |
| `telemetry.jsonl` / `health_metrics.jsonl` | ✅ | Day 2 |
| `docs/api-contracts.md` | ✅ | Day 2 |
| pytest 8件 | ✅ | |

### Day 2 で判明したギャップ（Day 3 で解消）

1. **scrubber_degradation がシナリオとして未整備** — ロジックが `scripts/run_mock_eclss.py` にハードコードされていた。
2. **デモ物語が未成立** — 異常前から scrub が production を上回り CO2 が単調減少。危険域（>1000 ppm）に到達しない。
3. **ベースライン回帰テスト不足** — シナリオ名付きガードテストがなかった。

**方針**: アーキテクチャは維持。Day 3 以降の優先順位のみ修正（全面プラン見直しは不要）。

---

## 修正版 1週間 MVP ロードマップ

| Day | 旧プラン | **修正後（採用）** | 状態 |
| --- | --- | --- | --- |
| **1** | ディレクトリ移行 + pyproject | 同左 | ✅ 完了 |
| **2** | Mock ECLSS + Protocol + telemetry | 同左 | ✅ 完了 |
| **3** | core 抽出 + runner 骨格 | **scrubber_degradation 正式化 + runner + 物理調整 + baseline 回帰テスト** | ✅ 完了 |
| **4** | 4 ロール LLM エージェント | **ルールベース 4 ロール**（LLM optional）+ 回復コマンド自動発火 | 未着手 |
| **5** | One Piece JSON provenance | 設計変更 provenance（`integrations/one_piece/`） | 未着手 |
| **6** | Streamlit ダッシュボード | 左チャット + 右 CO2 グラフ（JSONL tail） | 未着手 |
| **7** | E2E + CLI | `tools.cli run --scenario scrubber_degradation` 完走 | 未着手 |

**Week-1 でやらないこと**（据え置き）:

- Real SSOS / ROS2 ランタイム接続
- One Piece Web UI 統合
- LLM 必須化（deterministic baseline を主軸）
- batch sweep / 動画生成

---

## デモシナリオ: `scrubber_degradation`（ベースライン）

**最重要**: Week-1 を通じて **常に LLM なしで完走**できるベースライン。改変後は `pytest tests/scenario/test_scrubber_baseline.py` で確認。

- **初期状態**: CO2 ≈ 800 ppm、scrubber efficiency 0.95
- **Step 20**: 複合アノマリー — 効率低下 + 電力圧迫 + CO2 产生増
- **物語**: Step 1–19 均衡付近 → Step 20 以降 CO2 **>1000 ppm** → Day 4 以降回復・設計変更で安全域へ
- **ベースライン成功条件**: 50 step 完走、step 20 anomaly、peak CO2 > 1000、ログ出力

### エージェントロール（Day 4）

Monitor / Diagnostician / Operator / DesignEngineer — **ルールベース先行**、LLM は optional。

---

## テスト方針

| テスト | 目的 |
| --- | --- |
| `tests/environment/test_mock_eclss.py` | Mock 単体 |
| **`tests/scenario/test_scrubber_baseline.py`** | **ベースライン完走 + 物語 assert（毎コミット必須）** |

### ベースライン assert（Day 3）

1. `run_scenario("scrubber_degradation")` 完走
2. `telemetry.jsonl` N 行 + `health_metrics.jsonl` / `events.jsonl` / `summary.json` 存在
3. step 20 以降 `anomaly_flags` に `scrubber_degradation`
4. `peak_co2_ppm > 1000`

---

## 成功判定（MVP Done）

1. `python -m tools.cli run --scenario scrubber_degradation` 完走
2. 6 種ログ + `summary.json` 出力
3. Streamlit step 同期 UI
4. 設計変更が `design_state.jsonl` + One Piece provenance に記録
5. **`pytest tests/scenario/test_scrubber_baseline.py` が常に green**

---

## 実装タスク一覧

- [x] src/ 骨格作成
- [x] 既存 bar sim を materials へ移行
- [x] SimulatorProtocol + JSONL スキーマ
- [x] mock_eclss.py + ROS2-like topics
- [x] core 一般化移植
- [x] scrubber_degradation scenario.yaml + runner + baseline 回帰テスト
- [x] Mock 物理パラメータ調整（CO2 危険域到達）
- [ ] ルールベース 4 ロールエージェント（agents.yaml）
- [ ] integrations/one_piece/ provenance
- [ ] tools/dashboard/app.py
- [ ] tools/cli + scrubber_demo.yaml E2E

---

## 参考

- API 契約: [docs/api-contracts.md](../docs/api-contracts.md)
- アーキテクチャ: [docs/architecture.md](../docs/architecture.md)
