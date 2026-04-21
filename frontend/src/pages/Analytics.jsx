import { useState, useEffect } from 'react';
import { getWeeklyTrends, getProgress } from '../services/api';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { TrendingUp, Award, Calendar, Target } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Tooltip, Legend, Filler);

export default function Analytics() {
  const [weekly, setWeekly] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [weeklyRes, progressRes] = await Promise.all([getWeeklyTrends(), getProgress()]);
      setWeekly(weeklyRes.data);
      setProgress(progressRes.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
        <p className="loading-text">Loading analytics...</p>
      </div>
    );
  }

  // Weekly Bar Chart
  const weeklyBarData = {
    labels: weekly?.trends?.map((t) => t.day_name) || [],
    datasets: [
      {
        label: 'Calories',
        data: weekly?.trends?.map((t) => t.calories) || [],
        backgroundColor: weekly?.trends?.map((t) =>
          t.on_track ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)'
        ) || [],
        borderRadius: 8,
        borderSkipped: false,
      },
      {
        label: 'Budget',
        data: weekly?.trends?.map((t) => t.budget) || [],
        type: 'line',
        borderColor: 'rgba(59, 130, 246, 0.8)',
        borderDash: [6, 4],
        borderWidth: 2,
        pointStyle: false,
        fill: false,
      },
    ],
  };

  const weeklyBarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } },
      tooltip: {
        backgroundColor: '#1a1f35',
        titleColor: '#f0f4ff',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(148, 163, 184, 0.2)',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
      },
    },
    scales: {
      y: {
        ticks: { color: '#64748b', font: { family: 'Inter' } },
        grid: { color: 'rgba(148, 163, 184, 0.06)' },
      },
      x: {
        ticks: { color: '#64748b', font: { family: 'Inter' } },
        grid: { display: false },
      },
    },
  };

  // Macros Doughnut
  const avgProtein = weekly?.trends?.reduce((s, t) => s + t.protein_g, 0) / 7 || 0;
  const avgCarbs = weekly?.trends?.reduce((s, t) => s + t.carbs_g, 0) / 7 || 0;
  const avgFat = weekly?.trends?.reduce((s, t) => s + t.fat_g, 0) / 7 || 0;

  const macroDoughnutData = {
    labels: ['Protein', 'Carbs', 'Fat'],
    datasets: [
      {
        data: [avgProtein, avgCarbs, avgFat],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(168, 85, 247, 0.8)',
        ],
        borderWidth: 0,
        hoverOffset: 8,
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#94a3b8', padding: 16, font: { family: 'Inter' } },
      },
    },
  };

  // Calorie Trend Line
  const trendLineData = {
    labels: progress?.trend_data?.map((d) => {
      const dt = new Date(d.log_date);
      return `${dt.getMonth() + 1}/${dt.getDate()}`;
    }) || [],
    datasets: [
      {
        label: 'Calories',
        data: progress?.trend_data?.map((d) => d.total_calories) || [],
        borderColor: 'rgba(59, 130, 246, 1)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
        pointRadius: 3,
        pointHoverRadius: 6,
      },
      {
        label: 'Budget',
        data: progress?.trend_data?.map((d) => d.budget) || [],
        borderColor: 'rgba(239, 68, 68, 0.5)',
        borderDash: [6, 4],
        borderWidth: 2,
        pointStyle: false,
        fill: false,
      },
    ],
  };

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } },
      tooltip: {
        backgroundColor: '#1a1f35',
        titleColor: '#f0f4ff',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(148, 163, 184, 0.2)',
        borderWidth: 1,
        cornerRadius: 8,
      },
    },
    scales: {
      y: {
        ticks: { color: '#64748b', font: { family: 'Inter' } },
        grid: { color: 'rgba(148, 163, 184, 0.06)' },
      },
      x: {
        ticks: { color: '#64748b', font: { family: 'Inter' } },
        grid: { display: false },
      },
    },
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Analytics 📊</h1>
        <p className="page-subtitle">Track your eating habits and progress</p>
      </div>

      {/* Overview Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue"><TrendingUp size={24} /></div>
          <div>
            <div className="stat-value">{weekly?.average_calories || 0}</div>
            <div className="stat-label">Avg Daily Calories</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green"><Award size={24} /></div>
          <div>
            <div className="stat-value">{weekly?.days_on_track || 0}/{weekly?.total_days || 7}</div>
            <div className="stat-label">Days On Track (Week)</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple"><Calendar size={24} /></div>
          <div>
            <div className="stat-value">{progress?.days_logged || 0}</div>
            <div className="stat-label">Days Logged (Month)</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon orange"><Target size={24} /></div>
          <div>
            <div className="stat-value">{progress?.consistency || 0}%</div>
            <div className="stat-label">Goal Consistency</div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Weekly Calorie Trends</h3>
            <span className="card-subtitle">Last 7 days</span>
          </div>
          <div className="chart-container">
            <Bar data={weeklyBarData} options={weeklyBarOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Average Macro Split</h3>
            <span className="card-subtitle">Weekly average</span>
          </div>
          <div className="chart-container">
            <Doughnut data={macroDoughnutData} options={doughnutOptions} />
          </div>
        </div>
      </div>

      {/* Monthly Trend */}
      {progress?.trend_data?.length > 0 && (
        <div className="card" style={{ marginTop: 24 }}>
          <div className="card-header">
            <h3 className="card-title">30-Day Calorie Trend</h3>
            <span className="card-subtitle">Your progress over time</span>
          </div>
          <div className="chart-container">
            <Line data={trendLineData} options={lineOptions} />
          </div>
        </div>
      )}
    </div>
  );
}
