# AIタクシー日報 (Taxi OCR)

タクシー乗務員の日報入力を自動化する Streamlit アプリ。手書き日報とメーター明細書の写真 2 枚をアップロードすると、AI が画像を理解して業務ルールに沿った日報を自動生成する。

**🎯 課題**: 日報入力に毎日 10 分、年間 60 時間以上の単純作業
**💡 解決**: OCR ではなく AI が画像を「理解」して業務判断・自動計算

---

## 主な特徴

- **2 画像入力**: 手書き日報 + 営業明細書を写真でアップ → 完成日報を出力
- **Vision + Claude ハイブリッド OCR**: Google Vision API で生テキスト抽出 → Claude で構造化 JSON 化（精度と速度の両立）
- **業務ルール内蔵**: メーター超過、障害者割引（障割）、現収/未収判定を自動処理
- **3 段階の検証**:
  - 連番チェック（メーター明細書の欠番検出）
  - 乖離チェック（メーター件数 vs 日報件数）
  - 整合性チェック（メーター額 vs 出力合計）
- **モバイル対応**: iOS Safari でも安定動作（components.html を最小化、CSS のみのアニメーション）
- **JS 軽量**: 装飾アニメーションは CSS @keyframes のみ、業務ロジックは純 Python

---

## 技術スタック

| カテゴリ | 採用 |
|---|---|
| UI フレームワーク | Streamlit 1.50.0 |
| AI モデル | Anthropic Claude Opus 4.5 |
| OCR (補助) | Google Cloud Vision API (document_text_detection) |
| 画像処理 | Pillow + pillow-heif (HEIC 対応) |
| 並列処理 | concurrent.futures.ThreadPoolExecutor |
| 言語 | Python 3.10+ |

---

## アーキテクチャ

### パイプライン全体図

```
┌─────────────────────────────────────────────────────────────────┐
│                      run_pipeline()                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [画像 1, 画像 2]                                                │
│       │                                                          │
│       ├──▶ identify_image() × 2 並列  (Claude)                  │
│       │      → 'meter' / 'nippou' を判定                        │
│       │                                                          │
│       ├──▶ check_clarity()           (Claude)                   │
│       │      → 鮮明度チェック                                   │
│       │                                                          │
│       ├──▶ parse_meter()      ┐                                 │
│       │   (Stage 1)           │ ThreadPoolExecutor で           │
│       │                       │ 並列実行                        │
│       └──▶ classify_nippou()  ┘                                 │
│           (Stage 2)                                             │
│                ↓                                                 │
│           build_report()        (Stage 3, 純 Python)             │
│                ↓                                                 │
│           validate()                                             │
│                ↓                                                 │
│        最終日報テーブル                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Stage 1: メーター明細書 OCR (`parse_meter`)

Vision API → Claude のハイブリッド方式：
1. Google Vision API の `document_text_detection` で生テキストを抽出
2. 抽出テキストを Claude に渡して JSON 構造化（時刻と金額を抜き出す）
3. Vision API が失敗した場合は Claude 単独 (`_parse_meter_claude`) にフォールバック

**出力形式**:
```json
{
  "rows": [
    {"no": 1, "time": "10:32", "amount": 4100},
    {"no": 2, "time": "10:50", "amount": 1000}
  ],
  "total": 5100
}
```

### Stage 2: 日報分類 (`classify_nippou`)

手書き日報画像を Claude に直接渡し、各行を分類した JSON 配列を取得。

**出力形式**:
```json
{
  "rides": [
    {"meter_no": 1, "passengers": 2, "kind": "未収", "memo": "Visa", "case": "normal", "nippou_amount": 1500},
    {"meter_no": 2, "passengers": 1, "kind": "現収", "memo": "現金", "case": "normal", "nippou_amount": null},
    {"meter_no": 3, "passengers": null, "kind": "未収", "memo": "障割", "case": "discount", "nippou_amount": 70}
  ]
}
```

`case` の値:
- `"normal"`: 通常乗車
- `"overage"`: メーター超過（から回し）
- `"discount"`: 障害者割引

### Stage 3: 統合・検証 (`build_report`)

**重要な設計判断 (v1.1.0〜): Sequence ベースアライメント**

`classify_nippou` の `meter_no` は「日報の上から何番目」の連番にすぎず、メーター明細書の行番号と必ずしも一致しない（障割の空回しが行われていない場合に顕著にズレる）。

そのため `build_report` は：
- 通常乗車（normal / overage）を `meter_rows_list[real_idx]` と **順番（index）でマッピング**
- 障割（discount）は別系統で `nippou_amount` を真値として未収に計上
- 障割行は元の日報順の位置に `"6+"` 形式（前の行の番号 + `+`）で挿入

---

## 業務ルール

### 通常の乗車
- **現金**: 現収欄に金額記入、未収欄は空欄
- **カード・電子マネー等** (Visa / Suica / Uber / PayPay / 交通系 等): 未収欄に金額記入

### メーター超過（から回し）
客の支払いが終わった後にメーターが回ってしまった場合の自己負担分。
- 客分 (例: ¥1,600) は通常通り
- 超過分 (例: ¥100) を**現収で別行追加** (自己負担で会社納金)
- 出力では 2 行に分割（state='ok' + state='special'）
- 件数・人数カウントから超過分を除外（二重計上回避）

### 障害者割引（障割）
- **1 行目**: 割引後の乗客支払い額を現収または未収欄に記入
- **2 行目（別段）**: 割引額を未収欄に記入、摘要に「障割」と明記
- `kind` の入力に関わらず必ず未収扱い
- 日報の手書き割引額 (`nippou_amount`) を真値として採用
- 件数・人数カウントから除外（会計調整は乗客ではないため）

### 集計の方針 (`aggregate_totals`)
| state | 件数 (ken) | 人数 (nin) | 金額 |
|---|---|---|---|
| `ok` / `mismatch` / `edited` | ○ 含む | ○ 含む | ○ 含む |
| `special` (メーター超過) | × 除外 | × 除外 | ○ 含む |
| `discount` (障割) | × 除外 | × 除外 | ○ 含む |

消費税 = `round(総収 / 11, -1)` (10 円単位), 税抜運収 = 総収 - 消費税。

### 整合性チェック

**乖離チェック**: メーター件数 vs 日報件数の差が
- 2 件 → warning
- 3 件以上 OR 金額差 30 % 以上 → error + 再アップロード提案

**連番チェック** (`validate_meter_sequence`): メーター明細書の no が連番か検証（例: 1,2,4,5 で 3 が抜けると warning）

**整合性チェック**: 各 meter_no について「メーター額 = 出力テーブル (gen + mi)」の検証（障割は除外）

**最終整合性** (`validate`): 期待値 = `sum(aligned meter rows) + sum(discount nippou_amounts)`、`diff == 0` であることを確認

---

## セットアップ

### 必要なもの
- Python 3.10+
- Anthropic API キー（Claude Opus 4.5 アクセス可能）
- (任意) Google Cloud Vision API のサービスアカウント JSON

### インストール

```bash
git clone https://github.com/shuchan-daze/taxi-ocr.git
cd taxi-ocr
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### API キーの設定

**ローカル開発**: `.streamlit/secrets.toml`
```toml
ANTHROPIC_API_KEY = "sk-ant-..."

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
# 以下、サービスアカウント JSON の全フィールド
```

または `key.json`（Google Cloud Vision 用）をプロジェクトルートに置く + `ANTHROPIC_API_KEY` 環境変数を設定。

### ローカル起動
```bash
streamlit run app.py
```

### Streamlit Cloud デプロイ
1. GitHub リポジトリをプッシュ
2. Streamlit Cloud で `app.py` を指定してデプロイ
3. Settings → Secrets に上記の TOML をペースト

---

## プロジェクト構造

```
taxi-ocr/
├── app.py              # メインアプリ（全機能を 1 ファイルに集約）
├── requirements.txt    # Streamlit / Anthropic / google-cloud-vision / Pillow / pillow-heif
├── CHANGELOG.md        # バージョン履歴
├── README.md           # このファイル
├── .gitignore          # key.json / secrets.toml / venv 等を除外
├── convert_secrets.py  # ローカル開発補助
└── (gitignore 済み)
    ├── key.json            # Google Cloud サービスアカウント
    ├── secrets.toml        # API キー
    └── .streamlit/secrets.toml
```

---

## プライバシー

写真はアプリのサーバーに保存されません。AI 処理元（Anthropic / Google）に一時送信されますが、学習には使われず、30 日以内に自動削除されます。

---

## バージョン履歴

詳細は [CHANGELOG.md](./CHANGELOG.md) を参照。

| バージョン | リリース日 | 主な内容 |
|---|---|---|
| v1.1.3 | 2026-05-11 | README.md 整備（プロジェクト記録ドキュメント） |
| v1.1.2 | 2026-05-11 | 速度改善（to_b64 キャッシュ）、dead code 削除 |
| v1.1.1 | 2026-05-11 | UI 表示調整（バージョン番号拡大・余白削減・完成バー拡大） |
| v1.1.0 | 2026-05-11 | 障害者割引（障割）対応の本格実装、sequence ベースアライメント |
| v1.0.0 | 2026-05-10 | 初回リリース |

### バージョニング規約 (SemVer 2.0)
- **MAJOR** (X._._): 大きな変更・仕様変更（後方互換なし）
- **MINOR** (_.X._): 部分的な機能追加・改善（後方互換あり）
- **PATCH** (_._.X): バグ修正・小さな調整

---

## 開発で重視した点

1. **業務ドメインへの忠実性**: タクシー乗務員の実際の記入習慣・運用に合わせる（運転手が空回しを忘れた場合への耐性、障割の独立行扱い等）
2. **モバイル安定性**: iOS Safari で白画面にならないこと（components.html を最小化、CSS animation 主体）
3. **検証の多段化**: 各 Stage で誤読を捕捉できるよう品質・連番・乖離・整合性の 4 段階チェック
4. **保守性**: 1 ファイル構成だが SemVer + CHANGELOG で履歴を明確化、関数単位の単一責任

---

## 作者

**怒りの山本** ([@shuchan-daze](https://github.com/shuchan-daze))
