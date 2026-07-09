'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import DashboardLayout from '@/components/DashboardLayout';
import { Activity, Clock, CheckCircle, AlertCircle, Server, HardDrive } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const { jobs, devices, isAuthenticated, fetchJobs, fetchDevices } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchJobs();
    fetchDevices();

    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      fetchJobs();
      fetchDevices();
    }, 5000);

    return () => clearInterval(interval);
  }, [isAuthenticated, router]);

  // Calculate stats
  const activeJobs = jobs.filter(j => j.status === 'running').length;
  const completedJobs = jobs.filter(j => j.status === 'completed').length;
  const failedJobs = jobs.filter(j => j.status === 'failed').length;
  const onlineDevices = devices.filter(d => d.status === 'online' || d.status === 'busy').length;

  const stats = [
    {
      name: 'Active Jobs',
      value: activeJobs,
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Completed',
      value: completedJobs,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Failed',
      value: failedJobs,
      icon: AlertCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      name: 'Online Devices',
      value: onlineDevices,
      icon: Server,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 100) return 'bg-green-500';
    if (progress >= 50) return 'bg-blue-500';
    return 'bg-yellow-500';
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div
              key={stat.name}
              className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                </div>
                <div className={`${stat.bgColor} p-3 rounded-lg`}>
                  <stat.icon className={stat.color} size={24} />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Jobs */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Recent Jobs</h3>
          </div>
          
          {jobs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Clock className="mx-auto mb-4" size={48} />
              <p>No jobs yet. Start processing a document to see it here.</p>
            </div>
          ) : (
            <div className="divide-y">
              {jobs.slice(0, 10).map((job) => (
                <div key={job.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <HardDrive size={20} className="text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">Job {job.id.slice(0, 8)}</p>
                        <p className="text-sm text-gray-500">
                          Stage: {job.current_stage || 'Pending'}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                        job.status
                      )}`}
                    >
                      {job.status}
                    </span>
                  </div>
                  
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600">Progress</span>
                      <span className="font-medium text-gray-900">{job.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(
                          job.progress
                        )}`}
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                  </div>
                  
                  {job.error_message && (
                    <p className="mt-2 text-sm text-red-600">{job.error_message}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Devices */}
        {devices.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900">Connected Devices</h3>
            </div>
            
            <div className="divide-y">
              {devices.map((device) => (
                <div key={device.id} className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Server size={20} className="text-gray-400" />
                    <div>
                      <p className="font-medium text-gray-900">{device.name}</p>
                      <p className="text-sm text-gray-500">
                        {device.os} • {device.ram_gb}GB RAM
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        device.status === 'online' || device.status === 'busy'
                          ? 'bg-green-500'
                          : 'bg-gray-400'
                      }`}
                    />
                    <span className="text-sm font-medium text-gray-600 capitalize">
                      {device.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
