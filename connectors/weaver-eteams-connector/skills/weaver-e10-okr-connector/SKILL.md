---
name: weaver-e10-okr-connector
display_name: 泛微E10 OKR 目标管理
display_name_en: Weaver E10 OKR
description: "泛微E10 OKR 目标管理能力，覆盖目标分页查询、目标详情、关键成果查询与保存、目标对齐、目标评论、目标详情页链接，以及标准版与 ebuilder 双链路判定，通过 weaver-work-cli okr 命令执行。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "泛微E10 OKR 目标管理能力，覆盖目标分页查询、目标详情、关键成果查询与保存、目标对齐、目标评论、目标详情页链接，以及标准版与 ebuilder 双链路判定，通过 weaver-work-cli okr 命令执行。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "Weaver E10 OKR capabilities, including goal list and detail queries, key results, goal alignment, goal comments, goal detail links, and standard/ebuilder link detection, delivered through the weaver-work-cli okr command. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
dependencies:
  - weaver-e10-login
cliHelp: "weaver-work-cli okr --help"
---

# 泛微E10 OKR 目标管理

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**

本技能覆盖 OKR 目标管理业务域：**目标分页查询**、**目标详情**、**关键成果查询与保存**、**目标对齐**、**目标评论**、**目标详情页链接**、**链路判定**。所有写操作（新建/编辑目标、保存关键成果、添加目标对齐）全部走 `prepare -> apply` 确认协议。

## 认证与请求头契约

登录与会话由 E10 登录能力统一提供：文档型约定为 `weaver-e10-login` 技能；连接器场景下由连接器完成授权（`weaver-work-cli auth login`），业务命令统一通过 `--profile eteams` 读取该登录态。业务 Skill 不自建登录流程，不索取、打印或转存任何凭证。

CLI 发往 E10 的每个请求都自动携带以下三项用户信息参数，**缺一不可**（业务入参里不要传这些字段，也不要手工拼装请求头）：

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## 命令入口

```text
weaver-work-cli okr --help
weaver-work-cli --profile eteams okr schema
weaver-work-cli --profile eteams --json okr run <operation> --input-json '{"key":"value"}'
```

`schema` 是可用能力的唯一事实来源。禁止把本技能或源文档里的接口路径当成可直接调用的地址，也禁止把未出现在 `schema` 中的能力当作可用 operation。

高频便捷命令（等价于对应 operation 的薄包装）：

```text
weaver-work-cli --profile eteams okr route
weaver-work-cli --profile eteams okr list --period-type 3 --period-range 2026-09
weaver-work-cli --profile eteams okr get --id <目标ID>
weaver-work-cli --profile eteams okr viewlink --ids <目标ID1>,<目标ID2>
```

## 认证

所有请求复用 `weaver-work-cli` 托管的 E10 会话，业务输入只描述业务对象和意图。所有 `datajson` 结构接口的 `header.operator` 由 CLI 自动填充为当前登录用户，无需在输入中提供。

凭证必须由 E10 命名凭据插件提供，由 `weaver-work-cli auth` 托管获取。禁止硬编码地址、账号、口令、Cookie、ETEAMSID 或其它会话凭据，禁止用浏览器自动化绕过登录流程，禁止读取、列出、打印或解析认证目录与文件。认证诊断只能通过 `weaver-work-cli auth` 系列命令、`weaver-work-cli doctor --e10` 和业务命令返回的 JSON 错误完成。

## 链路判定（先做，再做业务）

OKR 目标在不同租户走**两套互不兼容的接口链路**，由 `okr.version.check` 读取 `ver_name` 判定：

- `ver_name >= V2` → **e10-ebuilder 链路**（`/api/ebuilder/form/formdata/v2/...`）。
- 其它 / 版本接口不可用 → **e10 标准版链路**（`/api/workrelate/goal/...`、`/api/goal/common/comment/...`）。

判定结果按租户缓存 1 天，命中缓存时不会重复请求版本接口。判定后严禁跨链路混用接口。细节见 [`references/okr-link-routing.md`](references/okr-link-routing.md)。

## Reference 路由表

命中任一条件时，执行下一步前读取对应 reference。

| 触发条件 | Reference |
| --- | --- |
| 判断当前租户走标准版还是 ebuilder、链路判定结果异常、目标详情页链接打不开、需要 eb 表单 id | [`references/okr-link-routing.md`](references/okr-link-routing.md) |
| 查目标列表、按周期/责任人/名称找目标、查目标详情、查关键成果列表、查目标评论、取详情页链接 | [`references/okr-query.md`](references/okr-query.md) |
| 新建目标、修改目标（写，prepare→apply） | [`references/okr-write.md`](references/okr-write.md) |
| 新建或修改关键成果（写，prepare→apply） | [`references/okr-keyresult.md`](references/okr-keyresult.md) |
| 添加目标对齐（写，prepare→apply，仅 ebuilder 链路） | [`references/okr-align.md`](references/okr-align.md) |

## 高优先级语义

- **目标**：goal / OKR objective，用户常说「目标」「OKR」「年度目标」「月度目标」「部门目标」。
- **关键成果**：key result / KR，是目标的子项，ebuilder 链路有独立接口，标准版链路随目标返回。
- **目标对齐**：把当前目标挂到另一个目标之下，**仅 ebuilder 链路可用**。
- **目标周期**：`period_type` 取 1-年度 / 2-季度 / 3-月度 / 4-自定义；`period_range` 格式随类型变化（年度/季度为 `yyyy`，月度为 `yyyy-MM`，自定义为 `开始日期,结束日期`）；季度还需 `period_quarter` 取 1-4。
- **人员 ID**：`principalid`（责任人）、`partners`（参与人）必须传**人员 ID**（先通过 weaver-e10-hrm-connector 解析姓名），不是姓名，禁止取 `userId` 字段。
- **目标状态**：标准版 `status` 为 0-草稿 / 1-正式；ebuilder 用 `m_status`（1-进行中 2-已完成 3-已撤销 4-审批中 5-未开始）。

## 关键业务规则（CLI 已内置）

- **目标列表固定四列**：「目标名称、目标责任人名称、目标周期类型、目标周期范围」，且目标名称为可点击的详情页链接（绝对地址）。
- **新建目标默认草稿**：标准版链路新建默认 `status=0`（保存草稿），不直接提交。
- **编辑目标为全量合并**：`update.prepare` 先查询当前详情再合并用户修改；标准版链路必须显式传 `status`，避免把正式目标静默回退为草稿。
- **ebuilder 新建默认值**：`m_status=1`（进行中）、`progress=0`。
- **详情不直出评论正文**：`okr.get` 在标准版链路只返回评论总条数与「是否需要查看评论内容」的提示，正文必须由用户确认后再调 `okr.comment.list` 获取。
- **链路专属能力明确报错**：eb 链路不支持按名称/状态筛选目标，标准版链路没有 `okr.kr.list`/`okr.align.create`，ebuilder 链路没有 `okr.comment.list`；CLI 会返回 `policy/link_unsupported` 或 `link_filter_unsupported`，不会静默忽略。

## 处理链（写操作）

新建/编辑目标、保存关键成果、添加目标对齐必须走 `prepare -> apply`：

1. `prepare` 只归一化输入、按需查询当前数据（编辑时）、生成预览和 continuation，**不写入**。
2. 向用户摘要目标、差异、风险。
3. 用户明确确认后调用 `apply`，必须带 `confirm=true` 和 prepare 返回的 continuation。
4. `apply` 遇到网络中断/不确定结果时返回 `partial/write_uncertain`，**禁止自动重试**，先做只读回查。

## 失败处理

- 遇到 `partial`、`write_uncertain`、登录失效、回查失败或网络中断，立即停止当前写流程，不自动重试写入。
- 认证类错误（`authentication`/`session_expired`）：引导用户断开并重新连接本连接器，不要用其他方式排查。
- `policy/link_unsupported`：当前链路没有该能力，不要换接口硬试，按 reference 中的替代路径处理。
- `validation/link_filter_unsupported`：ebuilder 链路列表不支持该筛选条件，改用 `query_scope=self` 或 `principalid` + 周期条件。
- `validation/period_quarter_invalid`、`validation/scope_data_id_required`、`validation/principal_dept_required`：补齐周期/部门参数后重试 prepare。
- 业务失败看 stderr JSON 的 `error.type` / `error.subtype` / `error.message`。

## 不在范围

- 人员「姓名 → 人员 ID」解析不在此技能内，交给 weaver-e10-hrm-connector skill。
- 目标分类、部门、岗位等组织字典查询不在此技能内，按需走对应业务 Skill。
- 禁止绕过 CLI 直接 curl/fetch 访问 E10 接口。
- 禁止把未出现在 `okr schema` 中的能力当作可用 operation。

## 平台兼容

命令示例同时兼容 Windows 与 macOS/Linux。简单 JSON 用 `--input-json`，复杂 JSON 存 UTF-8 文件后用 `--input <path>`。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json okr run okr.list --input-json '{"period_type":"3","period_range":"2026-09","page_size":10}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"period_type":"3","period_range":"2026-09","page_size":10}' | weaver-work-cli --profile eteams --json okr run okr.list --input -
```
