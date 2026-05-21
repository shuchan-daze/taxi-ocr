import json
import unittest

from kamichizu.openai_ocr import OcrImage, _extract_json_object, build_case_ocr_prompt


class OpenAiOcrTest(unittest.TestCase):
    def test_prompt_requires_single_formal_case_contract(self):
        prompt = build_case_ocr_prompt()

        self.assertIn('"paper"', prompt)
        self.assertIn('"evidences"', prompt)
        self.assertIn('"view"', prompt)
        self.assertIn("セルIDは物理住所だけ", prompt)
        self.assertIn("別名キーは禁止", prompt)

    def test_extract_json_object_accepts_json_object(self):
        data = _extract_json_object(json.dumps({"paper": {}, "evidences": []}))

        self.assertEqual(data["paper"], {})

    def test_extract_json_object_rejects_non_object(self):
        with self.assertRaises(ValueError):
            _extract_json_object("[]")

    def test_ocr_image_keeps_uploaded_bytes(self):
        image = OcrImage(name="a.jpg", mime_type="image/jpeg", data=b"abc")

        self.assertEqual(image.data, b"abc")


if __name__ == "__main__":
    unittest.main()
