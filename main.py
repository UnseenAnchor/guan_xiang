# -*- coding: utf-8 -*-
"""八字排盘 CLI: python main.py 1990 5 15 10 30 [1|0] [--lon 经度]"""
import argparse
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bazi.engine import build_chart, render_text

def main():
    parser = argparse.ArgumentParser(description='八字排盘')
    parser.add_argument('year', type=int)
    parser.add_argument('month', type=int)
    parser.add_argument('day', type=int)
    parser.add_argument('hour', type=int)
    parser.add_argument('minute', type=int)
    parser.add_argument('sex', type=int, nargs='?', default=1, choices=(0, 1), help='1男/0女')
    parser.add_argument('--lon', type=float, help='出生地经度；不提供则不校正真太阳时')
    args = parser.parse_args()
    kwargs = {'longitude': args.lon} if args.lon is not None else {}
    chart = build_chart(args.year, args.month, args.day, args.hour, args.minute,
                        0, sex=args.sex, **kwargs)
    print(render_text(chart))

if __name__ == '__main__':
    main()
