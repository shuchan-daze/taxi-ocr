"""nippou_core.py — 日報処理エンジンの中核 (独立モジュール).

設計の核 (Shuchan の哲学 2026-05-17、ChatGPT との議論で確定):

  Layer 1: 紙日報グリッド層
    - 日報の構造は OCR/AI に作らせない
    - Python 側で固定の 125 セル (25行 × 5列) を先に作る
    - OCR トークンを XY 座標で cell_id に配置
    - 読めないセルは空欄のまま、行は詰めない

  Layer 2: メーター明細層
    - 通常メーター営業の確認データとして使う
    - ただし紙日報の内訳を単純上書きしない (= メーター超過の二重計上を避ける)

  Layer 3: イレギュラー処理モジュール層
    - メーター超過、障害者割引、貸切などをルール式で処理
    - 将来追加できるプラグイン構造 (= adjustment_rules.append(NewRule()))
    - コア処理にベタ書きしない

重要な禁止事項:
  - OCR 結果から直接 paper_rows を作らない
  - OCR の戻り順は使わない
  - AI に論理セル判断をさせない
  - 空欄セルを削除しない
  - 行を詰めない
  - メーター明細金額で紙日報内訳を単純上書きしない
  - メーター超過分を二重加算しない
  - 貸切を meter_rows と照合しない
  - 紙日報にしかない売上を捨てない
  - イレギュラー処理をコア処理にベタ書きしない

既存アプリ (app.py 等) には一切触らない. このファイルは独立して動作確認できる.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# Section 1: データクラス
# ═══════════════════════════════════════════════════════════════════

@dataclass
class OCRToken:
    """OCR が返す 1 トークン + 物理座標 (ピクセル単位).

    find_cell_by_xy() で image_width / image_height で除算して相対化する.
    座標はピクセル、テンプレートは相対座標 (0.0〜1.0). 混ぜない.
    """
    text: str
    x: float       # 左上 x (px)
    y: float       # 左上 y (px)
    w: float       # 幅 (px)
    h: float       # 高さ (px)
    confidence: Optional[float] = None


@dataclass
class CellAddress:
    """セル住所 (= 論理座標). R{行}_{列} 形式."""
    cell_id: str
    row: int
    col: str


@dataclass
class Cell:
    """固定グリッドの 1 セル. OCR で読めても読めなくても必ず存在."""
    cell_id: str
    row: int
    col: str
    value: str = ""
    tokens: List[OCRToken] = field(default_factory=list)
    confidence: Optional[float] = None
    source: str = "blank"   # "blank" / "ocr"


@dataclass
class PaperRow:
    """紙日報の 1 行 (cell_map から組み立てた行データ).

    row_type は classify_rows_with_rules で後から設定する:
      - "meter_fare"                        通常メーター営業 (meter_rows と照合)
      - "meter_overrun_adjustment"          メーター超過分 (+100 メーター)
      - "disability_discount_adjustment"    障害者割引関連行
      - "charter_fare"                      貸切 (メーター外)
      - "review"                            分類不能、ユーザー確認
      - "blank"                             空行 (= 何も書かれてない)
    """
    paper_row: int          # 1〜25
    time: str = ""
    passengers: str = ""
    gen_raw: str = ""
    mi_raw: str = ""
    memo: str = ""
    row_type: str = "blank"


@dataclass
class MeterRow:
    """メーター明細の 1 件."""
    meter_no: int
    time: str
    amount: int


@dataclass
class AdjustmentResult:
    """イレギュラー処理ルールの共通結果型.

    重要フィールド:
      is_paper_only       — 紙日報にしか存在しない追加売上か (= 貸切)
      is_meter_breakdown  — メーター明細金額の内訳か (= メーター超過)
      reconciliation_mode — 整合確認のモード:
          "none"       照合に関与しない
          "strict"     単独でメーター明細と一致を要求 (= 通常営業行)
          "breakdown"  関連行と合算してメーター明細と一致 (= メーター超過)
          "review"     整合確認するが、ズレてもエラーにせず人間に報告
          "paper_only" メーター明細に対応しない独立売上 (= 貸切)
      status              "ok" / "review" / "error"
    """
    rule_name: str
    row_index: int
    related_row_index: Optional[int] = None
    amount: int = 0
    side: str = ""          # "gen" / "mi" / ""
    affects_cash_total: bool = False
    affects_mi_total: bool = False
    affects_meter_reconciliation: bool = False
    is_paper_only: bool = False
    is_meter_breakdown: bool = False
    status: str = "ok"
    reconciliation_mode: str = "none"
    note: str = ""


# ═══════════════════════════════════════════════════════════════════
# Section 2: テンプレート (= 紙日報の固定フォーマット)
# ═══════════════════════════════════════════════════════════════════
#
# 重要: 全て 0.0〜1.0 の相対座標で定義する.
# OCR トークンの物理座標 (px) は image_width/image_height で除算して
# 相対化し、ここと比較する. ピクセル座標は絶対に混ぜない.
# 罫線検出・台形補正は将来段階で実装、まずはこの固定テンプレートで動作させる.

PAPER_TEMPLATE = {
    "columns": {
        "time":       {"x1": 0.05, "x2": 0.16},
        "passengers": {"x1": 0.17, "x2": 0.23},
        "gen":        {"x1": 0.36, "x2": 0.48},
        "mi":         {"x1": 0.49, "x2": 0.61},
        "memo":       {"x1": 0.62, "x2": 0.92},
    },
    "rows": [
        {"row":  1, "y1": 0.180, "y2": 0.208},
        {"row":  2, "y1": 0.208, "y2": 0.236},
        {"row":  3, "y1": 0.236, "y2": 0.264},
        {"row":  4, "y1": 0.264, "y2": 0.292},
        {"row":  5, "y1": 0.292, "y2": 0.320},
        {"row":  6, "y1": 0.320, "y2": 0.348},
        {"row":  7, "y1": 0.348, "y2": 0.376},
        {"row":  8, "y1": 0.376, "y2": 0.404},
        {"row":  9, "y1": 0.404, "y2": 0.432},
        {"row": 10, "y1": 0.432, "y2": 0.460},
        {"row": 11, "y1": 0.460, "y2": 0.488},
        {"row": 12, "y1": 0.488, "y2": 0.516},
        {"row": 13, "y1": 0.516, "y2": 0.544},
        {"row": 14, "y1": 0.544, "y2": 0.572},
        {"row": 15, "y1": 0.572, "y2": 0.600},
        {"row": 16, "y1": 0.600, "y2": 0.628},
        {"row": 17, "y1": 0.628, "y2": 0.656},
        {"row": 18, "y1": 0.656, "y2": 0.684},
        {"row": 19, "y1": 0.684, "y2": 0.712},
        {"row": 20, "y1": 0.712, "y2": 0.740},
        {"row": 21, "y1": 0.740, "y2": 0.768},
        {"row": 22, "y1": 0.768, "y2": 0.796},
        {"row": 23, "y1": 0.796, "y2": 0.824},
        {"row": 24, "y1": 0.824, "y2": 0.852},
        {"row": 25, "y1": 0.852, "y2": 0.880},
    ],
}


# ═══════════════════════════════════════════════════════════════════
# Section 3: Layer 1 — 紙日報グリッド (= 固定セルを先に作る)
# ═══════════════════════════════════════════════════════════════════

def build_empty_cell_map(template: Optional[dict] = None) -> Dict[str, Cell]:
    """日報の固定フォーマットを「絶対の器」として先に作る.

    25 行 × 5 列 = 125 セルを必ず生成. OCR 結果に関係なく全セル存在.
    """
    if template is None:
        template = PAPER_TEMPLATE
    cell_map: Dict[str, Cell] = {}
    for row_band in template["rows"]:
        row_no = row_band["row"]
        for col_name in template["columns"].keys():
            cell_id = f"R{row_no:02d}_{col_name.upper()}"
            cell_map[cell_id] = Cell(
                cell_id=cell_id,
                row=row_no,
                col=col_name,
                value="",
                tokens=[],
                confidence=None,
                source="blank",
            )
    return cell_map


def find_cell_by_xy(
    token: OCRToken,
    template: dict,
    image_width: float,
    image_height: float,
) -> Optional[CellAddress]:
    """トークンの中心座標 → セル住所 (R{行}_{列}) を機械的に判定.

    AI の判断は介在しない. テンプレートの相対座標範囲と比較するだけ.
    """
    if image_width <= 0 or image_height <= 0:
        return None
    cx = token.x + token.w / 2.0
    cy = token.y + token.h / 2.0
    rx = cx / image_width
    ry = cy / image_height

    row_no: Optional[int] = None
    for row_band in template["rows"]:
        if row_band["y1"] <= ry < row_band["y2"]:
            row_no = row_band["row"]
            break
    if row_no is None:
        return None

    col_name: Optional[str] = None
    for name, col_band in template["columns"].items():
        if col_band["x1"] <= rx < col_band["x2"]:
            col_name = name
            break
    if col_name is None:
        return None

    return CellAddress(
        cell_id=f"R{row_no:02d}_{col_name.upper()}",
        row=row_no,
        col=col_name,
    )


def assign_ocr_tokens_to_cells(
    cell_map: Dict[str, Cell],
    ocr_tokens: List[OCRToken],
    template: dict,
    image_width: float,
    image_height: float,
) -> Dict[str, Cell]:
    """OCR トークンを XY 座標で cell_map に配置.

    OCR 戻り順は無視. 範囲外トークンは捨てる. 該当セルに OCR 結果が入ったら
    source='ocr' に変更. 各セル内のトークンは上→下、左→右にソートして
    value を組み立てる:
      - 数字系列 (gen / mi / passengers): 区切りなし連結 (例: '12'+'30'→'1230')
      - 文字系列 (time / memo): スペース区切り連結
    """
    for token in ocr_tokens:
        address = find_cell_by_xy(token, template, image_width, image_height)
        if address is None:
            continue
        if address.cell_id not in cell_map:
            continue
        cell = cell_map[address.cell_id]
        cell.tokens.append(token)
        cell.source = "ocr"

    for cell in cell_map.values():
        if not cell.tokens:
            continue
        cell.tokens.sort(key=lambda t: (t.y, t.x))
        if cell.col in ("gen", "mi", "passengers"):
            cell.value = "".join(t.text for t in cell.tokens)
        else:
            cell.value = " ".join(t.text for t in cell.tokens)
        confidences = [t.confidence for t in cell.tokens if t.confidence is not None]
        if confidences:
            cell.confidence = sum(confidences) / len(confidences)
    return cell_map


def _get_cell_value(cell_map: Dict[str, Cell], row_no: int, col: str) -> str:
    cell_id = f"R{row_no:02d}_{col.upper()}"
    cell = cell_map.get(cell_id)
    return cell.value if cell else ""


def build_paper_rows_from_cell_map(
    cell_map: Dict[str, Cell],
    total_rows: int = 25,
) -> List[PaperRow]:
    """cell_map → paper_rows. 全 25 行を必ず生成 (= 空行も詰めない)."""
    rows: List[PaperRow] = []
    for row_no in range(1, total_rows + 1):
        rows.append(
            PaperRow(
                paper_row=row_no,
                time=_get_cell_value(cell_map, row_no, "time"),
                passengers=_get_cell_value(cell_map, row_no, "passengers"),
                gen_raw=_get_cell_value(cell_map, row_no, "gen"),
                mi_raw=_get_cell_value(cell_map, row_no, "mi"),
                memo=_get_cell_value(cell_map, row_no, "memo"),
            )
        )
    return rows


# ═══════════════════════════════════════════════════════════════════
# Section 4: AdjustmentRule 基盤
# ═══════════════════════════════════════════════════════════════════

class AdjustmentRule:
    """イレギュラー処理ルールの基底クラス.

    サブクラスは:
      name      識別子
      priority  数値が小さい順に評価
      match(row, context) -> bool
      apply(row, context) -> AdjustmentResult
    を実装する.
    """
    name: str = ""
    priority: int = 100

    def match(self, row: PaperRow, context: dict) -> bool:
        raise NotImplementedError

    def apply(self, row: PaperRow, context: dict) -> AdjustmentResult:
        raise NotImplementedError


def classify_rows_with_rules(
    paper_rows: List[PaperRow],
    rules: List[AdjustmentRule],
) -> Tuple[List[PaperRow], List[AdjustmentResult]]:
    """各 paper_row に対して登録 rules を priority 順に試す.

    最初に match した rule の apply 結果を AdjustmentResult として収集.
    row.row_type を分類結果に応じて設定.
    どの rule にもマッチしない行:
      - 金額 (gen_raw or mi_raw) がある            → "meter_fare" (通常営業候補)
      - 金額なしで時刻 / 人数 / メモのいずれかあり → "review" (人間判断)
      - 完全に空                                    → "blank"

    重要: 金額のない不完全 OCR 行を meter_fare にしない.
    そうしないと meter_rows を 1 本余計に消費し、以降の照合がズレる事故が起きる.
    """
    sorted_rules = sorted(rules, key=lambda r: r.priority)
    adjustments: List[AdjustmentResult] = []
    context = {"all_rows": paper_rows}

    for idx, row in enumerate(paper_rows):
        context["row_index"] = idx
        matched = False
        for rule in sorted_rules:
            if rule.match(row, context):
                result = rule.apply(row, context)
                adjustments.append(result)
                # row_type を rule_name から推定
                row.row_type = _rule_name_to_row_type(rule.name)
                matched = True
                break
        if not matched:
            if _has_value(row.gen_raw) or _has_value(row.mi_raw):
                row.row_type = "meter_fare"
            elif row.time or row.passengers or row.memo:
                row.row_type = "review"
            else:
                row.row_type = "blank"
    return paper_rows, adjustments


def _rule_name_to_row_type(name: str) -> str:
    mapping = {
        "MeterOverrunRule": "meter_overrun_adjustment",
        "DisabilityDiscountRule": "disability_discount_adjustment",
        "CharterFareRule": "charter_fare",
    }
    return mapping.get(name, "review")


# ═══════════════════════════════════════════════════════════════════
# Section 5: 既知ルール 3 つ
# ═══════════════════════════════════════════════════════════════════

class MeterOverrunRule(AdjustmentRule):
    """メーター超過行の処理.

    判定:
      - memo に「メーター」を含む
      - AND gen_raw or mi_raw に「+」付き数字 (例: "+100"), または
        通常の数字 (例: "100") が小額で書かれてる
      (通常営業行と区別するキーは「memo にメーター」)

    処理:
      - amount = "+" を除いた数値
      - side = 紙の記入欄に従う (gen 欄 or mi 欄)
      - related_row_index = 直前の通常営業行候補 (paper_row - 1 から逆走)
      - is_meter_breakdown = True (= メーター明細金額の内訳)
      - reconciliation_mode = "breakdown" (関連行と合算してメーター明細と一致確認)
      - affects_cash_total = True if side=="gen"
      - affects_mi_total  = True if side=="mi"

    重要: メーター明細金額で通常営業行を上書きしない.
          通常営業行 + この超過分 = メーター明細 1 本、で照合する.
    """
    name = "MeterOverrunRule"
    priority = 10

    def match(self, row: PaperRow, context: dict) -> bool:
        memo = row.memo or ""
        if "メーター" not in memo:
            return False
        return _has_value(row.gen_raw) or _has_value(row.mi_raw)

    def apply(self, row: PaperRow, context: dict) -> AdjustmentResult:
        # gen 欄優先で金額を拾う ("+100" の "+" は除く)
        if _has_value(row.gen_raw):
            side = "gen"
            amount = _extract_amount(row.gen_raw)
        elif _has_value(row.mi_raw):
            side = "mi"
            amount = _extract_amount(row.mi_raw)
        else:
            side = ""
            amount = 0

        # 直前の通常営業行候補 (paper_row - 1 を起点に逆走)
        related = None
        all_rows: List[PaperRow] = context.get("all_rows", [])
        idx = context.get("row_index", row.paper_row - 1)
        for j in range(idx - 1, -1, -1):
            prev = all_rows[j]
            if _has_value(prev.gen_raw) or _has_value(prev.mi_raw):
                related = prev.paper_row
                break

        return AdjustmentResult(
            rule_name=self.name,
            row_index=row.paper_row,
            related_row_index=related,
            amount=amount,
            side=side,
            affects_cash_total=(side == "gen"),
            affects_mi_total=(side == "mi"),
            affects_meter_reconciliation=True,
            is_paper_only=False,
            is_meter_breakdown=True,
            status="ok",
            reconciliation_mode="breakdown",
            note=f"メーター超過: 関連行 {related} と合算してメーター明細と整合確認",
        )


class DisabilityDiscountRule(AdjustmentRule):
    """障害者割引関連行の処理.

    判定:
      - memo に「障害者割引」「障割」「小割」のいずれかを含む

    処理 (重要: 計算式は固定しない、紙の数字をそのまま拾う):
      - amount = 紙に書かれた数字 (mi_raw or gen_raw)
      - side = 紙の記入欄に従う:
          mi 欄に金額あり → "mi"
          gen 欄に金額あり → "gen"
          両方に金額あり  → status="review"
          どちらにも無い  → status="review"
        → mi 固定にはしない. 紙日報の記入位置を優先する.
      - reconciliation_mode = "review"
        (整合確認するが、ズレてもエラーにせず人間に報告)
      - status="review" デフォルト

    重要: 1/9 等の自動計算はしない. 丸めルールや会社処理が未確定なため.
          紙日報に書かれた数字を「ありのまま」拾う. 整合確認は reconcile 層
          が「客払い + 補填 = メーター明細」を「参考表示」として行う.
          将来仕様確定後に自動計算を追加できる.
    """
    name = "DisabilityDiscountRule"
    priority = 20

    def match(self, row: PaperRow, context: dict) -> bool:
        memo = row.memo or ""
        return any(kw in memo for kw in ["障害者割引", "障割", "小割"])

    def apply(self, row: PaperRow, context: dict) -> AdjustmentResult:
        gen_has = _has_value(row.gen_raw)
        mi_has = _has_value(row.mi_raw)

        if gen_has and mi_has:
            side = ""
            amount = 0
            status = "review"
            note = "障害者割引: 現収・未収両方に金額あり、人間判断が必要"
        elif mi_has:
            side = "mi"
            amount = _extract_amount(row.mi_raw)
            status = "review"
            note = "障害者割引: 紙の未収欄から拾った. 整合確認は reconcile 層で実施"
        elif gen_has:
            side = "gen"
            amount = _extract_amount(row.gen_raw)
            status = "review"
            note = "障害者割引: 紙の現収欄から拾った. 整合確認は reconcile 層で実施"
        else:
            side = ""
            amount = 0
            status = "review"
            note = "障害者割引: 金額が空欄、人間判断が必要"

        return AdjustmentResult(
            rule_name=self.name,
            row_index=row.paper_row,
            related_row_index=None,
            amount=amount,
            side=side,
            affects_cash_total=(side == "gen"),
            affects_mi_total=(side == "mi"),
            affects_meter_reconciliation=True,
            is_paper_only=False,
            is_meter_breakdown=False,
            status=status,
            reconciliation_mode="review",
            note=note,
        )


class CharterFareRule(AdjustmentRule):
    """貸切行の処理.

    判定:
      - memo に「貸切」を含む

    処理:
      - amount = 紙の数字 (gen_raw or mi_raw)
      - side = 紙の記入欄に従う (gen / mi / 不明なら review)
      - is_paper_only = True
      - reconciliation_mode = "paper_only" (メーター明細と照合しない)
      - 最終売上に独立加算する
    """
    name = "CharterFareRule"
    priority = 30

    def match(self, row: PaperRow, context: dict) -> bool:
        memo = row.memo or ""
        return "貸切" in memo

    def apply(self, row: PaperRow, context: dict) -> AdjustmentResult:
        gen_has = _has_value(row.gen_raw)
        mi_has = _has_value(row.mi_raw)

        if gen_has and not mi_has:
            side = "gen"
            amount = _extract_amount(row.gen_raw)
            status = "ok"
            note = "貸切: 紙の現収欄から拾った"
        elif mi_has and not gen_has:
            side = "mi"
            amount = _extract_amount(row.mi_raw)
            status = "ok"
            note = "貸切: 紙の未収欄から拾った"
        elif gen_has and mi_has:
            side = ""
            amount = 0
            status = "review"
            note = "貸切: 現収・未収両方に金額あり、人間判断が必要"
        else:
            side = ""
            amount = 0
            status = "review"
            note = "貸切: 金額が空欄、人間判断が必要"

        return AdjustmentResult(
            rule_name=self.name,
            row_index=row.paper_row,
            related_row_index=None,
            amount=amount,
            side=side,
            affects_cash_total=(side == "gen"),
            affects_mi_total=(side == "mi"),
            affects_meter_reconciliation=False,
            is_paper_only=True,
            is_meter_breakdown=False,
            status=status,
            reconciliation_mode="paper_only",
            note=note,
        )


# ═══════════════════════════════════════════════════════════════════
# Section 6: Layer 2 — メーター明細との照合
# ═══════════════════════════════════════════════════════════════════

def reconcile_meter_with_paper(
    paper_rows: List[PaperRow],
    meter_rows: List[MeterRow],
    adjustments: List[AdjustmentResult],
) -> List[dict]:
    """通常営業行 (row_type='meter_fare') を meter_rows と順序照合.

    breakdown 系の補正 (= メーター超過) は関連行に合算してメーター明細と整合.
    paper_only (= 貸切) は照合スキップ.
    review (= 障害者割引) は整合確認結果を note に残すが、エラーにしない.

    返値: 各 paper_row 1 つに対応する整合結果 (dict).
      {
        paper_row, time, passengers, gen_raw, mi_raw, memo,
        row_type, matched_meter_no, matched_meter_amount,
        breakdown_total, reconciliation_status, reconciliation_note
      }
    """
    # adjustments を row_index でインデックス化
    adj_by_row: Dict[int, AdjustmentResult] = {}
    for adj in adjustments:
        adj_by_row.setdefault(adj.row_index, adj)

    # 通常営業行のリスト (meter_fare のみ)
    meter_fare_rows = [r for r in paper_rows if r.row_type == "meter_fare"]
    meter_iter_idx = 0

    results: List[dict] = []
    for row in paper_rows:
        row_adj = adj_by_row.get(row.paper_row)
        entry = {
            "paper_row": row.paper_row,
            "time": row.time,
            "passengers": row.passengers,
            "gen_raw": row.gen_raw,
            "mi_raw": row.mi_raw,
            "memo": row.memo,
            "row_type": row.row_type,
            "matched_meter_no": None,
            "matched_meter_amount": None,
            "breakdown_total": None,
            "reconciliation_status": "n/a",
            "reconciliation_note": "",
        }

        if row.row_type == "meter_fare":
            # 通常営業 → 次の meter_rows と対応付け
            if meter_iter_idx < len(meter_rows):
                meter = meter_rows[meter_iter_idx]
                meter_iter_idx += 1
                entry["matched_meter_no"] = meter.meter_no
                entry["matched_meter_amount"] = meter.amount

                # この通常営業行に紐付く breakdown 補正があれば合算
                breakdown_sum = 0
                for adj in adjustments:
                    if (adj.related_row_index == row.paper_row
                            and adj.reconciliation_mode == "breakdown"):
                        breakdown_sum += adj.amount
                paper_amount = _extract_amount(row.gen_raw) or _extract_amount(row.mi_raw) or 0
                total_paper = paper_amount + breakdown_sum
                entry["breakdown_total"] = total_paper

                if total_paper == meter.amount:
                    entry["reconciliation_status"] = "ok"
                else:
                    entry["reconciliation_status"] = "mismatch"
                    entry["reconciliation_note"] = (
                        f"紙日報合計 {total_paper} (= 通常 {paper_amount} + 補正 {breakdown_sum}) "
                        f"≠ メーター明細 {meter.amount}"
                    )
            else:
                entry["reconciliation_status"] = "no_meter"
                entry["reconciliation_note"] = "メーター明細が無い"

        elif row.row_type == "meter_overrun_adjustment":
            entry["reconciliation_status"] = "breakdown_of_meter_fare"
            entry["reconciliation_note"] = (
                f"メーター超過: 関連行 {row_adj.related_row_index if row_adj else '?'} の内訳"
            )

        elif row.row_type == "disability_discount_adjustment":
            entry["reconciliation_status"] = "review"
            entry["reconciliation_note"] = (
                row_adj.note if row_adj else "障害者割引: 人間判断が必要"
            )

        elif row.row_type == "charter_fare":
            entry["reconciliation_status"] = "paper_only"
            entry["reconciliation_note"] = "貸切: メーター明細と照合しない"

        elif row.row_type == "blank":
            entry["reconciliation_status"] = "blank"

        else:  # review
            entry["reconciliation_status"] = "review"
            entry["reconciliation_note"] = "分類不能、人間判断が必要"

        results.append(entry)
    return results


def build_final_rows(
    paper_rows: List[PaperRow],
    meter_rows: List[MeterRow],
    adjustments: List[AdjustmentResult],
) -> List[dict]:
    """最終表 (= 日報と同じ 25 行) を組み立てる.

    各行に gen / mi / memo / status を含める. 表示用の gen / mi は、
    金額がない場合 0 ではなく "" (= 空欄のまま) を保持する.
    合計は calculate_totals() が int だけを集計するので "" は無視される.

      - meter_fare 行: 紙日報の金額を保持し、メーター明細は整合確認に使う
        (= 上書きしない. 上書きすると超過行 +100 と合わせて二重計上になる)
      - meter_overrun_adjustment 行: 別行として超過分を計上
      - disability_discount_adjustment 行: 紙の数字を採用 (= review)
      - charter_fare 行: 紙の数字を採用 (= meter_rows には無い独立行)
      - review 行: 金額なし、人間判断待ち (gen / mi は "")
      - blank 行: 完全空欄 (gen / mi は "")
    """
    reconciled = reconcile_meter_with_paper(paper_rows, meter_rows, adjustments)
    adj_by_row: Dict[int, AdjustmentResult] = {}
    for adj in adjustments:
        adj_by_row.setdefault(adj.row_index, adj)

    final_rows: List[dict] = []
    for row, rec in zip(paper_rows, reconciled):
        adj = adj_by_row.get(row.paper_row)
        gen: Any = ""
        mi: Any = ""
        status = "blank"

        if row.row_type == "meter_fare":
            # 通常営業行は紙日報の金額を保持. メーター明細値で上書きしない.
            # 理由: メーター超過があるケースで通常行を meter_amount に
            # 上書きすると、メーター超過分と合わせて二重計上になる.
            # (例: 紙 1300 を 1400 に上書き + 超過 +100 = 1500 になる事故)
            # 紙の数字は「客が実際に払った金額」、メーター明細は整合確認用.
            # 不一致は reconciliation_status で示す.
            gen = _extract_amount_or_blank(row.gen_raw)
            mi = _extract_amount_or_blank(row.mi_raw)
            status = rec.get("reconciliation_status", "ok")
        elif row.row_type == "meter_overrun_adjustment":
            if adj:
                if adj.side == "gen":
                    gen = adj.amount
                elif adj.side == "mi":
                    mi = adj.amount
            status = "meter_overrun"
        elif row.row_type == "disability_discount_adjustment":
            if adj:
                if adj.side == "gen":
                    gen = adj.amount
                elif adj.side == "mi":
                    mi = adj.amount
            status = adj.status if adj else "review"
        elif row.row_type == "charter_fare":
            if adj:
                if adj.side == "gen":
                    gen = adj.amount
                elif adj.side == "mi":
                    mi = adj.amount
            status = "charter"
        else:
            status = row.row_type  # "blank" or "review"

        final_rows.append({
            "paper_row": row.paper_row,
            "time": row.time,
            "passengers": row.passengers,
            "gen": gen,
            "mi": mi,
            "memo": row.memo,
            "row_type": row.row_type,
            "status": status,
            "reconciliation_status": rec.get("reconciliation_status"),
            "reconciliation_note": rec.get("reconciliation_note"),
        })
    return final_rows


# ═══════════════════════════════════════════════════════════════════
# Section 7: 集計
# ═══════════════════════════════════════════════════════════════════

def calculate_totals(final_rows: List[dict]) -> dict:
    """現金件数・未収件数・現金合計・未収合計・総売上を計算.

    blank / review は件数集計から除外 (= status を見て判断).
    """
    gen_values = [r["gen"] for r in final_rows if isinstance(r.get("gen"), int) and r["gen"] > 0]
    mi_values = [r["mi"] for r in final_rows if isinstance(r.get("mi"), int) and r["mi"] > 0]
    gen_total = sum(gen_values)
    mi_total = sum(mi_values)
    return {
        "gen_count": len(gen_values),
        "mi_count": len(mi_values),
        "gen_total": gen_total,
        "mi_total": mi_total,
        "total": gen_total + mi_total,
    }


# ═══════════════════════════════════════════════════════════════════
# ヘルパー (内部使用)
# ═══════════════════════════════════════════════════════════════════

def _normalize_digits(text: Any) -> str:
    """文字列から数字だけ抽出 (例: '+100' → '100')."""
    if text is None:
        return ""
    return "".join(ch for ch in str(text) if ch.isdigit())


def _has_value(text: Any) -> bool:
    """セルに数字が書かれてるか."""
    return _normalize_digits(text) != ""


def _extract_amount(text: Any) -> int:
    """セルの値を整数に変換. 空欄なら 0."""
    digits = _normalize_digits(text)
    if digits == "":
        return 0
    return int(digits)


def _extract_amount_or_blank(text: Any):
    """セルの値を整数に変換. 空欄なら "" を返す (= 表示用、空欄を 0 に変えない).

    最終表の gen / mi 列で使う. 合計集計は calculate_totals() が
    int だけ拾うので "" は自動的に無視される.
    """
    digits = _normalize_digits(text)
    if digits == "":
        return ""
    return int(digits)
