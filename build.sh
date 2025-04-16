#!/usr/bin/env bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Creating uploads directory ==="
mkdir -p uploads

echo "=== Building frontend ==="
cd frontend
npm install
SKIP_PREFLIGHT_CHECK=true ESLINT_NO_DEV_ERRORS=true CI=false REACT_APP_API_URL="" npm run build
cd ..

echo "=== Setting up static files ==="
# frontend/buildの中身を確認
ls -la frontend/build

echo "=== Build completed successfully ==="
