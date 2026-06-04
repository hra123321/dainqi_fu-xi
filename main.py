"""
============================================
 FastAPI 应用入口 — 项目启动文件
============================================
【作用】
这是整个项目的入口文件。运行方式：
  uvicorn main:app --reload

【启动流程】
1. 创建 FastAPI 实例
2. 配置 Jinja2 模板引擎（渲染 HTML 页面）
3. 配置静态文件目录（CSS/JS 等）
4. 注册所有 API 路由
5. 启动事件：加载提示词 → 初始化向量库 → 打开 Edge 浏览器
6. 等待用户访问

【理解 Python 的 __name__ == "__main__"】
Python 文件可以直接运行（python main.py）或被其他文件导入。
这个判断确保：只有直接运行时才执行启动代码，
被导入时不执行（防止重复启动）。
"""

import sys
import os
from pathlib import Path

# 确保项目根目录在 Python 搜索路径中
# 这样 import app.xxx 才能找到我们的模块
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ==================== 创建 FastAPI 应用 ====================
# FastAPI() 创建了一个 Web 应用实例
# title：在自动生成的 API 文档中显示的名字
app = FastAPI(
    title="电气专业课 AI 期末刷题系统",
    description="基于 DeepSeek-V4 的智能刷题与批改系统",
    version="1.0.0",
)

# ==================== 配置模板和静态文件 ====================
# 【Jinja2 模板】HTML 模板文件的存放目录
# 模板里可以写 {{ variable }} 来插入动态数据
templates = Jinja2Templates(directory="app/templates")

# 【静态文件】CSS/JS/图片等文件存放目录
# 访问方式：浏览器访问 /static/css/style.css
static_dir = Path("app/static")
static_dir.mkdir(exist_ok=True)
(static_dir / "css").mkdir(exist_ok=True)
(static_dir / "js").mkdir(exist_ok=True)


# ==================== 启动事件（应用启动时自动运行） ====================
@app.on_event("startup")
async def startup_event():
    """
    【启动事件】
    当 uvicorn 启动 FastAPI 应用时，这个函数会自动运行。
    负责在服务器开始监听之前做好所有准备工作。
    
    执行顺序：
    1. 加载提示词文件到内存
    2. 初始化 Chroma 向量数据库
    3. 注册 API 路由
    4. 打开 Edge 浏览器
    """
    print("=" * 50)
    print("电气专业课 AI 期末刷题系统 正在启动...")
    print("=" * 50)
    
    # ---- 1. 加载提示词 ----
    from app.prompts.loader import load_prompts, get_prompt_count
    load_prompts()
    print(f"[启动] 已加载 {get_prompt_count()} 套系统提示词")
    
    # ---- 2. 初始化向量数据库 ----
    from app.vector_db.client import vector_db
    stats = vector_db.get_all_collections()
    for s in stats:
        print(f"[启动] 向量库 [{s['name']}] 就绪，文档数: {s['doc_count']}")
    
    # ---- 3. 注册 API 路由 ----
    # 目前先注册首页路由，后续阶段逐步添加其他路由
    print("[启动] API 路由已注册")
    
    # ---- 4. 打开 Edge 浏览器 ----
    from app.utils.browser import try_open_browser
    try_open_browser("http://127.0.0.1:8000")
    
    print("[启动] 系统启动完成！")
    print(f"[启动] 访问地址: http://127.0.0.1:8000")
    print("=" * 50)


# ==================== 首页路由 ====================
# 【路由知识点】
# @app.get("/") 是 Python 的"装饰器"语法
# 意思是：当用户访问网站根路径 / 时，执行下面的函数
#
# "/" 是网站的首页，像你访问 baidu.com 看到的第一页

from fastapi import Request
from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    【首页】
    
    访问 http://127.0.0.1:8000/ 时触发。
    返回一个 HTML 页面给浏览器。
    
    参数:
        request: 包含用户浏览器信息、IP 等
    
    返回:
        HTML 页面内容
    """
    return templates.TemplateResponse(
        "index.html",  # 使用哪个模板文件
        {
            "request": request,          # 必须传入 request（FastAPI 要求）
            "title": "电气复习系统",       # 页面标题
            "message": "欢迎使用电气专业课 AI 期末刷题系统！",
            "version": "v1.0.0",
        },
    )


# ==================== 健康检查接口 ====================
@app.get("/api/health")
async def health_check():
    """
    【健康检查】
    
    用于监控系统是否正常运行。
    返回系统状态信息。
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "message": "系统运行正常",
    }


# ==================== 程序入口 ====================
if __name__ == "__main__":
    """
    【直接运行时的入口】
    
    当你执行 python main.py 时，会运行这里的代码。
    它的作用等同于在命令行输入：
      uvicorn main:app --reload
    
    --reload 参数让代码改动后自动重启服务器（开发时很方便）
    
    参数 host="0.0.0.0" 让局域网内其他设备也能访问（可选）
    """
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",  # 只允许本机访问（安全）
        port=8000,          # 端口号
        reload=True,        # 开发模式：代码改了自动重启
    )
