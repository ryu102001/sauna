#!/usr/bin/env bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Creating uploads directory ==="
mkdir -p uploads

echo "=== Building frontend ==="
cd frontend
npm install --silent
SKIP_PREFLIGHT_CHECK=true ESLINT_NO_DEV_ERRORS=true CI=false npm run build

echo "=== Setting up static files ==="
# frontend/buildディレクトリの内容を確認
ls -la build
# index.htmlが存在することを確認
if [ ! -f "build/index.html" ]; then
  echo "ERROR: build/index.html not found!"
  exit 1
fi
cd ..

echo "=== Verifying directory structure ==="
pwd
find frontend/build -type f | head -n 10

echo "=== Build completed successfully ==="
