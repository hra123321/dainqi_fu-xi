import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.insert(0, os.path.dirname(__file__))


app = FastAPI(
    title="电气专业课 AI 期末复习系统",
    description="基于 DeepSeek V4 Flash / Pro 的本地复习与批改系统",
    version="1.0.0",
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

static_dir = Path("app/static")
static_dir.mkdir(exist_ok=True)
(static_dir / "css").mkdir(exist_ok=True)
(static_dir / "js").mkdir(exist_ok=True)

from app.router import admin as admin_router
from app.router import exam as exam_router
from app.router import knowledge as knowledge_router
from app.router import mobile as mobile_router
from app.router import subjects as subjects_router
from app.router import sync as sync_router
from app.router import wrong_book as wrong_book_router

app.include_router(exam_router.router)
app.include_router(knowledge_router.router)
app.include_router(subjects_router.router)
app.include_router(admin_router.router)
app.include_router(mobile_router.router)
app.include_router(sync_router.router)
app.include_router(wrong_book_router.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "电气复习系统",
            "message": "欢迎使用电气专业课 AI 期末复习系统",
            "version": "v1.0.0",
        },
    )


@app.get("/exam", response_class=HTMLResponse)
async def exam_page(request: Request):
    return templates.TemplateResponse("exam.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/subjects", response_class=HTMLResponse)
async def subjects_page(request: Request):
    return templates.TemplateResponse("subjects.html", {"request": request})


@app.get("/wrong-book", response_class=HTMLResponse)
async def wrong_book_page(request: Request):
    return templates.TemplateResponse("wrong_book.html", {"request": request})


@app.get("/mobile", response_class=HTMLResponse)
async def mobile_page(request: Request):
    return templates.TemplateResponse("mobile.html", {"request": request})


@app.get("/mobile/manifest.json")
async def mobile_manifest():
    return FileResponse("app/templates/manifest.json", media_type="application/json")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0", "message": "System running"}


@app.get("/favicon.ico")
async def favicon_ico():
    path = os.path.join("app", "static", "favicon.svg")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/svg+xml")
    return Response(status_code=204)


@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("System starting...")
    print("=" * 50)

    from app.prompts.loader import get_prompt_count, load_prompts

    load_prompts()
    print(f"[startup] Prompts loaded: {get_prompt_count()}")

    from app.vector_db.client import vector_db

    stats = vector_db.get_all_collections()
    for item in stats:
        print(f"[startup] Collection [{item['name']}]: {item['doc_count']} docs")

    from app.utils.browser import try_open_browser

    try_open_browser("http://127.0.0.1:8000")
    print("[startup] System ready!")
    print("[startup] URL: http://127.0.0.1:8000")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
