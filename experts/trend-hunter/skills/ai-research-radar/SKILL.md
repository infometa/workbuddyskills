---
name: ai-research-radar
description: "定时任务：每日研究简报。漏掉重要论文和行业报告？每天帮你盯着，关键信息一条不漏 This skill should be used when the user asks about 定时任务：每日研究简报. Keywords: 每日简报, 研究简报."
---

# 定时任务：每日研究简报

> 漏掉重要论文和行业报告？每天帮你盯着，关键信息一条不漏

## 前置依赖

```bash
pip install pandas requests
```

## 核心能力

### 能力1：AI热点自动检索

每日定时用 `web_search` 搜索AI/大模型最新动态。

### 能力2：简报文件生成

运行脚本将搜索结果整理为结构化简报。

### 能力3：定时任务创建

用 `automation_update` 创建每日9点自动推送。

## 命令列表

| 命令 | 说明 | 用法 |
|------|------|------|
| `generate` | 生成今日简报框架 | `python3 scripts/ai_research_radar_tool.py generate --date DATE --output PATH` |
| `archive` | 归档历史简报 | `python3 scripts/ai_research_radar_tool.py archive --dir PATH` |

## 使用流程

### 步骤 1：创建定时任务

用 `automation_update` 创建每日定时任务：
```
automation_update: 
  name="AI每日研究简报"
  rrule=FREQ=DAILY;BYHOUR=9;BYMINUTE=0
  prompt="执行AI研究简报skill：1.搜索今日AI热点新闻 2.搜索arXiv最新论文 3.搜索GitHub热门AI项目 4.整理成简报文件"
```

### 步骤 2：搜索今日热点

每日执行以下搜索：
```
web_search("AI 大模型 最新进展 today")
web_search("artificial intelligence breakthrough news this week")
web_search("arXiv AI paper highlights")
web_search("GitHub trending AI machine learning")
```
从每个搜索结果中提取：标题、摘要、链接、发布时间。

### 步骤 3：运行脚本整理简报

```bash
python3 scripts/ai_research_radar_tool.py generate \
  --date today \
  --output "/path/to/daily_brief.md"
```

### 步骤 4：用write_to_file保存

将整理好的简报用 `write_to_file` 保存为Markdown文件，包含：
1. 📰 今日AI头条（3-5条热点新闻）
2. 📄 论文速递（2-3篇重要论文，含arXiv链接）
3. 🔧 开源项目（2-3个热门GitHub项目）
4. ⭐ 值得深读（标注1-2条特别值得深入阅读的内容）

## 输出格式

输出格式：Markdown 简报 + 资源链接

## 验收标准

- ✅ 创建定时任务
- ✅ 每日 9 点推送
- ✅ 结构清晰
- ✅ 标注重点

## 场景化适配

根据研究领域调整关键词

## 依赖 Skills

- **arxiv-watcher**
- **github-ai-trends**

## 注意事项

- 所有数据必须来自真实搜索结果或用户提供的文件，**严禁编造数据**
- 数据缺失时标注"数据不可用"而非猜测
- 输出必须保存为文件（`write_to_file`），不能只在对话中输出
- 建议结合人工判断使用，AI 分析仅供参考
