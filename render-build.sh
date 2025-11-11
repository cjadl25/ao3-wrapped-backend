#!/usr/bin/env bash
set -e  # Exit on error

echo "Installing Python dependencies..."
pip install --user -r requirements.txt

echo "Setting Playwright browsers path..."
export PLAYWRIGHT_BROWSERS_PATH=$HOME/.playwright

echo "Installing Chromium for Playwright locally..."
~/.local/bin/playwright install --with-deps chromium

echo "Build completed successfully!"
