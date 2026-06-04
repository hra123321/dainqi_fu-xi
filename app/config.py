"""
============================================
 全局配置文件
============================================
【作用】
这个文件集中管理项目的所有配置项，
其他代码文件通过 from app.config import settings 来读取配置。

【原理】
- 使用 pydantic-settings 库，能从环境变量自动读取配置
- settings 对象在项目启动时创建一次，运行期间只读不改
- API Key 等敏感信息从 .env 文件读取，不上传到 Git

【配置分类】
1. DeepSeek API 相关（Key、模型名、接口地址）
2. 生成参数（温度、最大 token 数等 — 固定值提升缓存命中）
3. 缓存策略（内存缓存 TTL、大小）
4. 向量知识库（路径、切片大小）
5. 技能目录（白名单、优化阈值）
6. Edge 浏览器路径
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    【类说明】
    BaseSettings 是 pydantic-settings 提供的基础类。
    继承它之后，这个类的属性会自动从环境变量或 .env 文件读取。
    比如 DEEPSEEK_API_KEY 会自动读取环境变量中的 DEEPSEEK_API_KEY。
    """

    # ==================== 1. DeepSeek API 配置 ====================
    # 【API Key】从 .env 文件读取，不要写真实值在这里
    DEEPSEEK_API_KEY: str = ""

    # 【API 地址】DeepSeek 兼容 OpenAI 的接口格式
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # 【模型名称】
    # Flash：轻量快速版，适合常规问题（选择题、简单问答）
    # Pro：增强推理版，适合复杂计算（电路推导、高数）
    MODEL_FLASH: str = "deepseek-chat"          # Flash 模型名
    MODEL_PRO: str = "deepseek-reasoner"        # Pro 模型名

    # ==================== 2. 生成参数（固定值！提升缓存命中率） ====================
    # 【temperature】"创造力"参数，0=严格按事实，1=自由发挥
    # 固定为 0.7 是"既有一定创造性又不至于胡扯"的平衡点
    TEMPERATURE: float = 0.7

    # 【top_p】另一种"多样性"控制，与 temperature 配合使用
    TOP_P: float = 0.9

    # 【max_tokens】AI 一次回答的最大字数（不是字符数，是 token 数）
    # 中文大约 1 个汉字 = 2 个 token，所以 2048 ≈ 1000 字
    MAX_TOKENS: int = 2048

    # 【频率/存在惩罚】防止 AI 重复自己说的话
    FREQUENCY_PENALTY: float = 0.0
    PRESENCE_PENALTY: float = 0.0

    # ==================== 3. 缓存配置 ====================
    # 【内存缓存 TTL】缓存存活时间（秒），300 秒 = 5 分钟
    MEMORY_CACHE_TTL: int = 300

    # 【内存缓存最大条数】防止缓存占用太多内存
    MEMORY_CACHE_MAXSIZE: int = 1000

    # ==================== 4. 向量知识库配置 ====================
    # 【向量库存储路径】Chroma 数据库文件存在哪里
    VECTOR_DB_PATH: str = str(Path("data/vector_db").absolute())

    # 【切片大小】上传的 PDF 每多少字切成一小段（字符数）
    CHUNK_SIZE: int = 500

    # 【切片重叠】相邻切片重叠多少字，防止关键内容被切到边界丢失
    CHUNK_OVERLAP: int = 50

    # 【召回数量】用户提问时从知识库找回几段相关文本
    RETRIEVAL_TOP_K: int = 5

    # ==================== 5. Skill 自迭代配置 ====================
    # 【技能目录】AI 技能代码存放的目录（也是写操作白名单）
    SKILL_DIR: str = "app/skills"

    # 【写操作白名单】AI 只能修改这个列表里的目录
    SKILL_WHITELIST: list = ["app/skills"]

    # 【自动优化阈值】错题/异常累计达到这个数量就触发 AI 自动优化
    AUTO_OPTIMIZE_THRESHOLD: int = 10

    # ==================== 6. Edge 浏览器配置 ====================
    # 【Edge 路径】Edge 浏览器的安装位置
    # 项目要求：强制使用 Edge，不能使用 Chrome/Firefox 等
    EDGE_PATH: str = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    # ==================== 7. 模型配置 ====================
    class Config:
        """
        【内部配置】
        env_file=".env" 表示自动从项目根目录的 .env 文件读取配置
        env_file_encoding="utf-8" 指定文件编码
        """
        env_file = ".env"
        env_file_encoding = "utf-8"


# ==================== 创建全局单例 ====================
# 【关键语法】
# 这行代码在项目启动时执行一次，创建一个 settings 对象
# 其他文件通过 "from app.config import settings" 来使用
# 这叫"单例模式" — 整个程序只有一个配置实例
settings = Settings()
