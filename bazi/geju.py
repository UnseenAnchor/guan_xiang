# -*- coding: utf-8 -*-
"""
geju.py — 格局喜忌 (对齐 app UfGeJuXiJi)
标准子平法: 五行旺衰量化 / 身强身弱 / 月令取格(八格+外格) / 沈氏用神 / 调候用神

📚 参考来源 (目标: 有参考不凭记忆):
- 调候用神表: 《穷通宝鉴》(徐乐吾评注版), 经算准网/维基文库交叉核对 120 条
- 用神五法: 《子平真诠》沈孝瞻 + 徐乐吾评注 (扶抑/病药/调候/专旺/通关)
- 神煞查表: 天乙/文昌/羊刃等经主流口诀核对 (甲戊庚牛羊…)
- 旺衰框架: 得令/得地/得势三主维 (主流共识; 权重为流派选择)
⚠ 权重细节为流派主观选择, 与 app 输出细节需真机对比
"""
from .ganzhi import GAN, ZHI, gan_wuxing, zhi_wuxing, zhi_canggan, zhi_canggan_wuxing, shishen

# ---------- 五行旺衰 (月令旺相休囚死) ----------
# 日主五行 -> {月支五行: 状态}
WANGXING = {
    '木': {'水': '相', '木': '旺', '火': '休', '土': '囚', '金': '死'},
    '火': {'木': '相', '火': '旺', '土': '休', '金': '囚', '水': '死'},
    '土': {'火': '相', '土': '旺', '金': '休', '水': '囚', '木': '死'},
    '金': {'土': '相', '金': '旺', '水': '休', '木': '囚', '火': '死'},
    '水': {'金': '相', '水': '旺', '木': '休', '火': '囚', '土': '死'},
}
STATE_WEIGHT = {'旺': 2.0, '相': 1.0, '休': 0.0, '囚': -1.0, '死': -2.0}

# 十二长生状态 -> 根力
CHANGSHENG_STRENGTH = {'长生': 1.0, '沐浴': 0.6, '冠带': 0.8, '临官': 1.0, '帝旺': 1.0,
                       '衰': 0.4, '病': 0.2, '死': 0.0, '墓': 0.8, '绝': 0.0, '胎': 0.3, '养': 0.5}
# 十二长生 (天干->地支) 简表: 用于计算日主地支根
CHANGSHENG_TABLE = {
    '甲': {'亥': '长生', '子': '沐浴', '丑': '冠带', '寅': '临官', '卯': '帝旺', '辰': '衰', '巳': '病', '午': '死', '未': '墓', '申': '绝', '酉': '胎', '戌': '养'},
    '丙': {'寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官', '午': '帝旺', '未': '衰', '申': '病', '酉': '死', '戌': '墓', '亥': '绝', '子': '胎', '丑': '养'},
    '戊': {'寅': '长生', '卯': '沐浴', '辰': '冠带', '巳': '临官', '午': '帝旺', '未': '衰', '申': '病', '酉': '死', '戌': '墓', '亥': '绝', '子': '胎', '丑': '养'},
    '庚': {'巳': '长生', '午': '沐浴', '未': '冠带', '申': '临官', '酉': '帝旺', '戌': '衰', '亥': '病', '子': '死', '丑': '墓', '寅': '绝', '卯': '胎', '辰': '养'},
    '壬': {'申': '长生', '酉': '沐浴', '戌': '冠带', '亥': '临官', '子': '帝旺', '丑': '衰', '寅': '病', '卯': '死', '辰': '墓', '巳': '绝', '午': '胎', '未': '养'},
    '乙': {'午': '长生', '巳': '沐浴', '辰': '冠带', '卯': '临官', '寅': '帝旺', '丑': '衰', '子': '病', '亥': '死', '戌': '墓', '酉': '绝', '申': '胎', '未': '养'},
    '丁': {'酉': '长生', '申': '沐浴', '未': '冠带', '午': '临官', '巳': '帝旺', '辰': '衰', '卯': '病', '寅': '死', '丑': '墓', '子': '绝', '亥': '胎', '戌': '养'},
    '己': {'酉': '长生', '申': '沐浴', '未': '冠带', '午': '临官', '巳': '帝旺', '辰': '衰', '卯': '病', '寅': '死', '丑': '墓', '子': '绝', '亥': '胎', '戌': '养'},
    '辛': {'子': '长生', '亥': '沐浴', '戌': '冠带', '酉': '临官', '申': '帝旺', '未': '衰', '午': '病', '巳': '死', '辰': '墓', '卯': '绝', '寅': '胎', '丑': '养'},
    '癸': {'卯': '长生', '寅': '沐浴', '丑': '冠带', '子': '临官', '亥': '帝旺', '戌': '衰', '酉': '病', '申': '死', '未': '墓', '午': '绝', '巳': '胎', '辰': '养'},
}

# 调候用神表 (《穷通宝鉴》徐乐吾评注版, 来源: 算准网/维基文库核对)
# 格式: 十干 x 12月(寅卯辰巳午未申酉戌亥子丑) -> 用神干支
TIAOHOU = {
    '甲': ['丙癸', '庚丙丁', '庚丁壬', '癸庚丁', '癸庚丁', '癸庚丁', '庚丁壬', '庚丁丙', '庚甲丁壬癸', '庚丁丙戊', '丁庚丙', '庚丁丙'],
    '乙': ['丙癸', '丙癸', '癸丙戊', '癸', '癸丙', '癸丙', '丙癸己', '癸丙丁', '癸辛', '丙戊', '丙', '丙'],
    '丙': ['壬庚', '壬己', '壬甲', '壬癸庚', '壬庚', '壬庚癸', '壬戊', '壬癸', '甲壬', '甲戊庚壬', '壬戊己', '壬甲'],
    '丁': ['甲庚', '甲庚', '甲庚', '甲庚', '壬庚癸', '甲壬庚', '甲庚丙戊', '甲庚丙戊', '甲庚戊', '甲庚', '甲庚', '甲庚'],
    '戊': ['丙甲癸', '丙甲癸', '甲丙癸', '甲丙癸', '壬甲丙', '癸丙甲', '丙癸甲', '丙癸', '甲丙癸', '甲丙', '丙甲', '丙甲'],
    '己': ['丙庚甲', '甲癸丙', '丙癸甲', '癸丙', '癸丙', '癸丙', '丙癸', '丙癸', '甲丙癸', '丙甲戊', '丙甲戊', '丙甲戊'],
    '庚': ['戊甲壬丙丁', '丁甲庚丙', '甲丁壬癸', '壬戊丙丁', '壬癸', '丁甲', '丁甲', '丁甲', '甲壬', '丁丙', '丁甲丙', '丙丁甲'],
    '辛': ['己壬庚', '壬甲', '壬甲', '壬甲癸', '壬己癸', '壬庚甲', '壬甲戊', '壬甲', '壬甲', '壬', '丙戊壬', '壬戊己'],
    '壬': ['庚丙戊', '戊辛庚', '甲庚', '壬辛庚癸', '癸庚辛', '辛甲', '戊丁', '甲庚', '甲丙', '戊丙庚', '戊丙', '丙丁甲'],
    '癸': ['辛丙', '庚辛', '丙辛甲', '辛', '庚辛壬癸', '庚辛壬癸', '丁', '辛丙', '辛甲壬癸', '庚辛戊丁', '丙辛', '丙丁'],
}
MONTH_IDX = {'寅': 0, '卯': 1, '辰': 2, '巳': 3, '午': 4, '未': 5,
             '申': 6, '酉': 7, '戌': 8, '亥': 9, '子': 10, '丑': 11}


def strength_analysis(pillars, rigan):
    """
    五行旺衰 + 身强弱量化评分
    pillars: {'年': gz, '月': gz, '日': gz, '时': gz}
    returns: dict
    """
    rg_wx = gan_wuxing(rigan)
    yz, mz, dz, hz = pillars['年'][1], pillars['月'][1], pillars['日'][1], pillars['时'][1]
    yg, mg, dg, hg = pillars['年'][0], pillars['月'][0], pillars['日'][0], pillars['时'][0]

    # 1. 得令 (月支状态)
    m_state = WANGXING[rg_wx][zhi_wuxing(mz)]
    score = STATE_WEIGHT[m_state]
    details = [f'月令{zhi_wuxing(mz)}({mz}): {m_state} ({STATE_WEIGHT[m_state]:+.0f})']

    # 2. 得地 (四支根力)
    root_score = 0.0
    roots = []
    for name, z in (('年', yz), ('月', mz), ('日', dz), ('时', hz)):
        cs = CHANGSHENG_TABLE[rigan][z]
        w = CHANGSHENG_STRENGTH[cs]
        # 藏干主气与日主同五行 -> 本气根
        cg_wx = zhi_canggan_wuxing(z)[0]
        if cg_wx == rg_wx:
            w = max(w, 1.0)  # 本气根强
        if w > 0:
            root_score += w
            roots.append(f'{z}({cs} {w:+.1f})')
    score += root_score
    details.append(f'地支根: {", ".join(roots) if roots else "无根"} ({root_score:+.1f})')

    # 3. 得势 (天干比劫/印)
    shi_score = 0.0
    shi_parts = []
    for name, g in (('年', yg), ('月', mg), ('时', hg)):
        if g == rigan:
            shi_score += 1.0
            shi_parts.append(f'{name}{g}比肩')
        elif gan_wuxing(g) == rg_wx:
            shi_score += 0.5
            shi_parts.append(f'{name}{g}同气')
    score += shi_score
    details.append(f'天干助身: {", ".join(shi_parts) if shi_parts else "无助"} ({shi_score:+.1f})')

    # 判定
    if score >= 4:
        strength = '身强'
    elif score >= 3:
        strength = '偏强'
    elif score >= 2:
        strength = '中和'
    elif score >= 0.5:
        strength = '偏弱'
    else:
        strength = '身弱'

    return {
        '评分': round(score, 1), '身强弱': strength, '月令状态': m_state,
        '细节': details, '得分项': {
            '得令': STATE_WEIGHT[m_state], '得地': round(root_score, 1), '得势': round(shi_score, 1)},
    }


def judge_geju(pillars, rigan, strength_info):
    """
    格局判定: 月令取格 (八格+建禄羊刃+外格)
    """
    mz = pillars['月'][1]
    mg = pillars['月'][0]
    yg, dg, hg = pillars['年'][0], pillars['日'][0], pillars['时'][0]
    all_gan = [yg, mg, dg, hg]

    # 月支本气
    benqi = zhi_canggan(mz)[0]
    benqi_ss = shishen(rigan, benqi)

    # 外格: 从格判断 (全局同一五行或日主无根无助)
    # 简化: 从财/从官杀/从儿/专旺
    wuxing_count = {}
    for g in all_gan:
        wx = gan_wuxing(g)
        wuxing_count[wx] = wuxing_count.get(wx, 0) + 1
    for z in (pillars['年'][1], pillars['月'][1], pillars['日'][1], pillars['时'][1]):
        wx = zhi_wuxing(z)
        wuxing_count[wx] = wuxing_count.get(wx, 0) + 1
    total = sum(wuxing_count.values())
    max_wx = max(wuxing_count, key=wuxing_count.get)
    ratio = wuxing_count[max_wx] / total

    if strength_info['身强弱'] in ('身弱', '偏弱') and ratio >= 0.75:
        if max_wx == gan_wuxing(rigan):
            geju = {'专旺格': {'曲直': '木', '炎上': '火', '稼穑': '土', '从革': '金', '润下': '水'}.get(max_wx, max_wx)}
            return ('外格', '专旺格', f'{max_wx}局成气')
        else:
            return ('外格', '从格', f'日主弱极, 全局{max_wx}旺, 从{max_wx}')

    # 月令取格
    if benqi_ss in ('比肩', '劫财'):
        # 建禄/羊刃格
        if benqi_ss == '比肩':
            return ('建禄格', '建禄格', f'月支{mz}为日主之禄')
        return ('羊刃格', '羊刃格', f'月支{mz}为日主之刃')
    # 本气透干 -> 定格
    for g in (yg, mg, hg):
        if g == benqi:
            return (benqi_ss + '格', benqi_ss + '格', f'月令{mz}本气{benqi}透于{"年" if g==yg else "月" if g==mg else "时"}')
    # 不透干 -> 按本气定格
    return (benqi_ss + '格', benqi_ss + '格', f'月令{mz}本气{benqi}不透, 按本气取格')


def pick_yongshen(pillars, rigan, strength_info, month_zhi):
    """
    用神/忌神/喜神 (《子平真诠》沈孝瞻五法: 扶抑/病药/调候/专旺/通关, 徐乐吾评注)
    """
    rg_wx = gan_wuxing(rigan)
    wx_list = ['木', '火', '土', '金', '水']
    sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 我生
    ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}      # 我克
    kewo = {v: k for k, v in ke.items()}   # 克我

    strength = strength_info['身强弱']

    # ---- 扶抑 (身强抑之/身弱扶之) ----
    if '身强' in strength or strength == '偏强':
        yongshen = [ke[rg_wx], sheng[rg_wx], kewo[rg_wx]]
        jishen = [rg_wx, sheng[kewo[rg_wx]]]  # 比劫印为忌
        method = '扶抑(身强用克泄耗)'
    elif '身弱' in strength or strength == '偏弱':
        yongshen = [rg_wx, sheng[kewo[rg_wx]]]  # 印比生扶
        jishen = [ke[rg_wx], sheng[rg_wx]]
        method = '扶抑(身弱用印比)'
    else:
        yongshen = [rg_wx]
        jishen = []
        method = '中和(酌情扶抑)'

    # ---- 病药 (《子平真诠》: 以扶为喜则以伤其扶者为病, 除其病神即药) ----
    # 病 = 克制用神主力的五行; 药 = 克制病的五行
    bing = []
    yao = []
    if jishen:
        bing = jishen[:1]  # 忌神即病 (主流解读: 病=克用神/耗用神者)
        yao = [kewo[bing[0]]] if bing[0] in kewo else []

    # ---- 调候 (《穷通宝鉴》修正版表) ----
    th = TIAOHOU[rigan][MONTH_IDX[month_zhi]]
    th_wx = [gan_wuxing(g) for g in th]

    # ---- 通关 (《子平真诠》: 两神对峙强弱均平须调和为美) ----
    tongguan = None
    # 简化: 月令五行 与 日主五行 若相克对峙, 取通关 (生月令而生日主之间的桥)
    mz_wx = zhi_wuxing(month_zhi)
    if ke.get(rg_wx) == mz_wx or ke.get(mz_wx) == rg_wx:
        # 相克: 通关 = 能同时生两者之一且被另一所生的五行
        # 简化: 若月令克日主(官杀当令), 印为通关 (官生印印生身)
        if ke.get(mz_wx) == rg_wx:
            tongguan = sheng[mz_wx]  # 月令生我之印
        else:
            tongguan = sheng[rg_wx]

    return {
        '用神': yongshen, '忌神': jishen, '病': bing, '药': yao,
        '调候用神': list(th), '调候干': th,
        '方法': method, '通关': tongguan,
    }


if __name__ == '__main__':
    p = {'年': '庚午', '月': '辛巳', '日': '庚辰', '时': '辛巳'}
    s = strength_analysis(p, '庚')
    print('强弱:', s['身强弱'], '评分:', s['评分'])
    for d in s['细节']: print('  ', d)
    g = judge_geju(p, '庚', s)
    print('格局:', g)
    y = pick_yongshen(p, '庚', s, '巳')
    print('用神:', y['用神'], '忌神:', y['忌神'], '调候:', y['调候用神'], y['方法'])
