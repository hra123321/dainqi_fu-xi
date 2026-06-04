"""
============================================
 Chroma 向量数据库客户端
============================================
【作用】
管理和操作本地 Chroma 向量数据库。
提供初始化、创建/获取子分区（Collection）、
以及基本的增删查接口。

【子分区设计】
按业务类型划分 4 个 Collection：
  course_materials  — 课程教材/课件 PDF 切片
  wrong_questions   — 错题数据
  skill_history     — Skill 源码历史版本
  prompt_history    — 提示词迭代记录

【原理】
Chroma 全程本地运行，数据存储在 data/vector_db/ 目录下。
不需要联网，不需要安装数据库服务器。
"""

import os
from pathlib import Path
from typing import List, Optional, Dict

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


# ==================== 定义子分区名称 ====================
# Collection（集合）类似于数据库中的"表"或"文件夹"
# 不同类别的数据存在不同的集合中
COURSE_MATERIALS = "course_materials"    # 课程教材
WRONG_QUESTIONS = "wrong_questions"      # 错题数据
SKILL_HISTORY = "skill_history"          # 技能代码历史
PROMPT_HISTORY = "prompt_history"        # 提示词迭代

# 所有集合名称列表
ALL_COLLECTIONS = [
    COURSE_MATERIALS,
    WRONG_QUESTIONS,
    SKILL_HISTORY,
    PROMPT_HISTORY,
]


class VectorDBClient:
    """
    【向量数据库客户端】
    
    封装了 Chroma 的所有操作，统一管理数据库连接。
    项目启动时创建此客户端，运行期间复用同一连接。
    """

    def __init__(self, persist_dir: str = None):
        """
        【初始化】— 创建 Chroma 客户端
        
        参数:
            persist_dir: 数据持久化目录路径
        
        Chroma 的 PersistentClient 会把数据自动保存到硬盘，
        下次启动时数据还在。
        """
        self._persist_dir = persist_dir or settings.VECTOR_DB_PATH
        
        # 确保目录存在
        os.makedirs(self._persist_dir, exist_ok=True)
        
        # 创建 Chroma 客户端
        # PersistentClient = 数据会自动保存到硬盘
        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,  # 关闭匿名统计
                allow_reset=True,            # 允许重置数据库
            ),
        )
        
        # 缓存已获取的 Collection 对象（避免重复创建）
        self._collections: Dict[str, chromadb.Collection] = {}

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """
        【获取或创建集合】
        
        如果集合已存在就获取，不存在就新建。
        
        参数:
            name: 集合名称（必须是 ALL_COLLECTIONS 中定义的）
        
        返回:
            Chroma Collection 对象
        """
        if name not in ALL_COLLECTIONS:
            raise ValueError(
                f"不支持的集合名称: '{name}'。"
                f"可用选项: {ALL_COLLECTIONS}"
            )
        
        # 如果已缓存，直接返回（避免重复查询 Chroma）
        if name in self._collections:
            return self._collections[name]
        
        # 获取或创建集合
        # get_or_create_collection = 有就用，没有就新建
        collection = self._client.get_or_create_collection(
            name=name,
            metadata={"description": _get_collection_description(name)},
        )
        
        # 缓存起来
        self._collections[name] = collection
        return collection

    def get_all_collections(self) -> List[Dict]:
        """
        【获取所有集合信息】
        
        返回所有集合的名称、文档数量等统计信息，
        用于管理页面展示。
        """
        result = []
        for name in ALL_COLLECTIONS:
            try:
                col = self.get_or_create_collection(name)
                count = col.count()
                result.append({
                    "name": name,
                    "doc_count": count,
                    "description": _get_collection_description(name),
                })
            except Exception as e:
                result.append({
                    "name": name,
                    "doc_count": -1,
                    "error": str(e),
                })
        return result

    def reset_database(self):
        """
        【重置数据库】（谨慎使用！）
        
        清空所有数据，慎用。
        """
        self._client.reset()
        self._collections.clear()

    @property
    def client(self) -> chromadb.PersistentClient:
        """获取原始 Chroma 客户端（给高级操作使用）"""
        return self._client

    @property
    def persist_dir(self) -> str:
        """获取数据库存储路径"""
        return self._persist_dir


def _get_collection_description(name: str) -> str:
    """获取集合的中文描述（辅助函数）"""
    descriptions = {
        COURSE_MATERIALS: "课程教材与课件 PDF 的切片向量",
        WRONG_QUESTIONS: "学生错题数据",
        SKILL_HISTORY: "技能模块源码历史版本",
        PROMPT_HISTORY: "提示词迭代记录",
    }
    return descriptions.get(name, "")


# ==================== 创建全局实例 ====================
# 项目启动时创建，所有模块共用同一个数据库连接
vector_db = VectorDBClient()
