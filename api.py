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

async def process_uploaded_csv(file, data_type):
    """
    CSVファイルを処理してデータを変換し、保存します
    """
    global dashboard_data

    try:
        # CSVファイルを読み込む
        print(f"CSVファイル読み込み開始: file={file.filename}")
        df = pd.read_csv(file.file, encoding='utf-8')
        print(f"CSVファイル読み込み成功: エンコーディング=utf-8")

        # カラム名を確認して出力
        print("CSVカラム:", df.columns.tolist())
        print("データサンプル:", df.head(3).to_dict('records'))

        # データタイプによって処理を分岐
        if data_type == "occupancy":
            # オリジナルのカラムを保存
            original_columns = df.columns.tolist()
            print("元のCSVカラム:", original_columns)
            print("入力ファイル情報:")
            print(f"- カラム数: {len(df.columns)}")
            print(f"- 行数: {len(df)}")
            print(f"- データ型: {df.dtypes}")

            # レッスン予約形式を検出
            if any(col in original_columns for col in ["ルームコード", "ルーム名"]):
                print("レッスン予約フォーマットを検出しました")
                print("レッスンデータフォーマットを処理します")

                # 必要なカラムがあるか確認
                date_col = None
                for col_name in ["レッスン日", "日付", "date"]:
                    if col_name in original_columns:
                        date_col = col_name
                        break

                if date_col is None:
                    print("日付カラムが見つかりません")
                    return {
                        "status": "エラー",
                        "detail": "CSVファイルに日付を示すカラムが見つかりません"
                    }

                # ルーム名カラムを確認
                room_col = None
                for col_name in ["ルーム名", "ルームコード"]:
                    if col_name in original_columns:
                        room_col = col_name
                        break

                if room_col is None:
                    print("ルーム名カラムが見つかりません")
                    return {
                        "status": "エラー",
                        "detail": "CSVファイルにルーム名を示すカラムが見つかりません"
                    }

                # 予約カラムを確認
                reservation_cols = []
                for col_name in ["総予約数", "無断キャンセル数", "スペース数"]:
                    if col_name in original_columns:
                        reservation_cols.append(col_name)

                if not reservation_cols:
                    print("予約情報カラムが見つかりません")
                    return {
                        "status": "エラー",
                        "detail": "CSVファイルに予約情報を示すカラムが見つかりません"
                    }

                # 日付カラムを変換
                print(f"検出したカラム - 日付: {date_col}, ルーム: {room_col}, 予約数: {reservation_cols}")
                df[date_col] = pd.to_datetime(df[date_col])
                df = df.rename(columns={date_col: "date"})

                # ルームごとに予約数と稼働率を集計
                room_summary = df.groupby(room_col).agg(
                    lesson_count=pd.NamedAgg(column="date", aggfunc="count")
                )

                # 稼働率カラムがある場合
                occupancy_col = None
                for col_name in ["稼働率", "occupancy"]:
                    if col_name in original_columns:
                        occupancy_col = col_name
                        break

                if occupancy_col:
                    print(f"稼働率カラム検出: {occupancy_col}")
                    print(f"稼働率データサンプル: {df[occupancy_col].head(10).tolist()}")

                    # 稼働率を数値に変換（例：'85%' → 85.0）
                    # 複数の値が結合されている場合に備えて、最初の数値部分のみを抽出
                    df[occupancy_col] = df[occupancy_col].apply(
                        lambda x: float(re.match(r'(\d+)', str(x)).group(1)) if pd.notnull(x) and re.match(r'(\d+)', str(x)) else None
                    )
                    print(f"変換後の稼働率データサンプル: {df[occupancy_col].head(10).tolist()}")

                    # ルームごとの平均稼働率を計算
                    room_summary["avg_occupancy"] = df.groupby(room_col)[occupancy_col].mean()
                    print(f"ルームごとの平均稼働率: {room_summary['avg_occupancy'].to_dict()}")

                    # 稼働率データフレームを作成
                    occupancy_df = df[[room_col, "date", occupancy_col]].copy()
                    print(f"稼働率データフレーム作成 - 行数: {len(occupancy_df)}, 欠損値: {occupancy_df.isna().sum().to_dict()}")
                    occupancy_df = occupancy_df.rename(columns={room_col: "room", occupancy_col: "occupancy"})

                    # タイムスタンプを含むファイル名で保存
                    timestamp = int(time.time())
                    output_file = f"uploads/occupancy_{timestamp}.csv"
                    occupancy_df.to_csv(output_file, index=False)
                    print(f"稼働率データを保存しました: {output_file}")

                    # 詳細データを保存
                    details_file = f"uploads/occupancy_details_{timestamp}.csv"
                    df.to_csv(details_file, index=False)
                    print(f"詳細データを保存しました: {details_file}")

                    # ルームごとの詳細情報を取得
                    room_details = {}
                    for room in occupancy_df["room"].unique():
                        room_data = occupancy_df[occupancy_df["room"] == room]
                        room_occupancy = room_data["occupancy"].dropna().tolist()
                        if room_occupancy:
                            avg_occ = sum(room_occupancy) / len(room_occupancy)
                            min_occ = min(room_occupancy)
                            max_occ = max(room_occupancy)
                            room_details[room] = {
                                "avg": avg_occ,
                                "min": min_occ,
                                "max": max_occ
                            }
                            print(f"ルーム {room} の稼働率情報: 平均={avg_occ:.1f}%, 最小={min_occ:.1f}%, 最大={max_occ:.1f}%")

                    # 日付範囲を取得
                    min_date = df["date"].min().strftime("%Y-%m-%d")
                    max_date = df["date"].max().strftime("%Y-%m-%d")
                    print(f"データ期間: {min_date} から {max_date} まで")

                    # dashboard_dataを更新する
                    print("ダッシュボードデータの更新を開始します")
                    update_dashboard_with_occupancy_data(occupancy_df)
                    print("ダッシュボードデータの更新が完了しました")

                    return {
                        "status": "成功",
                        "file": output_file,
                        "details_file": details_file,
                        "total_lessons": len(df),
                        "date_range": {
                            "from": min_date,
                            "to": max_date
                        },
                        "room_occupancy": room_details
                    }

                # 稼働率カラムがない場合はスペース数と予約数から計算
                else:
                    print("稼働率カラムがないため、スペース数と予約数から計算します")
                    if "総予約数" in original_columns and "スペース数" in original_columns:
                        # スペース数が0の場合に0除算を防ぐ
                        df["稼働率"] = df.apply(
                            lambda row: (row["総予約数"] / row["スペース数"]) * 100 if row["スペース数"] > 0 else 0,
                            axis=1
                        )
                        print(f"計算された稼働率データサンプル: {df['稼働率'].head(10).tolist()}")

                        # ルームごとの平均稼働率を計算
                        room_summary["avg_occupancy"] = df.groupby(room_col)["稼働率"].mean()
                        print(f"ルームごとの平均稼働率: {room_summary['avg_occupancy'].to_dict()}")

                        # 稼働率データフレームを作成
                        occupancy_df = df[[room_col, "date", "稼働率"]].copy()
                        print(f"稼働率データフレーム作成 - 行数: {len(occupancy_df)}, 欠損値: {occupancy_df.isna().sum().to_dict()}")
                        occupancy_df = occupancy_df.rename(columns={room_col: "room", "稼働率": "occupancy"})

                        # タイムスタンプを含むファイル名で保存
                        timestamp = int(time.time())
                        output_file = f"uploads/occupancy_{timestamp}.csv"
                        occupancy_df.to_csv(output_file, index=False)
                        print(f"稼働率データを保存しました: {output_file}")

                        # 詳細データを保存
                        details_file = f"uploads/occupancy_details_{timestamp}.csv"
                        df.to_csv(details_file, index=False)
                        print(f"詳細データを保存しました: {details_file}")

                        # ルームごとの詳細情報を取得
                        room_details = {}
                        for room in occupancy_df["room"].unique():
                            room_data = occupancy_df[occupancy_df["room"] == room]
                            room_occupancy = room_data["occupancy"].dropna().tolist()
                            if room_occupancy:
                                avg_occ = sum(room_occupancy) / len(room_occupancy)
                                min_occ = min(room_occupancy)
                                max_occ = max(room_occupancy)
                                room_details[room] = {
                                    "avg": avg_occ,
                                    "min": min_occ,
                                    "max": max_occ
                                }
                                print(f"ルーム {room} の稼働率情報: 平均={avg_occ:.1f}%, 最小={min_occ:.1f}%, 最大={max_occ:.1f}%")

                        # 日付範囲を取得
                        min_date = df["date"].min().strftime("%Y-%m-%d")
                        max_date = df["date"].max().strftime("%Y-%m-%d")
                        print(f"データ期間: {min_date} から {max_date} まで")

                        # dashboard_dataを更新する
                        print("ダッシュボードデータの更新を開始します")
                        update_dashboard_with_occupancy_data(occupancy_df)
                        print("ダッシュボードデータの更新が完了しました")

                        return {
                            "status": "成功",
                            "file": output_file,
                            "details_file": details_file,
                            "total_lessons": len(df),
                            "date_range": {
                                "from": min_date,
                                "to": max_date
                            },
                            "room_occupancy": room_details
                        }

            # シンプルなフォーマット（日付、ルーム名、稼働率のみ）
            elif all(col in original_columns for col in ["date", "room", "occupancy"]):
                print("シンプルフォーマットを検出しました")

                # 日付カラムを変換
                df["date"] = pd.to_datetime(df["date"])
                print("日付カラムを変換しました")

                # 稼働率を数値に変換（例：'85%' → 85.0）
                print(f"稼働率データサンプル: {df['occupancy'].head(10).tolist()}")
                df["occupancy"] = df["occupancy"].apply(
                    lambda x: float(re.match(r'(\d+)', str(x)).group(1)) if pd.notnull(x) and re.match(r'(\d+)', str(x)) else None
                )
                print(f"変換後の稼働率データサンプル: {df['occupancy'].head(10).tolist()}")

                # タイムスタンプを含むファイル名で保存
                timestamp = int(time.time())
                output_file = f"uploads/occupancy_{timestamp}.csv"
                df.to_csv(output_file, index=False)
                print(f"稼働率データを保存しました: {output_file}")

                # ルームごとの詳細情報を取得
                room_details = {}
                for room in df["room"].unique():
                    room_data = df[df["room"] == room]
                    room_occupancy = room_data["occupancy"].dropna().tolist()
                    if room_occupancy:
                        avg_occ = sum(room_occupancy) / len(room_occupancy)
                        min_occ = min(room_occupancy)
                        max_occ = max(room_occupancy)
                        room_details[room] = {
                            "avg": avg_occ,
                            "min": min_occ,
                            "max": max_occ
                        }
                        print(f"ルーム {room} の稼働率情報: 平均={avg_occ:.1f}%, 最小={min_occ:.1f}%, 最大={max_occ:.1f}%")

                # 日付範囲を取得
                min_date = df["date"].min().strftime("%Y-%m-%d")
                max_date = df["date"].max().strftime("%Y-%m-%d")
                print(f"データ期間: {min_date} から {max_date} まで")

                # dashboard_dataを更新する
                print("ダッシュボードデータの更新を開始します")
                update_dashboard_with_occupancy_data(df)
                print("ダッシュボードデータの更新が完了しました")

                return {
                    "status": "成功",
                    "file": output_file,
                    "total_lessons": len(df),
                    "date_range": {
                        "from": min_date,
                        "to": max_date
                    },
                    "room_occupancy": room_details
                }

            # フォーマットが認識できない場合
            else:
                print("認識できないCSVフォーマットです")
                return {
                    "status": "エラー",
                    "detail": "CSVフォーマットが認識できません。正しいフォーマットで再アップロードしてください。"
                }

        # その他のデータタイプの処理
        # ...

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        traceback.print_exc()
        return {
            "status": "エラー",
            "detail": f"CSVファイルの処理中にエラーが発生しました: {str(e)}"
        }

def update_dashboard_with_occupancy_data(occupancy_df):
    """
    アップロードされた稼働率データをdashboard_dataに反映させる

    Parameters:
    -----------
    occupancy_df : pandas.DataFrame
        date, room, occupancyのカラムを持つDataFrame
    """
    global dashboard_data

    try:
        # DataFrameが空の場合は処理しない
        if occupancy_df.empty:
            print("稼働率データが空のため、ダッシュボードの更新をスキップします")
            return

        print(f"ダッシュボード更新開始: データ行数={len(occupancy_df)}")
        print(f"入力データサンプル: {occupancy_df.head(3).to_dict('records')}")

        # dashboard_data.utilizationが初期化されていない場合は初期化
        if not hasattr(dashboard_data, 'utilization') or dashboard_data.utilization is None:
            dashboard_data.utilization = {}
            print("utilization辞書を初期化しました")

        # 必要なフィールドの初期化
        if 'monthly' not in dashboard_data.utilization:
            dashboard_data.utilization['monthly'] = {}
            print("monthly辞書を初期化しました")

        if 'weekly' not in dashboard_data.utilization:
            dashboard_data.utilization['weekly'] = {}
            print("weekly辞書を初期化しました")

        if 'rooms' not in dashboard_data.utilization:
            dashboard_data.utilization['rooms'] = {}
            print("rooms辞書を初期化しました")

        # 日付をdatetime形式に変換
        if len(occupancy_df) > 0:
            first_date = occupancy_df['date'].iloc[0]
            print(f"最初の日付値: {first_date}, タイプ: {type(first_date)}")

            if isinstance(first_date, str):
                occupancy_df['date'] = pd.to_datetime(occupancy_df['date'])
                print("日付列を日時形式に変換しました")

        # NaN値を確認
        nan_count = occupancy_df['occupancy'].isna().sum()
        print(f"稼働率のNaN値の数: {nan_count}")

        # NaN値を除外
        occupancy_df = occupancy_df.dropna(subset=['occupancy'])
        print(f"NaN値を除外後のデータ行数: {len(occupancy_df)}")

        # 月別の稼働率を計算
        try:
            occupancy_df['year_month'] = occupancy_df['date'].dt.strftime('%Y-%m')
            monthly_occupancy = occupancy_df.groupby(['year_month', 'room'])['occupancy'].mean().reset_index()
            print(f"月別稼働率計算結果: {len(monthly_occupancy)}行")
            print(f"月別稼働率サンプル: {monthly_occupancy.head(3).to_dict('records')}")

            for _, row in monthly_occupancy.iterrows():
                year_month = row['year_month']
                room = row['room']
                occupancy = row['occupancy']

                if year_month not in dashboard_data.utilization['monthly']:
                    dashboard_data.utilization['monthly'][year_month] = {}

                dashboard_data.utilization['monthly'][year_month][room] = occupancy

            print(f"月別稼働率更新完了: {len(dashboard_data.utilization['monthly'])}月分")
        except Exception as e:
            print(f"月別稼働率計算中にエラー: {str(e)}")
            traceback.print_exc()

        # 曜日別の稼働率を計算
        try:
            occupancy_df['day_of_week'] = occupancy_df['date'].dt.dayofweek  # 0=月曜, 6=日曜
            weekly_occupancy = occupancy_df.groupby(['day_of_week', 'room'])['occupancy'].mean().reset_index()
            print(f"曜日別稼働率計算結果: {len(weekly_occupancy)}行")

            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

            for _, row in weekly_occupancy.iterrows():
                day_idx = int(row['day_of_week'])
                day_name = day_names[day_idx]
                room = row['room']
                occupancy = row['occupancy']

                if day_name not in dashboard_data.utilization['weekly']:
                    dashboard_data.utilization['weekly'][day_name] = {}

                dashboard_data.utilization['weekly'][day_name][room] = occupancy

            print(f"曜日別稼働率更新完了: {len(dashboard_data.utilization['weekly'])}曜日分")
        except Exception as e:
            print(f"曜日別稼働率計算中にエラー: {str(e)}")
            traceback.print_exc()

        # ルームごとの平均稼働率を計算
        try:
            room_occupancy = occupancy_df.groupby('room')['occupancy'].mean()
            print(f"ルームごとの稼働率: {room_occupancy.to_dict()}")

            for room, occupancy in room_occupancy.items():
                dashboard_data.utilization['rooms'][room] = {
                    'average': occupancy,
                    'label': room
                }

            print(f"ルーム別稼働率更新完了: {len(dashboard_data.utilization['rooms'])}ルーム")
        except Exception as e:
            print(f"ルーム別稼働率計算中にエラー: {str(e)}")
            traceback.print_exc()

        # 全体平均の稼働率も計算
        try:
            overall_avg = occupancy_df['occupancy'].mean()
            dashboard_data.utilization['overall_average'] = overall_avg
            print(f"全体平均稼働率: {overall_avg:.2f}%")
        except Exception as e:
            print(f"全体平均計算中にエラー: {str(e)}")
            traceback.print_exc()

        # ダッシュボードデータの一部を表示して確認
        try:
            print("更新されたダッシュボードデータのサンプル:")
            print(f"- ルーム数: {len(dashboard_data.utilization['rooms'])}")
            print(f"- 月数: {len(dashboard_data.utilization['monthly'])}")
            print(f"- 曜日数: {len(dashboard_data.utilization['weekly'])}")
            print(f"- 全体平均: {dashboard_data.utilization.get('overall_average', 'N/A')}")
        except Exception as e:
            print(f"ダッシュボードデータ表示中にエラー: {str(e)}")

    except Exception as e:
        print(f"ダッシュボードデータの更新中にエラーが発生しました: {str(e)}")
        traceback.print_exc()

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
