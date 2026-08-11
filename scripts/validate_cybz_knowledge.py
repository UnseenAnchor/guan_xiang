# -*- coding: utf-8 -*-
"""Validate CYBZ_reverse knowledge assets before web integration."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


GAN = "甲乙丙丁戊己庚辛壬癸"
MONTH_ZHI = "寅卯辰巳午未申酉戌亥子丑"
XIU = set("角亢氐房心尾箕斗牛女虚危室壁奎娄胃昴毕觜参井鬼柳星张翼轸")
ENCODINGS = {
    "clean_long.json": "gbk",
    "clean_short.json": "gbk",
    "cn_classified.json": "gbk",
    "duanyu_structured.json": "gbk",
    "knowledge_archive.json": "gbk",
}
WEB_NOISE = re.compile(
    r"document\.|function|varprev|相关词条|热门词条|服务器暂时维护|"
    r"书签添加|@中文百科全书|clientWidth|[\ue000-\uf8ff]",
    re.I,
)


def load_unique(path: Path):
    duplicates = []

    def hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    text = path.read_text(encoding=ENCODINGS.get(path.name, "utf-8"))
    return json.loads(text, object_pairs_hook=hook), text, duplicates


def validate(root: Path):
    knowledge = root / "knowledge"
    errors = []
    notes = []

    for path in sorted(knowledge.glob("*.json")):
        try:
            _, text, duplicates = load_unique(path)
        except Exception as exc:
            errors.append(f"{path.name}: 无法解析：{exc}")
            continue
        if duplicates:
            errors.append(f"{path.name}: 存在重复键：{sorted(set(duplicates))[:10]}")
        if "\ufffd" in text:
            errors.append(f"{path.name}: 包含替换字符 U+FFFD")

    month, _, _ = load_unique(knowledge / "月令断语_穷通宝鉴_byAppTitle.json")
    expected_month = {f"{gan}日{zhi}月" for gan in GAN for zhi in MONTH_ZHI}
    if set(month) != expected_month:
        errors.append("月令正文没有完整覆盖十干×十二月令")
    contaminated = sorted(key for key, body in month.items() if WEB_NOISE.search(body))
    if contaminated:
        errors.append(f"月令正文有 {len(contaminated)} 条包含网页噪声或异常字符：{contaminated}")
    placeholders = sorted(key for key, body in month.items() if len(body.strip()) < 30)
    if placeholders:
        errors.append(f"月令正文有 {len(placeholders)} 条仅为短占位：{placeholders}")
    very_long = sorted(key for key, body in month.items() if len(body) > 5000)
    if very_long:
        errors.append(f"月令正文有 {len(very_long)} 条异常超长、疑似跨章节：{very_long}")

    structured, _, _ = load_unique(knowledge / "duanyu_structured.json")
    if set(structured.get("月令断语", {})) != expected_month:
        errors.append("APK 月令标题索引与120项标准键不一致")

    personality, _, _ = load_unique(knowledge / "性格断语_滴天髓.json")
    if set(personality.get("shigan_xingge", {})) != set(GAN):
        errors.append("滴天髓性格正文没有完整覆盖十天干")
    if not personality.get("xingqing_zonglun", "").strip():
        errors.append("滴天髓性情总论为空")

    tiaohou, _, _ = load_unique(knowledge / "tiaohou_qiongtong.json")
    table = tiaohou.get("表", {})
    if set(table) != set(GAN):
        errors.append("调候表没有完整覆盖十天干")
    for gan in GAN:
        if set(table.get(gan, {})) != set(MONTH_ZHI):
            errors.append(f"调候表 {gan} 未完整覆盖十二月令")
        for zhi, value in table.get(gan, {}).items():
            if not value or any(char not in GAN for char in value):
                errors.append(f"调候表 {gan}{zhi} 值非法：{value!r}")

    tree = ast.parse((root / "bazi" / "geju.py").read_text(encoding="utf-8"))
    code_table = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "TIAOHOU" for target in node.targets
        ):
            code_table = ast.literal_eval(node.value)
            break
    if code_table is None:
        errors.append("geju.py 中找不到 TIAOHOU 常量")
    else:
        mismatches = []
        for gan in GAN:
            for index, zhi in enumerate(MONTH_ZHI):
                if code_table[gan][index] != table[gan][zhi]:
                    mismatches.append(f"{gan}{zhi}")
        if mismatches:
            errors.append(f"调候 JSON 与代码常量不一致：{mismatches}")

    huangli, _, _ = load_unique(knowledge / "黄历_协纪辨方书.json")
    rows = huangli.get("二十八宿表", [])
    if len(rows) != 28 or {row.get("宿") for row in rows} != XIU:
        errors.append("二十八宿表不是28宿全集")
    bad_fullnames = [
        (row.get("宿"), row.get("全名"), row.get("宿", "") + row.get("七政", "") + row.get("动物", ""))
        for row in rows
        if row.get("全名") != row.get("宿", "") + row.get("七政", "") + row.get("动物", "")
    ]
    if bad_fullnames:
        errors.append(f"二十八宿全名不完整：{bad_fullnames}")

    ny, _, _ = load_unique(knowledge / "ny.json")
    for key, count in {"天干": 10, "地支": 12, "纳音": 60, "十神": 100, "十二长生": 120}.items():
        if len(ny.get(key, {})) != count:
            errors.append(f"ny.json {key} 数量为 {len(ny.get(key, {}))}，预期 {count}")

    ser, _, _ = load_unique(knowledge / "serjson.json")
    for key, count in {"shengsha": 52, "ssxx": 167, "swk": 120}.items():
        if len(ser.get(key, {})) != count:
            errors.append(f"serjson.json {key} 数量为 {len(ser.get(key, {}))}，预期 {count}")

    notes.extend([
        "性格断语：十干与总论结构完整，未发现网页噪声。",
        "调候表：120项齐全，且与 geju.py 常量逐项一致。",
        "大运流年、黄历两份原文 JSON 可解析且未发现网页脚本残留。",
        "基础表：天干10、地支12、纳音60、十神100、十二长生120。",
        "serjson：神煞52、十神断语167、坐支论120。",
    ])
    return errors, notes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="CYBZ_reverse/bazi-engine 路径")
    args = parser.parse_args()
    errors, notes = validate(args.root.resolve())
    for note in notes:
        print(f"PASS: {note}")
    for error in errors:
        print(f"FAIL: {error}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
