// シンプルなCSVアップロード処理用JavaScript
document.addEventListener('DOMContentLoaded', function() {
  // 要素の取得
  const uploadForm = document.getElementById('upload-form');
  const fileInput = document.getElementById('csv-file');
  const dataTypeSelect = document.getElementById('data-type');
  const uploadButton = document.getElementById('upload-button');
  const cancelButton = document.getElementById('cancel-button');
  const selectedFilename = document.getElementById('selected-filename');
  const uploadError = document.getElementById('upload-error');

  // フォームがない場合は終了
  if (!uploadForm) return;

  // ファイル選択時の処理
  fileInput.addEventListener('change', function() {
    if (fileInput.files.length > 0) {
      if (fileInput.files.length === 1) {
        selectedFilename.textContent = fileInput.files[0].name;
      } else {
        selectedFilename.textContent = `${fileInput.files.length}個のファイルが選択されました`;
      }
      uploadError.textContent = '';
    } else {
      selectedFilename.textContent = 'なし';
    }
  });

  // キャンセルボタン処理
  cancelButton.addEventListener('click', function() {
    fileInput.value = '';
    selectedFilename.textContent = 'なし';
    uploadError.textContent = '';
  });

  // フォーム送信処理
  uploadForm.addEventListener('submit', function(event) {
    event.preventDefault();

    if (!fileInput.files.length) {
      uploadError.textContent = 'ファイルを選択してください';
      return;
    }

    // ボタン無効化
    uploadButton.disabled = true;
    uploadButton.textContent = 'アップロード中...';

    // 複数ファイルか単一ファイルかで処理を分岐
    if (fileInput.files.length > 1) {
      // FormDataの作成
      const formData = new FormData();
      for (let i = 0; i < fileInput.files.length; i++) {
        formData.append('files', fileInput.files[i]);
      }
      formData.append('data_type', dataTypeSelect.value);

      // 直接アップロード
      fetchWithRetry('/api/upload-multiple', {
        method: 'POST',
        body: formData
      })
      .then(data => {
        console.log('複数アップロード成功:', data);
        alert(`${data.total}個中${data.success}個のファイルが正常にアップロードされました`);
        uploadForm.reset();
        selectedFilename.textContent = 'なし';
      })
      .catch(error => {
        console.error('アップロードエラー:', error);
        uploadError.textContent = error.message || 'アップロード中にエラーが発生しました';
      })
      .finally(() => {
        uploadButton.disabled = false;
        uploadButton.textContent = 'アップロード';
      });
    } else {
      // 単一ファイルのアップロード
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('data_type', dataTypeSelect.value);

      // 直接アップロード
      fetchWithRetry('/api/upload', {
        method: 'POST',
        body: formData
      })
      .then(data => {
        console.log('アップロード成功:', data);
        alert(`ファイル「${data.filename}」が正常にアップロードされました`);
        uploadForm.reset();
        selectedFilename.textContent = 'なし';
      })
      .catch(error => {
        console.error('アップロードエラー:', error);
        uploadError.textContent = error.message || 'アップロード中にエラーが発生しました';
      })
      .finally(() => {
        uploadButton.disabled = false;
        uploadButton.textContent = 'アップロード';
      });
    }
  });

  // リトライ機能付きのfetch
  function fetchWithRetry(url, options, retries = 3, delay = 1000) {
    return new Promise((resolve, reject) => {
      // 実際のフェッチ処理
      function attempt(attemptsLeft) {
        fetch(url, options)
          .then(response => {
            // レスポンスのContent-Typeを確認
            const contentType = response.headers.get('Content-Type');

            // エラーチェック
            if (!response.ok) {
              return response.text().then(text => {
                console.error(`エラーレスポンス (${response.status}):`, text);
                try {
                  // JSONパースを試みる
                  return JSON.parse(text);
                } catch (e) {
                  // JSONパースに失敗した場合
                  throw new Error(`サーバーエラー (${response.status}): ${text.substring(0, 100)}...`);
                }
              });
            }

            // JSONチェック
            if (!contentType || !contentType.includes('application/json')) {
              throw new Error(`予期しないContent-Type: ${contentType}`);
            }

            // JSONレスポンスを取得
            return response.json();
          })
          .then(data => {
            // 成功
            resolve(data);
          })
          .catch(error => {
            console.error(`試行 ${4 - attemptsLeft}/${retries} 失敗:`, error);

            // リトライ回数を確認
            if (attemptsLeft > 1) {
              // 次のリトライまで待機
              setTimeout(() => attempt(attemptsLeft - 1), delay);
            } else {
              // リトライ回数超過
              reject(error);
            }
          });
      }

      // 最初の試行
      attempt(retries);
    });
  }
});
