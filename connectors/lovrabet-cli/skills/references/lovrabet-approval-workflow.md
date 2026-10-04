# 审批流运行态办理

Runtime CLI 只负责当前 AccessKey 用户的运行态任务查询和办理，不管理流程定义。当前用户由 `X-User-AK` 对应的服务端认证上下文确定，命令不接受 `--user-id`。

## 查询待办

```bash
lovrabet approval todo --app-code <APP_CODE>
lovrabet approval todo --app-code <APP_CODE> --page 2 --page-size 20 --format compress
```

未传 `--app-code` 时，命令使用当前工作区解析出的应用；服务端请求参数是 `appCode`、`currentPage` 和 `pageSize`。

## 查看任务

```bash
lovrabet approval task-detail --task-id <TASK_ID> --format json
```

详情中的 `canHandle`、`canCancel`、`transferCandidates`、`formData` 和流程上下文以 Runtime 返回为准。输出会遮罩敏感键；如响应包含 `variables`，其中的值只显示脱敏占位符。

## 审批和拒绝

先预览请求：

```bash
lovrabet approval approve --task-id <TASK_ID> --comment '同意' --dry-run
lovrabet approval reject --task-id <TASK_ID> --comment '需要补充材料' --dry-run
```

确认后执行：

```bash
lovrabet approval approve --task-id <TASK_ID> --comment '同意' --yes
lovrabet approval reject --task-id <TASK_ID> --comment '需要补充材料' --yes
```

`approve` 和 `reject` 都调用 Runtime 的 `/api/flow/approve`，区别只在请求体的 `approved` 值。流程后续路径由已发布流程定义决定，CLI 不自行解释。

## 转交

目标用户应来自任务详情的 `transferCandidates` 或其他已确认的 Runtime 资源：

```bash
lovrabet approval transfer \
  --task-id <TASK_ID> \
  --target-user-id <USER_ID> \
  --comment '请协助处理' \
  --dry-run

lovrabet approval transfer \
  --task-id <TASK_ID> \
  --target-user-id <USER_ID> \
  --comment '请协助处理' \
  --yes
```

最终授权和候选人合法性由 Runtime 校验。

## Variables 与安全

审批变量支持内联 JSON 或文件：

```bash
lovrabet approval approve --task-id <TASK_ID> \
  --variables '{"amount":100}' --yes
lovrabet approval approve --task-id <TASK_ID> \
  --variables @variables.json --yes
```

变量解析失败时不会发送请求。dry-run、错误重试命令和本地命令日志不会回显变量值、AccessKey、token 或 secret。

高风险命令在非交互模式必须传 `--yes`；`--dry-run` 只生成脱敏预览，不执行写请求。
