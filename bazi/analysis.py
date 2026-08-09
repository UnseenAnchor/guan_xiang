# -*- coding: utf-8 -*-
"""
analysis.py — 断语分析
数据包含十神断语与日柱坐支论。
"""
import json, os, re
from .ganzhi import shishen, zhi_canggan

_HERE = os.path.dirname(os.path.abspath(__file__))
SER = json.load(open(os.path.join(_HERE, '..', 'knowledge', 'serjson.json'), encoding='utf-8'))
SSXX = SER['ssxx']      # 十神断语
SWK = SER['swk']        # 日柱坐支论 (key: 日干+日支, value: '长生#断语')

def strip_tags(text):
    """去除 <@font.../@> 富文本标签, 保留纯文本"""
    return re.sub(r'<@font\|[^>]*?/@>', '', text).replace('\\n', '\n').replace('\\u003c', '<').replace('\\u003e', '>')

def shishen_duanyu(rigan, gan_at_pillar, pillar):
    """某柱天干十神断语: ssxx['{十神}{柱}']"""
    ss = shishen(rigan, gan_at_pillar)
    key = ss + pillar  # 年/月/时
    if key in SSXX:
        return ss, strip_tags(SSXX[key])
    return ss, None

def shishen_total(rigan):
    """十神总论"""
    return strip_tags(SSXX[rigan]) if rigan in SSXX else None

def ri_zuo(rigan, rizhi):
    """日坐断语: ssxx['{十神}日坐'] + swk['{日干}{日支}']"""
    main_canggan = zhi_canggan(rizhi)[0]
    ss = shishen(rigan, main_canggan)
    texts = []
    key = ss + '日坐'
    if key in SSXX:
        texts.append((f'日坐{ss}', strip_tags(SSXX[key])))
    gz = rigan + rizhi
    if gz in SWK:
        v = SWK[gz]
        state, _, body = v.partition('#')
        texts.append((f'{gz}日({state})', body))
    return texts

def yue_zuo(rigan, yuezhi):
    """月坐断语: ssxx['{十神}月坐']"""
    ss = shishen(rigan, zhi_canggan(yuezhi)[0])
    key = ss + '月坐'
    if key in SSXX:
        return [(f'月坐{ss}', strip_tags(SSXX[key]))]
    return []

def zuo_zuo(rigan, gz):
    """天干十神 坐 支藏干十神: ssxx['{十神}坐{他神}']"""
    g, z = gz[0], gz[1]
    ss_tg = shishen(rigan, g)
    out = []
    for cg in zhi_canggan(z):
        ss_dz = shishen(rigan, cg)
        key = ss_tg + '坐' + ss_dz
        if key in SSXX:
            out.append((key, strip_tags(SSXX[key])))
    return out

def full_analysis(pillars, rigan):
    """
    pillars: {'年': gz, '月': gz, '日': gz, '时': gz}
    returns list of (标题, 断语)
    """
    results = []
    # 十神总论
    t = shishen_total(rigan)
    if t: results.append((f'日主{rigan}十神总论', t))
    # 各柱透干
    for pillar in ('年', '月', '时'):
        ss, txt = shishen_duanyu(rigan, pillars[pillar][0], pillar)
        if txt: results.append((f'{pillar}柱透{ss}', txt))
    # 日坐/月坐
    for item in ri_zuo(rigan, pillars['日'][1]):
        results.append(item)
    for item in yue_zuo(rigan, pillars['月'][1]):
        results.append(item)
    # 十神坐十神 (年/月/日/时)
    for pillar in ('年', '月', '日', '时'):
        for item in zuo_zuo(rigan, pillars[pillar]):
            results.append(item)
    return results

if __name__ == '__main__':
    p = {'年': '庚午', '月': '辛巳', '日': '庚辰', '时': '辛巳'}
    for title, body in full_analysis(p, '庚'):
        print('###', title)
        print(body[:120].replace('\n', ' '), '...' if len(body) > 120 else '')
        print()
