// CSVアップロード処理用のJavaScript

document.addEventListener('DOMContentLoaded', function() {
  // 要素の取得
  const uploadForm = document.getElementById('upload-form');
  const fileInput = document.getElementById('csv-file');
  const dataTypeSelect = document.getElementById('data-type');
  const uploadButton = document.getElementById('upload-button');
  const cancelButton = document.getElementById('cancel-button');
  const selectedFilename = document.getElementById('selected-filename');
  const uploadError = document.getElementById('upload-error');
  const uploadProgress = document.getElementById('upload-progress');

  // フォームがない場合は処理を中止
  if (!uploadForm) return;

  // ファイル選択時の処理
  fileInput.addEventListener('change', function() {
    if (fileInput.files.length > 0) {
      const filename = fileInput.files[0].name;
      selectedFilename.textContent = filename;
      uploadError.textContent = '';

      // ファイル名からデータタイプを自動判定
      if (filename.toLowerCase().includes('frame') || filename.toLowerCase().includes('occupancy')) {
        dataTypeSelect.value = 'occupancy';
      } else if (filename.toLowerCase().includes('sales')) {
        dataTypeSelect.value = 'sales';
      } else if (filename.toLowerCase().includes('member')) {
        dataTypeSelect.value = 'member';
      } else if (filename.toLowerCase().includes('reservation')) {
        dataTypeSelect.value = 'reservation';
      } else {
        dataTypeSelect.value = 'auto';
      }
    } else {
      selectedFilename.textContent = 'なし';
    }
  });

  // キャンセルボタン処理
  cancelButton.addEventListener('click', function() {
    fileInput.value = '';
    selectedFilename.textContent = 'なし';
    uploadError.textContent = '';
    dataTypeSelect.value = 'auto';
    if (uploadProgress) uploadProgress.style.width = '0%';
  });

  // フォーム送信処理
  uploadForm.addEventListener('submit', function(event) {
    event.preventDefault();

    if (!fileInput.files.length) {
      uploadError.textContent = 'ファイルを選択してください';
      return;
    }

    // FormDataオブジェクトを作成
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('data_type', dataTypeSelect.value);

    // ボタンを無効化
    uploadButton.disabled = true;
    uploadButton.textContent = 'アップロード中...';
    if (uploadProgress) uploadProgress.style.width = '0%';

    // アップロード実行
    uploadCSV(formData);
  });

  // CSVアップロード処理
  function uploadCSV(formData) {
    // エラーログ用
    console.log('アップロード開始:', {
      file: formData.get('file').name,
      type: formData.get('data_type')
    });

    // シンプルテスト実行によるチェック（先に実行）
    fetch('/api/test-upload')
      .then(response => {
        console.log('テストAPI応答ステータス:', response.status);
        if (!response.ok) {
          console.warn('テストAPIの応答が正常ではありません');
        }
        return response.json().catch(e => {
          console.error('テストAPIのJSON解析エラー:', e);
          return { status: 'エラー', detail: 'テストAPIレスポンスのJSONパースに失敗しました' };
        });
      })
      .then(data => {
        console.log('テストAPI応答:', data);
      })
      .catch(error => {
        console.error('テストAPI呼び出しエラー:', error);
      })
      .finally(() => {
        // 本番のアップロードを実行
        performActualUpload(formData);
      });
  }

  // 実際のアップロード処理
  function performActualUpload(formData) {
    fetch('/api/upload-csv', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      console.log('アップロードAPIの応答ステータス:', response.status);
      console.log('アップロードAPIのContent-Type:', response.headers.get('Content-Type'));

      // レスポンスがJSONでなければエラーを投げる
      const contentType = response.headers.get('Content-Type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error(`JSONレスポンスではありません (Content-Type: ${contentType})`);
      }

      return response.json().catch(e => {
        console.error('JSON解析エラー:', e);
        throw new Error('レスポンスのJSONパースに失敗しました');
      });
    })
    .then(data => {
      console.log('アップロード成功:', data);

      // 成功メッセージ表示
      alert('ファイルが正常にアップロードされました');

      // フォームリセット
      uploadForm.reset();
      selectedFilename.textContent = 'なし';
      uploadError.textContent = '';
      if (uploadProgress) uploadProgress.style.width = '100%';
    })
    .catch(error => {
      console.error('アップロードエラー:', error);

      // エラーメッセージ表示
      uploadError.textContent = error.message || 'アップロード中にエラーが発生しました';
      if (uploadProgress) uploadProgress.style.width = '0%';

      // 簡易アップロードへのフォールバック提案
      if (confirm('標準アップロードに失敗しました。シンプルモードで再試行しますか？')) {
        useSimpleUpload(formData.get('file'));
      }
    })
    .finally(() => {
      // ボタン復活
      uploadButton.disabled = false;
      uploadButton.textContent = 'アップロード';
    });
  }

  // シンプルアップロード（フォールバック用）
  function useSimpleUpload(file) {
    const simpleFormData = new FormData();
    simpleFormData.append('file', file);

    fetch('/api/simple-upload', {
      method: 'POST',
      body: simpleFormData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('シンプルアップロードに失敗しました');
      }
      return response.json();
    })
    .then(data => {
      console.log('シンプルアップロード成功:', data);
      alert('シンプルモードでファイルがアップロードされました');

      // フォームリセット
      uploadForm.reset();
      selectedFilename.textContent = 'なし';
      uploadError.textContent = '';
    })
    .catch(error => {
      console.error('シンプルアップロードエラー:', error);
      uploadError.textContent = 'すべてのアップロード方法が失敗しました: ' + error.message;
    });
  }
});
