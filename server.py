import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
import api  # 既存のAPIモジュールをインポート

# Streamlitコマンドの検出（--server.portなどの引数がある場合）
if any('--server.port' in arg for arg in sys.argv):
    print("Streamlitコマンドを検出しました。Streamlitを実行します。")
    try:
        import streamlit.web.cli as stcli
        sys.argv[0] = 'streamlit'
        sys.exit(stcli.main())
    except ImportError:
        print("Streamlitが見つかりません。通常のサーバーを起動します。")

# 環境変数からポート番号を取得
PORT = int(os.environ.get("PORT", 8000))

# 新しいFastAPIアプリを作成
app = FastAPI()

# CORSミドルウェアを追加（すべてのオリジンを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# APIのCORS設定も更新
api.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# Render環境かどうかを確認
is_render = os.environ.get("RENDER", "").lower() == "true"

# 静的ファイルのディレクトリ
# Render環境では、ビルドされたフロントエンドがルートディレクトリになっている可能性がある
static_dir = "frontend/build" if not is_render else "build"
if is_render and not os.path.exists(static_dir):
    static_dir = "frontend/build"  # フォールバック
    if not os.path.exists(static_dir):
        static_dir = "."  # 最終フォールバック

# 静的ファイルが存在するか確認
if not os.path.exists(static_dir):
    print(f"警告: 静的ファイルディレクトリが見つかりません: {static_dir}")
    print(f"現在のディレクトリ: {os.getcwd()}")
    print(f"ディレクトリ内容: {os.listdir('.')}")
    if os.path.exists('frontend'):
        print(f"Frontendディレクトリ内容: {os.listdir('frontend')}")

# APIの全エンドポイントをサブパスにマウント
try:
    api.app.root_path = "/api"
    print("APIルートパスを設定しました")
except Exception as e:
    print(f"APIルートパス設定エラー: {str(e)}")

# ファイルの存在を確認する関数
def check_file_exists(file_path):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return True
    print(f"ファイルが存在しません: {file_path}")
    return False

# ルートパスへのリクエストをindex.htmlにリダイレクト
@app.get("/")
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if check_file_exists(index_path):
        return FileResponse(index_path)
    else:
        error_message = f"index.htmlが見つかりません。パス: {index_path}, ディレクトリ内容: {os.listdir(static_dir) if os.path.exists(static_dir) else '不明'}"
        print(error_message)
        return JSONResponse({"error": error_message}, status_code=404)

# 静的ファイルを提供
@app.get("/{path:path}")
async def read_static(path: str, request: Request):
    print(f"リクエストパス: {path}")

    # APIパスはスキップしてAPIモジュールに転送
    if path.startswith("api/"):
        print(f"APIリクエスト転送: {path}")
        return await api.app(Request(scope={"type": "http", "path": path[4:], "method": request.method}))

    # 静的ファイルのパスを構築
    file_path = os.path.join(static_dir, path)

    # ファイル拡張子に基づいてMIMEタイプを設定
    content_type = None
    if path.endswith('.js'):
        content_type = 'application/javascript'
    elif path.endswith('.css'):
        content_type = 'text/css'
    elif path.endswith('.html'):
        content_type = 'text/html'
    elif path.endswith('.json'):
        content_type = 'application/json'
    elif path.endswith('.png'):
        content_type = 'image/png'
    elif path.endswith('.jpg') or path.endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif path.endswith('.svg'):
        content_type = 'image/svg+xml'
    elif path.endswith('.ico'):
        content_type = 'image/x-icon'

    # ファイルが存在するか確認
    if check_file_exists(file_path):
        print(f"ファイル配信: {file_path} (Content-Type: {content_type})")
        return FileResponse(file_path, media_type=content_type)

    # 静的アセットとして明確なパスをチェック
    asset_paths = [
        os.path.join(static_dir, "static", "js", path),
        os.path.join(static_dir, "static", "css", path),
        os.path.join(static_dir, "static", "media", path)
    ]

    for asset_path in asset_paths:
        if check_file_exists(asset_path):
            print(f"アセット配信: {asset_path}")
            return FileResponse(asset_path, media_type=content_type)

    # ファイルが存在しない場合はindex.htmlを返す（SPA対応）
    index_path = os.path.join(static_dir, "index.html")
    if check_file_exists(index_path):
        print(f"SPA対応: {path} → index.html")
        return FileResponse(index_path)

    # それでもダメなら404
    error_message = f"ファイルが見つかりません: {path}"
    print(error_message)
    return JSONResponse({"error": error_message}, status_code=404)

# APIエンドポイントを直接処理
@app.route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def api_endpoint(request: Request, path: str):
    print(f"API直接リクエスト: {path}, メソッド: {request.method}")

    # OPTIONSリクエストの場合、CORSヘッダーを直接返す
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            content={"allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
                "Content-Type": "application/json"
            }
        )

    try:
        # マルチパートデータの場合、新しいScopeベースのアプローチは使用しない
        content_type = request.headers.get("content-type", "")
        print(f"リクエストContent-Type: {content_type}")
        is_multipart = content_type.startswith("multipart/form-data")

        if is_multipart:
            print("マルチパートフォームデータ検出 - 専用処理を使用")

            # リクエスト本文を読み込む
            body = await request.body()

            # マルチパートリクエスト用の特別な処理
            # 通常のScopeベース転送では適切に処理できないため
            from starlette.requests import Request as StarletteRequest

            # 新しいスコープを作成
            new_scope = request.scope.copy()
            new_scope["path"] = "/" + path

            # 新しいリクエストを作成
            new_request = StarletteRequest(
                scope=new_scope,
                receive=request._receive,
                send=request._send
            )

            # リクエスト本文をセット
            setattr(new_request, "_body", body)

            # APIにリクエストを転送
            res = await api.app(new_request)

            # レスポンスにCORS情報を追加
            headers = dict(res.headers)
            headers["Access-Control-Allow-Origin"] = "*"

            # レスポンスのContent-Typeがない場合は追加
            if "content-type" not in [h.lower() for h in headers]:
                headers["Content-Type"] = "application/json"

            # 新しいレスポンスを返す
            from starlette.responses import Response
            return Response(
                content=res.body,
                status_code=res.status_code,
                headers=headers
            )
        else:
            # 通常のリクエスト処理（Scopeベース）
            print(f"通常のリクエスト - Scopeベースの転送を使用: パス=/{path}")

            # 新しいスコープを作成
            scope = {
                "type": "http",
                "http_version": "1.1",
                "method": request.method,
                "path": "/" + path,
                "root_path": "",
                "scheme": request.url.scheme,
                "query_string": request.url.query.encode(),
                "headers": [(k.lower().encode(), v.encode()) for k, v in request.headers.items()],
                "client": request.scope.get("client", None),
                "server": request.scope.get("server", None),
            }

            # レスポンスの処理を制御するために、特殊なsend関数を作成
            async def send_wrapper(message):
                # Responseヘッダーにアクセスし、必要なCORSヘッダーを追加
                if message["type"] == "http.response.start":
                    # ヘッダーを辞書に変換
                    headers = dict(message.get("headers", []))
                    # CORSヘッダーを追加
                    headers[b"access-control-allow-origin"] = b"*"
                    # Content-Typeがない場合は追加
                    if b"content-type" not in headers:
                        headers[b"content-type"] = b"application/json"
                    # ヘッダーをリストに戻す
                    message["headers"] = [(k, v) for k, v in headers.items()]

                # 元のsend関数に転送
                await request._send(message)

            # APIにリクエストを転送
            await api.app(scope, request._receive, send_wrapper)

            # 処理は完了しているので、None を返す
            return None

    except Exception as e:
        print(f"APIエラー: {str(e)}")
        import traceback
        trace = traceback.format_exc()
        print(f"詳細トレース: {trace}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "エラー",
                "detail": f"リクエスト処理中にエラーが発生しました: {str(e)}",
                "path": path,
                "method": request.method
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            }
        )

# 健全性チェック
@app.get("/health")
async def health_check():
    return {"status": "ok", "env": os.environ.get("PYTHON_ENV", "development")}

if __name__ == "__main__":
    # サーバー起動
    print(f"Starting server on port {PORT} with static dir: {os.path.abspath(static_dir)}")
    # Renderデプロイ情報
    if is_render:
        print(f"Render環境で実行中: {os.environ.get('RENDER_SERVICE_ID', '不明')}")
        print(f"ディレクトリ構造: {os.listdir('.')}")

    uvicorn.run("server:app", host="0.0.0.0", port=PORT)
