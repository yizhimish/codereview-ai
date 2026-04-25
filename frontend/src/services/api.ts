import axios from 'axios';

const API_BASE_URL = '';
const WS_BASE_URL = 'ws://localhost:9000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response) {
      // 服务器返回错误状态码
      console.error('API Error:', error.response.status, error.response.data);
      return Promise.reject({
        status: error.response.status,
        message: error.response.data?.message || '服务器错误',
        data: error.response.data,
      });
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('Network Error:', error.message);
      return Promise.reject({
        status: 0,
        message: '网络连接错误，请检查网络设置',
      });
    } else {
      // 请求配置出错
      console.error('Request Error:', error.message);
      return Promise.reject({
        status: -1,
        message: error.message || '请求配置错误',
      });
    }
  }
);

export interface AnalyzeRequest {
  code: string;
  language?: string;
}

export interface AnalyzeResponse {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  message: string;
}

export interface AnalysisResult {
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

export interface WebSocketMessage {
  job_id: string;
  progress: number;
  current_step: string;
}

export const analyzeCode = async (data: AnalyzeRequest): Promise<AnalyzeResponse> => {
  try {
    console.log('提交代码分析:', data);
    
    // 调用后端API
    const response = await api.post('/analyze', data);
    
    console.log('分析任务提交成功:', response);
    return response as unknown as AnalyzeResponse;
  } catch (error) {
    console.error('提交代码分析失败:', error);
    throw error;
  }
};

export const getAnalysisResult = async (jobId: string): Promise<AnalysisResult> => {
  try {
    console.log('获取分析结果:', jobId);
    
    // 调用后端API
    const response = await api.get(`/result/${jobId}`);
    
    console.log('分析结果:', response);
    return response as unknown as AnalysisResult;
  } catch (error) {
    console.error('获取分析结果失败:', error);
    throw error;
  }
};

export const getHealth = async (): Promise<{ status: string; timestamp: string }> => {
  try {
    const response = await api.get('/health');
    return response as unknown as { status: string; timestamp: string };
  } catch (error) {
    console.error('健康检查失败:', error);
    throw error;
  }
};

// WebSocket连接
let wsConnection: WebSocket | null = null;

export const connectWebSocket = (jobId: string, onMessage: (data: any) => void): WebSocket => {
  const wsUrl = `${WS_BASE_URL}/ws/${jobId}`;
  wsConnection = new WebSocket(wsUrl);
  
  wsConnection.onopen = () => {
    console.log(`WebSocket连接已建立: ${wsUrl}`);
  };
  
  wsConnection.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('WebSocket消息解析失败:', error);
    }
  };
  
  wsConnection.onerror = (error) => {
    console.error('WebSocket连接错误:', error);
  };
  
  wsConnection.onclose = () => {
    console.log('WebSocket连接已关闭');
    wsConnection = null;
  };
  
  return wsConnection;
};

export const closeWebSocket = () => {
  if (wsConnection) {
    wsConnection.close();
    wsConnection = null;
  }
};

export default api;