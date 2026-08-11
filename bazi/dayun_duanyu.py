# -*- coding: utf-8 -*-
"""
dayun_duanyu.py — 大运/流年断语 (对齐 app UfDayunHint/UfShhLiuNian)
近似实现: 以运干相对日主的十神 + 坐支状态, 从 app 断语库 (ssxx/swk/性格断语) 选取
⚠ 注: app 原版选取规则在 UfDayunHint 代码中, 此为基于标准命理规则的合理近似
"""
import json, os, re
from .ganzhi import shishen, shier_changsheng, zhi_canggan, nayin_jian

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, '..', 'knowledge', 'serjson.json'), encoding='utf-8') as _file:
    SER = json.load(_file)
SSXX = SER['ssxx']
SWK = SER['swk']
with open(os.path.join(_HERE, '..', 'knowledge', 'cn_pure.json'), encoding='utf-8') as _file:
    PURE = json.load(_file)

def _strip(t):
    return re.sub(r'<@font\|[^>]*?/@>', '', t).replace('\\n', ' ').strip()

# 性格断语池 (供运/年吉凶描述)
XINGGE_POOL = [s for s in PURE if re.match(r'^(一生|为人|主)', s)]

def dayun_duanyu(rigan, dayun_gz, sex=1):
    """
    大运断语: 运干十神 + 运支坐长生状态 + 运支藏干十神
    dayun_gz: '壬午'
    """
    g, z = dayun_gz[0], dayun_gz[1]
    ss = shishen(rigan, g)          # 运干相对日主十神
    cs = shier_changsheng(g, z)     # 运干坐支长生
    cg_main = zhi_canggan(z)[0]
    ss_z = shishen(rigan, cg_main)  # 运支主气十神
    ny = nayin_jian(dayun_gz)

    parts = [f'{dayun_gz}运: 天干{ss}, 坐{cs}, 支藏{cg_main}({ss_z}), 纳音{ny}']
    # 从断语库选主断语
    key = ss + '月' if (ss + '月') in SSXX else ss
    if key in SSXX:
        parts.append(_strip(SSXX[key])[:120])
    # 坐支论
    gz_key = g + z
    if gz_key in SWK:
        parts.append(_strip(SWK[gz_key].split('#', 1)[-1])[:80])
    return ' | '.join(parts)


def liunian_duanyu(rigan, ln_gz):
    """流年断语: 流年干十神"""
    g, z = ln_gz[0], ln_gz[1]
    ss = shishen(rigan, g)
    cs = shier_changsheng(g, z)
    return f'{ln_gz}年: 十神{ss}, 坐{cs}'


def chart_dy_analysis(rigan, dayuns, liunians):
    """整盘大运/流年断语列表"""
    out = {'大运': [], '流年': []}
    for d in dayuns:
        if isinstance(d, dict) and d.get('干支'):
            out['大运'].append({'干支': d['干支'], '断语': dayun_duanyu(rigan, d['干支'])})
    for l in liunians:
        out['流年'].append({'年': l['年'], '干支': l['干支'], '断语': liunian_duanyu(rigan, l['干支'])})
    return out


if __name__ == '__main__':
    print(dayun_duanyu('庚', '壬午'))
    print(liunian_duanyu('庚', '庚午'))
