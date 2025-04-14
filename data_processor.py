import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple

class SaunaDataProcessor:
    def __init__(self):
        self.member_data = None
        self.member_delete_data = None
        self.reservation_data = None
        self.frame_data = None
        self.sales_data = None

        # 実データのカラム名マッピング
        self.member_cols = {
            'member_id': 'メンバーID',
            'name': '氏名',
            'gender': '性別',
            'age': '年齢',
            'trial_datetime': 'トライアル 受講日時',
            'plan_start_date': 'プラン契約適用開始日',
            'plan_end_date': 'プラン契約適用終了日'
        }

        self.reservation_cols = {
            'reservation_id': '予約ID',
            'member_id': 'メンバーID',
            'ticket_name': '使用チケット',
            'reservation_datetime': '受講日',
            'status': '予約ステータス',
            'start_time': '開始時刻',
            'room': '店舗ルーム'
        }

        self.frame_cols = {
            'frame_id': None,  # 実際のデータにはこのカラムがないようなので無視
            'space_name': 'ルーム名',
            'lesson_datetime': 'レッスン日',
            'start_time': '開始時刻',
            'capacity': 'スペース数',
            'reservation_count': '総予約数',
            'occupancy_rate': '稼働率'
        }

        self.sales_cols = {
            'transaction_id': '売上ID',
            'member_id': 'メンバーID',
            'transaction_datetime': '精算日時',
            'item_name': '摘要',
            'amount': '合計金額'
        }

        # 特別なメンバーID（無断キャンセルを通常利用としてカウント）
        self.special_member_ids = [137, 3, 5576]

    def load_member_data(self, member_path: str, member_delete_path: str = None) -> None:
        """会員データの読み込みと前処理"""
        self.member_data = pd.read_csv(member_path, encoding='utf-8')

        if member_delete_path:
            self.member_delete_data = pd.read_csv(member_delete_path, encoding='utf-8')

            # 除外リストに含まれる会員を削除
            if self.member_delete_data is not None:
                self.member_data = self.member_data[
                    ~self.member_data[self.member_cols['member_id']].isin(
                        self.member_delete_data[self.member_cols['member_id']])
                ]

        # 日付列の変換
        date_columns = [self.member_cols['trial_datetime'],
                        self.member_cols['plan_start_date'],
                        self.member_cols['plan_end_date']]

        for col in date_columns:
            if col in self.member_data.columns:
                self.member_data[col] = pd.to_datetime(self.member_data[col], errors='coerce')

    def analyze_member_status(self) -> Dict:
        """会員ステータスの分析"""
        if self.member_data is None:
            return {
                'trial_count': 0,
                'current_members': 0,
                'former_members': 0,
                'gender_distribution': {},
                'age_distribution': {}
            }

        now = pd.Timestamp.now()

        # カラム名を実際のデータに合わせる
        trial_col = self.member_cols['trial_datetime']
        start_col = self.member_cols['plan_start_date']
        end_col = self.member_cols['plan_end_date']
        gender_col = self.member_cols['gender']
        age_col = self.member_cols['age']

        trial_members = self.member_data[self.member_data[trial_col].notna()]

        # 開始日があり、終了日がないか将来の会員
        current_members = self.member_data[
            (self.member_data[start_col].notna()) &
            ((self.member_data[end_col].isna()) |
             (self.member_data[end_col] > now))
        ]

        # 終了日が過去の会員
        former_members = self.member_data[
            (self.member_data[start_col].notna()) &
            (self.member_data[end_col].notna()) &
            (self.member_data[end_col] <= now)
        ]

        # 性別分布
        gender_distribution = {}
        if gender_col in self.member_data.columns:
            gender_distribution = self.member_data[gender_col].value_counts().to_dict()

        # 年齢分布
        age_distribution = {}
        if age_col in self.member_data.columns:
            # 年齢が数値として解釈できる場合のみ処理
            age_data = pd.to_numeric(self.member_data[age_col], errors='coerce')
            age_distribution = age_data.describe().to_dict()

        return {
            'trial_count': len(trial_members),
            'current_members': len(current_members),
            'former_members': len(former_members),
            'gender_distribution': gender_distribution,
            'age_distribution': age_distribution
        }

    def load_reservation_data(self, reservation_paths: List[str]) -> None:
        """予約データの読み込みと前処理"""
        dfs = []
        for path in reservation_paths:
            try:
                df = pd.read_csv(path, encoding='utf-8')

                # 必要なカラムが存在するか確認
                required_cols = [self.reservation_cols[col] for col in
                               ['reservation_id', 'member_id', 'ticket_name', 'reservation_datetime', 'status']
                               if self.reservation_cols[col] is not None]

                if all(col in df.columns for col in required_cols):
                    # 日時データを結合
                    if '開始時刻' in df.columns and '受講日' in df.columns:
                        df['予約日時'] = df['受講日'] + ' ' + df['開始時刻']

                    dfs.append(df)
            except Exception as e:
                print(f"警告: {path}の読み込み中にエラーが発生しました: {e}")

        if dfs:
            self.reservation_data = pd.concat(dfs, ignore_index=True)

            # 日付列の変換
            if '予約日時' in self.reservation_data.columns:
                self.reservation_data['予約日時'] = pd.to_datetime(
                    self.reservation_data['予約日時'], errors='coerce'
                )
            elif self.reservation_cols['reservation_datetime'] in self.reservation_data.columns:
                self.reservation_data[self.reservation_cols['reservation_datetime']] = pd.to_datetime(
                    self.reservation_data[self.reservation_cols['reservation_datetime']], errors='coerce'
                )

    def analyze_reservations(self) -> Dict:
        """予約データの分析"""
        if self.reservation_data is None:
            return {
                'monthly_stats': {},
                'ticket_distribution': {}
            }

        def categorize_ticket(ticket_name):
            if pd.isna(ticket_name):
                return 'その他'
            ticket_name = str(ticket_name)
            if '体験' in ticket_name:
                return '初回体験'
            elif '会員' in ticket_name or 'プラン' in ticket_name:
                return '会員'
            elif 'ビジター' in ticket_name:
                return 'ビジター'
            return 'その他'

        ticket_col = self.reservation_cols['ticket_name']
        if ticket_col in self.reservation_data.columns:
            self.reservation_data['ticket_category'] = self.reservation_data[ticket_col].apply(
                categorize_ticket
            )
        else:
            self.reservation_data['ticket_category'] = 'その他'

        # 予約状況分析用の日時列を決定
        if '予約日時' in self.reservation_data.columns:
            date_col = '予約日時'
        else:
            date_col = self.reservation_cols['reservation_datetime']

        # 月別の予約統計
        if date_col in self.reservation_data.columns:
            monthly_stats = self.reservation_data.groupby(
                [self.reservation_data[date_col].dt.to_period('M'),
                'ticket_category']
            ).size().unstack(fill_value=0)

            monthly_stats_dict = {}
            for ticket_type in monthly_stats.columns:
                monthly_stats_dict[ticket_type] = monthly_stats[ticket_type].to_dict()

            return {
                'monthly_stats': monthly_stats_dict,
                'ticket_distribution': self.reservation_data['ticket_category'].value_counts().to_dict()
            }
        else:
            return {
                'monthly_stats': {},
                'ticket_distribution': self.reservation_data['ticket_category'].value_counts().to_dict()
            }

    def load_frame_data(self, frame_paths: List[str]) -> None:
        """予約枠/稼働率データの読み込みと前処理"""
        dfs = []
        for path in frame_paths:
            try:
                df = pd.read_csv(path, encoding='utf-8')

                # 必要なカラムが存在するか確認
                required_cols = [self.frame_cols[col] for col in
                               ['space_name', 'lesson_datetime', 'occupancy_rate']
                               if self.frame_cols[col] is not None]

                if all(col in df.columns for col in required_cols):
                    # 日時データを結合
                    if 'レッスン日' in df.columns and '開始時刻' in df.columns:
                        df['レッスン日時'] = df['レッスン日'] + ' ' + df['開始時刻']

                    # 稼働率が文字列の場合、数値に変換
                    if '稼働率' in df.columns:
                        df['稼働率'] = pd.to_numeric(df['稼働率'].str.replace('%', ''), errors='coerce') / 100

                    dfs.append(df)
            except Exception as e:
                print(f"警告: {path}の読み込み中にエラーが発生しました: {e}")

        if dfs:
            self.frame_data = pd.concat(dfs, ignore_index=True)

            # 日付列の変換
            if 'レッスン日時' in self.frame_data.columns:
                self.frame_data['レッスン日時'] = pd.to_datetime(
                    self.frame_data['レッスン日時'], errors='coerce'
                )
            elif self.frame_cols['lesson_datetime'] in self.frame_data.columns:
                self.frame_data[self.frame_cols['lesson_datetime']] = pd.to_datetime(
                    self.frame_data[self.frame_cols['lesson_datetime']], errors='coerce'
                )

    def analyze_occupancy(self) -> Dict:
        """稼働率の分析"""
        if self.frame_data is None:
            return {}

        # 使用する日時列を決定
        if 'レッスン日時' in self.frame_data.columns:
            datetime_col = 'レッスン日時'
        else:
            datetime_col = self.frame_cols['lesson_datetime']

        # 稼働率列を決定
        occupancy_col = self.frame_cols['occupancy_rate']

        if datetime_col in self.frame_data.columns:
            self.frame_data['month'] = self.frame_data[datetime_col].dt.to_period('M')
            self.frame_data['weekday'] = self.frame_data[datetime_col].dt.day_name()
            self.frame_data['hour'] = self.frame_data[datetime_col].dt.hour

            # ルーム別の稼働率計算
            room_col = self.frame_cols['space_name']
            occupancy_stats = {}

            if room_col in self.frame_data.columns:
                room_groups = self.frame_data[room_col].unique()

                for room in room_groups:
                    if pd.isna(room):
                        continue

                    room_data = self.frame_data[self.frame_data[room_col] == room]

                    if occupancy_col in room_data.columns:
                        monthly_occupancy = room_data.groupby('month')[occupancy_col].mean()
                        hourly_occupancy = room_data.groupby('hour')[occupancy_col].mean()
                        weekday_occupancy = room_data.groupby('weekday')[occupancy_col].mean()

                        occupancy_stats[room] = {
                            'monthly': monthly_occupancy.to_dict(),
                            'hourly': hourly_occupancy.to_dict(),
                            'weekday': weekday_occupancy.to_dict()
                        }

            return occupancy_stats
        else:
            return {}

    def load_sales_data(self, sales_paths: List[str]) -> None:
        """売上データの読み込みと前処理"""
        dfs = []
        for path in sales_paths:
            try:
                df = pd.read_csv(path, encoding='utf-8')

                # 必要なカラムが存在するか確認
                required_cols = [self.sales_cols[col] for col in
                               ['transaction_id', 'member_id', 'transaction_datetime', 'amount']
                               if self.sales_cols[col] is not None]

                if all(col in df.columns for col in required_cols):
                    # 金額列が文字列の場合、数値に変換
                    amount_col = self.sales_cols['amount']
                    if amount_col in df.columns:
                        df[amount_col] = pd.to_numeric(df[amount_col].astype(str).str.replace(',', ''), errors='coerce')

                    dfs.append(df)
            except Exception as e:
                print(f"警告: {path}の読み込み中にエラーが発生しました: {e}")

        if dfs:
            self.sales_data = pd.concat(dfs, ignore_index=True)

            # 日付列の変換
            datetime_col = self.sales_cols['transaction_datetime']
            if datetime_col in self.sales_data.columns:
                self.sales_data[datetime_col] = pd.to_datetime(
                    self.sales_data[datetime_col], errors='coerce'
                )

    def analyze_sales(self) -> Dict:
        """売上データの分析"""
        if self.sales_data is None:
            return {
                'monthly_sales': {},
                'total_sales': 0,
                'average_transaction': 0
            }

        datetime_col = self.sales_cols['transaction_datetime']
        amount_col = self.sales_cols['amount']

        if datetime_col in self.sales_data.columns:
            self.sales_data['month'] = self.sales_data[datetime_col].dt.to_period('M')

            if amount_col in self.sales_data.columns:
                monthly_sales = self.sales_data.groupby('month')[amount_col].sum()

                return {
                    'monthly_sales': monthly_sales.to_dict(),
                    'total_sales': self.sales_data[amount_col].sum(),
                    'average_transaction': self.sales_data[amount_col].mean()
                }

        return {
            'monthly_sales': {},
            'total_sales': 0,
            'average_transaction': 0
        }
