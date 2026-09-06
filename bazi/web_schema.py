# -*- coding: utf-8 -*-
"""Stable presentation schemas for browser-facing chart data."""

from __future__ import annotations


EXPERIMENTAL_NOTICE = (
    "以下内容由程序规则推演，用于展示一种分析路径；权重与取法存在流派差异，"
    "不代表唯一命理结论，也不作确定性吉凶判断。"
)

EXPERIMENTAL_RULES = [
    {
        "rule_id": "strength.de-ling-de-di-de-shi",
        "source": "bazi.geju.strength_analysis",
        "version": 1,
        "school": "子平法（实验量化）",
        "confidence": "experimental",
        "title": "得令、得地、得势量化规则",
    },
    {
        "rule_id": "pattern.month-command",
        "source": "bazi.geju.judge_geju",
        "version": 1,
        "school": "子平法（月令取格）",
        "confidence": "school-dependent",
        "title": "月令取格规则",
    },
    {
        "rule_id": "guidance.fuyi-bingyao-tiaohou",
        "source": "bazi.geju.pick_yongshen",
        "version": 1,
        "school": "子平法（扶抑、病药、调候）",
        "confidence": "school-dependent",
        "title": "取用与调候规则",
    },
]


def build_experimental_analysis(chart):
    """Normalize the engine's mixed experimental fields for the web client."""
    strength = chart.get("旺衰") or {}
    pattern = chart.get("格局") or ()
    guidance = chart.get("用神") or {}
    details = strength.get("细节") or []
    scores = strength.get("得分项") or {}
    dimension_labels = ("得令", "得地", "得势")

    dimensions = []
    for index, label in enumerate(dimension_labels):
        dimensions.append({
            "key": label,
            "score": scores.get(label, 0),
            "evidence": details[index] if index < len(details) else "暂无对应证据",
            "rule_ref": "strength.de-ling-de-di-de-shi",
        })

    return {
        "schema_version": 1,
        "status": "experimental",
        "notice": EXPERIMENTAL_NOTICE,
        "strength": {
            "label": strength.get("身强弱", "未判定"),
            "score": strength.get("评分", 0),
            "month_state": strength.get("月令状态", "—"),
            "axis": {"min": -2, "max": 9},
            "dimensions": dimensions,
        },
        "pattern": {
            "label": pattern[0] if len(pattern) > 0 else "未命中",
            "candidate": pattern[1] if len(pattern) > 1 else "未命中",
            "evidence": pattern[2] if len(pattern) > 2 else "暂无对应证据",
            "wording": "程序规则命中 / 格局候选",
            "rule_ref": "pattern.month-command",
        },
        "guidance": {
            "method": guidance.get("方法", "未判定"),
            "focus_elements": guidance.get("用神", []),
            "balancing_elements": guidance.get("忌神", []),
            "climate_stems": guidance.get("调候用神", []),
            "illness_elements": guidance.get("病", []),
            "remedy_elements": guidance.get("药", []),
            "bridge_element": guidance.get("通关"),
            "wording": {
                "focus": "模型建议关注",
                "balance": "模型提示制衡",
            },
            "rule_ref": "guidance.fuyi-bingyao-tiaohou",
        },
        "evidence_registry": {"rules": EXPERIMENTAL_RULES},
        "sources": [
            {"layer": "实验模型", "title": "得令、得地、得势量化规则"},
            {"layer": "古籍参照", "title": "《子平真诠》扶抑、病药与通关取法"},
            {"layer": "古籍参照", "title": "《穷通宝鉴》调候用神表"},
        ],
    }


