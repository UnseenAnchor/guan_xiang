# -*- coding: utf-8 -*-
"""
hehui.py — 天干地支刑冲合会
标准规则: 天干五合 / 地支六合·三合·六冲·三刑·六害·相破
"""
from .ganzhi import (GAN, ZHI, tian_gan_he, di_zhi_he, di_zhi_chong, di_zhi_xing,
                     di_zhi_hai)

# 地支相破 (子酉破 丑辰破 寅亥破 卯午破 巳申破 未戌破)
PO_ZHI = {'子': '酉', '酉': '子', '丑': '辰', '辰': '丑', '寅': '亥', '亥': '寅',
          '卯': '午', '午': '卯', '巳': '申', '申': '巳', '未': '戌', '戌': '未'}

# 三合局: 支 -> (局名, 五行)
SANHE = {'申': ('水局', '申子辰'), '子': ('水局', '申子辰'), '辰': ('水局', '申子辰'),
         '寅': ('火局', '寅午戌'), '午': ('火局', '寅午戌'), '戌': ('火局', '寅午戌'),
         '巳': ('金局', '巳酉丑'), '酉': ('金局', '巳酉丑'), '丑': ('金局', '巳酉丑'),
         '亥': ('木局', '亥卯未'), '卯': ('木局', '亥卯未'), '未': ('木局', '亥卯未')}

# 三会方 (寅卯辰会东方木...)
SANHUI = {'寅': ('东方木', '寅卯辰'), '卯': ('东方木', '寅卯辰'), '辰': ('东方木', '寅卯辰'),
          '巳': ('南方火', '巳午未'), '午': ('南方火', '巳午未'), '未': ('南方火', '巳午未'),
          '申': ('西方金', '申酉戌'), '酉': ('西方金', '申酉戌'), '戌': ('西方金', '申酉戌'),
          '亥': ('北方水', '亥子丑'), '子': ('北方水', '亥子丑'), '丑': ('北方水', '亥子丑')}


def analyze(pillars):
    """
    pillars: {'年': '庚午', '月': '辛巳', '日': '庚辰', '时': '辛巳'}
    returns: list of (类型, 参与柱, 参与干支, 说明)
    """
    gz = {p: pillars[p] for p in ('年', '月', '日', '时')}
    pos = ['年', '月', '日', '时']
    gans = {p: gz[p][0] for p in pos}
    zhis = {p: gz[p][1] for p in pos}
    result = []

    # ---- 天干五合 ----
    for i in range(4):
        for j in range(i + 1, 4):
            gi, gj = gans[pos[i]], gans[pos[j]]
            if tian_gan_he(gi) == gj:
                result.append(('天干五合', f'{pos[i]}{pos[j]}', f'{gi}{gj}', f'{gi}与{gj}合'))

    # ---- 地支六合 ----
    for i in range(4):
        for j in range(i + 1, 4):
            zi, zj = zhis[pos[i]], zhis[pos[j]]
            if di_zhi_he(zi) == zj:
                result.append(('地支六合', f'{pos[i]}{pos[j]}', f'{zi}{zj}', f'{zi}与{zj}合'))

    # ---- 地支三合 (三支齐见才算) ----
    zhi_list = [zhis[p] for p in pos]
    for group_name, members in [('水局', '申子辰'), ('火局', '寅午戌'), ('金局', '巳酉丑'), ('木局', '亥卯未')]:
        present = [p for p in pos if zhis[p] in members]
        if len(present) == 3:
            result.append(('地支三合', ''.join(present), ''.join(sorted(zhis[p] for p in present)), f'{group_name}成局'))
        elif len(present) == 2 and any(z for z in zhi_list if z not in members and SANHE.get(z, ('', ''))[0].endswith(group_name[0])):
            pass  # 半合需中神, 简化只报成局

    # 半合 (两支 + 中神在)
    for group_name, members in [('水局', '申子辰'), ('火局', '寅午戌'), ('金局', '巳酉丑'), ('木局', '亥卯未')]:
        present = [p for p in pos if zhis[p] in members]
        if len(present) == 2:
            result.append(('地支半合', ''.join(present), ''.join(zhis[p] for p in present), f'{group_name}半合'))

    # ---- 地支六冲 ----
    for i in range(4):
        for j in range(i + 1, 4):
            zi, zj = zhis[pos[i]], zhis[pos[j]]
            if di_zhi_chong(zi) == zj:
                result.append(('地支六冲', f'{pos[i]}{pos[j]}', f'{zi}{zj}', f'{zi}冲{zj}'))

    # ---- 地支三刑 (寅巳申 / 丑戌未 三支齐, 子卯刑 两支, 自刑) ----
    for trio, name in [(('寅', '巳', '申'), '无恩之刑'), (('丑', '戌', '未'), '恃势之刑')]:
        present = [p for p in pos if zhis[p] in trio]
        if len(present) == 3:
            result.append(('地支三刑', ''.join(present), ''.join(zhis[p] for p in present), f'{name}成局'))
    for i in range(4):
        for j in range(i + 1, 4):
            zi, zj = zhis[pos[i]], zhis[pos[j]]
            if di_zhi_xing(zi) == zj:
                name = '无礼之刑' if {zi, zj} == {'子', '卯'} else '相刑'
                result.append(('地支相刑', f'{pos[i]}{pos[j]}', f'{zi}{zj}', f'{zi}刑{zj}'))
        # 自刑
        z = zhis[pos[i]]
        if z in ('辰', '午', '酉', '亥'):
            result.append(('地支自刑', pos[i], z + z, f'{z}自刑'))

    # ---- 地支六害 ----
    for i in range(4):
        for j in range(i + 1, 4):
            zi, zj = zhis[pos[i]], zhis[pos[j]]
            if di_zhi_hai(zi) == zj:
                result.append(('地支六害', f'{pos[i]}{pos[j]}', f'{zi}{zj}', f'{zi}害{zj}'))

    # ---- 地支相破 ----
    for i in range(4):
        for j in range(i + 1, 4):
            zi, zj = zhis[pos[i]], zhis[pos[j]]
            if PO_ZHI.get(zi) == zj:
                result.append(('地支相破', f'{pos[i]}{pos[j]}', f'{zi}{zj}', f'{zi}破{zj}'))

    # ---- 地支三会 ----
    for group_name, members in [('东方木', '寅卯辰'), ('南方火', '巳午未'), ('西方金', '申酉戌'), ('北方水', '亥子丑')]:
        present = [p for p in pos if zhis[p] in members]
        if len(present) == 3:
            result.append(('地支三会', ''.join(present), ''.join(zhis[p] for p in present), f'{group_name}会方'))

    return result


if __name__ == '__main__':
    p = {'年': '庚午', '月': '辛巳', '日': '庚辰', '时': '辛巳'}
    for r in analyze(p):
        print(f'  {r[0]} {r[1]} {r[2]} {r[3]}')
