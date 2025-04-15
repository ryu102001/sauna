import React, { useState, useEffect } from 'react';
import { Activity, Users, Calendar, Target, BarChart2, TrendingUp, Download, Filter, RefreshCw, Menu, ChevronDown, Upload } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, AreaChart, Area } from 'recharts';

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

// APIのベースURL
const API_BASE_URL = 'http://localhost:8000';

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
  const [file, setFile] = useState(null);
  const [dataType, setDataType] = useState('members');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [showUploader, setShowUploader] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError('');
    } else {
      setFile(null);
      setError('CSVファイルを選択してください');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('ファイルを選択してください');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-csv?data_type=${dataType}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'アップロードに失敗しました');
      }

      const data = await response.json();
      setFile(null);
      setShowUploader(false);
      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setUploading(false);
    }
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
                onChange={handleFileChange}
                className="w-full p-2 border border-gray-300 rounded-md"
              />
              {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowUploader(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-100"
              >
                キャンセル
              </button>
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
              >
                {uploading ? 'アップロード中...' : 'アップロード'}
              </button>
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
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // サイドバー切替
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // APIからデータを取得
  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard-data`);

      if (!response.ok) {
        throw new Error('データの取得に失敗しました');
      }

      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('APIエラー:', error);
      setError('データの取得中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  // コンポーネントマウント時にデータを取得
  useEffect(() => {
    fetchDashboardData();
  }, []);

  // CSVアップロード成功時の処理
  const handleUploadSuccess = (uploadResult) => {
    // データを再取得
    fetchDashboardData();
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

            <button className="p-2 bg-white rounded-lg shadow hover:shadow-md transition-shadow" onClick={fetchDashboardData}>
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

          {/* その他のタブ内容もここに同様に実装 */}
          {/* 簡略化のため各タブの内容は省略 */}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
