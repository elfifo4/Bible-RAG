import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Source {
  ref: string;
  ref_en: string;
  book?: string;
  book_en?: string;
  chapter?: number;
  verse_start?: number;
  verse_end?: number;
  text: string;
  score: number;
  chunk_id: string;
  chunk_type?: string;
}

export interface DebugInfo {
  latency_ms: number;
  top_k: number;
  embedding_model: string;
  retrieval_strategy: string;
}

export interface AskResponse {
  question: string;
  answer: string;
  context: Source[];
  debug?: DebugInfo;
}

export const ask = async (question: string, top_k = 5, debug = true): Promise<AskResponse> => {
  const response = await api.post('/api/ask', { question, top_k, debug });
  return response.data;
};

export const login = async (password: string): Promise<string> => {
  const response = await api.post('/api/login', { password });
  const { access_token } = response.data;
  localStorage.setItem('token', access_token);
  return access_token;
};

export const logout = () => {
  localStorage.removeItem('token');
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};
