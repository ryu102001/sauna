import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime
import os
import io

# データ保存ディレクトリの作成
os.makedirs("data", exist_ok=True)

# ページ設定
st.set_page_config(
    page_title="HAAAVE.sauna Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"  # デフォルトで閉じた状態
)

# カスタムCSSを適用
st.markdown("""
<style>
    /* ヘッダーのカスタマイズ */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    /* サイドバーのカスタマイズ */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }

    /* ボタン風のナビゲーション */
    .nav-button {
        display: block;
        width: 100%;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        text-align: left;
        border: none;
        border-radius: 0.5rem;
        background-color: white;
        color: #333;
        font-size: 1rem;
        transition: all 0.2s;
    }

    .nav-button:hover {
        background-color: #f0f0f0;
    }

    .nav-button.active {
        background-color: #e6f2ff;
        color: #0366d6;
        font-weight: 500;
        border-left: 4px solid #0366d6;
    }

    /* セクション区切り */
    .section-divider {
        height: 1px;
        background-color: #e1e4e8;
        margin: 1.5rem 0;
    }

    /* カード風のコンテナ */
    .metric-card {
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* モバイル用調整 */
    @media (max-width: 768px) {
        .metric-card {
            padding: 0.5rem;
        }
    }

    /* アイコンスタイル */
    .icon {
        display: inline-block;
        width: 24px;
        height: 24px;
        margin-right: 0.5rem;
        vertical-align: middle;
    }

    /* メトリックスタイル */
    .metric-value {
        font-size: 1.75rem;
        font-weight: bold;
    }

    .metric-label {
        font-size: 0.875rem;
        color: #777;
    }

    /* サイドバーの非表示ボタン */
    button[kind="header"] {
        background-color: transparent;
        color: #555;
    }

    /* サイドバーのカスタマイズ */
    section[data-testid="stSidebar"] {
        width: 100%;
        max-width: 20rem;
        background-color: #f8f9fa;
    }

    /* スタイル調整 - デフォルトmarginのリセット */
    div.row-widget.stRadio > div {
        margin-bottom: 0;
    }
</style>
""", unsafe_allow_html=True)

# キャッシュされたデータロード関数
@st.cache_data(ttl=300)  # 5分間キャッシュ
def load_data(data_type):
    """
    データを読み込む関数（キャッシュ付き）
    """
    try:
        if data_type == "members":
            file_path = "data/members_data.csv"
            if os.path.exists(file_path):
                return pd.read_csv(file_path)
        elif data_type == "utilization":
            file_path = "data/utilization_data.csv"
            if os.path.exists(file_path):
                return pd.read_csv(file_path)
        elif data_type == "competitors":
            file_path = "data/competitors_data.csv"
            if os.path.exists(file_path):
                return pd.read_csv(file_path)
        elif data_type == "finance":
            file_path = "data/finance_data.csv"
            if os.path.exists(file_path):
                return pd.read_csv(file_path)

        # ファイルが存在しない場合はダミーデータを返す
        return create_dummy_data(data_type)
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return None

# ダミーデータ生成関数
def create_dummy_data(data_type):
    """
    ダミーデータを生成する関数
    """
    if data_type == "members":
        # 会員データのダミー
        return pd.DataFrame({
            "member_id": range(1, 101),
            "gender": np.random.choice(["男性", "女性"], 100),
            "age_group": np.random.choice(["20代", "30代", "40代", "50代", "~19歳", "60歳~"], 100),
            "region": np.random.choice(["大阪府", "兵庫県", "京都府", "奈良県", "滋賀県", "和歌山県", "その他"], 100),
            "join_date": [f"2023-{np.random.randint(1, 13):02d}-{np.random.randint(1, 29):02d}" for _ in range(100)],
            "status": np.random.choice(["active", "inactive"], 100, p=[0.8, 0.2])
        })
    elif data_type == "utilization":
        # 稼働率データのダミー
        dates = pd.date_range(start="2023-01-01", end="2024-05-31", freq="D")
        rooms = ["Room1", "Room2", "Room3"]
        data = []
        for date in dates:
            for room in rooms:
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "room": room,
                    "occupancy_rate": np.random.randint(30, 95)
                })
        return pd.DataFrame(data)
    elif data_type == "competitors":
        # 競合データのダミー
        competitors = ["HAAAVE.sauna", "KUDOCHI sauna", "MENTE", "M's Sauna", "SAUNA Pod 槃", "SAUNA OOO OSAKA", "大阪サウナ DESSE"]
        areas = ["梅田", "難波", "天王寺", "福島", "本町", "心斎橋", "堀江"]
        return pd.DataFrame({
            "name": competitors,
            "location": [f"大阪市{np.random.choice(['北区', '中央区', '西区', '浪速区'])}"] * 7,
            "area": areas,
            "type": np.random.choice(["個室", "共同"], 7),
            "hourly_rate": np.random.randint(1500, 3500, 7),
            "rooms": np.random.randint(3, 10, 7),
            "cold_bath": np.random.choice(["あり", "なし"], 7),
            "mixed_gender": np.random.choice(["可", "不可"], 7),
            "opening_year": np.random.randint(2018, 2024, 7)
        })
    elif data_type == "finance":
        # 財務データのダミー
        months = pd.date_range(start="2023-01-01", end="2024-05-01", freq="MS")
        data = []
        for month in months:
            base_sales = np.random.randint(800000, 1500000)
            costs = int(base_sales * np.random.uniform(0.5, 0.7))
            data.append({
                "month": month.strftime("%Y-%m"),
                "sales": base_sales,
                "costs": costs,
                "profit": base_sales - costs,
                "profit_rate": (base_sales - costs) / base_sales * 100
            })
        return pd.DataFrame(data)

    return pd.DataFrame()  # 空のデータフレームを返す

# CSVファイルのアップロードと処理
def upload_and_process_csv(upload_type):
    uploaded_file = st.file_uploader(f"{upload_type}データのCSVをアップロード", type="csv")

    if uploaded_file is not None:
        try:
            # データの読み込み
            df = pd.read_csv(uploaded_file)

            # データの検証
            if upload_type == "会員" and not all(col in df.columns for col in ["member_id", "gender", "age_group"]):
                st.error("会員データには member_id, gender, age_group カラムが必要です")
                return None
            elif upload_type == "稼働率" and not all(col in df.columns for col in ["date", "room", "occupancy_rate"]):
                st.error("稼働率データには date, room, occupancy_rate カラムが必要です")
            elif upload_type == "競合" and not all(col in df.columns for col in ["name", "location", "hourly_rate"]):
                st.error("競合データには name, location, hourly_rate カラムが必要です")
            elif upload_type == "財務" and not all(col in df.columns for col in ["month", "sales", "costs"]):
                st.error("財務データには month, sales, costs カラムが必要です")
                return None

            # データの保存
            file_path = f"data/{upload_type}_data.csv"
            df.to_csv(file_path, index=False)

            st.success(f"{upload_type}データを保存しました！")

            # キャッシュをクリア
            st.cache_data.clear()

            return df
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            return None

    return None

# サイドバー
with st.sidebar:
    # タイトル部分
    st.markdown("### HAAAVE.sauna")

    # セクション区切り線
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ナビゲーションヘッダー
    st.markdown("#### ナビゲーション")

    # ラジオボタンでのナビゲーション
    page = st.radio(
        "",  # ラベルは空に
        ["概要", "会員分析", "ルーム稼働率", "曜日・時間分析", "競合分析", "売上分析"],
        index=0,  # デフォルトは「概要」
        label_visibility="collapsed"  # ラベルを非表示
    )

    # セクション区切り線
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # 期間選択
    st.markdown("#### 期間")
    period = st.selectbox("", ["全期間", "2023年", "2024年", "2025年"], label_visibility="collapsed")

    # セクション区切り線
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # データ管理セクション
    st.markdown("#### データ管理")

    upload_type = st.selectbox(
        "アップロードするデータ",
        ["会員", "稼働率", "競合", "財務"],
        label_visibility="visible"
    )

    # ファイルアップローダー
    df = upload_and_process_csv(upload_type)

    # データ自動更新の設定（非表示に）
    if st.checkbox("データを自動更新する", value=False, key="auto_refresh"):
        refresh_interval = st.slider(
            "更新間隔（秒）",
            min_value=10,
            max_value=300,
            value=60,
            step=10
        )
        st.info(f"{refresh_interval}秒ごとにデータを更新します")

        # 自動更新用のカウンター
        ph = st.empty()
        if "counter" not in st.session_state:
            st.session_state.counter = 0

        st.session_state.counter += 1
        ph.text(f"更新回数: {st.session_state.counter}")

        # 指定した間隔でページを再読み込み
        time.sleep(refresh_interval)
        st.experimental_rerun()

# メインコンテンツのヘッダー - タイトルとツールバー
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("サウナ施設分析ダッシュボード")
    st.caption("データに基づく施設運営の最適化")

with header_col2:
    # ツールバー
    toolbar = st.columns(4)
    with toolbar[0]:
        st.markdown(f"""
        <button class="tool-button">
            <span>📅 {period}</span>
        </button>
        """, unsafe_allow_html=True)
    with toolbar[1]:
        st.button("🔄", help="データを更新")
    with toolbar[2]:
        st.button("🔍", help="フィルター")
    with toolbar[3]:
        st.button("📥", help="データをエクスポート")

# データの読み込み
members_data = load_data("members")
utilization_data = load_data("utilization")
competitors_data = load_data("competitors")
finance_data = load_data("finance")

# データ処理
if utilization_data is not None:
    # 日付列をdatetime型に変換
    utilization_data['date'] = pd.to_datetime(utilization_data['date'])
    # 月と曜日の情報を追加
    utilization_data['month'] = utilization_data['date'].dt.strftime('%Y-%m')
    utilization_data['day_of_week'] = utilization_data['date'].dt.day_name()
    # 曜日を日本語に変換
    day_mapping = {
        'Monday': '月', 'Tuesday': '火', 'Wednesday': '水',
        'Thursday': '木', 'Friday': '金', 'Saturday': '土', 'Sunday': '日'
    }
    utilization_data['day_of_week_jp'] = utilization_data['day_of_week'].map(day_mapping)
    # 時間帯（仮のデータ）
    utilization_data['time_slot'] = np.random.choice(
        ['9-12時', '12-15時', '15-18時', '18-21時', '21-24時'],
        len(utilization_data)
    )

# タブ内容の表示
if page == "概要":
    # メトリックカード用のHTMLテンプレート
    def metric_card_html(title, value, icon_color, icon_emoji, suffix=""):
        return f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="metric-label">{title}</div>
                    <div class="metric-value" style="color: {icon_color};">{value}{suffix}</div>
                </div>
                <div style="background-color: {icon_color}20; padding: 8px; border-radius: 50%;">
                    <span style="color: {icon_color}; font-size: 20px;">{icon_emoji}</span>
                </div>
            </div>
        </div>
        """

    # 統計カード
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_members = len(members_data) if members_data is not None else "---"
        st.markdown(
            metric_card_html("総メンバー数", total_members, "#6979F8", "👥"),
            unsafe_allow_html=True
        )

    with col2:
        active_members = len(members_data[members_data['status'] == 'active']) if members_data is not None else 0
        total_members_int = len(members_data) if members_data is not None else 1
        join_rate = f"{active_members / total_members_int * 100:.1f}" if total_members_int > 0 else "---"

        st.markdown(
            metric_card_html("アクティブ会員数", active_members, "#10B981", "👥", f"<div style='font-size: 0.75rem; color: #999;'>入会率: {join_rate}%</div>"),
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            metric_card_html("トライアル体験者数", "---", "#00C6FF", "👥"),
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            metric_card_html("ビジター数", "---", "#FF5EDF", "👥"),
            unsafe_allow_html=True
        )

    # チャート
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ルーム別稼働率")
        if utilization_data is not None:
            # ルーム別の平均稼働率を計算
            room_avg = utilization_data.groupby('room')['occupancy_rate'].mean().reset_index()

            # グラフの作成
            fig = px.bar(
                room_avg,
                x='room',
                y='occupancy_rate',
                text_auto='.1f',
                color='room',
                color_discrete_map={
                    'Room1': '#6979F8',
                    'Room2': '#BE52F2',
                    'Room3': '#FF5EDF'
                },
                labels={
                    'room': 'ルーム',
                    'occupancy_rate': '稼働率 (%)'
                },
                title='ルーム別平均稼働率'
            )
            fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div style="height: 300px; display: flex; justify-content: center; align-items: center; border: 1px dashed #ccc; border-radius: 5px;"><p style="color: #999;">データロード中...</p></div>', unsafe_allow_html=True)

    with col2:
        st.subheader("会員属性")
        if members_data is not None:
            # 性別分布用タブ
            tabs = st.tabs(["性別分布", "年齢分布"])

            # 性別分布
            with tabs[0]:
                gender_counts = members_data['gender'].value_counts().reset_index()
                gender_counts.columns = ['gender', 'count']

                fig = px.pie(
                    gender_counts,
                    names='gender',
                    values='count',
                    color='gender',
                    color_discrete_map={
                        '男性': '#6979F8',
                        '女性': '#FF5EDF'
                    },
                    hole=0.4
                )
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            # 年齢分布
            with tabs[1]:
                age_counts = members_data['age_group'].value_counts().reset_index()
                age_counts.columns = ['age_group', 'count']

                # 年齢カテゴリを順序付け
                age_order = ['~19歳', '20代', '30代', '40代', '50代', '60歳~']
                age_counts['age_group'] = pd.Categorical(
                    age_counts['age_group'],
                    categories=age_order,
                    ordered=True
                )
                age_counts = age_counts.sort_values('age_group')

                fig = px.bar(
                    age_counts,
                    x='age_group',
                    y='count',
                    text_auto=True,
                    color='age_group',
                    labels={
                        'age_group': '年齢層',
                        'count': '会員数'
                    }
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div style="height: 300px; display: flex; justify-content: center; align-items: center; border: 1px dashed #ccc; border-radius: 5px;"><p style="color: #999;">データロード中...</p></div>', unsafe_allow_html=True)

    # 曜日別稼働率
    st.subheader("曜日別稼働率")
    if utilization_data is not None:
        # 曜日別の平均稼働率を計算
        weekday_avg = utilization_data.groupby(['day_of_week_jp', 'room'])['occupancy_rate'].mean().reset_index()

        # 曜日の順序を設定
        weekday_order = ['月', '火', '水', '木', '金', '土', '日']
        weekday_avg['day_of_week_jp'] = pd.Categorical(
            weekday_avg['day_of_week_jp'],
            categories=weekday_order,
            ordered=True
        )
        weekday_avg = weekday_avg.sort_values('day_of_week_jp')

        # グラフの作成
        fig = px.line(
            weekday_avg,
            x='day_of_week_jp',
            y='occupancy_rate',
            color='room',
            markers=True,
            color_discrete_map={
                'Room1': '#6979F8',
                'Room2': '#BE52F2',
                'Room3': '#FF5EDF'
            },
            labels={
                'day_of_week_jp': '曜日',
                'occupancy_rate': '稼働率 (%)',
                'room': 'ルーム'
            }
        )
        fig.update_traces(texttemplate='%{y:.1f}%', textposition='top center')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div style="height: 300px; display: flex; justify-content: center; align-items: center; border: 1px dashed #ccc; border-radius: 5px;"><p style="color: #999;">データロード中...</p></div>', unsafe_allow_html=True)

    # 月別稼働率の推移
    st.subheader("月別稼働率推移")
    if utilization_data is not None:
        # 月別の平均稼働率を計算
        monthly_avg = utilization_data.groupby(['month', 'room'])['occupancy_rate'].mean().reset_index()

        # 月の順序を設定
        monthly_avg['month'] = pd.to_datetime(monthly_avg['month'])
        monthly_avg = monthly_avg.sort_values('month')
        monthly_avg['month'] = monthly_avg['month'].dt.strftime('%Y-%m')

        # グラフの作成
        fig = px.line(
            monthly_avg,
            x='month',
            y='occupancy_rate',
            color='room',
            markers=True,
            color_discrete_map={
                'Room1': '#6979F8',
                'Room2': '#BE52F2',
                'Room3': '#FF5EDF'
            },
            labels={
                'month': '月',
                'occupancy_rate': '稼働率 (%)',
                'room': 'ルーム'
            }
        )
        # x軸のラベルを回転
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div style="height: 300px; display: flex; justify-content: center; align-items: center; border: 1px dashed #ccc; border-radius: 5px;"><p style="color: #999;">データロード中...</p></div>', unsafe_allow_html=True)

elif page == "会員分析":
    # 会員統計カード
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "総メンバー数",
            len(members_data) if members_data is not None else "---"
        )
    with col2:
        active_members = len(members_data[members_data['status'] == 'active']) if members_data is not None else 0
        total_members = len(members_data) if members_data is not None else 1
        st.metric(
            "アクティブ会員数",
            active_members if members_data is not None else "---"
        )
    with col3:
        join_rate = f"{active_members / total_members * 100:.1f}%" if total_members > 0 else "---%"
        inactive_members = total_members - active_members
        st.metric(
            "入会率",
            join_rate,
            f"{active_members}/{total_members}" if total_members > 0 else "--/--"
        )
    with col4:
        churn_rate = f"{inactive_members / total_members * 100:.1f}%" if total_members > 0 else "---%"
        st.metric(
            "退会率",
            churn_rate,
            f"{inactive_members}/{total_members}" if total_members > 0 else "--/--"
        )

    # 性別・年齢分布
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("性別分布")
        if members_data is not None:
            gender_counts = members_data['gender'].value_counts().reset_index()
            gender_counts.columns = ['gender', 'count']

            fig = px.pie(
                gender_counts,
                names='gender',
                values='count',
                color='gender',
                color_discrete_map={
                    '男性': '#6979F8',
                    '女性': '#FF5EDF'
                },
                hole=0.4
            )
            fig.update_traces(textinfo='percent+label')

            # ドーナツチャートの中央にテキストを追加
            fig.add_annotation(
                text=f'合計<br>{gender_counts["count"].sum()}名',
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.text("データロード中...")

    with col2:
        st.subheader("年齢分布")
        if members_data is not None:
            age_counts = members_data['age_group'].value_counts().reset_index()
            age_counts.columns = ['age_group', 'count']

            # 年齢カテゴリを順序付け
            age_order = ['~19歳', '20代', '30代', '40代', '50代', '60歳~']
            age_counts['age_group'] = pd.Categorical(
                age_counts['age_group'],
                categories=age_order,
                ordered=True
            )
            age_counts = age_counts.sort_values('age_group')

            fig = px.bar(
                age_counts,
                x='age_group',
                y='count',
                text_auto=True,
                color='age_group',
                labels={
                    'age_group': '年齢層',
                    'count': '会員数'
                }
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.text("データロード中...")

    # 地域分布
    st.subheader("地域分布")
    if members_data is not None:
        region_counts = members_data['region'].value_counts().reset_index()
        region_counts.columns = ['region', 'count']

        fig = px.bar(
            region_counts,
            x='region',
            y='count',
            text_auto=True,
            color='region',
            labels={
                'region': '地域',
                'count': '会員数'
            }
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # 地図表示のオプション（将来的な拡張）
        show_map = st.checkbox("地図で表示", value=False)
        if show_map:
            st.info("こちらの機能は今後実装予定です。")
    else:
        st.text("データロード中...")

    # 会員推移グラフ
    st.subheader("会員推移")
    if members_data is not None:
        # 入会日を日付型に変換
        members_data['join_date'] = pd.to_datetime(members_data['join_date'])

        # 月ごとの入会者数を集計
        monthly_joins = members_data.groupby(members_data['join_date'].dt.strftime('%Y-%m')).size().reset_index()
        monthly_joins.columns = ['month', 'new_members']

        # データを時系列順に並べ替え
        monthly_joins['month'] = pd.to_datetime(monthly_joins['month'])
        monthly_joins = monthly_joins.sort_values('month')
        monthly_joins['month'] = monthly_joins['month'].dt.strftime('%Y-%m')

        # 累積会員数を計算
        monthly_joins['cumulative_members'] = monthly_joins['new_members'].cumsum()

        # グラフの作成
        fig = go.Figure()

        # 新規会員数（棒グラフ）
        fig.add_trace(
            go.Bar(
                x=monthly_joins['month'],
                y=monthly_joins['new_members'],
                name='新規会員数',
                marker_color='#6979F8'
            )
        )

        # 累積会員数（折れ線グラフ）
        fig.add_trace(
            go.Scatter(
                x=monthly_joins['month'],
                y=monthly_joins['cumulative_members'],
                name='累積会員数',
                marker_color='#FF5EDF',
                line=dict(width=3),
                yaxis='y2'
            )
        )

        # レイアウトの調整
        fig.update_layout(
            title='月別会員登録数と累積会員数',
            xaxis_title='月',
            yaxis=dict(
                title='新規会員数',
                titlefont=dict(color='#6979F8'),
                tickfont=dict(color='#6979F8')
            ),
            yaxis2=dict(
                title='累積会員数',
                titlefont=dict(color='#FF5EDF'),
                tickfont=dict(color='#FF5EDF'),
                anchor='x',
                overlaying='y',
                side='right'
            ),
            xaxis_tickangle=-45,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            )
        )

        st.plotly_chart(fig, use_container_width=True)

        # 詳細データの表示オプション
        show_data = st.checkbox("詳細データを表示", value=False)
        if show_data:
            st.dataframe(monthly_joins)
    else:
        st.text("データロード中...")

elif page == "ルーム稼働率":
    # ルーム稼働率カード
    col1, col2, col3 = st.columns(3)
    if utilization_data is not None:
        # 各ルームの平均稼働率を計算
        room1_avg = utilization_data[utilization_data['room'] == 'Room1']['occupancy_rate'].mean()
        room2_avg = utilization_data[utilization_data['room'] == 'Room2']['occupancy_rate'].mean()
        room3_avg = utilization_data[utilization_data['room'] == 'Room3']['occupancy_rate'].mean()

        with col1:
            st.metric("Room1 稼働率", f"{room1_avg:.1f}%")
        with col2:
            st.metric("Room2 稼働率", f"{room2_avg:.1f}%")
        with col3:
            st.metric("Room3 稼働率", f"{room3_avg:.1f}%")
    else:
        with col1:
            st.metric("Room1 稼働率", "---%")
        with col2:
            st.metric("Room2 稼働率", "---%")
        with col3:
            st.metric("Room3 稼働率", "---%")

    # 稼働率比較チャート
    st.subheader("ルーム稼働率比較")
    if utilization_data is not None:
        # ルーム別の平均稼働率を計算
        room_avg = utilization_data.groupby('room')['occupancy_rate'].mean().reset_index()

        # グラフの作成
        fig = px.bar(
            room_avg,
            x='room',
            y='occupancy_rate',
            text_auto='.1f',
            color='room',
            color_discrete_map={
                'Room1': '#6979F8',
                'Room2': '#BE52F2',
                'Room3': '#FF5EDF'
            },
            labels={
                'room': 'ルーム',
                'occupancy_rate': '稼働率 (%)'
            },
            title=f"{period}の平均稼働率"
        )
        fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.text("データロード中...")

    # 年間推移チャート
    st.subheader("年間推移")
    if utilization_data is not None:
        # 月別の平均稼働率を計算
        monthly_avg = utilization_data.groupby(['month', 'room'])['occupancy_rate'].mean().reset_index()

        # 月の順序を設定
        monthly_avg['month'] = pd.to_datetime(monthly_avg['month'])
        monthly_avg = monthly_avg.sort_values('month')
        monthly_avg['month'] = monthly_avg['month'].dt.strftime('%Y-%m')

        # グラフの作成
        fig = px.line(
            monthly_avg,
            x='month',
            y='occupancy_rate',
            color='room',
            markers=True,
            color_discrete_map={
                'Room1': '#6979F8',
                'Room2': '#BE52F2',
                'Room3': '#FF5EDF'
            },
            labels={
                'month': '月',
                'occupancy_rate': '稼働率 (%)',
                'room': 'ルーム'
            }
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.text("データロード中...")

    # 月別稼働率テーブル
    st.subheader("月別稼働率詳細")
    if utilization_data is not None:
        # 月別・ルーム別の平均稼働率を計算
        monthly_table = utilization_data.pivot_table(
            index='month',
            columns='room',
            values='occupancy_rate',
            aggfunc='mean'
        ).reset_index()

        # 月の順序を設定
        monthly_table['month'] = pd.to_datetime(monthly_table['month'])
        monthly_table = monthly_table.sort_values('month')
        monthly_table['month'] = monthly_table['month'].dt.strftime('%Y-%m')

        # データフレームの表示形式を整える
        formatted_table = monthly_table.copy()
        for room in ['Room1', 'Room2', 'Room3']:
            if room in formatted_table.columns:
                formatted_table[room] = formatted_table[room].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "---")

        # 詳細ボタンを追加
        formatted_table['詳細'] = [f'<a href="#" class="detail-btn" data-month="{month}">詳細を見る</a>' for month in formatted_table['month']]

        # HTMLとしてテーブルを表示
        st.write(formatted_table.to_html(escape=False, index=False), unsafe_allow_html=True)

        # 詳細を表示する月を選択
        selected_month = st.selectbox("月を選択して詳細を表示", monthly_table['month'].tolist())

        if selected_month:
            st.subheader(f"{selected_month} の詳細データ")

            # 選択した月のデータ
            month_data = utilization_data[utilization_data['month'] == selected_month]

            if not month_data.empty:
                # ルーム別稼働率
                room_rates = month_data.groupby('room')['occupancy_rate'].mean()

                # 3つのメトリックカードを表示
                cols = st.columns(3)
                for i, room in enumerate(['Room1', 'Room2', 'Room3']):
                    if room in room_rates:
                        cols[i].metric(f"{room} 稼働率", f"{room_rates[room]:.1f}%")
                    else:
                        cols[i].metric(f"{room} 稼働率", "---")

                # 月間稼働率比較グラフ
                st.subheader("月間稼働率比較")

                # ルーム別稼働率の分布をボックスプロットで表示
                fig = px.box(
                    month_data,
                    x='room',
                    y='occupancy_rate',
                    color='room',
                    color_discrete_map={
                        'Room1': '#6979F8',
                        'Room2': '#BE52F2',
                        'Room3': '#FF5EDF'
                    },
                    labels={
                        'room': 'ルーム',
                        'occupancy_rate': '稼働率 (%)'
                    },
                    points="all"
                )
                st.plotly_chart(fig, use_container_width=True)

                # 曜日別稼働率
                st.subheader("曜日別稼働率")

                weekday_avg = month_data.groupby(['day_of_week_jp', 'room'])['occupancy_rate'].mean().reset_index()

                # 曜日の順序を設定
                weekday_order = ['月', '火', '水', '木', '金', '土', '日']
                weekday_avg['day_of_week_jp'] = pd.Categorical(
                    weekday_avg['day_of_week_jp'],
                    categories=weekday_order,
                    ordered=True
                )
                weekday_avg = weekday_avg.sort_values('day_of_week_jp')

                # グラフの作成
                fig = px.bar(
                    weekday_avg,
                    x='day_of_week_jp',
                    y='occupancy_rate',
                    color='room',
                    barmode='group',
                    text_auto='.1f',
                    color_discrete_map={
                        'Room1': '#6979F8',
                        'Room2': '#BE52F2',
                        'Room3': '#FF5EDF'
                    },
                    labels={
                        'day_of_week_jp': '曜日',
                        'occupancy_rate': '稼働率 (%)',
                        'room': 'ルーム'
                    }
                )
                fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"{selected_month} のデータはありません。")
    else:
        st.text("データロード中...")

elif page == "曜日・時間分析":
    # 曜日別稼働率チャート
    st.subheader("曜日別稼働率")
    if utilization_data is not None:
        # 曜日別の平均稼働率を計算
        weekday_avg = utilization_data.groupby(['day_of_week_jp', 'room'])['occupancy_rate'].mean().reset_index()

        # 曜日の順序を設定
        weekday_order = ['月', '火', '水', '木', '金', '土', '日']
        weekday_avg['day_of_week_jp'] = pd.Categorical(
            weekday_avg['day_of_week_jp'],
            categories=weekday_order,
            ordered=True
        )
        weekday_avg = weekday_avg.sort_values('day_of_week_jp')

        # グラフの作成
        fig = px.line(
            weekday_avg,
            x='day_of_week_jp',
            y='occupancy_rate',
            color='room',
            markers=True,
            color_discrete_map={
                'Room1': '#6979F8',
                'Room2': '#BE52F2',
                'Room3': '#FF5EDF'
            },
            labels={
                'day_of_week_jp': '曜日',
                'occupancy_rate': '稼働率 (%)',
                'room': 'ルーム'
            }
        )
        fig.update_traces(texttemplate='%{y:.1f}%', textposition='top center')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.text("データロード中...")

    # 時間帯別稼働率チャート
    st.subheader("時間帯別稼働率")
    if utilization_data is not None:
        # 時間帯別の平均稼働率を計算
        timeslot_avg = utilization_data.groupby(['time_slot', 'room'])['occupancy_rate'].mean().reset_index()

        # 時間帯の順序を設定
        timeslot_order = ['9-12時', '12-15時', '15-18時', '18-21時', '21-24時']
        timeslot_avg['time_slot'] = pd.Categorical(
            timeslot_avg['time_slot'],
            categories=timeslot_order,
            ordered=True
        )
        timeslot_avg = timeslot_avg.sort_values('time_slot')

        # グラフの作成
        fig = px.bar(
            timeslot_avg,
            x='time_slot',
            y='occupancy_rate',
            color='room',
            barmode='group',
            text_auto='.1f',
            color_discrete_map={
                'Room1': '#6979F8',
                'Room2': '#BE52F2',
                'Room3': '#FF5EDF'
            },
            labels={
                'time_slot': '時間帯',
                'occupancy_rate': '稼働率 (%)',
                'room': 'ルーム'
            }
        )
        fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.text("データロード中...")

    # ルーム別詳細分析
    st.subheader("ルーム別曜日稼働率")
    if utilization_data is not None:
        # タブを作成
        room_tabs = st.tabs(["Room1 曜日別稼働率", "Room2 曜日別稼働率", "Room3 曜日別稼働率"])

        for i, room in enumerate(['Room1', 'Room2', 'Room3']):
            with room_tabs[i]:
                # そのルームのデータを抽出
                room_data = utilization_data[utilization_data['room'] == room]

                if not room_data.empty:
                    # 曜日と時間帯のクロス集計
                    heatmap_data = room_data.pivot_table(
                        index='day_of_week_jp',
                        columns='time_slot',
                        values='occupancy_rate',
                        aggfunc='mean'
                    ).reset_index()

                    # 曜日の順序を設定
                    weekday_order = ['月', '火', '水', '木', '金', '土', '日']
                    heatmap_data['day_of_week_jp'] = pd.Categorical(
                        heatmap_data['day_of_week_jp'],
                        categories=weekday_order,
                        ordered=True
                    )
                    heatmap_data = heatmap_data.sort_values('day_of_week_jp')

                    # ヒートマップ形式に変換
                    heatmap_df = pd.melt(
                        heatmap_data,
                        id_vars=['day_of_week_jp'],
                        var_name='time_slot',
                        value_name='occupancy_rate'
                    )

                    # 時間帯の順序を設定
                    timeslot_order = ['9-12時', '12-15時', '15-18時', '18-21時', '21-24時']
                    heatmap_df['time_slot'] = pd.Categorical(
                        heatmap_df['time_slot'],
                        categories=timeslot_order,
                        ordered=True
                    )
                    heatmap_df = heatmap_df.sort_values(['day_of_week_jp', 'time_slot'])

                    # ヒートマップの作成
                    fig = px.density_heatmap(
                        heatmap_df,
                        x='time_slot',
                        y='day_of_week_jp',
                        z='occupancy_rate',
                        color_continuous_scale=[
                            [0, '#f7fbff'],
                            [0.3, '#c7dcef'],
                            [0.6, '#73b3d8'],
                            [1, '#08306b']
                        ],
                        labels={
                            'time_slot': '時間帯',
                            'day_of_week_jp': '曜日',
                            'occupancy_rate': '稼働率 (%)'
                        }
                    )
                    fig.update_layout(coloraxis_colorbar=dict(title='稼働率 (%)'))

                    # 各セルに値を表示
                    fig.update_traces(
                        text=heatmap_df['occupancy_rate'].apply(lambda x: f"{x:.1f}%"),
                        texttemplate="%{text}",
                        textfont={"size": 12}
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"{room} のデータはありません。")
    else:
        st.text("データロード中...")

elif page == "競合分析":
    # 競合施設料金比較
    st.subheader("競合施設 料金比較")
    st.caption("大阪市内の主なプライベートサウナ施設の料金比較（1時間あたり）")

    if competitors_data is not None:
        # 料金の比較グラフ
        sorted_competitors = competitors_data.sort_values('hourly_rate')

        # 自社のデータに色を付ける
        colors = ['#BE52F2' if name == 'HAAAVE.sauna' else '#6979F8' for name in sorted_competitors['name']]

        fig = px.bar(
            sorted_competitors,
            x='name',
            y='hourly_rate',
            text_auto=True,
            color='name',
            color_discrete_sequence=colors,
            labels={
                'name': '施設名',
                'hourly_rate': '1時間あたり料金 (円)'
            }
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # レーダーチャートの追加オプション
        show_radar = st.checkbox("レーダーチャートで比較", value=False)
        if show_radar:
            # カテゴリ別の評価データ（ダミー）
            categories = ['料金の安さ', '設備の充実度', 'サービスの質', '清潔さ', 'アクセス', '混雑度の低さ']

            # ダミー評価データの作成
            radar_data = {}
            for name in competitors_data['name']:
                if name == 'HAAAVE.sauna':
                    # 自社の評価（高め）
                    radar_data[name] = [
                        np.random.uniform(3.5, 5.0) for _ in range(len(categories))
                    ]
                else:
                    # 競合の評価
                    radar_data[name] = [
                        np.random.uniform(2.0, 4.5) for _ in range(len(categories))
                    ]

            # レーダーチャートの作成
            fig = go.Figure()

            for name, values in radar_data.items():
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=name,
                    line_color='#BE52F2' if name == 'HAAAVE.sauna' else None
                ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5]
                    )
                ),
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)

            st.info("注: 評価データはデモ用のダミーデータです。")
    else:
        st.text("データロード中...")

    # 競合施設詳細比較
    st.subheader("競合施設詳細比較")
    if competitors_data is not None:
        # 表の表示
        styled_df = competitors_data.copy()

        # 表示するカラムを選択
        columns_to_display = ['name', 'location', 'area', 'type', 'hourly_rate', 'rooms', 'cold_bath', 'mixed_gender', 'opening_year']
        formatted_df = styled_df[columns_to_display].copy()

        # カラム名を日本語に変更
        formatted_df.columns = ['施設名', '所在地', 'エリア', '形態', '料金', 'ルーム数', '水風呂', '男女混浴', '開業年']

        # 自社の行をハイライト
        def highlight_haaave(row):
            if row['施設名'] == 'HAAAVE.sauna':
                return ['background-color: #f0e6ff'] * len(row)
            return [''] * len(row)

        st.dataframe(
            formatted_df.style.apply(highlight_haaave, axis=1),
            use_container_width=True
        )
    else:
        st.text("データロード中...")

    # 地域分布
    st.subheader("競合施設 地域分布")
    if competitors_data is not None and 'area' in competitors_data.columns:
        # エリア別の集計
        area_counts = competitors_data['area'].value_counts().reset_index()
        area_counts.columns = ['area', 'count']

        fig = px.pie(
            area_counts,
            names='area',
            values='count',
            hole=0.4,
            labels={
                'area': 'エリア',
                'count': '施設数'
            }
        )
        fig.update_traces(textinfo='percent+label')

        # 中央にテキスト追加
        fig.add_annotation(
            text=f'合計<br>{area_counts["count"].sum()}施設',
            x=0.5, y=0.5,
            font_size=20,
            showarrow=False
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.text("データロード中...")

elif page == "売上分析":
    # 売上統計カード
    col1, col2, col3 = st.columns(3)

    if finance_data is not None:
        # 最新のデータ
        latest_data = finance_data.iloc[-1]

        with col1:
            st.metric(
                "直近月間売上",
                f"¥{latest_data['sales']:,.0f}"
            )
        with col2:
            st.metric(
                "直近月間利益",
                f"¥{latest_data['profit']:,.0f}"
            )
        with col3:
            st.metric(
                "直近月間利益率",
                f"{latest_data['profit_rate']:.1f}%"
            )
    else:
        with col1:
            st.metric("直近月間売上", "¥---")
        with col2:
            st.metric("直近月間利益", "¥---")
        with col3:
            st.metric("直近月間利益率", "---%")

    # 月別売上・利益推移
    st.subheader("月別売上・利益推移")
    if finance_data is not None:
        # 月を日付型に変換して並べ替え
        finance_data['month_date'] = pd.to_datetime(finance_data['month'])
        sorted_data = finance_data.sort_values('month_date')

        # グラフの作成
        fig = go.Figure()

        # 売上（棒グラフ）
        fig.add_trace(
            go.Bar(
                x=sorted_data['month'],
                y=sorted_data['sales'],
                name='売上',
                marker_color='#6979F8'
            )
        )

        # 利益（棒グラフ）
        fig.add_trace(
            go.Bar(
                x=sorted_data['month'],
                y=sorted_data['profit'],
                name='利益',
                marker_color='#10B981'
            )
        )

        # 利益率（折れ線グラフ）
        fig.add_trace(
            go.Scatter(
                x=sorted_data['month'],
                y=sorted_data['profit_rate'],
                name='利益率',
                marker_color='#FF5EDF',
                line=dict(width=3),
                yaxis='y2'
            )
        )

        # レイアウトの調整
        fig.update_layout(
            xaxis_title='月',
            yaxis=dict(
                title='金額 (円)',
                titlefont=dict(color='#6979F8'),
                tickfont=dict(color='#6979F8')
            ),
            yaxis2=dict(
                title='利益率 (%)',
                titlefont=dict(color='#FF5EDF'),
                tickfont=dict(color='#FF5EDF'),
                anchor='x',
                overlaying='y',
                side='right'
            ),
            xaxis_tickangle=-45,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            barmode='group'
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.text("データロード中...")

    # 利用者タイプ別平均利用料金
    st.subheader("利用者タイプ別平均利用料金")

    # ユーザータイプごとの売上シミュレーション（ダミー）
    user_types = ['会員', 'ビジター', '体験者']
    avg_spending = [2800, 3500, 2200]  # 平均利用単価
    user_counts = [65, 20, 15]  # ユーザー数（割合）

    # グラフデータの作成
    user_data = pd.DataFrame({
        'user_type': user_types,
        'avg_spending': avg_spending,
        'user_count': user_counts
    })

    col1, col2 = st.columns(2)

    with col1:
        # 平均利用単価のグラフ
        fig = px.bar(
            user_data,
            x='user_type',
            y='avg_spending',
            text_auto=True,
            color='user_type',
            labels={
                'user_type': 'ユーザータイプ',
                'avg_spending': '平均利用単価 (円/回)'
            }
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # ユーザー数の割合
        fig = px.pie(
            user_data,
            names='user_type',
            values='user_count',
            color='user_type',
            hole=0.4,
            labels={
                'user_type': 'ユーザータイプ',
                'user_count': '利用者数'
            }
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    st.info("注: このデータはデモ用のシミュレーションデータです。")
