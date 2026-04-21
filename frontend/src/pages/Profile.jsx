import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { updateProfile } from '../services/api';
import { User, Save } from 'lucide-react';

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({
    name: user?.name || '',
    age: user?.age || '',
    gender: user?.gender || '',
    weight_kg: user?.weight_kg || '',
    height_cm: user?.height_cm || '',
    activity_level: user?.activity_level || 'moderate',
    goal: user?.goal || 'maintain',
  });

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await updateProfile({
        ...form,
        age: parseInt(form.age),
        weight_kg: parseFloat(form.weight_kg),
        height_cm: parseFloat(form.height_cm),
      });
      updateUser(res.data.user);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Update failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600 }}>
      <div className="page-header">
        <h1 className="page-title">Profile Settings ⚙️</h1>
        <p className="page-subtitle">Update your health details and recalculate your calorie budget</p>
      </div>

      {/* Current Budget Display */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="stat-icon blue"><User size={24} /></div>
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Your Daily Calorie Budget</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-blue)' }}>
              {user?.daily_calorie_budget || 2000} cal
            </div>
          </div>
        </div>
      </div>

      {saved && (
        <div className="notification-bar success">
          ✅ Profile updated and calorie budget recalculated!
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              type="text"
              className="form-input"
              value={form.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Age</label>
              <input
                type="number"
                className="form-input"
                value={form.age}
                onChange={(e) => handleChange('age', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Gender</label>
              <select
                className="form-select"
                value={form.gender}
                onChange={(e) => handleChange('gender', e.target.value)}
                required
              >
                <option value="">Select</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Weight (kg)</label>
              <input
                type="number"
                className="form-input"
                value={form.weight_kg}
                onChange={(e) => handleChange('weight_kg', e.target.value)}
                step="0.1"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Height (cm)</label>
              <input
                type="number"
                className="form-input"
                value={form.height_cm}
                onChange={(e) => handleChange('height_cm', e.target.value)}
                step="0.1"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Activity Level</label>
            <select
              className="form-select"
              value={form.activity_level}
              onChange={(e) => handleChange('activity_level', e.target.value)}
            >
              <option value="sedentary">Sedentary</option>
              <option value="light">Light</option>
              <option value="moderate">Moderate</option>
              <option value="active">Active</option>
              <option value="very_active">Very Active</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Goal</label>
            <div className="meal-type-selector">
              {[
                { value: 'lose', label: '🔥 Lose Weight' },
                { value: 'maintain', label: '⚖️ Maintain' },
                { value: 'gain', label: '💪 Gain Muscle' },
              ].map((g) => (
                <button
                  key={g.value}
                  type="button"
                  className={`meal-type-btn ${form.goal === g.value ? 'active' : ''}`}
                  onClick={() => handleChange('goal', g.value)}
                  style={{ flex: 1 }}
                >
                  {g.label}
                </button>
              ))}
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            <Save size={18} />
            {loading ? 'Saving...' : 'Save & Recalculate'}
          </button>
        </form>
      </div>
    </div>
  );
}
