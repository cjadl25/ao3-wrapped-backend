#!/usr/bin/env bash
set -e

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Installing Playwright Browsers Locally (NO ROOT) ==="
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.playwright
# Chromium only, no root needed
npx playwright install chromium --with-deps

echo "=== Build Complete ✅ ==="
