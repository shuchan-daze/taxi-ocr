"""OpenAI OCR adapter for the single Kamichizu case contract."""

from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OPENAI_OCR_MODEL = "gpt-4o"


@dataclass(frozen=True)
class OcrImage:
    name: str
    mime_type: str
    data: bytes


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
- meter_amount は対象乗車のメーター明細金額
- expected_claim_amount は紙日報の障割額

貸切が紙日報にある場合:
- claims に type=charter_sale を追加
- payment_kind は紙の欄位置に従い gen または mi

判断できない値は作らず、読めたセルだけ cells に入れてください。"""


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
    return _extract_json_object(content_text)
