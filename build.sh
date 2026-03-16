#!/bin/bash
# Installation des dépendances Playwright (navigateur Chromium)
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
