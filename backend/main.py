import asyncio
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ==================== 閰嶇疆 ====================
MAX_CODE_LENGTH = 50000  # 鍏抽敭锛氫粠10000鏀逛负50000
CHUNK_SIZE = 1000  # 澶ф枃浠跺垎鍧楀ぇ灏?
# ==================== 搴旂敤鍒濆鍖?====================
app = FastAPI(title="CodeReview AI", version="2.0.0")

# CORS閰嶇疆
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 璇锋眰鏃ュ織涓棿浠?@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Powered-By"] = "CodeReview AI 2.0.0"
    return response

# ==================== 鏁版嵁妯″瀷 ====================
class CodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=MAX_CODE_LENGTH, description="瑕佸垎鏋愮殑浠ｇ爜")
    language: Optional[str] = Field("python", description="缂栫▼璇█")

    class Config:
        anystr_strip_whitespace = True
        min_anystr_length = 1

class TaskStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = 0
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

# ==================== 瀛樺偍 ====================
tasks_db = {}
websocket_connections = {}

# ==================== 鍋ュ悍妫€鏌?====================
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

# ==================== 璋冭瘯绔偣 ====================
@app.get("/debug/file-info")
async def debug_file_info(code: str = ""):
    """璋冭瘯绔偣锛氭煡鐪嬫枃浠朵俊鎭?""
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

# ==================== 浠ｇ爜鍒嗘瀽 ====================
@app.post("/analyze")
async def analyze_code(request: CodeRequest):
    """鍒嗘瀽浠ｇ爜 - 鏀寔澶ф枃浠跺垎鍧楀鐞?""

    # 1. 楠岃瘉浠ｇ爜闀垮害
    if len(request.code) > MAX_CODE_LENGTH:
        return JSONResponse(
            status_code=400,
            content={
                "error": "浠ｇ爜杩囬暱",
                "message": f"鏈€澶ф敮鎸?{MAX_CODE_LENGTH} 瀛楃锛屽綋鍓?{len(request.code)} 瀛楃",
                "suggestion": "璇峰皢浠ｇ爜鍒嗘鎻愪氦鎴栬仈绯荤鐞嗗憳"
            },
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

    # 2. 鐢熸垚浠诲姟ID
    job_id = str(uuid.uuid4())

    # 3. 鍒ゆ柇鏄惁涓哄ぇ鏂囦欢
    is_large_file = len(request.code) > 10000
    line_count = len(request.code.split('\n'))
    chunks_needed = (line_count // CHUNK_SIZE) + 1 if is_large_file else 1

    # 4. 瀛樺偍浠诲姟
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

    # 5. 鍚姩寮傛浠诲姟
    if is_large_file:
        asyncio.create_task(process_large_file_async(job_id, request.code))
    else:
        asyncio.create_task(process_normal_file_async(job_id, request.code))

    # 6. 杩斿洖202 Accepted
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "processing",
            "message": f"鍒嗘瀽浠诲姟宸叉彁浜'锛堝ぇ鏂囦欢锛屽垎鍧楀鐞嗕腑锛? if is_large_file else ''}",
            "estimated_time": f"{chunks_needed * 2}-{chunks_needed * 5}绉? if is_large_file else "3-5绉?,
            "total_chunks": chunks_needed,
            "total_lines": line_count,
            "is_large_file": is_large_file
        },
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

# ==================== 缁撴灉鏌ヨ ====================
@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """鏌ヨ鍒嗘瀽缁撴灉"""
    if job_id not in tasks_db:
        raise HTTPException(status_code=404, detail="浠诲姟涓嶅瓨鍦?)

    task = tasks_db[job_id]
    return task

# ==================== WebSocket ====================
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    websocket_connections[job_id] = websocket

    try:
        while True:
            # 淇濇寔杩炴帴锛屾帹閫佽繘搴︽洿鏂?            await asyncio.sleep(1)
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

# ==================== 澶勭悊鍑芥暟 ====================
async def process_normal_file_async(job_id: str, code: str):
    """澶勭悊鏅€氭枃浠讹紙< 10000瀛楃锛?""
    try:
        # 妯℃嫙澶勭悊鏃堕棿
        await asyncio.sleep(2)

        # 鏇存柊浠诲姟鐘舵€?        tasks_db[job_id].update({
            "status": "completed",
            "progress": 100,
            "result": {
                "issues": [
                    {"type": "info", "message": "浠ｇ爜缁撴瀯鑹ソ", "line": 1},
                    {"type": "warning", "message": "寤鸿娣诲姞娉ㄩ噴", "line": 5}
                ],
                "summary": "浠ｇ爜璐ㄩ噺鑹ソ锛屾湁鏀硅繘绌洪棿",
                "complexity": "浣?
            },
            "completed_at": datetime.now().isoformat()
        })

        # 閫氱煡WebSocket
        if job_id in websocket_connections:
            ws = websocket_connections[job_id]
            await ws.send_json({"job_id": job_id, "status": "completed", "progress": 100})

    except Exception as e:
        tasks_db[job_id].update({
            "status": "failed",
            "error": str(e)
        })

async def process_large_file_async(job_id: str, code: str):
    """澶勭悊澶ф枃浠讹紙> 10000瀛楃锛? 鍒嗗潡澶勭悊"""
    try:
        lines = code.split('\n')
        total_chunks = (len(lines) // CHUNK_SIZE) + 1

        for chunk_index in range(total_chunks):
            start = chunk_index * CHUNK_SIZE
            end = min((chunk_index + 1) * CHUNK_SIZE, len(lines))
            chunk = '\n'.join(lines[start:end])

            # 澶勭悊褰撳墠鍧?            await asyncio.sleep(1)  # 妯℃嫙澶勭悊鏃堕棿

            # 鏇存柊杩涘害
            progress = int(((chunk_index + 1) / total_chunks) * 100)
            completed_chunks = chunk_index + 1

            tasks_db[job_id].update({
                "progress": progress,
                "completed_chunks": completed_chunks,
                "status": f"processing_chunk_{completed_chunks}_of_{total_chunks}"
            })

            # 閫氱煡WebSocket
            if job_id in websocket_connections:
                ws = websocket_connections[job_id]
                await ws.send_json({
                    "job_id": job_id,
                    "status": "processing",
                    "progress": progress,
                    "completed_chunks": completed_chunks,
                    "total_chunks": total_chunks
                })

        # 鎵€鏈夊潡澶勭悊瀹屾垚
        tasks_db[job_id].update({
            "status": "completed",
            "progress": 100,
            "result": {
                "issues": [
                    {"type": "info", "message": f"澶ф枃浠跺鐞嗗畬鎴愶紝鍏眥len(lines)}琛?, "line": 1},
                    {"type": "info", "message": f"鍒唟total_chunks}鍧楀鐞?, "line": 2}
                ],
                "summary": f"澶ф枃浠跺垎鏋愬畬鎴愶紝鍏眥len(lines)}琛岋紝鍒唟total_chunks}鍧楀鐞?,
                "complexity": "涓?,
                "chunks_processed": total_chunks
            },
            "completed_at": datetime.now().isoformat()
        })

        # 鏈€缁堥€氱煡
        if job_id in websocket_connections:
            ws = websocket_connections[job_id]
            await ws.send_json({
                "job_id": job_id,
                "status": "completed",
                "progress": 100,
                "message": f"澶ф枃浠跺垎鏋愬畬鎴愶紝鍏眥total_chunks}鍧?
            })

    except Exception as e:
        tasks_db[job_id].update({
            "status": "failed",
            "error": str(e)
        })

# ==================== 鍚姩搴旂敤 ====================
if __name__ == "__main__":
    import uvicorn
    print("CodeReview AI 鍚庣鏈嶅姟鍚姩涓?..")
    print(f"绔彛锛?000")
    print(f"鏈€澶ф枃浠跺ぇ灏忥細{MAX_CODE_LENGTH} 瀛楃")
    print(f"鍒嗗潡澶у皬锛歿CHUNK_SIZE} 琛?鍧?)
    print(f"澶ф枃浠堕槇鍊硷細10000 瀛楃")
    print("鏈嶅姟鍚姩瀹屾垚锛岀瓑寰呰姹?..")
    uvicorn.run(app, host="0.0.0.0", port=9000)
