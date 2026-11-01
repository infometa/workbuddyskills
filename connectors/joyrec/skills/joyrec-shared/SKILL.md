---
name: joyrec-shared
display_name: JOY 录音卡公共约定
display_name_en: JOY Recorder Shared Conventions
description: "Shared auth, error, output and data-model conventions for all JOY Recorder skills. Read this before using joyrec-browse, joyrec-find, joyrec-read, joyrec-digest or joyrec-followup."
description_zh: "所有 JOY 录音卡技能共用的鉴权、错误语义、输出格式与数据模型约定。"
description_en: "Shared auth, error, output and data-model conventions for all JOY Recorder skills."
version: 1.0.0
author: SZITON
---

# joyrec-shared

所有 `joyrec-*` 技能的公共前置。**调用任何录音工具前先读本文件。**

## 工具名匹配规则（必读）

WorkBuddy 会给工具加连接器前缀，形如 `<连接器名>_<工具名>`，前缀由用户填写、**不可预测**。
因此本文件与其它 skill 中的工具名一律写作 `…list_files`、`…get_note`，**按后缀匹配**，
不要硬编码 `joyrec_list_files`。

当前连接器提供 6 个工具：

| 工具 | 作用 | 只读 |
|---|---|---|
| `…get_current_user` | 当前账号信息 | 是 |
| `…list_files` | 录音列表（分页/日期/名称筛选） | 是 |
| `…get_file` | 单条录音详情 + 音频短链 + 转写/纪要清单 | 是 |
| `…get_note` | AI 纪要（markdown） | 是 |
| `…get_transcript` | 带时间戳与说话人的转写（游标分页） | 是 |
| `…whoami` | 自检当前令牌身份与 scope | 是 |

v1 **全部只读**：不要尝试上传、删除、转写、归纳或修改录音。

## 鉴权

- 访问令牌由用户在 JOY App「设置 → MCP 访问」生成，仅保存在连接器配置里。
- **不要要求用户在对话中粘贴令牌**，也不要回显令牌。
- 令牌 scope 决定可用能力：`profile` / `files` / `notes` / `transcripts` / `audio`。
- 缺少 `audio` 时 `get_file` 的 `audio_url` 为空，属于正常情况，不要报错。

## 输出格式约定

- **时长**：`23s` / `5m23s` / `1h05m`（工具返回的是毫秒，必须换算后展示）
- **日期**：`YYYY-MM-DD`
- **转写**：每行 `[MM:SS-MM:SS] 说话人：内容`
- **分页**：展示当前页即可，不要主动拉全量
- **原始毫秒、游标、内部 id**：只用于工具调用，不直接展示给用户（用户问起再给）

## 错误语义

| 情况 | 含义 | 应该怎么做 |
|---|---|---|
| 401 | 令牌无效/过期/已撤销 | 告知用户去 JOY App 重新生成令牌，不要重试 |
| 403 或提示缺少 scope | 令牌权限不足 | 说明需要在生成令牌时勾选对应权限 |
| 404 / 找不到录音 | 记录不存在或不属于当前账号 | 明确告知找不到，**不要重试、不要猜测** |
| 参数错误 | 分页/日期/limit 越界 | 修正参数后重试一次 |
| 网络失败 | 超时/连接失败 | 最多重试一次，仍失败则告知用户 |
| 该录音暂无纪要 | 归纳尚未完成/未生成 | 明确说明状态，可改用转写原文 |

## 数据模型

```text
录音 = { id, name, created_at, start_at, duration(ms), status }
录音详情 = 录音 + { audio_url, audio_url_expires_in, source_list, note_list }
纪要 = [{ data_type, data_title, data_content(markdown), data_content_format }]
转写页 = { record_id, total, limit, returned, has_timestamps, next_cursor, segments[] }
分段 = { start_time(ms), end_time(ms), content, speaker }
```

## 意图路由

| 用户意图 | 使用技能 |
|---|---|
| 看看最近有什么录音 / 翻页 | joyrec-browse |
| 带时间或关键词找某条录音 | joyrec-find |
| 读某条录音的纪要或原文 | joyrec-read |
| 把录音整理成摘要/纪要 | joyrec-digest |
| 提取待办、责任人、跟进事项 | joyrec-followup |

## 通用反模式

- 不要在浏览阶段调用 `get_note` / `get_transcript`（浪费上下文）。
- 不要凭录音名称猜测内容；先定位 id，再读内容。
- 不要把工具返回的 JSON、游标或报错堆栈原样贴给用户。
- 不要虚构录音里没有的信息。
