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

export interface Chunk {
  chunk_id: string;
  text: string;
  display_text: string;
  score: number;
  dense_score?: number;
  lexical_score?: number;
  metadata: Record<string, any>;
}

export interface DebugInfo {
  latency_ms: number;
  top_k: number;
  embedding_model: string;
  retrieval_strategy: string;
  query_type?: string;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: string[];
  retrieved_chunks: Chunk[];
  context: Chunk[];
  debug?: DebugInfo;
}

export interface StrategyMetrics {
  strategy: string;
  questions_count: number;
  hit_at_1: number;
  hit_at_3: number;
  hit_at_5: number;
  recall_at_5: number;
  mrr: number;
}

export interface EvalSummaryResponse {
  strategies: Record<string, StrategyMetrics>;
  metadata?: {
    last_run: string;
    total_questions: number;
  };
}

export interface QuestionEvalResult {
  question: string;
  strategy: string;
  relevant_found: boolean;
  first_relevant_rank?: number;
  hit_at_1: boolean;
  hit_at_3: boolean;
  hit_at_5: boolean;
  recall_at_5: number;
  mrr: number;
  retrieved_refs: string[];
  expected?: any;
}

export interface EvalQuestionsResponse {
  results: QuestionEvalResult[];
}

export interface AnswerEvalResult {
  question: string;
  reference_answer: string;
  generated_answer: string;
  sources: string[];
  retrieved_refs: string[];
  strategy: string;
  contains_reference_answer: boolean;
  has_sources: boolean;
  manual_score: string;
  manual_notes: string;
}

export interface EvalAnswersResponse {
  results: AnswerEvalResult[];
}

export const getEvalSummary = async (): Promise<EvalSummaryResponse> => {
  const response = await api.get('/api/eval/summary');
  return response.data;
};

export const getEvalQuestions = async (strategy = 'hybrid'): Promise<EvalQuestionsResponse> => {
  const response = await api.get(`/api/eval/questions?strategy=${strategy}`);
  return response.data;
};

export const getEvalAnswers = async (strategy = 'hybrid'): Promise<EvalAnswersResponse> => {
  const response = await api.get(`/api/eval/answers?strategy=${strategy}`);
  return response.data;
};

export interface AblationResults {
  available: boolean;
  message?: string;
  results?: {
    retrieval_strategy_ablation: any[];
    top_k_ablation: any[];
  };
}

export const getEvalAblation = async (): Promise<AblationResults> => {
  const response = await api.get('/api/eval/ablation');
  return response.data;
};

export interface ErrorAnalysisResults {
  available: boolean;
  message?: string;
  results?: {
    summary: {
      total_failures: number;
      by_category: Record<string, number>;
    };
    failures: any[];
  };
}

export const getEvalErrors = async (): Promise<ErrorAnalysisResults> => {
  const response = await api.get('/api/eval/errors');
  return response.data;
};

export interface CompareResponse {
  question: string;
  results: Record<string, AskResponse>;
  total_latency_ms: number;
}

export const ask = async (
  question: string,
  top_k = 5,
  debug = true,
  retrieval_strategy = "hybrid"
): Promise<AskResponse> => {
  const response = await api.post('/api/ask', {
    question,
    top_k,
    debug,
    retrieval_strategy
  });
  return response.data;
};

export const compare = async (
  question: string,
  top_k = 5,
  strategies = ["hybrid", "dense_only", "lexical_only"]
): Promise<CompareResponse> => {
  const response = await api.post('/api/compare', {
    question,
    top_k,
    strategies
  });
  return response.data;
};

// --- Agent ("חברותא") chat ---

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface TraceStep {
  step: number;
  type: 'tool_call' | 'final_answer' | 'fallback';
  tool: string | null;
  label: string;
  args: Record<string, any> | null;
  summary: string;
  confidence: 'high' | 'medium' | 'low';
}

export interface NumberedVerse {
  ref: string;
  text: string;
  word_count: number;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  trace: TraceStep[];
  verses?: NumberedVerse[];
}

export const chat = async (messages: ChatMessage[]): Promise<ChatResponse> => {
  const response = await api.post('/api/chat', { messages });
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
