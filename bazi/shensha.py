# -*- coding: utf-8 -*-
"""
shensha.py — 神煞查法
采用常见传统神煞查法。
"""
from .ganzhi import GAN, ZHI, nayin, xunkong, zhi_index

# ---------- 标准查法表 ----------
# 天乙贵人: 日/年干 -> 地支 (阴贵/阳贵合并)
TIANYI = {'甲': '丑未', '戊': '丑未', '庚': '丑未', '乙': '子申', '己': '子申',
          '丙': '亥酉', '丁': '亥酉', '壬': '卯巳', '癸': '卯巳', '辛': '午寅'}
# 文昌贵人
WENCHANG = {'甲': '巳', '乙': '午', '丙': '申', '戊': '申', '丁': '酉', '己': '酉',
            '庚': '亥', '辛': '子', '壬': '寅', '癸': '卯'}
# 干禄
GANLU = {'甲': '寅', '乙': '卯', '丙': '巳', '戊': '巳', '丁': '午', '己': '午',
         '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
# 羊刃
YANGREN = {'甲': '卯', '乙': '辰', '丙': '午', '戊': '午', '丁': '未', '己': '未',
           '庚': '酉', '辛': '戌', '壬': '子', '癸': '丑'}
# 太极贵人
TAIJI = {'甲': '子午', '戊': '子午', '乙': '丑未', '己': '丑未', '丙': '寅申', '丁': '寅申',
         '壬': '卯酉', '癸': '卯酉', '庚': '辰戌', '辛': '辰戌'}
# 国印贵人
GUOYIN = {'甲': '戌', '乙': '亥', '丙': '丑', '戊': '丑', '丁': '寅', '己': '寅',
          '庚': '辰', '辛': '巳', '壬': '未', '癸': '申'}
# 金舆
JINYU = {'甲': '辰', '乙': '巳', '丙': '未', '戊': '未', '丁': '申', '己': '申',
         '庚': '戌', '辛': '亥', '壬': '丑', '癸': '寅'}
# 流霞
LIUXIA = {'甲': '酉', '乙': '戌', '丙': '未', '戊': '未', '丁': '午', '己': '午',
          '庚': '辰', '辛': '卯', '壬': '亥', '癸': '寅'}
# 红艳煞
HONGYAN = {'甲': '午', '乙': '申', '丙': '寅', '丁': '未', '戊': '辰', '己': '辰',
           '庚': '戌', '辛': '酉', '壬': '子', '癸': '申'}
# 天德贵人: 月支 -> 见干
TIANDE = {'子': '巳', '丑': '庚', '寅': '丁', '卯': '申', '辰': '壬', '巳': '辛',
          '午': '亥', '未': '甲', '申': '癸', '酉': '寅', '戌': '丙', '亥': '乙'}
# 月德贵人: 三合局 -> 见干
YUEDE = {('寅', '午', '戌'): '丙', ('申', '子', '辰'): '壬', ('亥', '卯', '未'): '甲', ('巳', '酉', '丑'): '庚'}
SANHE_GROUPS = [('申', '子', '辰'), ('寅', '午', '戌'), ('巳', '酉', '丑'), ('亥', '卯', '未')]
# 三合: 支 -> 所在局
def sanhe_group(z):
    for g in SANHE_GROUPS:
        if z in g: return g
    return None
# 三合 -> 驿马/桃花/华盖/将星/劫煞/亡神/灾煞
def sanhe_star(z, kind):
    g = sanhe_group(z)
    if not g: return None
    table = {
        '驿马': {0: 2, 1: 0, 2: 3, 3: 1},   # 申子辰->寅, 寅午戌->申, 巳酉丑->亥, 亥卯未->巳
        '桃花': {0: 3, 1: 1, 2: 0, 3: 2},   # 申子辰->酉, 寅午戌->卯, 巳酉丑->午, 亥卯未->子
        '华盖': {0: 2, 1: 2, 2: 2, 3: 2},   # 三合墓库: 辰戌丑未
        '将星': {0: 0, 1: 0, 2: 0, 3: 0},   # 三合中神: 子午卯酉
        '劫煞': {0: 3, 1: 2, 2: 1, 3: 0},
        '亡神': {0: 2, 1: 3, 2: 0, 3: 1},
        '灾煞': {0: 1, 1: 3, 2: 2, 3: 0},
    }
    # 具体: 以三合局五行论
    idx = g.index(z)
    if kind == '驿马': return g[(idx + 2) % 3]  # 冲三合首支之支
    if kind == '桃花':  # 三合局的沐浴位 = 三合首支的三合外
        return {'申子辰': '酉', '寅午戌': '卯', '巳酉丑': '午', '亥卯未': '子'}[ ''.join(g) ]
    if kind == '华盖':
        return {'申子辰': '辰', '寅午戌': '戌', '巳酉丑': '丑', '亥卯未': '未'}[ ''.join(g) ]
    if kind == '将星':
        return {'申子辰': '子', '寅午戌': '午', '巳酉丑': '酉', '亥卯未': '卯'}[ ''.join(g) ]
    if kind == '劫煞':
        return {'申子辰': '巳', '寅午戌': '亥', '巳酉丑': '寅', '亥卯未': '申'}[ ''.join(g) ]
    if kind == '亡神':
        return {'申子辰': '亥', '寅午戌': '巳', '巳酉丑': '申', '亥卯未': '寅'}[ ''.join(g) ]
    if kind == '灾煞':
        return {'申子辰': '午', '寅午戌': '子', '巳酉丑': '卯', '亥卯未': '酉'}[ ''.join(g) ]
    return None

# 天医: 月支前一位
def tianyi_star(month_zhi):
    return ZHI[(zhi_index(month_zhi) + 11) % 12]

# 红鸾/天喜: 年支 -> 卯/酉 偏移 (子->卯 卯->子 对称)
def hongluan(year_zhi):
    return ZHI[(zhi_index(year_zhi) + 3) % 12]   # 子(0)->卯(3), 丑(1)->辰(4)...
def tianxi(year_zhi):
    return ZHI[(zhi_index(year_zhi) + 9) % 12]   # 子(0)->酉(9)

# 孤辰/寡宿: 年支三合前后
GCHEN = {'亥子丑': '寅', '寅卯辰': '巳', '巳午未': '申', '申酉戌': '亥'}
GUASU = {'亥子丑': '戌', '寅卯辰': '丑', '巳午未': '辰', '申酉戌': '未'}
def jichu_group(z):
    for k in GCHEN:
        if z in k: return k
    return None
def guchen(year_zhi): return GCHEN[jichu_group(year_zhi)]
def guasu(year_zhi):  return GUASU[jichu_group(year_zhi)]

# 元辰(大耗): 年支查 (阳男阴女/阴男阳女不同, 简化用标准表)
YUANCHEN = {'子': '未', '丑': '辰', '寅': '酉', '卯': '戌', '辰': '亥', '巳': '午',
            '午': '丑', '未': '申', '申': '卯', '酉': '戌', '戌': '巳', '亥': '子'}  # 简化: 取一版

# 披麻/吊客/丧门: 年支偏移 (丧门=年支后2位, 吊客=年支后4位? 按app: 子年生: 丧门寅(前2), 吊客戌(后2), 披麻酉(后3))
def sangmen(year_zhi):  return ZHI[(zhi_index(year_zhi) + 2) % 12]   # 子->寅
def diaoke(year_zhi):   return ZHI[(zhi_index(year_zhi) + 10) % 12]  # 子->戌
def pima(year_zhi):     return ZHI[(zhi_index(year_zhi) + 9) % 12]   # 子->酉

# 勾绞煞：按年支与桃花六冲地支计算
def goujiao(year_zhi):
    taohua = sanhe_star(year_zhi, '桃花')
    return ZHI[(zhi_index(taohua) + 6) % 12] if taohua else None

# 飞刃 = 羊刃的六冲
def feiren(rigan):
    yr = YANGREN.get(rigan)
    return ZHI[(zhi_index(yr) + 6) % 12] if yr else None

# ---------- 日柱固定神煞 ----------
QUEIGANG = {'庚辰', '庚戌', '壬辰', '戊戌'}                      # 魁罡
GUANLUAN = {'甲寅', '乙巳', '丙午', '丁巳', '戊午', '戊申', '辛亥', '壬子'}  # 孤鸾煞
YINCHA_YANGCUO = {'丙子', '丙午', '丁丑', '丁未', '戊寅', '戊申', '辛卯', '辛酉', '壬辰', '壬戌', '癸巳', '癸亥'}  # 阴差阳错
BAZHUAN = {'甲寅', '乙卯', '丁未', '戊申', '己未', '庚申', '辛酉', '癸丑'}  # 八专
JIUCHOU = {'壬子', '壬午', '戊子', '戊午', '己卯', '己酉', '辛卯', '辛酉', '乙卯', '乙酉'}  # 九丑
SHILING = {'甲辰', '乙亥', '丙辰', '丁酉', '戊午', '庚戌', '庚寅', '辛亥', '壬寅', '癸未'}  # 十灵日
SHIE = {'甲辰', '乙巳', '壬申', '丙申', '丁亥', '庚辰', '戊戌', '癸亥', '辛巳', '己丑'}      # 十恶大败
JINSHEN = {'乙丑', '己巳', '癸酉'}                              # 金神 (日或时)
LIUXIU = {'丙午', '丁未', '戊子', '戊午', '己丑', '己未', '辛巳', '辛丑', '壬辰', '壬戌', '癸卯', '癸丑'}  # 六秀日
SIANFEI = {'春': {'庚申', '辛酉'}, '夏': {'壬子', '癸亥'}, '秋': {'甲寅', '乙卯'}, '冬': {'丙午', '丁巳'}}  # 四废日
TIANZHUAN = {'春': '乙卯', '夏': '丙午', '秋': '辛酉', '冬': '壬子'}   # 天转
DIZHUAN = {'春': '辛卯', '夏': '戊午', '秋': '癸酉', '冬': '丙子'}     # 地转
TIANSHE = {'春': '戊寅', '夏': '甲午', '秋': '戊申', '冬': '甲子'}     # 天赦日

def season(month):  # 月(节气月1-12) -> 季节
    return {1: '春', 2: '春', 3: '春', 4: '夏', 5: '夏', 6: '夏',
            7: '秋', 8: '秋', 9: '秋', 10: '冬', 11: '冬', 12: '冬'}[month]

# ---------- 童子煞 ----------
def tongzi(month_season, year_nayin, ri_zhi, shi_zhi, ri_gan):
    """按季节、年纳音和日时支计算童子煞。"""
    hits = []
    if month_season in ('春', '秋'):
        if ri_zhi in ('寅', '子') or shi_zhi in ('寅', '子'):
            hits.append('春秋生人, 日支或时支见寅/子')
    elif month_season in ('夏', '冬'):
        if ri_zhi in ('卯', '未', '辰') or shi_zhi in ('卯', '未', '辰'):
            hits.append('夏冬生人, 日支或时支见卯/未/辰')
    yn = year_nayin
    if yn in ('金', '木'):
        if ri_zhi in ('午', '卯') or shi_zhi in ('午', '卯'):
            hits.append('年纳音金/木, 日支或时支见午/卯')
    if yn in ('水', '火'):
        if ri_zhi in ('酉', '戌') or shi_zhi in ('酉', '戌'):
            hits.append('年纳音水/火, 日支或时支见酉/戌')
    if yn == '土':
        if ri_zhi in ('子', '丑', '巳') or shi_zhi in ('子', '丑', '巳'):
            hits.append('年纳音土, 日支或时支见子/丑/巳')
    return hits

# ---------- 主查法 ----------
def query_shensha(pillars, month_season, year_nayin):
    """
    pillars: dict with keys y_g, y_z, m_g, m_z, d_g, d_z, h_g, h_z (年月日时干支)
    returns: list of (神煞名, 所在柱, 说明)
    """
    yg, yz = pillars['y_g'], pillars['y_z']
    mg, mz = pillars['m_g'], pillars['m_z']
    dg, dz = pillars['d_g'], pillars['d_z']
    hg, hz = pillars['h_g'], pillars['h_z']
    rzhi4 = {'年': yz, '月': mz, '日': dz, '时': hz}
    rgan4 = {'年': yg, '月': mg, '日': dg, '时': hg}
    dz_combined = yz + mz + dz + hz
    gan_combined = yg + mg + dg + hg
    result = []

    def add(name, where, extra=''):
        result.append((name, where, extra))

    # 天乙贵人 (日/年干)
    for g, pos in (('日', dg), ('年', yg)):
        for z in TIANYI.get(g, ''):
            for p, zz in rzhi4.items():
                if zz == z: add('天乙贵人', p, f'{g}干见{z}')
    # 文昌贵人
    for g, pos in (('日', dg), ('年', yg)):
        z = WENCHANG.get(g)
        if z:
            for p, zz in rzhi4.items():
                if zz == z: add('文昌贵人', p, f'{g}干见{z}')
    # 干禄
    z = GANLU.get(dg)
    if z:
        for p, zz in rzhi4.items():
            if zz == z: add('干禄', p)
    # 羊刃
    z = YANGREN.get(dg)
    if z:
        for p, zz in rzhi4.items():
            if zz == z: add('羊刃', p)
    # 飞刃
    z = feiren(dg)
    if z:
        for p, zz in rzhi4.items():
            if zz == z: add('飞刃', p)
    # 太极贵人
    for g, pos in (('日', dg), ('年', yg)):
        for z in TAIJI.get(g, ''):
            for p, zz in rzhi4.items():
                if zz == z: add('太极贵人', p)
    # 国印贵人
    for g, pos in (('日', dg), ('年', yg)):
        z = GUOYIN.get(g)
        if z:
            for p, zz in rzhi4.items():
                if zz == z: add('国印贵人', p)
    # 金舆
    for g, pos in (('日', dg), ('年', yg)):
        z = JINYU.get(g)
        if z:
            for p, zz in rzhi4.items():
                if zz == z: add('金舆', p)
    # 流霞
    z = LIUXIA.get(dg)
    if z:
        for p, zz in rzhi4.items():
            if zz == z: add('流霞', p)
    # 红艳煞
    z = HONGYAN.get(dg)
    if z:
        for p, zz in rzhi4.items():
            if zz == z: add('红艳煞', p)
    # 天德贵人 (月支查干)
    g = TIANDE.get(mz)
    if g and g in gan_combined:
        add('天德贵人', '月', f'{mz}月见{g}')
    # 月德贵人
    for grp, g in YUEDE.items():
        if mz in grp and g in gan_combined:
            add('月德贵人', '月', f'{mz}月见{g}')
    # 驿马/桃花/华盖/将星/劫煞/亡神/灾煞 (年支、日支)
    for pos, zz in (('年', yz), ('日', dz)):
        for kind in ('驿马', '桃花', '华盖', '将星', '劫煞', '亡神', '灾煞'):
            t = sanhe_star(zz, kind)
            if t and t in dz_combined:
                where = [p for p, z2 in rzhi4.items() if z2 == t][0]
                add(kind, where, f'{pos}支{zz}见{t}')
    # 红鸾/天喜
    t = hongluan(yz)
    if t in dz_combined: add('红鸾', [p for p, z2 in rzhi4.items() if z2 == t][0])
    t = tianxi(yz)
    if t in dz_combined: add('天喜', [p for p, z2 in rzhi4.items() if z2 == t][0])
    # 孤辰/寡宿
    t = guchen(yz)
    if t in dz_combined: add('孤辰', [p for p, z2 in rzhi4.items() if z2 == t][0])
    t = guasu(yz)
    if t in dz_combined: add('寡宿', [p for p, z2 in rzhi4.items() if z2 == t][0])
    # 天医
    t = tianyi_star(mz)
    if t in dz_combined: add('天医', [p for p, z2 in rzhi4.items() if z2 == t][0])
    # 元辰
    t = YUANCHEN.get(yz)
    if t and t in dz_combined: add('元辰', [p for p, z2 in rzhi4.items() if z2 == t][0])
    # 丧门/吊客/披麻
    for name, f in (('丧门', sangmen), ('吊客', diaoke), ('披麻', pima)):
        t = f(yz)
        if t in dz_combined: add(name, [p for p, z2 in rzhi4.items() if z2 == t][0])
    # 勾绞煞
    t = goujiao(yz)
    if t and t in dz_combined: add('勾绞煞', [p for p, z2 in rzhi4.items() if z2 == t][0])
    # 三奇贵人
    for i in range(4):
        tri = gan_combined[i:i+3]
        if len(tri) == 3 and tri in ('甲乙丙', '乙丙丁', '丙丁戊', '丁戊己', '戊己庚', '己庚辛', '庚辛壬', '辛壬癸', '壬癸甲', '癸甲乙'):
            add('三奇贵人', '年月日'[i:i+3] if i < 2 else '月日时', ''.join(tri))
            break
    # 空亡 (日柱旬空)
    for gz_name, pos in (('日柱', '日'), ('年柱', '年')):
        gz = {'日柱': dg + dz, '年柱': yg + yz}[gz_name]
        for k in xunkong(gz):
            for p, zz in rzhi4.items():
                if zz == k: add('空亡', p, f'{gz_name}{gz}空{k}')

    # 日柱固定神煞
    rz = dg + dz
    if rz in QUEIGANG: add('魁罡', '日', rz)
    if rz in GUANLUAN: add('孤鸾煞', '日', rz)
    if rz in YINCHA_YANGCUO: add('阴差阳错', '日', rz)
    if rz in BAZHUAN: add('八专', '日', rz)
    if rz in JIUCHOU: add('九丑', '日', rz)
    if rz in SHILING: add('十灵日', '日', rz)
    if rz in SHIE: add('十恶大败', '日', rz)
    if rz in LIUXIU: add('六秀日', '日', rz)
    if rz in SIANFEI[season(month_season)]: add('四废日', '日', rz)
    if rz == TIANZHUAN[season(month_season)]: add('天转', '日')
    if rz == DIZHUAN[season(month_season)]: add('地转', '日')
    if rz == TIANSHE[season(month_season)]: add('天赦日', '日')
    # 金神 (日/时)
    for pos, gz2 in (('日', rz), ('时', hg + hz)):
        if gz2 in JINSHEN: add('金神', pos, gz2)
    # 童子煞
    for rule in tongzi(season(month_season), year_nayin, dz, hz, dg):
        add('童子煞', '日/时', rule)

    return result

if __name__ == '__main__':
    p = {'y_g': '庚', 'y_z': '午', 'm_g': '辛', 'm_z': '巳', 'd_g': '庚', 'd_z': '辰', 'h_g': '辛', 'h_z': '巳'}
    ss = query_shensha(p, 4, '土')
    for name, where, extra in ss:
        print(f'  {name:6s} {where} {extra}')
