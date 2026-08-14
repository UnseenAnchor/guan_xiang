# -*- coding: utf-8 -*-
"""
solar_time.py — 真太阳时校正 (对齐 app TZhenTaiYangShi)
标准公式: 真太阳时 = 平太阳时 + 经度时差 + 均时差
"""
import math
import calendar
from datetime import date


def _equation_of_time(y, m, d):
    """均时差（分钟）。采用 NOAA/Spencer 日角近似公式。"""
    day_of_year = date(y, m, d).timetuple().tm_yday
    days = 366 if calendar.isleap(y) else 365
    gamma = 2 * math.pi / days * (day_of_year - 1)
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )


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
