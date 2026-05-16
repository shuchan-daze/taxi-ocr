"""紙日報の固定グリッド構造 — 座標ベース設計の土台.

Shuchan の哲学 (2026-05-17):
- 日報の構造は OCR や AI に作らせない. Python 側で固定の空セルを先に作る.
- OCR の役割は「文字を読む + 物理座標を返す」だけ.
- AI に「これは何行目？」と判断させない. セル判定は Python が機械的に行う.
- 紙日報の固定グリッドが絶対基準. OCR 順は信用しない.

最小実装 (4 関数):
  1. build_empty_cell_map()       — 固定の 125 セルを空で生成
  2. find_cell_by_xy()             — トークン座標 → セル住所を機械的に判定
  3. assign_ocr_tokens_to_cells()  — OCR トークンを cell_map に配置
  4. build_paper_rows_from_cell_map() — cell_map → paper_rows に変換

OpenCV の罫線検出やセル切り出し OCR は後段の改善で対応する.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


# =========================
# データ構造
# =========================

@dataclass
class OCRToken:
    """OCR が返す 1 トークン (= 文字 or 単語) + 物理座標."""
    text: str
    x: float       # 左上 x (px)
    y: float       # 左上 y (px)
    w: float       # 幅 (px)
    h: float       # 高さ (px)
    confidence: Optional[float] = None


@dataclass
class CellAddress:
    """セル住所 (= 論理座標). R{行}_{列} の形式."""
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
    """日報の 1 行 (= cell_map から組み立てた行データ)."""
    paper_row: int
    time: str = ""
    passengers: str = ""
    gen_raw: str = ""
    mi_raw: str = ""
    memo: str = ""


# =========================
# テンプレート (= 紙日報の固定フォーマット)
# =========================
#
# 相対座標 (0.0〜1.0) で列の x 範囲と行の y 範囲を定義.
# 紙日報の歪みや写真サイズに依存しないように、相対値で持つ.
# 罫線検出 + 補正は将来段階で実装、まずはこの固定テンプレートで動作させる.
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


# =========================
# 1. 固定の空セルを先に作る
# =========================

def build_empty_cell_map(template: Optional[dict] = None) -> Dict[str, Cell]:
    """日報の固定フォーマットを「絶対の器」として先に作る.

    OCR で読めても読めなくても、全 125 セル (25 行 × 5 列) を必ず作る.
    OCR 順に依存しない構造の土台.

    Returns:
        Dict[cell_id, Cell]: 全セルが空状態 (value="", source="blank")
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


# =========================
# 2. トークン座標 → セル住所 (機械的判定)
# =========================

def find_cell_by_xy(
    token: OCRToken,
    template: dict,
    image_width: float,
    image_height: float,
) -> Optional[CellAddress]:
    """トークンの中心座標から、機械的にセル住所を決める.

    AI の判断は介在しない. テンプレートの相対座標範囲と比較するだけ.
    範囲外のトークンは None (= 表外の文字、ヘッダ等).
    """
    if image_width <= 0 or image_height <= 0:
        return None

    cx = token.x + token.w / 2.0
    cy = token.y + token.h / 2.0
    rx = cx / image_width
    ry = cy / image_height

    # 行範囲を線形探索 (25 行なので O(N) で十分)
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


# =========================
# 3. OCR トークンを cell_map に配置
# =========================

def assign_ocr_tokens_to_cells(
    cell_map: Dict[str, Cell],
    ocr_tokens: List[OCRToken],
    template: dict,
    image_width: float,
    image_height: float,
) -> Dict[str, Cell]:
    """OCR トークンを XY 座標で cell_map に振り分ける.

    OCR の戻り順は完全に無視. 物理座標だけで判定.
    範囲外のトークンは捨てる. 該当セルに OCR 結果が入ったら source='ocr'.

    各セル内のトークンは上から下・左から右にソートし、value を組み立てる:
    - 数字系列 (gen / mi / passengers): 区切りなしで連結 (例: '12' + '30' → '1230')
    - 文字系列 (time / memo): スペース区切りで連結
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

    # セル内の文字を組み立てる
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


# =========================
# 4. cell_map → paper_rows
# =========================

def _get_cell_value(cell_map: Dict[str, Cell], row_no: int, col: str) -> str:
    cell_id = f"R{row_no:02d}_{col.upper()}"
    cell = cell_map.get(cell_id)
    return cell.value if cell else ""


def build_paper_rows_from_cell_map(
    cell_map: Dict[str, Cell],
    total_rows: int = 25,
) -> List[PaperRow]:
    """cell_map から日報と同じ形の paper_rows を組み立てる.

    全行を必ず生成 (= 空行も詰めない). cell_map の値をそのまま行に流し込むだけ.
    AI の判断は一切介在しない.
    """
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
