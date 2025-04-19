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

        # CSVファイルの読み込みを複数のエンコーディングで試行
        encoding_list = ['utf-8', 'cp932', 'shift_jis', 'euc-jp', 'iso-2022-jp']
        df = None
        error_messages = []

        for encoding in encoding_list:
            try:
                # エンコーディングとセパレータを明示的に指定
                df = pd.read_csv(temp_file_path, encoding=encoding)
                print(f"CSVファイル読み込み成功: エンコーディング={encoding}")
                break
            except Exception as e:
                error_messages.append(f"エンコーディング {encoding} での読み込み失敗: {str(e)}")
                try:
                    # 区切り文字をカンマ以外（タブ、セミコロン）でも試行
                    df = pd.read_csv(temp_file_path, encoding=encoding, sep='\t')
                    print(f"CSVファイル読み込み成功: エンコーディング={encoding}, 区切り文字=タブ")
                    break
                except Exception as e2:
                    error_messages.append(f"タブ区切りでも失敗: {str(e2)}")
                    try:
                        df = pd.read_csv(temp_file_path, encoding=encoding, sep=';')
                        print(f"CSVファイル読み込み成功: エンコーディング={encoding}, 区切り文字=セミコロン")
                        break
                    except Exception as e3:
                        error_messages.append(f"セミコロン区切りでも失敗: {str(e3)}")

        # 読み込み失敗の場合
        if df is None:
            # ファイルの中身を直接確認
            with open(temp_file_path, 'rb') as f:
                first_line = f.readline().decode('utf-8', errors='replace')

            error_msg = f"CSVファイルの読み込みに失敗しました。ファイル形式を確認してください。\nファイル先頭の内容: {first_line}\n詳細エラー: {error_messages[-1]}"
            print(f"エラー: {error_msg}")
            return JSONResponse(
                status_code=400,
                content={"status": "エラー", "detail": error_msg},
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            )

        # 読み込みに成功したが、カラムが0または非常に少ない場合
        if len(df.columns) == 0 or (len(df.columns) == 1 and len(df) == 0):
            # CSVファイルの内容をプレビュー
            with open(temp_file_path, 'rb') as f:
                preview = f.read(1024).decode('utf-8', errors='replace')

            error_msg = f"CSVファイルにカラムが見つかりません。ファイル形式を確認してください。\nファイル内容プレビュー: {preview}"
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

        print(f"CSVカラム: {df.columns.tolist()}")
        print(f"データサンプル: {df.head(3).to_dict('records')}")

        # データタイプに基づく処理
        if data_type == "occupancy":
            # 元のカラム名を保存
            original_columns = df.columns.tolist()
            print(f"元のCSVカラム: {original_columns}")

            # 入力ファイルの詳細を出力（デバッグ用）
            print(f"入力ファイル情報:")
            print(f"- カラム数: {len(df.columns)}")
            print(f"- 行数: {len(df)}")
            print(f"- データ型: {df.dtypes}")

            # カラム名の前処理: 空白文字の削除とトリム
            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]

            # 予約データの詳細なフォーマットを検出
            is_lesson_format = any("レッスン日" in col for col in original_columns) and any("ルーム" in col for col in original_columns)
            is_simple_format = any(col.lower() in ["status", "room", "部屋", "ルーム", "date", "日付"] for col in df.columns)
            is_frame_format = any("frame" in filename.lower() or "frame" in col.lower() for col in df.columns)

            # CSVの種類を検出
            detected_format = None
            if is_lesson_format:
                detected_format = "lesson"
                print("レッスン予約フォーマットを検出しました")
            elif is_simple_format:
                detected_format = "simple"
                print("シンプルなフォーマットを検出しました")
            elif is_frame_format:
                detected_format = "frame"
                print("フレームデータ形式を検出しました")
            else:
                # カラム名からフォーマットを推測
                if len(df.columns) == 1:
                    # 1列のみの場合、カンマやタブで分割されていない可能性
                    first_row = df.iloc[0, 0] if len(df) > 0 else ""
                    if isinstance(first_row, str) and (',' in first_row or '\t' in first_row):
                        # カンマやタブ区切りの文字列を含む可能性がある
                        error_msg = f"CSVファイルの区切り文字が正しく認識されていません。最初の行の内容: {first_row}"
                        print(f"エラー: {error_msg}")
                        return JSONResponse(
                            status_code=400,
                            content={"status": "エラー", "detail": error_msg},
                            headers={
                                "Content-Type": "application/json",
                                "Access-Control-Allow-Origin": "*"
                            }
                        )

                # 既知のフォーマットに一致しない場合
                error_msg = "サポートされていないCSVフォーマットです。稼働率データに必要なカラム(date, room, occupancy_rate)またはそれに相当するカラムが必要です。"
                print(f"エラー: {error_msg}")
                print(f"利用可能なカラム: {df.columns.tolist()}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "エラー",
                        "detail": error_msg,
                        "available_columns": df.columns.tolist(),
                        "expected_columns": "date/日付, room/部屋, occupancy_rate/稼働率 またはそれに相当するカラム"
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    }
                )

            # ここからフォーマット別の処理
            if detected_format == "lesson":
                # レッスンデータの処理
                print("レッスンデータフォーマットを処理します")

                # 必要なカラムを確認
                date_column = None
                room_column = None
                reservation_column = None
                capacity_column = None
                no_show_column = None
                occupancy_column = None

                # レッスン日カラムの検出
                date_candidates = ["レッスン日", "日付", "date"]
                for candidate in date_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        date_column = matching_cols[0]
                        break

                # ルーム名カラムの検出
                room_candidates = ["ルーム名", "ルームコード", "room", "部屋"]
                for candidate in room_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        room_column = matching_cols[0]
                        break

                # 予約数カラムの検出
                reservation_candidates = ["総予約数", "予約数", "予約"]
                for candidate in reservation_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        reservation_column = matching_cols[0]
                        break

                # 無断キャンセル数カラムの検出
                no_show_candidates = ["無断キャンセル数", "無断キャンセル"]
                for candidate in no_show_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        no_show_column = matching_cols[0]
                        break

                # スペース数（キャパシティ）カラムの検出
                capacity_candidates = ["スペース数", "定員", "キャパシティ"]
                for candidate in capacity_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        capacity_column = matching_cols[0]
                        break

                # 稼働率カラムの検出
                occupancy_candidates = ["稼働率", "occupancy_rate"]
                for candidate in occupancy_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        occupancy_column = matching_cols[0]
                        break

                # カラムの検出状況を出力
                print(f"検出されたカラム - 日付: {date_column}, ルーム: {room_column}, 予約数: {reservation_column}")

                # 必須カラムの確認
                if date_column is None:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": "CSVファイルに日付を示すカラムが見つかりません"},
                        headers={"Content-Type": "application/json"}
                    )

                if room_column is None:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": "CSVファイルにルーム名を示すカラムが見つかりません"},
                        headers={"Content-Type": "application/json"}
                    )

                # 日付型への変換
                try:
                    df['date'] = pd.to_datetime(df[date_column], errors='coerce')
                    if df['date'].isna().all():
                        # 別の形式を試す
                        print("標準フォーマットでの日付変換に失敗しました。他の形式を試します。")
                        df['date'] = pd.to_datetime(df[date_column], format='%Y/%m/%d', errors='coerce')
                    if df['date'].isna().all():
                        # さらに別の形式を試す
                        print("2番目のフォーマットでの日付変換も失敗しました。他の形式を試します。")
                        df['date'] = pd.to_datetime(df[date_column], format='%Y年%m月%d日', errors='coerce')
                except Exception as e:
                    print(f"日付変換エラー: {e}")
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": f"日付の変換に失敗しました: {str(e)}"},
                        headers={"Content-Type": "application/json"}
                    )

                # データフレームを整形
                if room_column:
                    df['room'] = df[room_column]

                # 稼働率を計算または変換
                if not occupancy_column and reservation_column and capacity_column:
                    print(f"稼働率を計算します: {reservation_column} / {capacity_column}")
                    df['occupancy_rate'] = (df[reservation_column] / df[capacity_column]) * 100
                elif occupancy_column:
                    # 稼働率カラムがあるが、文字列（パーセント表記）の場合は数値に変換
                    def convert_occupancy(val):
                        if pd.isna(val):
                            return 0
                        if isinstance(val, (int, float)):
                            return float(val)
                        # 文字列の処理
                        if isinstance(val, str):
                            # %記号を削除して数値化
                            val = val.replace('%', '')
                            try:
                                return float(val)
                            except ValueError:
                                return 0
                        return 0

                    print(f"既存の稼働率カラムを変換します: {occupancy_column}")
                    df['occupancy_rate'] = df[occupancy_column].apply(convert_occupancy)
                else:
                    # どちらも利用できない場合はダミーデータを設定
                    df['occupancy_rate'] = 0

                # 整形されたデータを保存
                processed_df = df[['date', 'room', 'occupancy_rate']].copy()

                # 詳細データ（元のフォーマットに近い形で保存）
                details_df = df.copy()

                # 処理結果の保存
                target_file_path = f"uploads/occupancy_{timestamp}.csv"
                details_file_path = f"uploads/occupancy_details_{timestamp}.csv"

                # 日付をYYYY-MM-DD形式に変換
                processed_df['date'] = processed_df['date'].dt.strftime('%Y-%m-%d')
                processed_df.to_csv(target_file_path, index=False)

                # 詳細ファイルに元の日付形式を保存
                if 'date' in details_df.columns:
                    details_df['date'] = details_df['date'].dt.strftime('%Y-%m-%d')
                details_df.to_csv(details_file_path, index=False)

                # ルーム別の稼働率サマリーを計算
                room_summary = {}
                for room in processed_df['room'].unique():
                    if pd.isna(room):
                        continue
                    room_data = processed_df[processed_df['room'] == room]
                    if len(room_data) > 0:
                        try:
                            avg_rate = room_data['occupancy_rate'].astype(float).mean()
                            min_rate = room_data['occupancy_rate'].astype(float).min()
                            max_rate = room_data['occupancy_rate'].astype(float).max()
                            room_summary[str(room)] = {
                                "average": round(float(avg_rate), 2),
                                "min": round(float(min_rate), 2),
                                "max": round(float(max_rate), 2),
                                "lessons": len(room_data)
                            }
                        except Exception as e:
                            print(f"稼働率統計計算エラー（{room}）: {str(e)}")
                            # エラー時にはデフォルト値を設定
                            room_summary[str(room)] = {
                                "average": 0,
                                "min": 0,
                                "max": 0,
                                "lessons": len(room_data),
                                "error": str(e)
                            }

                # 日付の範囲を取得
                if len(processed_df) > 0:
                    min_date = processed_df['date'].min()
                    max_date = processed_df['date'].max()
                else:
                    min_date = "不明"
                    max_date = "不明"

                return JSONResponse(
                    content={
                        "status": "成功",
                        "file_saved": target_file_path,
                        "details_saved": details_file_path,
                        "total_lessons": len(processed_df),
                        "date_range": {
                            "from": min_date,
                            "to": max_date
                        },
                        "room_summary": room_summary
                    },
                    headers={"Content-Type": "application/json"}
                )
            elif detected_format == "simple":
                # シンプルデータの処理
                print("シンプルフォーマットを処理します")

                # 必要なカラムを確認
                date_column = None
                room_column = None
                status_column = None

                # 日付カラムの検出
                date_candidates = ["日付", "date", "予約日", "Date"]
                for candidate in date_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        date_column = matching_cols[0]
                        break

                # ルームカラムの検出
                room_candidates = ["部屋", "ルーム", "room", "Room"]
                for candidate in room_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        room_column = matching_cols[0]
                        break

                # ステータスカラムの検出
                status_candidates = ["状態", "status", "Status", "予約状態"]
                for candidate in status_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        status_column = matching_cols[0]
                        break

                # 必須カラムの確認
                if date_column is None:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": "CSVファイルに日付を示すカラムが見つかりません"},
                        headers={"Content-Type": "application/json"}
                    )

                if room_column is None:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": "CSVファイルにルーム名を示すカラムが見つかりません"},
                        headers={"Content-Type": "application/json"}
                    )

                # 日付型への変換
                try:
                    df['date'] = pd.to_datetime(df[date_column], errors='coerce')
                except Exception as e:
                    print(f"日付変換エラー: {e}")
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": f"日付の変換に失敗しました: {str(e)}"},
                        headers={"Content-Type": "application/json"}
                    )

                # ルーム名の標準化
                df['room'] = df[room_column]

                # 稼働率の計算（予約状態から）
                if status_column:
                    # ステータスが「予約済み」「利用済み」の場合は1、それ以外は0
                    status_mapping = {
                        '予約': 1, '予約済み': 1, '予約済': 1,
                        '利用': 1, '利用済み': 1, '利用済': 1,
                        '利用予定': 1, '確定': 1,
                        '空き': 0, '未予約': 0, '空室': 0,
                        'キャンセル': 0, 'キャンセル済み': 0, 'キャンセル済': 0
                    }

                    # 日本語のstatusをマッピング
                    def map_status(status):
                        if pd.isna(status):
                            return 0
                        for key, value in status_mapping.items():
                            if key in str(status):
                                return value
                        return 0  # デフォルトは0（未予約扱い）

                    df['reservation_status'] = df[status_column].apply(map_status)

                    # 日付とルームでグループ化して稼働率を計算
                    occupancy_df = df.groupby(['date', 'room'])['reservation_status'].agg(
                        lambda x: sum(x) / len(x) * 100
                    ).reset_index()
                    occupancy_df.rename(columns={'reservation_status': 'occupancy_rate'}, inplace=True)

                    # 結果を整形
                    processed_df = occupancy_df[['date', 'room', 'occupancy_rate']].copy()
                else:
                    # ステータスカラムがない場合は稼働率0とする
                    df['occupancy_rate'] = 0
                    processed_df = df[['date', 'room']].copy()
                    processed_df['occupancy_rate'] = 0

                # 処理結果の保存
                target_file_path = f"uploads/occupancy_{timestamp}.csv"
                details_file_path = f"uploads/occupancy_details_{timestamp}.csv"

                # 日付をYYYY-MM-DD形式に変換
                processed_df['date'] = processed_df['date'].dt.strftime('%Y-%m-%d')
                processed_df.to_csv(target_file_path, index=False)

                # 詳細データを保存
                df.to_csv(details_file_path, index=False)

                # ルーム別の稼働率サマリーを計算
                room_summary = {}
                for room in processed_df['room'].unique():
                    room_data = processed_df[processed_df['room'] == room]
                    if len(room_data) > 0:
                        avg_rate = room_data['occupancy_rate'].mean()
                        min_rate = room_data['occupancy_rate'].min()
                        max_rate = room_data['occupancy_rate'].max()
                        room_summary[str(room)] = {
                            "average": round(avg_rate, 2),
                            "min": round(min_rate, 2),
                            "max": round(max_rate, 2),
                            "days": len(room_data)
                        }

                # 日付の範囲を取得
                if len(processed_df) > 0:
                    min_date = processed_df['date'].min()
                    max_date = processed_df['date'].max()
                else:
                    min_date = "不明"
                    max_date = "不明"

                return JSONResponse(
                    content={
                        "status": "成功",
                        "file_saved": target_file_path,
                        "details_saved": details_file_path,
                        "total_days": len(processed_df),
                        "date_range": {
                            "from": min_date,
                            "to": max_date
                        },
                        "room_summary": room_summary
                    },
                    headers={"Content-Type": "application/json"}
                )
            elif detected_format == "frame":
                # フレームデータの処理
                print("フレームデータ形式を処理します")

                # 必要なカラムを確認
                date_column = None
                room_column = None
                status_column = None

                # 日付カラムの検出
                date_candidates = ["日付", "date", "Date"]
                for candidate in date_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        date_column = matching_cols[0]
                        break

                # ルームカラムの検出
                room_candidates = ["部屋", "ルーム", "room", "Room"]
                for candidate in room_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        room_column = matching_cols[0]
                        break

                # ステータスカラムの検出
                status_candidates = ["状態", "status", "Status", "予約状態"]
                for candidate in status_candidates:
                    matching_cols = [col for col in df.columns if candidate in col]
                    if matching_cols:
                        status_column = matching_cols[0]
                        break

                # 必須カラムの確認
                if date_column is None:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": "CSVファイルに日付を示すカラムが見つかりません"},
                        headers={"Content-Type": "application/json"}
                    )

                if room_column is None:
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": "CSVファイルにルーム名を示すカラムが見つかりません"},
                        headers={"Content-Type": "application/json"}
                    )

                # 日付型への変換
                try:
                    df['date'] = pd.to_datetime(df[date_column], errors='coerce')
                except Exception as e:
                    print(f"日付変換エラー: {e}")
                    return JSONResponse(
                        status_code=400,
                        content={"status": "エラー", "detail": f"日付の変換に失敗しました: {str(e)}"},
                        headers={"Content-Type": "application/json"}
                    )

                # ルームカラムの標準化
                df['room'] = df[room_column]

                # 稼働率計算 (フレームデータの場合はステータスから計算)
                if status_column:
                    # 予約済みステータスのマッピング
                    occupied_statuses = ['予約済み', '予約済', '利用', '利用済み', '利用済', '予約', '確定']

                    # ステータスに基づいて稼働率に変換 (0% または 100%)
                    def status_to_occupancy(status):
                        if pd.isna(status):
                            return 0
                        for s in occupied_statuses:
                            if s in str(status):
                                return 100  # 予約済み=100%稼働
                        return 0  # それ以外=0%稼働

                    df['occupancy_rate'] = df[status_column].apply(status_to_occupancy)
                else:
                    # ステータスカラムがない場合はすべて0%とする
                    df['occupancy_rate'] = 0

                # 日付とルームでグループ化して平均稼働率を計算
                if len(df) > 0:
                    occupancy_df = df.groupby(['date', 'room'])['occupancy_rate'].mean().reset_index()
                    processed_df = occupancy_df.copy()
                else:
                    # データがない場合の処理
                    processed_df = pd.DataFrame(columns=['date', 'room', 'occupancy_rate'])

                # 処理結果の保存
                target_file_path = f"uploads/occupancy_{timestamp}.csv"
                details_file_path = f"uploads/occupancy_details_{timestamp}.csv"

                # 日付をYYYY-MM-DD形式に変換
                processed_df['date'] = processed_df['date'].dt.strftime('%Y-%m-%d')
                processed_df.to_csv(target_file_path, index=False)

                # 詳細データを保存
                df.to_csv(details_file_path, index=False)

                # ルーム別の稼働率サマリーを計算
                room_summary = {}
                for room in processed_df['room'].unique():
                    room_data = processed_df[processed_df['room'] == room]
                    if len(room_data) > 0:
                        avg_rate = room_data['occupancy_rate'].mean()
                        min_rate = room_data['occupancy_rate'].min()
                        max_rate = room_data['occupancy_rate'].max()
                        room_summary[str(room)] = {
                            "average": round(avg_rate, 2),
                            "min": round(min_rate, 2),
                            "max": round(max_rate, 2),
                            "days": len(room_data)
                        }

                # 日付の範囲を取得
                if len(processed_df) > 0:
                    min_date = processed_df['date'].min()
                    max_date = processed_df['date'].max()
                else:
                    min_date = "不明"
                    max_date = "不明"

                return JSONResponse(
                    content={
                        "status": "成功",
                        "file_saved": target_file_path,
                        "details_saved": details_file_path,
                        "total_days": len(processed_df),
                        "date_range": {
                            "from": min_date,
                            "to": max_date
                        },
                        "room_summary": room_summary
                    },
                    headers={"Content-Type": "application/json"}
                )
            else:
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
                        "auto_detected_type": detected_format
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
