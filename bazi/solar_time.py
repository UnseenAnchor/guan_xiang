# -*- coding: utf-8 -*-
"""
solar_time.py — 真太阳时校正 (对齐 app TZhenTaiYangShi)
标准公式: 真太阳时 = 平太阳时 + 经度时差 + 均时差
"""
import math
from datetime import datetime


def _equation_of_time(y, m, d):
    """均时差 (分钟)。基于天文近似公式, 精度 ±1 分钟, 对排盘足够"""
    # 儒略日
    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    JD = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    n = JD - 2451545.0  # J2000 起天数
    # 太阳平黄经
    L = 280.460 + 0.9856474 * n
    # 太阳平近点角
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    # 黄经 (含主要摄动)
    lam = math.radians((L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360)
    # 赤经
    eps = math.radians(23.439 - 0.0000004 * n)
    RA = math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam)))
    if RA < 0:
        RA += 360
    RA /= 15.0  # 转小时
    # 平恒星时 (格林尼治)
    GMST = (18.697374558 + 24.06570982441908 * (n - 0.5)) % 24
    # 均时差 (小时): 平太阳时 - 真太阳时
    eot = (GMST - RA) % 24
    if eot > 12:
        eot -= 24
    return eot * 60.0  # 分钟


def true_solar_time(y, m, d, hour, minute, longitude, tz_hour=8):
    """
    真太阳时校正.
    longitude: 出生地经度 (东经为正, 如北京 116.4)
    tz_hour: 时区 (中国东八区 = 8)
    returns: (校正后时, 校正后分, 时差说明)
    """
    # 1. 经度时差: 每度 4 分钟
    lon_diff = (longitude - tz_hour * 15.0) * 4.0  # 分钟
    # 2. 均时差
    eot = _equation_of_time(y, m, d)
    # 3. 总校正
    total = lon_diff + eot
    minutes = hour * 60 + minute + total
    minutes = round(minutes)
    nh, nm = divmod(minutes, 60)
    nh %= 24
    return nh, nm, total, lon_diff, eot


if __name__ == '__main__':
    # 测试: 北京 (东经116.4) 1990-05-15 10:30 平太阳时
    nh, nm, total, lon, eot = true_solar_time(1990, 5, 15, 10, 30, 116.4)
    print(f'北京 10:30 → 真太阳时 {nh:02d}:{nm:02d} (总校正 {total:+.1f}分 = 经度{lon:+.1f} + 均时差{eot:+.1f})')
