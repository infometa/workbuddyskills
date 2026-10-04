# 岗位查询

## 何时使用

按名称/编号查岗位、按岗位 id 取详情（含职务/职级）、按组织/名称/编号批量查岗位时使用。全部为只读操作。

## 输入要点

| operation | 必填 | 说明 |
| --- | --- | --- |
| `hrm.position.query` | 至少一个收敛条件 | 按名称/编号查岗位（快捷搜索名称编号合一；显式 name/code 走高级条件） |
| `hrm.position.detail` | `id` | 按岗位 id 取详情表单（只读，含职务/职级） |
| `hrm.position.list` | 至少一个过滤或 `all=true` | 按组织/名称/编号批量查岗位（岗位地址簿，一次性 + 自动翻页） |

### `hrm.position.query` 关键字段

| 字段 | 说明 |
| --- | --- |
| `keyword` | 快捷搜索关键词，名称与编号合一匹配 |
| `name` | 岗位名称（包含匹配） |
| `code` | 岗位编号（精确匹配） |

`keyword` 与 `name`/`code` 互斥：传 `name`/`code` 时走高级条件，否则走快捷搜索。

### `hrm.position.list` 关键字段

| 字段 | 说明 |
| --- | --- |
| `org` | 组织 id（限定该组织下岗位） |
| `name` | 岗位名称过滤（与 `code` 二选一） |
| `code` | 岗位编号过滤（与 `name` 二选一） |
| `all` | 显式确认全量拉取（无 `org`/`name`/`code` 过滤时必填 `true`） |
| `pageSize` | 分页大小（默认 100，自动翻页到 total） |

## 命令

按名称查岗位：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.position.query --input-json '{"name":"示例岗位"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"name":"示例岗位"}' | weaver-work-cli --profile eteams --json hrm run hrm.position.query --input -
```

按编号查岗位：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.position.query --input-json '{"code":"POS001"}'
```

按 id 取岗位详情（含职务/职级）：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.position.detail --input-json '{"id":"1000000000000000201"}'
```

批量查某组织下岗位：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.position.list --input-json '{"org":"1000000000000000101"}'
```

按名称批量查岗位：

```powershell
weaver-work-cli --profile eteams --json hrm run hrm.position.list --input-json '{"name":"行政"}'
```

## 输出处理

- `position.query` 返回 `data.rows`（轻量行：`id`/`name`/`code`/`title`/`leaf`）+ `data.total`；每行含派生字段 `link`（岗位卡片链接 `/sp/hrm/positionCard/{id}`），Agent 输出用 `[岗位名](link)` 呈现。
- `position.list` 返回 `data.rows`（结构化行：`id`/`name`/`fullName`/`code`/`parent`/`department`/`userCount`/`partTimeCount`/`cancelStatus`/`jobsetid`）+ `data.total`；每行含 `link`。
- `position.detail` 返回 `data`（含岗位名称/全称/编号/上级岗位/所属部门/职务/职级）+ `data.link`。
- 岗位名/全称/职务/职级名已转多语言，直接呈现。

## 注意

- **🔴 无条件禁止全量拉取**：`position.query` 必须带至少一个收敛条件；`position.list` 无 `org`/`name`/`code` 过滤时必须显式 `all=true`，否则 `full_pull_blocked`。
- **批量禁止循环单查**：批量一律走 `position.list` 一次性返回，禁止按 id 逐个调 `position.detail`。
- 两个列表接口返回字段不同：`position.query`（浏览按钮）返回轻量行，`position.list`（岗位地址簿）返回结构化行（含全名/上级/人员数）。
- 岗位 id 是长整型，按字符串传递。
- `cancelStatus`：1=封存 / 0=未封存。

## 失败处理

- `empty_condition`：空条件拉取被拦截，先询问用户补条件。
- `full_pull_blocked`：`position.list` 无过滤，补 `org`/`name`/`code` 或显式 `all=true`。
- `permission_denied`（`code=403`）：HRM 读接口开关未开启，提示用户联系管理员开启。
- 认证类错误：引导用户断开并重新连接本连接器。
