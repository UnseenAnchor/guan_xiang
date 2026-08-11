# -*- coding: utf-8 -*-
"""从本地《穷通宝鉴》EPUB 正文重建干净的十干×十二月令断语。"""

from __future__ import annotations

import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


GAN = '甲乙丙丁戊己庚辛壬癸'
MONTH_ZHI = '寅卯辰巳午未申酉戌亥子丑'
SEASON_MONTHS = {'三春': (1, 2, 3), '三夏': (4, 5, 6),
                 '三秋': (7, 8, 9), '三冬': (10, 11, 12)}
SEASON_GENERAL_PREFIX = {
    '三春': ('三春', '春月之'), '三夏': ('三夏', '夏月之'),
    '三秋': ('三秋', '秋月之'), '三冬': ('三冬', '冬月之'),
}
MONTHS = {
    '正': (1,), '二': (2,), '三': (3,), '四': (4,), '五': (5,), '六': (6,),
    '七': (7,), '八': (8,), '九': (9,), '十': (10,), '十一': (11,),
    '十二': (12,), '冬': (11,), '腊': (12,), '正二': (1, 2),
    '五六': (5, 6), '八九': (8, 9), '十一二': (11, 12),
}
MONTH_PATTERN = re.compile(
    r'^(正二|五六|八九|十一二|十二|十一|正|二|三|四|五|六|七|八|九|十|冬|腊)月'
    r'(?:之)?([甲乙丙丁戊己庚辛壬癸])?'
)
PUA_REPLACEMENTS = {'\ue03d': '冲', '\ue10f': '克', '\ue4df': '明'}


def local_name(tag):
    return tag.rsplit('}', 1)[-1]


def clean_text(element):
    text = html.unescape(''.join(element.itertext()))
    text = re.sub(r'\s+', '', text)
    for source, target in PUA_REPLACEMENTS.items():
        text = text.replace(source, target)
    return text


def direct_heading(section, level):
    for child in section:
        if local_name(child.tag) == level:
            return clean_text(child)
    return ''


def month_blocks(section, stem, season):
    blocks = {}
    general = []
    current = None
    for element in section.iter():
        if local_name(element.tag) != 'p':
            continue
        text = clean_text(element)
        if not text:
            continue
        if text.startswith(SEASON_GENERAL_PREFIX[season]):
            current = None
            general.append(text)
            continue
        match = MONTH_PATTERN.match(text)
        if match:
            stated_stem = match.group(2)
            if stated_stem and stated_stem != stem:
                current = None
                continue
            current = MONTHS[match.group(1)]
            for month in current:
                blocks.setdefault(month, []).append(text)
        elif current:
            for month in current:
                blocks[month].append(text)
        else:
            general.append(text)

    for month in SEASON_MONTHS[season]:
        if month not in blocks and general:
            blocks[month] = ['[季节合述]' + ''.join(general)]
    return {month: '\n\n'.join(parts) for month, parts in blocks.items()}


def rebuild(source):
    root = ET.parse(source).getroot()
    result = {}
    for section in root.iter():
        h2 = direct_heading(section, 'h2')
        match = re.fullmatch(r'论([甲乙丙丁戊己庚辛壬癸]).*', h2)
        if not match:
            continue
        stem = match.group(1)
        for season_section in section:
            if local_name(season_section.tag) != 'section':
                continue
            h3 = direct_heading(season_section, 'h3')
            season_match = re.match(r'(三春|三夏|三秋|三冬)', h3)
            if not season_match:
                continue
            season = season_match.group(1)
            for month, body in month_blocks(season_section, stem, season).items():
                result[(stem, month)] = body

    missing = [(stem, month) for stem in GAN for month in range(1, 13)
               if (stem, month) not in result]
    if missing:
        raise ValueError(f'原始 EPUB 仍缺少月令：{missing}')

    output = {}
    for stem in GAN:
        for month, zhi in enumerate(MONTH_ZHI, start=1):
            output[f'{stem}日{zhi}月'] = result[(stem, month)]
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path, help='EPUB 解包后的正文 XHTML')
    parser.add_argument('output', type=Path, help='输出 JSON')
    args = parser.parse_args()
    data = rebuild(args.source)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'已从原始 EPUB 重建 {len(data)} 条月令正文：{args.output}')


if __name__ == '__main__':
    main()
