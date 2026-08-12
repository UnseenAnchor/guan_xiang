# -*- coding: utf-8 -*-
import json
import pathlib
import tempfile
import unittest

from bazi.llm_explainer import ExplanationError, chart_for_explanation, explain_chart


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


class LlmExplainerTests(unittest.TestCase):
    def chart(self):
        pillar = {
            "干支": "甲子", "十神(天干)": "比肩", "藏干": ["癸"],
            "十神(藏干)": ["正印"], "纳音": "海中金", "空亡": ["戌", "亥"],
            "长生": "沐浴",
        }
        return {
            "输入": {"性别": "男", "公历": "1990年5月15日 10:30"},
            "出生地": {"名称": "隐私地点", "经度": 120.0, "纬度": 30.0},
            "生肖": "马", "日主": "甲", "四柱": {name: pillar for name in "年月日时"},
            "胎元": "甲子", "命宫": "乙丑", "身宫": "丙寅", "刑冲合会": [],
            "神煞": [], "大运": [{"序": 1, "干支": "乙丑"}], "流年": [],
            "运年断语": {}, "实验推演": {"status": "experimental"},
            "分析": [["日主性格", "古籍正文"]],
        }

    def write_config(self, folder, api_key="test-key"):
        path = pathlib.Path(folder) / "config.json"
        path.write_text(json.dumps({"deepseek": {"api_key": api_key}}), encoding="utf-8")
        return path

    def test_missing_local_config_has_a_safe_message(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ExplanationError, "尚未配置"):
                explain_chart(self.chart(), pathlib.Path(folder) / "missing.json")

    def test_private_birth_fields_are_not_sent_to_the_model(self):
        facts = chart_for_explanation(self.chart())
        serialized = json.dumps(facts, ensure_ascii=False)
        self.assertNotIn("1990年5月15日", serialized)
        self.assertNotIn("隐私地点", serialized)
        self.assertNotIn("120.0", serialized)
        self.assertEqual(facts["四柱"]["日"]["干支"], "甲子")

    def test_official_chat_endpoint_and_model_are_used(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["authorization"] = request.get_header("Authorization")
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return FakeResponse({"choices": [{"message": {"content": "## 命盘骨架\n讲解正文"}}]})

        with tempfile.TemporaryDirectory() as folder:
            result = explain_chart(self.chart(), self.write_config(folder), opener=opener)

        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(captured["authorization"], "Bearer test-key")
        self.assertEqual(captured["body"]["model"], "deepseek-chat")
        self.assertEqual(result["provider"], "DeepSeek")
        self.assertIn("命盘骨架", result["content"])


if __name__ == "__main__":
    unittest.main()
