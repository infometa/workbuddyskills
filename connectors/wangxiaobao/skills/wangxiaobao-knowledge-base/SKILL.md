---
name: wangxiaobao-knowledge-base
version: 0.1.0
description: "旺小宝项目知识库：语义检索项目知识 chunk（kb search）、列文档（kb docs）、看文档详情（kb doc）、分页读文档正文（kb doc-content）。search/docs 按当前激活项目隔离；doc/doc-content 按 docId 直取。只读、无副作用。高频命令: xiaobao-cli kb search '<query>' [--k N]; xiaobao-cli kb docs [--title <kw>]; xiaobao-cli kb doc <doc-id>; xiaobao-cli kb doc-content <doc-id> [--offset N] [--limit N]。何时用：用户问项目资料/楼盘知识/销售政策/户型文档/物料/知识库里有没有讲过X/某文档具体写了啥/帮我查下资料。注：search 返回 chunk 不是全文，要逐段读全文用 doc-content 翻页（看 hasMore 续翻）；k 默认 5 上限 20；"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli kb --help"
---

# 旺小宝项目知识库

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（一份共享文档讲清安装 / 登录 / 选项目 / 错误码 / 输出协议等所有 xiaobao-cli 命令通用的前置约定）。

跑 `xiaobao-cli kb *` 检索 / 浏览当前激活项目的知识库（楼盘资料、政策、户型、物料等）。

## 执行前必读

- 必须有有效 token：先调 `xiaobao-cli auth whoami`；未登录就走 `auth login --no-wait` split-flow（见 wangxiaobao-shared）
- **必须有激活项目**：`kb search` / `kb docs` 按当前激活项目（estate）隔离知识；`kb doc` / `kb doc-content` 按 docId 直取（项目级而非顾问级隔离——任何登录用户按 docId 可读）
- **只读**：不写文件、不出报告

---

## 快速索引：意图 → 工具

| 用户意图 | 命令 | 关键参数 |
| --- | --- | --- |
| 知识库里有没有讲某主题 / 找答案 | `xiaobao-cli kb search` | `query` + `--k` |
| 列项目有哪些文档 | `xiaobao-cli kb docs` | `--title 关键字`（可选） |
| 看某文档的元信息 | `xiaobao-cli kb doc` | `<doc-id>` |
| 逐段读某文档全文 | `xiaobao-cli kb doc-content` | `<doc-id>` + `--offset` / `--limit` |

---

## 核心约束

### 1. search 返回 chunk，不是全文

`kb search` 走语义检索，返回最相关的若干 **chunk（片段）**，用于快速回答"知识库里怎么说 X"。要读某篇文档的完整内容，先 `kb docs` 找到 `docId`，再 `kb doc-content` 翻页读全文。

### 2. doc-content 用 offset/limit 翻页

正文可能很长，`kb doc-content` 按 `offset`/`limit` 分页（limit 默认 1000、最大 2000）。响应里 `hasMore=true` 说明还有后续，把 `offset` 加上已读长度继续翻，直到 `hasMore=false`。

### 3. k 默认 5，上限 20

`kb search --k` 控制返回 chunk 数；默认 5，最大 20。问题宽泛时调大 k，精确查证时用小 k。

### 4. 响应字段重点

`kb search`：
```jsonc
{ "code": "0", "data": {
  "query": "学区", "tenantId": "...", "estateId": "...",
  "chunks": [
    { "pageContent": "本项目对口 XX 小学...", "summary": "...", "sourceId": "123", "sourceType": "doc", "metadata": {...} }
  ] } }
```

`kb docs`：`data.docs[]`，每项 `{ docId, title }`。

`kb doc`：`data` = `{ id, title, fileName, description, enabled, parseStatus, createdAt, updatedAt }`。

`kb doc-content`：`data` = `{ docId, offset, limit, totalLength, hasMore, content }`。

CLI 都再包一层 → 实际读 `resp.data.data.*`。

---

## 使用场景示例

### 场景 1：知识库里关于学区怎么说

```bash
xiaobao-cli kb search "学区 对口小学" --k 5
```
把命中的 `chunks[].pageContent` 综合成一段回答，必要时标注来源 `sourceId`。

### 场景 2：找户型相关文档并读全文

```bash
# step 1: 找文档
xiaobao-cli kb docs --title 户型
# step 2: 假设 docId = 88，逐段读
xiaobao-cli kb doc-content 88 --offset 0 --limit 2000
# 若 hasMore=true，继续
xiaobao-cli kb doc-content 88 --offset 2000 --limit 2000
```

### 场景 3：看某文档元信息

```bash
xiaobao-cli kb doc 88
```

---

## 常见错误与排查

- **`error: 'NO_ACTIVE_PROJECT'`** — 跑 `wangxiaobao-switch-project` skill（search/docs 需要激活项目）
- **401 / token 过期** — 走 `auth login --no-wait --force` split-flow 重登
- **search 命中为空 / chunks 为空** — 换关键词或调大 `--k`；该项目知识库可能尚未入库相关内容
- **doc-content 读不全** — 看 `hasMore`，按 `offset` 继续翻页
- **用户其实想问业务数据（客户/来访/业绩）** — 那是 `wangxiaobao-quick-qa`，不是知识库
