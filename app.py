from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import time
from typing import List
import pandas as pd
import json

app = FastAPI()

# CORSを有効化
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイル設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# アップロードディレクトリの作成
os.makedirs("uploads", exist_ok=True)

@app.get("/")
async def read_root():
    """メインページを返す"""
    with open("templates/simple-upload.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/test")
async def test_api():
    """API動作確認用のテストエンドポイント"""
    return JSONResponse(
        content={"status": "成功", "message": "APIは正常に動作しています"},
        headers={"Content-Type": "application/json"}
    )

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...), data_type: str = Form(default="auto")):
    """CSVファイルをアップロードして処理する"""
    try:
        # ファイル読み込み
        contents = await file.read()

        # 保存用のパスを生成
        timestamp = int(time.time())
        filename = file.filename
        output_path = f"uploads/{data_type}_{timestamp}_{filename}"

        # ファイルを保存
        with open(output_path, "wb") as f:
            f.write(contents)

        # ファイル情報を返す
        return JSONResponse(
            content={
                "status": "成功",
                "filename": filename,
                "data_type": data_type,
                "saved_path": output_path,
                "size": len(contents),
                "message": "ファイルがアップロードされました"
            },
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        # エラー処理
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)},
            headers={"Content-Type": "application/json"}
        )

@app.post("/api/upload-multiple")
async def upload_multiple_csv(files: List[UploadFile] = File(...), data_type: str = Form(default="auto")):
    """複数のCSVファイルをアップロードして処理する"""
    try:
        results = []
        timestamp = int(time.time())

        for file in files:
            try:
                # ファイル読み込み
                contents = await file.read()
                filename = file.filename

                # 保存用のパスを生成
                output_path = f"uploads/{data_type}_{timestamp}_{filename}"

                # ファイルを保存
                with open(output_path, "wb") as f:
                    f.write(contents)

                # 結果を追加
                results.append({
                    "filename": filename,
                    "data_type": data_type,
                    "saved_path": output_path,
                    "size": len(contents),
                    "status": "成功"
                })
            except Exception as e:
                # このファイルのエラー
                results.append({
                    "filename": file.filename,
                    "status": "エラー",
                    "detail": str(e)
                })

        # 全体の結果を返す
        return JSONResponse(
            content={
                "status": "処理完了",
                "total": len(files),
                "success": len([r for r in results if r["status"] == "成功"]),
                "errors": len([r for r in results if r["status"] == "エラー"]),
                "results": results
            },
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        # 全体のエラー処理
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)},
            headers={"Content-Type": "application/json"}
        )

# サーバー起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
