#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import sys
import json
import pandas as pd  # データの前処理用にpandasをインポート

def upload_csv(file_path, data_type="occupancy", port=8001):
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

    try:
        # POSTリクエストを送信
        response = requests.post(url, files=files, data=data)

        # レスポンスのステータスコードを確認
        if response.status_code == 200:
            print("アップロード成功!")
            return response.json()
        else:
            print(f"アップロード失敗: ステータスコード {response.status_code}")
            print(f"レスポンス: {response.text}")
            return response.json() if response.headers.get('content-type') == 'application/json' else response.text
    except Exception as e:
        print(f"エラー: {str(e)}")
        return None
    finally:
        # ファイルを閉じる
        files["file"].close()

if __name__ == "__main__":
    # コマンドライン引数からファイルパスとデータタイプを取得
    if len(sys.argv) < 2:
        print("使用方法: python upload_helper.py [ファイルパス] [データタイプ(省略可)]")
        sys.exit(1)

    file_path = sys.argv[1]
    data_type = sys.argv[2] if len(sys.argv) > 2 else "occupancy"

    # アップロード実行
    result = upload_csv(file_path, data_type)
    if result:
        print("\n結果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
