# -*- coding: utf-8 -*-
"""生成 Go 客户端排盘的黄金样本（交叉验证用，不做运行时依赖）。

用法（仓库根目录）：
    python desktop/tools/gen_golden.py

数据取自仓库既有 fixtures（60 例名人 + 10 例边界）与额外补充用例，全部由
Python 引擎 bazi.engine.build_chart 计算，Go 端 parity_test.go 逐项比对。
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bazi.engine import build_chart  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
OUT = ROOT / "desktop" / "testdata" / "golden_charts.json"

EXTRA_CASES = [
    {"name": "solar-1900-01-01", "date": "1900-01-01", "time": "00:00", "sex": 1},
    {"name": "solar-2099-12-31", "date": "2099-12-31", "time": "23:59", "sex": 0},
    {"name": "late-zi-2024-02-10", "date": "2024-02-10", "time": "23:30", "sex": 1},
    {"name": "late-zi-1987-06-05", "date": "1987-06-05", "time": "23:05", "sex": 0},
    {"name": "true-solar-116.4", "date": "1990-05-15", "time": "10:30", "sex": 1, "longitude": 116.4},
    {"name": "true-solar-121.47", "date": "2001-11-07", "time": "06:12", "sex": 0, "longitude": 121.47},
    {"name": "true-solar-75.99", "date": "1976-09-09", "time": "00:10", "sex": 1, "longitude": 75.99},
    {"name": "solar-1978-11-12", "date": "1978-11-12", "time": "12:00", "sex": 1},
    {"name": "solar-1955-03-21", "date": "1955-03-21", "time": "04:45", "sex": 0},
    {"name": "solar-2010-08-08", "date": "2010-08-08", "time": "18:30", "sex": 1},
]


def load_cases():
    cases = []
    celebrity = json.loads((FIXTURES / "celebrity_charts.json").read_text(encoding="utf-8"))
    for case in celebrity["cases"]:
        cases.append({
            "name": case["name"],
            "date": case["date"],
            "time": case["time"],
            "sex": 1,
            "expected_pillars": case["pillars"],
        })
    boundary = json.loads((FIXTURES / "boundary_charts.json").read_text(encoding="utf-8"))
    for case in boundary["cases"]:
        item = {
            "name": case["id"],
            "date": case["date"],
            "time": case["time"],
            "sex": case.get("sex", 1),
            "expected_pillars": case["pillars"],
        }
        if "longitude" in case:
            item["longitude"] = case["longitude"]
        if "corrected_time" in case:
            item["expected_corrected_time"] = case["corrected_time"]
        if "corrected_date" in case:
            item["expected_corrected_date"] = case["corrected_date"]
        cases.append(item)
    for case in EXTRA_CASES:
        cases.append(dict(case))
    return cases


def build_case(case):
    date = case["date"].split("-")
    hour, minute = case["time"].split(":")
    kwargs = {"longitude": case["longitude"]} if "longitude" in case else {}
    chart = build_chart(
        int(date[0]), int(date[1]), int(date[2]),
        int(hour), int(minute), sex=case["sex"], **kwargs
    )
    true_solar = None
    if chart.get("真太阳时"):
        ts = chart["真太阳时"]
        true_solar = {
            "original": ts["原时间"],
            "correct_date": ts["校正日期"],
            "corrected": ts["校正后"],
            "total_minute": ts["总校正分"],
            "lon_diff": ts["经度差"],
            "equation": ts["均时差"],
        }
    return {
        "name": case["name"],
        "input": {
            "date": case["date"],
            "time": case["time"],
            "sex": case["sex"],
            "longitude": case.get("longitude"),
        },
        "expected_pillars": case.get("expected_pillars"),
        "expected_corrected_time": case.get("expected_corrected_time"),
        "expected_corrected_date": case.get("expected_corrected_date"),
        "lunar": chart["农历"],
        "shengxiao": chart["生肖"],
        "day_master": chart["日主"],
        "pillars": [
            {
                "name": name,
                "ganzhi": chart["四柱"][name]["干支"],
                "canggan": chart["四柱"][name]["藏干"],
                "shishen_gan": chart["四柱"][name]["十神(天干)"],
                "shishen_canggan": chart["四柱"][name]["十神(藏干)"],
                "nayin": chart["四柱"][name]["纳音"],
                "kongwang": chart["四柱"][name]["空亡"],
                "changsheng": chart["四柱"][name]["自坐长生"],
                "dishi": chart["四柱"][name]["日主地势"],
            }
            for name in ("年", "月", "日", "时")
        ],
        "true_solar": true_solar,
        "strength": {
            "score": chart["旺衰"]["评分"],
            "level": chart["旺衰"]["身强弱"],
            "month_state": chart["旺衰"]["月令状态"],
        },
        "geju": {
            "name": chart["格局"][0],
            "kind": chart["格局"][1],
            "note": chart["格局"][2],
        },
        "yongshen": {
            "use": chart["用神"]["用神"],
            "avoid": chart["用神"]["忌神"],
            "tiaohou": chart["用神"]["调候干"],
            "method": chart["用神"]["方法"],
            "bridge": chart["用神"]["通关"],
        },
        "shensha": [[item[0], item[1]] for item in chart["神煞"]],
        "relations": [list(item) for item in chart["刑冲合会"]],
        "dayun": [
            [item["序"], item["干支"], item["起年"], item["终年"], item["年龄"]]
            for item in chart["大运"]
        ],
        "dayun_start": [
            chart["起运详情"]["年"], chart["起运详情"]["月"],
            chart["起运详情"]["日"], chart["起运详情"]["时"],
            chart["起运详情"]["交运时间"],
        ],
        "liunian": [[item["年"], item["干支"]] for item in chart["流年"]],
        "notes": [item[0] for item in chart["分析"]],
        "taiyuan": chart["胎元"],
        "minggong": chart["命宫"],
        "shengong": chart["身宫"],
    }


def main():
    cases = load_cases()
    payload = {
        "schema_version": 1,
        "generator": "desktop/tools/gen_golden.py (Python bazi.engine.build_chart)",
        "case_count": len(cases),
        "cases": [build_case(case) for case in cases],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT} ({len(cases)} cases, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
