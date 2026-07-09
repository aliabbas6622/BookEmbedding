'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { ArrowRight, BookOpen, Zap, Shield, Globe } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const features = [
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'TurboVec quantization for 16x faster vector search with minimal accuracy loss',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Supabase Auth with RLS, encrypted API keys, and secure device registration',
    },
    {
      icon: Globe,
      title: 'Multi-Device Sync',
      description: 'Process on desktop, monitor from anywhere with realtime synchronization',
    },
    {
      icon: BookOpen,
      title: 'Smart Processing',
      description: 'OCR, LLM correction, chunking, embeddings - all in one pipeline',
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-blue-600">RAG Studio</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/login')}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              Sign In
            </button>
            <button
              onClick={() => router.push('/signup')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Production-Ready RAG
            <br />
            <span className="text-blue-600">Document Intelligence</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            Process thousands of documents with OCR, embeddings, and vector search.
            Monitor from any device with realtime updates. Built for scale.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => router.push(isAuthenticated ? '/dashboard' : '/signup')}
              className="bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
            >
              Start Processing <ArrowRight size={20} />
            </button>
            <button className="bg-white text-gray-900 px-8 py-4 rounded-lg font-semibold text-lg border-2 border-gray-200 hover:border-gray-300 transition-all">
              View Documentation
            </button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Everything You Need for Document AI
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="p-6 rounded-xl border hover:shadow-lg transition-shadow"
              >
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="text-blue-600" size={24} />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h4>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-gray-900 text-white">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <p className="text-4xl font-bold text-blue-400 mb-2">16x</p>
              <p className="text-gray-400">Faster Vector Search</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-green-400 mb-2">100%</p>
              <p className="text-gray-400">Resumable Pipelines</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-purple-400 mb-2">∞</p>
              <p className="text-gray-400">Scalable Architecture</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <h3 className="text-3xl font-bold text-gray-900 mb-6">
            Ready to Transform Your Documents?
          </h3>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Join developers building the next generation of document intelligence applications.
          </p>
          <button
            onClick={() => router.push('/signup')}
            className="bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-700 transition-all"
          >
            Get Started Free
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-gray-600">
              © 2024 RAG Studio. Built with Supabase & Next.js
            </p>
            <div className="flex gap-6">
              <a href="#" className="text-gray-600 hover:text-gray-900">
                Documentation
              </a>
              <a href="#" className="text-gray-600 hover:text-gray-900">
                GitHub
              </a>
              <a href="#" className="text-gray-600 hover:text-gray-900">
                Support
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
