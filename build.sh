#!/bin/bash
set -e
echo "Installation des dépendances..."
pip install --upgrade pip
pip install greenlet==3.0.3 --only-binary=:all:
pip install -r requirements.txt --only-binary=:all: || pip install -r requirements.txt
echo "Installation de Playwright Chromium..."
python -m playwright install chromium
python -m playwright install-deps chromium
echo "Build terminé !"
