"""Anthropic image OCR adapters for Kamichizu app inputs."""

from __future__ import annotations

import base64
import json
from io import BytesIO
from typing import Any, Mapping

from PIL import Image, ImageOps, UnidentifiedImageError


DEFAULT_ANTHROPIC_OCR_MODEL = "claude-opus-4-5"
PAPER_FIELDS = {"passengers", "route", "time", "gen", "mi", "memo"}
OBSERVED_STATES = {"observed", "blank", "unreadable", "empty_unknown", "missing"}


class AnthropicOcrError(RuntimeError):
    """Raised when Anthropic OCR cannot produce official Kamichizu inputs."""


def make_anthropic_client(api_key: str):
    """Create an Anthropic client lazily so tests can import app.py without the SDK."""

    try:
        import anthropic
    except ImportError as exc:
        raise AnthropicOcrError("anthropic package is not installed. Run pip install -r requirements.txt") from exc
    return anthropic.Anthropic(api_key=api_key)


def image_file_to_data_url(uploaded_file, *, max_side: int = 1800, quality: int = 85) -> str:
    """Convert an uploaded image to a compact JPEG data URL for image OCR."""

    try:
        try:
            import pillow_heif

            pillow_heif.register_heif_opener()
        except Exception:
            pass

        with Image.open(BytesIO(uploaded_file.getvalue())) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            image.thumbnail((max_side, max_side))
            output = BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise AnthropicOcrError(f"image could not be opened: {getattr(uploaded_file, 'name', '')}") from exc

    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _message_output_text(message: Any) -> str:
    chunks: list[str] = []
    for block in getattr(message, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            chunks.append(str(text))
    if chunks:
        return "".join(chunks)
    raise AnthropicOcrError("Anthropic response did not include text output")


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise AnthropicOcrError("OCR response did not include a JSON object")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AnthropicOcrError(f"OCR response was not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AnthropicOcrError("OCR response root must be a JSON object")
    return data


def _create_image_json_response(
    client: Any,
    *,
    model: str,
    image_data_url: str,
    prompt: str,
) -> dict[str, Any]:
    media_type, encoded = _split_data_url(image_data_url)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return _extract_json_object(_message_output_text(message))


def _split_data_url(data_url: str) -> tuple[str, str]:
    prefix, _, encoded = data_url.partition(",")
    if not encoded or not prefix.startswith("data:"):
        raise AnthropicOcrError("invalid image data URL")
    media_type = prefix.removeprefix("data:").split(";", 1)[0] or "image/jpeg"
    return media_type, encoded


def _paper_prompt() -> str:
    return (
        "紙日報の画像を読み、神地図エンジンへ渡す紙セル観測JSONだけを返してください。\n"
        "紙は固定セル住所の地図です。判断や採用金額の決定はしません。\n"
        "セルIDは R01_PASSENGERS, R01_ROUTE, R01_TIME, R01_GEN, R01_MI, R01_MEMO の形式です。\n"
        "行番号は紙面上の行位置で決め、読めた順番では補完しないでください。\n"
        "対象フィールドは passengers, route, time, gen, mi, memo です。\n"
        "読めたセルだけを cells に入れてください。空欄は無理に返さなくて構いません。\n"
        "何か書いてありそうだが読めない場合は observed_state='unreadable' にしてください。\n"
        "金額や人数は value を数値にしてください。時刻・区間・摘要は文字列にしてください。\n"
        "JSON以外の説明文は返さないでください。"
    )


def _meter_prompt() -> str:
    return (
        "メーター明細またはレシート画像を読み、神地図エンジンへ渡すメーター明細JSONだけを返してください。\n"
        "必ず次の形のJSONオブジェクトだけを返してください: "
        '{"schema":"meter_data","rows":[{"ride_id":"M01","time":"09:46","amount":900,"payment_hint":null,"raw":"09:46 900"}]}\n'
        "rows は必ずJSON直下に置き、別名や説明文やMarkdownを付けないでください。\n"
        "印字された乗車明細の順番を保ち、各行の時刻と金額を抽出してください。\n"
        "ride_id は M01, M02 のように明細順で付けてください。\n"
        "amount は円の整数にしてください。支払種別らしき文字があれば payment_hint に入れてください。\n"
        "読めない行は作らないでください。JSON以外の説明文は返さないでください。"
    )


def _normalize_cell_id(cell_id: Any) -> str:
    value = str(cell_id or "").strip().upper()
    if not value:
        raise AnthropicOcrError("paper OCR cell has empty cell_id")
    return value


def _normalize_observed_state(value: Any) -> str:
    state = str(value or "observed").strip().lower()
    if state not in OBSERVED_STATES:
        return "empty_unknown"
    return state


def _normalize_paper_value(cell_id: str, value: Any) -> Any:
    field = cell_id.rsplit("_", 1)[-1].lower()
    if value in ("", None):
        return None
    if field in {"passengers", "gen", "mi"}:
        text = str(value).replace(",", "").replace("円", "").strip()
        try:
            return int(text)
        except ValueError:
            return value
    return value


def normalize_paper_ocr_response(data: Mapping[str, Any]) -> dict[str, Any]:
    cells_list = data.get("cells")
    if "cells" not in data:
        raise AnthropicOcrError("paper OCR response requires top-level cells")
    if not isinstance(cells_list, list):
        raise AnthropicOcrError("paper OCR response cells must be a list")

    cells: dict[str, dict[str, Any]] = {}
    for item in cells_list:
        if not isinstance(item, Mapping):
            continue
        cell_id = _normalize_cell_id(item.get("cell_id"))
        field = cell_id.rsplit("_", 1)[-1].lower()
        if field not in PAPER_FIELDS:
            continue
        raw = "" if item.get("raw") is None else str(item.get("raw"))
        cells[cell_id] = {
            "raw": raw,
            "value": _normalize_paper_value(cell_id, item.get("value")),
            "confidence": item.get("confidence"),
            "ambiguous": bool(item.get("ambiguous")),
            "observed_state": _normalize_observed_state(item.get("observed_state")),
            "notes": "" if item.get("notes") is None else str(item.get("notes")),
        }

    if not cells:
        raise AnthropicOcrError("paper OCR produced no usable cells")
    return {"schema": "paper_map", "cells": cells}


def _normalize_amount(value: Any) -> int:
    text = str(value).replace(",", "").replace("円", "").strip()
    return int(text)


def normalize_meter_ocr_response(data: Mapping[str, Any]) -> dict[str, Any]:
    if "rows" not in data:
        raise AnthropicOcrError("meter OCR response requires top-level rows")
    rows_list = data.get("rows")
    if not isinstance(rows_list, list):
        raise AnthropicOcrError("meter OCR response rows must be a list")

    rows: list[dict[str, Any]] = []
    for index, item in enumerate(rows_list, start=1):
        if not isinstance(item, Mapping):
            continue
        try:
            amount = _normalize_amount(item.get("amount"))
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                "ride_id": str(item.get("ride_id") or f"M{index:02d}"),
                "time": item.get("time"),
                "amount": amount,
                "payment_hint": item.get("payment_hint"),
                "raw": "" if item.get("raw") is None else str(item.get("raw")),
            }
        )

    if not rows:
        raise AnthropicOcrError("meter OCR produced no usable rows")
    return {"schema": "meter_data", "rows": rows}


def ocr_paper_map(client: Any, uploaded_file, *, model: str = DEFAULT_ANTHROPIC_OCR_MODEL) -> dict[str, Any]:
    data = _create_image_json_response(
        client,
        model=model,
        image_data_url=image_file_to_data_url(uploaded_file),
        prompt=_paper_prompt(),
    )
    return normalize_paper_ocr_response(data)


def ocr_meter_data(client: Any, uploaded_file, *, model: str = DEFAULT_ANTHROPIC_OCR_MODEL) -> dict[str, Any]:
    data = _create_image_json_response(
        client,
        model=model,
        image_data_url=image_file_to_data_url(uploaded_file),
        prompt=_meter_prompt(),
    )
    return normalize_meter_ocr_response(data)
