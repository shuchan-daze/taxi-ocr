import unittest
import json

from kamichizu.openai_ocr import (
    OcrContractError,
    OcrImage,
    _extract_json_object,
    build_observation_ocr_prompt,
    validate_observation_ocr_response,
)


def minimal_ocr_observations() -> dict[str, object]:
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
    }


class OpenAiOcrTest(unittest.TestCase):
    def test_prompt_requires_observation_contract(self):
        prompt = build_observation_ocr_prompt()

        self.assertIn('"paper"', prompt)
        self.assertIn('"evidences"', prompt)
        self.assertIn("view は返さない", prompt)
        self.assertIn("セルIDは物理住所だけ", prompt)
        self.assertIn("別名キーは禁止", prompt)
        self.assertIn("写真のアップロード順に依存しない", prompt)
        self.assertIn("自動判別", prompt)
        self.assertIn("claims は返さない", prompt)
        self.assertIn("summary は返さない", prompt)
        self.assertIn("adopted や total を返さない", prompt)
        self.assertIn("障割請求、貸切売上、総売上を作らない", prompt)

    def test_extract_json_object_accepts_json_object(self):
        data = _extract_json_object(json.dumps({"paper": {}, "evidences": []}))

        self.assertEqual(data["paper"], {})

    def test_extract_json_object_rejects_non_object(self):
        with self.assertRaises(ValueError):
            _extract_json_object("[]")

    def test_ocr_image_keeps_uploaded_bytes(self):
        image = OcrImage(name="a.jpg", mime_type="image/jpeg", data=b"abc")

        self.assertEqual(image.data, b"abc")

    def test_validate_observation_ocr_response_accepts_observations(self):
        observations = validate_observation_ocr_response(minimal_ocr_observations())

        self.assertEqual(observations["paper"]["source_id"], "P01")

    def test_validate_observation_ocr_response_rejects_top_level_aliases(self):
        observations = minimal_ocr_observations()
        observations["meter_data"] = {"rows": []}

        with self.assertRaises(OcrContractError):
            validate_observation_ocr_response(observations)

    def test_validate_observation_ocr_response_rejects_paper_rows_alias(self):
        observations = minimal_ocr_observations()
        observations["paper"]["rows"] = []

        with self.assertRaises(OcrContractError):
            validate_observation_ocr_response(observations)

    def test_validate_observation_ocr_response_rejects_semantic_cell_id(self):
        observations = minimal_ocr_observations()
        observations["paper"]["cells"] = {"01_MI": {"raw": "2400", "value": 2400}}

        with self.assertRaises(ValueError):
            validate_observation_ocr_response(observations)

    def test_validate_observation_ocr_response_requires_evidence(self):
        observations = minimal_ocr_observations()
        observations["evidences"] = []

        with self.assertRaises(OcrContractError):
            validate_observation_ocr_response(observations)

    def test_validate_observation_ocr_response_rejects_claims(self):
        observations = minimal_ocr_observations()
        observations["claims"] = [
            {
                "type": "charter_sale",
                "target_global_cell_id": "P01:06_AE",
                "claim_amount": 16400,
                "payment_kind": "gen",
                "evidence": [
                    {
                        "paper_cell": "P01:06_AE",
                        "evidence_cell": "P01:06_AG",
                        "reason": "charter_from_paper_memo",
                    }
                ],
            }
        ]

        with self.assertRaisesRegex(OcrContractError, r"ocr_response\.claims is not part"):
            validate_observation_ocr_response(observations)

    def test_validate_observation_ocr_response_rejects_view_from_ocr(self):
        observations = minimal_ocr_observations()
        observations["view"] = {"view_id": "daily_report_table", "columns": []}

        with self.assertRaisesRegex(OcrContractError, r"ocr_response\.view is not part"):
            validate_observation_ocr_response(observations)


if __name__ == "__main__":
    unittest.main()
