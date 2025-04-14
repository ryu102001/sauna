import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import tempfile
from data_processor import SaunaDataProcessor

# タイトルとイントロダクション
st.title('サウナ施設データ分析ダッシュボード')
st.write('CSVファイルをアップロードして、サウナ施設のデータを分析します。')

# ファイルアップロード部分
st.header('データファイルのアップロード')
uploaded_files = st.file_uploader('CSVファイルをアップロードしてください',
                               type=['csv'], accept_multiple_files=True)

if uploaded_files:
    # 一時ディレクトリを作成してファイルを保存
    temp_dir = tempfile.mkdtemp()
    file_paths = {}

    for uploaded_file in uploaded_files:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        file_paths[uploaded_file.name] = file_path

    st.success(f'{len(uploaded_files)}個のファイルがアップロードされました')

    # ファイルを分類
    member_files = [f for f in file_paths.keys() if 'member' in f.lower()]
    reservation_files = [f for f in file_paths.keys() if 'reservation' in f.lower()]
    frame_files = [f for f in file_paths.keys() if 'frame' in f.lower()]
    sales_files = [f for f in file_paths.keys() if 'sales' in f.lower()]

    # プロセッサーを初期化
    processor = SaunaDataProcessor()

    # データの読み込みと分析実行
    with st.spinner('データ分析を実行中...'):
        # 会員データ
        if member_files:
            member_path = file_paths[[f for f in member_files if 'delete' not in f][0]] if [f for f in member_files if 'delete' not in f] else None
            member_delete_path = file_paths[[f for f in member_files if 'delete' in f][0]] if [f for f in member_files if 'delete' in f] else None

            if member_path:
                processor.load_member_data(member_path, member_delete_path)
                member_stats = processor.analyze_member_status()

                # 会員データ分析結果の表示
                st.header('会員分析結果')
                col1, col2, col3 = st.columns(3)
                col1.metric('体験会員数', member_stats.get('trial_count', 0))
                col2.metric('現会員数', member_stats.get('current_members', 0))
                col3.metric('退会会員数', member_stats.get('former_members', 0))

                # 性別分布のグラフ
                if 'gender_distribution' in member_stats and member_stats['gender_distribution']:
                    st.subheader('性別分布')
                    fig, ax = plt.subplots()
                    gender_data = member_stats['gender_distribution']
                    ax.pie(gender_data.values(), labels=gender_data.keys(), autopct='%1.1f%%')
                    st.pyplot(fig)

                # 年齢分布
                if 'age_distribution' in member_stats:
                    st.subheader('年齢分布')
                    st.write(f"平均年齢: {member_stats['age_distribution'].get('mean', 'N/A'):.1f}歳")

        # 予約データ
        if reservation_files:
            reservation_paths = [file_paths[f] for f in reservation_files]
            processor.load_reservation_data(reservation_paths)
            reservation_stats = processor.analyze_reservations()

            # 予約データ分析結果の表示
            st.header('予約分析結果')
            if 'ticket_distribution' in reservation_stats:
                st.subheader('チケット種別分布')
                fig, ax = plt.subplots()
                ticket_data = reservation_stats['ticket_distribution']
                ax.bar(ticket_data.keys(), ticket_data.values())
                plt.xticks(rotation=45)
                st.pyplot(fig)

            # 月別予約数
            if 'monthly_stats' in reservation_stats:
                st.subheader('月別予約数の推移')
                monthly_totals = {}
                for ticket_type, monthly_data in reservation_stats['monthly_stats'].items():
                    for month, count in monthly_data.items():
                        month_str = str(month)
                        if month_str in monthly_totals:
                            monthly_totals[month_str] += count
                        else:
                            monthly_totals[month_str] = count

                fig, ax = plt.subplots(figsize=(10, 6))
                months = sorted(monthly_totals.keys())
                values = [monthly_totals[m] for m in months]
                ax.plot(months, values, marker='o')
                plt.xticks(rotation=45)
                ax.set_xlabel('月')
                ax.set_ylabel('予約数')
                st.pyplot(fig)

        # 稼働率データ
        if frame_files:
            frame_paths = [file_paths[f] for f in frame_files]
            processor.load_frame_data(frame_paths)
            occupancy_stats = processor.analyze_occupancy()

            # 稼働率分析結果の表示
            st.header('稼働率分析結果')
            for room, stats in occupancy_stats.items():
                st.subheader(f'{room}の稼働率')

                # 月別稼働率
                if 'monthly' in stats:
                    st.write('月別平均稼働率')
                    monthly = stats['monthly']
                    if monthly:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        months = sorted(monthly.keys())
                        values = [monthly[m] * 100 for m in months]
                        ax.plot(months, values, marker='o')
                        plt.xticks(rotation=45)
                        ax.set_xlabel('月')
                        ax.set_ylabel('稼働率 (%)')
                        ax.set_ylim(0, 100)
                        st.pyplot(fig)

                # 曜日別稼働率
                if 'weekday' in stats:
                    st.write('曜日別平均稼働率')
                    weekday = stats['weekday']
                    if weekday:
                        weekday_jp = {
                            'Monday': '月曜日', 'Tuesday': '火曜日', 'Wednesday': '水曜日',
                            'Thursday': '木曜日', 'Friday': '金曜日', 'Saturday': '土曜日', 'Sunday': '日曜日'
                        }
                        fig, ax = plt.subplots()
                        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        days = [d for d in days if d in weekday]
                        values = [weekday[d] * 100 for d in days]
                        day_labels = [weekday_jp[d] for d in days]
                        ax.bar(day_labels, values)
                        ax.set_ylabel('稼働率 (%)')
                        ax.set_ylim(0, 100)
                        st.pyplot(fig)

        # 売上データ
        if sales_files:
            sales_paths = [file_paths[f] for f in sales_files]
            processor.load_sales_data(sales_paths)
            sales_stats = processor.analyze_sales()

            # 売上分析結果の表示
            st.header('売上分析結果')
            col1, col2 = st.columns(2)
            col1.metric('総売上', f'{sales_stats.get("total_sales", 0):,}円')
            col2.metric('平均取引額', f'{sales_stats.get("average_transaction", 0):,.0f}円')

            # 月別売上推移
            if 'monthly_sales' in sales_stats:
                st.subheader('月別売上推移')
                monthly_sales = sales_stats['monthly_sales']
                if monthly_sales:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    months = sorted(monthly_sales.keys())
                    values = [monthly_sales[m] for m in months]
                    ax.plot(months, values, marker='o')
                    plt.xticks(rotation=45)
                    ax.set_xlabel('月')
                    ax.set_ylabel('売上 (円)')
                    st.pyplot(fig)

                    # 売上トップ5の月
                    st.subheader('売上トップ5の月')
                    top_months = sorted(monthly_sales.items(), key=lambda x: x[1], reverse=True)[:5]
                    top_data = {str(month): sales for month, sales in top_months}
                    st.bar_chart(top_data)
else:
    st.info('データファイルをアップロードしてください')
