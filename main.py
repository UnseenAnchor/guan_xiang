# -*- coding: utf-8 -*-
"""八字排盘 CLI: python main.py 1990 5 15 10 30 [1|0]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bazi.engine import build_chart, render_text

def main():
    if len(sys.argv) < 6:
        print('用法: python main.py 年 月 日 时 分 [性别(1男/0女)]')
        print('示例: python main.py 1990 5 15 10 30 1')
        return
    y, m, d, h, mi = map(int, sys.argv[1:6])
    sex = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    chart = build_chart(y, m, d, h, mi, 0, sex=sex)
    print(render_text(chart))

if __name__ == '__main__':
    main()
