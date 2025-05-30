import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, HTMLResponse
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

# Render環境かどうかを確認
is_render = os.environ.get("RENDER", "").lower() == "true"

# 静的ファイルのディレクトリ
# Render環境では、ビルドされたフロントエンドがルートディレクトリになっている可能性がある
static_dir = "frontend/build" if not is_render else "build"

# Render環境でのディレクトリ検出を詳細化
if is_render:
    # 利用可能なパスを優先順で確認
    possible_paths = ["build", "static", "frontend/build", ".", "public"]
    found = False

    for path in possible_paths:
        if os.path.exists(path):
            print(f"ディレクトリが見つかりました: {path}")
            if os.path.exists(os.path.join(path, "index.html")):
                static_dir = path
                found = True
                print(f"index.htmlが見つかりました: {os.path.join(path, 'index.html')}")
                break
            else:
                # サブディレクトリも確認
                for subdir in os.listdir(path):
                    subpath = os.path.join(path, subdir)
                    if os.path.isdir(subpath) and os.path.exists(os.path.join(subpath, "index.html")):
                        static_dir = subpath
                        found = True
                        print(f"index.htmlが見つかりました: {os.path.join(subpath, 'index.html')}")
                        break
                if found:
                    break

    if not found:
        print("警告: index.htmlが見つかりませんでした")
        # リスト存在するディレクトリ内容
        print(f"現在のディレクトリ内容: {os.listdir('.')}")
        if os.path.exists('static'):
            print(f"static内のファイル: {os.listdir('static')}")

            # staticディレクトリに移動し、index.htmlを作成する
            if not os.path.exists(os.path.join('static', 'index.html')) and os.path.exists(os.path.join('frontend', 'build', 'index.html')):
                # frontendビルドからindex.htmlをコピー
                import shutil
                try:
                    shutil.copy(
                        os.path.join('frontend', 'build', 'index.html'),
                        os.path.join('static', 'index.html')
                    )
                    print("index.htmlをfrontend/buildからstaticにコピーしました")
                    static_dir = "static"
                except Exception as e:
                    print(f"index.htmlのコピーに失敗しました: {str(e)}")

# 静的ファイルが存在するか確認
if not os.path.exists(static_dir):
    print(f"警告: 静的ファイルディレクトリが見つかりません: {static_dir}")
    print(f"現在のディレクトリ: {os.getcwd()}")
    print(f"ディレクトリ内容: {os.listdir('.')}")
    if os.path.exists('frontend'):
        print(f"Frontendディレクトリ内容: {os.listdir('frontend')}")
        if os.path.exists('frontend/build'):
            print(f"Frontend buildディレクトリ内容: {os.listdir('frontend/build')}")

# Render環境でのデバッグ情報を追加
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")
if os.path.exists('static'):
    print(f"Static directory contents: {os.listdir('static')}")
if os.path.exists('frontend'):
    print(f"Frontend directory contents: {os.listdir('frontend')}")
    if os.path.exists('frontend/build'):
        print(f"Frontend build contents: {os.listdir('frontend/build')}")

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

# APIの全エンドポイントをサブパスにマウント
try:
    # ここでルートパスを空にリセット
    api.app.root_path = ""
    print("APIルートパスをリセットしました")
except Exception as e:
    print(f"APIルートパス設定エラー: {str(e)}")

# ファイルの存在を確認する関数
def check_file_exists(file_path):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return True
    print(f"ファイルが存在しません: {file_path}")
    return False

# ルートパスへのリクエストをindex.htmlにリダイレクト
@app.get("/", response_class=FileResponse)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    print(f"リクエスト: / -> {index_path}")

    if check_file_exists(index_path):
        print(f"ファイル配信: {index_path}")
        return FileResponse(index_path)
    else:
        # index.htmlが見つからない場合は、ファイル作成のためのロジックを追加
        fallback_paths = [
            os.path.join("frontend", "build", "index.html"),
            os.path.join("build", "index.html"),
            os.path.join("public", "index.html")
        ]

        for fallback_path in fallback_paths:
            if check_file_exists(fallback_path):
                print(f"フォールバックindex.htmlを使用: {fallback_path}")
                return FileResponse(fallback_path)

        # それでも見つからない場合は、簡易なHTMLを直接返す
        print("簡易HTMLを返します")
        html_content = """
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>サウナ分析ダッシュボード</title>
            <style>
                body { font-family: sans-serif; margin: 0; padding: 20px; }
                #root { max-width: 1200px; margin: 0 auto; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <div id="root">
                <h1>サウナ分析ダッシュボード</h1>
                <p>APIステータス:
                    <span id="api-status">確認中...</span>
                </p>
                <script>
                    fetch('/api/dashboard')
                        .then(response => {
                            document.getElementById('api-status').textContent =
                                response.ok ? '接続成功' : 'エラー: ' + response.status;
                            return response.json();
                        })
                        .then(data => {
                            console.log('API応答:', data);
                        })
                        .catch(err => {
                            document.getElementById('api-status').textContent = 'エラー: ' + err.message;
                            console.error('API接続エラー:', err);
                        });
                </script>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

# 静的ファイルを提供
@app.get("/{path:path}")
async def read_static(path: str, request: Request):
    print(f"リクエストパス: {path}")

    # 明示的に処理するパスのマッピング
    special_paths = {
        "manifest.json": {"content_type": "application/json", "paths": [
            os.path.join(static_dir, "manifest.json"),
            os.path.join("frontend", "build", "manifest.json"),
            os.path.join("public", "manifest.json")
        ]},
        "favicon.ico": {"content_type": "image/x-icon", "paths": [
            os.path.join(static_dir, "favicon.ico"),
            os.path.join("frontend", "build", "favicon.ico"),
            os.path.join("public", "favicon.ico")
        ]}
    }

    # 特別なパスの場合
    if path in special_paths:
        for try_path in special_paths[path]["paths"]:
            if check_file_exists(try_path):
                print(f"特別なパス配信: {try_path} ({special_paths[path]['content_type']})")
                return FileResponse(
                    try_path,
                    media_type=special_paths[path]["content_type"],
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
                        "Cache-Control": "no-cache, no-store, must-revalidate"
                    }
                )

    # APIパスはスキップしてAPIモジュールに転送
    if path.startswith("api/"):
        print(f"APIリクエスト転送: {path}")

        # 核心部分： api/dashboard のような形式は /api/dashboard に変換し、直接処理
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": request.method,
            "path": "/" + path,  # api/で始まるパスをそのまま使用（/api/xxxのまま）
            "root_path": "",  # ルートパスをクリア
            "scheme": request.url.scheme,
            "query_string": request.url.query.encode(),
            "headers": [(k.lower().encode(), v.encode()) for k, v in request.headers.items()],
            "client": request.scope.get("client", None),
            "server": request.scope.get("server", None),
        }
        print(f"read_static APIリクエスト転送: path={scope['path']}")

        # レスポンスの処理を制御するために、特殊なsend関数を作成
        async def send_wrapper(message):
            # Responseヘッダーにアクセスし、必要なCORSヘッダーを追加
            if message["type"] == "http.response.start":
                # ヘッダーを辞書に変換
                headers = {}
                for k, v in message.get("headers", []):
                    headers[k.lower()] = v

                # CORSヘッダーを追加
                headers[b"access-control-allow-origin"] = b"*"
                headers[b"access-control-allow-methods"] = b"GET, POST, PUT, DELETE, OPTIONS"
                headers[b"access-control-allow-headers"] = b"Content-Type, X-Requested-With"

                # Content-Typeがない場合は必ず追加
                if b"content-type" not in headers:
                    headers[b"content-type"] = b"application/json"

                # ヘッダーをリストに戻す
                message["headers"] = [(k, v) for k, v in headers.items()]

            # 元のsend関数に転送
            await request._send(message)

        # APIにリクエストを転送
        # apiモジュールのルートパスをクリアして直接アクセスできるようにする
        saved_root_path = getattr(api.app, "root_path", "")
        api.app.root_path = ""

        # APIアプリケーションを呼び出す
        await api.app(scope, request._receive, send_wrapper)

        # ルートパスを元に戻す
        api.app.root_path = saved_root_path

        return None

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
        return FileResponse(
            file_path,
            media_type=content_type,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
            }
        )

    # 静的アセットとして明確なパスをチェック
    asset_paths = [
        os.path.join(static_dir, "static", "js", path),
        os.path.join(static_dir, "static", "css", path),
        os.path.join(static_dir, "static", "media", path),
        os.path.join("frontend", "build", path),
        os.path.join("frontend", "build", "static", "js", path),
        os.path.join("frontend", "build", "static", "css", path)
    ]

    for asset_path in asset_paths:
        if check_file_exists(asset_path):
            print(f"アセット配信: {asset_path}")
            return FileResponse(
                asset_path,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
                }
            )

    # ファイルが存在しない場合はindex.htmlを返す（SPA対応）
    index_path = os.path.join(static_dir, "index.html")
    if check_file_exists(index_path):
        print(f"SPA対応: {path} → index.html")
        return FileResponse(
            index_path,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
            }
        )

    # それでもダメなら404
    error_message = f"ファイルが見つかりません: {path}"
    print(error_message)
    return JSONResponse({"error": error_message}, status_code=404)

# APIエンドポイントを直接処理 - 各HTTPメソッド別に定義
@app.get("/api/{path:path}")
async def api_endpoint_get(request: Request, path: str):
    return await handle_api_request(request, path)

@app.post("/api/{path:path}")
async def api_endpoint_post(request: Request, path: str):
    return await handle_api_request(request, path)

@app.put("/api/{path:path}")
async def api_endpoint_put(request: Request, path: str):
    return await handle_api_request(request, path)

@app.delete("/api/{path:path}")
async def api_endpoint_delete(request: Request, path: str):
    return await handle_api_request(request, path)

@app.options("/api/{path:path}")
async def api_endpoint_options(request: Request, path: str):
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

@app.head("/api/{path:path}")
async def api_endpoint_head(request: Request, path: str):
    return await handle_api_request(request, path)

@app.patch("/api/{path:path}")
async def api_endpoint_patch(request: Request, path: str):
    return await handle_api_request(request, path)

# 共通のAPI処理関数
async def handle_api_request(request: Request, path: str):
    print(f"API直接リクエスト: {path}, メソッド: {request.method}")
    print(f"リクエストヘッダー: {request.headers}")
    print(f"リクエストクエリパラメータ: {request.query_params}")

    try:
        # マルチパートデータの場合、新しいScopeベースのアプローチは使用しない
        content_type = request.headers.get("content-type", "")
        print(f"リクエストContent-Type: {content_type}")
        is_multipart = content_type.startswith("multipart/form-data")

        if is_multipart:
            print("マルチパートフォームデータ検出 - 専用処理を使用")

            # リクエスト本文を読み込む
            body = await request.body()
            print(f"リクエスト本文サイズ: {len(body)} バイト")

            # 新しいスコープを作成
            new_scope = request.scope.copy()

            # APIエンドポイントはすでに/api/で始まるように定義されているため
            # 例: POSTリクエスト /api/upload-csv -> /api/upload-csv
            # このとき、path="upload-csv" (api/プレフィックスが処理されてパス部分だけ渡される)
            api_path = "/api/" + path
            print(f"APIパス (変換後): {api_path}")

            # 適切なパスを設定
            new_scope["path"] = api_path
            print(f"新しいスコープパス: {new_scope['path']}")
            # ルートパスを空に設定
            new_scope["root_path"] = ""
            # クエリパラメータの設定
            new_scope["query_string"] = request.url.query.encode()

            # すべてのヘッダーをコピー
            new_scope["headers"] = [(k.lower().encode(), v.encode()) for k, v in request.headers.items()]

            # 修正方法: ASGI applicationを直接呼び出し
            # 新しいreceiveとsend関数を定義
            body_set = False

            async def modified_receive():
                nonlocal body_set
                if not body_set:
                    body_set = True
                    return {
                        "type": "http.request",
                        "body": body,
                        "more_body": False
                    }
                return await request._receive()

            response_started = False
            response_body = b""
            response_status = 200
            response_headers = []

            async def modified_send(message):
                nonlocal response_started, response_body, response_status, response_headers

                if message["type"] == "http.response.start":
                    response_started = True
                    response_status = message.get("status", 200)
                    response_headers = message.get("headers", [])
                    print(f"レスポンスヘッダー: {response_headers}")

                elif message["type"] == "http.response.body":
                    response_body += message.get("body", b"")
                    print(f"レスポンスボディサイズ: {len(response_body)} バイト")

            # APIアプリケーションを呼び出す
            print(f"APIアプリケーション呼び出し前 (修正方法): {path}, root_path={new_scope.get('root_path', 'なし')}")
            try:
                # apiモジュールのルートパスをクリアして直接アクセスできるようにする
                saved_root_path = getattr(api.app, "root_path", "")
                api.app.root_path = ""

                # APIアプリケーションを呼び出す
                await api.app(new_scope, modified_receive, modified_send)

                # ルートパスを元に戻す
                api.app.root_path = saved_root_path

                print(f"API呼び出し完了: ステータス={response_status}")
            except Exception as e:
                print(f"APIアプリケーション呼び出しエラー: {str(e)}")
                import traceback
                print(f"スタックトレース: {traceback.format_exc()}")
                raise

            # レスポンスにCORS情報を追加
            headers = {}
            for k, v in response_headers:
                headers[k.decode('utf-8').lower()] = v.decode('utf-8')

            headers["Access-Control-Allow-Origin"] = "*"

            # レスポンスのContent-Typeがない場合は追加（必ず設定）
            if "content-type" not in headers:
                headers["Content-Type"] = "application/json"

            # 新しいレスポンスを返す
            from starlette.responses import Response
            return Response(
                content=response_body,
                status_code=response_status,
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
                "path": "/api/" + path,  # /api/xxx形式に変換
                "root_path": "",  # ルートパスをクリア
                "scheme": request.url.scheme,
                "query_string": request.url.query.encode(),
                "headers": [(k.lower().encode(), v.encode()) for k, v in request.headers.items()],
                "client": request.scope.get("client", None),
                "server": request.scope.get("server", None),
            }
            print(f"作成したスコープ: path={scope['path']}")

            # レスポンスの処理を制御するために、特殊なsend関数を作成
            async def send_wrapper(message):
                print(f"send_wrapper呼び出し: メッセージタイプ={message.get('type')}")
                # Responseヘッダーにアクセスし、必要なCORSヘッダーを追加
                if message["type"] == "http.response.start":
                    # ヘッダーを辞書に変換
                    headers = {}
                    for k, v in message.get("headers", []):
                        headers[k.lower()] = v

                    # CORSヘッダーを追加
                    headers[b"access-control-allow-origin"] = b"*"

                    # Content-Typeがない場合は必ず追加
                    if b"content-type" not in headers:
                        headers[b"content-type"] = b"application/json"

                    # ヘッダーをリストに戻す
                    message["headers"] = [(k, v) for k, v in headers.items()]
                    print(f"修正後のヘッダー: {message['headers']}")

                # 元のsend関数に転送
                await request._send(message)
                print(f"元のsend関数呼び出し完了: {message.get('type')}")

            # APIにリクエストを転送
            print(f"APIアプリ呼び出し開始: path=/{path}, method={request.method}")
            try:
                # apiモジュールのルートパスをクリアして直接アクセスできるようにする
                saved_root_path = getattr(api.app, "root_path", "")
                api.app.root_path = ""

                # APIアプリケーションを呼び出す
                await api.app(scope, request._receive, send_wrapper)

                # ルートパスを元に戻す
                api.app.root_path = saved_root_path

                print(f"APIアプリ呼び出し完了: path=/{path}")
            except Exception as e:
                print(f"APIアプリ呼び出しエラー: {str(e)}")
                import traceback
                print(f"スタックトレース: {traceback.format_exc()}")
                raise

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

# メイン関数
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    print(f"\n{'='*50}")
    print(f"サーバー起動情報:")
    print(f"ポート: {port}")
    print(f"静的ファイルディレクトリ: {os.path.abspath(static_dir)}")
    print(f"Render環境: {is_render}")
    print(f"{'='*50}\n")

    uvicorn.run(app, host="0.0.0.0", port=port)
