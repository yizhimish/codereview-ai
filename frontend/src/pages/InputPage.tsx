import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeCode } from '../services/api';

const InputPage: React.FC = () => {
  const navigate = useNavigate();
  // 暂时只支持代码粘贴，GitHub功能后续添加
  // const [inputType, setInputType] = useState<'github' | 'code'>('github');
  // const [githubUrl, setGithubUrl] = useState('');
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const languages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
    { value: 'cpp', label: 'C++' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // 目前只支持直接粘贴代码
      if (!code.trim()) {
        throw new Error('请输入代码');
      }
      
      const payload = {
        code: code.trim(),
        language: language,
      };

      const response = await analyzeCode(payload);
      
      if (response.job_id) {
        navigate(`/result/${response.job_id}`);
      } else {
        throw new Error('分析任务提交失败');
      }
    } catch (err: any) {
      setError(err.message || '发生错误，请重试');
      console.error('分析错误:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-bold text-gray-900 mb-3">
          智能代码审查
        </h2>
        <p className="text-gray-600">
          使用AI分析代码质量，发现潜在问题，提供改进建议
        </p>
      </div>

      <div className="card mb-8">
        <div className="mb-6">
          <div className="inline-flex items-center px-4 py-2 bg-primary-100 text-primary-800 rounded-full">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            直接粘贴代码（GitHub支持后续版本添加）
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择编程语言
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input"
                disabled={isLoading}
              >
                {languages.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                代码内容
              </label>
              <div className="relative">
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="粘贴你的代码到这里..."
                  className="input font-mono min-h-[200px] w-full resize-y"
                  disabled={isLoading}
                  rows={12}
                  style={{ tabSize: 2 }}
                />
                <div className="absolute top-2 right-2 flex space-x-2">
                  <button
                    type="button"
                    onClick={() => {
                      // 自动格式化代码
                      const formatted = code
                        .replace(/^\s+/gm, '')
                        .replace(/\t/g, '  ');
                      setCode(formatted);
                    }}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                    title="格式化代码"
                  >
                    🔧 格式化
                  </button>
                  <button
                    type="button"
                    onClick={() => setCode('')}
                    className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                    title="清空代码"
                  >
                    🗑️ 清空
                  </button>
                </div>
              </div>
              <div className="flex justify-between items-center mt-2">
                <p className="text-sm text-gray-500">
                  支持最多1000行代码分析 • 当前行数: {code.split('\n').length}
                </p>
                <div className="flex space-x-2">
                  <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
                    Tab缩进
                  </span>
                  <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
                    语法高亮（后续版本）
                  </span>
                </div>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-danger-50 border border-danger-200 rounded-lg">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-danger-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-danger-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="mt-8 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              分析{languages.find(l => l.value === language)?.label}代码
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary px-8 py-3 text-lg font-semibold"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  提交中...
                </div>
              ) : (
                '开始分析'
              )}
            </button>
          </div>
        </form>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="card">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">代码质量</h3>
          <p className="text-gray-600">
            检查代码规范、复杂度、重复代码等质量指标
          </p>
        </div>

        <div className="card">
          <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">安全检测</h3>
          <p className="text-gray-600">
            发现潜在的安全漏洞和敏感信息泄露
          </p>
        </div>

        <div className="card">
          <div className="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-warning-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">性能优化</h3>
          <p className="text-gray-600">
            识别性能瓶颈，提供优化建议
          </p>
        </div>
      </div>
    </div>
  );
};

export default InputPage;