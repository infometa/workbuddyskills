# SearchWiki

## 接口描述

TAPD API 不支持 Wiki 全文搜索，通过 `scripts/search_wiki.py` 实现本地搜索。

原理：先将全部 Wiki 同步到本地缓存，再用关键词在本地搜索，返回匹配的内容片段和链接。

默认拉取最新的 5000 篇（按最后修改时间倒序），可通过环境变量 `PLUGIN_TAPD_WIKI_MAX` 调整。

## 1. 同步 Wiki（首次使用或需要更新时）

```bash
python3 ~/.codebuddy/skills/tapd-openapi/scripts/search_wiki.py sync

# 自定义最大拉取数量
PLUGIN_TAPD_WIKI_MAX=500 python3 ~/.codebuddy/skills/tapd-openapi/scripts/search_wiki.py sync
```

Wiki 缓存保存在 `~/.tapd-wiki-cache/{workspace_id}/` 目录，每篇 Wiki 一个 `.md` 文件。

## 2. 搜索 Wiki

```bash
# 全文搜索（标题 + 正文）
python3 ~/.codebuddy/skills/tapd-openapi/scripts/search_wiki.py search 关键词

# 多关键词（取交集）
python3 ~/.codebuddy/skills/tapd-openapi/scripts/search_wiki.py search 关键词1 关键词2

# 仅搜索标题
python3 ~/.codebuddy/skills/tapd-openapi/scripts/search_wiki.py search 关键词 --title-only
```

## 3. 进一步搜索（可选）

同步完成后，也可以直接用 grep 等工具搜索缓存文件：

```bash
grep -rl '关键词' ~/.tapd-wiki-cache/
cat ~/.tapd-wiki-cache/{workspace_id}/{wiki_id}.md
```

## 返回示例

```
找到 3 篇匹配的 Wiki（关键词: 部署）

### 1. 生产环境部署指南
- 链接: https://www.tapd.cn/31372104/markdown_wikis/show/#1131372104001000001
- 最后修改: 2025-03-10 14:30:00 by dev
- 匹配片段:
  > 前置准备工作完成后即可开始操作。 本文档介绍生产环境的**部署**流程，包括构建、发布和回滚操作。 具体步骤如下。
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| name | Wiki 标题 |
| url | Wiki 链接，格式 `https://www.tapd.cn/{workspace_id}/markdown_wikis/show/#{wiki_id}` |
| modified | 最后修改时间 |
| modifier | 最后修改人 |
| snippets | 匹配的内容片段（关键词所在句子及前后各一句，关键词 **加粗** 显示） |
