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
      // 複数ファイル対応
      if (fileInput.files.length === 1) {
        const filename = fileInput.files[0].name;
        selectedFilename.textContent = filename;
      } else {
        selectedFilename.textContent = `${fileInput.files.length}個のファイルが選択されました`;
      }

      uploadError.textContent = '';

      // 最初のファイル名からデータタイプを自動判定
      const firstFileName = fileInput.files[0].name.toLowerCase();
      if (firstFileName.includes('frame') || firstFileName.includes('occupancy')) {
        dataTypeSelect.value = 'occupancy';
      } else if (firstFileName.includes('sales')) {
        dataTypeSelect.value = 'sales';
      } else if (firstFileName.includes('member')) {
        dataTypeSelect.value = 'member';
      } else if (firstFileName.includes('reservation')) {
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

    // ボタンを無効化
    uploadButton.disabled = true;
    uploadButton.textContent = 'アップロード中...';
    if (uploadProgress) uploadProgress.style.width = '0%';

    // 複数ファイルか単一ファイルかで処理を分岐
    if (fileInput.files.length > 1) {
      uploadMultipleFiles(fileInput.files, dataTypeSelect.value);
    } else {
      uploadSingleFile(fileInput.files[0], dataTypeSelect.value);
    }
  });

  // 単一ファイルアップロード処理
  function uploadSingleFile(file, dataType) {
    console.log('単一ファイルアップロード開始:', {file: file.name, type: dataType});

    // FormDataオブジェクトを作成
    const formData = new FormData();
    formData.append('file', file);
    formData.append('data_type', dataType);

    // アップロード実行
    fetch('/api/upload-csv', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      console.log('アップロードAPI応答:', response.status, response.statusText);
      console.log('レスポンスヘッダ:', response.headers.get('Content-Type'));

      if (!response.ok) {
        return response.text().then(text => {
          console.error('エラーレスポンス本文:', text);
          try {
            // JSONとしてパースを試みる
            return JSON.parse(text);
          } catch (e) {
            // JSONパースに失敗した場合
            throw new Error(`サーバーエラー (${response.status}): ${text}`);
          }
        });
      }

      return response.json().catch(e => {
        console.error('JSONパースエラー:', e);
        throw new Error('レスポンスのJSONパースに失敗しました');
      });
    })
    .then(data => {
      console.log('アップロード成功:', data);

      // 成功メッセージ表示
      alert(`ファイル「${file.name}」が正常にアップロードされました`);

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

      // シンプルアップロードへのフォールバック
      if (confirm('標準アップロードに失敗しました。シンプルモードで再試行しますか？')) {
        useSimpleUpload(file);
      }
    })
    .finally(() => {
      // ボタン復活
      uploadButton.disabled = false;
      uploadButton.textContent = 'アップロード';
    });
  }

  // 複数ファイルアップロード処理
  function uploadMultipleFiles(files, dataType) {
    console.log('複数ファイルアップロード開始:', {filesCount: files.length, type: dataType});

    // FormDataオブジェクトを作成
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    formData.append('data_type', dataType);

    // アップロード実行
    fetch('/api/upload-multiple-csv', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      console.log('複数アップロードAPI応答:', response.status, response.statusText);

      if (!response.ok) {
        return response.text().then(text => {
          console.error('エラーレスポンス本文:', text);
          try {
            // JSONとしてパースを試みる
            return JSON.parse(text);
          } catch (e) {
            // JSONパースに失敗した場合
            throw new Error(`サーバーエラー (${response.status}): ${text}`);
          }
        });
      }

      return response.json().catch(e => {
        console.error('JSONパースエラー:', e);
        throw new Error('レスポンスのJSONパースに失敗しました');
      });
    })
    .then(data => {
      console.log('複数アップロード成功:', data);

      // 成功/失敗の件数を表示
      let message = `${data.total}個中${data.success}個のファイルが正常にアップロードされました`;
      if (data.errors > 0) {
        message += `\n${data.errors}個のファイルでエラーが発生しました`;
      }
      alert(message);

      // フォームリセット
      uploadForm.reset();
      selectedFilename.textContent = 'なし';
      uploadError.textContent = '';
      if (uploadProgress) uploadProgress.style.width = '100%';

      // エラーがあった場合は表示
      if (data.errors > 0 && data.error_details) {
        const errorMessages = data.error_details.map(e => `${e.filename}: ${e.detail}`).join('\n');
        uploadError.textContent = `一部のファイルでエラーが発生: ${errorMessages}`;
      }
    })
    .catch(error => {
      console.error('複数アップロードエラー:', error);

      // エラーメッセージ表示
      uploadError.textContent = error.message || '複数ファイルのアップロード中にエラーが発生しました';
      if (uploadProgress) uploadProgress.style.width = '0%';

      // シンプルアップロードへのフォールバック
      if (confirm('標準アップロードに失敗しました。シンプルモードで再試行しますか？')) {
        useSimpleUploadMultiple(files);
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
      alert(`シンプルモードでファイル「${file.name}」がアップロードされました`);

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

  // 複数ファイルのシンプルアップロード
  function useSimpleUploadMultiple(files) {
    const simpleFormData = new FormData();
    for (let i = 0; i < files.length; i++) {
      simpleFormData.append('files', files[i]);
    }

    fetch('/api/simple-upload-multiple', {
      method: 'POST',
      body: simpleFormData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('複数ファイルのシンプルアップロードに失敗しました');
      }
      return response.json();
    })
    .then(data => {
      console.log('複数シンプルアップロード成功:', data);
      alert(`シンプルモードで${data.total}個のファイルがアップロードされました`);

      // フォームリセット
      uploadForm.reset();
      selectedFilename.textContent = 'なし';
      uploadError.textContent = '';
    })
    .catch(error => {
      console.error('複数シンプルアップロードエラー:', error);
      uploadError.textContent = 'すべてのアップロード方法が失敗しました: ' + error.message;
    });
  }
});
