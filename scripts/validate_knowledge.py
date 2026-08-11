# -*- coding: utf-8 -*-
"""CYBZ_reverse 知识库接入前质量校验。"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ROOT = (REPOSITORY_ROOT / 'bazi-engine'
        if (REPOSITORY_ROOT / 'bazi-engine').is_dir()
        else REPOSITORY_ROOT)
KNOWLEDGE = ROOT / 'knowledge'
GAN = '甲乙丙丁戊己庚辛壬癸'
MONTH_ZHI = '寅卯辰巳午未申酉戌亥子丑'
XIU = set('角亢氐房心尾箕斗牛女虚危室壁奎娄胃昴毕觜参井鬼柳星张翼轸')
ENCODINGS = {
    'clean_long.json': 'gbk', 'clean_short.json': 'gbk',
    'cn_classified.json': 'gbk', 'duanyu_structured.json': 'gbk',
    'knowledge_archive.json': 'gbk',
}
NOISE = re.compile(
    r'document\.|function|varprev|相关词条|热门词条|服务器暂时维护|'
    r'书签添加|@中文百科全书|clientWidth|[\ue000-\uf8ff]', re.I,
)


def load_json(path):
    duplicates = []

    def hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    text = path.read_text(encoding=ENCODINGS.get(path.name, 'utf-8'))
    return json.loads(text, object_pairs_hook=hook), text, duplicates


def main():
    errors = []
    for path in sorted(KNOWLEDGE.glob('*.json')):
        try:
            _, text, duplicates = load_json(path)
        except Exception as exc:
            errors.append(f'{path.name}: 无法解析：{exc}')
            continue
        if duplicates:
            errors.append(f'{path.name}: 重复键 {sorted(set(duplicates))[:10]}')
        if '\ufffd' in text:
            errors.append(f'{path.name}: 包含替换字符 U+FFFD')

    month, _, _ = load_json(KNOWLEDGE / '月令断语_穷通宝鉴_byAppTitle.json')
    expected_month = {f'{gan}日{zhi}月' for gan in GAN for zhi in MONTH_ZHI}
    if set(month) != expected_month:
        errors.append('月令正文未完整覆盖十干×十二月令')
    dirty = sorted(key for key, body in month.items() if NOISE.search(body))
    if dirty:
        errors.append(f'月令正文包含网页噪声或异常字符：{dirty}')
    short = sorted(key for key, body in month.items() if len(body.strip()) < 30)
    if short:
        errors.append(f'月令正文过短：{short}')

    structured, _, _ = load_json(KNOWLEDGE / 'duanyu_structured.json')
    if set(structured.get('月令断语', {})) != expected_month:
        errors.append('APK 月令标题索引与120项标准键不一致')

    personality, _, _ = load_json(KNOWLEDGE / '性格断语_滴天髓.json')
    if set(personality.get('shigan_xingge', {})) != set(GAN):
        errors.append('滴天髓性格正文未完整覆盖十天干')
    if not personality.get('xingqing_zonglun', '').strip():
        errors.append('滴天髓性情总论为空')

    tiaohou, _, _ = load_json(KNOWLEDGE / 'tiaohou_qiongtong.json')
    table = tiaohou.get('表', {})
    if set(table) != set(GAN):
        errors.append('调候表未完整覆盖十天干')
    for gan in GAN:
        if set(table.get(gan, {})) != set(MONTH_ZHI):
            errors.append(f'调候表 {gan} 未完整覆盖十二月令')
        for zhi, value in table.get(gan, {}).items():
            if not value or any(char not in GAN for char in value):
                errors.append(f'调候表 {gan}{zhi} 值非法：{value!r}')

    tree = ast.parse((ROOT / 'bazi' / 'geju.py').read_text(encoding='utf-8'))
    code_table = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == 'TIAOHOU' for target in node.targets
        ):
            code_table = ast.literal_eval(node.value)
            break
    if code_table is None:
        errors.append('geju.py 中找不到 TIAOHOU 常量')
    else:
        mismatch = [(gan, zhi) for gan in GAN for index, zhi in enumerate(MONTH_ZHI)
                    if code_table[gan][index] != table[gan][zhi]]
        if mismatch:
            errors.append(f'调候 JSON 与代码常量不一致：{mismatch}')

    huangli, _, _ = load_json(KNOWLEDGE / '黄历_协纪辨方书.json')
    rows = huangli.get('二十八宿表', [])
    if len(rows) != 28 or {row.get('宿') for row in rows} != XIU:
        errors.append('二十八宿表不是28宿全集')
    bad_names = [(row.get('宿'), row.get('全名')) for row in rows
                 if row.get('全名') != row.get('宿', '') + row.get('七政', '') + row.get('动物', '')]
    if bad_names:
        errors.append(f'二十八宿全名不完整：{bad_names}')

    ny, _, _ = load_json(KNOWLEDGE / 'ny.json')
    for key, count in {'天干': 10, '地支': 12, '纳音': 60, '十神': 100, '十二长生': 120}.items():
        if len(ny.get(key, {})) != count:
            errors.append(f'ny.json {key} 数量异常')
    ser, _, _ = load_json(KNOWLEDGE / 'serjson.json')
    for key, count in {'shengsha': 52, 'ssxx': 167, 'swk': 120}.items():
        if len(ser.get(key, {})) != count:
            errors.append(f'serjson.json {key} 数量异常')

    if errors:
        for error in errors:
            print(f'FAIL: {error}')
        raise SystemExit(1)
    print('PASS: 全部 JSON 可解析且无重复键/替换字符')
    print('PASS: 月令正文 120 项完整、干净并与 APK 标题索引一致')
    print('PASS: 十干性格、性情总论与调候 120 项结构完整')
    print('PASS: 调候 JSON 与 geju.py 代码常量逐项一致')
    print('PASS: 二十八宿 28 项全名完整')
    print('PASS: 基础表与 serjson 核心计数正确')


if __name__ == '__main__':
    main()
