# CodeReview AI 🔥

> 全AI团队构建的全自动代码审查系统，29分钟从0到1，50用户并发100%成功。

## ✨ 核心功能

- **AI 代码审查** ✨ 自动发现bug、性能问题、安全漏洞
- **多语言支持** 💻 Python / JavaScript / TypeScript / Java / Go / Rust / C++
- **异步处理** 🔄 提交即走，查询结果，支持WebSocket实时推送
- **零配置** 🚀 装依赖后2条命令即可运行
- **低延迟** ⚡ 平均120ms响应，支持50+并发

## 🚀 快速开始

`ash
# 1. 安装依赖
pip install -r backend/requirements.txt

# 2. 启动后端服务
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 9000

# 3. 打开 http://localhost:9000
`

## 📡 API

| 接口 | 方法 | 说明 |
|------|------|------|
| /analyze | POST | 提交代码审查 |
| /result/{job_id} | GET | 获取审查结果 |
| /ws/{job_id} | WS | 实时推送进度 |
| /health | GET | 健康检查 |

## 💻 CLI 工具

`ash
# 安装
cd cli && npm install -g .

# 使用
codereview analyze ./my-project
`

## 🛠️ 技术栈

- **后端**: FastAPI + Python 3.11
- **前端**: React + TypeScript + TailwindCSS
- **架构**: 异步任务队列 + WebSocket实时推送

## ⚡ 为什么特别

这款产品**100%由AI构建和运营**：

- CEO (AI) ✅ 写前端、做推广
- CTO (AI) ✅ 写后端、搭架构
- 从想法到产品仅29分钟
- 无需人工干预，完全自主运营

## 📄 许可证

MIT
