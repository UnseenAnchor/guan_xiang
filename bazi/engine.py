# -*- coding: utf-8 -*-
"""
engine.py — 八字排盘主引擎
结合 lunar-python 的历法能力与本地命理规则数据。
"""
from lunar_python import Solar, Lunar, EightChar
from .ganzhi import (GAN, ZHI, shishen, nayin, nayin_jian, xunkong, shier_changsheng,
                     zhi_canggan, zhi_canggan_wuxing, zhi_shengxiao, gan_wuxing, gan_yinyang,
                     zhi_wuxing, zhi_yinyang, tian_gan_he, di_zhi_he, di_zhi_chong, JIAZI)
from .shensha import query_shensha, season

GAN_CN = GAN
ZHI_CN = ZHI

def solar_to_lunar(y, m, d, h=12, mi=0, s=0):
    """公历 -> lunar-python Lunar 对象"""
    return Solar.fromYmdHms(y, m, d, h, mi, s).getLunar()

def pillars_from_lunar(lunar):
    """从 Lunar 取四柱 (含藏干/十神等)"""
    ec = lunar.getEightChar()
    y_gz = ec.getYear()      # 年柱 (立春分界)
    m_gz = ec.getMonth()     # 月柱 (节气分界)
    d_gz = ec.getDay()       # 日柱
    h_gz = ec.getTime()      # 时柱
    return {'年': y_gz, '月': m_gz, '日': d_gz, '时': h_gz}

def build_pillar_detail(gz, rigan=None):
    """单柱详情: 干支/五行/阴阳/藏干/十神/纳音/空亡/长生"""
    g, z = gz[0], gz[1]
    d = {
        '干支': gz,
        '天干': g, '干五行': gan_wuxing(g), '干阴阳': gan_yinyang(g),
        '地支': z, '支五行': zhi_wuxing(z), '支阴阳': zhi_yinyang(z), '生肖': zhi_shengxiao(z),
        '藏干': zhi_canggan(z), '藏干五行': zhi_canggan_wuxing(z),
        '纳音': nayin(gz), '纳音简': nayin_jian(gz),
        '空亡': xunkong(gz),
        '长生': shier_changsheng(g, z),
    }
    if rigan:
        d['十神(天干)'] = shishen(rigan, g)
        d['十神(藏干)'] = [shishen(rigan, cg) for cg in d['藏干']]
    return d

def build_chart(y, m, d, h, mi=0, s=0, sex=1, **kwargs):
    """
    输入公历生日, 输出完整命盘 dict.
    sex: 1=男 0=女 (用于大运顺逆)
    """
    solar = Solar.fromYmdHms(y, m, d, h, mi, s)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    pillars = pillars_from_lunar(lunar)
    rigan = pillars['日'][0]

    result = {
        '输入': {'公历': f'{y}年{m}月{d}日 {h:02d}:{mi:02d}', '性别': '男' if sex else '女'},
        '农历': lunar.toString(),
        '生肖': lunar.getYearShengXiao(),
        '四柱': {},
        '日主': rigan,
        '身强弱': None,
    }
    month_idx = (ZHI.index(pillars['月'][1]) - 2) % 12 + 1  # 寅=1 ... 丑=12
    result['神煞'] = query_shensha(
        {'y_g': pillars['年'][0], 'y_z': pillars['年'][1],
         'm_g': pillars['月'][0], 'm_z': pillars['月'][1],
         'd_g': pillars['日'][0], 'd_z': pillars['日'][1],
         'h_g': pillars['时'][0], 'h_z': pillars['时'][1]},
        month_season=month_idx,
        year_nayin=nayin_jian(pillars['年']),
    )
    result['胎元'] = ec.getTaiYuan() if hasattr(ec, 'getTaiYuan') else None
    result['命宫'] = ec.getMingGong() if hasattr(ec, 'getMingGong') else None
    result['身宫'] = None
    result['纳音'] = {}
    for name, gz in pillars.items():
        result['四柱'][name] = build_pillar_detail(gz, rigan)
        result['纳音'][name] = nayin(gz)

    # 大运
    try:
        yun = ec.getYun(1 if sex else 0)
        result['起运'] = yun.getStartYear() if hasattr(yun, 'getStartYear') else None
        result['大运'] = []
        for dy in yun.getDaYun():
            result['大运'].append({
                '序': dy.getIndex(),
                '干支': dy.getGanZhi(),
                '起年': dy.getStartYear(),
                '终年': dy.getEndYear(),
                '年龄': f"{dy.getStartAge()}-{dy.getEndAge()}" if hasattr(dy, 'getStartAge') else '',
            })
    except Exception as e:
        result['大运'] = [('error', str(e))]

    # 流年 (最近5年, 以立春为界)
    result['流年'] = []
    from lunar_python import Lunar as _Lunar
    for i in range(5):
        y2 = y + i
        # 立春分界: 2/4 后取 y2 年干支, 否则 y2-1
        lichun = _Lunar.fromYmd(y2, 2, 4)
        gz_year = lichun.getYearInGanZhi()
        result['流年'].append({'年': y2, '干支': gz_year})

    # 断语分析
    from .analysis import full_analysis
    result['分析'] = full_analysis(pillars, rigan)

    # 刑冲合会
    from .hehui import analyze as analyze_xchh
    result['刑冲合会'] = analyze_xchh(pillars)

    # 大运/流年断语
    from .dayun_duanyu import chart_dy_analysis
    result['运年断语'] = chart_dy_analysis(rigan, result.get('大运', []), result.get('流年', []))

    # 真太阳时 (默认北京经度 116.4, 可传 longitude 覆盖)
    from .solar_time import true_solar_time
    lon = kwargs.get('longitude', 116.4)
    nh, nm, total, lon_d, eot = true_solar_time(y, m, d, h, mi, lon)
    result['真太阳时'] = {'原时间': f'{h:02d}:{mi:02d}', '校正后': f'{nh:02d}:{nm:02d}',
                          '总校正分': round(total, 1), '经度差': round(lon_d, 1), '均时差': round(eot, 1)}

    return result

def _month_index(ec):
    """取节气月序号 (1-12)"""
    try:
        s = ec.getMonth()
        for i, gz in enumerate(JIAZI):
            pass
    except Exception:
        return 1
    return 1

def render_text(chart):
    """命盘 -> 文本"""
    L = []
    L.append('=' * 42)
    L.append(f"【{chart['输入']['公历']}】 {chart['输入']['性别']}")
    L.append(f"农历: {chart['农历']}  生肖: {chart['生肖']}")
    L.append('-' * 42)
    L.append('        年柱      月柱      日柱      时柱')
    gz_line = '    ' + ''.join(f'{chart["四柱"][p]["干支"]:^9s}' for p in ('年', '月', '日', '时'))
    L.append(gz_line)
    for attr, label in (('藏干', '藏干'), ('十神(天干)', '十神'), ('纳音', '纳音'), ('空亡', '空亡'), ('长生', '长生')):
        vals = []
        for p in ('年', '月', '日', '时'):
            v = chart['四柱'][p][attr]
            if attr == '藏干': v = ''.join(v)
            if attr == '十神(天干)': v = str(v)
            if attr == '空亡': v = ''.join(v)
            vals.append(f'{v:^9s}')
        L.append(f'{label:4s} ' + ''.join(vals))
    L.append('-' * 42)
    L.append(f"日主: {chart['日主']}  胎元: {chart['胎元']}  命宫: {chart['命宫']}")
    if chart.get('起运'):
        L.append(f"起运: {chart['起运']}岁")
    L.append('大运: ' + ' '.join(f"{d['干支']}({d['起年']})" for d in chart['大运'][1:10] if d.get('干支')))
    L.append('流年: ' + ' '.join(f"{d['年']}:{d['干支']}" for d in chart['流年']))
    L.append('-' * 42)
    L.append('神煞:')
    for name, where, extra in chart['神煞']:
        L.append(f"  {name}({where}) {extra}")
    L.append('-' * 42)
    L.append('断语分析:')
    for title, body in chart.get('分析', [])[:8]:
        L.append(f'◆ {title}')
        L.append('  ' + body[:200].replace('\n', ' '))
    # 刑冲合会
    if chart.get('刑冲合会'):
        L.append('-' * 42)
        L.append('刑冲合会:')
        for r in chart['刑冲合会']:
            L.append(f"  {r[0]} {r[1]} {r[2]} {r[3]}")
    # 真太阳时
    if chart.get('真太阳时'):
        ts = chart['真太阳时']
        L.append(f"真太阳时: {ts['原时间']} → {ts['校正后']} (校正 {ts['总校正分']}分)")
    # 运年断语
    if chart.get('运年断语'):
        L.append('-' * 42)
        L.append('运年断语 (近似):')
        for d in chart['运年断语']['大运'][:3]:
            L.append(f"  {d['干支']}运: {d['断语'][:80]}")
        for ln in chart['运年断语']['流年'][:2]:
            L.append(f"  {ln['干支']}年: {ln['断语']}")
    L.append('=' * 42)
    return '\n'.join(L)

if __name__ == '__main__':
    chart = build_chart(1990, 5, 15, 10, 30, 0, sex=1)
    print(render_text(chart))
