# -*- coding: utf-8 -*-
"""月令断语: 《穷通宝鉴》十干×十二月 120 条 (按 app 标题格式: 甲日寅月)"""
import json, os

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = None

def _load():
    global _DATA
    if _DATA is None:
        with open(os.path.join(_HERE, '..', 'knowledge', '月令断语_穷通宝鉴_byAppTitle.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA

def yueling_duanyu(rigan, yuezhi):
    """返回 (标题, 正文)。rigan=日干, yuezhi=月支 (如 '甲','寅')"""
    d = _load()
    key = f'{rigan}日{yuezhi}月'
    if key in d:
        return key, d[key]
    return key, None

def all_titles():
    return list(_load().keys())

if __name__ == '__main__':
    for g, z in [('甲', '寅'), ('丙', '午'), ('庚', '申'), ('癸', '丑')]:
        t, body = yueling_duanyu(g, z)
        print(f'=== {t} ===')
        print((body or '缺')[:100])
