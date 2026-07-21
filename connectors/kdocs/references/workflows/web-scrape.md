# 网页剪藏

> 抓取网页内容并自动保存为智能文档

**适用场景**：将网页内容保存为金山文档

**触发词**：保存、存到、收藏、剪藏

- 用户消息中同时包含 URL（非金山文档链接）+ 保存意图词

**工具链**：`scrape_url` → `scrape_progress`（轮询至完成）→ `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `scrape_url` | drive | 提交剪藏任务 |
| `scrape_progress` | drive | 轮询任务进度（每 2-5 秒） |
| `get_file_link` | drive | 获取文档链接 |

## 执行流程

> 🎯 **当用户要求保存网页/URL 到金山文档时，直接调用 `scrape_url`。禁止先用 `web_fetch`、`web_search` 或浏览器抓取内容。**

**触发识别**：用户消息中同时包含 **URL**（非金山文档链接）+ **保存/存到/收藏/剪藏** 等意图词时，走此流程。

```
步骤 1: scrape_url(url="https://example.com")
        → 返回 job_id

步骤 2: scrape_progress(job_id=xxx)
        → 轮询（每 2-5 秒），status 判定：
          1  = 完成 → 获得 scrape_file_id（剪藏专用标识）
          -1 = 失败 → 检查 URL 或重试
          其他 = 进行中 → 继续轮询

步骤 3: get_file_link(file_id=scrape_file_id)
        → 返回文档在线链接
```
