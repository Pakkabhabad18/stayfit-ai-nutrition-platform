import { createContext, useContext, useState, useCallback, useRef } from 'react';
import { getTodayMeals, getTaskStatus } from '../services/api';

const MealContext = createContext();

export function MealProvider({ children }) {
  const [latestAnalysis, setLatestAnalysis] = useState(null);
  const [hasUnseenAnalysis, setHasUnseenAnalysis] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [todayMeals, setTodayMeals] = useState(null);
  const lastProcessedTaskIdRef = useRef(null);
  const activeTaskIdRef = useRef(null);
  const fallbackTimerRef = useRef(null);

  const normalizeMealForAnalysis = (meal) => ({
    ...meal,
    total_protein_g: meal.total_protein_g ?? meal.protein_g ?? 0,
    total_carbs_g: meal.total_carbs_g ?? meal.carbs_g ?? 0,
    total_fat_g: meal.total_fat_g ?? meal.fat_g ?? 0,
    provider: meal.provider || 'AI'
  });

  const fetchLatestAnalysis = useCallback(async (mealId = null, taskId = null) => {
    // If we've already processed this task, skip to avoid double updates
    if (taskId && taskId === lastProcessedTaskIdRef.current) return;

    try {
      // 1. Refresh today's meals list (Source of Truth)
      const res = await getTodayMeals();
      const todayData = res.data || {};
      setTodayMeals(todayData);
      
      // 2. If this was triggered by a specific task/meal, find it
      if (taskId || mealId) {
        const allMeals = todayData.meals || [];
        if (allMeals.length > 0) {
          // Find the specific meal by ID if provided, otherwise fallback to the newest
          const latest = mealId 
            ? allMeals.find(m => String(m.id) === String(mealId)) || allMeals[0]
            : allMeals[0];

          // Map to the format the UI expects (handle potential field name differences)
          setLatestAnalysis(normalizeMealForAnalysis(latest));
          setHasUnseenAnalysis(true);
          activeTaskIdRef.current = null;
          if (fallbackTimerRef.current) {
            clearTimeout(fallbackTimerRef.current);
            fallbackTimerRef.current = null;
          }
          if (taskId) lastProcessedTaskIdRef.current = taskId;
        }
      }
      setIsProcessing(false);
    } catch (err) {
      console.error('Failed to fetch latest analysis:', err);
    }
  }, []);

  const dismissAnalysis = useCallback(() => {
    setLatestAnalysis(null);
    setHasUnseenAnalysis(false);
  }, []);

  const clearDraft = useCallback(() => {
    activeTaskIdRef.current = null;
    if (fallbackTimerRef.current) {
      clearTimeout(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
    setLatestAnalysis(null);
    setHasUnseenAnalysis(false);
    setIsProcessing(false);
  }, []);

  const startProcessing = useCallback((taskId) => {
    activeTaskIdRef.current = taskId;
    setIsProcessing(true);
    setLatestAnalysis(null);
    setHasUnseenAnalysis(false);

    if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current);

    const pollTaskStatus = async () => {
      if (activeTaskIdRef.current !== taskId || lastProcessedTaskIdRef.current === taskId) return;

      try {
        console.warn("SSE Timeout: Performing fallback poll for task", taskId);
        const statusRes = await getTaskStatus(taskId);
        const { status, result } = statusRes.data || {};

        if (status === 'SUCCESS') {
          const mealId = result?.meal_id;
          await fetchLatestAnalysis(mealId, taskId);
        } else if (status === 'FAILURE' || status === 'REVOKED') {
          activeTaskIdRef.current = null;
          setIsProcessing(false);
        } else if (activeTaskIdRef.current === taskId) {
          fallbackTimerRef.current = setTimeout(pollTaskStatus, 2000);
        }
      } catch (err) {
        console.error('Fallback task status poll failed:', err);
        if (activeTaskIdRef.current === taskId) {
          fallbackTimerRef.current = setTimeout(pollTaskStatus, 2000);
        }
      }
    };

    fallbackTimerRef.current = setTimeout(pollTaskStatus, 10000);
  }, [fetchLatestAnalysis]);

  const value = {
    latestAnalysis,
    hasUnseenAnalysis,
    isProcessing,
    todayMeals,
    fetchLatestAnalysis,
    startProcessing,
    dismissAnalysis,
    clearDraft,
    setTodayMeals
  };

  return (
    <MealContext.Provider value={value}>
      {children}
    </MealContext.Provider>
  );
}

export function useMeals() {
  const context = useContext(MealContext);
  if (!context) {
    throw new Error('useMeals must be used within a MealProvider');
  }
  return context;
}
