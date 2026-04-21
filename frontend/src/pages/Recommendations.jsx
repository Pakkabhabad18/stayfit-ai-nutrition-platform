import { useState, useEffect } from 'react';
import { getRecommendations } from '../services/api';
import { Sparkles, ChefHat, RefreshCw } from 'lucide-react';

export default function Recommendations() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mealType, setMealType] = useState('any');

  useEffect(() => {
    loadRecommendations();
  }, [mealType]);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      const res = await getRecommendations({ meal_type: mealType });
      setData(res.data);
    } catch (err) {
      console.error('Failed to load recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Meal Recommendations 🤖</h1>
        <p className="page-subtitle">AI-powered meal suggestions based on your remaining calorie budget</p>
      </div>

      {/* Remaining Budget Info */}
      {data && (
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-icon green"><Sparkles size={24} /></div>
            <div>
              <div className="stat-value" style={{ color: 'var(--accent-green)' }}>{data.remaining_calories}</div>
              <div className="stat-label">Remaining Calories</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon blue"><ChefHat size={24} /></div>
            <div>
              <div className="stat-value">{data.consumed}</div>
              <div className="stat-label">Consumed Today</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon purple">
              <span style={{ fontSize: '1.2rem' }}>
                {data.goal === 'lose' ? '🔥' : data.goal === 'gain' ? '💪' : '⚖️'}
              </span>
            </div>
            <div>
              <div className="stat-value" style={{ fontSize: '1.3rem', textTransform: 'capitalize' }}>
                {data.goal} Weight
              </div>
              <div className="stat-label">Your Goal</div>
            </div>
          </div>
        </div>
      )}

      {/* Meal Type Filter */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <div className="meal-type-selector">
          {[
            { value: 'any', label: '✨ All' },
            { value: 'breakfast', label: '🌅 Breakfast' },
            { value: 'lunch', label: '☀️ Lunch' },
            { value: 'dinner', label: '🌙 Dinner' },
            { value: 'snack', label: '🍿 Snack' },
          ].map((t) => (
            <button
              key={t.value}
              className={`meal-type-btn ${mealType === t.value ? 'active' : ''}`}
              onClick={() => setMealType(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <button className="btn btn-outline btn-sm" onClick={loadRecommendations} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Recommendations */}
      {loading ? (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p className="loading-text">Getting AI recommendations...</p>
        </div>
      ) : (
        <div>
          {data?.recommendations?.map((rec, i) => (
            <div key={i} className="reco-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div className="reco-name">{rec.name}</div>
                  <div className="reco-description">{rec.description}</div>
                </div>
                <div style={{
                  background: 'var(--gradient-green)',
                  padding: '8px 16px',
                  borderRadius: 'var(--radius-full)',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  whiteSpace: 'nowrap',
                }}>
                  {rec.calories} cal
                </div>
              </div>

              <div className="reco-macros">
                <span className="reco-macro">🥩 Protein: {rec.protein_g}g</span>
                <span className="reco-macro">🍞 Carbs: {rec.carbs_g}g</span>
                <span className="reco-macro">🧈 Fat: {rec.fat_g}g</span>
              </div>

              {rec.highlights && (
                <div className="reco-highlights">
                  {rec.highlights.map((h, j) => (
                    <span key={j} className="reco-tag">{h}</span>
                  ))}
                </div>
              )}

              {rec.preparation && (
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>
                    How to prepare:
                  </h4>
                  <ol className="reco-steps">
                    {rec.preparation.map((step, k) => (
                      <li key={k}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
