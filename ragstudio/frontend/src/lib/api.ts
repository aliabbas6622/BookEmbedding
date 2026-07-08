import axios from 'axios';

const API_BASE_URL = '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Documents API
export const documentsApi = {
  getAll: () => api.get('/documents'),
  getById: (id: string) => api.get(`/documents/${id}`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  delete: (id: string) => api.delete(`/documents/${id}`),
  getChunks: (id: string, page?: number, limit?: number) => 
    api.get(`/documents/${id}/chunks`, { params: { page, limit } }),
};

// Jobs API
export const jobsApi = {
  getAll: () => api.get('/jobs'),
  getById: (id: string) => api.get(`/jobs/${id}`),
  create: (documentId: string) => api.post('/jobs', { document_id: documentId }),
  cancel: (id: string) => api.post(`/jobs/${id}/cancel`),
  retry: (id: string) => api.post(`/jobs/${id}/retry`),
  getProgress: (id: string) => api.get(`/jobs/${id}/progress`),
};

// Pipeline API
export const pipelineApi = {
  getConfig: () => api.get('/pipeline/config'),
  updateConfig: (config: any) => api.put('/pipeline/config', config),
  execute: (documentId: string, config?: any) => api.post('/pipeline/execute', { document_id: documentId, config }),
  getStages: (jobId: string) => api.get(`/pipeline/jobs/${jobId}/stages`),
};

// Providers API
export const providersApi = {
  getAll: (type?: string) => api.get('/providers', { params: { type } }),
  getById: (id: string) => api.get(`/providers/${id}`),
  create: (provider: any) => api.post('/providers', provider),
  update: (id: string, provider: any) => api.put(`/providers/${id}`, provider),
  delete: (id: string) => api.delete(`/providers/${id}`),
  testConnection: (id: string) => api.post(`/providers/${id}/test`),
};

// API Keys API
export const apiKeysApi = {
  getAll: (providerId: string) => api.get(`/providers/${providerId}/keys`),
  create: (providerId: string, keyData: any) => api.post(`/providers/${providerId}/keys`, keyData),
  delete: (providerId: string, keyId: string) => api.delete(`/providers/${providerId}/keys/${keyId}`),
  rotate: (providerId: string, keyId: string) => api.post(`/providers/${providerId}/keys/${keyId}/rotate`),
};

// Vector Index API
export const vectorIndexApi = {
  getAll: () => api.get('/vector-indexes'),
  getById: (id: string) => api.get(`/vector-indexes/${id}`),
  create: (indexData: any) => api.post('/vector-indexes', indexData),
  delete: (id: string) => api.delete(`/vector-indexes/${id}`),
  search: (indexId: string, query: string, topK?: number) => 
    api.post(`/vector-indexes/${indexId}/search`, { query, top_k: topK }),
};

// RAG Playground API
export const ragApi = {
  chat: (conversationId: string | null, message: string, indexIds?: string[]) => 
    api.post('/rag/chat', { conversation_id: conversationId, message, index_ids: indexIds }),
  getConversation: (id: string) => api.get(`/rag/conversations/${id}`),
  getConversations: () => api.get('/rag/conversations'),
  deleteConversation: (id: string) => api.delete(`/rag/conversations/${id}`),
};

// Dashboard API
export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
};

// Settings API
export const settingsApi = {
  getAll: () => api.get('/settings'),
  update: (settings: any) => api.put('/settings', settings),
};
