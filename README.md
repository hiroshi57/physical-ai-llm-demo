# physical-ai-llm-demo

LLM を "頭脳" として、**シミュレーション環境内の移動ロボットを自然言語指示で動かす**最小デモ。
実機不要。LLM が行動計画（プラン）を生成し、シミュレータ API を呼び出して実行する。

## 差別化ポイント

**プラン安全性検証レイヤ** — LLM が生成したプランを、実行の前に**独立した検証レイヤ**が
シミュレータのコピー上でドライ実行し、以下を検出して**危険なプランの実行を阻止**する:

- 範囲外への移動 / 障害物との衝突
- 危険セル（hazard）への進入
- 不正な pick/place（保持状態の矛盾）
- プラン長の上限超過

LLM の出力をそのまま実行せず「計画 → **検証** → 実行」の 3 層に分けることで、
フィジカル AI で致命的な誤動作を防ぐ。すべて **API キー不要**で動作する。

## パイプライン

```
自然言語指示 ──planner──▶ 行動プラン ──safety verifier──▶ (SAFE のみ) ──executor──▶ シミュレータ
                (BFS/LLM)                 ★実行前ゲート                        (ログ記録)
```

## 全機能(差別化＋拡張)

- プラン安全性検証レイヤ（差別化コア）
- **クローズドループ自動リプランニング**（`safe_planner.py`）: 計画→検証→(危険なら)回避して再計画
- **複数物体の連続搬送**（`plan_deliver_all`）
- **グリッド可視化モジュール**（`simulator/render.py`）

## 本番構成（SQLite + HTMLレポート + Vite 2画面）

- **DB**: `service/db.py`（SQLite）。実行履歴(プラン/安全性/納品)をテナント別に永続化＝**テナント分離**
- **API**: `service/api.py`（FastAPI）。run(計画+安全検証+実行) / history / report(HTML)
- **HTMLレポート**: `service/report_html.py`（初期グリッド＋生成プラン＋安全性バッジ、XSSエスケープ）
- **フロント**: `frontend/`（React+Vite）。**プラン可視化**＋**実行履歴**の2画面。ビルド不要は `frontend/standalone.html`
- **CI**: `.github/workflows/ci.yml`

```bash
uvicorn service.api:app --reload
cd frontend && npm install && npm run dev     # or: open frontend/standalone.html
python -m pytest -q                            # テスト26件(DB/テナント分離/HTMLレポート/API E2E含む)
```

## クイックスタート

```bash
python demo.py          # 世界表示→計画→検証→実行→危険拒否→自動リプラン→複数搬送
python -m pytest -q     # テスト21件(外部依存なし)
```

デモ出力（抜粋）: ロボット R が障害物 `#` と危険セル `!` を避けて箱 `o` を把持し、
ゴール `G` へ納品する。危険セルを横切るプランは実行前に `hazard` 違反で拒否される。

## 構成

```
simulator/env.py            # 2Dグリッド世界 + move/pick/place(障害物・危険セル)
planner/
  llm_planner.py            # 自然言語 -> 行動プラン(BFS経路計画, LLMフォールバック)
  safety.py                 # ★プラン安全性検証レイヤ(差別化)
  prompts/planner_prompt.md # LLM用プロンプト(JSON行動列)
executor/action_executor.py # 検証通過プランのみ実行 + ログ
logs/                       # 実行ログ出力先
tests/                      # 衝突/範囲外/危険/不正pick検出・実行拒否を検証
```

## 実 LLM 接続

`planner/prompts/planner_prompt.md` を Claude に与えて行動列(JSON)を得て `Action` に変換すれば、
`llm_planner` の BFS を置換できる。安全性検証・実行・ログの仕組みはそのまま利用可能。
```
