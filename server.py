import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import api  # 既存のAPIモジュールをインポート

# 環境変数からポート番号を取得
PORT = int(os.environ.get("PORT", 8000))

# 既存のFastAPIアプリを取得
app = api.app

# 静的ファイルを提供するためのマウント
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

# CORSミドルウェアを追加（既存の設定を保持）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限するべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    # サーバー起動
    uvicorn.run("server:app", host="0.0.0.0", port=PORT)
