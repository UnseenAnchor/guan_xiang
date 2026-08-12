# -*- coding: utf-8 -*-
"""Stable presentation schemas for browser-facing chart and almanac data."""

from __future__ import annotations

from lunar_python import Solar

from .huangli import get_huangli, get_jianchu_jieshi


EXPERIMENTAL_NOTICE = (
    "以下内容由程序规则推演，用于展示一种分析路径；权重与取法存在流派差异，"
    "不代表唯一命理结论，也不作确定性吉凶判断。"
)


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
        },
        "sources": [
            {"layer": "实验模型", "title": "得令、得地、得势量化规则"},
            {"layer": "古籍参照", "title": "《子平真诠》扶抑、病药与通关取法"},
            {"layer": "古籍参照", "title": "《穷通宝鉴》调候用神表"},
        ],
    }


def _nine_star(star):
    return {
        "name": str(star),
        "number": star.getNumber(),
        "color": star.getColor(),
        "element": star.getWuXing(),
        "position": star.getPosition(),
        "position_desc": star.getPositionDesc(),
    }


def _solar_term(term):
    solar = term.getSolar()
    return {
        "name": term.getName(),
        "datetime": solar.toYmdHms(),
    }


def build_almanac(y, m, d):
    """Build a JSON-safe, versioned almanac payload for one civil date."""
    info = get_huangli(y, m, d)
    solar = Solar.fromYmd(y, m, d)
    lunar = solar.getLunar()
    officer_luck, officer_mnemonic = get_jianchu_jieshi(info["值星"])

    return {
        "schema_version": 1,
        "date": {
            "solar": info["日期"],
            "weekday": f"星期{solar.getWeekInChinese()}",
            "lunar": info["农历"],
            "ganzhi": info["干支"],
            "zodiac": info["生肖"],
            "western_zodiac": info["星座"],
        },
        "solar_terms": {
            "current": info["当前节气"] if info["当前节气"] != "无" else None,
            "previous": _solar_term(lunar.getPrevJieQi()),
            "next": _solar_term(lunar.getNextJieQi()),
        },
        "day_officer": {
            "name": info["值星"],
            "classification": officer_luck,
            "mnemonic": officer_mnemonic,
        },
        "ecliptic": {
            "deity": info["天神"],
            "type": info["黄道黑道"],
            "luck": info["吉凶"],
        },
        "lodge": {
            "name": info["星宿"],
            "full_name": info["星宿全名"],
            "planet": info["七政"],
            "animal": info["动物"],
            "direction": info["方位"],
            "symbol": info["四象"],
        },
        "nine_stars": {
            "year": _nine_star(info["年九星"]),
            "month": _nine_star(info["月九星"]),
            "day": _nine_star(info["日九星"]),
        },
        "activities": {
            "recommended": info["宜"],
            "avoided": info["忌"],
        },
        "spirits": {
            "auspicious": info["吉神"],
            "inauspicious": info["凶煞"],
        },
        "taboos": {
            "pengzu": [info["彭祖日干忌"], info["彭祖日支忌"]],
            "fetus": info["胎神"],
        },
        "directions": [
            {"label": "喜神", "trigram": info["喜神"], "direction": info["喜神方位"]},
            {"label": "福神", "trigram": info["福神"], "direction": info["福神方位"]},
            {"label": "财神", "trigram": info["财神"], "direction": info["财神方位"]},
            {"label": "阳贵", "trigram": info["阳贵"], "direction": info["阳贵方位"]},
            {"label": "阴贵", "trigram": info["阴贵"], "direction": info["阴贵方位"]},
        ],
        "clash": info["冲煞"],
        "sources": [
            {"layer": "历法计算", "title": "lunar-python（寿星天文历）"},
            {"layer": "古籍参照", "title": "《钦定协纪辨方书》"},
            {"layer": "传统历注", "title": "建除十二神与每日宜忌"},
        ],
        "notice": "黄历宜忌属于传统历注展示，仅供民俗文化研究与体验。",
    }
