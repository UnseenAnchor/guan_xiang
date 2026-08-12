# -*- coding: utf-8 -*-
import pathlib
import re
import subprocess
import unittest


ROOT = pathlib.Path(__file__).parents[1]


class FrontendContractTests(unittest.TestCase):
    def test_static_dom_contains_all_render_targets(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        scripts = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        html_ids = set(re.findall(r'\bid="([^"]+)"', html))
        queried_ids = set(re.findall(r"querySelector\('#([^']+)'\)", scripts))
        dynamic_ids = {"knowledge-panel"}
        self.assertEqual(queried_ids - html_ids - dynamic_ids, set())

    def test_true_solar_time_is_opt_in(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        tag = re.search(r'<input id="use-true-solar-time"[^>]*>', html)
        self.assertIsNotNone(tag)
        self.assertNotIn("checked", tag.group(0))
        self.assertIn('id="annual-track"', html)

    def test_default_page_loads_canonical_assets_once(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('href="/styles.css?v=0.4.2"'), 1)
        self.assertEqual(html.count('src="/app.js?v=0.4.2"'), 1)
        self.assertEqual(html.count('?v=0.4.2'), 2)

    def test_solar_and_lunar_dates_share_the_same_three_part_structure(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertEqual(html.count('class="date-grid"'), 2)
        for field_id in (
            "solar-year", "solar-month", "solar-day",
            "lunar-year", "lunar-month", "lunar-day",
        ):
            self.assertIn(f'id="{field_id}"', html)
        self.assertNotIn('id="birth-date"', html)
        self.assertNotIn('type="date"', html)
        self.assertIn("function updateSolarDays(defaultDay)", script)
        self.assertIn("date: solarDateValue()", script)

    def test_calendar_height_and_true_solar_copy_are_structurally_stable(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        styles = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertEqual(html.count('class="calendar-support'), 2)
        self.assertRegex(styles, r"\.calendar-support\s*\{[^}]*height:\s*22px")
        self.assertIn('class="true-solar-setting"', html)
        self.assertRegex(styles, r"\.true-solar-note\s*\{[^}]*margin:\s*10px 0 0 30px")

    def test_default_server_exports_canonical_contract(self):
        import web_server

        for name in ("BaziRequestHandler", "build_chart_from_request", "build_almanac_from_date"):
            self.assertTrue(hasattr(web_server, name))

    def test_location_status_follows_true_solar_time_opt_in(self):
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("function syncLocationStatus()", script)
        self.assertIn("真太阳时未启用", script)
        self.assertIn("trueSolarInput.checked ? '将用于真太阳时校正'", script)
        self.assertIn("selectedPlace = null;\n  syncLocationStatus();", script)
        self.assertIn("trueSolarInput.addEventListener('change', () => {\n  syncLocationStatus();", script)

    def test_chart_has_section_navigation_and_experimental_panel(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('href="#section-experimental"', html)
        self.assertIn('id="experimental-root"', html)
        self.assertRegex(html, r'<details class="experimental-panel">')
        self.assertIn("旺衰与取用推演", html)
        self.assertIn("本部分基于综合规则分析，不同命理流派可能存在不同结论。", html)
        self.assertNotIn("实验模型 / EXPERIMENT", html)
        self.assertIn("renderExperimental(chart['实验推演'])", script)
        self.assertIn("模型建议关注", script)

    def test_chart_directory_orders_facts_before_research_content(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('aria-label="命盘目录"', html)
        self.assertIn('<nav class="chart-nav" aria-label="命盘目录">', html)
        self.assertIn("排盘事实", html)
        self.assertIn("参研内容", html)
        self.assertLess(html.index('id="section-relations"'), html.index('id="section-cycles"'))
        self.assertLess(html.index('id="section-references"'), html.index('class="research-zone'))
        self.assertLess(html.index('id="section-experimental"'), html.index('id="section-ai"'))
        self.assertIn("function initializeChapterNav()", script)
        self.assertIn("event.preventDefault()", script)
        self.assertIn("target.scrollIntoView({ behavior: 'smooth', block: 'start' })", script)
        self.assertIn("history.replaceState(null, '', link.hash)", script)
        self.assertIn("main { overflow-x: clip; }", styles)
        self.assertNotIn("main { overflow: hidden; }", styles)

    def test_chart_has_ai_explanation_and_local_exports(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('id="generate-explanation"', html)
        self.assertNotIn("不含姓名", html)
        self.assertIn("出生日期、出生地和坐标不会发送", html)
        self.assertRegex(html, r'<details class="ai-explanation" id="ai-explanation" hidden open>')
        self.assertIn('id="ai-explanation-body"', html)
        self.assertNotIn("DeepSeek", html)
        self.assertNotIn("DeepSeek", script)
        self.assertEqual(html.count('data-export='), 2)
        self.assertIn("/api/chart-explanation", script)
        self.assertIn("function renderMarkdownInline(value)", script)
        self.assertIn("function renderSafeMarkdown(markdown)", script)
        self.assertIn("markdown-table-wrap", script)
        self.assertIn("const ordered =", script)
        self.assertIn("<blockquote>", script)
        self.assertIn(".ai-explanation:not([open])", styles)
        self.assertIn("function buildChartMarkdown(chart)", script)
        self.assertIn("function buildChartText(chart)", script)
        self.assertIn("async function readJsonResponse(response)", script)

    def test_almanac_page_contains_every_script_render_target(self):
        html = (ROOT / "web" / "almanac.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "almanac.js").read_text(encoding="utf-8")
        html_ids = set(re.findall(r'\bid="([^"]+)"', html))
        queried_ids = set(re.findall(r"querySelector\('#([^']+)'\)", script))
        self.assertEqual(queried_ids - html_ids, set())
        self.assertIn('href="/almanac" aria-current="page"', html)
        self.assertEqual(html.count('src="/almanac.js?v=0.4.2"'), 1)
        self.assertEqual(html.count('href="/almanac.css?v=0.4.2"'), 1)
        self.assertEqual(html.count('?v=0.4.2'), 3)

    def test_repository_has_no_retired_version_layers(self):
        retired = [
            ROOT / "web_server_v2.py", ROOT / "web_server_v3.py",
            ROOT / "web" / "app_v2.js", ROOT / "web" / "app_v3.js",
            ROOT / "web" / "styles_v2.css", ROOT / "web" / "styles_v3.css",
            ROOT / "web" / "index_v2.html",
            ROOT / "scripts" / "build_locations_v2.py",
            ROOT / "scripts" / "build_locations_v3.py",
            ROOT / "scripts" / "validate_cybz_knowledge.py",
            ROOT / "WEB-README.md", ROOT / "WEB-V2.md", ROOT / "WEB-V3.md",
        ]
        self.assertEqual([str(path.relative_to(ROOT)) for path in retired if path.exists()], [])
        self.assertEqual([path.name for path in ROOT.glob("web_server*.py")], ["web_server.py"])
        tracked = subprocess.check_output(
            ["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8"
        ).splitlines()
        self.assertNotIn("AGENTS.md", tracked)

    def test_real_service_config_is_ignored(self):
        ignored = subprocess.run(
            ["git", "check-ignore", "config.json"], cwd=ROOT,
            text=True, encoding="utf-8", capture_output=True,
        )
        self.assertEqual(ignored.returncode, 0)
        tracked = subprocess.check_output(
            ["git", "ls-files", "config.json"], cwd=ROOT, text=True, encoding="utf-8"
        ).strip()
        self.assertEqual(tracked, "")


if __name__ == "__main__":
    unittest.main()
