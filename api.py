from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from io import StringIO
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import traceback
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uuid
import random
import re
import time

app = FastAPI(title="サウナ分析ダッシュボードAPI")

# グローバル例外ハンドラの設定
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTPExceptionをハンドリングし、一貫したJSON形式でレスポンスを返す"""
    print(f"HTTPException: {exc.detail}, status_code={exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "エラー", "detail": str(exc.detail)},
        headers={"Content-Type": "application/json"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """リクエスト検証エラーをハンドリングし、一貫したJSON形式でレスポンスを返す"""
    error_details = str(exc)
    print(f"バリデーションエラー: {error_details}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "エラー",
            "detail": "リクエストデータの検証に失敗しました",
            "errors": error_details
        },
        headers={"Content-Type": "application/json"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """すべての未処理例外をキャッチし、一貫したJSON形式でレスポンスを返す"""
    error_details = str(exc)
    trace = traceback.format_exc()
    print(f"予期せぬエラー: {error_details}")
    print(f"詳細トレース: {trace}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "エラー",
            "detail": "サーバー内部エラーが発生しました",
            "message": error_details
        },
        headers={"Content-Type": "application/json"}
    )

# CORSを有効にして、Reactからのリクエストを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# アップロードされたCSVファイルを保存するディレクトリ
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# データモデル
class DashboardData(BaseModel):
    labels: Dict[str, List[str]]
    metrics: Dict[str, Any] = {}
    members: Dict[str, Any] = {}
    utilization: Dict[str, Any] = {}
    competitors: Dict[str, Any] = {}
    finance: Dict[str, Any] = {}

# グローバルインスタンス
dashboard_data = DashboardData(
    labels={
        "months": [f"2023-{i:02d}" for i in range(1, 13)] + [f"2024-{i:02d}" for i in range(1, 7)],
        "daysOfWeek": ["月", "火", "水", "木", "金", "土", "日"],
        "timeSlots": ["9-12時", "12-15時", "15-18時", "18-21時", "21-24時"],
        "regions": ["大阪府", "兵庫県", "京都府", "奈良県", "滋賀県", "和歌山県", "その他"],
        "roomNames": ["Room1", "Room2", "Room3"],
        "competitorNames": ["HAAAVE.sauna", "KUDOCHI sauna", "MENTE", "M's Sauna", "SAUNA Pod 槃", "SAUNA OOO OSAKA", "大阪サウナ DESSE"],
        "ageGroups": ["20代", "30代", "40代", "50代", "~19歳", "60歳~"],
        "genders": ["男性", "女性"]
    }
)

# ダミーデータ生成関数
def generate_dummy_data():
    # 基本データ構造
    data = {
        "labels": {
            "months": ["2023-05", "2023-06", "2023-07", "2023-08", "2023-09", "2023-10", "2023-11", "2023-12",
                      "2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
            "daysOfWeek": ["月", "火", "水", "木", "金", "土", "日"],
            "timeSlots": ["9-12時", "12-15時", "15-18時", "18-21時", "21-24時"],
            "regions": ["大阪市北区", "大阪市中央区", "大阪市西区", "大阪市浪速区", "大阪市天王寺区", "大阪市淀川区", "その他"],
            "roomNames": ["Room1", "Room2", "Room3"],
            "competitorNames": [
                "HAAAVE.sauna", "KUDOCHI sauna", "MENTE", "M's Sauna",
                "SAUNA Pod 槃", "SAUNA OOO OSAKA", "大阪サウナ DESSE"
            ],
            "ageGroups": ["20代", "30代", "40代", "50代", "~19歳", "60歳~"],
            "genders": ["男性", "女性"]
        },
        "members": {
            "total": 100,
            "active": 78,
            "trial": 45,
            "visitor": 132,
            "joinRate": 78.0,
            "churnRate": 3.2,
            "genderDistribution": [
                {"name": "男性", "value": 50},
                {"name": "女性", "value": 50}
            ],
            "ageDistribution": [
                {"name": "~19歳", "value": 5},
                {"name": "20代", "value": 35},
                {"name": "30代", "value": 30},
                {"name": "40代", "value": 20},
                {"name": "50代", "value": 7},
                {"name": "60歳~", "value": 3}
            ],
            "regionDistribution": [
                {"name": "大阪市北区", "value": 30},
                {"name": "大阪市中央区", "value": 25},
                {"name": "大阪市西区", "value": 15},
                {"name": "大阪市浪速区", "value": 10},
                {"name": "大阪市天王寺区", "value": 8},
                {"name": "大阪市淀川区", "value": 7},
                {"name": "その他", "value": 5}
            ],
            "membershipTrend": []
        },
        "utilization": {
            "rooms": {
                "Room1": {"average": 75.2},
                "Room2": {"average": 68.3},
                "Room3": {"average": 82.7}
            },
            "byDayOfWeek": [],
            "byTimeSlot": [],
            "byMonth": []
        },
        "competitors": {
            "pricing": [
                {"name": "HAAAVE.sauna", "価格": 3500},
                {"name": "KUDOCHI sauna", "価格": 3800},
                {"name": "MENTE", "価格": 4000},
                {"name": "M's Sauna", "価格": 3200},
                {"name": "SAUNA Pod 槃", "価格": 3600},
                {"name": "SAUNA OOO OSAKA", "価格": 4200},
                {"name": "大阪サウナ DESSE", "価格": 3300}
            ],
            "details": [
                {
                    "施設名": "HAAAVE.sauna",
                    "所在地": "大阪市北区",
                    "形態": "個室",
                    "料金": "3,500円/時",
                    "ルーム数": "3",
                    "水風呂": "あり",
                    "男女混浴": "可",
                    "開業年": "2023"
                },
                {
                    "施設名": "KUDOCHI sauna",
                    "所在地": "大阪市中央区",
                    "形態": "個室",
                    "料金": "3,800円/時",
                    "ルーム数": "4",
                    "水風呂": "あり",
                    "男女混浴": "可",
                    "開業年": "2022"
                },
                {
                    "施設名": "MENTE",
                    "所在地": "大阪市西区",
                    "形態": "個室",
                    "料金": "4,000円/時",
                    "ルーム数": "2",
                    "水風呂": "あり",
                    "男女混浴": "可",
                    "開業年": "2023"
                },
                {
                    "施設名": "M's Sauna",
                    "所在地": "大阪市天王寺区",
                    "形態": "個室",
                    "料金": "3,200円/時",
                    "ルーム数": "2",
                    "水風呂": "なし",
                    "男女混浴": "可",
                    "開業年": "2021"
                },
                {
                    "施設名": "SAUNA Pod 槃",
                    "所在地": "大阪市北区",
                    "形態": "カプセル",
                    "料金": "3,600円/時",
                    "ルーム数": "8",
                    "水風呂": "あり",
                    "男女混浴": "不可",
                    "開業年": "2022"
                },
                {
                    "施設名": "SAUNA OOO OSAKA",
                    "所在地": "大阪市中央区",
                    "形態": "個室",
                    "料金": "4,200円/時",
                    "ルーム数": "5",
                    "水風呂": "あり",
                    "男女混浴": "可",
                    "開業年": "2022"
                },
                {
                    "施設名": "大阪サウナ DESSE",
                    "所在地": "大阪市浪速区",
                    "形態": "個室",
                    "料金": "3,300円/時",
                    "ルーム数": "3",
                    "水風呂": "あり",
                    "男女混浴": "可",
                    "開業年": "2023"
                }
            ],
            "regionDistribution": [
                {"name": "大阪市北区", "value": 3},
                {"name": "大阪市中央区", "value": 5},
                {"name": "大阪市西区", "value": 2},
                {"name": "大阪市浪速区", "value": 1},
                {"name": "大阪市天王寺区", "value": 2},
                {"name": "大阪市淀川区", "value": 0},
                {"name": "その他", "value": 1}
            ]
        },
        "finance": {
            "summary": {
                "latestMonth": "2024-05",
                "monthlySales": 1250000,
                "monthlyProfit": 375000,
                "profitRate": 30.0
            },
            "monthlySalesTrend": [],
            "salesByType": [
                {"name": "会員", "value": 850000},
                {"name": "ビジター", "value": 250000},
                {"name": "トライアル", "value": 150000}
            ],
            "salesByRoom": [
                {"name": "Room1", "value": 450000},
                {"name": "Room2", "value": 350000},
                {"name": "Room3", "value": 450000}
            ]
        }
    }

    # 月次データのトレンド生成
    for month in data["labels"]["months"]:
        # 会員トレンド
        data["members"]["membershipTrend"].append({
            "name": month,
            "会員": random.randint(60, 100),
            "体験者": random.randint(20, 50),
            "ビジター": random.randint(40, 140)
        })

        # 月別稼働率
        data["utilization"]["byMonth"].append({
            "name": month,
            "Room1": round(random.uniform(60, 90), 1),
            "Room2": round(random.uniform(55, 85), 1),
            "Room3": round(random.uniform(70, 95), 1)
        })

        # 月別売上
        sales = random.randint(900000, 1300000)
        cost = int(sales * 0.7)
        profit = sales - cost

        data["finance"]["monthlySalesTrend"].append({
            "name": month,
            "売上": sales,
            "利益": profit
        })

    # 曜日別稼働率
    for day in data["labels"]["daysOfWeek"]:
        data["utilization"]["byDayOfWeek"].append({
            "name": day,
            "Room1": round(random.uniform(60, 90), 1),
            "Room2": round(random.uniform(55, 85), 1),
            "Room3": round(random.uniform(70, 95), 1)
        })

    # 時間帯別稼働率
    for time_slot in data["labels"]["timeSlots"]:
        data["utilization"]["byTimeSlot"].append({
            "name": time_slot,
            "Room1": round(random.uniform(60, 90), 1),
            "Room2": round(random.uniform(55, 85), 1),
            "Room3": round(random.uniform(70, 95), 1)
        })

    return data

@app.get("/")
def read_root():
    return JSONResponse(
        content={"message": "サウナ分析ダッシュボードAPI", "version": "1.0.0"},
        headers={"Content-Type": "application/json"}
    )

@app.get("/api/dashboard")
async def get_dashboard_data():
    """ダッシュボードデータを取得するエンドポイント"""
    try:
        # 直接辞書として返す
        data_dict = {
            "labels": dict(dashboard_data.labels),
            "metrics": dict(dashboard_data.metrics),
            "members": dict(dashboard_data.members),
            "utilization": dict(dashboard_data.utilization),
            "competitors": dict(dashboard_data.competitors),
            "finance": dict(dashboard_data.finance)
        }
        # nullや空の辞書を削除
        for key in list(data_dict.keys()):
            if data_dict[key] is None or data_dict[key] == {}:
                data_dict[key] = {}

        return JSONResponse(
            content=data_dict,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        print(f"ダッシュボードデータの取得中にエラーが発生しました: {str(e)}")
        # エラー時はダミーデータを返す
        return JSONResponse(
            content=generate_dummy_data(),
            headers={"Content-Type": "application/json"}
        )

@app.put("/api/upload-csv")
async def upload_csv_put(file: UploadFile = File(...), data_type: str = Form(default="auto")):
    """CSVファイルをアップロードして処理する (PUTメソッド)"""
    try:
        print(f"PUT CSV上アップロード開始: file={file.filename}, data_type={data_type}")
        result = await process_uploaded_csv(file, data_type)
        print(f"PUT CSV処理結果: {result}")

        # この部分が重要: JSONResponseを返す場合、content_typeを明示的に設定
        if isinstance(result, JSONResponse):
            return result
        else:
            # 通常の辞書の場合はJSONResponseでラップ
            return JSONResponse(
                content=result,
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                }
            )
    except Exception as e:
        print(f"アップロードエラー(PUT): {str(e)}")
        print(f"トレースバック: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)},
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
            }
        )

@app.post("/api/upload-csv")
async def upload_csv_post(file: UploadFile = File(...), data_type: str = Form(default="auto")):
    """CSVファイルをアップロードして処理する (POSTメソッド)"""
    try:
        print(f"POST CSV上アップロード開始: file={file.filename}, data_type={data_type}")
        result = await process_uploaded_csv(file, data_type)
        print(f"POST CSV処理結果: {result}")

        # この部分が重要: JSONResponseを返す場合、content_typeを明示的に設定
        if isinstance(result, JSONResponse):
            return result
        else:
            # 通常の辞書の場合はJSONResponseでラップ
            return JSONResponse(
                content=result,
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                }
            )
    except Exception as e:
        print(f"アップロードエラー(POST): {str(e)}")
        print(f"トレースバック: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)},
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
            }
        )

@app.post("/api/upload-multiple-csv")
async def upload_multiple_csv(files: List[UploadFile] = File(...), data_type: str = Form(default="auto")):
    """複数のCSVファイルを一度にアップロードして処理する"""
    try:
        print(f"複数CSVアップロード開始: files数={len(files)}, data_type={data_type}")

        results = []
        errors = []

        for file in files:
            try:
                print(f"ファイル処理開始: {file.filename}")
                result = await process_uploaded_csv(file, data_type)

                # JSONResponseオブジェクトから内容を取り出す
                if isinstance(result, JSONResponse):
                    # レスポンスの内容を取得
                    content = result.body
                    if isinstance(content, bytes):
                        import json
                        content = json.loads(content.decode('utf-8'))
                    results.append({
                        "filename": file.filename,
                        "status": "成功",
                        "detail": content
                    })
                else:
                    # 通常の辞書の場合はそのまま追加
                    results.append({
                        "filename": file.filename,
                        "status": "成功",
                        "detail": result
                    })
            except Exception as e:
                print(f"ファイル処理エラー: {file.filename}, エラー: {str(e)}")
                errors.append({
                    "filename": file.filename,
                    "status": "エラー",
                    "detail": str(e)
                })

        return JSONResponse(
            content={
                "status": "処理完了",
                "total": len(files),
                "success": len(results),
                "errors": len(errors),
                "results": results,
                "error_details": errors
            },
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        print(f"複数アップロードエラー: {str(e)}")
        print(f"トレースバック: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)},
            headers={"Content-Type": "application/json"}
        )

# シンプルなファイルアップロードエンドポイント（テスト用）
@app.post("/api/simple-upload")
async def simple_upload(file: UploadFile = File(...)):
    """シンプルなファイルアップロードエンドポイント"""
    try:
        # ファイル名とサイズを取得
        contents = await file.read()
        file_size = len(contents)

        # ファイルを保存
        output_path = f"uploads/simple_{int(time.time())}_{file.filename}"
        with open(output_path, "wb") as f:
            f.write(contents)

        # 結果を返す
        return JSONResponse(
            content={
                "status": "成功",
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file_size,
                "saved_path": output_path,
                "message": "ファイルが正常にアップロードされました"
            },
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
            }
        )
    except Exception as e:
        print(f"シンプルアップロードエラー: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)},
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
            }
        )

# シンプルな複数ファイルアップロードエンドポイント（テスト用）
@app.post("/api/simple-upload-multiple")
async def simple_upload_multiple(files: List[UploadFile] = File(...)):
    """シンプルな複数ファイルアップロードエンドポイント"""
    try:
        results = []
        timestamp = int(time.time())

        for file in files:
            try:
                # ファイル読み込み
                contents = await file.read()
                file_size = len(contents)

                # ファイル保存
                output_path = f"uploads/simple_multi_{timestamp}_{file.filename}"
                with open(output_path, "wb") as f:
                    f.write(contents)

                # 結果追加
                results.append({
                    "filename": file.filename,
                    "status": "成功",
                    "size": file_size,
                    "saved_path": output_path
                })
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "エラー",
                    "detail": str(e)
                })

        return JSONResponse(
            content={
                "status": "処理完了",
                "total": len(files),
                "results": results
            },
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        print(f"複数シンプルアップロードエラー: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)},
            headers={"Content-Type": "application/json"}
        )

@app.options("/api/upload-csv")
async def upload_csv_options():
    """CSVファイルアップロードのOPTIONSリクエスト処理"""
    print("OPTIONS リクエスト受信: /api/upload-csv")
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
        "Content-Type": "application/json"
    }
    return JSONResponse(
        status_code=200,
        content={"allowed_methods": ["POST", "PUT", "OPTIONS"]},
        headers=headers
    )

# テスト用エンドポイント（アップロードが動作しない場合に使用）
@app.get("/api/test-upload")
async def test_upload():
    """アップロード機能のテスト用エンドポイント"""
    print("テストアップロードエンドポイント呼び出し")
    return JSONResponse(
        status_code=200,
        content={"status": "成功", "message": "アップロードエンドポイントが正常に動作しています"},
        headers={"Content-Type": "application/json"}
    )

async def process_uploaded_csv(file: UploadFile, data_type: str):
    """アップロードされたCSVファイルを処理する"""
    try:
        contents = await file.read()
        filename = file.filename

        # 一時ファイルパスを作成
        timestamp = int(time.time())
        temp_file_path = f"uploads/temp_{timestamp}_{filename}"

        # uploads ディレクトリが存在しない場合は作成
        if not os.path.exists("uploads"):
            os.makedirs("uploads")

        # ファイルを一時保存
        with open(temp_file_path, "wb") as f:
            f.write(contents)

        # CSVファイルを読み込む
        df = pd.read_csv(temp_file_path, encoding='utf-8')
        print(f"CSVカラム: {df.columns.tolist()}")

        # データタイプに基づく処理
        if data_type == "occupancy":
            # 元のカラム名を保存
            original_columns = df.columns.tolist()
            print(f"元のCSVカラム: {original_columns}")

            # 予約データの詳細なフォーマットを検出
            is_lesson_format = any("レッスン日" in col for col in original_columns) and any("ルームコード" in col for col in original_columns or "ルーム名" in col for col in original_columns)
            is_simple_format = "status" in [col.lower() for col in original_columns] or "room" in [col.lower() for col in original_columns]

            # 稼働率データの処理方法を判断
            if is_lesson_format:
                print("レッスン予約フォーマットを検出しました")
                # レッスンデータからルーム別稼働率を計算

                # 必要なカラムをチェック
                required_columns = ["レッスン日", "ルーム名", "総予約数", "無断キャンセル数", "スペース数"]
                missing_columns = [col for col in required_columns if not any(rcol in original_columns for rcol in [col, col.lower()])]

                if missing_columns:
                    error_msg = f"レッスンデータには以下のカラムが必要です: {', '.join(missing_columns)}"
                    print(f"エラー: {error_msg}")
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": error_msg},
                        headers={
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                        }
                    )

                # 日付列の検出と変換
                date_col = next((col for col in original_columns if "レッスン日" in col or "日付" in col or "date" in col.lower()), None)
                room_col = next((col for col in original_columns if "ルーム名" in col or "room" in col.lower()), None)
                reservation_col = next((col for col in original_columns if "総予約数" in col), None)
                no_show_col = next((col for col in original_columns if "無断キャンセル" in col), None)
                space_col = next((col for col in original_columns if "スペース数" in col), None)

                # 列が見つかったかどうかを確認
                print(f"検出された列: date={date_col}, room={room_col}, reservation={reservation_col}")

                # 必要に応じて日付形式を変換
                if date_col:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
                    df = df.rename(columns={date_col: "date"})

                # ルーム名をマッピング
                if room_col:
                    df = df.rename(columns={room_col: "room"})

                # 特殊処理：ダミーアカウント(ID: 137, 3, 5576)の無断キャンセルは利用としてカウント
                # 今回のCSVデータにはIDの情報がないため、単純に総予約数と無断キャンセル数から稼働率を計算

                df["occupancy_rate"] = 0  # デフォルト値

                # スタッフコード列を検出してダミーアカウントを処理
                staff_id_col = next((col for col in original_columns if "スタッフコード" in col), None)
                member_id_col = next((col for col in original_columns if "会員ID" in col or "メンバーID" in col), None)

                # 特殊なダミーアカウントIDを設定
                dummy_account_ids = [137, 3, 5576]

                # 予約がある場合（総予約数 > 0）
                if reservation_col and space_col:
                    # 基本の稼働率計算
                    df["effective_reservation"] = df[reservation_col]

                    # もしメンバーIDが存在し、無断キャンセルが存在する場合、ダミーアカウントの無断キャンセルを処理
                    if member_id_col and no_show_col and df[no_show_col].sum() > 0:
                        print("メンバーIDと無断キャンセルデータが存在します。ダミーアカウント処理を適用します。")
                        # ダミーアカウントの無断キャンセルは利用としてカウント
                        for dummy_id in dummy_account_ids:
                            mask = (df[member_id_col] == dummy_id) & (df[no_show_col] > 0)
                            if mask.any():
                                # ダミーアカウントの無断キャンセルは有効予約に加算
                                df.loc[mask, "effective_reservation"] = df.loc[mask, reservation_col]

                    # 稼働率の計算：(有効予約数 / スペース数) × 100
                    df["occupancy_rate"] = (df["effective_reservation"] / df[space_col]) * 100
                    # 小数点以下を切り捨て
                    df["occupancy_rate"] = df["occupancy_rate"].round(0).astype(int)

                # 新しいCSVファイルを作成
                result_df = df[["date", "room", "occupancy_rate"]].copy()

                # ルーム別の日次集計を行う
                daily_summary = result_df.groupby(["date", "room"])["occupancy_rate"].mean().reset_index()
                daily_summary["occupancy_rate"] = daily_summary["occupancy_rate"].round(0).astype(int)

                # 基本の集計結果と詳細情報
                summary_stats = {
                    "total_lessons": len(df),
                    "rooms": df["room"].unique().tolist(),
                    "date_range": [df["date"].min(), df["date"].max()],
                    "occupancy_by_room": {}
                }

                # 各ルームの平均稼働率
                for room in df["room"].unique():
                    room_data = df[df["room"] == room]
                    summary_stats["occupancy_by_room"][room] = {
                        "avg_occupancy": int(room_data["occupancy_rate"].mean()),
                        "min_occupancy": int(room_data["occupancy_rate"].min()),
                        "max_occupancy": int(room_data["occupancy_rate"].max()),
                        "lesson_count": len(room_data)
                    }

                # CSV処理（例：保存など）
                target_file_path = f"uploads/occupancy_{timestamp}.csv"
                daily_summary.to_csv(target_file_path, index=False)

                # 元の詳細データも保存
                details_path = f"uploads/occupancy_details_{timestamp}.csv"
                result_df.to_csv(details_path, index=False)

                return JSONResponse(
                    content={
                        "status": "成功",
                        "file": filename,
                        "saved_path": target_file_path,
                        "details_path": details_path,
                        "rows": len(df),
                        "summary": summary_stats,
                        "original_columns": original_columns,
                        "processed_columns": daily_summary.columns.tolist(),
                        "message": "レッスンデータから稼働率を計算しました"
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                    }
                )

            elif is_simple_format:
                print("シンプルなフォーマットを検出しました")
                # カラム名を小文字に変換
                df.columns = [col.lower() for col in df.columns]

                # CSVファイルのフォーマットを自動的に検出
                # 日付、部屋、稼働率に関連するカラムがあるか確認
                date_columns = [col for col in df.columns if 'date' in col or '日付' in col or '日時' in col or '年月日' in col]
                room_columns = [col for col in df.columns if 'room' in col or '部屋' in col or 'ルーム' in col]

                # 稼働率または状態のカラムを検出
                occupancy_columns = [col for col in df.columns if 'occupancy' in col or '稼働' in col or '占有' in col or 'rate' in col]
                status_columns = [col for col in df.columns if 'status' in col or '状態' in col or '状況' in col]

                # マッピング用の辞書
                column_mapping = {}

                # 日付と部屋のカラムは必須
                if not date_columns:
                    # 日付カラムがない場合はエラー
                    error_msg = "CSVファイルに日付を示すカラムが見つかりません"
                    print(f"エラー: {error_msg}")
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": error_msg},
                        headers={
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                        }
                    )

                if not room_columns:
                    # 部屋カラムがない場合はエラー
                    error_msg = "CSVファイルに部屋を示すカラムが見つかりません"
                    print(f"エラー: {error_msg}")
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": error_msg},
                        headers={
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                        }
                    )

                # 日付と部屋のカラムをマッピング
                column_mapping["date"] = date_columns[0]
                column_mapping["room"] = room_columns[0]

                # 稼働率または状態のカラムを処理
                if occupancy_columns:
                    # 稼働率カラムが存在する場合
                    column_mapping["occupancy_rate"] = occupancy_columns[0]
                elif status_columns:
                    # 状態カラムが存在する場合、稼働率カラムに変換
                    column_mapping["status"] = status_columns[0]
                    # 状態から稼働率への変換を行う
                    status_column = status_columns[0]
                    # 「利用済み」または「予約済み」を100%、「空き」を0%に変換
                    status_mapping = {
                        '利用済み': 100,
                        '予約済み': 100,
                        '空き': 0
                    }
                    # 新しい稼働率カラムを作成
                    df['occupancy_rate'] = df[status_column].map(status_mapping)
                    column_mapping["occupancy_rate"] = "occupancy_rate"
                else:
                    # どちらも存在しない場合は汎用的に処理
                    print("稼働率または状態を示すカラムが見つかりません。すべてのカラムを保持します。")

                # カラム名をマッピング
                df = df.rename(columns=column_mapping)

                # CSV処理（例：保存など）
                target_file_path = f"uploads/occupancy_{timestamp}.csv"
                df.to_csv(target_file_path, index=False)

                return JSONResponse(
                    content={
                        "status": "成功",
                        "file": filename,
                        "saved_path": target_file_path,
                        "rows": len(df),
                        "original_columns": original_columns,
                        "processed_columns": df.columns.tolist(),
                        "mapped_columns": column_mapping
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                    }
                )
            else:
                # どのフォーマットにも該当しない場合
                error_msg = "サポートされていないCSVフォーマットです。稼働率データまたはレッスン予約データを提供してください。"
                print(f"エラー: {error_msg}")
                return JSONResponse(
                    status_code=400,
                    content={"status": "エラー", "detail": error_msg},
                    headers={
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                    }
                )
        elif data_type == "sales":
            # 売上データの処理
            # 必要なカラムの検出
            required_hints = {
                "売上日": ["売上日", "date", "日付", "sales_date"],
                "部屋": ["部屋", "room", "ルーム", "場所"],
                "売上金額": ["売上金額", "金額", "amount", "sales", "価格", "料金"]
            }

            column_mapping = {}
            missing_columns = []

            # カラムの自動検出
            for req_col, hints in required_hints.items():
                found = False
                for hint in hints:
                    matching_cols = [col for col in df.columns if hint.lower() in col.lower()]
                    if matching_cols:
                        column_mapping[req_col] = matching_cols[0]
                        found = True
                        break
                if not found:
                    missing_columns.append(req_col)

            if missing_columns:
                # 必要なカラムがない場合はエラー
                error_msg = f"売上データのCSVには、{', '.join(required_hints.keys())}のカラムが必要です"
                print(f"エラー: {error_msg}")
                return JSONResponse(
                    status_code=400,
                    content={"status": "エラー", "detail": error_msg},
                    headers={
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                    }
                )

            # カラム名をマッピング
            df_mapped = df.copy()
            for standard_name, original_name in column_mapping.items():
                if standard_name != original_name:
                    df_mapped = df_mapped.rename(columns={original_name: standard_name})

            # CSV処理
            target_file_path = f"uploads/sales_{timestamp}.csv"
            df_mapped.to_csv(target_file_path, index=False)

            return JSONResponse(
                content={
                    "status": "成功",
                    "file": filename,
                    "saved_path": target_file_path,
                    "rows": len(df),
                    "columns": df_mapped.columns.tolist(),
                    "mapped_columns": column_mapping
                },
                headers={"Content-Type": "application/json"}
            )
        elif data_type == "member":
            # 会員データの処理
            required_hints = {
                "会員ID": ["会員ID", "id", "member_id", "会員番号", "番号"],
                "氏名": ["氏名", "name", "名前", "会員名"],
                "性別": ["性別", "gender", "sex"]
            }

            column_mapping = {}
            missing_columns = []

            # カラムの自動検出
            for req_col, hints in required_hints.items():
                found = False
                for hint in hints:
                    matching_cols = [col for col in df.columns if hint.lower() in col.lower()]
                    if matching_cols:
                        column_mapping[req_col] = matching_cols[0]
                        found = True
                        break
                if not found:
                    missing_columns.append(req_col)

            if missing_columns:
                # 必要なカラムがない場合はエラー
                error_msg = f"会員データのCSVには、{', '.join(required_hints.keys())}のカラムが必要です。見つかったカラム: {df.columns.tolist()}"
                print(f"エラー: {error_msg}")
                return JSONResponse(
                    status_code=400,
                    content={"status": "エラー", "detail": error_msg},
                    headers={"Content-Type": "application/json"}
                )

            # カラム名をマッピング
            df_mapped = df.copy()
            for standard_name, original_name in column_mapping.items():
                if standard_name != original_name:
                    df_mapped = df_mapped.rename(columns={original_name: standard_name})

            # CSV処理
            target_file_path = f"uploads/member_{timestamp}.csv"
            df_mapped.to_csv(target_file_path, index=False)

            return JSONResponse(
                content={
                    "status": "成功",
                    "file": filename,
                    "saved_path": target_file_path,
                    "rows": len(df),
                    "columns": df_mapped.columns.tolist(),
                    "mapped_columns": column_mapping
                },
                headers={"Content-Type": "application/json"}
            )
        elif data_type == "reservation":
            # 予約データの処理
            required_hints = {
                "予約日": ["予約日", "日付", "date", "年月日"],
                "部屋": ["部屋", "room", "ルーム", "room_name"],
                "開始時間": ["開始時間", "開始", "start", "start_time"],
                "終了時間": ["終了時間", "終了", "end", "end_time"]
            }

            column_mapping = {}
            missing_columns = []

            # カラムの自動検出
            for req_col, hints in required_hints.items():
                found = False
                for hint in hints:
                    matching_cols = [col for col in df.columns if hint.lower() in col.lower()]
                    if matching_cols:
                        column_mapping[req_col] = matching_cols[0]
                        found = True
                        break
                if not found:
                    missing_columns.append(req_col)

            if missing_columns:
                # 必要なカラムがない場合はエラー
                error_msg = f"予約データのCSVには、{', '.join(required_hints.keys())}のカラムが必要です。見つかったカラム: {df.columns.tolist()}"
                print(f"エラー: {error_msg}")
                return JSONResponse(
                    status_code=400,
                    content={"status": "エラー", "detail": error_msg},
                    headers={"Content-Type": "application/json"}
                )

            # カラム名をマッピング
            df_mapped = df.copy()
            for standard_name, original_name in column_mapping.items():
                if standard_name != original_name:
                    df_mapped = df_mapped.rename(columns={original_name: standard_name})

            # CSV処理
            target_file_path = f"uploads/reservation_{timestamp}.csv"
            df_mapped.to_csv(target_file_path, index=False)

            return JSONResponse(
                content={
                    "status": "成功",
                    "file": filename,
                    "saved_path": target_file_path,
                    "rows": len(df),
                    "columns": df_mapped.columns.tolist(),
                    "mapped_columns": column_mapping
                },
                headers={"Content-Type": "application/json"}
            )
        else:
            # 汎用的な処理 (自動検出)
            # ファイル名からデータタイプを推測
            auto_data_type = "generic"
            filename_lower = filename.lower()
            if "frame" in filename_lower or "occupancy" in filename_lower:
                auto_data_type = "occupancy"
            elif "sales" in filename_lower:
                auto_data_type = "sales"
            elif "member" in filename_lower:
                auto_data_type = "member"
            elif "reservation" in filename_lower:
                auto_data_type = "reservation"

            print(f"ファイル名から推測したデータタイプ: {auto_data_type}")

            # 推測したデータタイプで再処理
            if auto_data_type != "generic":
                return await process_uploaded_csv(file, auto_data_type)

            # 汎用処理
            target_file_path = f"uploads/generic_{timestamp}_{filename}"
            df.to_csv(target_file_path, index=False)
            return JSONResponse(
                content={
                    "status": "成功",
                    "file": filename,
                    "saved_path": target_file_path,
                    "rows": len(df),
                    "columns": df.columns.tolist(),
                    "auto_detected_type": auto_data_type
                },
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        print(f"CSV処理エラー: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"トレースバック: {traceback_str}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e), "traceback": traceback_str},
            headers={"Content-Type": "application/json"}
        )

# ヘルスチェック
@app.get("/health")
async def health_check():
    return JSONResponse(
        content={"status": "ok"},
        headers={"Content-Type": "application/json"}
    )

# 競合分析用ダミーデータを初期化
def initialize_competitors_data():
    """競合分析用のデータを初期化する関数"""
    return {
        "pricing": [
            {"name": "HAAAVE.sauna", "価格": 16000},
            {"name": "M's Sauna", "価格": 10000},
            {"name": "KUDOCHI sauna", "価格": 6000},
            {"name": "SAUNA Pod 槃", "価格": 5500},
            {"name": "SAUNA OOO OSAKA", "価格": 5500},
            {"name": "MENTE", "価格": 5000},
            {"name": "大阪サウナ DESSE", "価格": 1500}
        ],
        "details": [
            {
                "施設名": "HAAAVE.sauna",
                "所在地": "大阪市西区南堀江",
                "形態": "会員制",
                "料金": "16,000円〜",
                "ルーム数": "3室",
                "水風呂": "あり",
                "男女混浴": "可",
                "開業年": "2023年"
            },
            {
                "施設名": "KUDOCHI sauna",
                "所在地": "大阪市中央区東心斎橋",
                "形態": "完全個室",
                "料金": "6,000円〜",
                "ルーム数": "6室",
                "水風呂": "あり",
                "男女混浴": "可",
                "開業年": "2024年"
            },
            {
                "施設名": "MENTE",
                "所在地": "大阪市北区茶屋町",
                "形態": "男性専用",
                "料金": "5,000円〜",
                "ルーム数": "1室",
                "水風呂": "なし",
                "男女混浴": "不可",
                "開業年": "2022年"
            },
            {
                "施設名": "M's Sauna",
                "所在地": "大阪市北区曽根崎新地",
                "形態": "VIP個室",
                "料金": "10,000円〜",
                "ルーム数": "3室",
                "水風呂": "あり",
                "男女混浴": "不可",
                "開業年": "2023年"
            },
            {
                "施設名": "SAUNA Pod 槃",
                "所在地": "大阪市西区",
                "形態": "会員制",
                "料金": "5,500円〜",
                "ルーム数": "4室",
                "水風呂": "あり",
                "男女混浴": "可",
                "開業年": "2023年"
            },
            {
                "施設名": "SAUNA OOO OSAKA",
                "所在地": "大阪市中央区西心斎橋",
                "形態": "予約制",
                "料金": "5,500円〜",
                "ルーム数": "3室",
                "水風呂": "なし",
                "男女混浴": "可",
                "開業年": "2023年"
            },
            {
                "施設名": "大阪サウナ DESSE",
                "所在地": "大阪市中央区南船場",
                "形態": "大型複合",
                "料金": "1,500円〜",
                "ルーム数": "7室",
                "水風呂": "あり",
                "男女混浴": "不可",
                "開業年": "2023年"
            }
        ],
        "regionDistribution": [
            {"name": "大阪市北区", "value": 3},
            {"name": "大阪市中央区", "value": 5},
            {"name": "大阪市西区", "value": 2},
            {"name": "大阪市浪速区", "value": 1},
            {"name": "大阪市天王寺区", "value": 2},
            {"name": "大阪市淀川区", "value": 0},
            {"name": "その他", "value": 1}
        ]
    }

# サーバー起動時に競合分析データを必ず初期化
dashboard_data.competitors = initialize_competitors_data()

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時に実行されるイベントハンドラ"""
    print("API server has started")
    # uploads ディレクトリが存在しない場合は作成
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("Created uploads directory")

    # 競合分析データを確実に初期化
    global dashboard_data
    if not dashboard_data.competitors:
        dashboard_data.competitors = initialize_competitors_data()
    print("競合分析データを初期化しました")

# ダッシュボードデータをリセットする関数
def reset_dashboard_data():
    """ダッシュボードデータをリセットする関数（競合分析データは保持）"""
    global dashboard_data

    # 競合データを一時保存
    competitors_backup = dashboard_data.competitors

    # データを初期化
    dashboard_data = DashboardData(
        labels={
            "months": [f"2023-{i:02d}" for i in range(1, 13)] + [f"2024-{i:02d}" for i in range(1, 7)],
            "daysOfWeek": ["月", "火", "水", "木", "金", "土", "日"],
            "timeSlots": ["9-12時", "12-15時", "15-18時", "18-21時", "21-24時"],
            "regions": ["大阪府", "兵庫県", "京都府", "奈良県", "滋賀県", "和歌山県", "その他"],
            "roomNames": ["Room1", "Room2", "Room3"],
            "competitorNames": ["HAAAVE.sauna", "KUDOCHI sauna", "MENTE", "M's Sauna", "SAUNA Pod 槃", "SAUNA OOO OSAKA", "大阪サウナ DESSE"],
            "ageGroups": ["20代", "30代", "40代", "50代", "~19歳", "60歳~"],
            "genders": ["男性", "女性"]
        },
        metrics={},
        members={},
        utilization={},
        competitors={},
        finance={}
    )

    # 競合データを復元
    dashboard_data.competitors = competitors_backup

    # 競合データが空の場合は初期化
    if not dashboard_data.competitors or len(dashboard_data.competitors) == 0:
        dashboard_data.competitors = initialize_competitors_data()
        print("競合分析データを再初期化しました")

    return {
        "status": "成功",
        "message": "ダッシュボードデータがリセットされました（競合分析データは保持）"
    }

# ダッシュボードデータリセットエンドポイント
@app.post("/api/reset-dashboard")
async def reset_dashboard():
    """ダッシュボードデータをリセットするエンドポイント（競合分析データは保持）"""
    try:
        result = reset_dashboard_data()
        return JSONResponse(
            content=result,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        print(f"ダッシュボードリセット中にエラーが発生しました: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)},
            headers={"Content-Type": "application/json"}
        )

# サーバー起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
