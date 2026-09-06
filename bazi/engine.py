# -*- coding: utf-8 -*-
"""
engine.py — 八字排盘主引擎
结合: lunar-python (标准历法/节气/大运) + 诚易排盘 app 知识库 (十神/纳音/长生/神煞/断语)
"""
from lunar_python import Solar, Lunar, EightChar
import datetime as _dt
import os
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

# 反汇编确认 (libCYBZ.so 0x20996B4): app 晚子时(时>=23)日柱+1换日, 时柱按次日日干起时
def pillars_from_lunar_wzs(lunar, h):
    """晚子时处理: h>=23 时日柱换次日 (对齐 app 行为)"""
    p = pillars_from_lunar(lunar)
    if h >= 23:
        s = lunar.getSolar()
        nxt = Solar.fromYmd(s.getYear(), s.getMonth(), s.getDay())
        nxt_lunar = nxt.next(1).getLunar() if hasattr(nxt, 'next') else None
        if nxt_lunar is None:
            import datetime as _dt
            d0 = _dt.date(s.getYear(), s.getMonth(), s.getDay()) + _dt.timedelta(days=1)
            nxt_lunar = Solar.fromYmd(d0.year, d0.month, d0.day).getLunar()
        p['日'] = nxt_lunar.getDayInGanZhi()
    return p

def build_pillar_detail(gz, rigan=None):
    """单柱详情: 干支/五行/阴阳/藏干/十神/纳音/空亡/长生"""
    g, z = gz[0], gz[1]
    self_stage = shier_changsheng(g, z)
    d = {
        '干支': gz,
        '天干': g, '干五行': gan_wuxing(g), '干阴阳': gan_yinyang(g),
        '地支': z, '支五行': zhi_wuxing(z), '支阴阳': zhi_yinyang(z), '生肖': zhi_shengxiao(z),
        '藏干': zhi_canggan(z), '藏干五行': zhi_canggan_wuxing(z),
        '纳音': nayin(gz), '纳音简': nayin_jian(gz),
        '空亡': xunkong(gz),
        '长生': self_stage,
        '自坐长生': self_stage,
    }
    if rigan:
        d['十神(天干)'] = shishen(rigan, g)
        d['十神(藏干)'] = [shishen(rigan, cg) for cg in d['藏干']]
        d['日主地势'] = shier_changsheng(rigan, z)
    return d

def build_chart(y, m, d, h, mi=0, s=0, sex=1, **kwargs):
    """
    输入公历生日, 输出完整命盘 dict.
    sex: 1=男 0=女 (用于大运顺逆)
    """
    original_dt = _dt.datetime(y, m, d, h, mi, s)
    chart_dt = original_dt
    solar_info = None
    longitude = kwargs.get('longitude')
    if longitude is not None:
        from .solar_time import true_solar_time
        nh, nm, total, lon_d, eot = true_solar_time(y, m, d, h, mi, longitude)
        corrected_minutes = round(h * 60 + mi + total)
        chart_dt = _dt.datetime(y, m, d) + _dt.timedelta(minutes=corrected_minutes, seconds=s)
        solar_info = {
            '原时间': f'{h:02d}:{mi:02d}',
            '校正日期': chart_dt.strftime('%Y-%m-%d'),
            '校正后': f'{nh:02d}:{nm:02d}',
            '总校正分': round(total, 1),
            '经度差': round(lon_d, 1),
            '均时差': round(eot, 1),
        }

    solar = Solar.fromYmdHms(chart_dt.year, chart_dt.month, chart_dt.day,
                             chart_dt.hour, chart_dt.minute, chart_dt.second)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    pillars = pillars_from_lunar_wzs(lunar, chart_dt.hour)
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
    result['身宫'] = ec.getShenGong() if hasattr(ec, 'getShenGong') else None
    result['纳音'] = {}

    # 格局喜忌 (身强弱/格局/用神/忌神/调候/旺衰)
    from .geju import strength_analysis, judge_geju, pick_yongshen
    result['旺衰'] = strength_analysis(pillars, rigan)
    result['格局'] = judge_geju(pillars, rigan, result['旺衰'])
    result['用神'] = pick_yongshen(pillars, rigan, result['旺衰'], pillars['月'][1])
    for name, gz in pillars.items():
        result['四柱'][name] = build_pillar_detail(gz, rigan)
        result['纳音'][name] = nayin(gz)

    # 大运
    try:
        yun = ec.getYun(1 if sex else 0)
        result['起运'] = yun.getStartYear() if hasattr(yun, 'getStartYear') else None
        start_solar = yun.getStartSolar() if hasattr(yun, 'getStartSolar') else None
        result['起运详情'] = {
            '年': yun.getStartYear() if hasattr(yun, 'getStartYear') else None,
            '月': yun.getStartMonth() if hasattr(yun, 'getStartMonth') else None,
            '日': yun.getStartDay() if hasattr(yun, 'getStartDay') else None,
            '时': yun.getStartHour() if hasattr(yun, 'getStartHour') else None,
            '交运时间': start_solar.toYmdHms()[:16] if start_solar else None,
            '算法': 'lunar-python sect=1',
        }
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

    # 流年 (从当前年份起5年)
    result['流年'] = []
    current_year = _dt.date.today().year
    for i in range(5):
        y2 = current_year + i
        gz_year = JIAZI[(y2 - 4) % 60]
        result['流年'].append({'年': y2, '干支': gz_year})

    # 断语分析
    from .analysis import full_analysis
    result['分析'] = full_analysis(pillars, rigan)

    # 月令断语 (《穷通宝鉴》120条, 标题格式对齐 app: 甲日寅月)
    try:
        from .yueling import yueling_duanyu
        mt, mb = yueling_duanyu(rigan, pillars['月'][1])
        if mb:
            result['分析'].insert(0, ('月令断语·' + mt, mb))
    except Exception:
        pass

    # 日主性格 (《滴天髓》十干)
    try:
        import json as _json
        _p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'knowledge', '性格断语_滴天髓.json')
        with open(_p, encoding='utf-8') as _f:
            _x = _json.load(_f)
        if rigan in _x.get('shigan_xingge', {}):
            result['分析'].insert(0, ('日主性格·' + rigan + '日(' + _x['shigan_xingge'][rigan][:12] + '…)', _x['shigan_xingge'][rigan]))
    except Exception:
        pass

    # 刑冲合会
    from .hehui import analyze as analyze_xchh
    result['刑冲合会'] = analyze_xchh(pillars)

    # 大运/流年断语
    from .dayun_duanyu import chart_dy_analysis
    result['运年断语'] = chart_dy_analysis(rigan, result.get('大运', []), result.get('流年', []))

    # 《三命通会》古籍参照 (论大运/论太岁)
    try:
        from .dayun_zhengyi import dayun_zhengyi, taisui_zhengyi
        zhengyi = []
        for dy in result.get('大运', [])[1:]:
            if dy.get('干支'):
                zhengyi.append({'干支': dy['干支'], '断语': dayun_zhengyi(rigan, dy['干支'])})
        result['运年断语']['三命通会'] = zhengyi
        result['运年断语']['三命通会流年'] = [
            {'干支': ln['干支'], '断语': taisui_zhengyi(rigan, ln['干支'])}
            for ln in result.get('流年', [])]
    except Exception:
        pass

    result['真太阳时'] = solar_info

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
    for attr, label in (('藏干', '藏干'), ('十神(天干)', '十神'), ('纳音', '纳音'), ('空亡', '空亡'),
                        ('日主地势', '地势'), ('自坐长生', '自坐')):
        vals = []
        for p in ('年', '月', '日', '时'):
            v = chart['四柱'][p][attr]
            if attr == '藏干': v = ''.join(v)
            if attr == '十神(天干)': v = str(v)
            if attr == '空亡': v = ''.join(v)
            vals.append(f'{v:^9s}')
        L.append(f'{label:4s} ' + ''.join(vals))
    L.append('-' * 42)
    L.append(f"日主: {chart['日主']}  胎元: {chart['胎元']}  命宫: {chart['命宫']}  身宫: {chart['身宫']}")
    # 格局喜忌
    if chart.get('格局'):
        w = chart['旺衰']
        g = chart['格局']
        y = chart['用神']
        L.append(f"旺衰: {w['身强弱']} (评分 {w['评分']})  月令{w['月令状态']}  得令{w['得分项']['得令']:+.0f}/得地{w['得分项']['得地']:+.1f}/得势{w['得分项']['得势']:+.1f}")
        L.append(f"格局: {g[0]} ({g[2]})")
        L.append(f"用神: {'/'.join(y['用神'])}  忌神: {'/'.join(y['忌神']) if y['忌神'] else '—'}  调候: {''.join(y['调候干'])}  ({y['方法']})")
        if y.get('病') or y.get('通关'):
            L.append(f"病药: 病={y.get('病') or '—'} 药={y.get('药') or '—'}  通关: {y.get('通关') or '—'}")
    if chart.get('起运') is not None:
        start = chart.get('起运详情') or {}
        precision = f"{start.get('年', 0)}年{start.get('月', 0)}个月{start.get('日', 0)}天{start.get('时', 0)}小时"
        L.append(f"起运: {precision}  交运: {start.get('交运时间') or '—'}")
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
        if chart['运年断语'].get('三命通会'):
            L.append('运年断语 (《三命通会》古籍参照):')
            for d in chart['运年断语']['三命通会'][:4]:
                L.append(f"  {d['干支']}运: {d['断语'][:60]}")
            for ln in chart['运年断语']['三命通会流年'][:2]:
                L.append(f"  {ln['干支']}年: {ln['断语'][:60]}")
    L.append('=' * 42)
    return '\n'.join(L)

if __name__ == '__main__':
    chart = build_chart(1990, 5, 15, 10, 30, 0, sex=1)
    print(render_text(chart))
