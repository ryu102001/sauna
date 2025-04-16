import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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

# 静的ファイルのディレクトリ
static_dir = "frontend/build"

# APIの全エンドポイントをサブパスにマウント
# 注意: 既存のAPIアプリを適応させるために必要な処理
api.app.root_path = "/api"

# ルートパスへのリクエストをindex.htmlにリダイレクト
@app.get("/")
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return JSONResponse({"error": "index.html not found"}, status_code=404)

# 静的ファイルを提供
@app.get("/{path:path}")
async def read_static(path: str):
    # APIパスはスキップ
    if path.startswith("api/"):
        return await api.app(Request(scope={"type": "http", "path": path[4:]}))

    # 静的ファイルのパスを構築
    file_path = os.path.join(static_dir, path)

    # ファイルが存在するか確認
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)

    # ファイルが存在しない場合はindex.htmlを返す（SPA対応）
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    # それでもダメなら404
    return JSONResponse({"error": f"File not found: {path}"}, status_code=404)

# APIエンドポイントを追加
@app.get("/api/{path:path}")
async def api_endpoint(path: str, request: Request):
    # APIリクエストを既存のAPIアプリに転送
    return await api.app(request)

if __name__ == "__main__":
    # サーバー起動
    print(f"Starting server on port {PORT}")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT)
