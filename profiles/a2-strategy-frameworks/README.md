# a2-strategy-frameworks — 用途 Profile 集（a2-mind / a2-plan 共有）

> **拘束元**: `a2-mind-instruction-v1.1.md` §2（C6 Profile 駆動）・`a2-mind-api-mcp-spec.md` §2.3。
> **設計思想（拘束）**: コア機能は増やさず **Profile（型付きノード）で用途を増やす**。
> a2-mind / a2-plan は本セットを**読むだけ**。**Profile の追加＝コア変更ゼロ**が適合条件
> （新 Profile 投入時にコア diff 無しで動くことを構造テストで検証する）。

## 形式（1 Profile = 1 ファイル）

各 Profile は `v<ver>/profile.schema.json`（メタスキーマ・draft 2020-12）に適合する:

| キー | 意味 |
|---|---|
| `profile` | `<name>@<major>`（例 `swot@1`）。破壊的変更のみ major を上げる。追加変更は同 major。 |
| `nodeTypes` | 型名（`Node.type` の値）→ `{title, description, fields, x-a2-complete-when}`。`fields` は当該型の `Node.fields` を検証する JSON Schema。 |
| `template` | Profile 適用時に map root 直下へ生成するノード雛形ツリー（`{text, type?, children?}`）。 |
| `genTargets` | a2-gen で生成できる成果物 id（入力 = Profile＋ノード群 Envelope）。 |

**完全性の規約**: `fields` の全プロパティは**必ず optional**（hard required にすると
テンプレ雛形の生成が弾かれる）。「必須項目」は `x-a2-complete-when`（フィールド名の列挙）で宣言し、
**UI が未記入を明示**する（=フォーマットの抜け漏れ検出）。バリデーション失敗にはしない。
サーバは PATCH された `fields` を型スキーマで検証する（型違反は 422）。

## 版管理

- ディレクトリ = セット版（`v0.1.0/` … + `latest/` コピー。隣接 profiles/ と同じ規約）。
- Profile 単位の版は `profile` の `@<major>`。同 major 内は追加のみ（platform-api-mcp §3 と同一原則）。
- 消費者（a2-mind `GET /profiles`）は `index.json` を読み、各ファイルをメタスキーマ検証してロード。

## 初期セット（v0.1.0・instruction v1.1 §2 の順）

| Profile | 内容 | genTargets |
|---|---|---|
| `swot@1` | SWOT 4象限（evidence/impact 付き） | summary.html, biz-plan.docx |
| `3c@1` | 3C（Customer/Competitor/Company） | summary.html, biz-plan.docx |
| `biz-plan@1` | 事業企画書 10 セクション | biz-plan.docx, summary.html |
| `todo@1` | タスク（期限/担当/進捗%・コアの別ビューで リスト/カンバン/ガント） | todo-list.csv, summary.html |
| `product-spec@1` | 商品開発仕様（ニーズ→MoSCoW 要求→計測可能仕様） | product-spec.docx, summary.html |
| `eval-criteria@1` | 意思決定マトリクス（重み付き基準・votes 採点・a2.decided 連動） | decision-matrix.csv, summary.html |

**追加予定（Profile 追加のみで対応・コア変更ゼロが適合条件）**: PEST / 5Forces / 契約書 / 定款。

## 名前空間の注記

`$id` は本リポジトリの既存規約（`https://a2-schema.org/...`）に合わせている。
dx-platform 側 IXF は `a2-schema.ichiri.biz`（owner ruling 2026-07-23）— リポジトリ跨ぎの
ホスト統一は owner 判断待ち（どちらに寄せる場合も参照実体は本リポジトリのまま）。
