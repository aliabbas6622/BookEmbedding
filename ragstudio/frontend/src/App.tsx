import { useAppStore } from '../store/useAppStore';
import { Sidebar } from './components/Sidebar';
import DashboardPage from './pages/Dashboard';
import UploadPage from './pages/Upload';
import PipelinePage from './pages/Pipeline';
import DocumentsPage from './pages/Documents';
import VectorIndexPage from './pages/VectorIndex';
import RagPlaygroundPage from './pages/RagPlayground';
import ProvidersPage from './pages/Providers';
import SettingsPage from './pages/Settings';

function App() {
  const { currentPage } = useAppStore();

  const renderPage = () => {
    switch (currentPage) {
      case '/':
      case '/dashboard':
        return <DashboardPage />;
      case '/upload':
        return <UploadPage />;
      case '/pipeline':
        return <PipelinePage />;
      case '/documents':
        return <DocumentsPage />;
      case '/vector-index':
        return <VectorIndexPage />;
      case '/rag-playground':
        return <RagPlaygroundPage />;
      case '/providers':
        return <ProvidersPage />;
      case '/settings':
        return <SettingsPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
