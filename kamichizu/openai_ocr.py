"""OpenAI OCR adapter for Kamichizu observations only.

OCR is allowed to observe documents.  It must not adopt amounts, create claims,
choose a view, or complete a report.  Layer 2 and Layer 3 own those decisions.
"""

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
    """Raised when OCR output does not match the observation contract."""


def build_observation_ocr_prompt() -> str:
    return """あなたはタクシー手書き日報とメーター明細を読むOCRです。

目的:
写真から、紙面と証拠資料の観測JSONだけを返してください。

絶対ルール:
- JSONだけを返す
- 説明文、Markdown、コードブロックは禁止
- セルIDは物理住所だけにする。例: 01_AA, 01_AB, 02_AF
- GEN, MI, MEMO, TIME など意味入りセルIDは禁止
- 別名キーは禁止
- paper / paper_format / evidences を必ず返す
- claims は返さない
- view は返さない
- summary は返さない
- adopted や total を返さない
- 障割請求、貸切売上、総売上を作らない
- 読み取りと判断を混ぜない
- 写真のアップロード順に依存しない
- 画像ごとに紙日報かメーター明細かを自動判別する
- 紙日報は paper に、メーター明細は evidences に入れる
- 紙日報の金額OCRは確定値ではない。確定金額は後段で証拠資料と照合する
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
  ]
}

障割・貸切・自己負担などの特例:
- claims を作らない
- その文字が紙に見える場合は memo セルの raw/value に観測として残す
- 特例判断は後段の Layer 3 が行う
"""


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
            raise OcrContractError(f"{name}.{key} is not part of the observation contract")


def _validate_cells(data: Any, name: str) -> None:
    cells = _mapping(data, name)
    if not cells:
        raise OcrContractError(f"{name} must not be empty")
    for cell_id, cell_data in cells.items():
        split_local_cell_id(str(cell_id))
        _mapping(cell_data, f"{name}.{cell_id}")


def validate_observation_ocr_response(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate OCR observations before Layer 2 can adopt anything."""

    observation = _mapping(data, "ocr_response")
    _reject_keys(
        observation,
        ("paper_map", "paper_map_v1", "meter_data", "meter_rows", "rows", "claims", "view", "summary", "adopted"),
        "ocr_response",
    )

    paper = _mapping(_require(observation, "paper", "ocr_response"), "paper")
    _reject_keys(paper, ("rows",), "paper")
    _validate_cells(_require(paper, "cells", "paper"), "paper.cells")
    for key in ("source_id", "source_role", "source_type", "format_id"):
        _require(paper, key, "paper")

    paper_format = _mapping(_require(observation, "paper_format", "ocr_response"), "paper_format")
    _mapping(_require(paper_format, "columns", "paper_format"), "paper_format.columns")

    evidences = _list(_require(observation, "evidences", "ocr_response"), "ocr_response.evidences")
    if not evidences:
        raise OcrContractError("ocr_response.evidences must include at least one evidence source")
    for index, evidence_data in enumerate(evidences):
        evidence = _mapping(evidence_data, f"evidences[{index}]")
        source = _mapping(_require(evidence, "source", f"evidences[{index}]"), f"evidences[{index}].source")
        _reject_keys(source, ("rows",), f"evidences[{index}].source")
        _validate_cells(_require(source, "cells", f"evidences[{index}].source"), f"evidences[{index}].source.cells")
        format_map = _mapping(_require(evidence, "format", f"evidences[{index}]"), f"evidences[{index}].format")
        _mapping(_require(format_map, "columns", f"evidences[{index}].format"), f"evidences[{index}].format.columns")

    return observation


def build_observations_from_images(
    images: list[OcrImage],
    *,
    api_key: str,
    model: str = DEFAULT_OPENAI_OCR_MODEL,
    timeout: int = 120,
) -> Mapping[str, Any]:
    """Call OpenAI vision OCR and return source observations only."""

    if len(images) < 2:
        raise ValueError("日報とメーター明細の写真を2枚以上選択してください")
    content: list[dict[str, Any]] = [{"type": "text", "text": build_observation_ocr_prompt()}]
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
    return validate_observation_ocr_response(_extract_json_object(content_text))
