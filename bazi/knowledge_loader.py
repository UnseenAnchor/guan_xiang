# -*- coding: utf-8 -*-
"""Load previously dormant knowledge assets and derive deterministic chart matches."""

from __future__ import annotations

import json
import os
from functools import lru_cache


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_ROOT = os.path.join(ROOT, "knowledge")


@lru_cache(maxsize=1)
def load_knowledge():
    with open(os.path.join(KNOWLEDGE_ROOT, "duanyu_structured.json"), encoding="gbk") as file:
        structured = json.load(file)
    with open(os.path.join(KNOWLEDGE_ROOT, "cn_classified.json"), encoding="gbk") as file:
        classified = json.load(file)
    with open(os.path.join(KNOWLEDGE_ROOT, "cn_pure.json"), encoding="utf-8") as file:
        pure = json.load(file)
    return {
        "structured": structured,
        "classified": classified,
        "pure": pure,
    }


def _stem_combinations(stems, available):
    pairs = {"甲己合": ("甲", "己"), "乙庚合": ("乙", "庚"), "丙辛合": ("丙", "辛"),
             "丁壬合": ("丁", "壬"), "戊癸合": ("戊", "癸")}
    return [name for name, pair in pairs.items() if name in available and all(stem in stems for stem in pair)]


def chart_knowledge(chart):
    """Return only deterministic matches; unkeyed phrases are never assigned at random."""
    data = load_knowledge()
    structured = data["structured"]
    classified = data["classified"]
    pillars = chart["四柱"]
    stems = [pillars[name]["天干"] for name in ("年", "月", "日", "时")]
    month_key = f"{chart['日主']}日{pillars['月']['地支']}月"
    month_entries = structured.get("月令断语", {})
    combinations = _stem_combinations(stems, structured.get("天干五合断语", {}))

    relation_terms = []
    available_relations = classified.get("地支合/冲/刑/害", [])
    relation_text = " ".join(" ".join(map(str, item)) for item in chart.get("刑冲合会", []))
    for term in available_relations:
        if term in relation_text and term not in relation_terms:
            relation_terms.append(term)

    return {
        "载入统计": {
            "结构分类": len(structured),
            "月令索引": len(month_entries),
            "性格短语": len(structured.get("性格断语", [])),
            "知识分类": len(classified),
            "纯文本短语": len(data["pure"]),
        },
        "月令索引": {"条目": month_key, "命中": month_key in month_entries},
        "天干五合": combinations,
        "关系索引": relation_terms,
        "说明": "结构化文件中的月令、五合条目主要为索引标题；未将无规则归属的性格短语随机附会到个人命盘。",
    }


def enrich_chart(chart):
    chart["知识库"] = chart_knowledge(chart)
    return chart
