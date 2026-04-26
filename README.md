# CodeReview AI 🔥

> AI驱动的代码审查系统 — 全AI智能体公司产品  
> 29分钟从0到1，50用户并发100%成功

## ✨ 特性

- **AI 代码审查** — 自动发现bug、安全漏洞、性能问题
- **多语言支持** — Python / JavaScript / TypeScript / Java / Go / Rust / C++
- **实时进度** — WebSocket实时推送审查进度
- **异步任务** — 提交后随时查看结果
- **高性能** — 平均响应120ms，支持50+并发

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt

# 2. 启动后端
cd backend
python main.py

# 3. 访问 http://localhost:9000/docs
```

## 📡 API

| 端点 | 方法 | 说明 |
|------|------|------|
| /analyze | POST | 提交代码审查 |
| /result/{job_id} | GET | 获取审查结果 |
| /ws/{job_id} | WS | WebSocket实时审查 |
| /health | GET | 健康检查 |

## 🖥️ CLI 使用

```bash
# 安装
cd cli && npm install -g .

# 使用
codereview analyze ./my-project
```

## 🛠 技术栈

- **后端**: FastAPI + Python 3.11
- **前端**: React + TypeScript + TailwindCSS
- **架构**: 异步任务 + WebSocket实时推送

## 📦 项目结构

```
codereview-ai/
├── backend/        # FastAPI后端
├── frontend/       # React前端
├── cli/            # CLI工具
└── marketing/      # 营销素材
```

## 🤝 贡献

全AI智能体公司产品 — CEO: Spark 🔥

[GitHub仓库](https://github.com/yizhimish/codereview-ai)
