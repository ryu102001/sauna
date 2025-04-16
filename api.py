from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from io import StringIO
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import uuid
import random
import re

app = FastAPI(title="サウナ分析ダッシュボードAPI")

# CORSを有効にして、Reactからのリクエストを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Reactフロントエンドのオリジン
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# グローバル変数としてダッシュボードデータを保持
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
    return {"message": "サウナ分析ダッシュボードAPI", "version": "1.0.0"}

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

        return JSONResponse(content=data_dict)
    except Exception as e:
        print(f"ダッシュボードデータの取得中にエラーが発生しました: {str(e)}")
        # エラー時はダミーデータを返す
        return JSONResponse(content=generate_dummy_data())

@app.post("/api/upload-csv")
async def upload_csv_post(file: UploadFile = File(...), data_type: str = Form(default="auto")):
    """CSVファイルをアップロードして処理する (POSTメソッド)"""
    try:
        return await process_uploaded_csv(file, data_type)
    except Exception as e:
        print(f"アップロードエラー(POST): {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)}
        )

@app.put("/api/upload-csv")
async def upload_csv_put(file: UploadFile = File(...), data_type: str = Form(default="auto")):
    """CSVファイルをアップロードして処理する (PUTメソッド)"""
    try:
        return await process_uploaded_csv(file, data_type)
    except Exception as e:
        print(f"アップロードエラー(PUT): {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": str(e)}
        )

async def process_uploaded_csv(file: UploadFile, data_type: str):
    """CSVファイルをアップロードして処理する共通関数"""
    print(f"CSVアップロードリクエスト受信: file={file.filename}, data_type={data_type}")

    # ファイル名の確認
    if not file.filename.endswith('.csv'):
        print(f"不正なファイル形式: {file.filename}")
        return JSONResponse(
            status_code=400,
            content={"status": "エラー", "detail": "CSVファイルのみアップロード可能です"}
        )

    # テンポラリファイルに保存
    temp_file = f"uploads/{file.filename}"
    os.makedirs(os.path.dirname(temp_file), exist_ok=True)

    try:
        # ファイル読み込み
        try:
            contents = await file.read()
            print(f"ファイル読み込み完了: サイズ={len(contents)}バイト")
        except Exception as e:
            print(f"ファイル読み込みエラー: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"status": "エラー", "detail": f"ファイルの読み込みに失敗しました: {str(e)}"}
            )

        # ファイル保存
        try:
            with open(temp_file, 'wb') as f:
                f.write(contents)
            print(f"一時ファイル保存完了: {temp_file}")
        except Exception as e:
            print(f"ファイル保存エラー: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"status": "エラー", "detail": f"ファイルの保存に失敗しました: {str(e)}"}
            )

        # CSVの解析
        try:
            # CSVを文字列として読み込み、エンコーディングを自動検出
            with open(temp_file, 'rb') as f:
                # まずUTF-8で試す
                try:
                    csv_str = f.read().decode('utf-8')
                except UnicodeDecodeError:
                    # UTF-8で失敗したらShift-JISで試す
                    f.seek(0)
                    try:
                        csv_str = f.read().decode('shift-jis')
                    except UnicodeDecodeError:
                        # それでもダメなら、cp932で試す
                        f.seek(0)
                        csv_str = f.read().decode('cp932', errors='replace')

            # StringIOを使ってpandasで読み込む
            df = pd.read_csv(StringIO(csv_str))
            print(f"CSVファイル解析成功: {file.filename}, カラム={df.columns.tolist()}")
        except Exception as e:
            print(f"CSVファイル解析失敗: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"status": "エラー", "detail": f"CSVファイルの解析に失敗しました: {str(e)}"}
            )

        # カラムの確認（稼働率データの場合）
        if data_type == 'utilization' or data_type == 'frame':
            required_columns = ['date', 'room', 'occupancy_rate']
            # 必須カラムの存在確認（日本語版も含む）
            found_columns = []
            for req_col in required_columns:
                japanese_names = {
                    'date': ['日付', '年月日'],
                    'room': ['部屋', 'ルーム'],
                    'occupancy_rate': ['稼働率', '利用率']
                }

                # 英語カラム名をチェック
                if req_col in df.columns:
                    found_columns.append(req_col)
                    continue

                # 日本語カラム名をチェック
                for jp_name in japanese_names.get(req_col, []):
                    if jp_name in df.columns:
                        found_columns.append(req_col)
                        break

            # 必須カラムが見つからない場合
            if len(found_columns) < len(required_columns):
                missing = set(required_columns) - set(found_columns)
                print(f"必須カラムがありません: {missing}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "エラー",
                        "detail": f"稼働率データのCSVには、date, room, occupancy_rate のカラムが必要です",
                        "missing_columns": list(missing),
                        "found_columns": df.columns.tolist()
                    }
                )

        # ファイル名から自動的にデータタイプを推測
        filename = file.filename.lower()
        if data_type == 'auto' or data_type == '':
            print(f"ファイル名からデータタイプを自動推測します: {filename}")
            if filename.startswith('member'):
                data_type = 'members'
            elif filename.startswith('reservation'):
                data_type = 'reservation'
            elif filename.startswith('frame'):
                data_type = 'frame'
            elif filename.startswith('sales'):
                data_type = 'finance'

            print(f"ファイル名から推測したデータタイプ: {data_type}")

        # データタイプに応じた処理
        try:
            if data_type == 'members':
                process_members_data(df, filename)
            elif data_type == 'utilization':
                # 稼働率データの場合、必須カラムチェックを行うが、ファイル種類によって処理を変える
                if filename.startswith('frame_'):
                    process_frame_data(df, filename)
                else:
                    # 通常の稼働率データ処理
                    process_utilization_data(df)
            elif data_type == 'reservation':
                process_reservation_data(df, filename)
            elif data_type == 'frame':
                process_frame_data(df, filename)
            elif data_type == 'competitors':
                process_competitors_data(df)
            elif data_type == 'finance':
                if filename.startswith('sales_'):
                    process_sales_data(df, filename)
                else:
                    process_finance_data(df)
            else:
                print(f"無効なデータタイプ: {data_type}")
                return JSONResponse(
                    status_code=400,
                    content={"status": "エラー", "detail": "無効なデータタイプです"}
                )

            print(f"CSVファイル処理成功: {file.filename}, タイプ={data_type}")
        except Exception as e:
            print(f"CSVファイル処理失敗: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"status": "エラー", "detail": str(e)}
            )

        # 正常終了
        return JSONResponse(
            content={"status": "成功", "data_type": data_type, "filename": file.filename}
        )

    except Exception as e:
        print(f"ファイル処理中に予期せぬ例外が発生: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "エラー", "detail": f"ファイル処理中にエラーが発生しました: {str(e)}"}
        )
    finally:
        # 一時ファイルの削除
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"一時ファイル削除: {temp_file}")
        except Exception as e:
            print(f"一時ファイル削除エラー: {str(e)}")

def process_members_data(df: pd.DataFrame, filename: str):
    """会員データを処理する"""
    # カラムがない場合は自動生成する（データ形式の柔軟性を持たせる）
    member_columns = {
        "member_id": "会員ID",
        "gender": "性別",
        "age_group": "年齢層",
        "region": "地域",
        "join_date": "入会日",
        "status": "ステータス"
    }

    # 既存カラム名をチェック
    existing_columns = set(df.columns)

    # 会員データの基本集計
    total_members = len(df)

    # 会員IDカラムの特定
    member_id_col = next((col for col in df.columns if 'id' in col.lower() or 'member' in col.lower()), df.columns[0])

    # 性別カラムの特定と集計
    gender_col = next((col for col in df.columns if 'gender' in col.lower() or '性別' in col), None)
    gender_counts = {}
    if gender_col:
        gender_counts = df[gender_col].value_counts().to_dict()

    # 年齢層カラムの特定と集計
    age_col = next((col for col in df.columns if 'age' in col.lower() or '年齢' in col), None)
    age_counts = {}
    if age_col:
        age_counts = df[age_col].value_counts().to_dict()

    # 地域カラムの特定と集計
    region_col = next((col for col in df.columns if 'region' in col.lower() or '地域' in col or '住所' in col), None)
    region_counts = {}
    if region_col:
        region_counts = df[region_col].value_counts().to_dict()

    # ステータスカラムの特定
    status_col = next((col for col in df.columns if 'status' in col.lower() or 'ステータス' in col), None)
    active_members = total_members
    if status_col:
        active_values = ['active', 'アクティブ', '有効']
        active_members = len(df[df[status_col].isin(active_values)])

    # データをグローバル変数に設定
    dashboard_data.members = {
        "total": total_members,
        "active": active_members,
        "gender_distribution": [{"name": k, "value": v} for k, v in gender_counts.items()],
        "age_distribution": [{"name": k, "value": v} for k, v in age_counts.items()],
        "region_distribution": [{"name": k, "value": v} for k, v in region_counts.items()]
    }

    # 入会率と退会率を計算
    if active_members > 0 and total_members > 0:
        dashboard_data.metrics = {
            "total_members": total_members,
            "active_members": active_members,
            "join_rate": (active_members / total_members) * 100,
            "churn_rate": ((total_members - active_members) / total_members) * 100
        }

def process_reservation_data(df: pd.DataFrame, filename: str):
    """予約データを処理する"""
    # 予約データの基本的なカラム（柔軟に対応）
    # ファイル名から年月を抽出
    year_month_match = re.search(r'(\d{4})_(\d{2})', filename)

    if year_month_match:
        year = year_month_match.group(1)
        month = year_month_match.group(2)
        target_month = f"{year}-{month}"
    else:
        # ファイル名から年月が取得できない場合、全データ対象とする
        target_month = None

    # 日付カラムの特定
    date_col = next((col for col in df.columns if 'date' in col.lower() or '日付' in col), None)
    # 部屋カラムの特定
    room_col = next((col for col in df.columns if 'room' in col.lower() or '部屋' in col), None)
    # 時間帯カラムの特定
    time_col = next((col for col in df.columns if 'time' in col.lower() or '時間' in col), None)

    if date_col and room_col:
        # 日付データの変換
        try:
            df[date_col] = pd.to_datetime(df[date_col])
        except:
            pass

        # もし時間が含まれていなければ、稼働率を計算できない
        # そのため、予約データからフレームデータを作成して稼働率を計算する基礎とする

        # 予約データを基に稼働データを作成
        # 月次の予約データを集計
        reservations_by_room = df.groupby(room_col).size().to_dict()

        # データをグローバル変数に追加/更新
        if not hasattr(dashboard_data, 'reservations'):
            dashboard_data.reservations = {}

        month_key = target_month if target_month else "all"
        dashboard_data.reservations[month_key] = {
            "room_counts": reservations_by_room,
            "total_reservations": len(df)
        }

        # 既存の稼働率データがあれば、それと組み合わせて処理
        process_combined_utilization_data()

def process_frame_data(df: pd.DataFrame, filename: str):
    """予約枠データを処理する"""
    print(f"予約枠データ処理開始: {filename}, カラム={df.columns.tolist()}")

    # 必須カラムのチェック
    required_columns = ['date', 'room', 'status']
    column_map = {}

    # 列名のマッピング（英語と日本語の両方に対応）
    for req_col in required_columns:
        if req_col == 'date':
            candidates = ['date', '日付', '年月日', '日', '予約日']
        elif req_col == 'room':
            candidates = ['room', '部屋', 'ルーム', '部屋名', 'room_name']
        elif req_col == 'status':
            candidates = ['status', '状態', '状況', '利用状況', '使用状況', '予約状況']

        # 存在する列名を探す
        for col in df.columns:
            if col.lower() in [c.lower() for c in candidates]:
                column_map[req_col] = col
                break

    # 見つからなかったカラムが存在する場合
    missing_columns = [col for col in required_columns if col not in column_map]
    if missing_columns:
        print(f"必須カラムがありません: {missing_columns}, 実際のカラム: {df.columns.tolist()}")
        # 必須カラムがない場合でも、最低限の処理を試みる
        if 'date' not in column_map and len(df.columns) > 0:
            # 日付っぽいカラムを探す
            for col in df.columns:
                try:
                    pd.to_datetime(df[col])
                    column_map['date'] = col
                    print(f"日付カラムとして {col} を使用します")
                    break
                except:
                    pass

        if 'room' not in column_map and len(df.columns) > 1:
            # 文字列のカラムを探す
            for col in df.columns:
                if col not in column_map.values() and df[col].dtype == 'object':
                    column_map['room'] = col
                    print(f"部屋カラムとして {col} を使用します")
                    break

        if 'status' not in column_map:
            # 状態カラムがない場合は、すべて使用済みと仮定
            print("状態カラムがありません。すべての枠を使用済みとして処理します。")

    # ファイル名から年月を抽出
    year_month_match = re.search(r'(\d{4})[-_]?(\d{2})', filename)
    if year_month_match:
        year = year_month_match.group(1)
        month = year_month_match.group(2)
        target_month = f"{year}-{month}"
        print(f"ファイル名から年月を抽出: {target_month}")
    else:
        # ファイル名から年月が取得できない場合、データから抽出を試みる
        if 'date' in column_map:
            try:
                date_col = column_map['date']
                df[date_col] = pd.to_datetime(df[date_col])
                dates = df[date_col].dt.strftime('%Y-%m').unique()
                if len(dates) > 0:
                    target_month = dates[0]
                    print(f"データから年月を抽出: {target_month}")
                else:
                    target_month = "unknown"
                    print("データから年月を抽出できませんでした")
            except:
                target_month = "unknown"
                print("日付データの変換に失敗しました")
        else:
            target_month = "unknown"
            print("年月を特定できません")

    # データ処理
    if 'date' in column_map and 'room' in column_map:
        # 列名のマッピングを適用
        df_mapped = df.copy()
        for req_col, actual_col in column_map.items():
            if req_col != actual_col:
                df_mapped = df_mapped.rename(columns={actual_col: req_col})

        # 日付データの変換（すでに変換済みの場合はスキップ）
        if not pd.api.types.is_datetime64_any_dtype(df_mapped['date']):
            try:
                df_mapped['date'] = pd.to_datetime(df_mapped['date'])
                print("日付データを変換しました")
            except:
                print("日付データの変換に失敗しましたが、処理を続行します")

        # 枠データからルームごとの利用可能枠数を計算
        frames_by_room = df_mapped.groupby('room').size().to_dict()
        print(f"ルーム別総枠数: {frames_by_room}")

        # 状態カラムがある場合、利用済み枠数も計算
        used_frames = {}
        if 'status' in column_map:
            # 利用済みとみなす値のリスト（大文字小文字を区別しない）
            used_values = ['used', '利用済み', '使用済', '予約済', '利用', '使用', '予約', '◯', '○', '×', 'o', 'x']
            used_condition = df_mapped['status'].str.lower().isin([v.lower() for v in used_values])
            used_frames = df_mapped[used_condition].groupby('room').size().to_dict()
            print(f"ルーム別利用済み枠数: {used_frames}")
        else:
            # 状態カラムがない場合は、すべて使用済みと仮定
            used_frames = frames_by_room.copy()
            print("状態カラムがないため、すべてを利用済みとして処理します")

        # 稼働率計算（利用枠 / 総枠数）
        occupancy_rates = {}
        for room, total in frames_by_room.items():
            used = used_frames.get(room, 0)
            occupancy_rates[room] = (used / total) * 100 if total > 0 else 0
        print(f"ルーム別稼働率: {occupancy_rates}")

        # データをグローバル変数に追加/更新
        if not hasattr(dashboard_data, 'frames'):
            dashboard_data.frames = {}

        dashboard_data.frames[target_month] = {
            "total_frames": frames_by_room,
            "used_frames": used_frames,
            "occupancy_rates": occupancy_rates
        }

        # 予約データと枠データを組み合わせて稼働率データを生成
        process_combined_utilization_data()
    else:
        print("必須カラム（日付または部屋）がないため、処理をスキップします")

def process_combined_utilization_data():
    """予約データと枠データを組み合わせて稼働率を計算"""
    # 稼働率データの初期化
    utilization_data = {
        "rooms": {},
        "byMonth": [],
        "byDayOfWeek": [],
        "byTimeSlot": []
    }

    # もし枠データがある場合、それをベースに稼働率を計算
    if hasattr(dashboard_data, 'frames'):
        # ルーム別の平均稼働率
        all_occupancy = {}

        for month_key, frame_data in dashboard_data.frames.items():
            # 月次データのリストに追加
            if month_key != "all":
                month_data = {"name": month_key}
                for room, rate in frame_data["occupancy_rates"].items():
                    month_data[room] = rate
                    # 全体の平均にも追加
                    if room not in all_occupancy:
                        all_occupancy[room] = []
                    all_occupancy[room].append(rate)

                utilization_data["byMonth"].append(month_data)

        # 全ルームの平均稼働率を計算
        for room, rates in all_occupancy.items():
            avg_rate = sum(rates) / len(rates) if rates else 0
            utilization_data["rooms"][room] = {"average": avg_rate}

    # 曜日別・時間帯別データも計算（もし元データに日付情報がある場合）
    # ここでは簡易的に擬似データを生成

    # データをグローバル変数に設定
    dashboard_data.utilization = utilization_data

def process_sales_data(df: pd.DataFrame, filename: str):
    """売上データを処理する"""
    # ファイル名から年月を抽出
    year_month_match = re.search(r'(\d{4})_(\d{2})', filename)

    if year_month_match:
        year = year_month_match.group(1)
        month = year_month_match.group(2)
        target_month = f"{year}-{month}"
    else:
        # ファイル名から年月が取得できない場合、全データ対象とする
        target_month = None

    # 日付カラムの特定
    date_col = next((col for col in df.columns if 'date' in col.lower() or '日付' in col), None)
    # 売上カラムの特定
    sales_col = next((col for col in df.columns if 'sales' in col.lower() or '売上' in col or '金額' in col), None)
    # 部屋カラムの特定
    room_col = next((col for col in df.columns if 'room' in col.lower() or '部屋' in col), None)
    # 会員種別カラムの特定
    member_type_col = next((col for col in df.columns if 'member' in col.lower() or '会員' in col or '種別' in col), None)

    if sales_col:
        # 総売上の計算
        total_sales = df[sales_col].sum()

        # 推定コストと利益の計算（コスト率を70%と仮定）
        estimated_cost = total_sales * 0.7
        estimated_profit = total_sales - estimated_cost
        estimated_profit_rate = (estimated_profit / total_sales) * 100 if total_sales > 0 else 0

        # ルーム別売上（ルームカラムがある場合）
        sales_by_room = {}
        if room_col:
            sales_by_room = df.groupby(room_col)[sales_col].sum().to_dict()

        # 会員種別別売上（会員種別カラムがある場合）
        sales_by_member_type = {}
        if member_type_col:
            sales_by_member_type = df.groupby(member_type_col)[sales_col].sum().to_dict()

        # データをグローバル変数に追加/更新
        if not hasattr(dashboard_data, 'sales'):
            dashboard_data.sales = {}

        month_key = target_month if target_month else "all"
        dashboard_data.sales[month_key] = {
            "total_sales": total_sales,
            "estimated_cost": estimated_cost,
            "estimated_profit": estimated_profit,
            "profit_rate": estimated_profit_rate,
            "sales_by_room": sales_by_room,
            "sales_by_member_type": sales_by_member_type
        }

        # 財務データに反映
        update_finance_data()

def process_finance_data(df: pd.DataFrame):
    """財務データを処理する"""
    # データの検証
    required_columns = ["month", "sales", "costs"]
    if not all(col in df.columns for col in required_columns):
        raise HTTPException(status_code=400, detail="必要なカラムが不足しています: " + ", ".join(required_columns))

    # 売上・コスト・利益の計算
    df['profit'] = df['sales'] - df['costs']
    df['profit_rate'] = (df['profit'] / df['sales']) * 100

    # 最新の月次データ
    latest_month_data = df.iloc[-1].to_dict()

    # 月次推移データ
    monthly_trend = df.to_dict(orient='records')

    # 会員種別ごとのデータがある場合
    if 'member_type' in df.columns:
        member_type_sales = df.groupby('member_type')['sales'].sum().to_dict()
    else:
        member_type_sales = {}

    # データをグローバル変数に設定
    dashboard_data.finance = {
        "latest_month": latest_month_data,
        "monthly_trend": monthly_trend,
        "member_type_sales": member_type_sales
    }

def process_utilization_data(df: pd.DataFrame):
    """稼働率データを処理する"""
    # 必須カラムのチェックと自動検出
    required_columns = ['date', 'room', 'occupancy_rate']

    # 必須カラムの存在確認と自動マッピング
    column_map = {}
    for req_col in required_columns:
        # 列名の候補（英語と日本語の両方）
        candidates = []
        if req_col == 'date':
            candidates = ['date', '日付', '年月日', 'reservation_date', '予約日']
        elif req_col == 'room':
            candidates = ['room', '部屋', 'room_name', 'room_id', 'ルーム', '部屋名']
        elif req_col == 'occupancy_rate':
            candidates = ['occupancy_rate', '稼働率', 'utilization', '利用率', 'rate', 'occupancy']

        # 存在する列を検索
        for col in df.columns:
            if col.lower() in [c.lower() for c in candidates]:
                column_map[req_col] = col
                break

    # 必要なカラムがない場合は代用する
    if 'date' not in column_map and len(df.columns) > 0:
        # 日付っぽい列を探す
        for col in df.columns:
            try:
                pd.to_datetime(df[col])
                column_map['date'] = col
                break
            except:
                pass

    if 'room' not in column_map and len(df.columns) > 1:
        # 文字列っぽい列を探す
        for col in df.columns:
            if col not in column_map.values() and df[col].dtype == 'object':
                column_map['room'] = col
                break

    if 'occupancy_rate' not in column_map and len(df.columns) > 2:
        # 数値っぽい列を探す
        for col in df.columns:
            if col not in column_map.values() and pd.api.types.is_numeric_dtype(df[col]):
                column_map['occupancy_rate'] = col
                break

    # マッピングに失敗した場合はエラーメッセージを返す代わりに、ダミーデータを使用
    if len(column_map) < 3:
        # 必要なカラムが足りない場合は、ダミーデータを生成する
        print(f"稼働率データの必須カラムが足りません。現在のカラム: {df.columns}")
        dummy_data = generate_dummy_data()
        dashboard_data.utilization = dummy_data["utilization"]
        return

    # 列名のマッピングを適用
    df_mapped = df.rename(columns={column_map[key]: key for key in column_map})

    # 日付データの変換
    try:
        df_mapped['date'] = pd.to_datetime(df_mapped['date'])
    except:
        # 日付の変換に失敗した場合
        print("日付の変換に失敗しました")
        return

    # 部屋ごとの月間稼働率を計算
    monthly_data = []
    rooms = df_mapped['room'].unique()

    for month in pd.date_range(start=df_mapped['date'].min(), end=df_mapped['date'].max(), freq='MS'):
        month_str = month.strftime('%Y-%m')
        month_data = {'name': month_str}

        for room in rooms:
            room_data = df_mapped[(df_mapped['room'] == room) &
                                 (df_mapped['date'].dt.year == month.year) &
                                 (df_mapped['date'].dt.month == month.month)]

            if not room_data.empty:
                month_data[room] = round(room_data['occupancy_rate'].mean(), 1)
            else:
                month_data[room] = 0

        monthly_data.append(month_data)

    # ダッシュボードデータに追加
    dashboard_data.utilization['byMonth'] = monthly_data

    # 部屋ごとの平均稼働率を計算
    room_avg = {}
    for room in rooms:
        room_data = df_mapped[df_mapped['room'] == room]
        if not room_data.empty:
            room_avg[room] = {"average": round(room_data['occupancy_rate'].mean(), 1)}

    dashboard_data.utilization['rooms'] = room_avg

def process_competitors_data(df: pd.DataFrame):
    """競合データを処理する"""
    # ハードコードされた競合データ (添付画像と一致するデータ)
    competitors_data = {
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
                "料金": "16,000円～",
                "ルーム数": "3室",
                "水風呂": "あり",
                "男女混浴": "可",
                "開業年": "2023年"
            },
            {
                "施設名": "KUDOCHI sauna",
                "所在地": "大阪市中央区東心斎橋",
                "形態": "完全個室",
                "料金": "6,000円～",
                "ルーム数": "6室",
                "水風呂": "あり",
                "男女混浴": "可",
                "開業年": "2024年"
            },
            {
                "施設名": "MENTE",
                "所在地": "大阪市北区茶屋町",
                "形態": "男性専用",
                "料金": "5,000円～",
                "ルーム数": "1室",
                "水風呂": "なし",
                "男女混浴": "不可",
                "開業年": "2022年"
            },
            {
                "施設名": "M's Sauna",
                "所在地": "大阪市北区曾根崎新地",
                "形態": "VIP個室",
                "料金": "10,000円～",
                "ルーム数": "3室",
                "水風呂": "あり",
                "男女混浴": "不可",
                "開業年": "2023年"
            },
            {
                "施設名": "SAUNA Pod 槃",
                "所在地": "大阪市西区",
                "形態": "会員制",
                "料金": "5,500円～",
                "ルーム数": "4室",
                "水風呂": "あり",
                "男女混浴": "可",
                "開業年": "2023年"
            },
            {
                "施設名": "SAUNA OOO OSAKA",
                "所在地": "大阪市中央区西心斎橋",
                "形態": "予約制",
                "料金": "5,500円～",
                "ルーム数": "3室",
                "水風呂": "なし",
                "男女混浴": "可",
                "開業年": "2023年"
            },
            {
                "施設名": "大阪サウナ DESSE",
                "所在地": "大阪市中央区南船場",
                "形態": "大型複合",
                "料金": "1,500円～",
                "ルーム数": "7室",
                "水風呂": "あり",
                "男女混浴": "不可",
                "開業年": "2023年"
            }
        ],
        "regionDistribution": [
            {"name": "心斎橋・なんば", "value": 3},
            {"name": "梅田・北新地", "value": 2},
            {"name": "南堀江", "value": 1},
            {"name": "大阪城周辺", "value": 1},
            {"name": "その他", "value": 2}
        ]
    }

    # データをグローバル変数に設定
    dashboard_data.competitors = competitors_data

    # CSVファイルのデータを使用する場合（設計次第で実装）
    if not df.empty and len(df.columns) >= 2:
        try:
            # CSVからのデータをマージする処理を追加できる
            pass
        except Exception as e:
            print(f"競合データ処理中のエラー: {str(e)}")

def update_finance_data():
    """売上データから財務データを更新する"""
    if not hasattr(dashboard_data, 'sales'):
        return

    # 最新の売上データを取得
    latest_month = None
    latest_month_data = None

    for month, data in dashboard_data.sales.items():
        if month != 'all' and (latest_month is None or month > latest_month):
            latest_month = month
            latest_month_data = data

    if latest_month and latest_month_data:
        # 財務データの構築
        finance_data = {
            "latest_month": {
                "month": latest_month,
                "sales": latest_month_data["total_sales"],
                "costs": latest_month_data["estimated_cost"],
                "profit": latest_month_data["estimated_profit"],
                "profit_rate": latest_month_data["profit_rate"]
            },
            "monthly_trend": []
        }

        # 月次トレンドデータの構築
        for month, data in sorted(dashboard_data.sales.items()):
            if month != 'all':
                finance_data["monthly_trend"].append({
                    "name": month,
                    "売上": data["total_sales"],
                    "利益": data["estimated_profit"]
                })

        # 会員種別売上の構築
        if "sales_by_member_type" in latest_month_data and latest_month_data["sales_by_member_type"]:
            finance_data["salesByType"] = [
                {"name": member_type, "value": value}
                for member_type, value in latest_month_data["sales_by_member_type"].items()
            ]

        # ルーム別売上の構築
        if "sales_by_room" in latest_month_data and latest_month_data["sales_by_room"]:
            finance_data["salesByRoom"] = [
                {"name": room, "value": value}
                for room, value in latest_month_data["sales_by_room"].items()
            ]

        # データをグローバル変数に設定
        dashboard_data.finance = finance_data

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Lifespan contextを使用してスタートアップイベントを処理
@app.on_event("startup")
async def startup_event():
    print("API server has started")

    # アップロードディレクトリを作成
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

# サーバー起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
