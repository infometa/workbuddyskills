# AI-HIVE 错误代码字典（references/error-catalog.md）

适用版本：AI-HIVE Connector 1.0.0 / `@infimind-next/ai-hive-mcp@0.2.1`
更新日期：2026-07-31

## 错误响应通用结构

服务端工具失败时，会返回安全展示的 `errorCode` 与 `errorCategory`。Skill 不应回显原始堆栈、上游响应或内部凭证。

```json
{
  "errorCode": "INSUFFICIENT_BALANCE",
  "errorCategory": "billing",
  "retryable": false,
  "message": "账户余额不足，请充值后重试"
}
```

## 错误类别

| Category | 含义 | 是否 retry |
|---|---|---|
| `billing` | 余额不足、额度耗尽 | ❌（等待用户充值后由用户重试）|
| `auth` | 凭证失效/撤销/过期 | ❌（需用户重新连接 Connector） |
| `model` | 模型不存在或暂时下线 | ❌（建议用户切换模型） |
| `validation` | 参数缺失/格式错误 | ❌（需向用户询问补齐） |
| `upstream` | 上游模型/媒体服务商失败 | 部分 ✅（仅当 `retryable: true`） |
| `timeout` | 请求超时或网络不明 | ✅（建议用户稍后重试） |
| `internal` | 服务端内部异常 | ❌（建议用户重试或换时间） |

## 常见错误码

| `errorCode` | Category | 含义 | 推荐下一步 |
|---|---|---|---|
| `INSUFFICIENT_BALANCE` | billing | 余额不足或额度耗尽 | 提示用户在 AI-HIVE 完成充值后再试 |
| `MODEL_UNAVAILABLE` | model | 模型不存在或暂时下线 | 提示切换到 `list_models` 中其他可用模型 |
| `MODEL_DEPRECATED` | model | 模型已被废弃 | 提示切换到推荐模型替代 |
| `TASK_NOT_FOUND` | validation | `taskId` 不属于当前用户或已被清理 | 重新调用 `generate_*` 拿新 `taskId` |
| `TASK_PENDING` | validation | 任务尚未到达查询节奏 | 继续用同一 `taskId` 查询，避免重复创建 |
| `UNAUTHORIZED` | auth | access token 失效或撤销 | 提示用户重新连接 AI-HIVE Connector |
| `TOKEN_EXPIRED` | auth | access token 过期已自动刷新失败 | 提示用户重新连接 AI-HIVE Connector |
| `UPLOAD_PATH_NOT_ALLOWED` | validation | `upload_media_from_path` 路径不可访问 | 请用户在对话中重新选择文件 |
| `MEDIA_TYPE_MISMATCH` | validation | 上传媒体类型与请求不符 | 请用户提供正确类型的文件 |
| `PROMPT_TOO_LONG` | validation | `prompt` 超过服务端限额 | 请用户拆分或精简提示词 |
| `RATE_LIMITED` | upstream | 触发限流 | 建议稍后重试或降低并发 |
| `UPSTREAM_TIMEOUT` | timeout | 上游响应超时 | 稍后重试；如持续失败建议用户换时间 |
| `UPSTREAM_FAILED` | upstream | 上游模型/媒体异常 | 若 `retryable: true` 可重试，否则建议用户换时间或切换模型 |

## 通用展示建议

- 对用户**只展示** `errorCode`、**通用可读描述**与**明确下一步**。
- 不要展示：内部异常堆栈、远端完整响应、敏感凭证、原始 SQL/查询。
- 鉴权类错误出现时，**优先**引导用户撤销失效 Token 或重建 Connector 连接，而不是反复重试扣费调用。
