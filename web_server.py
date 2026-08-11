# -*- coding: utf-8 -*-
"""Canonical web entrypoint; legacy command now runs the current V3 application."""

from web_server_v3 import BaziV3RequestHandler, main


BaziRequestHandler = BaziV3RequestHandler


if __name__ == "__main__":
    main()
