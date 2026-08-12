# -*- coding: utf-8 -*-
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).parents[1]


class FrontendContractTests(unittest.TestCase):
    def test_static_dom_contains_all_render_targets(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        scripts = "\n".join(
            (ROOT / "web" / name).read_text(encoding="utf-8")
            for name in ("app_v2.js", "app_v3.js")
        )
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

    def test_default_page_loads_current_v3_assets_once(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('href="/styles_v3.css?v=0.3.0"'), 1)
        self.assertEqual(html.count('src="/app_v3.js?v=0.3.0"'), 1)
        self.assertEqual(html.count('?v=0.3.0'), 5)

    def test_default_server_delegates_to_current_handler(self):
        from web_server import BaziRequestHandler
        from web_server_v3 import BaziV3RequestHandler

        self.assertIs(BaziRequestHandler, BaziV3RequestHandler)

    def test_location_status_follows_true_solar_time_opt_in(self):
        script = (ROOT / "web" / "app_v2.js").read_text(encoding="utf-8")
        self.assertIn("function syncLocationStatus()", script)
        self.assertIn("真太阳时未启用", script)
        self.assertIn("trueSolarInput.checked ? '将用于真太阳时校正'", script)
        self.assertIn("selectedPlace = null;\n  syncLocationStatus();", script)
        self.assertIn("trueSolarInput.addEventListener('change', () => {\n  syncLocationStatus();", script)

    def test_chart_has_section_navigation_and_experimental_panel(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "app_v3.js").read_text(encoding="utf-8")
        self.assertIn('href="#section-experimental"', html)
        self.assertIn('id="experimental-root"', html)
        self.assertRegex(html, r'<details class="experimental-panel">')
        self.assertIn("renderExperimental(chart['实验推演'])", script)
        self.assertIn("模型建议关注", script)

    def test_almanac_page_contains_every_script_render_target(self):
        html = (ROOT / "web" / "almanac.html").read_text(encoding="utf-8")
        script = (ROOT / "web" / "almanac.js").read_text(encoding="utf-8")
        html_ids = set(re.findall(r'\bid="([^"]+)"', html))
        queried_ids = set(re.findall(r"querySelector\('#([^']+)'\)", script))
        self.assertEqual(queried_ids - html_ids, set())
        self.assertIn('href="/almanac" aria-current="page"', html)
        self.assertEqual(html.count('src="/almanac.js?v=0.3.0"'), 1)
        self.assertEqual(html.count('href="/almanac.css?v=0.3.0"'), 1)
        self.assertEqual(html.count('?v=0.3.0'), 3)


if __name__ == "__main__":
    unittest.main()
