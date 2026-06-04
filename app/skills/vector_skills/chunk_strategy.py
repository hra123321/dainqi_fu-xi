"""
============================================
 切片策略 Skill — 控制 PDF 文本如何切分成知识片段
============================================
【作用】
这个 Skill 负责优化文本切片策略。
如果用户发现切片把完整知识点切断了，
AI 可以优化这里的代码来改进切分逻辑。

【白名单】
本文件位于 app/skills/ 下，AI 可自动修改。
"""

from typing import List, Dict


def smart_chunk(texts: List[str], chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    【智能切片】
    
    将文本按段落边界切分成适合向量化的片段。
    
    参数:
        texts: 要切分的文本列表
        chunk_size: 目标切片大小（字符数）
        overlap: 相邻切片重叠字符数
    
    返回:
        [{"text": "...", "index": 0}, ...]
    """
    chunks = []
    current = ""
    
    for text in texts:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        
        for para in paragraphs:
            if len(current) + len(para) > chunk_size:
                if current.strip():
                    chunks.append({"text": current.strip(), "index": len(chunks)})
                current = current[-overlap:] + "\n" + para if len(current) > overlap else para
            else:
                current = current + "\n" + para if current else para
    
    if current.strip():
        chunks.append({"text": current.strip(), "index": len(chunks)})
    
    return chunks


def validate_chunks(chunks: List[Dict]) -> List[str]:
    """验证切片质量，返回问题列表"""
    issues = []
    for c in chunks:
        if len(c["text"]) < 10:
            issues.append(f"片段 {c['index']} 过短")
        if len(c["text"]) > 2000:
            issues.append(f"片段 {c['index']} 过长")
    return issues
