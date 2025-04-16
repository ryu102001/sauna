#!/usr/bin/env bash
set -e

echo "=== Current directory ==="
pwd
ls -la

echo "=== Installing Python dependencies ==="
python3 -m pip install -r requirements.txt --no-cache-dir

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

# 静的ファイルが正しく配置されていることを確認
echo "=== Checking for static files ==="
if [ ! -f "build/static/js/main.js" ] && [ ! -d "build/static/js" ]; then
  echo "WARNING: JS files not found in expected location. Creating directories..."
  mkdir -p build/static/js
  mkdir -p build/static/css
fi

# logo192.pngとlogo512.pngが正しく配置されていることを確認
for file in "logo192.png" "logo512.png" "favicon.ico"; do
  if [ ! -f "build/$file" ]; then
    echo "WARNING: $file not found. Copying from public directory..."
    cp -f "public/$file" "build/$file" || echo "Failed to copy $file"
  fi
done

cd ..

echo "=== Verifying directory structure ==="
find frontend/build -type f | head -n 20

echo "=== Build completed successfully ==="
