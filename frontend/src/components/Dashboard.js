import React, { useState, useEffect } from 'react';
import { Activity, Users, Calendar, Target, BarChart2, TrendingUp, Download, Filter, RefreshCw, Menu, ChevronDown, Upload, DollarSign, Percent, PieChart } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

// カラーパレット
const COLORS = {
  primary: '#6979F8',
  secondary: '#BE52F2',
  accent1: '#00C6FF',
  accent2: '#FF5EDF',
  light: '#F7F8FC',
  white: '#FFFFFF',
  dark: '#121438',
  gray: '#E2E8F0',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  room1: '#6979F8',
  room2: '#BE52F2',
  room3: '#FF5EDF',
  male: '#6979F8',
  female: '#FF5EDF',
};

// PIEチャート用の色配列
const PIE_COLORS = [
  COLORS.primary,
  COLORS.secondary,
  COLORS.accent1,
  COLORS.accent2,
  COLORS.success,
  COLORS.warning
];

// APIのベースURL - 環境変数から取得するように修正
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

// APIパス
const API_PATHS = {
  dashboard: `/api/dashboard`,
  upload: `/api/upload-csv`
};

// レスポンシブカードコンポーネント
const Card = ({ title, value, subValue, icon, color = COLORS.primary, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-gray-500 text-sm">{title}</p>
          <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
          {subValue && <p className="text-sm text-gray-500 mt-1">{subValue}</p>}
        </div>
        <div className="p-2 rounded-full" style={{ backgroundColor: `${color}20` }}>
          {icon}
        </div>
      </div>
    </div>
  );
};

// チャートカードコンポーネント
const ChartCard = ({ title, subtitle, children, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
      <div className="mb-4">
        <h3 className="font-medium text-gray-800">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
};

// カスタムツールチップコンポーネント
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 shadow-md rounded-lg">
        <p className="font-medium text-gray-900">{`${label}`}</p>
        {payload.map((entry, index) => (
          <p key={`item-${index}`} className="text-sm" style={{ color: entry.color }}>
            {`${entry.name}: ${entry.value}${entry.unit || (entry.name === '稼働率' ? '%' : '')}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// サイドバーのナビゲーション項目
const NavItem = ({ icon, label, active, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center p-3 rounded-lg mb-2 transition-colors ${
        active
          ? 'bg-blue-50 text-blue-600'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      }`}
    >
      <span className="mr-3">{icon}</span>
      <span>{label}</span>
    </button>
  );
};

// CSVアップロードコンポーネント
const CSVUploader = ({ onUploadSuccess }) => {
  const [files, setFiles] = useState([]);
  const [dataType, setDataType] = useState('utilization');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [showUploader, setShowUploader] = useState(false);
  const [showButtons, setShowButtons] = useState(false);  // ファイル選択後のボタン表示制御用

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFiles = selectedFiles.filter(file => file.name.endsWith('.csv'));

    if (validFiles.length > 0) {
      setFiles(validFiles);
      setError('');
      setShowButtons(true);  // ファイル選択時にボタンを表示
    } else {
      setFiles([]);
      setError('CSVファイルを選択してください');
      setShowButtons(false);  // 有効なファイルがない場合はボタンを非表示
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('ファイルを選択してください');
      return;
    }

    setUploading(true);
    setError('');

    try {
      // 全ファイルのアップロード結果を管理
      const results = [];

      // 各ファイルを順番にアップロード
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('data_type', dataType); // フォームデータとしてデータタイプを送信

        console.log(`アップロード開始: ${file.name}, タイプ: ${dataType}`);

        // APIサーバーにファイルをアップロード
        const response = await fetch(API_PATHS.upload, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error(`アップロードエラー: ${file.name}`, errorData);
          throw new Error(`${file.name}: ${errorData.detail || 'アップロードに失敗しました'}`);
        }

        const data = await response.json();
        console.log(`アップロード成功: ${file.name}`, data);
        results.push({
          fileName: file.name,
          data
        });
      }

      setFiles([]);
      setShowUploader(false);
      setShowButtons(false);  // アップロード完了時にボタンを非表示
      console.log("すべてのファイルのアップロード完了:", results);

      // アップロード成功時にonUploadSuccessを呼び出し
      if (onUploadSuccess) {
        onUploadSuccess(results);
      }
    } catch (error) {
      console.error("アップロードエラー:", error);
      setError(error.message);
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setFiles([]);
    setError('');
    setShowButtons(false);  // キャンセル時にボタンを非表示
  };

  return (
    <div>
      <button
        onClick={() => setShowUploader(!showUploader)}
        className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
      >
        <Upload size={18} className="mr-2" />
        CSVアップロード
      </button>

      {showUploader && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">CSVファイルのアップロード</h3>

            <div className="mb-4">
              <label className="block text-gray-700 mb-2">データタイプ</label>
              <select
                value={dataType}
                onChange={(e) => setDataType(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value="members">会員データ</option>
                <option value="utilization">稼働率データ</option>
                <option value="competitors">競合データ</option>
                <option value="finance">財務データ</option>
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-gray-700 mb-2">CSVファイル</label>
              <input
                type="file"
                accept=".csv"
                multiple
                onChange={handleFileChange}
                className="w-full p-2 border border-gray-300 rounded-md"
              />
              {files.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-gray-700 font-semibold">選択されたファイル:</p>
                  <ul className="text-sm text-gray-600 mt-1">
                    {files.map((file, index) => (
                      <li key={index}>{file.name}</li>
                    ))}
                  </ul>
                </div>
              )}
              {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
              {dataType === 'utilization' && (
                <p className="text-blue-500 text-sm mt-2">
                  稼働率データのCSVには、date, room, occupancy_rate のカラムが必要です
                </p>
              )}
            </div>

            <div className="flex justify-end space-x-3">
              {showButtons ? (
                <>
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-100"
                  >
                    キャンセル
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={files.length === 0 || uploading}
                    className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
                  >
                    {uploading ? 'アップロード中...' : 'アップロード'}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setShowUploader(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-100"
                >
                  閉じる
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ダミーデータの生成用関数 (実データは後から差し替え)
const generateDummyData = () => {
  // プレースホルダー用のダミーデータを生成
  return {
    labels: {
      months: ['2023-05', '2023-06', '2023-07', '2023-08', '2023-09', '2023-10', '2023-11', '2023-12',
              '2024-01', '2024-02', '2024-03', '2024-04', '2024-05'],
      daysOfWeek: ['月', '火', '水', '木', '金', '土', '日'],
      timeSlots: ['9-12時', '12-15時', '15-18時', '18-21時', '21-24時'],
      regions: ['大阪府', '兵庫県', '京都府', '奈良県', '滋賀県', '和歌山県', 'その他'],
      roomNames: ['Room1', 'Room2', 'Room3'],
      competitorNames: ['HAAAVE.sauna', 'KUDOCHI sauna', 'MENTE', 'M\'s Sauna', 'SAUNA Pod 槃', 'SAUNA OOO OSAKA', '大阪サウナ DESSE'],
      ageGroups: ['20代', '30代', '40代', '50代', '~19歳', '60歳~'],
      genders: ['男性', '女性']
    },
    // 空の状態で初期化 - 実際のデータは外部から取得
    members: {},
    utilization: {},
    competitors: {},
    finance: {}
  };
};

// メインダッシュボードコンポーネント
const Dashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedPeriod, setSelectedPeriod] = useState('all');
  const [selectedMonth, setSelectedMonth] = useState('');
  const [showMonthlyDetail, setShowMonthlyDetail] = useState(false);
  const [dashboardData, setDashboardData] = useState(generateDummyData());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // サイドバー切替
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // ESCキーでモーダルを閉じる
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && showMonthlyDetail) {
        setShowMonthlyDetail(false);
      }
    };

    window.addEventListener('keydown', handleEsc);

    return () => {
      window.removeEventListener('keydown', handleEsc);
    };
  }, [showMonthlyDetail]);

  // 月別詳細表示ハンドラー
  const handleMonthlyDetailShow = (month) => {
    setSelectedMonth(month);
    setShowMonthlyDetail(true);
  };

  // APIからデータを取得する
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(API_PATHS.dashboard);
        if (!response.ok) {
          throw new Error('APIからのデータ取得に失敗しました');
        }
        const data = await response.json();
        setDashboardData(data);
      } catch (error) {
        console.error('APIエラー:', error);
        // エラー時はダミーデータを使用
        setDashboardData(generateDummyData());
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // CSVアップロード成功時の処理
  const handleUploadSuccess = () => {
    // データを再取得（遅延を入れる）
    setIsLoading(true);
    console.log("CSVアップロード成功！データを再取得します...");

    // キャッシュを回避するためのタイムスタンプと少し遅延させてデータを再取得
    setTimeout(() => {
      console.log("データ再取得を開始します");

      // 数回再試行するようにする
      const fetchWithRetry = async (retryCount = 3) => {
        try {
          const response = await fetch(API_PATHS.dashboard);
          if (!response.ok) {
            throw new Error('APIからのデータ取得に失敗しました');
          }
          const data = await response.json();
          console.log("新しいデータを取得しました:", data);
          setDashboardData(data);
          setIsLoading(false);
        } catch (error) {
          console.error('APIエラー:', error);

          if (retryCount > 0) {
            console.log(`再試行します... (残り ${retryCount} 回)`);
            setTimeout(() => fetchWithRetry(retryCount - 1), 1000);
          } else {
            console.error('再試行回数を超えました');
            setIsLoading(false);
          }
        }
      };

      fetchWithRetry();
    }, 2000); // 2秒遅延させる
  };

  // データ再取得関数 - リフレッシュボタン用
  const fetchData = async () => {
    try {
      setIsLoading(true);
      // キャッシュを回避するためのタイムスタンプ付きURLでデータを再取得
      const response = await fetch(API_PATHS.dashboard);
      if (!response.ok) {
        throw new Error('APIからのデータ取得に失敗しました');
      }
      const data = await response.json();
      console.log("データを取得しました:", data);
      setDashboardData(data);
    } catch (error) {
      console.error('APIエラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* サイドバー */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-white shadow-sm transition-all duration-300`} style={{ position: 'fixed', height: '100vh' }}>
        <div className="p-4 flex items-center justify-between">
          <h1 className={`font-bold text-lg transition-opacity ${sidebarOpen ? 'opacity-100' : 'opacity-0 hidden'}`}>HAAAVE.sauna</h1>
          <button onClick={toggleSidebar} className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
            <Menu size={20} className="text-gray-500" />
          </button>
        </div>

        <div className="px-4 pt-2 pb-6">
          <NavItem
            icon={<Activity size={20} />}
            label="概要"
            active={activeTab === 'overview'}
            onClick={() => setActiveTab('overview')}
          />
          <NavItem
            icon={<Users size={20} />}
            label="会員分析"
            active={activeTab === 'members'}
            onClick={() => setActiveTab('members')}
          />
          <NavItem
            icon={<Calendar size={20} />}
            label="ルーム稼働率"
            active={activeTab === 'utilization'}
            onClick={() => setActiveTab('utilization')}
          />
          <NavItem
            icon={<Target size={20} />}
            label="曜日・時間分析"
            active={activeTab === 'dayTime'}
            onClick={() => setActiveTab('dayTime')}
          />
          <NavItem
            icon={<BarChart2 size={20} />}
            label="競合分析"
            active={activeTab === 'competitors'}
            onClick={() => setActiveTab('competitors')}
          />
          <NavItem
            icon={<TrendingUp size={20} />}
            label="売上分析"
            active={activeTab === 'finance'}
            onClick={() => setActiveTab('finance')}
          />
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="flex-1 overflow-x-hidden" style={{ marginLeft: sidebarOpen ? '16rem' : '5rem' }}>
        {/* ヘッダー */}
        <header className="bg-white shadow-sm p-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">サウナ施設分析ダッシュボード</h1>
            <p className="text-sm text-gray-500">データに基づく施設運営の最適化</p>
          </div>

          <div className="flex items-center space-x-3">
            {/* CSVアップロードコンポーネント */}
            <CSVUploader onUploadSuccess={handleUploadSuccess} />

            <div className="relative">
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="appearance-none bg-white border border-gray-300 rounded-lg py-2 px-4 pr-10 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全期間</option>
                <option value="2023">2023年</option>
                <option value="2024">2024年</option>
                <option value="2025">2025年</option>
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                <ChevronDown size={16} className="text-gray-500" />
              </div>
            </div>

            <button className="p-2 bg-white rounded-lg shadow hover:shadow-md transition-shadow" onClick={fetchData}>
              <RefreshCw size={20} className="text-gray-500" />
            </button>

            <button className="p-2 bg-white rounded-lg shadow hover:shadow-md transition-shadow">
              <Filter size={20} className="text-gray-500" />
            </button>

            <button className="p-2 bg-white rounded-lg shadow hover:shadow-md transition-shadow">
              <Download size={20} className="text-gray-500" />
            </button>
          </div>
        </header>

        {/* エラーメッセージ */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded m-4" role="alert">
            <p>{error}</p>
          </div>
        )}

        {/* ロード中表示 */}
        {isLoading && (
          <div className="flex justify-center items-center p-6">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
          </div>
        )}

        {/* メインコンテンツエリア */}
        <main className="p-6">
          {/* 概要タブ */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* 基本統計カード */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card
                  title="総メンバー数"
                  value={dashboardData.metrics?.total_members || "---"}
                  icon={<Users size={20} color={COLORS.primary} />}
                  color={COLORS.primary}
                />
                <Card
                  title="アクティブ会員数"
                  value={dashboardData.metrics?.active_members || "---"}
                  subValue={`入会率: ${dashboardData.metrics?.join_rate?.toFixed(1) || "---"}%`}
                  icon={<Users size={20} color={COLORS.success} />}
                  color={COLORS.success}
                />
                <Card
                  title="トライアル体験者数"
                  value="---"
                  icon={<Users size={20} color={COLORS.accent1} />}
                  color={COLORS.accent1}
                />
                <Card
                  title="ビジター数"
                  value="---"
                  icon={<Users size={20} color={COLORS.accent2} />}
                  color={COLORS.accent2}
                />
              </div>

              {/* ルーム稼働率と会員属性 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ChartCard
                  title="ルーム別稼働率"
                  subtitle={selectedPeriod === 'all' ? '全期間の平均稼働率' : `${selectedPeriod}年の平均稼働率`}
                >
                  <div style={{ height: 300 }} className="flex justify-center items-center">
                    <p className="text-gray-400">データロード中...</p>
                  </div>
                </ChartCard>

                <ChartCard
                  title="会員属性"
                  subtitle="性別・年齢分布"
                >
                  <div style={{ height: 300 }} className="flex justify-center items-center">
                    <p className="text-gray-400">データロード中...</p>
                  </div>
                </ChartCard>
              </div>

              {/* 曜日別稼働率 */}
              <ChartCard
                title="曜日別稼働率"
                subtitle="各ルームの曜日別稼働状況"
              >
                <div style={{ height: 300 }} className="flex justify-center items-center">
                  <p className="text-gray-400">データロード中...</p>
                </div>
              </ChartCard>

              {/* 月別稼働率の推移 */}
              <ChartCard
                title="月別稼働率推移"
                subtitle="各ルームの月別稼働率推移"
              >
                <div style={{ height: 300 }} className="flex justify-center items-center">
                  <p className="text-gray-400">データロード中...</p>
                </div>
              </ChartCard>
            </div>
          )}

          {/* 会員分析タブ */}
          {activeTab === 'members' && (
            <div className="space-y-6">
              {/* 会員統計カード */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card
                  title="総メンバー数"
                  value={dashboardData.members?.total || "100"}
                  icon={<Users size={20} color={COLORS.primary} />}
                  color={COLORS.primary}
                />
                <Card
                  title="アクティブ会員数"
                  value={dashboardData.members?.active || "78"}
                  subValue={`入会率: ${dashboardData.members?.joinRate || "78"}%`}
                  icon={<Users size={20} color={COLORS.success} />}
                  color={COLORS.success}
                />
                <Card
                  title="入会率"
                  value={`${dashboardData.members?.joinRate || "78"}%`}
                  subValue={`${dashboardData.members?.active || "78"}/${dashboardData.members?.total || "100"}`}
                  icon={<TrendingUp size={20} color={COLORS.accent1} />}
                  color={COLORS.accent1}
                />
                <Card
                  title="退会率"
                  value={`${dashboardData.members?.churnRate || "3.2"}%`}
                  icon={<TrendingUp size={20} color={COLORS.danger} />}
                  color={COLORS.danger}
                />
              </div>

              {/* 性別・年齢分布 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ChartCard
                  title="性別分布"
                  subtitle="会員の性別比率"
                >
                  <div style={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={dashboardData.members?.genderDistribution || [
                            { name: "男性", value: 50 },
                            { name: "女性", value: 50 }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={0}
                          dataKey="value"
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        >
                          <Cell key="男性" fill={COLORS.male} />
                          <Cell key="女性" fill={COLORS.female} />
                        </Pie>
                        <Legend />
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                <ChartCard
                  title="年齢分布"
                  subtitle="会員の年代別分布"
                >
                  <div style={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={dashboardData.members?.ageDistribution || [
                          { name: "~19歳", value: 5 },
                          { name: "20代", value: 35 },
                          { name: "30代", value: 30 },
                          { name: "40代", value: 20 },
                          { name: "50代", value: 7 },
                          { name: "60歳~", value: 3 }
                        ]}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="value" fill={COLORS.primary} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>
              </div>

              {/* 地域分布 */}
              <ChartCard
                title="地域分布"
                subtitle="会員の都道府県別分布"
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={dashboardData.members?.regionDistribution || [
                        { name: "大阪市北区", value: 30 },
                        { name: "大阪市中央区", value: 25 },
                        { name: "大阪市西区", value: 15 },
                        { name: "大阪市浪速区", value: 10 },
                        { name: "大阪市天王寺区", value: 8 },
                        { name: "大阪市淀川区", value: 7 },
                        { name: "その他", value: 5 }
                      ]}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill={COLORS.primary} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* 会員推移グラフ */}
              <ChartCard
                title="会員推移"
                subtitle="会員・体験者・ビジターの月別推移"
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={dashboardData.members?.membershipTrend || dashboardData.labels.months.map(month => ({
                        name: month,
                        会員: Math.floor(Math.random() * 40) + 60,
                        体験者: Math.floor(Math.random() * 30) + 20,
                        ビジター: Math.floor(Math.random() * 100) + 40,
                      }))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="会員" stroke={COLORS.primary} activeDot={{ r: 8 }} />
                      <Line type="monotone" dataKey="体験者" stroke={COLORS.accent1} />
                      <Line type="monotone" dataKey="ビジター" stroke={COLORS.accent2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            </div>
          )}

          {/* ルーム稼働率タブ */}
          {activeTab === 'utilization' && (
            <div className="space-y-6">
              {/* ルーム稼働率カード */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card
                  title="Room1 稼働率"
                  value={`${dashboardData.utilization?.rooms?.Room1?.average?.toFixed(1) || "75.2"}%`}
                  icon={<Activity size={20} color={COLORS.room1} />}
                  color={COLORS.room1}
                />
                <Card
                  title="Room2 稼働率"
                  value={`${dashboardData.utilization?.rooms?.Room2?.average?.toFixed(1) || "68.3"}%`}
                  icon={<Activity size={20} color={COLORS.room2} />}
                  color={COLORS.room2}
                />
                <Card
                  title="Room3 稼働率"
                  value={`${dashboardData.utilization?.rooms?.Room3?.average?.toFixed(1) || "82.7"}%`}
                  icon={<Activity size={20} color={COLORS.room3} />}
                  color={COLORS.room3}
                />
              </div>

              {/* 稼働率比較チャート */}
              <ChartCard
                title="ルーム稼働率比較"
                subtitle={selectedPeriod === 'all' ? '全期間の平均稼働率' : `${selectedPeriod}年の平均稼働率`}
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        {
                          name: 'Room1',
                          稼働率: dashboardData.utilization?.rooms?.Room1?.average || 75.2
                        },
                        {
                          name: 'Room2',
                          稼働率: dashboardData.utilization?.rooms?.Room2?.average || 68.3
                        },
                        {
                          name: 'Room3',
                          稼働率: dashboardData.utilization?.rooms?.Room3?.average || 82.7
                        }
                      ]}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="稼働率" fill={COLORS.primary} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* 年間推移チャート */}
              <ChartCard
                title="年間推移"
                subtitle="各ルームの年間稼働率推移"
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={dashboardData.utilization?.byMonth || dashboardData.labels.months.map(month => ({
                        name: month,
                        Room1: Math.floor(Math.random() * 30) + 60,
                        Room2: Math.floor(Math.random() * 30) + 55,
                        Room3: Math.floor(Math.random() * 25) + 70,
                      }))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="Room1" stroke={COLORS.room1} activeDot={{ r: 8 }} />
                      <Line type="monotone" dataKey="Room2" stroke={COLORS.room2} activeDot={{ r: 8 }} />
                      <Line type="monotone" dataKey="Room3" stroke={COLORS.room3} activeDot={{ r: 8 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* 月別稼働率テーブル */}
              <ChartCard
                title="月別稼働率詳細"
                subtitle="各ルームの月別稼働率データ"
              >
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">月</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Room1</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Room2</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Room3</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">詳細</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {(dashboardData.utilization?.byMonth || dashboardData.labels.months.map(month => ({
                        name: month,
                        Room1: Math.floor(Math.random() * 30) + 60,
                        Room2: Math.floor(Math.random() * 30) + 55,
                        Room3: Math.floor(Math.random() * 25) + 70,
                      }))).map((month, index) => (
                        <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="px-6 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{month.name}</td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-500">{month.Room1?.toFixed(1) || "---"}%</td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-500">{month.Room2?.toFixed(1) || "---"}%</td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-500">{month.Room3?.toFixed(1) || "---"}%</td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-500">
                            <button
                              onClick={() => handleMonthlyDetailShow(month.name)}
                              className="text-blue-600 hover:text-blue-800 font-medium"
                            >
                              詳細を見る
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </ChartCard>
            </div>
          )}

          {/* 曜日・時間分析タブ */}
          {activeTab === 'dayTime' && (
            <div className="space-y-6">
              {/* 曜日別稼働率チャート */}
              <ChartCard
                title="曜日別稼働率"
                subtitle="各ルームの曜日別稼働状況"
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={dashboardData.utilization?.byDayOfWeek || [
                        { name: '月', Room1: 65, Room2: 58, Room3: 75 },
                        { name: '火', Room1: 60, Room2: 55, Room3: 70 },
                        { name: '水', Room1: 70, Room2: 60, Room3: 80 },
                        { name: '木', Room1: 75, Room2: 65, Room3: 85 },
                        { name: '金', Room1: 85, Room2: 75, Room3: 90 },
                        { name: '土', Room1: 95, Room2: 85, Room3: 95 },
                        { name: '日', Room1: 90, Room2: 80, Room3: 90 }
                      ]}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="Room1" fill={COLORS.room1} />
                      <Bar dataKey="Room2" fill={COLORS.room2} />
                      <Bar dataKey="Room3" fill={COLORS.room3} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* 時間帯別稼働率チャート */}
              <ChartCard
                title="時間帯別稼働率"
                subtitle="各ルームの時間帯別稼働状況"
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={dashboardData.utilization?.byTimeSlot || [
                        { name: '9-12時', Room1: 50, Room2: 45, Room3: 55 },
                        { name: '12-15時', Room1: 65, Room2: 60, Room3: 70 },
                        { name: '15-18時', Room1: 80, Room2: 70, Room3: 85 },
                        { name: '18-21時', Room1: 95, Room2: 85, Room3: 90 },
                        { name: '21-24時', Room1: 70, Room2: 65, Room3: 75 }
                      ]}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="Room1" fill={COLORS.room1} />
                      <Bar dataKey="Room2" fill={COLORS.room2} />
                      <Bar dataKey="Room3" fill={COLORS.room3} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* ルーム別分析 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <ChartCard
                  title="Room1 曜日別稼働率"
                  subtitle="Room1の曜日別詳細"
                >
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={(dashboardData.utilization?.byDayOfWeek || []).map(day => ({
                          name: day.name,
                          稼働率: day.Room1
                        }))}
                        margin={{ top: 20, right: 10, left: 10, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Bar dataKey="稼働率" fill={COLORS.room1} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                <ChartCard
                  title="Room2 曜日別稼働率"
                  subtitle="Room2の曜日別詳細"
                >
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={(dashboardData.utilization?.byDayOfWeek || []).map(day => ({
                          name: day.name,
                          稼働率: day.Room2
                        }))}
                        margin={{ top: 20, right: 10, left: 10, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Bar dataKey="稼働率" fill={COLORS.room2} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                <ChartCard
                  title="Room3 曜日別稼働率"
                  subtitle="Room3の曜日別詳細"
                >
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={(dashboardData.utilization?.byDayOfWeek || []).map(day => ({
                          name: day.name,
                          稼働率: day.Room3
                        }))}
                        margin={{ top: 20, right: 10, left: 10, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Bar dataKey="稼働率" fill={COLORS.room3} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>
              </div>
            </div>
          )}

          {/* 競合分析タブ */}
          {activeTab === 'competitors' && (
            <div className="space-y-6">
              {/* 競合統計カード */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card
                  title="競合施設数"
                  value={dashboardData.competitors?.total || "12"}
                  icon={<Target size={20} color={COLORS.primary} />}
                  color={COLORS.primary}
                />
                <Card
                  title="平均料金"
                  value={`¥${(dashboardData.competitors?.avgPrice || 3200).toLocaleString()}`}
                  icon={<DollarSign size={20} color={COLORS.success} />}
                  color={COLORS.success}
                />
                <Card
                  title="当社料金優位性"
                  value={`${dashboardData.competitors?.priceDiff || "-12"}%`}
                  icon={<TrendingUp size={20} color={COLORS.accent1} />}
                  color={COLORS.accent1}
                />
                <Card
                  title="エリア内シェア"
                  value={`${dashboardData.competitors?.marketShare || "15"}%`}
                  icon={<PieChart size={20} color={COLORS.accent2} />}
                  color={COLORS.accent2}
                />
              </div>

              {/* 価格比較チャート */}
              <ChartCard
                title="競合施設料金比較"
                subtitle="大阪市内の主なプライベートサウナ施設の料金比較（1時間あたり）"
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={dashboardData.competitors?.pricing || [
                        { name: "HAAAVE.sauna", "価格": 16000, "表示価格": "16,000円～" },
                        { name: "M's Sauna", "価格": 10000, "表示価格": "10,000円～" },
                        { name: "KUDOCHI sauna", "価格": 6000, "表示価格": "6,000円～" },
                        { name: "SAUNA Pod 槃", "価格": 5500, "表示価格": "5,500円～" },
                        { name: "SAUNA OOO OSAKA", "価格": 5500, "表示価格": "5,500円～" },
                        { name: "MENTE", "価格": 5000, "表示価格": "5,000円～" },
                        { name: "大阪サウナ DESSE", "価格": 1500, "表示価格": "1,500円～" }
                      ]}
                      layout="vertical"
                      margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[0, 18000]} />
                      <YAxis type="category" dataKey="name" width={100} />
                      <Tooltip formatter={(value, name) => name === "価格" ? `${value.toLocaleString()}円～` : value} />
                      <Bar dataKey="価格" fill={COLORS.primary} name="料金" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* 競合詳細テーブル */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">競合詳細情報</h3>
                  <button
                    className="text-sm flex items-center text-primary-600 hover:text-primary-800"
                    onClick={() => {}} // ダウンロード機能は省略
                  >
                    <Download size={16} className="mr-1" />
                    CSV出力
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">施設名</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">所在地</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">形態</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">料金</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ルーム数</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">水風呂</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">男女混浴</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">開業年</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {(dashboardData.competitors?.details || [
                        {
                          "施設名": "HAAAVE.sauna",
                          "所在地": "大阪市西区南堀江",
                          "形態": "会員制",
                          "料金": "16,000円～",
                          "ルーム数": "3室",
                          "水風呂": "あり",
                          "男女混浴": "可",
                          "開業年": "2023年"
                        },
                        {
                          "施設名": "KUDOCHI sauna",
                          "所在地": "大阪市中央区東心斎橋",
                          "形態": "完全個室",
                          "料金": "6,000円～",
                          "ルーム数": "6室",
                          "水風呂": "あり",
                          "男女混浴": "可",
                          "開業年": "2024年"
                        },
                        {
                          "施設名": "MENTE",
                          "所在地": "大阪市北区茶屋町",
                          "形態": "男性専用",
                          "料金": "5,000円～",
                          "ルーム数": "1室",
                          "水風呂": "なし",
                          "男女混浴": "不可",
                          "開業年": "2022年"
                        },
                        {
                          "施設名": "M's Sauna",
                          "所在地": "大阪市北区曾根崎新地",
                          "形態": "VIP個室",
                          "料金": "10,000円～",
                          "ルーム数": "3室",
                          "水風呂": "あり",
                          "男女混浴": "不可",
                          "開業年": "2023年"
                        },
                        {
                          "施設名": "SAUNA Pod 槃",
                          "所在地": "大阪市西区",
                          "形態": "会員制",
                          "料金": "5,500円～",
                          "ルーム数": "4室",
                          "水風呂": "あり",
                          "男女混浴": "可",
                          "開業年": "2023年"
                        },
                        {
                          "施設名": "SAUNA OOO OSAKA",
                          "所在地": "大阪市中央区西心斎橋",
                          "形態": "予約制",
                          "料金": "5,500円～",
                          "ルーム数": "3室",
                          "水風呂": "なし",
                          "男女混浴": "可",
                          "開業年": "2023年"
                        },
                        {
                          "施設名": "大阪サウナ DESSE",
                          "所在地": "大阪市中央区南船場",
                          "形態": "大型複合",
                          "料金": "1,500円～",
                          "ルーム数": "7室",
                          "水風呂": "あり",
                          "男女混浴": "不可",
                          "開業年": "2023年"
                        }
                      ]).map((competitor, index) => (
                        <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                            {competitor.施設名 === 'HAAAVE.sauna' ? (
                              <span className="font-bold text-blue-600">{competitor.施設名}</span>
                            ) : (
                              competitor.施設名
                            )}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{competitor.所在地}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{competitor.形態}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{competitor.料金}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{competitor.ルーム数}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                            {competitor.水風呂 === 'あり' ? <span className="text-green-500">✓</span> : <span className="text-red-500">✕</span>}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                            {competitor.男女混浴 === '可' ? <span className="text-green-500">✓</span> : <span className="text-red-500">✕</span>}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{competitor.開業年}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 地域分布 */}
              <ChartCard
                title="競合施設 地域分布"
                subtitle="大阪市内のエリア別サウナ施設数"
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      layout="vertical"
                      data={dashboardData.competitors?.regionDistribution || [
                        { name: "心斎橋エリア", value: 3 },
                        { name: "梅田・北新地", value: 2 },
                        { name: "西区", value: 2 },
                        { name: "その他", value: 1 }
                      ]}
                      margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis type="category" dataKey="name" width={100} />
                      <Tooltip />
                      <Bar
                        dataKey="value"
                        fill={COLORS.primary}
                        name="施設数"
                        isAnimationActive={true}
                        animationDuration={1000}
                        animationEasing="ease-out"
                      >
                        {(dashboardData.competitors?.regionDistribution || []).map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.name === '心斎橋エリア' ? COLORS.success : COLORS.primary}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            </div>
          )}

          {/* 売上分析タブ */}
          {activeTab === 'finance' && (
            <div className="space-y-6">
              {/* 売上統計カード */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card
                  title="月間売上"
                  value={`¥${(dashboardData.finance?.latest_month?.sales || 1250000).toLocaleString()}`}
                  icon={<DollarSign size={20} color={COLORS.primary} />}
                  color={COLORS.primary}
                />
                <Card
                  title="月間利益"
                  value={`¥${(dashboardData.finance?.latest_month?.profit || 375000).toLocaleString()}`}
                  icon={<TrendingUp size={20} color={COLORS.success} />}
                  color={COLORS.success}
                />
                <Card
                  title="利益率"
                  value={`${(dashboardData.finance?.latest_month?.profit_rate || 30).toFixed(1)}%`}
                  subValue={`前月比: ${dashboardData.finance?.trend?.profit_change || "+2.3"}%`}
                  icon={<Percent size={20} color={COLORS.accent1} />}
                  color={COLORS.accent1}
                />
                <Card
                  title="平均客単価"
                  value={`¥${(dashboardData.finance?.latest_month?.average_value || 5800).toLocaleString()}`}
                  icon={<Users size={20} color={COLORS.accent2} />}
                  color={COLORS.accent2}
                />
              </div>

              {/* 月別売上・利益推移 */}
              <ChartCard
                title="月別売上・利益推移"
                subtitle={selectedPeriod === 'all' ? '全期間の推移' : `${selectedPeriod}年の推移`}
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={dashboardData.finance?.monthly_trend || dashboardData.labels.months.map(month => ({
                        name: month,
                        売上: Math.floor(Math.random() * 400000) + 900000,
                        利益: Math.floor(Math.random() * 150000) + 250000,
                      }))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip formatter={(value) => `¥${value.toLocaleString()}`} />
                      <Legend />
                      <Bar dataKey="売上" fill={COLORS.primary} />
                      <Bar dataKey="利益" fill={COLORS.success} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              {/* 会員種別・ルーム別売上分布 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ChartCard
                  title="会員種別売上分布"
                  subtitle="会員種別ごとの売上比率"
                >
                  <div style={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: "会員", value: dashboardData.finance?.salesByType?.会員 || 850000 },
                            { name: "ビジター", value: dashboardData.finance?.salesByType?.ビジター || 250000 },
                            { name: "トライアル", value: dashboardData.finance?.salesByType?.トライアル || 150000 }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={5}
                          dataKey="value"
                          nameKey="name"
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        >
                          <Cell key="会員" fill={COLORS.primary} />
                          <Cell key="ビジター" fill={COLORS.accent1} />
                          <Cell key="トライアル" fill={COLORS.accent2} />
                        </Pie>
                        <Legend />
                        <Tooltip formatter={(value) => `¥${value.toLocaleString()}`} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                <ChartCard
                  title="ルーム別売上分布"
                  subtitle="各ルームの売上比率"
                >
                  <div style={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: "Room1", value: dashboardData.finance?.salesByRoom?.Room1 || 450000 },
                            { name: "Room2", value: dashboardData.finance?.salesByRoom?.Room2 || 350000 },
                            { name: "Room3", value: dashboardData.finance?.salesByRoom?.Room3 || 450000 }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={5}
                          dataKey="value"
                          nameKey="name"
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        >
                          <Cell key="Room1" fill={COLORS.room1} />
                          <Cell key="Room2" fill={COLORS.room2} />
                          <Cell key="Room3" fill={COLORS.room3} />
                        </Pie>
                        <Legend />
                        <Tooltip formatter={(value) => `¥${value.toLocaleString()}`} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>
              </div>

              {/* 曜日別売上分布 */}
              <ChartCard
                title="曜日別売上分布"
                subtitle="曜日ごとの売上推移"
              >
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={dashboardData.finance?.dailySales || [
                        { name: '月', 売上: 150000, 利益: 45000 },
                        { name: '火', 売上: 120000, 利益: 36000 },
                        { name: '水', 売上: 180000, 利益: 54000 },
                        { name: '木', 売上: 210000, 利益: 63000 },
                        { name: '金', 売上: 250000, 利益: 75000 },
                        { name: '土', 売上: 320000, 利益: 96000 },
                        { name: '日', 売上: 280000, 利益: 84000 }
                      ]}
                      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip formatter={(value) => `¥${value.toLocaleString()}`} />
                      <Legend />
                      <Bar dataKey="売上" fill={COLORS.primary} />
                      <Bar dataKey="利益" fill={COLORS.success} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
