# -*- coding: utf-8 -*-
"""Bazi web experience v2: solar/lunar input and private offline place search."""

from __future__ import annotations

import json
import os
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from lunar_python import Lunar, LunarYear

from bazi.engine import build_chart


ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_ROOT = os.path.join(ROOT, "web")


def lunar_month_info(year):
    lunar_year = LunarYear.fromYear(year)
    return {
        "leap_month": lunar_year.getLeapMonth(),
        "months": [
            {"month": month.getMonth(), "days": month.getDayCount()}
            for month in lunar_year.getMonthsInYear()
        ],
    }


def parse_birth(data):
    calendar = str(data.get("calendar", "solar"))
    time_value = str(data.get("time", ""))
    parsed_time = datetime.strptime(time_value, "%H:%M")

    if calendar == "solar":
        date_value = str(data.get("date", ""))
        born = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
        original = f"{born.year}年{born.month}月{born.day}日 {time_value}"
        return born, "公历", original
    if calendar != "lunar":
        raise ValueError("历法参数无效")

    year = int(data.get("lunar_year"))
    month = int(data.get("lunar_month"))
    day = int(data.get("lunar_day"))
    is_leap = bool(data.get("lunar_leap", False))
    if not 1900 <= year <= 2099 or not 1 <= month <= 12 or not 1 <= day <= 30:
        raise ValueError("农历日期超出支持范围")

    info = lunar_month_info(year)
    signed_month = -month if is_leap else month
    month_record = next((item for item in info["months"] if item["month"] == signed_month), None)
    if not month_record:
        if is_leap:
            raise ValueError(f"农历 {year} 年没有闰{month}月")
        raise ValueError("农历月份无效")
    if day > month_record["days"]:
        raise ValueError(f"该农历月份只有 {month_record['days']} 天")

    lunar = Lunar.fromYmdHms(year, signed_month, day, parsed_time.hour, parsed_time.minute, 0)
    solar = lunar.getSolar()
    born = datetime(
        solar.getYear(), solar.getMonth(), solar.getDay(),
        solar.getHour(), solar.getMinute(), solar.getSecond(),
    )
    leap_label = "闰" if is_leap else ""
    return born, "农历", f"{year}年{leap_label}{month}月{day}日 {time_value}"


class BaziV2RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)

    def log_message(self, fmt, *args):
        print("[bazi-web-v2] " + fmt % args)

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({"ok": True, "engine": "bazi-engine", "version": 2})
            return
        if parsed.path == "/api/lunar-year":
            try:
                year = int(parse_qs(parsed.query).get("year", [""])[0])
                if not 1900 <= year <= 2099:
                    raise ValueError("年份应在 1900—2099 之间")
                self._send_json({"ok": True, **lunar_month_info(year)})
            except (ValueError, TypeError) as exc:
                self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if parsed.path == "/":
            self.path = "/index_v2.html"
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
            born, calendar_label, original_date = parse_birth(data)
            if not 1900 <= born.year <= 2099:
                raise ValueError("目前支持 1900—2099 年的出生日期")

            sex = int(data.get("sex", 1))
            if sex not in (0, 1):
                raise ValueError("性别参数无效")

            raw_longitude = data.get("longitude", "")
            raw_latitude = data.get("latitude", "")
            has_location = raw_longitude not in (None, "")
            longitude = float(raw_longitude) if has_location else 116.4
            latitude = float(raw_latitude) if raw_latitude not in (None, "") else None
            if not -180 <= longitude <= 180:
                raise ValueError("经度应在 -180 到 180 之间")
            if latitude is not None and not -90 <= latitude <= 90:
                raise ValueError("纬度应在 -90 到 90 之间")

            chart = build_chart(
                born.year, born.month, born.day, born.hour, born.minute, 0,
                sex=sex, longitude=longitude,
            )
            chart["输入"]["历法"] = calendar_label
            chart["输入"]["原始日期"] = original_date
            chart["出生地"] = None
            if has_location:
                chart["出生地"] = {
                    "名称": str(data.get("location_name", "")).strip() or "手动坐标",
                    "经度": longitude,
                    "纬度": latitude,
                }
            else:
                chart["真太阳时"] = None
            self._send_json({"ok": True, "chart": chart})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"ok": False, "error": f"排盘失败：{exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)


def main():
    host = os.environ.get("BAZI_HOST", "127.0.0.1")
    port = int(os.environ.get("BAZI_PORT", "8787"))
    server = ThreadingHTTPServer((host, port), BaziV2RequestHandler)
    print(f"八字排盘网页 v2 已启动：http://{host}:{port}")
    print("按 Ctrl+C 停止服务")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
