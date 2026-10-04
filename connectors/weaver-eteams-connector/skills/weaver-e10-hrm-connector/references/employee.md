# 员工查询

## 何时使用

按工号/姓名/手机/邮箱查员工、按人员 id 查当前登录人或任意员工的下属、查部门/分部下成员、按 id 列表批量查人员精简详情、按人员 id 取资料名片时使用。全部为只读操作。

## 输入要点

| operation | 必填 | 说明 |
| --- | --- | --- |
| `hrm.employee.query` | 至少一个收敛条件 | 按工号/姓名/手机/邮箱/状态分页查询员工 |
| `hrm.employee.batch` | `ids` | 按人员 id 列表批量查精简详情（每批 ≤100 自动分批，不含部门/岗位/上级名称） |
| `hrm.employee.detail` | `id` | 按人员 id 取资料名片（头像/是否管理员/在线状态，不含姓名/工号/部门/手机） |
| `hrm.subordinate.mine` | `scope`（默认 all） | 查当前登录人的下属（direct/indirect/all），基于当前会话身份 |
| `hrm.subordinate.by-id` | `id`（`scope` 默认 direct） | 按目标人员 id 查直接/间接下属（**无需切换会话**）；所有下属 = direct + indirect 两次并集 |
| `hrm.dept.members` | `dept` | 按部门/分部名或 id 查其下直接成员（组织名需唯一） |

### `hrm.employee.query` 关键字段

| 字段 | 说明 |
| --- | --- |
| `keyword` | 查询关键词，自动推断字段：含 `@`→邮箱；11 位纯数字→手机；纯数字或字母开头含数字→工号；其余→姓名（模糊） |
| `username` | 姓名（模糊匹配） |
| `job_num` | 工号（模糊匹配） |
| `mobile` | 手机号（模糊匹配） |
| `email` | 邮箱（模糊匹配） |
| `status` | `["normal"]` 在职（默认）/ `["6"]` 离职。**不能单独使用**，必须搭配其它条件 |
| `current`/`pageSize` | 分页（pageSize 默认 200） |

`keyword` 与 `username`/`job_num`/`mobile`/`email` 互斥，显式字段优先。

## 命令

按姓名查员工：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.employee.query --input-json '{"keyword":"张三"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"keyword":"张三"}' | weaver-work-cli --profile eteams --json hrm run hrm.employee.query --input -
```

查离职人员（须搭配其它条件）：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.employee.query --input-json '{"keyword":"李四","status":["6"]}'
```

按 id 列表批量查人员：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.employee.batch --input-json '{"ids":["1000000000000000001","1000000000000000002"]}'
```

按 id 取资料名片（头像/管理员/在线）：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.employee.detail --input-json '{"id":"1000000000000000001"}'
```

查当前登录人的所有下属：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.subordinate.mine --input-json '{"scope":"all"}'
```

查某人的直接下属（无需切换会话）：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.subordinate.by-id --input-json '{"id":"1000000000000000001","scope":"direct"}'
```

查部门下成员：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.dept.members --input-json '{"dept":"示例部门"}'
```

## 输出处理

- 查询类返回 `data.rows`（行数组）+ `data.total`（总数）+ `meta`（current/pageSize）；批量/下属返回 `data.rows` + `data.total`。
- 每行含派生字段 `link`（人员卡片链接 `/sp/hrm/profileInfo/{id}`）与 `deptLink`（部门卡片链接），Agent 输出用 `[姓名](link)` 形式呈现；列表行自带 `departmentId`，可同时输出 `[部门名](deptLink)`。
- `employee.detail` 返回 `data`（含 `avatar`/`isAdmin`/`managerType`/`online`）+ `data.link`。这是轻量名片，**不含**姓名/工号/部门/手机。
- `subordinate.by-id` 返回 `data.rows` + `data.total` + `data.page`（hasNext/totalPages）。
- `mobile` 已由 CLI 脱敏（3 位前缀 + `****` + 末 4 位），直接呈现。

## 注意

- **🔴 无条件禁止全量拉取**：`employee.query` 必须带至少一个收敛条件。
- **🔴 `status` 不能单独使用**：必须搭配其它条件，否则 `empty_condition`。
- 在职查询未命中时，CLI 会在 `data.hint` 提示"可能已离职"，Agent 应据此询问用户是否要查离职人员，不要直接答复"查无此人"。
- `employee.batch` 不含部门/岗位/上级**名称**，需要名称时用列表接口或 `employee.detail`（但 detail 也不含这些，需走 `employee.query` 或 `subordinate.by-id`）。
- `subordinate.by-id` 的 `scope` 两值：`direct`（直接）/`indirect`（间接）；"所有下属"需两次调用并集（无 `all` 接口，实测 404）。
- `subordinate.mine` 返回的是**当前登录人**的下属，查"某人的下属"请用 `subordinate.by-id`。
- 人员 id 是长整型，按字符串传递。
- **代理商查询禁用**：`hrm.employee.dls`（`containsDls=true`）仅泛微自用系统支持，未实现，不得编造或绕过。

## 失败处理

- `empty_condition`：空条件拉取被拦截，先询问用户补条件。
- `enum_invalid`：`status`/`scope` 取值非法。
- `dept_not_found`/`dept_ambiguous`：`dept.members` 组织未找到或重名，改用组织 id。
- `permission_denied`（`code=403`）：HRM 读接口开关未开启，提示用户联系管理员开启，不要盲目重试。
- 认证类错误：引导用户断开并重新连接本连接器。
