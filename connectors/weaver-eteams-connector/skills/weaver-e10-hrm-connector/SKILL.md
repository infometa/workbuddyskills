---
name: weaver-e10-hrm-connector
display_name: 泛微E10组织管理
display_name_en: Weaver E10 Organization Management
description: 泛微E10组织管理（员工/组织/岗位查询）的 E10 查询能力，通过 weaver-work-cli hrm 命令执行。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_zh: 泛微E10组织管理（员工/组织/岗位查询）的 E10 查询能力，通过 weaver-work-cli hrm 命令执行。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_en: Weaver E10 Organization Management capabilities for E10, covering employee, organization and position queries, delivered through the weaver-work-cli hrm command. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint.
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
cliHelp: "weaver-work-cli hrm --help"
---

# 泛微E10组织管理

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**


本技能覆盖组织管理三大业务域：**员工（employee）**、**组织（org）**、**岗位（position）**，全部为只读查询，无写操作。代理商查询（`containsDls=true`）属于禁用边界，见 [`references/employee.md`](references/employee.md)。

## 命令入口

```text
weaver-work-cli hrm --help
weaver-work-cli --profile eteams hrm schema
weaver-work-cli --profile eteams --json hrm run <operation> --input -
```

`schema` 是可用能力的唯一事实来源。禁止把本技能或源文档里的接口路径当成可直接调用的地址，也禁止把未出现在 `schema` 中的能力当作可用 operation。

## 认证

所有请求复用 `weaver-work-cli` 托管的 E10 会话，业务输入只描述业务对象和意图。会话凭证（Cookie / ETEAMSID / 业务 Token）由 `weaver-work-cli` 认证体系统一托管获取与保存，本技能不自行登录、不保存、不转发任何凭证，禁止硬编码凭证或使用浏览器自动化登录兜底。禁止读取、列出、打印或解析 `.e10-cli` 等认证目录和文件；认证诊断只能通过 `weaver-work-cli auth` 系列命令、`weaver-work-cli doctor --e10` 和业务命令返回的 JSON 错误完成。

## Reference 路由表

命中任一条件时，执行下一步前读取对应 reference。

| 触发条件 | Reference |
| --- | --- |
| 查员工、工号/手机/邮箱、查下属、部门成员、批量人员、人员详情 | [`references/employee.md`](references/employee.md) |
| 查分部、查部门、组织架构、层级路径、组织详情 | [`references/org.md`](references/org.md) |
| 查岗位、岗位详情、批量岗位 | [`references/position.md`](references/position.md) |

## 跨模块约定（必须先知道）

三个业务域统一走 E10 HRM 内部浏览/详情接口，响应统一 `WeaResult` 契约，已在 CLI 内归一化，但语义差异仍会影响结果解读：

- **响应成功判定**：统一 `code=200`（WeaResult）。业务失败码即使 HTTP 200 也会抛 `api/business_error`；`403` 会抛 `api/permission_denied`（提示联系管理员开启接口开关，不盲目重试）。
- **数据行位置**：列表接口行在 `data.data`（浏览按钮 `browser/data/*` 与岗位批量 `queryListByOrgTree`），总数在 `data.total`；员工浏览/下属查询因 `data/resource` 的 `data.count` 恒为 0，CLI 额外请求 `count/resource` 取真实 `data.total`。下属按 id 查询（`myDirectSubordinates`/`myIndirectSubordinates`）的行在 `data.page.result`、总数在 `data.page.totalCount`。
- **详情接口**：员工名片（`profile/get`）、组织详情（`organization/getForm`）、岗位详情（`getEditOrAddPostForm`）返回单对象（`data` 直接承载），CLI 附 `link`。
- **长整型 id 一律按字符串传递**：人员 id、组织节点 id、岗位 id 都是长整型，避免精度丢失。
- **手机号脱敏**：员工/批量/下属列表返回的 `mobile` 已由 CLI 脱敏（3 位前缀 + `****` + 末 4 位），Agent 直接呈现，不做二次处理。

## 安全边界

- **🔴 无条件禁止全量拉取**：`employee.query`/`org.query`/`position.query` 必须携带至少一个收敛条件，无条件时先询问用户，禁止空条件调用。`position.list` 无 `org`/`name`/`code` 过滤时必须显式 `all=true`。
- **🔴 `status` 不能单独使用**：`employee.query` 的 `status`（`["normal"]` 在职 / `["6"]` 离职）必须搭配其它条件（keyword/工号/姓名/手机/邮箱）。
- **批量禁止循环单查**：批量查询一律走 `batch`（每批 ≤100，CLI 自动分批）；岗位批量走 `position.list` 一次性返回，禁止按 id 逐个调详情。
- **姓名/工号/名称模糊匹配**：多人命中时必须列出候选让用户选择，不得自动取第一条；`dept.members` 部门重名时报 `dept_ambiguous`，需改用组织 id。
- **人员 id、组织 id、岗位 id 都是长整型**，一律按字符串传递。
- **代理商查询禁用**：`hrm.employee.dls`（`containsDls=true`）仅泛微自用系统支持，已列为禁用边界，不得编造或绕过。

## 失败处理

- `code=302` 或认证类错误：引导用户断开并重新连接本连接器，不要用其他方式排查。
- 业务失败看 stderr JSON 的 `error.type` / `error.subtype` / `error.message`，不要用退出码 `0` 判断成功。
- 常见业务错误：`empty_condition`（空条件拉取被拦截）、`full_pull_blocked`（岗位全量需 `all=true`）、`dept_not_found`/`dept_ambiguous`（组织未找到或重名，改用 id）、`enum_invalid`（枚举取值非法）、`permission_denied`（接口开关未开启）。

## 平台兼容

命令示例必须同时兼容 Windows 与 macOS/Linux。涉及 JSON stdin 时：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.employee.query --input-json '{"keyword":"张三"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"keyword":"张三"}' | weaver-work-cli --profile eteams --json hrm run hrm.employee.query --input -
```

复杂 JSON 建议保存为 UTF-8 文件后按平台传给 `--input <file>`。
