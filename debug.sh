#!/bin/bash

DEBUG=true
RENDER=true
export PORT=8000

print() {
  echo "$(date +"%Y-%m-%d %H:%M:%S") $1"
}

print "=== デバッグモードでサーバー起動 ==="
print "現在のディレクトリ: $(pwd)"
print "ディレクトリ内容:"
ls -la

print "環境変数:"
env | grep -E 'PORT|PYTHON|RENDER'

print "静的ファイルの確認:"
find . -name "*.html" | head -n 10

print "サーバー起動中..."
python3 -u server.py
