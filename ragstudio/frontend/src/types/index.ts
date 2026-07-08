export interface Document {
  id: string;
  title: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  total_chunks?: number;
  total_pages?: number;
}

export interface Job {
  id: string;
  document_id: string;
  status: 'pending' | 'running' | 'paused' | 'failed' | 'completed' | 'retrying' | 'cancelled';
  stage: 'upload' | 'split' | 'ocr' | 'llm_correction' | 'text_cleaning' | 'chunking' | 'embedding' | 'vector_index';
  progress: number;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

export interface PipelineStage {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  duration?: number;
  error_message?: string;
}

export interface Chunk {
  id: string;
  document_id: string;
  content: string;
  chunk_index: number;
  start_page?: number;
  end_page?: number;
  embedding_provider?: string;
  created_at: string;
}

export interface Provider {
  id: string;
  name: string;
  type: 'ocr' | 'llm' | 'embedding' | 'vector_index';
  provider_name: string;
  is_active: boolean;
  config?: Record<string, any>;
}

export interface ApiKey {
  id: string;
  provider_id: string;
  key: string;
  is_active: boolean;
  last_used?: string;
  quota_limit?: number;
  quota_used?: number;
  cooldown_until?: string;
}

export interface VectorIndex {
  id: string;
  name: string;
  provider: string;
  dimensionality: number;
  total_vectors: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  sources?: RetrievedChunk[];
  latency?: number;
}

export interface RetrievedChunk {
  chunk_id: string;
  content: string;
  score: number;
  document_id: string;
  document_title: string;
}

export interface DashboardStats {
  total_documents: number;
  total_chunks: number;
  total_indexes: number;
  active_jobs: number;
  storage_used: string;
}
