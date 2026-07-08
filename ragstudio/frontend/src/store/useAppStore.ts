import { create } from 'zustand';
import type { Document, Job, Provider, VectorIndex, ChatMessage } from '../types';

interface AppState {
  // Documents
  documents: Document[];
  selectedDocument: Document | null;
  
  // Jobs
  jobs: Job[];
  activeJob: Job | null;
  
  // Providers
  providers: Provider[];
  selectedProvider: Provider | null;
  
  // Vector Indexes
  vectorIndexes: VectorIndex[];
  selectedIndex: VectorIndex | null;
  
  // RAG Playground
  conversations: string[];
  currentConversation: string | null;
  chatMessages: ChatMessage[];
  isChatLoading: boolean;
  
  // UI State
  sidebarOpen: boolean;
  currentPage: string;
  
  // Actions
  setDocuments: (docs: Document[]) => void;
  addDocument: (doc: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  setSelectedDocument: (doc: Document | null) => void;
  
  setJobs: (jobs: Job[]) => void;
  updateJob: (id: string, updates: Partial<Job>) => void;
  setActiveJob: (job: Job | null) => void;
  
  setProviders: (providers: Provider[]) => void;
  setSelectedProvider: (provider: Provider | null) => void;
  
  setVectorIndexes: (indexes: VectorIndex[]) => void;
  set.selectedIndex: (index: VectorIndex | null) => void;
  
  setChatMessages: (messages: ChatMessage[]) => void;
  addChatMessage: (message: ChatMessage) => void;
  setCurrentConversation: (id: string | null) => void;
  setIsChatLoading: (loading: boolean) => void;
  
  setSidebarOpen: (open: boolean) => void;
  setCurrentPage: (page: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  documents: [],
  selectedDocument: null,
  jobs: [],
  activeJob: null,
  providers: [],
  selectedProvider: null,
  vectorIndexes: [],
  selectedIndex: null,
  conversations: [],
  currentConversation: null,
  chatMessages: [],
  isChatLoading: false,
  sidebarOpen: true,
  currentPage: 'dashboard',
  
  // Document actions
  setDocuments: (docs) => set({ documents: docs }),
  addDocument: (doc) => set((state) => ({ documents: [...state.documents, doc] })),
  updateDocument: (id, updates) => set((state) => ({
    documents: state.documents.map(d => d.id === id ? { ...d, ...updates } : d),
    selectedDocument: state.selectedDocument?.id === id 
      ? { ...state.selectedDocument, ...updates } 
      : state.selectedDocument,
  })),
  setSelectedDocument: (doc) => set({ selectedDocument: doc }),
  
  // Job actions
  setJobs: (jobs) => set({ jobs }),
  updateJob: (id, updates) => set((state) => ({
    jobs: state.jobs.map(j => j.id === id ? { ...j, ...updates } : j),
    activeJob: state.activeJob?.id === id 
      ? { ...state.activeJob, ...updates } 
      : state.activeJob,
  })),
  setActiveJob: (job) => set({ activeJob: job }),
  
  // Provider actions
  setProviders: (providers) => set({ providers }),
  setSelectedProvider: (provider) => set({ selectedProvider: provider }),
  
  // Vector Index actions
  setVectorIndexes: (indexes) => set({ vectorIndexes: indexes }),
  setSelectedIndex: (index) => set({ selectedIndex: index }),
  
  // Chat actions
  setChatMessages: (messages) => set({ chatMessages: messages }),
  addChatMessage: (message) => set((state) => ({ 
    chatMessages: [...state.chatMessages, message] 
  })),
  setCurrentConversation: (id) => set({ currentConversation: id }),
  setIsChatLoading: (loading) => set({ isChatLoading: loading }),
  
  // UI actions
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setCurrentPage: (page) => set({ currentPage: page }),
}));
