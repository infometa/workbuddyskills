# 组织查询（分部 / 部门）

## 何时使用

按名称/编号/上级组织查分部（subcompany）与部门（department）、按组织节点 id 取详情、按多级路径逐级收敛查询时使用。全部为只读操作。

## 输入要点

| operation | 必填 | 说明 |
| --- | --- | --- |
| `hrm.org.query` | 至少一个收敛条件 | 按名称/编号/上级组织查询组织（`type` 区分分部/部门） |
| `hrm.org.detail` | `id` | 按组织节点 id 取详情表单（类型由服务端自动判断，含全路径与人员统计） |

### `hrm.org.query` 关键字段

| 字段 | 说明 |
| --- | --- |
| `type` | `subcompany` 分部 / `department` 部门；不传默认 `department` |
| `name` | 组织名称（模糊包含匹配） |
| `code` | 组织编号（模糊包含匹配） |
| `parent` | 上级**部门** id 数组（查挂在某部门下的子部门，`department`） |
| `subcompany` | 上级**分部** id 数组（查挂在某分部下的组织，`department`） |
| `supSubDepartment` | 上级**分部** id 数组（查挂在某分部下的分部，`subcompany`） |
| `current`/`pageSize` | 分页（pageSize 默认 200） |

> **parent vs subcompany vs supSubDepartment**：`parent` 限定上级部门、`subcompany` 限定上级分部（部门挂在分部下）、`supSubDepartment` 限定上级分部（分部挂在分部下）。三者键名不同，按 `type` 选用，不要混用。

## 命令

按名称查部门：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.org.query --input-json '{"name":"示例部门","type":"department"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"name":"示例部门","type":"department"}' | weaver-work-cli --profile eteams --json hrm run hrm.org.query --input -
```

按名称查分部：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.org.query --input-json '{"name":"示例分部","type":"subcompany"}'
```

查某部门下的子部门（drill-down）：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.org.query --input-json '{"parent":["1000000000000000101"],"type":"department"}'
```

查某分部下的组织：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.org.query --input-json '{"subcompany":["1000000000000000102"],"type":"department"}'
```

按 id 取组织详情（含全路径与人员统计）：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.org.detail --input-json '{"id":"1000000000000000101"}'
```

## 多级路径查询（drill-down 编排）

路径形如 `总部/研发部/产品组`，逐级用「父节点 id 作为上级条件 + 下一段名称」调用 `org.query`：

1. 首段名称查 `org.query`（`name`），得到根节点（看返回 `type` 判断是分部还是部门）。
2. 父为**部门** → `parent=[父部门id]` + 下一段 `name`；父为**分部** → `subcompany=[父分部id]`（查部门）或 `supSubDepartment=[父分部id]`（查分部）+ 下一段 `name`。
3. 逐级收敛至末段；先根→叶，空则叶→根（两者等价）。

## 输出处理

- `org.query` 返回 `data.rows`（组织数组）+ `data.total` + `meta`（current/pageSize）；每行含派生字段 `link`（组织卡片链接 `/sp/hrm/orgCard/{id}`），Agent 输出用 `[组织名](link)` 呈现。
- `org.detail` 返回 `data`（含 `name`/`code`/`type`/`fullPath`/`employee_count`/`parent`/`subcompany` 等）+ `data.link`。`employee_count` 格式为 `"直接人数/总人数"`（`includeSub=true` 时总数含下级）。
- 名称/全称已转多语言，直接呈现。

## 注意

- **🔴 无条件禁止全量拉取**：`org.query` 必须带至少一个收敛条件。
- 分部与部门是两个不同接口（`browser/data/subcompany` 与 `browser/data/department`），CLI 用 `type` 区分；不传 `type` 默认查部门。
- `org.detail` 详情查询**只需传 `id`**，服务端按记录自动判断分部/部门，无需传 `type`。
- 组织节点 id 是长整型，按字符串传递。
- 浏览按钮行含 `title`（`名称|全路径`），可直接用于路径确认/重建。

## 失败处理

- `empty_condition`：空条件拉取被拦截，先询问用户补条件。
- `enum_invalid`：`type` 取值非法（仅 `subcompany`/`department`）。
- `permission_denied`（`code=403`）：HRM 读接口开关未开启，提示用户联系管理员开启。
- 认证类错误：引导用户断开并重新连接本连接器。
