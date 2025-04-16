import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import api  # 既存のAPIモジュールをインポート

# 環境変数からポート番号を取得
PORT = int(os.environ.get("PORT", 8000))

# 新しいFastAPIアプリを作成
app = FastAPI()

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限するべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIの全エンドポイントをサブパスにマウント
app.mount("/api", api.app)

# 静的ファイルのディレクトリ
static_dir = "frontend/build"

# ルートパスへのリクエストをindex.htmlにリダイレクト
@app.get("/")
async def read_index():
    return FileResponse(f"{static_dir}/index.html")

# その他のファイルパスを静的ファイルとして提供
app.mount("/", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    # サーバー起動
    uvicorn.run("server:app", host="0.0.0.0", port=PORT)
