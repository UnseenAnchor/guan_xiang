# -*- coding: utf-8 -*-
"""Compare checked-in golden charts with the production engine and sxtwl oracle."""

import datetime as dt
import json
from pathlib import Path
import sys

import sxtwl

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from bazi.engine import build_chart  # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures"
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


def _load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _parts(case):
    date = dt.date.fromisoformat(case["date"])
    time = dt.time.fromisoformat(case["time"])
    return date.year, date.month, date.day, time.hour, time.minute


def _engine_pillars(case):
    y, m, d, hour, minute = _parts(case)
    kwargs = {"longitude": case["longitude"]} if "longitude" in case else {}
    chart = build_chart(y, m, d, hour, minute, sex=1, **kwargs)
    pillars = "".join(chart["四柱"][name]["干支"] for name in "年月日时")
    return pillars, chart


def _gz(value):
    return GAN[value.tg] + ZHI[value.dz]


def _sxtwl_pillars(case):
    y, m, d, hour, _ = _parts(case)
    day = sxtwl.fromSolar(y, m, d)
    day_gz = day.after(1).getDayGZ() if hour >= 23 else day.getDayGZ()
    return "".join((
        _gz(day.getYearGZ(False)),
        _gz(day.getMonthGZ()),
        _gz(day_gz),
        _gz(day.getHourGZ(hour, True)),
    ))


def main():
    failures = []
    celebrities = _load("celebrity_charts.json")["cases"]
    for case in celebrities:
        expected = case["pillars"]
        engine, _ = _engine_pillars(case)
        oracle = _sxtwl_pillars(case)
        if engine != expected or oracle != expected:
            failures.append(f"{case['name']}: golden={expected} engine={engine} sxtwl={oracle}")

    boundaries = _load("boundary_charts.json")["cases"]
    for case in boundaries:
        engine, chart = _engine_pillars(case)
        if engine != case["pillars"]:
            failures.append(f"{case['id']}: golden={case['pillars']} engine={engine}")
        if "corrected_date" in case:
            solar = chart["真太阳时"] or {}
            actual = (solar.get("校正日期"), solar.get("校正后"))
            expected = (case["corrected_date"], case["corrected_time"])
            if actual != expected:
                failures.append(f"{case['id']}: corrected={actual} expected={expected}")

    if failures:
        print("FAIL: golden/oracle comparison found differences")
        for failure in failures:
            print(" -", failure)
        raise SystemExit(1)

    print(f"PASS: {len(celebrities)} celebrity charts / {len(celebrities) * 4} pillars match golden and sxtwl 2.0.7.")
    print(f"PASS: {len(boundaries)} solar-term, late-zi and true-solar boundary fixtures match.")


if __name__ == "__main__":
    main()
