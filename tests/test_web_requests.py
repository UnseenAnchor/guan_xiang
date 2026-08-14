# -*- coding: utf-8 -*-
import datetime
import json
import unittest

from web_server import build_almanac_from_date, build_chart_from_request


class WebRequestTests(unittest.TestCase):
    def solar_payload(self, **overrides):
        payload = {
            "calendar": "solar",
            "date": "2024-01-02",
            "time": "00:30",
            "sex": 1,
            "longitude": "",
            "latitude": "",
            "use_true_solar_time": False,
            "timezone": "Asia/Shanghai",
        }
        payload.update(overrides)
        return payload

    def test_standard_time_is_default_and_does_not_silently_correct(self):
        chart = build_chart_from_request(self.solar_payload())
        self.assertIsNone(chart["真太阳时"])
        self.assertEqual(chart["排盘口径"]["模式"], "标准时间")
        self.assertEqual(chart["四柱"]["日"]["干支"], "乙丑")
        self.assertEqual(chart["四柱"]["时"]["干支"], "丙子")

    def test_location_can_be_recorded_without_enabling_correction(self):
        chart = build_chart_from_request(self.solar_payload(
            longitude=75,
            latitude=39,
            location_name="测试地点",
        ))
        self.assertIsNone(chart["真太阳时"])
        self.assertEqual(chart["出生地"]["经度"], 75.0)
        self.assertEqual(chart["四柱"]["日"]["干支"], "乙丑")
        self.assertEqual(chart["四柱"]["时"]["干支"], "丙子")

    def test_true_solar_time_requires_longitude(self):
        with self.assertRaisesRegex(ValueError, "请先选择出生地或填写经度"):
            build_chart_from_request(self.solar_payload(use_true_solar_time=True))

    def test_request_types_are_strictly_validated(self):
        with self.assertRaisesRegex(ValueError, "请求JSON应为对象"):
            build_chart_from_request([])
        with self.assertRaisesRegex(ValueError, "性别参数无效"):
            build_chart_from_request(self.solar_payload(sex=True))
        with self.assertRaisesRegex(ValueError, "真太阳时参数无效"):
            build_chart_from_request(self.solar_payload(use_true_solar_time="false"))
        with self.assertRaisesRegex(ValueError, "闰月参数无效"):
            build_chart_from_request({
                "calendar": "lunar",
                "lunar_year": 1990,
                "lunar_month": 4,
                "lunar_day": 21,
                "lunar_leap": "false",
                "time": "10:30",
                "sex": 1,
            })

    def test_true_solar_time_rebuilds_date_and_pillars(self):
        chart = build_chart_from_request(self.solar_payload(
            longitude=75,
            use_true_solar_time=True,
        ))
        self.assertEqual(chart["真太阳时"]["校正日期"], "2024-01-01")
        self.assertEqual(chart["真太阳时"]["校正后"], "21:27")
        self.assertEqual(chart["四柱"]["日"]["干支"], "甲子")
        self.assertEqual(chart["四柱"]["时"]["干支"], "乙亥")
        self.assertEqual(chart["时间对比"]["变化柱"], ["日", "时"])

    def test_solar_and_lunar_input_for_same_birth_match(self):
        solar = build_chart_from_request({
            "calendar": "solar",
            "date": "1990-05-15",
            "time": "10:30",
            "sex": 1,
        })
        lunar = build_chart_from_request({
            "calendar": "lunar",
            "lunar_year": 1990,
            "lunar_month": 4,
            "lunar_day": 21,
            "lunar_leap": False,
            "time": "10:30",
            "sex": 1,
        })
        self.assertEqual(
            {name: solar["四柱"][name]["干支"] for name in "年月日时"},
            {name: lunar["四柱"][name]["干支"] for name in "年月日时"},
        )

    def test_verified_content_is_available_to_the_web_response(self):
        chart = build_chart_from_request({
            "calendar": "solar",
            "date": "1990-05-15",
            "time": "10:30",
            "sex": 1,
        })
        self.assertEqual(chart["身宫"], "丁亥")
        self.assertEqual(
            [item["年"] for item in chart["流年"]],
            list(range(datetime.date.today().year, datetime.date.today().year + 5)),
        )
        effective_dayun = [item for item in chart["大运"][1:] if item.get("干支")]
        self.assertEqual(len(chart["运年断语"]["三命通会"]), len(effective_dayun))
        titles = [item[0] for item in chart["分析"]]
        self.assertTrue(any(title.startswith("月令断语") for title in titles))
        self.assertTrue(any(title.startswith("日主性格") for title in titles))

    def test_experimental_analysis_has_a_stable_evidence_schema(self):
        chart = build_chart_from_request(self.solar_payload())
        model = chart["实验推演"]
        self.assertEqual(model["schema_version"], 1)
        self.assertEqual(model["status"], "experimental")
        self.assertEqual(
            [item["key"] for item in model["strength"]["dimensions"]],
            ["得令", "得地", "得势"],
        )
        self.assertTrue(all(item["evidence"] for item in model["strength"]["dimensions"]))
        self.assertIn("格局候选", model["pattern"]["wording"])
        self.assertIn("不代表唯一命理结论", model["notice"])
        rules = model["evidence_registry"]["rules"]
        self.assertEqual(len(rules), 3)
        self.assertTrue(all({"rule_id", "source", "version", "school", "confidence"} <= set(rule)
                            for rule in rules))
        self.assertEqual(model["strength"]["dimensions"][0]["rule_ref"], rules[0]["rule_id"])

    def test_almanac_schema_is_complete_and_json_safe(self):
        almanac = build_almanac_from_date("2026-08-12")
        self.assertEqual(almanac["date"]["solar"], "2026-08-12")
        self.assertEqual(almanac["date"]["weekday"], "星期三")
        self.assertEqual(almanac["day_officer"]["name"], "开")
        self.assertEqual(almanac["day_officer"]["classification"], "吉")
        self.assertEqual(almanac["ecliptic"]["type"], "黑道")
        self.assertEqual(almanac["lodge"]["full_name"], "参水猿")
        self.assertEqual(almanac["nine_stars"]["day"]["number"], "九")
        self.assertTrue(almanac["activities"]["recommended"])
        self.assertTrue(almanac["activities"]["avoided"])
        self.assertEqual(len(almanac["directions"]), 5)
        json.dumps(almanac, ensure_ascii=False)

    def test_almanac_rejects_invalid_or_unsupported_dates(self):
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            build_almanac_from_date("2026/08/12")
        with self.assertRaisesRegex(ValueError, "1900—2099"):
            build_almanac_from_date("2100-01-01")


if __name__ == "__main__":
    unittest.main()
