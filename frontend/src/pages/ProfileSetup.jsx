import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { updateProfile } from '../services/api';

export default function ProfileSetup() {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    age: user?.age || '',
    gender: user?.gender || '',
    weight_kg: user?.weight_kg || '',
    height_cm: user?.height_cm || '',
    activity_level: user?.activity_level || 'moderate',
    goal: user?.goal || 'maintain',
  });

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
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
      navigate('/dashboard');
    } catch (err) {
      console.error('Profile update failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card" style={{ maxWidth: 520 }}>
        <div className="auth-header">
          <div className="auth-logo">⚙️</div>
          <h2>Set Up Your Profile</h2>
          <p>We'll calculate your personalized daily calorie budget</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Age</label>
              <input
                type="number"
                className="form-input"
                placeholder="25"
                value={form.age}
                onChange={(e) => handleChange('age', e.target.value)}
                required
                min="10"
                max="120"
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
                placeholder="70"
                value={form.weight_kg}
                onChange={(e) => handleChange('weight_kg', e.target.value)}
                required
                step="0.1"
                min="20"
                max="300"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Height (cm)</label>
              <input
                type="number"
                className="form-input"
                placeholder="175"
                value={form.height_cm}
                onChange={(e) => handleChange('height_cm', e.target.value)}
                required
                step="0.1"
                min="100"
                max="250"
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
              <option value="sedentary">Sedentary (little or no exercise)</option>
              <option value="light">Light (1-3 days/week)</option>
              <option value="moderate">Moderate (3-5 days/week)</option>
              <option value="active">Active (6-7 days/week)</option>
              <option value="very_active">Very Active (intense daily exercise)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Goal</label>
            <div className="meal-type-selector">
              {[
                { value: 'lose', label: '🔥 Lose Weight', desc: '-500 cal/day' },
                { value: 'maintain', label: '⚖️ Maintain', desc: 'Stay balanced' },
                { value: 'gain', label: '💪 Gain Muscle', desc: '+500 cal/day' },
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

          <button type="submit" className="btn btn-success btn-full btn-lg" disabled={loading}>
            {loading ? 'Calculating...' : 'Calculate My Budget & Start'}
          </button>
        </form>
      </div>
    </div>
  );
}
