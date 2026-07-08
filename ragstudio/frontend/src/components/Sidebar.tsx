import { Sidebar, Menu, MenuItem } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { cn } from '../lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Upload', href: '/upload', icon: '📤' },
  { name: 'Pipeline', href: '/pipeline', icon: '⚙️' },
  { name: 'Documents', href: '/documents', icon: '📚' },
  { name: 'Vector Index', href: '/vector-index', icon: '🗂️' },
  { name: 'RAG Playground', href: '/rag-playground', icon: '🎮' },
  { name: 'Providers', href: '/providers', icon: '🔌' },
  { name: 'Settings', href: '/settings', icon: '🔧' },
];

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const { sidebarOpen, currentPage, setCurrentPage } = useAppStore();

  if (!sidebarOpen) return null;

  return (
    <div className={cn(
      "w-64 bg-white border-r border-gray-200 h-full flex flex-col",
      className
    )}>
      {/* Logo */}
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">RAG Studio</h1>
        <p className="text-sm text-gray-500 mt-1">Document Intelligence Platform</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = currentPage === item.href || 
            (currentPage === '/' && item.href === '/') ||
            (currentPage !== '/' && item.href !== '/' && currentPage.startsWith(item.href));
          
          return (
            <button
              key={item.name}
              onClick={() => setCurrentPage(item.href)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <span className="text-lg">{item.icon}</span>
              {item.name}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <p>RAG Studio v0.0.1</p>
          <p className="mt-1">© 2024 All rights reserved</p>
        </div>
      </div>
    </div>
  );
}
