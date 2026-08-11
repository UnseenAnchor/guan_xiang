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
        self.assertEqual(html.count('href="/styles_v3.css"'), 1)
        self.assertEqual(html.count('src="/app_v3.js"'), 1)

    def test_default_server_delegates_to_current_handler(self):
        from web_server import BaziRequestHandler
        from web_server_v3 import BaziV3RequestHandler

        self.assertIs(BaziRequestHandler, BaziV3RequestHandler)


if __name__ == "__main__":
    unittest.main()
