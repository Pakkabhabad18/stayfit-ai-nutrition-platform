import { useState, useRef } from 'react';
import { uploadMeal, getTodayMeals, deleteMeal, getTaskStatus } from '../services/api';
import { Camera, Upload, Trash2, Sparkles, X } from 'lucide-react';
import { useEffect } from 'react';

export default function MealLogger() {
  const [mealType, setMealType] = useState('lunch');
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [todayMeals, setTodayMeals] = useState(null);
  const [dragover, setDragover] = useState(false);
  const fileInputRef = useRef(null);

  const getUserId = () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      // Check for various common ID field names
      return user.id || user._id || user.user_id || 'guest';
    } catch (e) {
      return 'guest';
    }
  };

  useEffect(() => {
    loadTodayMeals();
    // Restore analysis and preview from localStorage if they exist (user-specific)
    const userId = getUserId();
    
    const savedAnalysis = localStorage.getItem(`lastAnalysis_${userId}`);
    const savedPreview = localStorage.getItem(`lastPreview_${userId}`);
    
    if (savedAnalysis) {
      try {
        setAnalysis(JSON.parse(savedAnalysis));
        if (savedPreview) setPreview(savedPreview);
      } catch (e) {
        localStorage.removeItem(`lastAnalysis_${userId}`);
        localStorage.removeItem(`lastPreview_${userId}`);
      }
    }
  }, []);

  const saveAnalysis = (data, previewData = null) => {
    setAnalysis(data);
    const userId = getUserId();

    if (data) {
      localStorage.setItem(`lastAnalysis_${userId}`, JSON.stringify(data));
      if (previewData) {
        localStorage.setItem(`lastPreview_${userId}`, previewData);
      }
    } else {
      localStorage.removeItem(`lastAnalysis_${userId}`);
      localStorage.removeItem(`lastPreview_${userId}`);
    }
  };

  const loadTodayMeals = async () => {
    try {
      const res = await getTodayMeals();
      setTodayMeals(res.data);
    } catch (err) {
      console.error('Failed to load meals:', err);
    }
  };

  const handleImageSelect = (file) => {
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(file);
      saveAnalysis(null);
    }
  };

  const handleFileChange = (e) => {
    handleImageSelect(e.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragover(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleImageSelect(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragover(true);
  };

  const handleDragLeave = () => {
    setDragover(false);
  };

  const clearImage = () => {
    const userId = getUserId();
    
    setImage(null);
    setPreview(null);
    saveAnalysis(null);
    localStorage.removeItem(`lastPreview_${userId}`);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const pollTaskStatus = async (taskId) => {
    try {
      const res = await getTaskStatus(taskId);
      const { status, result, error } = res.data;

      // SUCCESS is the standard Celery state
      if (status === 'SUCCESS') {
        // Our task returns { status: 'completed', analysis: { ... }, ... }
        if (result) {
          saveAnalysis(result.analysis, preview);
          
          // In-Band Notification Engine: Read alerts directly from the response!
          if (result.alerts && result.alerts.length > 0) {
            import('react-hot-toast').then(({ default: toast }) => {
              result.alerts.forEach((alertMsg) => {
                toast(alertMsg, {
                  duration: 8000,
                  icon: '🎉',
                  style: {
                    border: '2px solid var(--accent-red)',
                    padding: '16px',
                    color: 'var(--text-primary)',
                    background: 'var(--bg-card)'
                  }
                });
              });
            });
          }
          loadTodayMeals();
        }
        setUploading(false);
      } else if (status === 'FAILURE' || status === 'REVOKED') {
        console.error('Analysis failed:', error);
        alert(`Analysis failed: ${error || 'The background task was cancelled or failed.'}`);
        setUploading(false);
      } else {
        // PENDING or STARTED: poll again in 1 second
        setTimeout(() => pollTaskStatus(taskId), 1000);
      }
    } catch (err) {
      console.error('Polling failed:', err);
      // Don't stop on a single network error, try again
      setTimeout(() => pollTaskStatus(taskId), 2000);
    }
  };

  const handleUpload = async () => {
    if (!image) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('image', image);
      formData.append('meal_type', mealType);

      const res = await uploadMeal(formData);
      
      if (res.status === 202) {
        // Start polling for background task completion
        pollTaskStatus(res.data.task_id);
      } else {
        // Fallback for direct response if any
        setAnalysis(res.data.analysis);
        loadTodayMeals();
        setUploading(false);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Failed to start meal analysis. Please try again.');
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this meal entry?')) return;
    try {
      await deleteMeal(id);
      loadTodayMeals();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const mealTypes = [
    { value: 'breakfast', label: '🌅 Breakfast' },
    { value: 'lunch', label: '☀️ Lunch' },
    { value: 'dinner', label: '🌙 Dinner' },
    { value: 'snack', label: '🍿 Snack' },
  ];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Log a Meal 📸</h1>
        <p className="page-subtitle">Take a photo of your food and let AI analyze the calories</p>
      </div>

      <div className="grid-2">
        {/* Upload Section */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Upload Meal Photo</h3>
          </div>

          {/* Meal Type Selector */}
          <div className="meal-type-selector">
            {mealTypes.map((t) => (
              <button
                key={t.value}
                className={`meal-type-btn ${mealType === t.value ? 'active' : ''}`}
                onClick={() => setMealType(t.value)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Upload Zone */}
          {!preview ? (
            <div
              className={`meal-upload-zone ${dragover ? 'dragover' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleFileChange}
              />
              <div className="upload-icon"><Camera size={48} /></div>
              <p className="upload-text">Click or drag to upload a meal photo</p>
              <p className="upload-hint">Supports JPG, PNG, WebP • Max 16MB</p>
            </div>
          ) : (
            <div style={{ position: 'relative', textAlign: 'center' }}>
              <button
                onClick={clearImage}
                style={{
                  position: 'absolute', top: 8, right: 8, zIndex: 2,
                  background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%',
                  width: 32, height: 32, cursor: 'pointer', color: 'white',
                  display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}
              >
                <X size={16} />
              </button>
              <img src={preview} alt="Meal preview" className="meal-preview" />
            </div>
          )}

          {/* Upload Button */}
          {preview && !analysis && (
            <button
              className="btn btn-primary btn-full"
              onClick={handleUpload}
              disabled={uploading}
              style={{ marginTop: 16 }}
            >
              {uploading ? (
                <>
                  <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }}></div>
                  Analyzing with AI...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Analyze with AI
                </>
              )}
            </button>
          )}

          {/* Analysis Result */}
          {analysis && (
            <div className="analysis-result">
              <div className="analysis-header">
                <div className="analysis-icon"><Sparkles size={20} /></div>
                <div>
                  <h4 style={{ fontWeight: 600 }}>AI Analysis Complete</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Powered by Gemini 1.5 Flash
                  </p>
                </div>
              </div>

              <ul className="analysis-food-list">
                {analysis.food_items?.map((item, i) => (
                  <li key={i} className="analysis-food-item">
                    <span>{item.name} <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({item.portion})</span></span>
                    <span style={{ fontWeight: 600 }}>{item.calories} cal</span>
                  </li>
                ))}
              </ul>

              <div className="analysis-total">
                <span>Total Calories</span>
                <span style={{ color: 'var(--accent-green)' }}>{analysis.total_calories} cal</span>
              </div>

              <div style={{ display: 'flex', gap: 16, marginTop: 12, justifyContent: 'center' }}>
                <span className="reco-macro" style={{ fontSize: '0.75rem' }}>
                  🥩 P: {analysis.total_protein_g}g
                </span>
                <span className="reco-macro" style={{ fontSize: '0.75rem' }}>
                  🍞 C: {analysis.total_carbs_g}g
                </span>
                <span className="reco-macro" style={{ fontSize: '0.75rem' }}>
                  🧈 F: {analysis.total_fat_g}g
                </span>
              </div>

              <button
                className="btn btn-success btn-full"
                onClick={clearImage}
                style={{ marginTop: 16 }}
              >
                Log Another Meal
              </button>
            </div>
          )}
        </div>

        {/* Today's Meals */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Today's Log</h3>
            {todayMeals?.summary && (
              <span style={{
                background: 'var(--gradient-primary)',
                padding: '4px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.8rem',
                fontWeight: 600
              }}>
                {todayMeals.summary.total_calories} / {todayMeals.summary.budget} cal
              </span>
            )}
          </div>

          {(!todayMeals?.meals || todayMeals.meals.length === 0) ? (
            <div className="empty-state">
              <div className="empty-state-icon">🍽️</div>
              <h3>No meals logged yet</h3>
              <p>Upload a photo of your meal to get started!</p>
            </div>
          ) : (
            <>
              {['breakfast', 'lunch', 'dinner', 'snack'].map((type) => {
                const typeMeals = todayMeals.categorized?.[type] || [];
                if (typeMeals.length === 0) return null;

                const emojis = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '🍿' };
                return (
                  <div key={type} className="meals-section">
                    <div className="meals-section-title">
                      {emojis[type]} {type.charAt(0).toUpperCase() + type.slice(1)}
                    </div>
                    {typeMeals.map((meal) => (
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
                            P: {meal.protein_g}g · C: {meal.carbs_g}g · F: {meal.fat_g}g
                          </div>
                        </div>
                        <div className="meal-item-calories">{meal.total_calories} cal</div>
                        <button className="meal-item-delete" onClick={() => handleDelete(meal.id)}>
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                );
              })}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
