"""OpenAI OCR adapter for the single Kamichizu case contract."""

from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

from .models import split_local_cell_id


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OPENAI_OCR_MODEL = "gpt-4o"


@dataclass(frozen=True)
class OcrImage:
    name: str
    mime_type: str
    data: bytes


class OcrContractError(ValueError):
    """Raised when OCR output does not match the formal Kamichizu case contract."""


def build_case_ocr_prompt() -> str:
    return """あなたはタクシー手書き日報を神地図形式へ変換するOCRです。

目的:
写真の紙日報とメーター明細から、神地図エンジンの正式ケースJSONだけを返してください。

絶対ルール:
- JSONだけを返す
- 説明文、Markdown、コードブロックは禁止
- セルIDは物理住所だけにする。例: 01_AA, 01_AB, 02_AF
- GEN, MI, MEMO, TIME など意味入りセルIDは禁止
- 別名キーは禁止
- paper / paper_format / evidences / view を必ず返す
- 写真のアップロード順に依存しない
- 画像ごとに紙日報かメーター明細かを自動判別する
- 紙日報は paper に、メーター明細は evidences に入れる
- 紙日報の金額OCRは確定値ではない。確定金額はメーター明細で照合する
- 紙日報では時刻、現収欄/未収欄の位置、摘要の支払い種別を優先して読む
- 現収欄/未収欄に何か書かれているが金額が読めない場合も、そのセルを raw に残し value は null にする

紙日報の標準列:
AA=no, AB=passengers, AC=route, AD=time, AE=gen, AF=mi, AG=memo

メーター明細の標準列:
AA=time, AB=amount

返すJSONの形:
{
  "paper": {
    "source_id": "P01",
    "source_role": "primary",
    "source_type": "daily_report",
    "label": "daily_report",
    "format_id": "daily_report_default",
    "cells": {
      "01_AA": {"raw": "1", "value": 1},
      "01_AD": {"raw": "10:44", "value": "10:44"},
      "01_AF": {"raw": "2,400", "value": 2400}
    }
  },
  "paper_format": {
    "format_id": "daily_report_default",
    "columns": {
      "AA": "no",
      "AB": "passengers",
      "AC": "route",
      "AD": "time",
      "AE": "gen",
      "AF": "mi",
      "AG": "memo"
    }
  },
  "evidences": [
    {
      "source": {
        "source_id": "E01",
        "source_role": "evidence",
        "source_type": "meter_receipt",
        "label": "meter_receipt",
        "format_id": "meter_receipt_default",
        "cells": {
          "01_AA": {"raw": "10:44", "value": "10:44"},
          "01_AB": {"raw": "2,430", "value": 2430}
        }
      },
      "format": {
        "format_id": "meter_receipt_default",
        "columns": {
          "AA": "time",
          "AB": "amount"
        }
      }
    }
  ],
  "claims": [],
  "view": {
    "view_id": "daily_report_table",
    "columns": [
      ["no", "No"],
      ["passengers", "人数"],
      ["time", "時刻"],
      ["gen", "現収"],
      ["mi", "未収"],
      ["memo", "摘要"],
      ["status", "状態"]
    ]
  }
}

障割が紙日報にある場合:
- claims に type=public_discount_claim を追加
- target_row_addr は対象乗車の紙行
- target_global_cell_id は対象乗車の金額セルのグローバル住所。例: P01:03_AF
- meter_amount は対象乗車のメーター明細金額
- expected_claim_amount は紙日報の障割額
- evidence は必須。paper_cell / evidence_cell / reason を持つ根拠を入れる

貸切が紙日報にある場合:
- claims に type=charter_sale を追加
- claim_amount は貸切金額
- target_global_cell_id は貸切を示す紙セルのグローバル住所。例: P01:06_AG
- payment_kind は紙の欄位置に従い gen または mi
- evidence は必須。paper_cell / evidence_cell / reason を持つ根拠を入れる

判断できない金額を推測して作らないでください。
ただし、現収欄/未収欄/摘要に書き込みが見える場合は、金額が読めなくてもセル住所を残してください。"""


def _data_url(image: OcrImage) -> str:
    encoded = base64.b64encode(image.data).decode("ascii")
    return f"data:{image.mime_type};base64,{encoded}"


def _extract_json_object(text: str) -> Mapping[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    data = json.loads(stripped)
    if not isinstance(data, Mapping):
        raise ValueError("OCR response must be a JSON object")
    return data


def _mapping(data: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise OcrContractError(f"{name} must be an object")
    return data


def _list(data: Any, name: str) -> list[Any]:
    if not isinstance(data, list):
        raise OcrContractError(f"{name} must be a list")
    return data


def _require(data: Mapping[str, Any], key: str, name: str) -> Any:
    if key not in data:
        raise OcrContractError(f"{name}.{key} is required")
    return data[key]


def _reject_keys(data: Mapping[str, Any], forbidden: tuple[str, ...], name: str) -> None:
    for key in forbidden:
        if key in data:
            raise OcrContractError(f"{name}.{key} is not part of the Kamichizu case contract")


def _validate_cells(data: Any, name: str) -> None:
    cells = _mapping(data, name)
    if not cells:
        raise OcrContractError(f"{name} must not be empty")
    for cell_id, cell_data in cells.items():
        split_local_cell_id(str(cell_id))
        _mapping(cell_data, f"{name}.{cell_id}")


def validate_case_ocr_response(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate OCR output before it can enter the Kamichizu engine."""

    case_data = _mapping(data, "ocr_response")
    _reject_keys(case_data, ("paper_map", "paper_map_v1", "meter_data", "meter_rows", "rows"), "ocr_response")

    paper = _mapping(_require(case_data, "paper", "ocr_response"), "paper")
    _reject_keys(paper, ("rows",), "paper")
    _validate_cells(_require(paper, "cells", "paper"), "paper.cells")
    for key in ("source_id", "source_role", "source_type", "format_id"):
        _require(paper, key, "paper")

    paper_format = _mapping(_require(case_data, "paper_format", "ocr_response"), "paper_format")
    _mapping(_require(paper_format, "columns", "paper_format"), "paper_format.columns")

    evidences = _list(_require(case_data, "evidences", "ocr_response"), "ocr_response.evidences")
    if not evidences:
        raise OcrContractError("ocr_response.evidences must include at least one meter evidence source")
    for index, evidence_data in enumerate(evidences):
        evidence = _mapping(evidence_data, f"evidences[{index}]")
        source = _mapping(_require(evidence, "source", f"evidences[{index}]"), f"evidences[{index}].source")
        _reject_keys(source, ("rows",), f"evidences[{index}].source")
        _validate_cells(_require(source, "cells", f"evidences[{index}].source"), f"evidences[{index}].source.cells")
        format_map = _mapping(_require(evidence, "format", f"evidences[{index}]"), f"evidences[{index}].format")
        _mapping(_require(format_map, "columns", f"evidences[{index}].format"), f"evidences[{index}].format.columns")

    view = _mapping(_require(case_data, "view", "ocr_response"), "view")
    _list(_require(view, "columns", "view"), "view.columns")
    return case_data


def build_case_from_images(
    images: list[OcrImage],
    *,
    api_key: str,
    model: str = DEFAULT_OPENAI_OCR_MODEL,
    timeout: int = 120,
) -> Mapping[str, Any]:
    """Call OpenAI vision OCR and return the single formal case JSON."""

    if len(images) < 2:
        raise ValueError("日報とメーター明細の写真を2枚以上選択してください")
    content: list[dict[str, Any]] = [{"type": "text", "text": build_case_ocr_prompt()}]
    for image in images:
        content.append({"type": "text", "text": f"image file: {image.name}"})
        content.append({"type": "image_url", "image_url": {"url": _data_url(image)}})

    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": content}],
    }
    request = urllib.request.Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    content_text = body["choices"][0]["message"]["content"]
    return validate_case_ocr_response(_extract_json_object(content_text))
