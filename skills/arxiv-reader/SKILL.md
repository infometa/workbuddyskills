---
name: arxiv-reader
description: 利用python，指定某个arxiv_id/url， 基于 LLM Agent 对这篇arxiv论文进行分类与深度阅读，直接print打印阅读笔记
description_zh: "基于 LLM 的 ArXiv 论文分类与深度阅读工具"
description_en: "LLM-based ArXiv paper classification and in-depth reading tool"
version: 1.0.3
metadata:
  openclaw:
    requires:
      bins:
        - uv
      env:
        - LLM_API_KEY
        - LLM_BASE_URL
        - LLM_TEMPERATURE
        - LLM_MAX_TOKENS
    primaryEnv: LLM_API_KEY
---

## 快速开始

### 1. 配置 `.env`

```bash
cp .env.example .env   # 或直接编辑 .env
```

确定你已经配置了：
- `LLM_API_KEY` — OpenAI 或兼容 API 的密钥
- `LLM_BASE_URL` — API 地址

### 2. 运行

```bash
uv venv
uv pip install -r "{baseDir}/requirements.txt"

# 单篇论文模式：指定 arxiv_id 或 URL
uv run python "{baseDir}/main.py" --arxiv-id 2401.12345
uv run python "{baseDir}/main.py" --arxiv-id https://arxiv.org/abs/2401.12345
uv run python "{baseDir}/main.py" --arxiv-id https://arxiv.org/pdf/2401.12345.pdf

# 指定以特定类别阅读
uv run python "{baseDir}/main.py" --arxiv-id xxxx --category yyy

# 查看所有类别
uv run python "{baseDir}/main.py" --list

```

## 添加新的阅读分类

在 `skills/` 下新建文件夹，包含两个文件：

```
skills/your_new_category/
├── _metadata.md        # 分类描述（告诉 Classifier 什么论文属于这个类别）
└── reading_prompt.md   # 阅读指南（告诉 Reader Agent 重点关注什么）
```

重启即可自动识别，无需修改任何代码。

## Python包

- LangChain 1.x — Agent 框架（基于 LangGraph）
- LangChain OpenAI — LLM 接口（兼容 DeepSeek 等 OpenAI-compatible API）
- arxiv — 官方 Python 库
- arxiv-to-prompt 获取arxiv论文latex源码
