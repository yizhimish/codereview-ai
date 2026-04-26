import asyncio
import uuid
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, WebSocket, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from auth import (
    register_user, authenticate, validate_api_key,
    extract_api_key, get_user_info, regenerate_api_key
)

MAX_CODE_LENGTH = 50000
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "build")

app = FastAPI(title="CodeReview AI", version="2.1.0")

# ── Mount frontend static files if built ─────────────────────
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
else:
    FRONTEND_DIR = None

@app.get("/")
async def serve_index():
    if FRONTEND_DIR:
        pricing_html = os.path.join(FRONTEND_DIR, "pricing.html")
        if os.path.exists(pricing_html):
            return FileResponse(pricing_html)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    return JSONResponse({
        "app": "CodeReview AI", "version": "2.1.0",
        "message": "Frontend not built. Run: cd frontend && npm run build",
        "docs": "/docs"
    })

@app.get("/pricing")
async def serve_pricing():
    if FRONTEND_DIR:
        p = os.path.join(FRONTEND_DIR, "pricing.html")
        if os.path.exists(p):
            return FileResponse(p)
    return {"message": "Pricing page not available"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    return response


# ── Pydantic models ───────────────────────────────────────────

class CodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=MAX_CODE_LENGTH)
    language: Optional[str] = Field("python")

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)
    email: str = Field(..., max_length=128)

class LoginRequest(BaseModel):
    username: str
    password: str

class RegenerateKeyRequest(BaseModel):
    username: str
    password: str


# ── In-memory store for async analysis ────────────────────────
_tasks_db: Dict[str, Dict[str, Any]] = {}


# ── Health & Debug ────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.1.0", "timestamp": time.time()}

@app.get("/debug")
async def debug():
    return {"app": "CodeReview AI", "version": "2.1.0", "max_code_length": MAX_CODE_LENGTH, "frontend_built": FRONTEND_DIR is not None}


# ── User / Auth Endpoints ─────────────────────────────────────

@app.post("/auth/register")
async def api_register(req: RegisterRequest):
    """注册新用户并获取API Key"""
    result = register_user(req.username, req.password, req.email)
    if result is None:
        raise HTTPException(status_code=409, detail="Username already exists")
    return {"status": "success", "data": result}

@app.post("/auth/login")
async def api_login(req: LoginRequest):
    """登录验证并获取API Key"""
    result = authenticate(req.username, req.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "success", "data": result}

@app.post("/auth/regenerate-key")
async def api_regenerate_key(req: RegenerateKeyRequest):
    """重新生成API Key（旧的会失效）"""
    new_key = regenerate_api_key(req.username, req.password)
    if new_key is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "success", "data": {"api_key": new_key}}

@app.get("/auth/me")
async def api_me(request: Request):
    """获取当前用户信息（通过Authorization头）"""
    auth_header = request.headers.get("Authorization")
    api_key = extract_api_key(auth_header)
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    info = validate_api_key(api_key)
    if info is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    user_info = get_user_info(info["username"])
    return {"status": "success", "data": user_info}


# ── Code Review Endpoints ─────────────────────────────────────

def _require_auth(request: Request) -> Optional[Dict]:
    """检查请求是否包含有效的API Key（可选认证模式）"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None  # 允许未认证请求（但会受速率限制）
    api_key = extract_api_key(auth_header)
    if api_key:
        info = validate_api_key(api_key)
        if info:
            return info
    return None

@app.post("/analyze")
async def analyze_code(request: Request, data: CodeRequest):
    if len(data.code) > MAX_CODE_LENGTH:
        return JSONResponse(
            status_code=400,
            content={
                "error": "code_too_long",
                "message": f"Max code length is {MAX_CODE_LENGTH}, got {len(data.code)} chars",
            }
        )

    # 可选认证 —— free用户有代码长度限制
    auth_info = _require_auth(request)
    if auth_info:
        user_info = get_user_info(auth_info["username"])
        plan = user_info.get("plan", "free") if user_info else "free"
        if plan == "free" and len(data.code) > 10000:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "plan_limit",
                    "message": "Free plan limited to 10000 chars. Upgrade or use API Key.",
                }
            )

    job_id = str(uuid.uuid4())

    from analyzer import analyze
    result = analyze(data.code, data.language or "python")

    _tasks_db[job_id] = {
        "job_id": job_id,
        "code_preview": data.code[:100],
        "status": "completed",
        "created_at": datetime.now().isoformat(),
        **result,
    }

    return {
        "status": "completed",
        "job_id": job_id,
        **result,
    }

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    task = _tasks_db.get(job_id)
    if not task:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": f"Job {job_id} not found"}
        )
    return {"status": task.get("status", "completed"), "job_id": job_id, **task}


# ── WebSocket ──────────────────────────────────────────────────

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        await websocket.send_json({"type": "progress", "stage": "connecting", "progress": 0})

        data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
        code = data.get("code", "")
        language = data.get("language", "python")

        if not code or len(code) > MAX_CODE_LENGTH:
            await websocket.send_json({
                "type": "error",
                "message": f"Code must be 1-{MAX_CODE_LENGTH} characters",
                "job_id": job_id,
            })
            return

        progress_sent = set()

        async def progress_callback(stage: str, progress: int):
            if stage in progress_sent:
                return
            progress_sent.add(stage)
            try:
                await websocket.send_json({
                    "type": "progress",
                    "stage": stage,
                    "progress": progress,
                    "job_id": job_id,
                })
            except Exception:
                pass

        from analyzer import analyze
        result = analyze(code, language, progress_callback=progress_callback)

        _tasks_db[job_id] = {
            "job_id": job_id,
            "code_preview": code[:100],
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            **result,
        }

        await websocket.send_json({
            "type": "complete",
            "status": "completed",
            "job_id": job_id,
            "progress": 100,
            **result,
        })

    except asyncio.TimeoutError:
        try:
            await websocket.send_json({"type": "error", "message": "Timeout waiting for code input"})
        except Exception:
            pass
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    fe_status = "OK" if FRONTEND_DIR else "NOT BUILT"
    print(f"""
  CodeReview AI v2.1.0
  Auth: /auth/register | /auth/login | /auth/me
  API:  /analyze | /result/{{id}} | /ws/{{id}}
  Web:  / (pricing) | /docs
  Frontend: {fe_status}  |  Port: 9000
""")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 9000)))
