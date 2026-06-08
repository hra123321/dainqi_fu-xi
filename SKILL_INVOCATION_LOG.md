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
