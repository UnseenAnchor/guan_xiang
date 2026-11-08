# -*- coding: utf-8 -*-
"""观象桌面版 UI 取证脚本（只读，不改产品代码）。

前置：先启动 exe（--serve 模式），例如
    build/观象.exe --serve --port 8799 --data-dir .testdata
然后运行：
    python tools/verify_ui.py --base http://127.0.0.1:8799 --out evidence

覆盖：四柱渲染、保存到历史、重启读取、农历模式、深浅色、手机断点、
无外网请求、无登录入口、控制台无报错，并输出截图。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

from playwright.sync_api import sync_playwright

EXPECTED = {
    "solar": {"pillars": "庚午辛巳庚辰辛巳", "date": "1990-05-15", "time": "10:30", "sex": 1},
}

ROOT = pathlib.Path(__file__).resolve().parents[1]


def api(base: str, path: str) -> dict:
    with urllib.request.urlopen(base + path) as response:
        return json.loads(response.read().decode())


def pillar_text(page) -> str:
    return page.eval_on_selector_all(
        ".pillar-card .pillar-char",
        "nodes => nodes.map(n => [...n.querySelectorAll('span')].map(s => s.textContent.trim()).join('')).join('')",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8799")
    parser.add_argument("--out", default=str(ROOT / "evidence"))
    args = parser.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    console_errors: list[str] = []
    requests: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge")
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))
        page.on("request", lambda req: requests.append(req.url))

        page.goto(args.base + "/", wait_until="load")
        page.wait_for_selector("#chart-form")

        # 无登录入口
        if page.locator("input[type=password]").count():
            failures.append("界面出现密码输入框（不应存在登录）")
        login_controls = page.locator("button, a, input[type=submit]").filter(has_text="登录").count()
        if login_controls:
            failures.append("界面出现登录按钮")
        health = api(args.base, "/api/health")
        if health.get("login") is not False or health.get("offline") is not True:
            failures.append(f"健康检查未声明离线/免登录: {health}")

        # 填表并排盘
        page.fill("#chart-name", "张三")
        page.fill("#solar-year", EXPECTED["solar"]["date"][:4])
        page.fill("#solar-month", str(int(EXPECTED["solar"]["date"][5:7])))
        page.fill("#solar-day", str(int(EXPECTED["solar"]["date"][8:])))
        page.fill("#birth-time", EXPECTED["solar"]["time"])
        page.click("#submit-btn")
        page.wait_for_selector(".pillar-card", timeout=10000)

        got = pillar_text(page)
        if got != EXPECTED["solar"]["pillars"]:
            failures.append(f"四柱渲染不一致: {got} != {EXPECTED['solar']['pillars']}")
        if page.locator(".pillar-card").count() != 4:
            failures.append("四柱卡片数量不是 4")
        if page.locator(".dayun-card").count() < 9:
            failures.append("大运卡片数量异常")
        if page.locator(".accordion").count() < 3:
            failures.append("参照断语折叠区缺失")
        metrics = page.inner_text(".metric-row")
        for keyword in ("旺衰", "格局", "用神"):
            if keyword not in metrics:
                failures.append(f"结构分析缺少 {keyword}")

        page.wait_for_timeout(700)
        page.screenshot(path=str(out / "ui-light-1440.png"))
        page.locator("section.section", has_text="神煞").first.screenshot(path=str(out / "ui-shensha.png"))
        page.locator("section.section", has_text="大运").first.screenshot(path=str(out / "ui-dayun.png"))
        page.locator("section.section", has_text="结构分析").first.screenshot(path=str(out / "ui-structure.png"))

        # 深色模式
        page.click("#theme-seg label:has(input[value=dark])")
        page.wait_for_timeout(350)
        mode = page.eval_on_selector("html", "el => el.dataset.mode")
        if mode != "dark":
            failures.append(f"深色模式未生效: {mode}")
        page.screenshot(path=str(out / "ui-dark-1440.png"))
        page.click("#theme-seg label:has(input[value=light])")
        page.wait_for_timeout(250)

        # 保存到历史
        before = api(args.base, "/api/history")["items"]
        page.click("#save-chart")
        page.wait_for_selector(".toast")
        page.wait_for_timeout(600)
        after = api(args.base, "/api/history")["items"]
        if len(after) != len(before) + 1:
            failures.append(f"保存后历史条数未增加: {len(before)} -> {len(after)}")
        saved = [item for item in after if item["title"] == "张三"]
        if not saved:
            failures.append("历史列表没有找到『张三』")
        elif saved[0]["pillars"] != EXPECTED["solar"]["pillars"]:
            failures.append(f"历史记录干支不一致: {saved[0]['pillars']}")

        # 重载后从历史读取
        page.reload(wait_until="load")
        page.wait_for_selector(".history-item")
        page.locator(".history-item", has_text="张三").first.click()
        page.wait_for_selector(".pillar-card")
        if pillar_text(page) != EXPECTED["solar"]["pillars"]:
            failures.append("从历史读取后四柱渲染不一致")
        page.screenshot(path=str(out / "ui-history-1440.png"))

        # 农历模式
        page.click("#calendar-seg label:has(input[value=lunar])")
        page.wait_for_timeout(350)
        options = page.eval_on_selector_all("#lunar-month option", "nodes => nodes.map(n => n.textContent)")
        if not options or "闰" not in "".join(options) and len(options) < 12:
            failures.append(f"农历月份选项异常: {options[:3]}")

        # 真太阳时开关受经度约束
        disabled = page.eval_on_selector("#true-solar", "el => el.disabled")
        if not disabled:
            failures.append("未填经度时真太阳时开关应禁用")
        page.click("#extra-toggle")
        page.wait_for_timeout(250)
        page.fill("#longitude", "116.4")
        enabled = page.eval_on_selector("#true-solar", "el => !el.disabled")
        if not enabled:
            failures.append("填写经度后真太阳时开关应可用")
        page.click(".switch-track")
        if not page.eval_on_selector("#true-solar", "el => el.checked"):
            failures.append("点击开关后真太阳时未勾选")
        page.click("#submit-btn")
        page.wait_for_timeout(800)
        if page.locator(".pillar-card").count() != 4:
            failures.append("真太阳时排盘未渲染四柱")

        # 手机断点
        page.set_viewport_size({"width": 390, "height": 844})
        page.reload(wait_until="load")
        page.wait_for_selector("#sidebar-toggle")
        page.screenshot(path=str(out / "ui-mobile-390.png"))
        page.click("#sidebar-toggle")
        page.wait_for_timeout(350)
        opened = page.evaluate("document.body.classList.contains('sidebar-open')")
        if not opened:
            failures.append("手机端侧栏开关无效")
        page.screenshot(path=str(out / "ui-mobile-drawer-390.png"))

        # 无外网请求
        external = [url for url in requests if not url.startswith(args.base) and not url.startswith("data:")]
        if external:
            failures.append(f"出现外网/非本机请求: {external[:5]}")

        context.close()
        browser.close()

    report = {
        "base": args.base,
        "console_errors": console_errors,
        "request_count": len(requests),
        "external_requests": [u for u in requests if not u.startswith(args.base) and not u.startswith("data:")],
        "failures": failures,
        "screenshots": sorted(p.name for p in out.glob("ui-*.png")),
    }
    if console_errors:
        failures.append(f"控制台报错: {console_errors[:3]}")
        report["failures"] = failures
    (out / "ui-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
