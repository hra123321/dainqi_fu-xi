"""
============================================
 API 数据模型定义（Pydantic Schemas）
============================================
【作用】
定义所有 API 接口的请求和响应数据格式。
FastAPI 自动用这些模型校验请求数据、生成 API 文档。

【原理】
Pydantic 模型 = 数据的"模板"或"合同"。
- 请求进来时：按模板检查格式是否正确
- 响应出去时：按模板保证返回的字段齐全
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


QuestionType = Literal[
    "single_choice",
    "multiple_choice",
    "judge",
    "calculation",
    "short_answer",
]


# ==================== 请求模型（客户端 → 服务器） ====================

class QuestionGenerateRequest(BaseModel):
    """
    【出题请求】
    用户从前端发来的"帮我出题"请求
    
    字段说明：
      knowledge_point: 要考的知识点（如"戴维南定理"）
      difficulty: 难度标签，控制用 Flash 还是 Pro
      count: 一次性出几道题
    """
    knowledge_point: str = Field(
        ...,                          # ... 表示"必填"
        description="知识点名称",
        min_length=1,
        max_length=200,
    )
    difficulty: str = Field(
        default="normal",             # 默认中等难度
        description="难度标签: easy/normal/hard/expert",
    )
    count: int = Field(
        default=5,
        description="出题数量",
        ge=1,                         # ge = Greater or Equal（≥1）
        le=20,                        # le = Less or Equal（≤20）
    )
    subject: str = Field(default="", description="所属学科")


class AnswerSubmitRequest(BaseModel):
    """
    【提交作答请求】
    用户做完题后提交答案
    
    字段说明：
      question_id: 题目的唯一编号
      question_type: 题型（objective=客观题, advanced=高阶题）
      question: 题目原文
      student_answer: 用户写的答案
      correct_answer: 标准答案（客观题用）
      reference_answer: 参考答案（高阶题用）
      knowledge_context: 相关的知识点参考文本
    """
    question_id: str = Field(..., description="题目 ID")
    question_type: Optional[str] = Field(
        default=None, description="题型: objective/advanced（兼容旧前端）"
    )
    question: Optional[str] = Field(default=None, description="题目内容（兼容旧前端）")
    student_answer: str = Field(..., description="学生答案")
    correct_answer: Optional[str] = Field(
        default=None, description="标准答案（兼容旧前端）"
    )
    reference_answer: Optional[str] = Field(
        default=None, description="参考答案（兼容旧前端）"
    )
    knowledge_context: str = Field(
        default="", description="知识点参考上下文"
    )
    subject: str = Field(default="", description="所属学科")
    knowledge_point: str = Field(default="", description="知识点名称")


class BatchAnswerItem(BaseModel):
    """批量批改中的单题答案"""

    question_id: str = Field(..., description="题目 ID")
    student_answer: str = Field(..., description="学生答案")
    subject: str = Field(default="", description="所属学科")
    knowledge_point: str = Field(default="", description="知识点名称")


class BatchGradeRequest(BaseModel):
    """批量批改请求"""

    topic: str = Field(default="", description="当前知识点")
    subject: str = Field(default="", description="当前学科")
    answers: List[BatchAnswerItem] = Field(default_factory=list)


class KnowledgeUploadRequest(BaseModel):
    """
    【知识库上传请求】
    上传课件到知识库
    
    注意：PDF 文件本身用 UploadFile 处理，
    这里只放文本相关的元数据
    """
    category: str = Field(
        default="course_materials",
        description="存入哪个分类: course_materials/wrong_questions",
    )


class KnowledgeSearchRequest(BaseModel):
    """
    【知识检索请求】
    根据问题/关键词搜索知识库
    """
    query: str = Field(
        ..., description="搜索关键词或问题"
    )
    category: str = Field(
        default="course_materials",
        description="在哪个分类中搜索",
    )
    top_k: int = Field(
        default=5,
        description="返回几条结果",
        ge=1,
        le=20,
    )
    subject_id: str = Field(default="", description="限定检索的学科 ID")


# ==================== 响应模型（服务器 → 客户端） ====================

class QuestionItem(BaseModel):
    """
    【单道题目】
    返回给前端的题目数据
    
    字段说明：
      id: 唯一编号
      question_text: 题目正文
      type: 题型标识
      difficulty: 难度
    """
    id: str
    question_text: str
    type: QuestionType
    difficulty: str
    options: List[str] = Field(default_factory=list)


class GeneratedQuestionPayload(BaseModel):
    """模型返回的完整题目结构，含服务端保留字段"""

    question_text: str = Field(..., min_length=1)
    type: QuestionType
    options: List[str] = Field(default_factory=list)
    answer: str = Field(default="")
    reference_answer: str = Field(default="")
    explanation: str = Field(default="")


class GeneratedQuestionSet(BaseModel):
    """模型返回的结构化题目集合"""

    questions: List[GeneratedQuestionPayload] = Field(default_factory=list)


class QuestionGenerateResponse(BaseModel):
    """
    【出题响应】
    AI 出完题后返回的数据
    """
    questions: List[QuestionItem]
    knowledge_context: str    # 用的哪些知识点参考
    model_used: str           # 用了 Flash 还是 Pro


class GradingResult(BaseModel):
    """
    【批改结果】
    AI 批改完后的评分数据
    """
    question_id: str
    score: float              # 分数（客观题 0 或 100，高阶题 0-100）
    conclusion: str           # "正确" / "错误"
    analysis: str             # AI 的详细解析
    model_used: str           # 用了哪个模型


class KnowledgeChunk(BaseModel):
    """
    【知识片段】
    检索到的知识库文档片段
    """
    text: str                 # 文本内容
    source: str               # 来源（文件名等）
    score: float              # 相关度分数


class KnowledgeSearchResponse(BaseModel):
    """
    【知识检索响应】
    """
    results: List[KnowledgeChunk]
    total: int
