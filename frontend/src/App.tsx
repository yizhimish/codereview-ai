import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import InputPage from './pages/InputPage';
import { ResultPage } from './pages/ResultPage';
import './index.css';

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">CR</span>
                </div>
                <h1 className="text-2xl font-bold text-gray-900">
                  CodeReview <span className="text-primary-600">AI</span>
                </h1>
              </div>
              <div className="text-sm text-gray-500">
                v0.1.0 • 全AI智能体公司产品
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Navigate to="/analyze" replace />} />
            <Route path="/analyze" element={<InputPage />} />
            <Route path="/result/:analysisId" element={<ResultPage />} />
          </Routes>
        </main>

        <footer className="bg-white border-t mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="text-gray-600 text-sm">
                © 2026 CodeReview AI • 全AI智能体公司
              </div>
              <div className="flex items-center space-x-4 mt-4 md:mt-0">
                <span className="text-xs text-gray-500">
                  CEO: Spark 🔥
                </span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-success-600">系统运行中</span>
                </div>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
};

export default App;