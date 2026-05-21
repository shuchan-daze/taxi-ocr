import unittest
import json

from kamichizu.openai_ocr import (
    OcrContractError,
    OcrImage,
    _extract_json_object,
    build_case_ocr_prompt,
    validate_case_ocr_response,
)


def minimal_ocr_case() -> dict[str, object]:
    return {
        "paper": {
            "source_id": "P01",
            "source_role": "primary",
            "source_type": "daily_report",
            "format_id": "daily_report_default",
            "cells": {
                "01_AD": {"raw": "10:44", "value": "10:44"},
                "01_AF": {"raw": "2,400", "value": 2400},
            },
        },
        "paper_format": {
            "format_id": "daily_report_default",
            "columns": {
                "AD": "time",
                "AF": "mi",
            },
        },
        "evidences": [
            {
                "source": {
                    "source_id": "E01",
                    "source_role": "evidence",
                    "source_type": "meter_receipt",
                    "format_id": "meter_receipt_default",
                    "cells": {
                        "01_AA": {"raw": "10:44", "value": "10:44"},
                        "01_AB": {"raw": "2,430", "value": 2430},
                    },
                },
                "format": {
                    "format_id": "meter_receipt_default",
                    "columns": {
                        "AA": "time",
                        "AB": "amount",
                    },
                },
            }
        ],
        "view": {
            "view_id": "daily_report_table",
            "columns": [["time", "時刻"], ["mi", "未収"]],
        },
    }


class OpenAiOcrTest(unittest.TestCase):
    def test_prompt_requires_single_formal_case_contract(self):
        prompt = build_case_ocr_prompt()

        self.assertIn('"paper"', prompt)
        self.assertIn('"evidences"', prompt)
        self.assertIn('"view"', prompt)
        self.assertIn("セルIDは物理住所だけ", prompt)
        self.assertIn("別名キーは禁止", prompt)
        self.assertIn("写真のアップロード順に依存しない", prompt)
        self.assertIn("自動判別", prompt)

    def test_extract_json_object_accepts_json_object(self):
        data = _extract_json_object(json.dumps({"paper": {}, "evidences": []}))

        self.assertEqual(data["paper"], {})

    def test_extract_json_object_rejects_non_object(self):
        with self.assertRaises(ValueError):
            _extract_json_object("[]")

    def test_ocr_image_keeps_uploaded_bytes(self):
        image = OcrImage(name="a.jpg", mime_type="image/jpeg", data=b"abc")

        self.assertEqual(image.data, b"abc")

    def test_validate_case_ocr_response_accepts_formal_case(self):
        case = validate_case_ocr_response(minimal_ocr_case())

        self.assertEqual(case["paper"]["source_id"], "P01")

    def test_validate_case_ocr_response_rejects_top_level_aliases(self):
        case = minimal_ocr_case()
        case["meter_data"] = {"rows": []}

        with self.assertRaises(OcrContractError):
            validate_case_ocr_response(case)

    def test_validate_case_ocr_response_rejects_paper_rows_alias(self):
        case = minimal_ocr_case()
        case["paper"]["rows"] = []

        with self.assertRaises(OcrContractError):
            validate_case_ocr_response(case)

    def test_validate_case_ocr_response_rejects_semantic_cell_id(self):
        case = minimal_ocr_case()
        case["paper"]["cells"] = {"01_MI": {"raw": "2400", "value": 2400}}

        with self.assertRaises(ValueError):
            validate_case_ocr_response(case)

    def test_validate_case_ocr_response_requires_meter_evidence(self):
        case = minimal_ocr_case()
        case["evidences"] = []

        with self.assertRaises(OcrContractError):
            validate_case_ocr_response(case)


if __name__ == "__main__":
    unittest.main()
