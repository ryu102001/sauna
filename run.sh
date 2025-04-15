#!/bin/bash

# 必要なディレクトリを作成
mkdir -p uploads

# バックエンドの依存関係をインストール
echo "Installing backend dependencies..."
pip3 install fastapi uvicorn python-multipart pandas numpy

# フロントエンドのセットアップ
echo "Setting up frontend..."
cd frontend
npm install
cd ..

# バックエンドを起動（バックグラウンドで）
echo "Starting backend server..."
python3 api.py &
BACKEND_PID=$!

# フロントエンドを起動
echo "Starting frontend development server..."
cd frontend
npm start

# プロセスをクリーンアップ
kill $BACKEND_PID
