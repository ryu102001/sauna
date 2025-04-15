import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# アプリの初期化
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# カラーパレット
COLORS = {
    "primary": "#6979F8",
    "secondary": "#BE52F2",
    "accent1": "#00C6FF",
    "accent2": "#FF5EDF",
    "light": "#F7F8FC",
    "white": "#FFFFFF",
    "dark": "#121438",
    "gray": "#E2E8F0",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "room1": "#6979F8",
    "room2": "#BE52F2",
    "room3": "#FF5EDF",
    "male": "#6979F8",
    "female": "#FF5EDF",
}

# PIEチャート用の色配列
PIE_COLORS = [
    COLORS["primary"],
    COLORS["secondary"],
    COLORS["accent1"],
    COLORS["accent2"],
    COLORS["success"],
    COLORS["warning"]
]

# ダミーデータの生成用関数
def generate_dummy_data():
    # ダミーデータを返すだけ
    # 実際の実装では、データベースやAPIからデータを取得する

    # 月のリスト
    months = pd.date_range(start='2023-05-01', end='2025-03-01', freq='MS').strftime('%Y-%m').tolist()

    # 曜日
    days_of_week = ['月', '火', '水', '木', '金', '土', '日']

    # 時間帯
    time_slots = ['9-12時', '12-15時', '15-18時', '18-21時', '21-24時']

    # 地域
    regions = ['大阪府', '兵庫県', '京都府', '奈良県', '滋賀県', '和歌山県', 'その他']

    # 部屋名
    room_names = ['Room1', 'Room2', 'Room3']

    # 競合施設名
    competitor_names = ['HAAAVE.sauna', 'KUDOCHI sauna', 'MENTE', 'M\'s Sauna', 'SAUNA Pod 槃',
                        'SAUNA OOO OSAKA', '大阪サウナ DESSE']

    # 年齢層
    age_groups = ['20代', '30代', '40代', '50代', '~19歳', '60歳~']

    # 性別
    genders = ['男性', '女性']

    return {
        "labels": {
            "months": months,
            "days_of_week": days_of_week,
            "time_slots": time_slots,
            "regions": regions,
            "room_names": room_names,
            "competitor_names": competitor_names,
            "age_groups": age_groups,
            "genders": genders
        }
    }

# ダミーデータの取得
dummy_data = generate_dummy_data()

# カードコンポーネント
def create_card(title, value, icon, color=COLORS["primary"], subvalue=None):
    card_content = [
        dbc.CardHeader(title, className="text-muted small"),
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.P(value, className="h3 font-weight-bold mb-0", style={"color": color}),
                    html.P(subvalue, className="text-muted small") if subvalue else None,
                ], className="col-8"),
                html.Div([
                    html.Span(icon, className="p-2 rounded-circle",
                              style={"backgroundColor": f"{color}20"})
                ], className="col-4 d-flex justify-content-end align-items-start"),
            ], className="row")
        ])
    ]
    return dbc.Card(card_content, className="mb-4 shadow-sm")

# チャートカードコンポーネント
def create_chart_card(title, subtitle, chart_content):
    return dbc.Card([
        dbc.CardBody([
            html.H5(title, className="font-weight-medium text-dark"),
            html.P(subtitle, className="text-muted small mb-4") if subtitle else None,
            chart_content
        ])
    ], className="mb-4 shadow-sm")

# プレースホルダーチャート
def placeholder_chart(height=300):
    return html.Div([
        html.P("データロード中...", className="text-muted")
    ], className="d-flex justify-content-center align-items-center", style={"height": f"{height}px"})

# サイドバーの項目
def create_sidebar_item(icon, label, active=False):
    return dbc.Button([
        html.Span(icon, className="mr-3"),
        html.Span(label)
    ], color="primary" if active else "light", outline=True,
       className="mb-2 text-left w-100", id=f"nav-{label}")

# サイドバーの作成
sidebar = html.Div([
    html.Div([
        html.H4("HAAAVE.sauna", className="font-weight-bold"),
        html.Button(
            "≡",
            className="btn btn-light",
            id="toggle-sidebar"
        )
    ], className="d-flex justify-content-between align-items-center p-3"),

    html.Hr(),

    html.Div([
        create_sidebar_item("📊", "概要", active=True),
        create_sidebar_item("👥", "会員分析"),
        create_sidebar_item("📅", "ルーム稼働率"),
        create_sidebar_item("🎯", "曜日・時間分析"),
        create_sidebar_item("📈", "競合分析"),
        create_sidebar_item("💰", "売上分析"),
    ], className="p-3"),
], id="sidebar", className="bg-white shadow-sm", style={"width": "250px", "height": "100vh", "position": "fixed"})

# ヘッダーの作成
header = html.Div([
    html.Div([
        html.H4("サウナ施設分析ダッシュボード", className="mb-0"),
        html.P("データに基づく施設運営の最適化", className="text-muted small"),
    ]),

    html.Div([
        dbc.Select(
            id="period-selector",
            options=[
                {"label": "全期間", "value": "all"},
                {"label": "2023年", "value": "2023"},
                {"label": "2024年", "value": "2024"},
                {"label": "2025年", "value": "2025"},
            ],
            value="all",
            className="mr-2"
        ),
        dbc.Button("🔄", color="light", className="mr-2", id="refresh-btn"),
        dbc.Button("🔍", color="light", className="mr-2", id="filter-btn"),
        dbc.Button("📥", color="light", id="download-btn"),
    ], className="d-flex")
], className="d-flex justify-content-between align-items-center bg-white p-4 shadow-sm",
   style={"marginLeft": "250px"})

# 概要タブの内容
overview_tab = html.Div([
    # 基本統計カード
    html.Div([
        dbc.Row([
            dbc.Col(create_card("総メンバー数", "---", "👥", COLORS["primary"]), width=12, md=6, lg=3),
            dbc.Col(create_card("アクティブ会員数", "---", "👥", COLORS["success"], "入会率: ---%"), width=12, md=6, lg=3),
            dbc.Col(create_card("トライアル体験者数", "---", "👥", COLORS["accent1"]), width=12, md=6, lg=3),
            dbc.Col(create_card("ビジター数", "---", "👥", COLORS["accent2"]), width=12, md=6, lg=3),
        ], className="mb-4")
    ]),

    # ルーム稼働率と会員属性
    dbc.Row([
        dbc.Col(create_chart_card(
            "ルーム別稼働率",
            "全期間の平均稼働率",
            placeholder_chart(300)
        ), width=12, lg=6),

        dbc.Col(create_chart_card(
            "会員属性",
            "性別・年齢分布",
            placeholder_chart(300)
        ), width=12, lg=6),
    ], className="mb-4"),

    # 曜日別稼働率
    create_chart_card(
        "曜日別稼働率",
        "各ルームの曜日別稼働状況",
        placeholder_chart(300)
    ),

    # 月別稼働率の推移
    create_chart_card(
        "月別稼働率推移",
        "各ルームの月別稼働率推移",
        placeholder_chart(300)
    ),
])

# 会員分析タブ
members_tab = html.Div([
    # 会員統計カード
    dbc.Row([
        dbc.Col(create_card("総メンバー数", "---", "👥", COLORS["primary"]), width=12, md=6, lg=3),
        dbc.Col(create_card("アクティブ会員数", "---", "👥", COLORS["success"]), width=12, md=6, lg=3),
        dbc.Col(create_card("入会率", "---%", "📈", COLORS["accent1"], "--/--"), width=12, md=6, lg=3),
        dbc.Col(create_card("退会率", "---%", "📈", COLORS["danger"], "--/--"), width=12, md=6, lg=3),
    ], className="mb-4"),

    # 性別・年齢分布
    dbc.Row([
        dbc.Col(create_chart_card(
            "性別分布",
            "会員の性別比率",
            placeholder_chart(300)
        ), width=12, lg=6),

        dbc.Col(create_chart_card(
            "年齢分布",
            "会員の年代別分布",
            placeholder_chart(300)
        ), width=12, lg=6),
    ], className="mb-4"),

    # 地域分布
    create_chart_card(
        "地域分布",
        "会員の都道府県別分布",
        placeholder_chart(300)
    ),

    # 会員推移グラフ
    create_chart_card(
        "会員推移",
        "会員・体験者・ビジターの月別推移",
        placeholder_chart(300)
    ),
])

# ルーム稼働率タブ
utilization_tab = html.Div([
    # ルーム稼働率カード
    dbc.Row([
        dbc.Col(create_card("Room1 稼働率", "---%", "📊", COLORS["room1"]), width=12, md=4),
        dbc.Col(create_card("Room2 稼働率", "---%", "📊", COLORS["room2"]), width=12, md=4),
        dbc.Col(create_card("Room3 稼働率", "---%", "📊", COLORS["room3"]), width=12, md=4),
    ], className="mb-4"),

    # 稼働率比較チャート
    create_chart_card(
        "ルーム稼働率比較",
        "全期間の平均稼働率",
        placeholder_chart(300)
    ),

    # 年間推移チャート
    create_chart_card(
        "年間推移",
        "各ルームの年間稼働率推移",
        placeholder_chart(300)
    ),

    # 月別稼働率テーブル
    create_chart_card(
        "月別稼働率詳細",
        "各ルームの月別稼働率データ",
        html.Div([
            dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("月"),
                        html.Th("Room1"),
                        html.Th("Room2"),
                        html.Th("Room3"),
                        html.Th("詳細"),
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(month),
                        html.Td("---"),
                        html.Td("---"),
                        html.Td("---"),
                        html.Td(
                            dbc.Button("詳細を見る", color="link", size="sm", id=f"detail-btn-{i}")
                        )
                    ]) for i, month in enumerate(dummy_data["labels"]["months"])
                ]),
            ], bordered=True, hover=True, responsive=True, striped=True)
        ])
    ),
])

# 曜日・時間分析タブ
daytime_tab = html.Div([
    # 曜日別稼働率チャート
    create_chart_card(
        "曜日別稼働率",
        "各ルームの曜日別稼働状況",
        placeholder_chart(300)
    ),

    # 時間帯別稼働率チャート
    create_chart_card(
        "時間帯別稼働率",
        "各ルームの時間帯別稼働状況",
        placeholder_chart(300)
    ),

    # ルーム別分析
    dbc.Row([
        dbc.Col(create_chart_card(
            "Room1 曜日別稼働率",
            "Room1の曜日別詳細",
            placeholder_chart(200)
        ), width=12, md=4),

        dbc.Col(create_chart_card(
            "Room2 曜日別稼働率",
            "Room2の曜日別詳細",
            placeholder_chart(200)
        ), width=12, md=4),

        dbc.Col(create_chart_card(
            "Room3 曜日別稼働率",
            "Room3の曜日別詳細",
            placeholder_chart(200)
        ), width=12, md=4),
    ]),
])

# 競合分析タブ
competitors_tab = html.Div([
    # 競合施設料金比較
    create_chart_card(
        "競合施設 料金比較",
        "大阪市内の主なプライベートサウナ施設の料金比較（1時間あたり）",
        placeholder_chart(300)
    ),

    # 競合施設詳細比較
    create_chart_card(
        "競合施設詳細比較",
        "各施設の特徴比較",
        html.Div([
            dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("施設名"),
                        html.Th("所在地"),
                        html.Th("形態"),
                        html.Th("料金"),
                        html.Th("ルーム数"),
                        html.Th("水風呂"),
                        html.Th("男女混浴"),
                        html.Th("開業年"),
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(
                            html.Span(name, className="font-weight-bold text-primary")
                            if name == "HAAAVE.sauna" else name
                        ),
                        html.Td("---"),
                        html.Td("---"),
                        html.Td("---"),
                        html.Td("---"),
                        html.Td("---"),
                        html.Td("---"),
                        html.Td("---"),
                    ]) for name in dummy_data["labels"]["competitor_names"]
                ]),
            ], bordered=True, hover=True, responsive=True, striped=True)
        ])
    ),

    # 地域分布
    create_chart_card(
        "競合施設 地域分布",
        "大阪市内のエリア別サウナ施設数",
        placeholder_chart(200)
    ),
])

# 売上分析タブ
finance_tab = html.Div([
    # 売上統計カード
    dbc.Row([
        dbc.Col(create_card("直近月間売上", "¥---", "📊", COLORS["primary"]), width=12, md=4),
        dbc.Col(create_card("直近月間利益", "¥---", "📊", COLORS["success"]), width=12, md=4),
        dbc.Col(create_card("直近月間利益率", "---%", "📊", COLORS["accent1"]), width=12, md=4),
    ], className="mb-4"),

    # 月別売上・利益推移
    create_chart_card(
        "月別売上・利益推移",
        "売上と利益の月次推移",
        placeholder_chart(300)
    ),

    # 利用者タイプ別平均利用料金
    create_chart_card(
        "利用者タイプ別平均利用料金",
        "体験者・ビジター・会員の平均利用額",
        placeholder_chart(300)
    ),
])

# 月別詳細データモーダル
monthly_detail_modal = dbc.Modal([
    dbc.ModalHeader("--- 詳細データ"),
    dbc.ModalBody([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Room1 稼働率", className="text-muted small"),
                        html.P("---%", className="h3", style={"color": COLORS["room1"]}),
                    ])
                ], className="bg-light"),
            ], width=12, md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Room2 稼働率", className="text-muted small"),
                        html.P("---%", className="h3", style={"color": COLORS["room2"]}),
                    ])
                ], className="bg-light"),
            ], width=12, md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Room3 稼働率", className="text-muted small"),
                        html.P("---%", className="h3", style={"color": COLORS["room3"]}),
                    ])
                ], className="bg-light"),
            ], width=12, md=4),
        ], className="mb-4"),

        html.H5("月間稼働率比較", className="mt-4 mb-3"),
        placeholder_chart(250),

        html.H5("売上データ", className="mt-4 mb-3"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.P("売上", className="text-muted small"),
                        html.P("¥---", className="h4 text-primary"),
                    ], width=12, md=4),
                    dbc.Col([
                        html.P("コスト", className="text-muted small"),
                        html.P("¥---", className="h4 text-danger"),
                    ], width=12, md=4),
                    dbc.Col([
                        html.P("利益", className="text-muted small"),
                        html.P("¥---", className="h4 text-success"),
                    ], width=12, md=4),
                ]),
            ])
        ], className="bg-light"),
    ]),
    dbc.ModalFooter(
        dbc.Button("閉じる", id="close-modal", className="ml-auto")
    ),
], id="monthly-detail-modal", size="lg")

# タブコンテンツをまとめる
tab_content = html.Div([
    overview_tab,
], id="tab-content", style={"marginLeft": "250px", "padding": "20px"})

# 全体レイアウト
app.layout = html.Div([
    dcc.Store(id="active-tab", data="overview"),
    sidebar,
    html.Div([
        header,
        tab_content,
    ]),
    monthly_detail_modal,
])

# コールバック：タブ切り替え
@app.callback(
    Output("tab-content", "children"),
    Output("active-tab", "data"),
    [
        Input("nav-概要", "n_clicks"),
        Input("nav-会員分析", "n_clicks"),
        Input("nav-ルーム稼働率", "n_clicks"),
        Input("nav-曜日・時間分析", "n_clicks"),
        Input("nav-競合分析", "n_clicks"),
        Input("nav-売上分析", "n_clicks"),
    ],
    State("active-tab", "data"),
)
def switch_tab(overview, members, utilization, daytime, competitors, finance, current):
    ctx = dash.callback_context
    if not ctx.triggered:
        return overview_tab, "overview"
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "nav-概要":
            return overview_tab, "overview"
        elif button_id == "nav-会員分析":
            return members_tab, "members"
        elif button_id == "nav-ルーム稼働率":
            return utilization_tab, "utilization"
        elif button_id == "nav-曜日・時間分析":
            return daytime_tab, "daytime"
        elif button_id == "nav-競合分析":
            return competitors_tab, "competitors"
        elif button_id == "nav-売上分析":
            return finance_tab, "finance"
        return overview_tab, "overview"

# コールバック：モーダル操作
@app.callback(
    Output("monthly-detail-modal", "is_open"),
    [
        Input("detail-btn-0", "n_clicks"),
        Input("close-modal", "n_clicks"),
    ],
    State("monthly-detail-modal", "is_open"),
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# コールバック：サイドバートグル
@app.callback(
    Output("sidebar", "style"),
    Output("tab-content", "style"),
    Output("header", "style"),
    [Input("toggle-sidebar", "n_clicks")],
    [State("sidebar", "style")]
)
def toggle_sidebar(n_clicks, current_style):
    if n_clicks and n_clicks % 2 == 1:
        # サイドバー最小化
        return {"width": "60px", "height": "100vh", "position": "fixed"}, \
               {"marginLeft": "60px", "padding": "20px"}, \
               {"marginLeft": "60px"}
    # サイドバー通常表示
    return {"width": "250px", "height": "100vh", "position": "fixed"}, \
           {"marginLeft": "250px", "padding": "20px"}, \
           {"marginLeft": "250px"}

# アプリ起動
if __name__ == "__main__":
    app.run(debug=True)
