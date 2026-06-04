"""
============================================
 PDF 处理器 — 上传 → 切片 → 向量化 → 入库
============================================
【作用】
处理上传的课件 PDF，完成从原始文件到向量知识库的全流程。

【处理流程】
PDF 文件 → 提取文字 → 智能切片 → 生成向量 → 存入 Chroma

【切片策略】
- 按段落边界切片（不把一句话切成两半）
- 每段约 500 个中文字符
- 相邻切片重叠 50 字符（防止关键信息恰好在边界丢失）
"""

import os
import uuid
from typing import List, Dict
import traceback

# PDF 文字提取
import fitz  # PyMuPDF

# 向量数据库
from app.vector_db.client import vector_db, COURSE_MATERIALS


class PDFProcessor:
    """
    【PDF 处理器】
    
    封装了整个"PDF → 知识库"的处理流程。
    每个方法只管一件事（单一职责原则），方便理解和修改。
    """

    def __init__(self):
        """初始化时创建嵌入模型（延迟加载，第一次用时才下载）"""
        self._embedding_model = None

    def _get_embedding_model(self):
        """
        【获取嵌入模型】（懒加载）
        
        因为 sentence-transformers 第一次加载要下载模型文件（几十 MB），
        所以等到真正需要时才加载，而不是在项目启动时加载。
        
        模型选择说明：
        - paraphrase-multilingual-MiniLM-L12-v2 支持中文
        - 首次使用会自动下载，之后缓存到本地
        """
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            print("[PDF处理] 正在加载嵌入模型（首次下载约需1-2分钟）...")
            # 多语言模型，支持中文
            self._embedding_model = SentenceTransformer(
                "paraphrase-multilingual-MiniLM-L12-v2"
            )
            print("[PDF处理] 嵌入模型加载完成")
        return self._embedding_model

    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        【从 PDF 提取文字】
        
        用 PyMuPDF 逐页提取文字，返回每页的内容列表。
        
        参数:
            pdf_path: PDF 文件的完整路径
        
        返回:
            [{"page": 1, "text": "第1页内容..."}, {"page": 2, "text": "第2页内容..."}]
        """
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        pages = []
        doc = fitz.open(pdf_path)
        file_name = os.path.basename(pdf_path)
        
        print(f"[PDF处理] 文件 '{file_name}' 共 {len(doc)} 页")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if text.strip():  # 跳过空白页
                pages.append({
                    "page": page_num + 1,  # 页码从 1 开始（更直观）
                    "text": text.strip(),
                })
        
        doc.close()
        print(f"[PDF处理] 成功提取 {len(pages)} 页文字")
        return pages

    def chunk_text(self, pages: List[Dict]) -> List[Dict]:
        """
        【智能文本切片】
        
        把大段文字切成适合存入向量库的小段。
        
        切片规则：
        1. 按换行符分割成"候选段落"
        2. 逐个合并段落，直到接近目标大小
        3. 记录每个切片来自哪一页
        
        参数:
            pages: extract_text_from_pdf 的返回结果
        
        返回:
            [{"text": "切片内容...", "page": 1, "chunk_index": 0}, ...]
        """
        from app.config import settings
        
        chunks = []
        chunk_size = settings.CHUNK_SIZE      # 目标大小（500字符）
        chunk_overlap = settings.CHUNK_OVERLAP  # 重叠大小（50字符）
        
        for page in pages:
            page_num = page["page"]
            text = page["text"]
            
            # 按换行符分割成段落
            paragraphs = text.split("\n")
            # 去掉空段落
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            current_chunk = ""
            
            for para in paragraphs:
                # 如果当前切片加上新段落会超大小限制
                if len(current_chunk) + len(para) > chunk_size:
                    # 先把当前切片保存（如果不为空）
                    if current_chunk.strip():
                        chunks.append({
                            "text": current_chunk.strip(),
                            "page": page_num,
                        })
                    
                    # 保留末尾 overlap 长度的内容作为新切片的开头（重叠）
                    if len(current_chunk) > chunk_overlap:
                        current_chunk = current_chunk[-chunk_overlap:] + "\n" + para
                    else:
                        current_chunk = para
                else:
                    # 没超大小，继续追加
                    if current_chunk:
                        current_chunk += "\n" + para
                    else:
                        current_chunk = para
            
            # 别忘了页面最后一组切片
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk.strip(),
                    "page": page_num,
                })
        
        print(f"[PDF处理] 切片完成: {len(chunks)} 个片段")
        return chunks

    def embed_and_store(self, chunks: List[Dict], source_file: str) -> int:
        """
        【生成向量并入库】
        
        把文本片段转成向量，存入 Chroma 数据库。
        
        参数:
            chunks: chunk_text 的返回结果
            source_file: 源文件名（存在 metadata 中做来源标记）
        
        返回:
            成功入库的片段数量
        """
        # 获取集合
        collection = vector_db.get_or_create_collection(COURSE_MATERIALS)
        
        # 获取嵌入模型
        model = self._get_embedding_model()
        
        texts = [c["text"] for c in chunks]
        pages = [c["page"] for c in chunks]
        
        # 生成向量（把文字转成数学向量）
        print(f"[PDF处理] 正在生成向量（共 {len(texts)} 段）...")
        embeddings = model.encode(texts, show_progress_bar=True)
        
        # 准备 Chroma 数据
        ids = []
        metadatas = []
        
        for i, (text, page) in enumerate(zip(texts, pages)):
            # 每个片段一个唯一 ID
            chunk_id = f"{source_file}_p{page}_{i}"
            ids.append(chunk_id)
            metadatas.append({
                "source": source_file,
                "page": page,
                "chunk_index": i,
            })
        
        # 批量存入 Chroma
        # Chroma 的 add 方法接受三个数组（长度必须相同）：
        #   ids: 唯一标识符
        #   embeddings: 向量数组
        #   metadatas: 附带的元数据
        #   documents: 原始文本
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            documents=texts,
        )
        
        print(f"[PDF处理] 成功入库 {len(ids)} 个片段")
        return len(ids)

    def process_pdf(self, pdf_path: str) -> Dict:
        """
        【完整处理流程】（一键调用）
        
        把上面三个步骤串起来：提取 → 切片 → 入库
        
        参数:
            pdf_path: PDF 文件路径
        
        返回:
            处理结果统计
        """
        file_name = os.path.basename(pdf_path)
        
        try:
            # 1. 提取文字
            pages = self.extract_text_from_pdf(pdf_path)
            if not pages:
                return {"success": False, "error": "PDF 中没有提取到文字"}
            
            # 2. 切片
            chunks = self.chunk_text(pages)
            if not chunks:
                return {"success": False, "error": "切片后没有有效内容"}
            
            # 3. 入库
            count = self.embed_and_store(chunks, file_name)
            
            return {
                "success": True,
                "file_name": file_name,
                "pages": len(pages),
                "chunks": count,
                "message": f"成功处理 '{file_name}'，共 {count} 个知识片段入库",
            }
        
        except Exception as e:
            error_msg = f"处理 PDF 时出错: {str(e)}\n{traceback.format_exc()}"
            print(f"[PDF处理] 失败: {error_msg}")
            return {"success": False, "error": error_msg}


# ==================== 全局实例 ====================
pdf_processor = PDFProcessor()
