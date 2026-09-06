"""Browser regression checks for the three approved UI readability fixes.

Optional dev tooling: Python Playwright + an existing Chrome (or --browser PATH).
No production dependency, downloads, persistent browser profile or external fonts
are required. Use --online-fonts for visual review with the page's web fonts.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web_server import BaziRequestHandler


class QuietHandler(BaziRequestHandler):
    def log_message(self, fmt, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Existing Chromium-compatible browser executable")
    parser.add_argument("--screenshots", type=Path, help="Optional evidence output directory")
    parser.add_argument("--online-fonts", action="store_true")
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        parser.error("Optional check requires Python playwright and an existing browser; no dependencies were installed.")

    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, passed, evidence):
        checks.append({"check": name, "passed": bool(passed), "evidence": evidence})
        print(f"{'PASS' if passed else 'FAIL'} {name}: {evidence}")

    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as p:
            launch = {"executable_path": args.browser} if args.browser else {"channel": "chrome"}
            browser = p.chromium.launch(headless=True, **launch)
            try:
                for width, height in [(1440, 1000), (768, 1024), (390, 844), (320, 844)]:
                    context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
                    try:
                        if not args.online_fonts:
                            context.route("**/*", lambda route: route.continue_() if route.request.url.startswith(base + "/") else route.abort())
                        page = context.new_page()
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        page.goto(base + "/", wait_until="domcontentloaded")
                        page.wait_for_function("document.querySelector('#solar-day').options.length === 31")
                        if args.online_fonts:
                            page.evaluate("async () => { await Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 8000))]); }")
                        with page.expect_response(lambda r: r.url.endswith("/api/chart")) as response:
                            page.locator('.submit-button').click()
                        check(f"{width}: chart response", response.value.status == 200, response.value.status)
                        page.locator('#result-shell').wait_for(state='visible')
                        page.wait_for_function("[...document.querySelectorAll('.reveal')].every(e => +getComputedStyle(e).opacity > .99)")
                        # Let pending scroll/reveal frames settle without altering product styles.
                        page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
                        if args.screenshots:
                            page.locator('#result-shell').scroll_into_view_if_needed()
                            page.screenshot(path=str(args.screenshots / f'{width}-result.png'), animations='disabled')
                            page.locator('.summary-grid').screenshot(path=str(args.screenshots / f'{width}-summary.png'), animations='disabled')

                        bounds = page.evaluate("""() => {
                          const rect = s => {const r=document.querySelector(s).getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,right:r.right,bottom:r.bottom};};
                          return {nav:rect('.chart-nav'),content:rect('.result-content'),summary:rect('.summary-grid'),elements:rect('#section-elements'),
                            cards:[...document.querySelectorAll('.summary-grid > article')].map(e=>({left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right})),
                            position:getComputedStyle(document.querySelector('.chart-nav')).position};
                        }""")
                        if width <= 680:
                            check(f"{width}: directory above content", bounds['nav']['bottom'] <= bounds['content']['y'] + 1 and bounds['position'] == 'static', bounds)
                            check(f"{width}: full-width content", abs(bounds['content']['w'] - (width - 24)) < 1, bounds['content']['w'])
                        else:
                            check(f"{width}: sidebar retained", bounds['nav']['right'] < bounds['content']['x'], bounds)
                        check(f"{width}: summary contained", all(c['left'] >= bounds['content']['x'] - 1 and c['right'] <= bounds['content']['right'] + 1 for c in bounds['cards']), bounds['cards'])

                        chart = page.locator('#pillar-chart')
                        overflow = chart.evaluate("e => getComputedStyle(e).overflowX")
                        if width <= 960:
                            check(f"{width}: scroll available", overflow in ('auto', 'scroll'), overflow)
                            chart.evaluate("e => e.scrollTo({left:e.scrollWidth, behavior:'instant'})")
                            visible = chart.evaluate("e => e.querySelector('.pillar:last-child').getBoundingClientRect().right <= e.getBoundingClientRect().right + 1")
                            check(f"{width}: last pillar reachable", visible, chart.evaluate("e => ({left:e.scrollLeft,client:e.clientWidth,scroll:e.scrollWidth})"))
                            if args.screenshots:
                                chart.screenshot(path=str(args.screenshots / f'{width}-last-pillar.png'), animations='disabled')
                            chart.evaluate("e => e.scrollTo({left:0,behavior:'instant'})")
                            chart.focus()
                            page.keyboard.press('ArrowRight')
                            try:
                                page.wait_for_function("document.querySelector('#pillar-chart').scrollLeft > 0", timeout=1500)
                                moved = True
                            except Exception:
                                moved = False
                            check(f"{width}: keyboard scroll", moved and chart.evaluate("e => e === document.activeElement"), chart.evaluate("e => ({left:e.scrollLeft,tabIndex:e.tabIndex})"))
                            check(f"{width}: named focusable region", chart.get_attribute('role') == 'region' and chart.get_attribute('aria-label') == '四柱命盘', chart.get_attribute('aria-label'))
                            check(f"{width}: visible scroll focus", chart.evaluate("e => getComputedStyle(e).outlineStyle !== 'none'"), chart.evaluate("e => getComputedStyle(e).outline"))
                        else:
                            check(f"{width}: all pillars visible", chart.evaluate("e => [...e.querySelectorAll('.pillar')].every(p=>p.getBoundingClientRect().left>=e.getBoundingClientRect().left && p.getBoundingClientRect().right<=e.getBoundingClientRect().right)"), overflow)

                        rows = page.locator('.element-row-complete').evaluate_all("els=>els.map(e=>({total:Number(e.querySelector('strong').textContent),bar:parseFloat(e.querySelector('i').dataset.width)}))")
                        check(f"{width}: original counts and ratios", [r['total'] for r in rows] == [1,6,5,6,1] and all(abs(r['bar']-r['total']/6*100)<.001 for r in rows), rows)
                        caption = page.locator('#section-elements .card-caption').inner_text()
                        check(f"{width}: count explanation", '数量对比' in page.locator('.element-table-head').inner_text() and '条长按本盘最大计数归一化' in caption and '不等同于身强弱或喜用神判断' in caption, caption)

                        links = page.locator('.chart-nav a')
                        check(f"{width}: eight chapter links", links.count() == 8, links.count())
                        # Native Tab from the last chapter should reach exports in DOM order.
                        links.last.focus()
                        page.keyboard.press('Tab')
                        check(f"{width}: directory keyboard exit", page.evaluate("document.activeElement.dataset.export") == 'md', page.evaluate("document.activeElement.outerHTML"))
                        link = page.locator('.chart-nav a[href="#section-elements"]')
                        link.focus()
                        check(f"{width}: visible nav focus", link.evaluate("e => getComputedStyle(e).outlineStyle !== 'none'"), link.evaluate("e => getComputedStyle(e).outline"))
                        # Observe the real navigation call while still forwarding it to the browser.
                        page.evaluate("""() => {
                          const el = document.querySelector('#section-elements');
                          const scroll = el.scrollIntoView.bind(el);
                          el.scrollIntoView = options => {window.__navScrollOptions=options; scroll(options);};
                        }""")
                        link.press('Enter')
                        page.wait_for_function("location.hash === '#section-elements'")
                        check(f"{width}: reduced-motion navigation", page.evaluate("window.__navScrollOptions.behavior") in ('auto','instant'), page.evaluate("window.__navScrollOptions"))
                        # ARIA-current is managed by the existing observer as well as link activation.
                        page.wait_for_function("document.querySelector('.chart-nav a[href=\"#section-elements\"]').getAttribute('aria-current') === 'location'")
                        check(f"{width}: active chapter", link.get_attribute('aria-current') == 'location', link.get_attribute('class'))
                        for fmt in ['md','txt']:
                            with page.expect_download() as download:
                                page.locator(f'[data-export="{fmt}"]').click()
                            check(f"{width}: local {fmt} export", download.value.suggested_filename.endswith('.'+fmt), download.value.suggested_filename)
                        check(f"{width}: no page errors", not errors, errors)
                    finally:
                        context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if args.screenshots:
            (args.screenshots / 'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    failed = sum(not row['passed'] for row in checks)
    print(f"\n{len(checks)-failed}/{len(checks)} checks passed")
    return int(failed > 0)


if __name__ == '__main__':
    raise SystemExit(main())
