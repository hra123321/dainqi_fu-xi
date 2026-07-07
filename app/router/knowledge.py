"""
============================================
 知识库路由 — PDF 上传、检索
============================================
"""

import os
import uuid
import tempfile

from fastapi import APIRouter, UploadFile, File, Form, Query
from app.models.schemas import KnowledgeSearchRequest, KnowledgeSearchResponse
from app.vector_db.processor import pdf_processor
from app.vector_db.retriever import retriever
from app.utils.logger import logger

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    category: str = Form("course_materials"),
):
    """
    【上传课件 PDF】
    
    接收 PDF 文件，自动提取文字 → 切片 → 向量化 → 入库。
    
    请求方式: multipart/form-data
    参数:
        file: PDF 文件
        category: 分类（默认 course_materials）
    """
    # 检查文件类型
    if not file.filename.lower().endswith(".pdf"):
        return {"success": False, "error": "只支持 PDF 文件"}
    
    # 保存上传的文件到临时目录
    temp_dir = "data/cache"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file.filename}")
    content = await file.read()
    
    with open(temp_path, "wb") as f:
        f.write(content)
    
    logger.info(f"[上传] 收到文件: {file.filename} ({len(content)} bytes)")
    
    try:
        # 调用处理器
        result = pdf_processor.process_pdf(temp_path)
        
        if result["success"]:
            logger.info(f"[上传] 成功: {result['message']}")
        
        return result
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/search")
async def search_knowledge(req: KnowledgeSearchRequest):
    """
    【检索知识库】
    
    根据查询文本搜索知识库，返回最相关的知识片段。
    
    请求示例:
        POST /api/knowledge/search
        {"query": "欧姆定律", "category": "course_materials", "top_k": 5}
    """
    result = retriever.search(
        query=req.query,
        category=req.category,
        top_k=req.top_k,
        subject_id=req.subject_id,
    )
    return result


@router.get("/search")
async def search_knowledge_get(
    query: str = Query(..., min_length=1),
    category: str = Query("course_materials"),
    top_k: int = Query(5, ge=1, le=20),
    subject_id: str = Query(""),
):
    return retriever.search(
        query=query,
        category=category,
        top_k=top_k,
        subject_id=subject_id,
    )


@router.get("/collections")
async def get_collections():
    """
    【获取知识库统计】
    
    返回所有集合（分区）的名称和文档数量。
    """
    from app.vector_db.client import vector_db
    return {"collections": vector_db.get_all_collections()}
