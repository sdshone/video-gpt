import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
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
  const response = await api.post('/auth/login', formData);
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

export default api; 