import { create } from 'zustand';
import { supabase } from '@/lib/supabase';

export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
}

export interface Device {
  id: string;
  device_uuid: string;
  name: string;
  os?: string;
  cpu?: string;
  ram_gb?: number;
  gpu?: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  last_heartbeat?: string;
  software_version?: string;
}

export interface Job {
  id: string;
  user_id: string;
  device_id?: string;
  book_id?: string;
  priority: number;
  status: 'pending' | 'queued' | 'running' | 'paused' | 'retrying' | 'completed' | 'cancelled' | 'failed';
  current_stage?: string;
  progress: number;
  eta_seconds?: number;
  retry_count: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

interface AuthState {
  user: User | null;
  devices: Device[];
  jobs: Job[];
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  fetchDevices: () => Promise<void>;
  fetchJobs: () => Promise<void>;
  subscribeToJobUpdates: (jobId: string) => void;
  unsubscribeFromJobUpdates: (jobId: string) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  devices: [],
  jobs: [],
  isLoading: false,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;

      const user: User = {
        id: data.user.id,
        email: data.user.email || '',
        full_name: data.user.user_metadata?.full_name,
        avatar_url: data.user.user_metadata?.avatar_url,
      };

      set({ user, isAuthenticated: true, isLoading: false });
      
      // Fetch associated data
      get().fetchDevices();
      get().fetchJobs();
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      set({ isLoading: false });
      return false;
    }
  },

  logout: async () => {
    await supabase.auth.signOut();
    set({ 
      user: null, 
      devices: [], 
      jobs: [], 
      isAuthenticated: false 
    });
  },

  fetchDevices: async () => {
    const { user } = get();
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from('devices')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;

      set({ devices: data || [] });
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    }
  },

  fetchJobs: async () => {
    const { user } = get();
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from('jobs')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(50);

      if (error) throw error;

      set({ jobs: data || [] });
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  },

  subscribeToJobUpdates: (jobId: string) => {
    const channel = supabase
      .channel(`jobs:${jobId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'jobs',
          filter: `id=eq.${jobId}`,
        },
        (payload) => {
          const { jobs } = get();
          const updatedJobs = jobs.map(job => 
            job.id === payload.new.id ? { ...job, ...payload.new } : job
          );
          set({ jobs: updatedJobs });
        }
      )
      .subscribe();

    // Store channel reference for cleanup (in a real app, use a Map)
    return () => {
      supabase.removeChannel(channel);
    };
  },

  unsubscribeFromJobUpdates: (jobId: string) => {
    supabase.removeChannel(`jobs:${jobId}`);
  },
}));
