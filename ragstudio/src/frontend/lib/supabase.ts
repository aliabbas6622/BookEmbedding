import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase credentials not configured. Cloud features disabled.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Realtime subscription helper
export function subscribeToJobUpdates(jobId: string, callback: (data: any) => void) {
  return supabase
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
        callback(payload.new);
      }
    )
    .subscribe();
}

export function subscribeToNotifications(userId: string, callback: (data: any) => void) {
  return supabase
    .channel(`notifications:${userId}`)
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'notifications',
        filter: `user_id=eq.${userId}`,
      },
      (payload) => {
        callback(payload.new);
      }
    )
    .subscribe();
}

export function subscribeToDeviceUpdates(deviceId: string, callback: (data: any) => void) {
  return supabase
    .channel(`devices:${deviceId}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'devices',
        filter: `id=eq.${deviceId}`,
      },
      (payload) => {
        callback(payload.new);
      }
    )
    .subscribe();
}
