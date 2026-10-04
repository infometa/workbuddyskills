# lovrabet notification config-list

只读查询当前应用的应用级通知渠道配置，主要用于获得已存在通知配置的 `configCode`。

## 命令

```bash
lovrabet notification config-list --format compress
lovrabet notification config-list --type EMAIL --format compress
lovrabet notification config-list --type EMAIL --appcode <appCode> --format json
```

`--type` 默认 `EMAIL`，支持：

- `EMAIL`
- `FEISHU`
- `DINGTALK`
- `WECOM`
- `WEBHOOK`

类型值使用大写。完整参数写法为 `--type EMAIL|FEISHU|DINGTALK|WECOM|WEBHOOK`。

## 安全输出

每个配置项只返回用于识别和选择配置的字段：

- `configCode`
- `configName`
- `channelType`
- `description`

该命令不会输出 `endpointUrl`、`channelConfig`、配置 ID、创建或更新时间、SMTP 用户名或密码、token、secret、连接超时和人员身份审计字段。若任一配置缺少可用的 `configCode`、`configName` 或 `channelType`，命令返回错误，不把残缺记录包装成成功结果。

示例输出：

```json
{
  "ok": true,
  "data": {
    "appCode": "app-xxxxx",
    "channelType": "EMAIL",
    "count": 1,
    "configs": [
      {
        "configCode": "ncc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "configName": "官方邮件",
        "channelType": "EMAIL",
        "description": "业务通知邮件"
      }
    ]
  },
  "message": "Found 1 EMAIL notification config(s)"
}
```

## 选择与消费边界

- `configCode` 是应用级通知渠道配置编码，可供已确认契约的通知型 Backend Function 使用。
- dataset 级通知通道的 `channelCode` 不能替代应用级 `configCode`。
- 没有结果时，不要猜测或从其他应用复制配置编码。
- 多个候选能够根据用户明确给出的配置名称或用途唯一匹配时，使用该项；多个候选仍无法判断时，向用户确认，不要默认取第一条。
- 查询结果不代表已经授权发送通知。发送前仍须确认目标应用、Backend Function 契约、`configCode`、接收对象、消息摘要和真实外发副作用。
- 该命令不会发送通知，也不会创建、更新或删除平台配置。

## 失败处理

- AccessKey 无效或无权访问目标应用时，先用 `lovrabet auth info` 核对当前身份，再确认应用权限。
- 应用不明确时，显式传入 `--app` 或 `--appcode`；不要修改本地配置来抬高权限或切换到未经授权的应用。
- 渠道类型不支持时，使用上面列出的五种大写值之一。
- 查询失败时保持 `configCode` 未知，不继续执行依赖该编码的通知发送。

## 参考

- [Backend Function 工作流](lovrabet-bff-workflow.md)
- [输出格式与 --jq](lovrabet-output-format-jq.md)
