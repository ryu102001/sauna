from data_processor import SaunaDataProcessor
import pandas as pd
import os
import re

def main():
    # SaunaDataProcessorのインスタンスを作成
    processor = SaunaDataProcessor()

    print("サウナダッシュボードデータ処理を開始します...")

    # データディレクトリ内のファイルを検索
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"{data_dir}ディレクトリが存在しないため作成しました。")

    # 利用可能なCSVファイルを確認
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    print(f"データディレクトリ内のCSVファイル: {len(csv_files)}個")

    # 会員データファイルを検索
    member_files = [f for f in csv_files if f.startswith('member')]
    if member_files:
        member_path = os.path.join(data_dir, [f for f in member_files if 'delete' not in f][0]) if [f for f in member_files if 'delete' not in f] else None
        member_delete_path = os.path.join(data_dir, [f for f in member_files if 'delete' in f][0]) if [f for f in member_files if 'delete' in f] else None

        if member_path:
            print(f"会員データファイル: {member_path}")
            if member_delete_path:
                print(f"退会会員データファイル: {member_delete_path}")
                processor.load_member_data(member_path, member_delete_path)
            else:
                print("退会会員データファイルが見つからないため、会員データのみ読み込みます。")
                processor.load_member_data(member_path)

            # 会員ステータスの分析
            print("会員データを分析しています...")
            member_stats = processor.analyze_member_status()
            print("\n会員分析結果:")
            print(f"体験会員数: {member_stats.get('trial_count', 'N/A')}")
            print(f"現会員数: {member_stats.get('current_members', 'N/A')}")
            print(f"退会会員数: {member_stats.get('former_members', 'N/A')}")
            print(f"性別分布: {member_stats.get('gender_distribution', 'N/A')}")
            if 'age_distribution' in member_stats:
                print(f"年齢分布: 平均{member_stats['age_distribution'].get('mean', 'N/A')}歳")
    else:
        print("会員データファイルが見つかりません。")

    # 予約データファイルを検索
    reservation_files = sorted([f for f in csv_files if 'reservation' in f])
    if reservation_files:
        reservation_paths = [os.path.join(data_dir, f) for f in reservation_files]
        print(f"\n予約データファイル: {len(reservation_paths)}個見つかりました")
        print("予約データを読み込んでいます...")
        processor.load_reservation_data(reservation_paths)

        # 予約データの分析
        print("予約データを分析しています...")
        reservation_stats = processor.analyze_reservations()
        print("\n予約分析結果:")
        print(f"チケット種別分布: {reservation_stats.get('ticket_distribution', 'N/A')}")
        if 'monthly_stats' in reservation_stats:
            for ticket_type, monthly_data in reservation_stats['monthly_stats'].items():
                print(f"{ticket_type}の予約状況: {len(monthly_data)}ヶ月分のデータあり")

            # 月別予約数の推移を表示
            monthly_totals = {}
            for ticket_type, monthly_data in reservation_stats['monthly_stats'].items():
                for month, count in monthly_data.items():
                    if month in monthly_totals:
                        monthly_totals[month] += count
                    else:
                        monthly_totals[month] = count

            print("\n月別予約総数:")
            for month, count in sorted(monthly_totals.items())[:10]:  # 最初の10ヶ月分だけ表示
                print(f"{month}: {count}件")
    else:
        print("\n予約データファイルが見つかりません。")

    # 予約枠データファイルを検索
    frame_files = sorted([f for f in csv_files if 'frame' in f])
    if frame_files:
        frame_paths = [os.path.join(data_dir, f) for f in frame_files]
        print(f"\n予約枠データファイル: {len(frame_paths)}個見つかりました")
        print("予約枠データを読み込んでいます...")
        processor.load_frame_data(frame_paths)

        # 稼働率の分析
        print("稼働率を分析しています...")
        occupancy_stats = processor.analyze_occupancy()
        print("\n稼働率分析結果:")
        for room, stats in occupancy_stats.items():
            print(f"\n{room}の稼働率:")
            print(f"月別平均稼働率: データあり")

            # 最高稼働率と最低稼働率の月を表示
            if 'monthly' in stats:
                monthly = stats['monthly']
                if monthly:
                    max_month = max(monthly.items(), key=lambda x: x[1])
                    min_month = min(monthly.items(), key=lambda x: x[1])
                    print(f"最高稼働率: {max_month[0]} ({max_month[1]*100:.1f}%)")
                    print(f"最低稼働率: {min_month[0]} ({min_month[1]*100:.1f}%)")

            print(f"時間別平均稼働率: データあり")

            # 最高稼働率の時間帯を表示
            if 'hourly' in stats:
                hourly = stats['hourly']
                if hourly:
                    max_hour = max(hourly.items(), key=lambda x: x[1])
                    print(f"最も人気の時間帯: {max_hour[0]}時 ({max_hour[1]*100:.1f}%)")

            print(f"曜日別平均稼働率: データあり")

            # 曜日別稼働率を表示
            if 'weekday' in stats:
                weekday = stats['weekday']
                if weekday:
                    # 曜日を日本語に変換
                    weekday_jp = {
                        'Monday': '月曜日', 'Tuesday': '火曜日', 'Wednesday': '水曜日',
                        'Thursday': '木曜日', 'Friday': '金曜日', 'Saturday': '土曜日', 'Sunday': '日曜日'
                    }
                    max_weekday = max(weekday.items(), key=lambda x: x[1])
                    print(f"最も人気の曜日: {weekday_jp.get(max_weekday[0], max_weekday[0])} ({max_weekday[1]*100:.1f}%)")
    else:
        print("\n予約枠データファイルが見つかりません。")

    # 売上データファイルを検索
    sales_files = sorted([f for f in csv_files if 'sales' in f])
    if sales_files:
        sales_paths = [os.path.join(data_dir, f) for f in sales_files]
        print(f"\n売上データファイル: {len(sales_paths)}個見つかりました")
        print("売上データを読み込んでいます...")
        processor.load_sales_data(sales_paths)

        # 売上データの分析
        print("売上データを分析しています...")
        sales_stats = processor.analyze_sales()
        print("\n売上分析結果:")
        print(f"総売上: {sales_stats.get('total_sales', 'N/A'):,}円")
        print(f"平均取引額: {sales_stats.get('average_transaction', 'N/A'):,.0f}円")
        if 'monthly_sales' in sales_stats:
            # 売上トップ5の月を表示
            top_months = sorted(sales_stats['monthly_sales'].items(), key=lambda x: x[1], reverse=True)[:5]
            print("\n売上トップ5の月:")
            for month, sales in top_months:
                print(f"{month}: {sales:,}円")

            # 直近数ヶ月の売上推移を表示
            recent_months = sorted(sales_stats['monthly_sales'].items())[-6:]  # 直近6ヶ月
            print("\n直近の売上推移:")
            for month, sales in recent_months:
                print(f"{month}: {sales:,}円")
    else:
        print("\n売上データファイルが見つかりません。")

    print("\n分析が完了しました！")

if __name__ == "__main__":
    main()
