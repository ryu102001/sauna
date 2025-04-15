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
            'plan_end_date': 'プラン契約適用終了日',
            'contract_date': 'プラン契約日'  # JavaScriptコードに合わせて追加
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
        self.dummy_user_ids = [137, 3, 5576]

        # 基準日の設定（デフォルトは現在日）
        self.reference_date = pd.Timestamp.now()

    def set_reference_date(self, date_str):
        """基準日を設定する"""
        self.reference_date = pd.to_datetime(date_str)

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
        date_columns = [
            self.member_cols['trial_datetime'],
            self.member_cols['plan_start_date'],
            self.member_cols['plan_end_date'],
            self.member_cols.get('contract_date')  # 存在する場合のみ変換
        ]

        for col in date_columns:
            if col and col in self.member_data.columns:
                self.member_data[col] = pd.to_datetime(self.member_data[col], errors='coerce')

        # 削除データの日付列も変換
        if self.member_delete_data is not None:
            for col in date_columns:
                if col and col in self.member_delete_data.columns:
                    self.member_delete_data[col] = pd.to_datetime(self.member_delete_data[col], errors='coerce')

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

        reference_date = self.reference_date

        # カラム名を実際のデータに合わせる
        trial_col = self.member_cols['trial_datetime']
        start_col = self.member_cols['plan_start_date']
        end_col = self.member_cols['plan_end_date']
        contract_col = self.member_cols.get('contract_date')
        gender_col = self.member_cols['gender']
        age_col = self.member_cols['age']
        member_id_col = self.member_cols['member_id']

        # 会員分類用のカテゴリ
        categories = {
            'trial': [],      # 初回体験者
            'active': [],     # アクティブ会員
            'former': [],     # 退会者
            'visitor': [],    # ビジター
            'total': len(self.member_data) + (len(self.member_delete_data) if self.member_delete_data is not None else 0)
        }

        # 通常会員データの分類
        for _, member in self.member_data.iterrows():
            member_id = member[member_id_col]

            # 初回体験者として分類
            if pd.notna(member[trial_col]):
                categories['trial'].append(member_id)

                # さらに、会員か退会者かを判定
                if contract_col and pd.notna(member.get(contract_col)):
                    if pd.notna(member[end_col]):
                        if member[end_col] > reference_date:
                            categories['active'].append(member_id)
                        else:
                            categories['former'].append(member_id)
                    else:
                        categories['active'].append(member_id)
                # 契約日がない場合でも、開始日があれば判定
                elif pd.notna(member[start_col]):
                    if pd.notna(member[end_col]):
                        if member[end_col] > reference_date:
                            categories['active'].append(member_id)
                        else:
                            categories['former'].append(member_id)
                    else:
                        categories['active'].append(member_id)

        # 削除された会員データの分類
        if self.member_delete_data is not None:
            for _, member in self.member_delete_data.iterrows():
                member_id = member[member_id_col]

                if pd.notna(member.get(trial_col)):
                    categories['trial'].append(member_id)
                    categories['former'].append(member_id)  # 削除されているので退会者として扱う

        # 予約データからビジターを特定
        if self.reservation_data is not None:
            ticket_col = self.reservation_cols['ticket_name']
            reservation_member_id_col = self.reservation_cols['member_id']

            for _, reservation in self.reservation_data.iterrows():
                member_id = reservation[reservation_member_id_col]
                ticket_type = str(reservation.get(ticket_col, ''))

                # チケットタイプでの分類
                if ('ビジター' in ticket_type and
                    member_id not in categories['active'] and
                    member_id not in categories['former'] and
                    member_id not in categories['visitor']):
                    categories['visitor'].append(member_id)

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

            # 年齢グループ分布も追加
            age_ranges = {
                '~19歳': (0, 19),
                '20~29歳': (20, 29),
                '30~39歳': (30, 39),
                '40~49歳': (40, 49),
                '50~59歳': (50, 59),
                '60歳~': (60, 120)
            }

            age_groups = {}
            for group_name, (min_age, max_age) in age_ranges.items():
                age_groups[group_name] = len(age_data[(age_data >= min_age) & (age_data <= max_age)])

            age_distribution['groups'] = age_groups

        # 入会率と退会率を計算
        conversion_rate = 0
        if len(categories['trial']) > 0:
            conversion_rate = (len(categories['active']) + len(categories['former'])) / len(categories['trial']) * 100

        churn_rate = 0
        if (len(categories['active']) + len(categories['former'])) > 0:
            churn_rate = len(categories['former']) / (len(categories['active']) + len(categories['former'])) * 100

        return {
            'trial_count': len(categories['trial']),
            'current_members': len(categories['active']),
            'former_members': len(categories['former']),
            'visitor_count': len(categories['visitor']),
            'total_members': categories['total'],
            'gender_distribution': gender_distribution,
            'age_distribution': age_distribution,
            'categories': categories,
            'conversion_rate': round(conversion_rate, 2),
            'churn_rate': round(churn_rate, 2)
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

        # 月別集計
        monthly_stats = {}
        if date_col in self.reservation_data.columns:
            # 予約日付を日付型として解釈
            self.reservation_data['month'] = self.reservation_data[date_col].dt.strftime('%Y-%m')

            # チケットタイプ別の月別集計
            for category in self.reservation_data['ticket_category'].unique():
                category_data = self.reservation_data[self.reservation_data['ticket_category'] == category]
                monthly_counts = category_data['month'].value_counts().sort_index().to_dict()
                monthly_stats[category] = monthly_counts

        # チケット種別分布
        ticket_distribution = self.reservation_data['ticket_category'].value_counts().to_dict()

        # ステータス別集計
        status_col = self.reservation_cols['status']
        status_distribution = {}
        if status_col in self.reservation_data.columns:
            status_distribution = self.reservation_data[status_col].value_counts().to_dict()

        return {
            'monthly_stats': monthly_stats,
            'ticket_distribution': ticket_distribution,
            'status_distribution': status_distribution
        }

    def load_frame_data(self, frame_paths: List[str]) -> None:
        """フレームデータの読み込みと前処理"""
        dfs = []
        for path in frame_paths:
            try:
                df = pd.read_csv(path, encoding='utf-8')

                # 必要なカラムが存在するか確認
                required_cols = [self.frame_cols[col] for col in
                                ['space_name', 'lesson_datetime', 'capacity', 'occupancy_rate']
                                if self.frame_cols[col] is not None]

                if all(col in df.columns for col in required_cols):
                    dfs.append(df)
            except Exception as e:
                print(f"警告: {path}の読み込み中にエラーが発生しました: {e}")

        if dfs:
            self.frame_data = pd.concat(dfs, ignore_index=True)

            # 日付列の変換
            date_col = self.frame_cols['lesson_datetime']
            if date_col in self.frame_data.columns:
                self.frame_data[date_col] = pd.to_datetime(self.frame_data[date_col], errors='coerce')

                # 月と曜日の抽出
                self.frame_data['month'] = self.frame_data[date_col].dt.strftime('%Y-%m')
                self.frame_data['weekday'] = self.frame_data[date_col].dt.day_name()

    def analyze_occupancy(self) -> Dict:
        """稼働率の分析"""
        if self.frame_data is None:
            return {}

        # カラム名を実際のデータに合わせる
        space_name_col = self.frame_cols['space_name']
        capacity_col = self.frame_cols['capacity']
        occupancy_rate_col = self.frame_cols['occupancy_rate']
        reservation_count_col = self.frame_cols['reservation_count']

        # ルーム別の稼働率を計算
        room_rates = {}
        if space_name_col in self.frame_data.columns:
            for room in self.frame_data[space_name_col].unique():
                if pd.isna(room):
                    continue

                room_data = self.frame_data[self.frame_data[space_name_col] == room]

                # 月別稼働率
                monthly_rates = {}
                if 'month' in room_data.columns and occupancy_rate_col in room_data.columns:
                    for month in room_data['month'].unique():
                        month_data = room_data[room_data['month'] == month]
                        monthly_rates[month] = month_data[occupancy_rate_col].mean()

                # 曜日別稼働率
                weekday_rates = {}
                if 'weekday' in room_data.columns and occupancy_rate_col in room_data.columns:
                    for weekday in room_data['weekday'].unique():
                        weekday_data = room_data[room_data['weekday'] == weekday]
                        weekday_rates[weekday] = weekday_data[occupancy_rate_col].mean()

                # ダミーユーザーの無断キャンセルを考慮
                adjusted_rates = {}
                if self.reservation_data is not None:
                    room_key = 'Room1' if 'Room1' in room else 'Room2' if 'Room2' in room else 'Room3' if 'Room3' in room else None

                    # 無断キャンセルをカウント（仮実装）
                    # 注: 実際の実装ではさらに詳細な条件チェックが必要
                    dummy_cancellations = self.reservation_data[
                        (self.reservation_data[self.reservation_cols['member_id']].isin(self.dummy_user_ids)) &
                        (self.reservation_data[self.reservation_cols['status']] == '無断キャンセル')
                    ]

                    # 稼働率の調整（簡易実装）
                    if room_key:
                        adjusted_rates = monthly_rates.copy()
                        # 実装省略: ダミーユーザーの予約を稼働率に加算する処理

                room_rates[room] = {
                    'monthly': monthly_rates,
                    'weekday': weekday_rates,
                    'adjusted': adjusted_rates
                }

        # 全体の稼働率を計算
        overall_rate = 0
        if capacity_col in self.frame_data.columns and reservation_count_col in self.frame_data.columns:
            total_capacity = self.frame_data[capacity_col].sum()
            total_reservations = self.frame_data[reservation_count_col].sum()

            if total_capacity > 0:
                overall_rate = total_reservations / total_capacity * 100

        return {
            'overall': overall_rate,
            'byRoom': room_rates
        }

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
                    dfs.append(df)
            except Exception as e:
                print(f"警告: {path}の読み込み中にエラーが発生しました: {e}")

        if dfs:
            self.sales_data = pd.concat(dfs, ignore_index=True)

            # 日付列の変換
            date_col = self.sales_cols['transaction_datetime']
            if date_col in self.sales_data.columns:
                self.sales_data[date_col] = pd.to_datetime(self.sales_data[date_col], errors='coerce')

                # 月の抽出
                self.sales_data['month'] = self.sales_data[date_col].dt.strftime('%Y-%m')

    def analyze_sales(self) -> Dict:
        """売上の分析"""
        if self.sales_data is None:
            return {
                'total_sales': 0,
                'average_transaction': 0
            }

        # 会員ステータスを取得（必要に応じて計算）
        member_categories = self.analyze_member_status().get('categories', {})

        # カラム名を実際のデータに合わせる
        member_id_col = self.sales_cols['member_id']
        amount_col = self.sales_cols['amount']
        item_name_col = self.sales_cols['item_name']

        # 売上カテゴリごとにカウント
        sales_by_category = {
            'trial': 0,    # 初回体験
            'member': 0,   # 会員
            'visitor': 0,  # ビジター
            'other': 0     # その他
        }

        # ルーム別の売上
        sales_by_room = {
            'Room1': 0,
            'Room2': 0,
            'Room3': 0,
            'Other': 0
        }

        # 売上データを分析
        for _, sale in self.sales_data.iterrows():
            member_id = sale[member_id_col]
            amount = sale[amount_col] or 0
            summary = str(sale.get(item_name_col, ''))

            # 売上カテゴリの判定
            if member_id in member_categories.get('active', []):
                sales_by_category['member'] += amount
            elif member_id in member_categories.get('trial', []):
                sales_by_category['trial'] += amount
            elif member_id in member_categories.get('visitor', []):
                sales_by_category['visitor'] += amount
            else:
                sales_by_category['other'] += amount

            # ルーム別売上の判定
            if 'Room1' in summary and 'Room2' not in summary and 'Room3' not in summary:
                sales_by_room['Room1'] += amount
            elif 'Room1' not in summary and 'Room2' in summary and 'Room3' not in summary:
                sales_by_room['Room2'] += amount
            elif 'Room1' not in summary and 'Room2' not in summary and 'Room3' in summary:
                sales_by_room['Room3'] += amount
            elif 'Room1/Room2' in summary:
                # Room1とRoom2の両方に言及がある場合は按分
                sales_by_room['Room1'] += amount / 2
                sales_by_room['Room2'] += amount / 2
            else:
                sales_by_room['Other'] += amount

        # 総売上と売上比率を計算
        total_sales = sum(sales_by_category.values())

        # カテゴリ別売上比率
        category_ratios = {}
        for category, amount in sales_by_category.items():
            category_ratios[category] = round(amount / total_sales * 100, 1) if total_sales > 0 else 0

        # ルーム別売上比率
        room_ratios = {}
        for room, amount in sales_by_room.items():
            room_ratios[room] = round(amount / total_sales * 100, 1) if total_sales > 0 else 0

        # 月別売上集計
        monthly_sales = {}
        if 'month' in self.sales_data.columns:
            for month in self.sales_data['month'].unique():
                month_data = self.sales_data[self.sales_data['month'] == month]
                monthly_sales[month] = month_data[amount_col].sum()

        # 平均取引額
        avg_transaction = 0
        if len(self.sales_data) > 0:
            avg_transaction = total_sales / len(self.sales_data)

        return {
            'total_sales': total_sales,
            'average_transaction': avg_transaction,
            'monthly_sales': monthly_sales,
            'sales_by_category': sales_by_category,
            'sales_by_room': sales_by_room,
            'category_ratios': category_ratios,
            'room_ratios': room_ratios
        }
