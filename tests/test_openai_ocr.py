import unittest
import json
from unittest.mock import patch

from kamichizu.openai_ocr import (
    OcrContractError,
    OcrImage,
    _extract_json_object,
    build_observation_ocr_prompt,
    build_observations_from_images,
    build_source_observation_ocr_prompt,
    combine_source_observations,
    validate_source_observation_ocr_response,
    validate_observation_ocr_response,
)


def minimal_daily_report_source() -> dict[str, object]:
    return {
        "source": {
            "source_type": "daily_report",
            "format_id": "daily_report_default",
            "cells": {
                "01_AD": {"raw": "10:44", "value": "10:44"},
                "01_AF": {"raw": "2,400", "value": 2400},
            },
        },
        "format": {
            "format_id": "daily_report_default",
            "columns": {
                "AD": "time",
                "AF": "mi",
            },
        },
    }


def minimal_meter_receipt_source(amount: int = 2430) -> dict[str, object]:
    return {
        "source": {
            "source_type": "meter_receipt",
            "format_id": "meter_receipt_default",
            "cells": {
                "01_AA": {"raw": "10:44", "value": "10:44"},
                "01_AB": {"raw": f"{amount:,}", "value": amount},
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

        self.assertIn('"source"', prompt)
        self.assertIn('"format"', prompt)
        self.assertIn("view は返さない", prompt)
        self.assertIn("セルIDは物理住所だけ", prompt)
        self.assertIn("別名キーは禁止", prompt)
        self.assertIn("この画像1枚", prompt)
        self.assertIn("資料間の補完、転記、採用判断は禁止", prompt)
        self.assertIn("claims は返さない", prompt)
        self.assertIn("summary は返さない", prompt)
        self.assertIn("adopted や total を返さない", prompt)
        self.assertIn("障割請求、貸切売上、総売上を作らない", prompt)
        self.assertIn("紙日報画像なら、紙日報に実際に見える文字だけ", prompt)
        self.assertIn("メーター明細の金額、時刻、カード名、支払い名を紙日報として返さない", prompt)
        self.assertIn("紙日報の欄位置が不明な金額を、未収欄に寄せてはいけない", prompt)
        self.assertIn('state は "unreadable"', prompt)

    def test_source_prompt_does_not_ask_for_combined_report(self):
        prompt = build_source_observation_ocr_prompt()

        self.assertNotIn('"paper"', prompt)
        self.assertNotIn('"evidences"', prompt)
        self.assertIn("source / format だけを返す", prompt)

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

    def test_validate_source_observation_accepts_one_daily_report_source(self):
        source = validate_source_observation_ocr_response(minimal_daily_report_source())

        self.assertEqual(source["source"]["source_type"], "daily_report")

    def test_validate_source_observation_accepts_one_meter_source(self):
        source = validate_source_observation_ocr_response(minimal_meter_receipt_source())

        self.assertEqual(source["source"]["source_type"], "meter_receipt")

    def test_validate_source_observation_rejects_combined_shape(self):
        with self.assertRaises(OcrContractError):
            validate_source_observation_ocr_response(minimal_ocr_observations())

    def test_validate_source_observation_rejects_source_identity_from_model(self):
        source = minimal_daily_report_source()
        source["source"]["source_id"] = "P99"

        with self.assertRaisesRegex(OcrContractError, r"source\.source_id is not part"):
            validate_source_observation_ocr_response(source)

    def test_combine_source_observations_builds_app_contract(self):
        observations = combine_source_observations(
            [
                minimal_meter_receipt_source(),
                minimal_daily_report_source(),
            ]
        )

        self.assertEqual(observations["paper"]["source_id"], "P01")
        self.assertEqual(observations["paper"]["source_role"], "primary")
        self.assertEqual(observations["evidences"][0]["source"]["source_id"], "E01")
        self.assertEqual(observations["evidences"][0]["source"]["source_role"], "evidence")

    def test_combine_source_observations_requires_exactly_one_daily_report(self):
        with self.assertRaisesRegex(OcrContractError, "exactly one daily_report"):
            combine_source_observations([minimal_meter_receipt_source()])

        with self.assertRaisesRegex(OcrContractError, "exactly one daily_report"):
            combine_source_observations([minimal_daily_report_source(), minimal_daily_report_source()])

    def test_combine_source_observations_requires_evidence(self):
        with self.assertRaisesRegex(OcrContractError, "at least one meter_receipt"):
            combine_source_observations([minimal_daily_report_source()])

    def test_build_observations_from_images_calls_ocr_once_per_image(self):
        images = [
            OcrImage(name="paper.jpg", mime_type="image/jpeg", data=b"paper"),
            OcrImage(name="meter.jpg", mime_type="image/jpeg", data=b"meter"),
        ]

        with patch(
            "kamichizu.openai_ocr._call_openai_for_source_image",
            side_effect=[minimal_daily_report_source(), minimal_meter_receipt_source()],
        ) as call:
            observations = build_observations_from_images(images, api_key="test-key")

        self.assertEqual(call.call_count, 2)
        self.assertEqual(call.call_args_list[0].args[0].name, "paper.jpg")
        self.assertEqual(call.call_args_list[1].args[0].name, "meter.jpg")
        self.assertEqual(observations["paper"]["source_id"], "P01")
        self.assertEqual(observations["evidences"][0]["source"]["source_id"], "E01")

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
