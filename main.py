import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="电气专业课 AI 期末刷题系统",
    description="基于 DeepSeek-V4 的智能刷题与批改系统",
    version="1.0.0",
)

templates = Jinja2Templates(directory="app/templates")

static_dir = Path("app/static")
static_dir.mkdir(exist_ok=True)
(static_dir / "css").mkdir(exist_ok=True)
(static_dir / "js").mkdir(exist_ok=True)

# Register API routers
from app.router import exam as exam_router
from app.router import knowledge as knowledge_router
from app.router import admin as admin_router

app.include_router(exam_router.router)
app.include_router(knowledge_router.router)
app.include_router(admin_router.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "电气复习系统",
            "message": "欢迎使用电气专业课 AI 期末刷题系统！",
            "version": "v1.0.0",
        },
    )


@app.get("/exam", response_class=HTMLResponse)
async def exam_page(request: Request):
    return templates.TemplateResponse("exam.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0", "message": "System running"}


@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("System starting...")
    print("=" * 50)
    from app.prompts.loader import load_prompts, get_prompt_count
    load_prompts()
    print(f"[startup] Prompts loaded: {get_prompt_count()}")
    from app.vector_db.client import vector_db
    stats = vector_db.get_all_collections()
    for s in stats:
        print(f"[startup] Collection [{s['name']}]: {s['doc_count']} docs")
    from app.utils.browser import try_open_browser
    try_open_browser("http://127.0.0.1:8000")
    print("[startup] System ready!")
    print(f"[startup] URL: http://127.0.0.1:8000")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
