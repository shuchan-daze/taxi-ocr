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


def build_source_observation_ocr_prompt() -> str:
    return """あなたは1枚の画像だけを読むOCRです。

目的:
この画像1枚に実際に見える文字とセルだけを、観測JSONとして返してください。

絶対ルール:
- JSONだけを返す
- 説明文、Markdown、コードブロックは禁止
- セルIDは物理住所だけにする。例: 01_AA, 01_AB, 02_AF
- GEN, MI, MEMO, TIME など意味入りセルIDは禁止
- 別名キーは禁止
- source / format だけを返す
- この1枚に見えない資料の情報を作らない
- claims は返さない
- view は返さない
- summary は返さない
- adopted や total を返さない
- 障割請求、貸切売上、総売上を作らない
- 読み取りと判断を混ぜない
- この画像が紙日報かメーター明細かだけを source_type で分類する
- 紙日報画像なら、紙日報に実際に見える文字だけを source.cells に入れる
- メーター明細画像なら、メーター明細に実際に見える文字だけを source.cells に入れる
- 資料間の補完、転記、採用判断は禁止
- メーター明細の金額、時刻、カード名、支払い名を紙日報として返さない
- メーター明細の金額から紙日報の現収欄/未収欄を推測して埋めない
- 紙日報の欄位置が不明な金額を、未収欄に寄せてはいけない
- 現収欄と未収欄の区別ができない場合は、見えた文字を raw に残し、value は null、state は "unreadable" にする
- 紙日報の現収欄に見える金額は AE、未収欄に見える金額は AF に置く
- 紙日報の金額OCRは確定値ではない。確定金額は後段で証拠資料と照合する
- 紙日報では時刻、現収欄/未収欄の位置、摘要の支払い種別を優先して読む
- 現収欄/未収欄に何か書かれているが金額が読めない場合も、そのセルを raw に残し value は null にする

紙日報の標準列:
AA=no, AB=passengers, AC=route, AD=time, AE=gen, AF=mi, AG=memo

メーター明細の標準列:
AA=time, AB=amount

返すJSONの形:
{
  "source": {
    "source_type": "daily_report",
    "label": "daily_report",
    "format_id": "daily_report_default",
    "cells": {
      "01_AA": {"raw": "1", "value": 1},
      "01_AD": {"raw": "10:44", "value": "10:44"},
      "01_AF": {"raw": "2,400", "value": 2400}
    }
  },
  "format": {
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
  }
}

障割・貸切・自己負担などの特例:
- claims を作らない
- その文字が紙に見える場合は memo セルの raw/value に観測として残す
- 特例判断は後段の Layer 3 が行う
"""


def build_observation_ocr_prompt() -> str:
    """Existing public name delegates to the per-source OCR prompt."""

    return build_source_observation_ocr_prompt()


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


def validate_source_observation_ocr_response(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate one-image OCR output before it is combined with other sources."""

    observation = _mapping(data, "source_ocr_response")
    _reject_keys(
        observation,
        (
            "paper",
            "paper_format",
            "evidences",
            "paper_map",
            "paper_map_v1",
            "meter_data",
            "meter_rows",
            "rows",
            "claims",
            "view",
            "summary",
            "adopted",
        ),
        "source_ocr_response",
    )
    source = _mapping(_require(observation, "source", "source_ocr_response"), "source")
    _reject_keys(source, ("rows", "source_id", "source_role"), "source")
    source_type = str(_require(source, "source_type", "source"))
    if source_type not in ("daily_report", "meter_receipt"):
        raise OcrContractError("source.source_type must be daily_report or meter_receipt")
    _validate_cells(_require(source, "cells", "source"), "source.cells")
    _require(source, "format_id", "source")

    format_map = _mapping(_require(observation, "format", "source_ocr_response"), "format")
    _mapping(_require(format_map, "columns", "format"), "format.columns")
    return observation


def _source_with_identity(source: Mapping[str, Any], *, source_id: str, source_role: str) -> dict[str, Any]:
    return {
        **dict(source),
        "source_id": source_id,
        "source_role": source_role,
        "label": str(source.get("label", source.get("source_type", source_id))),
    }


def combine_source_observations(source_observations: list[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Combine independently observed sources into the app observation contract."""

    validated = [validate_source_observation_ocr_response(data) for data in source_observations]
    daily_reports = [
        data for data in validated if _mapping(data["source"], "source")["source_type"] == "daily_report"
    ]
    evidence_sources = [
        data for data in validated if _mapping(data["source"], "source")["source_type"] == "meter_receipt"
    ]
    if len(daily_reports) != 1:
        raise OcrContractError("OCR must produce exactly one daily_report source")
    if not evidence_sources:
        raise OcrContractError("OCR must produce at least one meter_receipt source")

    paper_source = _mapping(daily_reports[0]["source"], "paper_source")
    paper = _source_with_identity(paper_source, source_id="P01", source_role="primary")
    paper_format = dict(_mapping(daily_reports[0]["format"], "paper_format"))

    evidences: list[dict[str, Any]] = []
    for index, evidence_data in enumerate(evidence_sources, start=1):
        source = _mapping(evidence_data["source"], f"evidence_source[{index}]")
        evidence_id = f"E{index:02d}"
        evidences.append(
            {
                "source": _source_with_identity(source, source_id=evidence_id, source_role="evidence"),
                "format": dict(_mapping(evidence_data["format"], f"evidence_format[{index}]")),
            }
        )
    return validate_observation_ocr_response(
        {
            "paper": paper,
            "paper_format": paper_format,
            "evidences": evidences,
        }
    )


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


def _call_openai_for_source_image(
    image: OcrImage,
    *,
    api_key: str,
    model: str,
    timeout: int,
) -> Mapping[str, Any]:
    content: list[dict[str, Any]] = [
        {"type": "text", "text": build_source_observation_ocr_prompt()},
        {"type": "text", "text": f"image file: {image.name}"},
        {"type": "image_url", "image_url": {"url": _data_url(image)}},
    ]
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
    return validate_source_observation_ocr_response(_extract_json_object(content_text))


def build_observations_from_images(
    images: list[OcrImage],
    *,
    api_key: str,
    model: str = DEFAULT_OPENAI_OCR_MODEL,
    timeout: int = 120,
) -> Mapping[str, Any]:
    """Call OpenAI vision OCR one image at a time and combine observations."""

    if len(images) < 2:
        raise ValueError("日報とメーター明細の写真を2枚以上選択してください")
    source_observations = [
        _call_openai_for_source_image(image, api_key=api_key, model=model, timeout=timeout)
        for image in images
    ]
    return combine_source_observations(source_observations)
