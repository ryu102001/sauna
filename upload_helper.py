#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import sys
import json
import pandas as pd  # データの前処理用にpandasをインポート

def upload_csv(file_path, data_type="occupancy", port=8000):
    """
    CSVファイルをAPIサーバーにアップロードする

    Args:
        file_path: アップロードするCSVファイルのパス
        data_type: データの種類（occupancy, sales, memberのいずれか）
        port: APIサーバーのポート番号

    Returns:
        レスポンスのJSON
    """
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"エラー: ファイル {file_path} が見つかりません")
        return None

    # APIエンドポイントURL
    url = f"http://localhost:{port}/api/upload-csv"

    # 使用するポート番号を表示
    print(f"使用ポート: {port}")

    # CSVファイルの分析（レッスンデータかどうかを確認）
    try:
        df = pd.read_csv(file_path)
        columns = df.columns.tolist()
        print(f"CSVファイルの列名: {columns}")

        # レッスンフォーマット検出
        is_lesson_format = any("レッスン日" in col for col in columns) and any("ルーム名" in col for col in columns)
        if is_lesson_format:
            print("レッスン予約フォーマットを検出しました")

            # ルーム別の予約状況を出力
            for room in df["ルーム名"].unique():
                room_data = df[df["ルーム名"] == room]
                print(f"{room}の予約: {len(room_data)}件")

                # 稼働率の状況
                if "稼働率" in columns:
                    occupancy_sum = 0
                    try:
                        # 稼働率が数値でない場合の処理
                        occupancy_values = []
                        for val in room_data["稼働率"]:
                            if isinstance(val, str) and '%' in val:
                                occupancy_values.append(float(val.replace('%', '')))
                            elif isinstance(val, (int, float)):
                                occupancy_values.append(float(val))
                        if occupancy_values:
                            avg_occupancy = sum(occupancy_values) / len(occupancy_values)
                            print(f"{room}の平均稼働率: {avg_occupancy:.1f}%")
                    except Exception as e:
                        print(f"稼働率計算エラー: {str(e)}")
    except Exception as e:
        print(f"CSVファイル分析エラー: {str(e)}")

    # リクエストのパラメータ
    files = {"file": open(file_path, "rb")}
    data = {"data_type": data_type}

    print(f"アップロード中: {file_path} (タイプ: {data_type})")

    # POSTリクエストを送信
    try:
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            print("アップロード成功！")
            try:
                result = response.json()
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return result
            except json.JSONDecodeError:
                print(f"警告: レスポンスのJSONパースに失敗しました。レスポンス本文: {response.text}")
                return {"error": "レスポンスのJSONパースに失敗しました"}
        else:
            print(f"エラー: ステータスコード {response.status_code}")
            try:
                error_detail = response.json()
                print(json.dumps(error_detail, indent=2, ensure_ascii=False))
            except:
                print(f"レスポンス本文: {response.text}")
            return {"error": f"エラーレスポンス: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        print(f"エラー: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python3 upload_helper.py [ファイルパス] [データタイプ(optional)] [ポート番号(optional)]")
        sys.exit(1)

    file_path = sys.argv[1]
    data_type = sys.argv[2] if len(sys.argv) > 2 else "occupancy"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000  # デフォルトポートを8000に変更

    upload_csv(file_path, data_type, port)
