# -*- coding: utf-8 -*-
"""A tiny dependency-free web server for the bazi-engine experience."""

from __future__ import annotations

import json
import os
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from bazi.engine import build_chart


ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_ROOT = os.path.join(ROOT, "web")


class BaziRequestHandler(SimpleHTTPRequestHandler):
    """Serve the static experience and expose the local chart engine as JSON."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)

    def log_message(self, fmt, *args):
        print("[bazi-web] " + fmt % args)

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json({"ok": True, "engine": "bazi-engine"})
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/chart":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise ValueError("请求内容为空或过大")
            data = json.loads(self.rfile.read(length).decode("utf-8"))

            date_value = str(data.get("date", ""))
            time_value = str(data.get("time", ""))
            born = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
            if not 1900 <= born.year <= 2099:
                raise ValueError("目前支持 1900—2099 年的出生日期")

            sex = int(data.get("sex", 1))
            if sex not in (0, 1):
                raise ValueError("性别参数无效")

            longitude = float(data.get("longitude", 116.4))
            if not -180 <= longitude <= 180:
                raise ValueError("经度应在 -180 到 180 之间")

            chart = build_chart(
                born.year,
                born.month,
                born.day,
                born.hour,
                born.minute,
                0,
                sex=sex,
                longitude=longitude,
            )
            self._send_json({"ok": True, "chart": chart})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # Keep the browser response useful during local development.
            self._send_json(
                {"ok": False, "error": f"排盘失败：{exc}"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )


def main():
    host = os.environ.get("BAZI_HOST", "127.0.0.1")
    port = int(os.environ.get("BAZI_PORT", "8787"))
    server = ThreadingHTTPServer((host, port), BaziRequestHandler)
    print(f"八字排盘网页已启动：http://{host}:{port}")
    print("按 Ctrl+C 停止服务")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
