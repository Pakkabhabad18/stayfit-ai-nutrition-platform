import { useEffect, useRef, useState } from 'react';
import { uploadMeal, deleteMeal, logMealText } from '../services/api';
import { Camera, Trash2, Sparkles, X } from 'lucide-react';
import { useMeals } from '../context/MealContext';

export default function MealLogger() {
  const { 
    latestAnalysis, 
    hasUnseenAnalysis,
    isProcessing, 
    todayMeals, 
    fetchLatestAnalysis, 
    startProcessing,
    dismissAnalysis,
    clearDraft
  } = useMeals();

  const [mealType, setMealType] = useState('lunch');
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragover, setDragover] = useState(false);
  const [logMode, setLogMode] = useState('photo');
  const [textDescription, setTextDescription] = useState('');
  const fileInputRef = useRef(null);
  const analysisVisible = Boolean(latestAnalysis && hasUnseenAnalysis);
  const analysisImageSrc = analysisVisible && latestAnalysis?.image_url
    ? `http://localhost:5000${latestAnalysis.image_url}`
    : null;
  const visibleMealImage = preview || analysisImageSrc;
  const analysisVisibleRef = useRef(analysisVisible);
  const analysisSeenRef = useRef(false);
  const seenTimerRef = useRef(null);

  useEffect(() => {
    fetchLatestAnalysis(); // Initial load of Today's Log

    return () => {
      if (seenTimerRef.current) clearTimeout(seenTimerRef.current);
      // Dismiss only after the card was actually visible on Log Meal.
      if (analysisSeenRef.current) dismissAnalysis();
    };
  }, [fetchLatestAnalysis, dismissAnalysis]);

  useEffect(() => {
    analysisVisibleRef.current = analysisVisible;
    if (seenTimerRef.current) {
      clearTimeout(seenTimerRef.current);
      seenTimerRef.current = null;
    }

    if (!analysisVisible) {
      analysisSeenRef.current = false;
      return;
    }

    const markSeen = () => {
      if (document.visibilityState === 'visible') {
        analysisSeenRef.current = true;
      }
    };

    seenTimerRef.current = setTimeout(markSeen, 1000);

    const handleVisibilityChange = () => {
      if (analysisVisibleRef.current) markSeen();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (seenTimerRef.current) clearTimeout(seenTimerRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [analysisVisible]);

  const handleImageSelect = (file) => {
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(file);
      clearDraft();
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
    setImage(null);
    setPreview(null);
    setTextDescription('');
    clearDraft();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleTextUpload = async () => {
    if (!textDescription.trim()) return;
    try {
      const res = await logMealText({
        text: textDescription,
        meal_type: mealType
      });
      
      if (res.status === 202) {
        const taskId = res.data.task_id;
        startProcessing(taskId);
      }
    } catch (err) {
      console.error('Text logging failed:', err);
      alert('Failed to start text analysis. Please try again.');
    }
  };

  const handleUpload = async () => {
    if (!image) return;
    try {
      const formData = new FormData();
      formData.append('image', image);
      formData.append('meal_type', mealType);

      const res = await uploadMeal(formData);
      
      if (res.status === 202) {
        const taskId = res.data.task_id;
        startProcessing(taskId);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Failed to start meal analysis. Please try again.');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this meal entry?')) return;
    try {
      await deleteMeal(id);
      fetchLatestAnalysis();
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
            <h3 className="card-title">Log Your Meal</h3>
          </div>

          {/* Toggle buttons for Photo vs Text */}
          <div className="log-mode-toggle" style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            <button 
              className={`btn ${logMode === 'photo' ? 'btn-primary' : 'btn-outline'}`} 
              onClick={() => { setLogMode('photo'); clearDraft(); }}
              style={{ flex: 1 }}
            >
              📸 Photo
            </button>
            <button 
              className={`btn ${logMode === 'text' ? 'btn-primary' : 'btn-outline'}`} 
              onClick={() => { setLogMode('text'); clearDraft(); }}
              style={{ flex: 1 }}
            >
              ✍️ Text Entry
            </button>
          </div>

          {/* Meal Type Selector */}
          <div className="meal-type-selector">
            {mealTypes.map((t) => (
              <button
                key={t.value}
                className={`meal-type-btn ${mealType === t.value ? 'active' : ''}`}
                onClick={() => {
                  setMealType(t.value);
                  clearImage();
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Input Zone */}
          {logMode === 'text' ? (
            <div className="meal-text-zone" style={{ marginTop: '15px' }}>
              <textarea
                placeholder="E.g., I had a bowl of oatmeal with a handful of almonds and a sliced banana."
                value={textDescription}
                onChange={(e) => setTextDescription(e.target.value)}
                style={{
                  width: '100%',
                  minHeight: '120px',
                  padding: '12px',
                  borderRadius: '8px',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-card)',
                  color: 'var(--text-primary)',
                  resize: 'vertical',
                  marginBottom: '15px',
                  fontFamily: 'inherit'
                }}
              />
              {!analysisVisible && (
                <button
                  className="btn btn-primary btn-full"
                  onClick={handleTextUpload}
                  disabled={isProcessing || !textDescription.trim()}
                >
                  {isProcessing ? (
                    <>
                      <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }}></div>
                      Analyzing Text...
                    </>
                  ) : (
                    <>
                      <Sparkles size={18} />
                      Analyze Text with AI
                    </>
                  )}
                </button>
              )}
            </div>
          ) : (
            <>
              {/* Upload Zone */}
              {!visibleMealImage ? (
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
                  <img
                    src={visibleMealImage}
                    alt={analysisVisible ? 'Analyzed meal' : 'Meal preview'}
                    className="meal-preview"
                  />
                </div>
              )}

              {/* Upload Button */}
              {preview && !analysisVisible && (
                <button
                  className="btn btn-primary btn-full"
                  onClick={handleUpload}
                  disabled={isProcessing}
                  style={{ marginTop: 16 }}
                >
                  {isProcessing ? (
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
            </>
          )}

          {/* Analysis Result */}
          {analysisVisible && (
            <div className="analysis-result">
              <div className="analysis-header">
                <div className="analysis-icon"><Sparkles size={20} /></div>
                <div>
                  <h4 style={{ fontWeight: 600 }}>AI Analysis Complete</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Powered by {latestAnalysis.provider || 'AI'}
                  </p>
                </div>
              </div>

              <ul className="analysis-food-list">
                {latestAnalysis.food_items?.map((item, i) => (
                  <li key={i} className="analysis-food-item">
                    <span>{item.name} <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>({item.portion})</span></span>
                    <span style={{ fontWeight: 600 }}>{item.calories} cal</span>
                  </li>
                ))}
              </ul>

              <div className="analysis-total">
                <span>Total Calories</span>
                <span style={{ color: 'var(--accent-green)' }}>{latestAnalysis.total_calories} cal</span>
              </div>

              <div style={{ display: 'flex', gap: 16, marginTop: 12, justifyContent: 'center' }}>
                <span className="reco-macro" style={{ fontSize: '0.75rem' }}>
                  🥩 P: {latestAnalysis.total_protein_g}g
                </span>
                <span className="reco-macro" style={{ fontSize: '0.75rem' }}>
                  🍞 C: {latestAnalysis.total_carbs_g}g
                </span>
                <span className="reco-macro" style={{ fontSize: '0.75rem' }}>
                  🧈 F: {latestAnalysis.total_fat_g}g
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
