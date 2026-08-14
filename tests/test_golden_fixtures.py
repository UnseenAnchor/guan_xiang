# -*- coding: utf-8 -*-
import datetime as dt
import json
import pathlib
import unittest

from bazi.engine import build_chart


FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def build_fixture_chart(case):
    date = dt.date.fromisoformat(case["date"])
    time = dt.time.fromisoformat(case["time"])
    kwargs = {"longitude": case["longitude"]} if "longitude" in case else {}
    return build_chart(date.year, date.month, date.day, time.hour, time.minute, sex=1, **kwargs)


def pillar_string(chart):
    return "".join(chart["四柱"][name]["干支"] for name in "年月日时")


class GoldenFixtureTests(unittest.TestCase):
    def test_celebrity_fixture_is_sourced_and_matches_engine(self):
        data = load_fixture("celebrity_charts.json")
        cases = data["cases"]
        self.assertEqual(len(cases), 60)
        self.assertEqual({case["rating"] for case in cases}, {"A", "AA"})
        self.assertEqual(len({case["source"] for case in cases}), 60)
        for case in cases:
            with self.subTest(name=case["name"]):
                self.assertTrue(case["source"].startswith("https://www.astro.com/astro-databank/"))
                self.assertEqual(pillar_string(build_fixture_chart(case)), case["pillars"])

    def test_boundary_fixture_matches_engine_and_corrected_time(self):
        cases = load_fixture("boundary_charts.json")["cases"]
        self.assertEqual(len(cases), 10)
        for case in cases:
            with self.subTest(case=case["id"]):
                chart = build_fixture_chart(case)
                self.assertEqual(pillar_string(chart), case["pillars"])
                if "corrected_date" in case:
                    self.assertEqual(chart["真太阳时"]["校正日期"], case["corrected_date"])
                    self.assertEqual(chart["真太阳时"]["校正后"], case["corrected_time"])


if __name__ == "__main__":
    unittest.main()
