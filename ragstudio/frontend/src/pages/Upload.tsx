import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { documentsApi, jobsApi } from '../lib/api';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [autoStart, setAutoStart] = useState(true);
  const { addDocument, setActiveJob } = useAppStore();

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const response = await documentsApi.upload(file);
      return response.data;
    },
    onSuccess: (data) => {
      addDocument(data);
      if (autoStart) {
        startJob(data.id);
      }
      setSelectedFile(null);
    },
  });

  const startJob = async (documentId: string) => {
    try {
      const response = await jobsApi.create(documentId);
      setActiveJob(response.data);
    } catch (error) {
      console.error('Failed to start job:', error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Upload Documents</h1>
        <p className="text-gray-500 mt-2">Upload PDF documents for processing</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Upload File</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-gray-400 transition-colors"
            >
              <div className="text-6xl mb-4">📤</div>
              <p className="text-lg font-medium text-gray-900 mb-2">
                Drag and drop your file here
              </p>
              <p className="text-sm text-gray-500 mb-4">or</p>
              <label className="inline-block">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <span className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md cursor-pointer hover:bg-gray-200 transition-colors">
                  Browse Files
                </span>
              </label>
              {selectedFile && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              )}
            </div>

            <div className="mt-6 flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={autoStart}
                  onChange={(e) => setAutoStart(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm text-gray-700">Auto-start pipeline</span>
              </label>
            </div>

            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploadMutation.isPending}
              className="w-full mt-6"
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload Document'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Supported Formats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">PDF Documents</h4>
                <p className="text-sm text-gray-600">
                  Native PDF files with text content. OCR will be applied automatically 
                  for scanned documents.
                </p>
              </div>
              
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Processing Pipeline</h4>
                <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                  <li>Document Split (multi-page PDFs)</li>
                  <li>OCR (Optical Character Recognition)</li>
                  <li>LLM Correction (optional)</li>
                  <li>Text Cleaning</li>
                  <li>Chunking</li>
                  <li>Embedding Generation</li>
                  <li>Vector Index Storage</li>
                </ol>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-2">💡 Tips</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Large files will be split by pages</li>
                  <li>• Processing time depends on document size</li>
                  <li>• You can monitor progress in the Pipeline page</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
