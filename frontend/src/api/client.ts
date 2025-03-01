import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,  // Important for CORS with credentials
  headers: {
    'Content-Type': 'application/json',
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  // For login, we need to set the content type specifically
  const response = await api.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const register = async (userData: { username: string; email: string; password: string }) => {
  const response = await api.post('/auth/register', userData);
  return response.data;
};

export const transcribeVideo = async (videoUrl: string) => {
  const response = await api.post('/transcript/transcribe', { video_url: videoUrl });
  return response.data;
};

export const getTranscriptionStatus = async (videoId: string) => {
  const response = await api.get(`/transcript/status/${videoId}`);
  return response.data;
};

export const askQuestion = async (videoId: string, question: string) => {
  const response = await api.post('/query/ask-question', { video_id: videoId, question });
  return response.data;
};

export const logout = async () => {
  try {
    const response = await api.post('/auth/logout');
    // Clear the token from localStorage
    localStorage.removeItem('token');
    return response.data;
  } catch (error) {
    console.error('Logout error:', error);
    // Still remove the token even if the API call fails
    localStorage.removeItem('token');
    throw error;
  }
};

export const getQueryHistory = async (videoId: string) => {
  const response = await api.get(`/query/history/${videoId}`);
  return response.data;
};

export default api; 