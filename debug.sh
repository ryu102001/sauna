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

print "アップロードディレクトリ作成:"
mkdir -p uploads
chmod 777 uploads
ls -la uploads

print "環境変数:"
env | grep -E 'PORT|PYTHON|RENDER'

print "Python依存関係確認:"
pip list | grep -E 'fastapi|uvicorn|pandas|starlette|multipart'

print "インストールされているPythonエンコーディング:"
python3 -c "import encodings; print(sorted([x for x in dir(encodings) if not x.startswith('_')]))"

print "静的ファイルの確認:"
find . -name "*.html" | head -n 10

print "CSVテストファイル作成:"
echo "date,room,occupancy_rate
2023-01-01,Room1,85.5
2023-01-02,Room2,76.2
2023-01-03,Room3,92.0" > uploads/test_occupancy.csv

print "Pythonのエンコーディング確認:"
python3 -c "
import pandas as pd
try:
    df = pd.read_csv('uploads/test_occupancy.csv')
    print('テストCSV読み込み成功:', df.columns.tolist())
except Exception as e:
    print('テストCSV読み込み失敗:', str(e))
"

print "サーバー起動中..."
python3 -u server.py
