import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getAnalysisResult } from '../services/api';

interface AnalysisResult {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  result?: {
    metrics: {
      lines_of_code: number;
      cyclomatic_complexity: number;
      maintainability_index: number;
    };
    issues: Array<{
      type: 'style' | 'security' | 'best_practice';
      line: number;
      message: string;
      severity: 'low' | 'medium' | 'high';
    }>;
    suggestions: string[];
    grade: 'A' | 'B' | 'C' | 'D' | 'F';
  };
}

export const ResultPage: React.FC = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchResult = async () => {
      if (!analysisId) {
        setError('无效的任务ID');
        setLoading(false);
        return;
      }

      try {
        // 调用后端API
        const data = await getAnalysisResult(analysisId);
        setResult(data);
        
        // 如果还在处理中，设置轮询
        if (data.status === 'processing') {
          const pollInterval = setInterval(async () => {
            try {
              const updatedData = await getAnalysisResult(analysisId);
              setResult(updatedData);
              
              if (updatedData.status !== 'processing') {
                clearInterval(pollInterval);
              }
            } catch (err) {
              console.error('轮询错误:', err);
            }
          }, 3000); // 每3秒轮询一次
          
          // 清理函数
          return () => clearInterval(pollInterval);
        }
        
      } catch (err: any) {
        setError(err.message || '获取分析结果失败');
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [analysisId]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="card text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600 mb-4"></div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">正在分析代码...</h3>
          <p className="text-gray-600">AI正在仔细审查你的代码，请稍候</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="card">
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">获取结果失败</h3>
            <p className="text-gray-600 mb-6">{error || '未知错误'}</p>
            <Link to="/analyze" className="btn btn-primary">
              返回重新分析
            </Link>
          </div>
        </div>
      </div>
    );
  }
  
  // 处理中的状态
  if (result.status === 'processing') {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="card text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600 mb-4"></div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">代码分析处理中</h3>
          <p className="text-gray-600 mb-6">任务ID: {result.job_id}</p>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div 
              className="bg-primary-600 h-2 rounded-full transition-all duration-500"
              style={{ width: '60%' }}
            ></div>
          </div>
          <p className="text-gray-500 text-sm">正在分析代码，请稍候...</p>
        </div>
      </div>
    );
  }
  
  // 失败状态
  if (result.status === 'failed') {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="card">
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">分析失败</h3>
            <p className="text-gray-600 mb-6">任务ID: {result.job_id}</p>
            <Link to="/analyze" className="btn btn-primary">
              返回重新分析
            </Link>
          </div>
        </div>
      </div>
    );
  }
  
  // 完成状态但没有结果
  if (!result.result) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="card">
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">分析完成但无结果</h3>
            <p className="text-gray-600 mb-6">任务ID: {result.job_id}</p>
            <Link to="/analyze" className="btn btn-primary">
              返回重新分析
            </Link>
          </div>
        </div>
      </div>
    );
  }
  
  const analysis = result.result;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">代码分析结果</h2>
          <p className="text-gray-600">
            任务ID: {result.job_id} • 分析完成
          </p>
        </div>
        <Link to="/analyze" className="btn btn-secondary">
          分析新代码
        </Link>
      </div>

      {/* 总体评分卡片 */}
      <div className="card mb-8">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="mb-6 md:mb-0">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">代码评分</h3>
            <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${
              analysis.grade === 'A' ? 'text-green-600 bg-green-100' :
              analysis.grade === 'B' ? 'text-green-500 bg-green-50' :
              analysis.grade === 'C' ? 'text-yellow-600 bg-yellow-100' :
              analysis.grade === 'D' ? 'text-yellow-700 bg-yellow-200' :
              'text-red-600 bg-red-100'
            } text-3xl font-bold`}>
              {analysis.grade}
            </div>
            <p className="mt-2 text-gray-600 text-sm">
              {analysis.grade === 'A' ? '优秀' : 
               analysis.grade === 'B' ? '良好' : 
               analysis.grade === 'C' ? '一般' : 
               analysis.grade === 'D' ? '需要改进' : '不合格'}
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 text-blue-600 text-xl font-bold mb-2">
                {analysis.metrics.lines_of_code}
              </div>
              <p className="text-sm font-medium text-gray-700">代码行数</p>
            </div>
            <div className="text-center">
              <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${
                analysis.metrics.cyclomatic_complexity > 10 ? 'bg-yellow-100 text-yellow-600' : 'bg-green-100 text-green-600'
              } text-xl font-bold mb-2`}>
                {analysis.metrics.cyclomatic_complexity.toFixed(1)}
              </div>
              <p className="text-sm font-medium text-gray-700">圈复杂度</p>
            </div>
            <div className="text-center">
              <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${
                analysis.metrics.maintainability_index > 80 ? 'bg-green-100 text-green-600' : 
                analysis.metrics.maintainability_index > 60 ? 'bg-yellow-100 text-yellow-600' : 'bg-red-100 text-red-600'
              } text-xl font-bold mb-2`}>
                {analysis.metrics.maintainability_index.toFixed(0)}
              </div>
              <p className="text-sm font-medium text-gray-700">可维护性指数</p>
            </div>
          </div>
        </div>
      </div>

      {/* 问题列表 */}
      <div className="card mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">发现的问题 ({analysis.issues.length}个)</h3>
        <div className="space-y-4">
          {analysis.issues.map((issue, index) => (
            <div key={index} className="border rounded-lg overflow-hidden">
              <div className={`px-4 py-3 border-b ${
                issue.type === 'security' ? 'bg-red-50 text-red-700 border-red-200' :
                issue.type === 'best_practice' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                'bg-green-50 text-green-700 border-green-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className={`badge ${
                      issue.severity === 'high' ? 'badge-danger' :
                      issue.severity === 'medium' ? 'badge-warning' :
                      'bg-blue-100 text-blue-800'
                    } capitalize`}>
                      {issue.severity}
                    </span>
                    <span className="font-medium text-gray-900">
                      {issue.type === 'style' ? '代码风格' : 
                       issue.type === 'security' ? '安全问题' : '最佳实践'}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">第 {issue.line} 行</span>
                </div>
              </div>
              <div className="p-4">
                <p className="text-gray-700 mb-3">{issue.message}</p>
                <div className="bg-blue-50 border border-blue-200 rounded p-3">
                  <div className="flex items-start">
                    <svg className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <p className="font-medium text-blue-800 mb-1">建议</p>
                      <p className="text-blue-700">请检查代码并修复此问题</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 改进建议 */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">改进建议 ({analysis.suggestions.length}条)</h3>
        <div className="space-y-3">
          {analysis.suggestions.map((suggestion, index) => (
            <div key={index} className="flex items-start p-3 bg-green-50 border border-green-200 rounded-lg">
              <svg className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-800">{suggestion}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};