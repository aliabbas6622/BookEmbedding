import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi, documentsApi, jobsApi, vectorIndexApi } from '../lib/api';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

export default function DashboardPage() {
  const { setDocuments, setJobs, setVectorIndexes } = useAppStore();

  const { data: stats } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      const response = await dashboardApi.getStats();
      return response.data;
    },
  });

  const { data: documentsData } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await documentsApi.getAll();
      return response.data;
    },
  });

  const { data: jobsData } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await jobsApi.getAll();
      return response.data;
    },
  });

  const { data: indexesData } = useQuery({
    queryKey: ['vectorIndexes'],
    queryFn: async () => {
      const response = await vectorIndexApi.getAll();
      return response.data;
    },
  });

  useEffect(() => {
    if (documentsData) {
      setDocuments(documentsData);
    }
  }, [documentsData, setDocuments]);

  useEffect(() => {
    if (jobsData) {
      setJobs(jobsData);
    }
  }, [jobsData, setJobs]);

  useEffect(() => {
    if (indexesData) {
      setVectorIndexes(indexesData);
    }
  }, [indexesData, setVectorIndexes]);

  const statsCards = [
    { title: 'Total Documents', value: stats?.total_documents ?? 0, icon: '📚' },
    { title: 'Total Chunks', value: stats?.total_chunks ?? 0, icon: '🔪' },
    { title: 'Vector Indexes', value: stats?.total_indexes ?? 0, icon: '🗂️' },
    { title: 'Active Jobs', value: stats?.active_jobs ?? 0, icon: '⚙️' },
    { title: 'Storage Used', value: stats?.storage_used ?? '0 MB', icon: '💾' },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-2">Overview of your document intelligence platform</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        {statsCards.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {stat.title}
              </CardTitle>
              <span className="text-2xl">{stat.icon}</span>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Documents</CardTitle>
          </CardHeader>
          <CardContent>
            {documentsData && documentsData.length > 0 ? (
              <div className="space-y-4">
                {documentsData.slice(0, 5).map((doc: any) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{doc.title}</p>
                      <p className="text-sm text-gray-500">{doc.filename}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      doc.status === 'completed' ? 'bg-green-100 text-green-700' :
                      doc.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                      doc.status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No documents yet</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            {jobsData && jobsData.length > 0 ? (
              <div className="space-y-4">
                {jobsData.filter((j: any) => j.status === 'running' || j.status === 'pending').slice(0, 5).map((job: any) => (
                  <div key={job.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium text-gray-900">Job #{job.id.slice(0, 8)}</p>
                      <span className="text-sm text-gray-500">{job.stage}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{job.progress}% complete</p>
                  </div>
                ))}
                {jobsData.filter((j: any) => j.status === 'running' || j.status === 'pending').length === 0 && (
                  <p className="text-gray-500 text-center py-8">No active jobs</p>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No jobs yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Button onClick={() => window.location.hash = '/upload'}>
                Upload Document
              </Button>
              <Button variant="outline" onClick={() => window.location.hash = '/rag-playground'}>
                Open RAG Playground
              </Button>
              <Button variant="outline" onClick={() => window.location.hash = '/providers'}>
                Configure Providers
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
