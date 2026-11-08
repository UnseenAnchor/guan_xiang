# -*- coding: utf-8 -*-
"""从品牌矢量图渲染多尺寸 PNG 与 favicon.ico（可复现，无需设计工具）。

用法（在 desktop/ 目录）：
    python tools/make_brand.py

依赖：Python Playwright（本机 Edge 即可）+ Pillow。
产物（写入 ui/brand/ 与 ui/favicon.ico）：
    icon-16.png / icon-24.png / icon-32.png / icon-48.png / icon-64.png
    icon-128.png / icon-180.png / icon-256.png / icon-512.png
    favicon.ico（内嵌 16/24/32/48/64/128/256）
    ../../ui/favicon.ico 由服务端根路径直接提供
"""

from __future__ import annotations

import io
import pathlib
import struct
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRAND = ROOT / "ui" / "brand"
SVG = BRAND / "icon.svg"
SVG_SMALL = BRAND / "icon-small.svg"
SIZES = [16, 24, 32, 48, 64, 128, 180, 192, 256, 512]
# 16/24px 用简化版（加宽爻线间距），其余用完整版
SMALL_SIZES = {16, 24}
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def write_ico(frames: list[tuple[int, bytes]], path: pathlib.Path) -> None:
    """写多帧 ICO（PNG 压缩帧，Vista+ 全支持），每帧内容独立，互不缩放。"""
    count = len(frames)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + 16 * count
    entries, blobs = [], []
    for size, blob in frames:
        entries.append(struct.pack(
            "<BBBBHHII",
            0 if size >= 256 else size,  # 256 用 0 表示
            0 if size >= 256 else size,
            0, 0, 1, 32, len(blob), offset,
        ))
        blobs.append(blob)
        offset += len(blob)
    path.write_bytes(header + b"".join(entries) + b"".join(blobs))


def render(page, size: int, out: pathlib.Path, svg_markup: str) -> None:
    """把矢量源内联进页面再截图：file:// 子资源会被 Chromium 拦截，内联最稳。"""
    page.set_viewport_size({"width": size, "height": size})
    page.set_content(
        f"""<!doctype html><html><head><meta charset="utf-8"><style>
        html,body{{margin:0;padding:0;background:transparent;overflow:hidden}}
        svg{{display:block;width:{size}px;height:{size}px}}
        </style></head><body>{svg_markup}</body></html>""",
        wait_until="load",
    )
    page.wait_for_timeout(120)
    page.locator("svg").screenshot(path=str(out), omit_background=True)


def main() -> int:
    if not SVG.exists():
        print(f"缺少矢量源: {SVG}")
        return 1
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge")
        page = browser.new_page(device_scale_factor=1)
        full_markup = SVG.read_text(encoding="utf-8")
        small_markup = SVG_SMALL.read_text(encoding="utf-8")
        for size in SIZES:
            target = BRAND / f"icon-{size}.png"
            render(page, size, target, small_markup if size in SMALL_SIZES else full_markup)
            print(f"  {target.name}  {target.stat().st_size // 1024} KB")
        browser.close()

    # 组装多尺寸 ICO：每帧都用该尺寸专属的 PNG（不能用 Pillow 的 sizes=，它只会缩放最后一张图，
    # 会把 16/24px 的单字版替换成 256px 的缩小版）。
    ico_path = BRAND / "icon.ico"
    frames = []
    for size in ICO_SIZES:
        buf = io.BytesIO()
        Image.open(BRAND / f"icon-{size}.png").convert("RGBA").save(buf, format="PNG")
        frames.append((size, buf.getvalue()))
    write_ico(frames, ico_path)
    # 根路径 favicon.ico：浏览器/应用窗口默认会请求 /favicon.ico
    root_ico = ROOT / "ui" / "favicon.ico"
    root_ico.write_bytes(ico_path.read_bytes())
    print(f"  {ico_path.name} {ico_path.stat().st_size // 1024} KB（{len(ICO_SIZES)} 个尺寸）")
    print(f"  ui/favicon.ico 已同步")
    return 0


if __name__ == "__main__":
    sys.exit(main())
