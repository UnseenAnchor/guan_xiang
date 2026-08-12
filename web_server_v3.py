# -*- coding: utf-8 -*-
"""Bazi web v3: complete element/pillar/dayun presentation plus knowledge loading."""

from __future__ import annotations

import os
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

import web_server_v2 as base
from bazi.engine import build_chart as core_build_chart
from bazi.knowledge_loader import enrich_chart, load_knowledge


def enriched_build_chart(*args, **kwargs):
    return enrich_chart(core_build_chart(*args, **kwargs))


base.build_chart = enriched_build_chart


class BaziV3RequestHandler(base.BaziV2RequestHandler):
    def do_GET(self):
        route = urlparse(self.path).path
        page = {"/": "index.html", "/almanac": "almanac.html", "/almanac/": "almanac.html"}.get(route)
        if page:
            source = os.path.join(base.WEB_ROOT, page)
            with open(source, encoding="utf-8") as file:
                html = file.read()
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


def main():
    host = os.environ.get("BAZI_HOST", "127.0.0.1")
    port = int(os.environ.get("BAZI_PORT", "8787"))
    knowledge = load_knowledge()
    print(
        "知识库已载入："
        f"{len(knowledge['structured'])} 个结构分类，"
        f"{len(knowledge['classified'])} 个知识分类，"
        f"{len(knowledge['pure'])} 条短语，"
        f"{len(knowledge['keys'])} 个词键"
    )
    server = ThreadingHTTPServer((host, port), BaziV3RequestHandler)
    print(f"八字排盘网页 v3 已启动：http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
