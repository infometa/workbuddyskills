---
name: weaver-e10-calendar-connector
display_name: 泛微E10日程管理
display_name_en: Weaver E10 Calendar
description: 泛微E10日程管理的查询与写操作能力，支持创建、查询列表、查询详情、查询总数、更新、删除日程，查询日程类型与紧急程度，以及应用版本检测，通过 weaver-work-cli calendar 命令执行。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_zh: 泛微E10日程管理的查询与写操作能力，支持创建、查询列表、查询详情、查询总数、更新、删除日程，查询日程类型与紧急程度，以及应用版本检测，通过 weaver-work-cli calendar 命令执行。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_en: Weaver E10 calendar capabilities, including create, list, get, count, update and delete schedules, query schedule type and priority dictionaries, and check app version, delivered through the weaver-work-cli calendar command. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint.
version: 1.1.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
cliHelp: "weaver-work-cli calendar --help"
---

# 泛微E10日程管理

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**


本技能覆盖日程管理业务域：**创建日程**、**查询列表**、**查询详情**、**查询总数**、**更新日程**、**删除日程**、**查询类型/紧急程度字典**、**应用版本检测**。写操作（创建/更新/删除）全部走 prepare→apply 确认协议。

## 命令入口

```text
weaver-work-cli calendar --help
weaver-work-cli --profile eteams calendar schema
weaver-work-cli --profile eteams --json calendar run <operation> --input-json '{"key":"value"}'
```

`schema` 是可用能力的唯一事实来源。禁止把本技能或源文档里的接口路径当成可直接调用的地址，也禁止把未出现在 `schema` 中的能力当作可用 operation。

## 认证

所有请求复用 `weaver-work-cli` 托管的 E10 会话，业务输入只描述业务对象和意图。所有 `datajson` 结构接口的 `header.operator` 由 CLI 自动填充为当前登录用户，无需在输入中提供。

凭证必须由 E10 命名凭据插件提供，由 `weaver-work-cli auth` 托管获取。禁止硬编码地址、账号、口令、Cookie、ETEAMSID 或其它会话凭据，禁止用浏览器自动化绕过登录流程，禁止读取、列出、打印或解析认证目录与文件。认证诊断只能通过 `weaver-work-cli auth` 系列命令、`weaver-work-cli doctor --e10` 和业务命令返回的 JSON 错误完成。

## Reference 路由表

命中任一条件时，执行下一步前读取对应 reference。

| 触发条件 | Reference |
| --- | --- |
| 查看日程列表、按关键字/时间范围找日程、为更新/删除取日程 ID | [`references/calendar-query.md`](references/calendar-query.md) |
| 查询日程详情、查询日程总数 | [`references/calendar-query.md`](references/calendar-query.md) |
| 查询日程类型、查询紧急程度（创建/更新前取选项 ID） | [`references/calendar-dict.md`](references/calendar-dict.md) |
| 创建日程、修改日程、删除日程（写，prepare→apply） | [`references/calendar-write.md`](references/calendar-write.md) |
| 判断日程应用是否安装、版本检测、详情卡片页链接 | [`references/calendar-app-check.md`](references/calendar-app-check.md) |

## 高优先级语义

- **日程**：calendar / agenda，用户常说「日程」「安排」「提醒」「日程列表」「这周有什么安排」。
- **关键字段**：`agn_name`（名称）、`start_time`/`end_time`（起止，`yyyy-MM-dd HH:mm`）、`participants`（参与人人员 ID）、`agn_type`（类型选项 ID）、`priority`（紧急程度选项 ID）。
- **ID 语义**：`agn_type` 与 `priority` 必须传**选项 ID**（先通过 `calendar.type.list` / `calendar.priority.list` 获取），不是 `meeting`/`high` 之类语义字符串。`participants` 必须传**人员 ID**（通过 weaver-e10-hrm-connector 解析姓名），不是姓名。
- **Switch 字段**：`all_day`、`remind`、`part_receipt` 必须传数字 `0`/`1`，禁止布尔值。
- **时间格式**：`start_time`/`end_time` 为 `yyyy-MM-dd HH:mm`（不含秒）；`next_start_remind`/`next_end_remind` 为 `yyyy-MM-dd HH:mm:ss`（含秒）。

## 关键业务规则（CLI 已内置）

- **参与人默认带当前人**：未传 `participants` 时，CLI 自动用当前登录用户；额外指定他人时当前人仍默认包含，除非用户明确表示自己不参与。
- **时长默认 1 小时**：只传 `start_time` 未传 `end_time` 时，CLI 自动补 `end_time = start_time + 1 小时`。
- **更新为全量覆盖**：`calendar.update.prepare` 会先查询当前日程详情并合并用户修改，避免遗漏字段。
- **列表默认一页**：`page_no`/`page_size` 默认 1/10，不自动翻页。

## 已知回显瑕疵（忽略，不当作 bug）

`calendar.list` 响应回显的 `pageNo`/`pageSize` 可能与实际入参不符（如入参 `page_size=20` 却回显成 `pageNo:20 / pageSize:1`）。这是 ESB 响应回显层的**展示瑕疵**，仅影响这两个回显字段的显示值，**不影响实际分页与返回的 `count`/`agenda` 数据**。接口本身正常：调用方以实际入参 `page_no`/`page_size` 为准，**忽略回显值，不登记为缺陷、不要求后端修复、不在 CLI 层规避**。详见 [`references/calendar-query.md`](references/calendar-query.md) 的「已知回显瑕疵」小节。

## 处理链（写操作）

创建、更新、删除日程必须走 prepare→apply：

1. `prepare` 只归一化输入、查当前数据（更新/删除时）、生成预览和 continuation，**不写入**。
2. 向用户摘要目标、差异、风险。
3. 用户明确确认后调用 `apply`，必须带 `confirm=true` 和 prepare 返回的 continuation。
4. `apply` 遇到网络中断/不确定结果时返回 `partial/write_uncertain`，**禁止自动重试**，先做只读回查。

## 失败处理

- 遇到 `partial`、`write_uncertain`、登录失效、回查失败或网络中断，立即停止当前写流程，不自动重试写入。
- 认证类错误（`authentication`/`session_expired`）：引导用户断开并重新连接本连接器，不要用其他方式排查。
- 接口返回 404 或提示「找不到动作流」：日程应用可能未安装，先运行 `calendar.app.check` 检测，再决定是否停止。
- 业务失败看 stderr JSON 的 `error.type` / `error.subtype` / `error.message`。

## 不在范围

- 参与人「姓名 → 人员 ID」解析不在此技能内，交给 weaver-e10-hrm-connector skill。
- 禁止绕过 CLI 直接 curl/fetch 访问 E10 接口。
- 禁止把未出现在 `calendar schema` 中的能力当作可用 operation。

## 平台兼容

命令示例同时兼容 Windows 与 macOS/Linux。简单 JSON 用 `--input-json`，复杂 JSON 存 UTF-8 文件后用 `--input <path>`。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.list --input-json '{"page_no":1,"page_size":10}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"page_no":1,"page_size":10}' | weaver-work-cli --profile eteams --json calendar run calendar.list --input -
```
