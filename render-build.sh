#!/usr/bin/env bash
set -e  # stop on first error

echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set Playwright path inside project (avoids root permission issues)
export PLAYWRIGHT_BROWSERS_PATH=.playwright

echo "Installing Playwright Chromium with all dependencies..."
playwright install --with-deps chromium

echo "Build completed successfully!"
