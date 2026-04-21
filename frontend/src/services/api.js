import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const register = (data) => api.post('/auth/register', data);
export const login = (data) => api.post('/auth/login', data);
export const googleLogin = (data) => api.post('/auth/google', data);
export const getProfile = () => api.get('/auth/profile');
export const updateProfile = (data) => api.put('/auth/profile', data);

// Meals
export const uploadMeal = (formData) =>
  api.post('/meals/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
export const getTodayMeals = () => api.get('/meals/today');
export const deleteMeal = (id) => api.delete(`/meals/${id}`);

// Analytics
export const getDailySummary = () => api.get('/analytics/daily');
export const getWeeklyTrends = () => api.get('/analytics/weekly');
export const getProgress = () => api.get('/analytics/progress');

// Recommendations
export const getRecommendations = (params) =>
  api.get('/recommendations/', { params });

export default api;
