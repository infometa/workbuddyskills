# lovrabet user-account

按 provider 绑定当前 AccessKey 所属的 Lovrabet 平台用户与外部账号。本期 provider 支持 `dingtalk`，其 `account-id` 是钉钉 userId。该能力只处理显式提供的账号 ID，不打开登录流程，也不自动获取账号 ID。

## 命令

先预览：

```bash
lovrabet user-account bind \
  --provider dingtalk \
  --account-id <id> \
  --dry-run \
  --format compress
```

确认 ID 和当前 AccessKey 身份后正式绑定：

```bash
lovrabet user-account bind \
  --provider dingtalk \
  --account-id <id> \
  --format compress
```

该命令不需要 `appCode`。`--account-id` 是所选 provider 的外部账号 ID，不是 Lovrabet 平台 `userId`；不要传入应用编码。

## 输出确认

重点检查以下字段：

- `data.operation = "bind"`
- `data.selector.provider` 与输入一致
- `data.selector.accountId` 与输入一致
- 正式执行成功时 `data.after.bound = true`
- `data.dryRun` 与本次执行模式一致

`before: null` 表示当前绑定不可查询，不代表旧绑定不存在。只有服务端明确返回成功时，才可将正式绑定视为成功。

## 失败与恢复

- `--provider` 不受支持，或 `--account-id` 缺失、只包含空白字符时，CLI 在发起请求前拒绝执行。
- AccessKey 无效时，先重新执行 `lovrabet auth login`，并使用 `lovrabet auth info` 核对当前身份。
- 网络超时或响应丢失时，结果可能不确定，不得自动重试。
- 人工确认当前 AccessKey 身份和目标账号后，只能使用相同的 provider 和 `--account-id` 显式重试，避免误绑到其他账号。
- 当前命令不提供绑定查询或解绑能力；需要确认既有绑定时，应通过平台现有查询渠道核实。
