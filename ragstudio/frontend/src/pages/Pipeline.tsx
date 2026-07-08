import { useQuery } from '@tanstack/react-query';
import { jobsApi, pipelineApi } from '../lib/api';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

const STAGES = ['upload', 'split', 'ocr', 'llm_correction', 'text_cleaning', 'chunking', 'embedding', 'vector_index'];

export default function PipelinePage() {
  const { activeJob } = useAppStore();

  const { data: jobs } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await jobsApi.getAll();
      return response.data;
    },
  });

  const getStageStatus = (job: any, stageIndex: number) => {
    const currentStageIndex = STAGES.indexOf(job.stage);
    if (currentStageIndex > stageIndex) return 'completed';
    if (currentStageIndex === stageIndex && job.status === 'running') return 'running';
    if (currentStageIndex < stageIndex) return 'pending';
    return 'pending';
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Pipeline Management</h1>
        <p className="text-gray-500 mt-2">Monitor and manage document processing pipelines</p>
      </div>

      {activeJob && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Active Job</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">Job #{activeJob.id.slice(0, 8)}</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  activeJob.status === 'running' ? 'bg-blue-100 text-blue-700' :
                  activeJob.status === 'completed' ? 'bg-green-100 text-green-700' :
                  activeJob.status === 'failed' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {activeJob.status}
                </span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-blue-600 h-3 rounded-full transition-all"
                  style={{ width: `${activeJob.progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">{activeJob.progress}% complete - Stage: {activeJob.stage}</p>

              {/* Pipeline Visualization */}
              <div className="flex items-center gap-2 overflow-x-auto py-4">
                {STAGES.map((stage, index) => {
                  const status = getStageStatus(activeJob, index);
                  return (
                    <div key={stage} className="flex items-center flex-shrink-0">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                        status === 'completed' ? 'bg-green-500 border-green-500 text-white' :
                        status === 'running' ? 'bg-blue-500 border-blue-500 text-white animate-pulse' :
                        'bg-gray-100 border-gray-300 text-gray-400'
                      }`}>
                        {index + 1}
                      </div>
                      {index < STAGES.length - 1 && (
                        <div className={`w-8 h-0.5 ${
                          status === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                        }`} />
                      )}
                      <span className="ml-2 text-xs font-medium text-gray-600 capitalize whitespace-nowrap">
                        {stage.replace('_', ' ')}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>All Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {jobs && jobs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Job ID</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Document</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Stage</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Progress</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job: any) => (
                    <tr key={job.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-mono text-gray-900">#{job.id.slice(0, 8)}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">Doc #{job.document_id.slice(0, 8)}</td>
                      <td className="py-3 px-4 text-sm text-gray-600 capitalize">{job.stage.replace('_', ' ')}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          job.status === 'running' ? 'bg-blue-100 text-blue-700' :
                          job.status === 'completed' ? 'bg-green-100 text-green-700' :
                          job.status === 'failed' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          {job.status === 'failed' && (
                            <Button size="sm" variant="outline">Retry</Button>
                          )}
                          {job.status === 'running' && (
                            <Button size="sm" variant="outline">Cancel</Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No jobs yet</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
