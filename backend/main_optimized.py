import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import os
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==================== 配置 ====================
MAX_CODE_LENGTH = 50000  # 关键：从10000改为50000
CHUNK_SIZE = 1000  # 大文件分块大小

# ==================== 应用初始化 ====================
app = FastAPI(title="CodeReview AI", version="2.0.0")

# 静态文件服务
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================
class CodeRequest(BaseModel):
    code: str
    language: Optional[str] = "python"

class TaskStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = 0
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

# ==================== 存储 ====================
tasks_db = {}
websocket_connections = {}

# ==================== 健康检查 ====================
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "codereview-ai",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "jobs_running": len([t for t in tasks_db.values() if t["status"] == "processing"]),
        "jobs_pending": len([t for t in tasks_db.values() if t["status"] == "pending"])
    }

# ==================== 调试端点 ====================
@app.get("/debug/file-info")
async def debug_file_info(code: str = ""):
    """调试端点：查看文件信息"""
    line_count = len(code.split('\n')) if code else 0
    is_large_file = len(code) > 10000

    return {
        "code_length": len(code),
        "line_count": line_count,
        "is_large_file": is_large_file,
        "chunks_needed": (line_count // CHUNK_SIZE) + 1 if is_large_file else 1,
        "max_length_allowed": MAX_CODE_LENGTH,
        "chars_remaining": MAX_CODE_LENGTH - len(code) if code else MAX_CODE_LENGTH,
        "chunk_size": CHUNK_SIZE
    }

# ==================== 代码分析 ====================
@app.post("/analyze")
async def analyze_code(request: CodeRequest):
    """分析代码 - 支持大文件分块处理"""

    # 1. 验证代码长度
    if len(request.code) > MAX_CODE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "代码过长",
                "message": f"最大支持 {MAX_CODE_LENGTH} 字符，当前 {len(request.code)} 字符",
                "suggestion": "请将代码分段提交或联系管理员"
            }
        )

    # 2. 生成任务ID
    job_id = str(uuid.uuid4())

    # 3. 判断是否为大文件
    is_large_file = len(request.code) > 10000
    line_count = len(request.code.split('\n'))
    chunks_needed = (line_count // CHUNK_SIZE) + 1 if is_large_file else 1

    # 4. 存储任务
    tasks_db[job_id] = {
        "job_id": job_id,
        "code_preview": request.code[:100] + "..." if len(request.code) > 100 else request.code,
        "status": "processing",
        "progress": 0,
        "total_chunks": chunks_needed,
        "completed_chunks": 0,
        "created_at": datetime.now().isoformat(),
        "is_large_file": is_large_file,
        "total_lines": line_count,
        "result": None
    }

    # 5. 启动异步任务
    if is_large_file:
        asyncio.create_task(process_large_file_async(job_id, request.code))
    else:
        asyncio.create_task(process_normal_file_async(job_id, request.code))

    # 6. 返回202 Accepted
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "processing",
            "message": f"分析任务已提交{'（大文件，分块处理中）' if is_large_file else ''}",
            "estimated_time": f"{chunks_needed * 2}-{chunks_needed * 5}秒" if is_large_file else "3-5秒",
            "total_chunks": chunks_needed,
            "total_lines": line_count,
            "is_large_file": is_large_file
        }
    )

# ==================== 结果查询 ====================
@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """查询分析结果"""
    if job_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks_db[job_id]
    return task

# ==================== WebSocket ====================
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    websocket_connections[job_id] = websocket

    try:
        while True:
            # 保持连接，推送进度更新
            await asyncio.sleep(1)
            if job_id in tasks_db:
                task = tasks_db[job_id]
                await websocket.send_json({
                    "job_id": job_id,
                    "status": task["status"],
                    "progress": task["progress"],
                    "completed_chunks": task.get("completed_chunks", 0),
                    "total_chunks": task.get("total_chunks", 1)
                })
    except:
        if job_id in websocket_connections:
            del websocket_connections[job_id]

# ==================== 处理函数 ====================
async def process_normal_file_async(job_id: str, code: str):
    """处理普通文件（< 10000字符）"""
    try:
        # 模拟处理时间
        await asyncio.sleep(2)

        # 更新任务状态
        code_lines = code.count('\\n') + 1
        tasks_db[job_id].update({
            "status": "completed",
            "progress": 100,
            "result": {
                "issues": [
                    {"type": "info", "message": "代码结构良好", "line": 1},
                    {"type": "warning", "message": "建议添加注释", "line": 5}
                ],
                "summary": "代码质量良好，有改进空间",
                "complexity": "低",
                "metrics": {
                    "lines_of_code": code_lines,
                    "cyclomatic_complexity": 1,
                    "maintainability_index": 85
                },
                "suggestions": ["建议添加函数注释", "考虑添加异常处理"],
                "grade": "A"
            },
            "completed_at": datetime.now().isoformat()
        })

        # 通知WebSocket
        if job_id in websocket_connections:
            ws = websocket_connections[job_id]
            await ws.send_json({"job_id": job_id, "status": "completed", "progress": 100})

    except Exception as e:
        tasks_db[job_id].update({
            "status": "failed",
            "error": str(e)
        })

async def process_large_file_async(job_id: str, code: str):
    """处理大文件（> 10000字符）- 分块处理"""
    try:
        lines = code.split('\n')
        total_chunks = (len(lines) // CHUNK_SIZE) + 1

        for chunk_index in range(total_chunks):
            start = chunk_index * CHUNK_SIZE
            end = min((chunk_index + 1) * CHUNK_SIZE, len(lines))
            chunk = '\n'.join(lines[start:end])

            # 处理当前块
            await asyncio.sleep(1)  # 模拟处理时间

            # 更新进度
            progress = int(((chunk_index + 1) / total_chunks) * 100)
            completed_chunks = chunk_index + 1

            tasks_db[job_id].update({
                "progress": progress,
                "completed_chunks": completed_chunks,
                "status": f"processing_chunk_{completed_chunks}_of_{total_chunks}"
            })

            # 通知WebSocket
            if job_id in websocket_connections:
                ws = websocket_connections[job_id]
                await ws.send_json({
                    "job_id": job_id,
                    "status": "processing",
                    "progress": progress,
                    "completed_chunks": completed_chunks,
                    "total_chunks": total_chunks
                })

        # 所有块处理完成
        tasks_db[job_id].update({
            "status": "completed",
            "progress": 100,
            "result": {
                "issues": [
                    {"type": "info", "message": f"大文件处理完成，共{len(lines)}行", "line": 1},
                    {"type": "info", "message": f"分{total_chunks}块处理", "line": 2}
                ],
                "summary": f"大文件分析完成，共{len(lines)}行，分{total_chunks}块处理",
                "complexity": "中",
                "chunks_processed": total_chunks,
                "metrics": {
                    "lines_of_code": len(lines),
                    "cyclomatic_complexity": 3,
                    "maintainability_index": 70
                },
                "suggestions": ["大文件建议拆分模块", "考虑添加类型注解"],
                "grade": "B"
            },
            "completed_at": datetime.now().isoformat()
        })

        # 最终通知
        if job_id in websocket_connections:
            ws = websocket_connections[job_id]
            await ws.send_json({
                "job_id": job_id,
                "status": "completed",
                "progress": 100,
                "message": f"大文件分析完成，共{total_chunks}块"
            })

    except Exception as e:
        tasks_db[job_id].update({
            "status": "failed",
            "error": str(e)
        })

# ==================== 启动应用 ====================
if __name__ == "__main__":
    import uvicorn
    print("🚀 CodeReview AI 后端服务启动中...")
    print(f"📍 端口：9000")
    print(f"📁 最大文件大小：{MAX_CODE_LENGTH} 字符")
    print(f"🔧 分块大小：{CHUNK_SIZE} 行/块")
    print(f"🔧 大文件阈值：10000 字符")
    print("✅ 服务启动完成，等待请求...")
    uvicorn.run(app, host="0.0.0.0", port=9000)