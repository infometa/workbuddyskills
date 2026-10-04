---
name: zenava
description: Zenava（CtiCloud/Clink2）命令行连接器。通过 zenava 完成呼叫中心、工单、CRM、在线客服、智能体与知识库操作。凭证由连接配置流程写入 ~/.zenava/profile.json，AI 不应向用户索要 Token/Secret。
version: 0.1.2
author: Tinet
---

# Zenava CLI 使用指引（Skill）

> 本 Skill 配套 `zenava` Connector（方案二 CLI + Skill；市场 source=`zenava`）。
> 所有命令通过 `zenava` 执行；先安装后使用（`cli.json` 的 init：`pip install zenava`）。
> 任意命令完整参数以 `zenava <command> --help` 为准。Python ≥ 3.12。

## 1. 连接与凭证

- 安装后 WorkBuddy 会执行 `auth`：弹出**本地授权页**（127.0.0.1），用户填写 Endpoint / 凭证后，写入 `~/.zenava/profile.json` 的 `workbuddy` profile，并设为 `currentProfile`；**用户无需把凭证粘贴到对话中**。
- **AI 不得要求用户把 Token / AccessKeySecret 粘贴到对话中**。凭证无效时，提示用户在 WorkBuddy「连接设置」更新，或断开后重连。
- 查看配置：`zenava --json profile list`（敏感字段脱敏）；切换：`zenava profile use <name>`；单次指定：`zenava --profile <name> ...`。
- 连接状态由 WorkBuddy 调用连接器 `auth_server.py --status`：本地校验 `currentProfile` 完备性，并尽量用 `zenava callcenter enterprise get` 做轻量探测。

## 2. 全局参数与输出约定

| 全局参数 | 说明 |
|---|---|
| `--json` | JSON 输出（AI 解析优先） |
| `--dry-run` | 写操作本地校验与预览，不发请求、不写配置 |
| `--profile <name>` | 指定 profile（不改写 currentProfile） |
| `--no-redact` | 关闭手机号脱敏（确需明文须用户确认） |
| `--verbose` | 打印 URL / TraceId（不含 token/sign/body） |
| `--version` / `--help` | 版本 / 帮助 |

成功常见形态：`result` 为 `"0"` / `"success"`；失败读 `error.message` / `description`。进程非 0 退出时一并呈现退出码与错误文本。

## 3. 常用命令

### 3.1 Profile 与诊断

```bash
zenava --json profile list
zenava profile use workbuddy
zenava update check
```

### 3.2 外呼任务（callcenter task）

```bash
zenava callcenter task query --type 1 --status 1 --start 0 --limit 10
zenava callcenter task get --task-id 34
zenava callcenter task create ...          # --help 看参数
zenava callcenter task start --task-id 34
zenava callcenter task pause --task-id 34
zenava callcenter task stop --task-id 34   # 写操作，先确认
zenava callcenter task import-tel --task-id 34 --file contacts.csv
zenava callcenter task list-tel --task-id 34 --start 0 --limit 100
zenava callcenter task monitor-tasks --status 1
```

### 3.3 座席 / 话单 / 录音 / 监控

```bash
zenava callcenter agent query --limit 10
zenava callcenter agent get --cno 2001
zenava callcenter agent-status get --cno 2001
zenava --json callcenter cdr ib-query --start-time 1700000000 --end-time 1700086400
zenava --json callcenter record get-url --record-file your-record-file.mp3
zenava --json callcenter monitor agent --limit 10
zenava --json callcenter enterprise get
```

### 3.4 呼叫中心其他能力和其它产品域的能力

```bash
zenava callcenter --help     # 呼叫中心
zenava ticket --help         # 工单
zenava crm --help            # CRM
zenava livechat --help       # 在线客服
zenava agent --help          # 智能体（根级，非 callcenter agent）
zenava aikb --help           # 智能知识库
```

> 完整命令树：`zenava --help`

## 4. 通用约定

| 项 | 约定 |
|---|---|
| 配置路径 | `~/.zenava/profile.json`（`currentProfile` + `profiles`） |
| 时间格式 | task/报表：`"YYYY-MM-DD HH:mm:ss"`；cdr/asr：Unix 秒 |
| 任务状态 | `0` 初始，`1` 运行，`2` 暂停，`3` 结束 |
| 任务类型 | `1` 预测外呼，`2` 自动外呼 |
| 分页 | `start` 从 0，`limit` 最大 100（默认 10） |
| 脱敏 | 默认脱敏；确需明文用户授权后 `--no-redact` |
| 危险操作 | stop / delete 等：二次确认，必要时先 `--dry-run` |
| 串行执行 | 禁止并发跑 CLI；先查后用（task-id、cno 等不得臆造） |
| 禁止透传密钥 | 命令参数中不要带 Token / AccessKeySecret |

## 5. 典型场景

1. **外呼任务**：`callcenter task query` → `task get` → `task monitor-tasks`
2. **座席状态**：`callcenter agent-status get --cno …`
3. **话单试听**：`callcenter cdr ib-query` → 取 `recordFile` → `record get-url`
4. **新建任务**：`task create … --dry-run` → 确认后执行 → `import-tel` → `start`

## 6. 错误处理

| 现象 | 处理 |
|---|---|
| InvalidParameter | 按 message 修正参数 |
| 权限不足 / 4xx | 检查企业编号与 Token/AK 权限 |
| 凭证缺失或无效 | 提示在连接设置更新或断开重连；**不要索要明文密钥** |
| 未设置 currentProfile | `zenava profile use <name>` 或让用户走 WorkBuddy 连接流程 |

