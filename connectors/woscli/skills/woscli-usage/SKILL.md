---
name: woscli-usage
description: 微盟 WOS CLI 操作技能 - 通过 woscli 命令行工具发现并执行微盟 WOS 业务能力（订单、商品、客户、营销、数据看板等）
description_en: Weimob WOS CLI usage - discover and execute Weimob WOS business capabilities (orders, goods, customers, marketing, dashboards, etc.) via the woscli command-line tool
version: "1.0.0"
author: "Weimob WOS"
---

# 微盟 WOS CLI (woscli) Skill

本 Skill 提供通过 `woscli` 命令行工具调用微盟 WOS 业务能力的能力。woscli 是一个命令路由器：它把自然语言任务翻译成对应业务 category 下的具体命令，并通过 Gateway 执行。

## 环境前提

- woscli 已由连接器（CLI 连接器）自动安装到用户目录：
  - Unix：`~/.woscli/woscli`
  - Windows：`$env:USERPROFILE\.woscli\woscli.exe`
- 当前会话若刚安装，PATH 可能未生效。验证与调用时**优先使用绝对路径**：
  - Unix：`~/.woscli/woscli ...`
  - Windows：`$env:USERPROFILE\.woscli\woscli.exe ...`
  - 若 `woscli` 已在 PATH 中，可直接使用 `woscli`。

## 登录与鉴权

所有业务命令需要先登录。使用 Bash 工具执行：

```bash
# 登录微盟账号（会打开授权页，按提示完成授权）
woscli login

# 查看授权状态与 access token 到期时间
woscli status

# 退出登录
woscli logout
```

> 登录凭证保存在操作系统密钥存储（Windows 凭据管理器 / macOS Keychain / Linux Secret Service），
> 不可用时回退到 `~/.woscli/token.json`（权限 0600）。无需在命令中显式传 token。
>
> `woscli status` 会显示 `已授权，access token 到期时间：<时间>`；未授权时显示非 `已授权` 字样。
>
> **woscli 无自动刷新机制**：access token 到期后不会静默续期，执行命令会报鉴权错误。此时只需重新执行 `woscli login` 完成授权即可，无需其他刷新流程。

## 发现可用命令（关键）

**先发现，再执行。** 不要凭空猜测命令名与参数。用以下方式探索：

```bash
# 1) 按任务描述搜索相关命令
woscli search "创建商品并上架"
woscli search "查询客户订单" --category order

# 2) 浏览某个业务域下的所有命令
woscli order --help
woscli goods --help

# 3) 查看某条命令的详细参数
woscli order <command> --help
woscli goods <command> --help --output-format json
```

常用业务域（category）包括：`order`(订单与售后)、`goods`(商品管理)、`customer`(客户资料与关系)、`marketing`(营销活动与优惠权益)、`dashboard`(数据看板)、`cdp`(客户数据与行为)、`content`(内容管理)、`merchant`(商户)、`finance`(财务与资金)、`team`(团队与组织)、`image`(图片创建重绘与理解) 等。完整列表运行 `woscli --help`。

## 执行命令

```bash
# 通用格式
woscli <category> <command> [arguments] [--output-format json|table]

# 示例：查询订单列表
woscli order <具体命令> --output-format json
```

- 默认执行结果以 **json** 返回，便于程序化处理；`--output-format table` 更适合人类阅读。
- 所有命令名、参数名统一为 **kebab-case**（短横线命名），例如 `--output-format`、`--meeting-id`。严禁驼峰。

## 使用约定与注意事项

- **先搜索后执行**：遇到不确定的能力，先用 `woscli search` 或 `<category> --help` 确认命令与参数，避免猜测导致报错。
- **参数使用 kebab-case**，与 woscli 规范一致。
- **列表/批量参数**优先用重复 flag（如 `--id a --id b`）；仅在结构复杂且数据量小（< 1KB）时用 JSON 字符串。
- **只读优先**：查询类命令默认安全；写操作（创建/更新/取消/删除）执行前确认影响范围且必须取得用户确认。
- **超时与调试**：HTTP 超时用 `--timeout <秒>`；排错加 `--debug` 查看请求细节。

## 常见错误与处理

- **鉴权错误（401 / 403）**：多为 access token 失效，执行 `woscli login` 重新授权即可。
- **限流（429）**：稍作退避后重试；如频繁触发，降低并发与请求频率。
- **命令未找到 / PATH 未生效**：用绝对路径调用（见「环境前提」），或新开终端使 PATH 生效。
- **参数错误**：先 `woscli <category> --help` 或 `woscli search` 确认命令与参数，勿凭猜测。
- **分页 / 列表翻页**：列表类命令通常支持 `--page <n>` 与 `--page-size <n>`（以 `--help` 输出为准），按需翻页获取全量数据。

## 典型工作流

1. 用户提出业务诉求（如"查一下最近 10 笔订单"）。
2. `woscli search "查询最近订单"` 或 `woscli order --help` 找到正确命令与参数。
3. 必要时 `woscli <category> <command> --help` 确认参数。
4. 用绝对路径执行：`~/.woscli/woscli order <command> --output-format json`。
5. 解析返回的 JSON 数据，整理后回复用户。
