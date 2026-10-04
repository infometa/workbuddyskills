---
name: yanxu-publisher
description: 通过言序 MCP 完成微信公众号文章的建稿与发布。适用于查询已绑定的公众号、查询样式主题、创建文章草稿、推送到公众号草稿箱。触发场景：用户提到公众号文章、排版、建稿、草稿箱、言序。
---

# 言序 · 微信公众号建稿与发布

言序是专业级中文排版引擎，把结构化稿件渲染成排版后的公众号文章并存入草稿箱。
完整流程是三步：**查账号/主题 → 建稿（拿到 info_id）→ 发布到草稿箱**。

## 工具总览

| 工具 | 用途 | 关键返回 |
|---|---|---|
| `list_wechat_accounts` | 查询当前用户已绑定的公众号 | `account_id`、`default_theme_id` |
| `list_theme_styles` | 查询可用的样式主题（系统 + 自建） | `theme_id`、样式名称与描述 |
| `create_article` | 创建文章草稿 | `info_id`（发布时必用） |
| `publish_article` | 发布到指定公众号草稿箱 | 发布结果 |

## 推荐工作流

1. **建稿前**先调 `list_wechat_accounts` 确认账号与默认主题；用户只有一个公众号时，`publish_article` 的 `account_id` 可省略。
2. 用户没有指定主题时，使用账号的 `default_theme_id`（发布时省略 `theme_id` 即可）；指定了主题名称时，先 `list_theme_styles` 把名称映射成 `theme_id`。
3. 调 `create_article` 建稿，**保存返回的 `info_id`**。
4. **建稿完成后先停下**，向用户复述：文章标题 + `info_id` + 目标公众号名 + 所用主题名，等用户确认后再调 `publish_article`。
   - 发布目标是公众号**草稿箱**（可删除、不群发），但它是一次真实写入外部系统的操作，**不要在建稿的同一条回复里连着做完**。
   - 例外：用户在同一句话里已明确要求「写完直接发到草稿箱」时，可跳过复述直接发布。
   - 用户说「先建稿 / 先别发 / 给我看看」时，只执行到第 3 步，把 `info_id` 交给用户待命。

## create_article 参数

必填：`title`、`intro`、`chapters`。可选：`abstract`、`cover_img`。

- `title`：**不超过 30 字**，超限会被拒绝。
- `abstract`：**不超过 100 字**，建议写有信息量的摘要，不要写"本文介绍了……"。
- `intro`：导语，无字数限制，可与摘要一致。
- `cover_img`：封面图 URL。远程 URL 会被服务端下载到静态目录；**可留空**——无文章封面时，发布依次回落到公众号默认封面、系统封面。
- `chapters`：章节列表，**不能为空**。每章结构：

  | 字段 | 类型 | 必填 | 说明 |
  |---|---|---|---|
  | `type` | string | 否 | 建议固定为 `"chapter"` |
  | `title` | string | 是 | 章节标题，会被渲染成小标题 |
  | `blocks` | array | 是 | 块列表，按数组顺序渲染 |

  注意：**`intro` 与各章 `title` 不需要写成 block**——导语由顶层 `intro` 字段渲染，章节标题由 `title` 渲染，重复写成块会出现两层标题。

### 图片体积上限（硬约束）

生成或挑选图片时必须控制体积，超限会导致建稿失败：

- **封面图（`cover_img`）不超过 2MB。**
- **正文图片（`image` 块）单张不超过 1MB。**
- 推荐做法：正文配图压到 200KB～800KB、长边 1200px 以内；封面压到 1MB 以内。优先用 JPEG/WebP，PNG 仅用于需要透明底的场景。
- 生成图片后先确认体积再调用工具；超限时重新生成或压缩，不要直接提交。

### blocks 块类型

| type | 字段 | 说明 |
|---|---|---|
| `paragraph` | `content` | 正文段落，纯文本，用换行分段 |
| `image` | `url`、`alt`（可选） | 图片，必须传服务端可访问的 http(s) URL 或服务端本地路径；**单张 ≤1MB** |
| `list` | `style`、`items` | `style` 为 `unordered` 或 `ordered`，`items` 为字符串数组 |
| `table` | `headers`、`rows` | `headers` 为字符串数组，`rows` 为二维字符串数组 |

注意：公众号对表格的渲染效果不佳，结构化对比数据优先改写成段落叙述，确有必要再用 `table` 块。
正文使用纯文本与块结构表达，不要把 HTML 标签塞进 `content`。

### 完整 payload 示例

顶层是**扁平结构**——`intro` / `chapters` 与 `title` 同级，**不要套 `content` 包裹**。

```json
{
  "title": "文章标题",
  "abstract": "外部摘要，不超过 100 字",
  "cover_img": "https://example.com/cover.jpg",
  "intro": "这里是文章导语……",
  "chapters": [
    {
      "type": "chapter",
      "title": "章节 1",
      "blocks": [
        { "type": "paragraph", "content": "第一段正文……" },
        { "type": "image", "url": "https://example.com/a.jpg", "alt": "图片说明" },
        { "type": "list", "style": "unordered", "items": ["第一项", "第二项"] },
        { "type": "table", "headers": ["列 1", "列 2"], "rows": [["a", "b"], ["c", "d"]] },
        { "type": "paragraph", "content": "块可以继续追加……" }
      ]
    },
    {
      "type": "chapter",
      "title": "章节 2",
      "blocks": [
        { "type": "paragraph", "content": "第二章正文……" }
      ]
    }
  ]
}
```

要点：块类型只有 4 种（`paragraph` / `image` / `list` / `table`）；章节之间是平级的，**不支持章节嵌套**，块内也不能再嵌块。

## publish_article 参数

- `info_id`（必填）：`create_article` 返回的文章 ID。
- `account_id`（可选）：未指定且用户只有一个公众号时自动使用；**多个公众号时必须指定**，否则失败。
- `theme_id`（可选）：未指定时用公众号绑定的默认样式；账号无默认样式时必须指定。

封面可空：无文章封面时，依次使用公众号默认封面、系统封面。

## 错误场景与恢复

| 场景 | 现象 | 处理 |
|---|---|---|
| 图片超体积（封面 >2MB / 正文图 >1MB） | 建稿失败或服务端异常 | 压缩图片后重新生成 payload 再试，不要原样重发 |
| `title` 超 30 字 / `abstract` 超 100 字 | 建稿被拒 | 截断或改写后重试 |
| 多个公众号未指定 `account_id` | 发布失败 | 先 `list_wechat_accounts`，让用户选一个 |
| `info_id` 不存在 | 发布失败 | 确认 ID 来自本次会话的 `create_article` 返回，不要凭记忆编造 |
| 401 / 授权失效 | 请求被拒 | 引导用户在连接器页重新连接授权 |

## 边界

- 建稿与发布是**两个独立步骤**：`create_article` 只把文章写进言序并返回 `info_id`，`publish_article` 才写入公众号草稿箱。默认先建稿、向用户复述确认后再发布。
- 本连接器只写到**草稿箱**，不做群发；确认群发请在公众号后台手动操作。
- 一次连接只对应一个 MCP Server；账号、主题数据以工具实时返回为准，不要使用历史会话里的旧 ID。
