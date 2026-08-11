# -*- coding: utf-8 -*-
import unittest

from web_server_v2 import build_chart_from_request


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

    def test_true_solar_time_rebuilds_date_and_pillars(self):
        chart = build_chart_from_request(self.solar_payload(
            longitude=75,
            use_true_solar_time=True,
        ))
        self.assertEqual(chart["真太阳时"]["校正日期"], "2024-01-01")
        self.assertEqual(chart["真太阳时"]["校正后"], "21:24")
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


if __name__ == "__main__":
    unittest.main()
