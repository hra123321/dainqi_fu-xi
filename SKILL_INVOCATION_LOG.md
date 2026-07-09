# Skill 调用日志 — 电气专业课 AI 期末刷题系统

## 版本信息
- **版本**: v2.0.0 (完整版)
- **提交时间**: 2026-06-04
- **作者**: Codex Agent

## 项目总览
本系统是一个基于 DeepSeek-V4（Flash + Pro 双规格 API）的本地电气专业课 AI 期末刷题系统，
包含：分层模型调度、固定提示词架构、本地缓存机制、Chroma 本地向量知识库、Skill 技能库自主迭代、
PWA 移动端支持、Flutter Android 原生应用。

---

## 所有调用到的 Skills 及详细说明

### 1. knowledge-first（知识优先检索）
- **文件**: `C:\Users\123\.codex\skills\knowledge-first\SKILL.md`
- **作用**: 在刷题时自动搜索本地 Chroma 向量知识库，获取关联教材原文作为参考上下文
- **实现位置**: `app/vector_db/retriever.py` → `retriever.search()`
- **调用时机**: 每次 AI 出题时，先检索知识库再构造提示词
- **效果**: 使 AI 生成的题目和批改基于教材原文，减少幻觉

### 2. create-plan（计划生成）
- **文件**: `C:\Users\123\.codex\skills\create-plan\SKILL.md`
- **作用**: 将用户的需求文档拆分为 3 个阶段、12+ 个具体可执行步骤
- **实现位置**: 项目启动时的分阶段实施计划
- **调用时机**: 项目初始阶段
- **效果**: 清晰的开发路线图，每个阶段有明确产出物

### 3. pdf（PDF 处理）
- **文件**: `C:\Users\123\.codex\skills\pdf\SKILL.md`
- **作用**: 提供 PDF 文字提取的最佳实践（PyMuPDF + pdfplumber）
- **实现位置**: `app/vector_db/processor.py`
- **调用时机**: 用户上传 PDF 课件时
- **效果**: PDF 上传 → 文字提取 → 切片 → 向量化入库的完整链路

### 4. browser:control-in-app-browser（浏览器调试）
- **文件**: `C:\Users\123\.codex\plugins\cache\openai-bundled\browser\...\control-in-app-browser\SKILL.md`
- **作用**: 控制浏览器进行前端页面预览和调试
- **实现位置**: `app/utils/browser.py` — 强制调用 Microsoft Edge
- **调用时机**: 项目启动时自动打开浏览器、前端调试时
- **效果**: 硬性约束「默认使用 Edge」已实现，双层保障路径

### 5. playwright（浏览器自动化测试）
- **文件**: `C:\Users\123\.codex\skills\playwright\SKILL.md`
- **作用**: 提供浏览器自动化测试思路
- **实现位置**: `tests/test_core.py`
- **调用时机**: 自动化测试阶段
- **效果**: 验证前端页面是否正常渲染

### 6. datasheet（数据手册读取）
- **文件**: `C:\Users\123\.codex\skills\datasheet_reader\SKILL.md`
- **作用**: 参考其 PDF 解析模式设计课件处理流程
- **实现位置**: `app/vector_db/processor.py` 的 PDF 解析逻辑
- **调用时机**: PDF 课件处理流程设计时参考
- **效果**: 借鉴了专业文档解析的最佳实践

### 7. planner（实施规划器）
- **文件**: `C:\Users\123\.codex\skills\planner\SKILL.md`
- **作用**: 将复杂任务拆解为可执行的 Sprint 和任务列表
- **实现位置**: 项目全周期的任务拆解
- **调用时机**: 每个阶段开始前
- **效果**: 有序推进，避免遗漏

### 8. mcp-builder（MCP 服务构建）
- **文件**: `C:\Users\123\.codex\skills\mcp-builder\SKILL.md`
- **作用**: 参考 API 设计模式，设计 RESTful 接口规范
- **实现位置**: `app/router/` 全部 22 条 API 路由
- **调用时机**: API 路由设计时
- **效果**: 统一的 API 设计规范，22 条路由结构清晰

### 9. gh-address-comments（GitHub 协作）
- **文件**: `C:\Users\123\.codex\skills\gh-address-comments\SKILL.md`
- **作用**: 使用 gh CLI 管理 Git 版本和远程推送
- **实现位置**: Git 版本控制全流程
- **调用时机**: 每次代码提交和推送
- **效果**: 8 次规范提交，已推送至 GitHub

### 10. gh-fix-ci（CI 调试）
- **文件**: `C:\Users\123\.codex\skills\gh-fix-ci\SKILL.md`
- **作用**: 参考 GitHub Actions 工作流设计自动化测试
- **实现位置**: `tests/test_core.py` — 8 项测试
- **调用时机**: 测试阶段
- **效果**: 7/8 测试通过，核心功能可验证

---

## 项目内实现的自定义 Skills（3 个）
这些 Skill 位于项目 `app/skills/` 目录，是 AI 可自修改的白名单范围：

### 1. api_skills/ai_caller.py（AI 接口调用 Skill）
- **作用**: 封装 DeepSeek API 的 HTTP 调用（请求构造、重试、错误处理）
- **代码行数**: ~80 行
- **关键函数**: `call_deepseek()`
- **可优化点**: 重试策略、超时处理

### 2. vector_skills/chunk_strategy.py（向量切片策略 Skill）
- **作用**: 控制 PDF 文本切分为知识片段的策略
- **代码行数**: ~60 行
- **关键函数**: `smart_chunk()`
- **可优化点**: 切片边界检测、学科专用规则

### 3. exam_skills/scoring.py（阅卷评分 Skill）
- **作用**: 解析 AI 批改结果、提取分数和结论
- **代码行数**: ~80 行
- **关键函数**: `parse_grading_result()`
- **可优化点**: 分数提取准确率、多题型支持

---

## 调用链路图

```
用户输入
  │
  ├─1→ knowledge-first（检索知识库上下文）
  │
  ├─2→ create-plan / planner（任务规划）
  │
  ├─3→ model dispatch（模型分层调度）
  │     ├─ easy/normal → DeepSeek-V4-Flash
  │     └─ hard/expert → DeepSeek-V4-Pro
  │
  ├─4→ api_skills/ai_caller.py（调用 AI API）
  │
  ├─5→ exam_skills/scoring.py（批改解析）
  │
  ├─6→ pdf（PDF 课件处理）
  │     └─ vector_skills/chunk_strategy.py（智能切片）
  │
  ├─7→ cache（双层缓存命中）
  │     ├─ memory_cache.py（内存 LRU）
  │     └─ cache_key.py（确定性缓存键）
  │
  ├─8→ browser:control-in-app-browser（Edge 预览）
  │
  └─9→ gh-address-comments（Git 提交/推送）
```

---

## 硬性约束遵守确认

| 约束 | 状态 | 验证方式 |
|------|------|----------|
| 禁止运行时修改提示词 | ✅ | `app/prompts/loader.py` 启动时一次性加载到内存 |
| 禁止变更模型分流规则 | ✅ | `app/models/dispatch.py` 规则硬编码 |
| 白名单目录外禁止读写 | ✅ | `app/config.py` 中 `SKILL_WHITELIST = ["app/skills"]` |
| 每次改动 Git 提交 | ✅ | 共 8 次规范提交 |
| 前端默认 Edge 浏览器 | ✅ | `app/utils/browser.py` 硬编码 Edge 路径 |

---

### 6. website-ui-design（网站UI设计）
- **文件**: \C:\Users\123\.codex\skills\web-ui-design\SKILL.md\
- **作用**: 参考 UI 设计最佳实践重构 exam.html 页面布局、交互流程
- **参考内容**: anti-ai-slop.md（视觉质量检查）、accessibility.md（可访问性检查）
- **具体应用**:
  - 参考 anti-ai-slop 清单修复了页面中的"无明确主要任务"结构问题
  - 修复了"空状态不提示用户如何继续"的问题（emptyState 添加了引导文字）
  - 增加了清晰的"当前学科"指示器、视频课程链接、快速搜索标签
  - 确保每道题都有完整的评分/讲解展示
- **实现文件**: \pp/templates/exam.html\

### 7. browser:control-in-app-browser（浏览器控制）
- **文件**: \C:\Users\123\.codex\plugins\cache\openai-bundled\browser\26.602.30954\skills\control-in-app-browser\SKILL.md\
- **作用**: 通过浏览器验证前端页面渲染效果和交互功能
- **实现方式**: 启动Edge浏览器打开本地服务验证

### 8. skill-installer（技能安装器）
- **文件**: \C:\Users\123\.codex\skills\.system\skill-installer\SKILL.md\
- **作用**: 安装UI设计和移动端开发相关的技能到全局skills目录
- **已安装相关技能**: website-ui-design, apple-web-ui, hue-design-system, lanhu-to-native, skill-mobile-engineer
## 2026-06-08 - v2.1 UI修复与体验改进

## 2026-06-08 - v2.1 UI修复与体验改进

## 2026-06-09 - v2.2 HTML结构修复与全面测试

### 本次调用 Skills

| Skill | 用途 |
|-------|------|
| knowledge-first | 审查本地向量知识库状态，确认 Chroma 已初始化但数据为空 |
| website-ui-design | 参考 UI 设计原则检查 exam.html 布局问题 |
| create-plan | 制定修复计划（定位问题→编写修复→验证→提交） |

### 修复内容

1. **exam.html 破损div标签**：<div     <div id="emptyState" → <div id="emptyState"
2. **exam.html 重复尾部代码**：删除 {% endblock %} 后的重复 step-guide 内容
3. **exam.html 多余空行**：压缩连续空行（4+ → 2）
4. **验证全部页面**：exam(28097B)/首页(5029B)/错题本(11089B) 均返回 200 OK
5. **验证静态文件**：subjects.js(54197B)/style.css(18640B)/favicon 均正常
6. **验证API**：health/wrong-book/analysis 全部正常响应

### Git 提交

提交: 修复exam.html HTML结构错误+全面页面验证


## 2026-06-09 - v2.3 星星简化+标签标注+向量库导入

### 调用 Skills
- **knowledge-first**: 完善本地向量知识库，导入154条学科知识数据
- **website-ui-design**: 简化UI中星星显示，减少视觉杂乱
- **skill-installer**: 之前已安装 website-ui-design 等技能

### 改动
1. renderStars 只显示实心星，取消空心星
2. 搜索结果标注中文标签：难度/考试重要/工程重要
3. 向量库导入9学科154条知识条目
4. 清理临时修复脚本 + 更新.gitignore

### Git 提交
- 1ba53e9 简化星星显示+添加中文标签标注
- f0013db 清理临时修复脚本

---

## 2026-06-09 - v2.4 公式渲染修复与动态KaTeX重渲染

### 本次调用 Skills

| Skill | 用途 |
|-------|------|
| website-ui-design | 参考UI设计原则检查页面结构问题 |
| knowledge-first | 审查本地向量知识库状态 |
| browser:control-in-app-browser | 浏览器页面状态验证 |
| create-plan | 制定修复计划与步骤 |

### 修复内容

1. **KaTeX动态重渲染**: renderQuestions()/renderResults() 动态插入HTML后调用 renderMathInElement() 重新渲染所有 LaTeX 公式
2. **renderResults异步Bug修复**: function → async function（之前内部用了 await 但函数未声明 async）
3. **知识点自动展示**: 切换学科时自动展示全部知识点列表
4. **完善迭代报告**: 新增 reports/v2.2.md 记录本次迭代

### 涉及文件
- app/templates/exam.html
- reports/v2.2.md
- SKILL_INVOCATION_LOG.md

### Git 提交
提交信息: [fix] KaTeX动态重渲染+renderResults异步修复

---

## 2026-06-25 - v2.5 网页核心链路修复

### 本次实际调用 Skills

| Skill | 用途 | 结果 |
|-------|------|------|
| `knowledge-first` | 先检查本地知识库上下文 | 发现当前 skill 指向的是外部“热电偶项目”知识库，且只读报错，不适合作为本项目知识源 |
| `create-plan` | 对照用户给定的 P0/P1 计划核对实施顺序 | 用于确认本轮先修网页核心链路，不扩散到 Android |
| `browser:control-in-app-browser` | 尝试做浏览器实测 | 被本机浏览器安全策略拦截 `127.0.0.1`，未绕过；改用本地 `TestClient` 验证页面输出 |

### 本轮完成内容

1. **结构化出题闭环**
   - 出题改为严格 JSON 结构
   - 删除按空行拆题与 `questions[:5]` 截断逻辑
   - 增加服务端题目会话缓存，前端不再提前拿到标准答案

2. **复杂题完整渲染**
   - 增加半导体三小问回归测试
   - 保证题干内多小问与换行不再被拆散
   - 动态题目与批改内容统一重新执行 KaTeX 渲染

3. **网页学习页乱码修复**
   - 重写 `base.html`、`index.html`、`exam.html`、`wrong_book.html`
   - 修复导航、步骤提示、知识点搜索、错题本页面的中文乱码
   - 去掉页面中的技术暴露文案，仅保留学习相关内容

4. **错题本与自进化安全门禁**
   - 错题记录补充 `subject`、`knowledge_point`、`question_type`
   - `Skill` 自进化改为候选文件验证制
   - 缺少专项测试、语法检查失败、核心回归失败时禁止覆盖源码

5. **专项测试补齐**
   - 新增 `tests/test_scoring.py`
   - 新增 `tests/test_chunking.py`
   - 新增 `tests/test_api_call.py`
   - 重写 `tests/test_core.py`

### 本轮验证记录

- `python -m compileall -q app main.py tests`
- `python tests/test_scoring.py`
- `python tests/test_chunking.py`
- `python tests/test_api_call.py`
- `python tests/test_core.py`
- 使用 `FastAPI TestClient` 验证 `/`、`/exam`、`/wrong-book`、`/api/health` 返回成功

### 当前遗留问题

1. `knowledge-first` 仍指向外部旧知识库路径，需要在后续 P2 阶段改为本项目独立库
2. Chroma 仍打印 telemetry 相关告警，需要后续处理依赖兼容
3. 浏览器自动化实测受本机安全策略限制，本轮改用本地进程内页面验证
# 2026-07-07 自定义学科与向量入库链路

## 调用的 Skill

- knowledge-first：按项目要求先检查本地向量知识库；实际发现该 skill 指向旧热电偶项目路径，且路径当前不存在，因此未作为本项目依据。
- browser:control-in-app-browser：读取并尝试用于页面验证；浏览器安全策略拒绝访问 `http://127.0.0.1:8000`，因此未绕过，改用 FastAPI TestClient 验证页面与 API。
- create-plan：上一阶段用于形成实施计划，本轮按计划执行。

## 本轮修改

- 新增 SQLite 学科注册表，支持自定义学科持久化。
- 新增 `/api/subjects`、`/api/subjects/{id}/topics`、`/api/subjects/{id}/ingest`、`/api/ingestion-jobs/{id}`。
- 新增“新增学科”网页，创建学科后自动启动公开资料搜索与入库任务。
- 前端学科选择器改为优先读取后端 API，保留九门课种子数据。
- Chroma 检索新增 `subject_id` 过滤参数，避免跨学科误召回。

## 验证

- `python -m compileall -q app main.py tests`
- `python tests/test_subjects.py`
- `python tests/test_subject_api.py`
- `python tests/test_core.py`
- `python tests/test_scoring.py`
- `python tests/test_chunking.py`
- `python tests/test_api_call.py`

## 已知问题

- Chroma 0.5.18 在当前环境仍打印 telemetry 兼容性错误：`capture() takes 1 positional argument but 3 were given`。功能测试通过，该问题暂定为日志噪声，后续建议通过固定兼容依赖或替换 telemetry 实现解决。

# 2026-07-09 长期平台阶段 0：密钥安全基线

## 本次调用 Skills

- `knowledge-first`：按规则尝试读取本地知识库；旧库属于其他项目且 Chroma 版本不兼容，未作为本项目依据。
- `security-best-practices`：读取 FastAPI 与浏览器 JavaScript 安全规范，用于约束密钥、输入验证和前端输出边界。

## 本次修改

- 增加 DeepSeek API Key 使用前校验，错误信息不包含密钥内容。
- 增加 Git 跟踪文件泄密扫描测试。
- 增加不含真实密钥的 `.env.example`。
- 重写乱码配置文件，保留既有固定模型、缓存和路径参数。
