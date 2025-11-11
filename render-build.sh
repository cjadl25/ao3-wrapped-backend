#!/usr/bin/env bash
set -e

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Installing Playwright Chromium ==="
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.playwright
python -m playwright install chromium

echo "=== Build Complete ✅ ==="
