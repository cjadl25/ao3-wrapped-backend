#!/usr/bin/env bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Setting Playwright browsers path..."
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.playwright

echo "Installing Chromium for Playwright..."
playwright install --with-deps chromium

echo "Build completed successfully!"
