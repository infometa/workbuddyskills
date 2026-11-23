# issue report

将问题描述作为日志提交，供后续排查。使用当前 AK 身份，不要求绑定应用。

## 使用方式

```bash
lovrabet issue report --title "Dataset query failed" --description "Observed error and reproduction steps" --dry-run --format json
lovrabet issue report --title "Dataset query failed" --description-file ./issue.md --format compress
```

- `--title` 必填；`--description` 与 `--description-file` 必须二选一，正文不能为空。
- 文件只作为本地内容来源，不自动上传文件或工作目录；请填写复现步骤、实际结果、期望结果和可用证据。
- 自动附带 CLI 版本、环境、已配置的 AppCode、OS/终端信息；不会自动抓取对话或历史失败日志，必要证据应由调用者明确写入正文。
- 标题、正文与附加上下文会进行敏感信息清洗；正文按 UTF-8 字节限制截断，输出包含清洗与截断统计。
- `--dry-run` 只预览最终业务载荷，不提交日志、不查询用户信息；正式提交使用当前用户信息。
- 先预览并检查正文、凭证脱敏和截断情况；重要证据被截断时，缩短重复内容或提供已有证据链接后再提交。
- `Issue log submitted` 表示问题日志已提交。
- 提交报错时，根据错误提示检查登录状态和网络连接。

## 输出

返回 `traceName`、`spanName`、`logDataKeys` 和 `issue` 摘要；`issue.sanitize` 包含原始字节数、截断状态、正文脱敏数量与类别。
`descriptionFile` 是本地读取路径，仅用于命令输出，不属于上报日志字段。
