"""
============================================
 知识点检索器 — 语义搜索 + 召回
============================================
【作用】
根据用户问题/知识点，从 Chroma 向量库中检索最相关的教材原文。
检索结果拼接到 AI 提示词的 {{knowledge_context}} 中。

【召回策略】
1. 向量语义搜索（主要方式）— 找意思相近的内容
2. 返回 top_k 条最相关的结果
3. 每条结果附带来源（文件名、页码）方便追溯
"""

from typing import List, Dict, Optional
import traceback

from app.config import settings
from app.vector_db.client import vector_db, COURSE_MATERIALS


class KnowledgeRetriever:
    """
    【知识检索器】
    
    封装向量检索逻辑，提供简洁的检索接口。
    """

    def __init__(self):
        """初始化，嵌入模型延迟加载"""
        self._embedding_model = None

    def _get_embedding_model(self):
        """获取嵌入模型 - 使用 Chroma 默认模型"""
        if self._embedding_model is None:
            print("[检索器] 使用 Chroma 默认嵌入模型")
            self._embedding_model = "default"
        return self._embedding_model

    def search(
        self,
        query: str,
        category: str = COURSE_MATERIALS,
        top_k: int = None,
    ) -> Dict:
        """
        【核心检索方法】
        
        参数:
            query: 查询文本（知识点、问题等）
            category: 在哪个集合中搜索（默认课件库）
            top_k: 返回几条结果
        
        返回:
            {
                "success": True/False,
                "results": [{"text": "...", "source": "...", "page": 1, "score": 0.95}, ...],
                "total": 3
            }
        """
        if top_k is None:
            top_k = settings.RETRIEVAL_TOP_K
        
        try:
            # 1. 获取集合
            collection = vector_db.get_or_create_collection(category)
            
            # 检查集合是否有数据
            if collection.count() == 0:
                return {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "message": "知识库为空，请先上传课件",
                }
            
            # 2. 直接用文本搜索（Chroma 内置 embedding）
            # 3. 在 Chroma 中搜索
            result = collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            
            # 4. 整理结果
            results = []
            if result["documents"] and result["documents"][0]:
                for i in range(len(result["documents"][0])):
                    doc = result["documents"][0][i]
                    meta = result["metadatas"][0][i]
                    distance = result["distances"][0][i]
                    
                    # distance 是"距离"，越小越相似
                    # 转成 0-1 之间的"相似度分数"（1=最相似）
                    similarity = 1 - distance
                    
                    results.append({
                        "text": doc,
                        "source": meta.get("source", "未知"),
                        "page": meta.get("page", 0),
                        "score": round(similarity, 4),
                    })
            
            return {
                "success": True,
                "results": results,
                "total": len(results),
            }
        
        except Exception as e:
            error_msg = f"检索失败: {str(e)}\n{traceback.format_exc()}"
            print(f"[检索器] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "results": [],
                "total": 0,
            }

    def format_context(self, search_result: Dict) -> str:
        """
        【格式化检索结果为上下文字符串】
        
        把检索到的结果拼接成一段文本，
        直接塞到 AI 提示词的 {{knowledge_context}} 中。
        
        参数:
            search_result: search() 的返回结果
        
        返回:
            格式化的参考文本
        """
        if not search_result["success"] or not search_result["results"]:
            return "（未找到相关参考内容）"
        
        parts = []
        for i, r in enumerate(search_result["results"]):
            source_info = f"来源: {r['source']}"
            if r["page"]:
                source_info += f" 第{r['page']}页"
            
            part = f"[参考片段 {i+1}]（{source_info}）\n{r['text']}"
            parts.append(part)
        
        return "\n\n".join(parts)


# ==================== 全局实例 ====================
retriever = KnowledgeRetriever()
