# -*- coding: utf-8 -*-
"""把「观象」两个字从字体转成矢量路径，生成可移植的图标 SVG。

为什么要转路径：SVG 里直接写 <text font-family="Noto Serif SC"> 依赖本机字体，
换台机器就会回退成别的字形。这里用 fontTools 取字形轮廓，产出纯 <path>，
任何环境渲染结果一致。

用法（在 desktop/ 目录）：
    python tools/make_wordmark.py
需要：pip install fonttools；字体 C:/Windows/Fonts/NotoSerifSC-VF.ttf（思源宋体，OFL-1.1）。
生成：ui/brand/icon.svg（完整版）、ui/brand/icon-small.svg（16/24px 单字版）

小尺寸为什么要换单字：两个汉字在 16px 里每字只有约 6×7 像素，笔画不足 1px，
必然糊成一个白团。16/24px 改用「观」单字（笔画少、结构清楚），32px 起恢复「观象」二字——
这是图标设计里的常规做法（知乎=知、小红书=书）。
"""

from __future__ import annotations

import pathlib
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONT_PATH = pathlib.Path("C:/Windows/Fonts/NotoSerifSC-VF.ttf")
WEIGHT = 700
OUT = pathlib.Path("ui/brand")
CANVAS = 512
RADIUS = 112
CLAY = "#D97757"
PAPER = "#F9F9F7"


def glyph_path(font, glyph_name: str) -> tuple[str, tuple[float, float, float, float]]:
    """返回 (SVG path, 墨迹包围盒 xMin yMin xMax yMax)，坐标系为字体单位、y 向上。"""
    glyph_set = font.getGlyphSet()
    pen = SVGPathPen(glyph_set, ntos=lambda v: f"{v:.2f}")
    glyph_set[glyph_name].draw(pen)
    bounds_pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(bounds_pen)
    if bounds_pen.bounds is None:
        raise SystemExit(f"字形 {glyph_name} 没有轮廓")
    return pen.getCommands(), bounds_pen.bounds


def build_svg(chars: str, ink_width: float, gap: float, label: str = "") -> str:
    font = TTFont(FONT_PATH)
    font = instantiateVariableFont(font, {"wght": WEIGHT})
    cmap = font.getBestCmap()
    glyphs = []
    for ch in chars:
        name = cmap[ord(ch)]
        d, (x0, y0, x1, y1) = glyph_path(font, name)
        glyphs.append({"d": d, "bbox": (x0, y0, x1, y1), "w": x1 - x0})

    # 用同一字号：以最宽的字形定标，其余按比例（保持字体原有宽度差异）
    widest = max(g["w"] for g in glyphs)
    scale = (ink_width - gap * (len(glyphs) - 1)) / sum(g["w"] for g in glyphs)
    total = sum(g["w"] * scale for g in glyphs) + gap * (len(glyphs) - 1)

    # 基线对齐后，按合并墨迹的垂直中心做光学居中
    top = max(g["bbox"][3] for g in glyphs) * scale
    bottom = min(g["bbox"][1] for g in glyphs) * scale
    baseline = CANVAS / 2 + (top + bottom) / 2

    x = (CANVAS - total) / 2
    parts = []
    for g in glyphs:
        x0 = g["bbox"][0]
        tx = x - x0 * scale
        parts.append(f'<path transform="translate({tx:.2f} {baseline:.2f}) scale({scale:.5f} {-scale:.5f})" d="{g["d"]}"/>')
        x += g["w"] * scale + gap

    _ = widest
    label = label or chars
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-label="{label}">
  <title>{label} · 字标</title>
  <!-- 「观象」二字由思源宋体（Noto Serif SC，SIL OFL-1.1）第 {WEIGHT} 字重转曲而来，
       本文件只含路径，不含字体文件，渲染不依赖本机字体。 -->
  <rect width="512" height="512" rx="{RADIUS}" fill="{CLAY}"/>
  <g fill="{PAPER}">
    {chr(10).join("    " + p for p in parts).strip()}
  </g>
</svg>
'''


def _set_weight(weight: int) -> None:
    global WEIGHT
    WEIGHT = weight


def main() -> int:
    if not FONT_PATH.exists():
        print(f"缺少字体: {FONT_PATH}（思源宋体 Noto Serif SC）", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    # 完整版：左右各留 ~10% 内边距
    (OUT / "icon.svg").write_text(build_svg("观象", ink_width=410, gap=14), encoding="utf-8")
    # 小尺寸版：16/24px 用单字「观」，保证在 6-9 像素的字号下仍可辨认
    mw_weight = 800
    _set_weight(mw_weight)
    (OUT / "icon-small.svg").write_text(build_svg("观", ink_width=340, gap=0, label="观（16/24px 单字版）"), encoding="utf-8")
    print("已生成 ui/brand/icon.svg 与 ui/brand/icon-small.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
