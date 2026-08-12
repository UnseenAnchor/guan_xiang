# -*- coding: utf-8 -*-
"""
huangli.py — 老黄历模块 (对齐 app UCyCalendar)
数据源: lunar-python (寿星天文历, 与 app 同源 UShouXingUtil)
覆盖 app UCyCalendar 全部字段: 值星/十二神/黄道黑道/九星/二十八宿/六曜/彭祖百忌/胎神/星座/宜忌
"""
from lunar_python import Solar


def get_huangli(y, m, d):
    """返回某日完整黄历信息 dict"""
    solar = Solar.fromYmd(y, m, d)
    l = solar.getLunar()
    # 时辰列表 (子时~亥时)
    shichen = []
    for i in range(12):
        shichen.append({
            '时辰': l.getTimeGanZhiByIndex(i) if hasattr(l, 'getTimeGanZhiByIndex') else '',
            '六曜': '',
        })
    xiu = l.getXiu()
    xiu_fullname, _, _ = get_xiu_fullname(xiu)
    info = {
        '日期': f'{y}-{m:02d}-{d:02d}',
        '农历': l.toString(),
        '干支': f'{l.getYearInGanZhi()}年 {l.getMonthInGanZhi()}月 {l.getDayInGanZhi()}日',
        '生肖': l.getYearShengXiao(),
        '星座': solar.getXingZuo() if hasattr(solar, 'getXingZuo') else '',
        # 建除十二值星 (Duty)
        '值星': l.getZhiXing(),
        # 黄道黑道十二神 (TwelveStar/Ecliptic)
        '天神': l.getDayTianShen(),
        '黄道黑道': l.getDayTianShenType(),
        '吉凶': l.getDayTianShenLuck(),
        # 二十八宿 (TwentyEightStar)
        '星宿': xiu,
        '星宿全名': xiu_fullname or xiu,
        '七政': l.getZheng(),
        '动物': l.getAnimal(),
        '方位': l.getGong(),
        '四象': l.getShou(),
        # 九星 (NineStar)
        '日九星': l.getDayNineStar(),
        '月九星': l.getMonthNineStar(),
        '年九星': l.getYearNineStar(),
        # 彭祖百忌 (PengZu)
        '彭祖日干忌': l.getPengZuGan(),
        '彭祖日支忌': l.getPengZuZhi(),
        # 胎神 (Fetus)
        '胎神': l.getDayPositionTai(),
        # 神位方位
        '喜神': l.getDayPositionXi(),
        '喜神方位': l.getDayPositionXiDesc(),
        '福神': l.getDayPositionFu(),
        '福神方位': l.getDayPositionFuDesc(),
        '财神': l.getDayPositionCai(),
        '财神方位': l.getDayPositionCaiDesc(),
        '阳贵': l.getDayPositionYangGui(),
        '阳贵方位': l.getDayPositionYangGuiDesc(),
        '阴贵': l.getDayPositionYinGui(),
        '阴贵方位': l.getDayPositionYinGuiDesc(),
        # 宜忌
        '宜': l.getDayYi(),
        '忌': l.getDayJi(),
        '吉神': l.getDayJiShen(),
        '凶煞': l.getDayXiongSha(),
        # 节气
        '当前节气': str(l.getJieQi() or '无'),
        '上节气': str(l.getPrevJieQi()),
        '下节气': str(l.getNextJieQi()),
        '冲煞': l.getDayChongDesc() if hasattr(l, 'getDayChongDesc') else '',
    }
    return info


def get_solar_terms(y, m, d):
    """当年节气表"""
    l = Solar.fromYmd(y, m, d).getLunar()
    table = l.getJieQiTable()
    out = {}
    for k, v in table.items():
        out[k] = str(v)
    return out


def get_jianchu_jieshi(zhi_xing):
    """建除十二神解释 (维基百科白话 + 协纪辨方书原文)"""
    import json as _json, os as _os
    _p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'knowledge', '黄历_建除十二神.json')
    with open(_p, encoding='utf-8') as _f:
        d = _json.load(_f)
    luck = d['shier_shen_jixiong']
    # 建除值日的传统吉凶分类与黄道十二天神是两套并列系统，不在此混称黄道/黑道。
    ji = '吉' if zhi_xing in luck['吉'] else ('凶' if zhi_xing in luck['凶'] else '')
    return ji, luck['口诀']


def get_xiu_fullname(xiu):
    """二十八宿全名 (协纪辨方书): 角木蛟/亢金龙..."""
    import json as _json, os as _os
    _p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'knowledge', '黄历_协纪辨方书.json')
    with open(_p, encoding='utf-8') as _f:
        d = _json.load(_f)
    for row in d.get('二十八宿表', []):
        if row['宿'] == xiu:
            return row['全名'], row['七政'], row['动物']
    return None, None, None


if __name__ == '__main__':
    info = get_huangli(2024, 2, 10)
    for k, v in info.items():
        print(f'  {k}: {v}')
