from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from io import StringIO
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from pydantic import BaseModel

app = FastAPI(title="サウナ分析ダッシュボードAPI")

# CORSを有効にして、Reactからのリクエストを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンに制限すべき
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

@app.get("/")
def read_root():
    return {"message": "サウナ分析ダッシュボードAPI", "version": "1.0.0"}

@app.get("/api/dashboard-data")
def get_dashboard_data():
    """ダッシュボード全体のデータを取得"""
    return dashboard_data

@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...), data_type: str = "members"):
    """CSVファイルをアップロードして処理する"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")

    try:
        # ファイルの内容を読み込む
        contents = await file.read()
        # バイナリデータを文字列に変換
        csv_data = StringIO(contents.decode('utf-8-sig'))

        # pandasでCSVを読み込む
        df = pd.read_csv(csv_data)

        # データタイプに応じて処理
        if data_type == "members":
            process_members_data(df)
        elif data_type == "utilization":
            process_utilization_data(df)
        elif data_type == "competitors":
            process_competitors_data(df)
        elif data_type == "finance":
            process_finance_data(df)
        else:
            raise HTTPException(status_code=400, detail=f"不明なデータタイプ: {data_type}")

        # ファイルを保存
        file_path = os.path.join(UPLOAD_DIR, f"{data_type}_{file.filename}")
        with open(file_path, "wb") as f:
            # ファイルポインタを先頭に戻す
            await file.seek(0)
            f.write(await file.read())

        return {
            "filename": file.filename,
            "data_type": data_type,
            "rows": len(df),
            "columns": list(df.columns),
            "save_path": file_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSVファイルの処理中にエラーが発生しました: {str(e)}")

def process_members_data(df: pd.DataFrame):
    """会員データを処理する"""
    # データの検証
    required_columns = ["member_id", "gender", "age_group", "region", "join_date"]
    if not all(col in df.columns for col in required_columns):
        raise HTTPException(status_code=400, detail="必要なカラムが不足しています: " + ", ".join(required_columns))

    # 会員データの基本集計
    total_members = len(df)
    active_members = len(df[df['status'] == 'active']) if 'status' in df.columns else total_members

    # 性別分布
    gender_counts = df['gender'].value_counts().to_dict()

    # 年齢層分布
    age_counts = df['age_group'].value_counts().to_dict()

    # 地域分布
    region_counts = df['region'].value_counts().to_dict()

    # データをグローバル変数に設定
    dashboard_data.members = {
        "total": total_members,
        "active": active_members,
        "gender_distribution": gender_counts,
        "age_distribution": age_counts,
        "region_distribution": region_counts
    }

    # 入会率と退会率を計算
    if active_members > 0 and total_members > 0:
        dashboard_data.metrics = {
            "total_members": total_members,
            "active_members": active_members,
            "join_rate": (active_members / total_members) * 100,
            "churn_rate": ((total_members - active_members) / total_members) * 100
        }

def process_utilization_data(df: pd.DataFrame):
    """稼働率データを処理する"""
    # データの検証
    required_columns = ["date", "room", "occupancy_rate"]
    if not all(col in df.columns for col in required_columns):
        raise HTTPException(status_code=400, detail="必要なカラムが不足しています: " + ", ".join(required_columns))

    # 日付カラムをdatetime型に変換
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.strftime('%Y-%m')
    df['day_of_week'] = df['date'].dt.day_name()

    # 部屋ごとの平均稼働率
    room_avg_rates = df.groupby('room')['occupancy_rate'].mean().to_dict()

    # 月別の稼働率
    monthly_rates = df.groupby(['month', 'room'])['occupancy_rate'].mean().unstack().to_dict()

    # 曜日別稼働率
    weekday_rates = df.groupby(['day_of_week', 'room'])['occupancy_rate'].mean().unstack().to_dict()

    # データをグローバル変数に設定
    dashboard_data.utilization = {
        "room_avg_rates": room_avg_rates,
        "monthly_rates": monthly_rates,
        "weekday_rates": weekday_rates
    }

def process_competitors_data(df: pd.DataFrame):
    """競合データを処理する"""
    # データの検証
    required_columns = ["name", "location", "hourly_rate"]
    if not all(col in df.columns for col in required_columns):
        raise HTTPException(status_code=400, detail="必要なカラムが不足しています: " + ", ".join(required_columns))

    # 競合の価格比較データ
    price_comparison = df[['name', 'hourly_rate']].set_index('name').to_dict()['hourly_rate']

    # 競合詳細情報
    competitor_details = df.to_dict(orient='records')

    # 地域分布
    if 'area' in df.columns:
        area_distribution = df['area'].value_counts().to_dict()
    else:
        area_distribution = {}

    # データをグローバル変数に設定
    dashboard_data.competitors = {
        "price_comparison": price_comparison,
        "competitor_details": competitor_details,
        "area_distribution": area_distribution
    }

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

# サーバー起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
