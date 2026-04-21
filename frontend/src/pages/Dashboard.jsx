import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getDailySummary, getTodayMeals } from '../services/api';
import { Flame, Target, TrendingUp, Utensils, Zap, AlertTriangle, CheckCircle } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [meals, setMeals] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryRes, mealsRes] = await Promise.all([getDailySummary(), getTodayMeals()]);
      setSummary(summaryRes.data);
      setMeals(mealsRes.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
        <p className="loading-text">Loading your dashboard...</p>
      </div>
    );
  }

  const totalCalories = summary?.total_calories || 0;
  const budget = summary?.budget || user?.daily_calorie_budget || 2000;
  const remaining = budget - totalCalories;
  const percentage = Math.min((totalCalories / budget) * 100, 100);
  const alertStatus = summary?.alert || 'normal';

  const circumference = 2 * Math.PI * 62;
  const offset = circumference - (percentage / 100) * circumference;

  const getProgressColor = () => {
    if (percentage > 100) return '#ef4444';
    if (percentage > 90) return '#f97316';
    if (percentage > 70) return '#eab308';
    return '#22c55e';
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Good {getGreeting()}, {user?.name?.split(' ')[0]} 👋</h1>
        <p className="page-subtitle">Here's your nutrition overview for today</p>
      </div>

      {/* Smart Notifications */}
      {alertStatus === 'warning' && (
        <div className="notification-bar warning">
          <AlertTriangle size={20} />
          You're approaching your daily calorie limit! {remaining} calories remaining.
        </div>
      )}
      {alertStatus === 'exceeded' && (
        <div className="notification-bar danger">
          <AlertTriangle size={20} />
          You've exceeded your daily calorie budget by {Math.abs(remaining)} calories.
        </div>
      )}
      {totalCalories > 0 && alertStatus === 'normal' && (
        <div className="notification-bar success">
          <CheckCircle size={20} />
          You're on track! {remaining} calories remaining for today.
        </div>
      )}

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon green"><Flame size={24} /></div>
          <div>
            <div className="stat-value">{totalCalories}</div>
            <div className="stat-label">Calories Consumed</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue"><Target size={24} /></div>
          <div>
            <div className="stat-value">{budget}</div>
            <div className="stat-label">Daily Budget</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple"><TrendingUp size={24} /></div>
          <div>
            <div className="stat-value" style={{ color: remaining < 0 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
              {remaining}
            </div>
            <div className="stat-label">Remaining</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon orange"><Utensils size={24} /></div>
          <div>
            <div className="stat-value">{meals?.meals?.length || 0}</div>
            <div className="stat-label">Meals Logged</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Calorie Progress Ring */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Today's Progress</h3>
            <span className="card-subtitle">{percentage.toFixed(0)}% of daily budget</span>
          </div>
          <div className="progress-ring-container">
            <div className="progress-ring">
              <svg width="160" height="160" viewBox="0 0 160 160">
                <circle className="progress-ring-bg" cx="80" cy="80" r="62" fill="none" strokeWidth="12" />
                <circle
                  className="progress-ring-fill"
                  cx="80" cy="80" r="62"
                  fill="none"
                  strokeWidth="12"
                  stroke={getProgressColor()}
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset}
                />
              </svg>
              <div className="progress-ring-text">
                <div className="progress-ring-value">{totalCalories}</div>
                <div className="progress-ring-label">of {budget} cal</div>
              </div>
            </div>
          </div>
        </div>

        {/* Macros Breakdown */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Macronutrients</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Zap size={16} color="var(--accent-yellow)" />
              <span className="card-subtitle">Today's intake</span>
            </div>
          </div>
          <div className="macro-bar-group">
            <div className="macro-bar">
              <span className="macro-bar-label">Protein</span>
              <div className="macro-bar-track">
                <div
                  className="macro-bar-fill"
                  style={{
                    width: `${Math.min((summary?.macros?.protein_g || 0) / 1.5, 100)}%`,
                    background: 'var(--accent-blue)',
                  }}
                />
              </div>
              <span className="macro-bar-value">{summary?.macros?.protein_g || 0}g</span>
            </div>
            <div className="macro-bar">
              <span className="macro-bar-label">Carbs</span>
              <div className="macro-bar-track">
                <div
                  className="macro-bar-fill"
                  style={{
                    width: `${Math.min((summary?.macros?.carbs_g || 0) / 3, 100)}%`,
                    background: 'var(--accent-orange)',
                  }}
                />
              </div>
              <span className="macro-bar-value">{summary?.macros?.carbs_g || 0}g</span>
            </div>
            <div className="macro-bar">
              <span className="macro-bar-label">Fat</span>
              <div className="macro-bar-track">
                <div
                  className="macro-bar-fill"
                  style={{
                    width: `${Math.min((summary?.macros?.fat_g || 0) / 1, 100)}%`,
                    background: 'var(--accent-purple)',
                  }}
                />
              </div>
              <span className="macro-bar-value">{summary?.macros?.fat_g || 0}g</span>
            </div>
          </div>

          {/* Meal Breakdown */}
          <div style={{ marginTop: 24 }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 12, color: 'var(--text-secondary)' }}>
              Meal Breakdown
            </h4>
            {['breakfast', 'lunch', 'dinner', 'snack'].map((type) => {
              const mealEmojis = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '🍿' };
              const cal = summary?.breakdown?.[type]?.calories || 0;
              return (
                <div key={type} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 0', borderBottom: '1px solid var(--border-color)',
                  fontSize: '0.85rem',
                }}>
                  <span>
                    {mealEmojis[type]} {type.charAt(0).toUpperCase() + type.slice(1)}
                  </span>
                  <span style={{ fontWeight: 600 }}>{cal} cal</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent Meals */}
      {meals?.meals?.length > 0 && (
        <div className="card" style={{ marginTop: 24 }}>
          <div className="card-header">
            <h3 className="card-title">Today's Meals</h3>
          </div>
          {meals.meals.slice(0, 5).map((meal) => (
            <div key={meal.id} className="meal-item">
              {meal.image_url ? (
                <img src={`http://localhost:5000${meal.image_url}`} alt="meal" className="meal-item-image" />
              ) : (
                <div className="meal-item-image-placeholder">🍽️</div>
              )}
              <div className="meal-item-info">
                <div className="meal-item-name">
                  {meal.food_items?.map((f) => f.name).join(', ') || 'Meal'}
                </div>
                <div className="meal-item-details">
                  {meal.meal_type.charAt(0).toUpperCase() + meal.meal_type.slice(1)} •{' '}
                  P: {meal.protein_g}g · C: {meal.carbs_g}g · F: {meal.fat_g}g
                </div>
              </div>
              <div className="meal-item-calories">{meal.total_calories} cal</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Morning';
  if (hour < 17) return 'Afternoon';
  return 'Evening';
}
