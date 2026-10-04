# ihr-cli staff entry

## 用途

查询待入职、已入职、已放弃的入职表单列表，或按入职表单 ID 读取详情。只读操作，不发起或修改入职流程。

## `staff entry +search`

```bash
ihr-cli staff entry +search --state pending --keyword "张三" --page 1 --page-size 20
ihr-cli staff entry +search --state joined --department-id 1001,1002
ihr-cli staff entry +search --search-items '[{"searchKey":"expectEntryDate","searchParam":"2026-07-01","fieldType":"GTE"}]'
```

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--state` | string | OPTIONAL | `pending` | `pending/joined/abandoned` | 无 | 选择待入职、已入职或已放弃列表 | 除 `request.tableCode` 映射外，CLI 必带状态条件：`pending` 为 `entryStaffInfo=0 AND entryStatus!=3`，`joined` 为 `entryStaffInfo=1 AND entryStatus!=3`，`abandoned` 为 `entryStatus=3` |
| `--keyword` | string | OPTIONAL | 无 | 姓名模糊匹配 | 无 | 按员工姓名筛选入职表单 | `request.specification.predications[]`：`staffName/CONTAINS` |
| `--mobile` | string | OPTIONAL | 无 | 手机号模糊匹配 | 无 | 按手机号筛选 | `request.specification.predications[]`：`mobile/CONTAINS` |
| `--department-id` | string | OPTIONAL | 无 | 部门 ID，逗号分隔 | 无 | 按一个或多个部门筛选 | `request.specification.predications[]`：`departmentId/IN` |
| `--position-id` | string | OPTIONAL | 无 | 职位 ID，逗号分隔 | 无 | 按一个或多个职位筛选 | `request.specification.predications[]`：`positionId/IN` |
| `--fields` | string | OPTIONAL | `staffName,mobile,departmentId,positionId,expectEntryDate` | 逗号分隔字段 code | 不能为空列表 | 选择列表返回字段 | `request.fieldList[]` |
| `--search-items` | string | OPTIONAL | 无 | JSON 对象数组 | 与 `--json/--stdin` 互斥 | 高级查询 carrier；字段使用 `searchKey/searchParam/fieldType` | 归一为 `request.specification.predications[]` |
| `--sort-field` | string | OPTIONAL | 无 | 可排序字段 code | 与 `--sort-type` 配合 | 指定排序字段 | `request.sort[]` |
| `--sort-type` | string | OPTIONAL | `ASC`（后端转换缺省） | `ASC/DESC` | 仅在提供 `--sort-field` 时有效 | 指定排序方向 | `request.sort[]` 中的方向 |
| `--search-blacklist` | bool | OPTIONAL | 不发送 | boolean | 只有显式传入时发送 | 是否补充黑名单状态 | `query.searchBlacklist` |
| `--sort-mode` | string | OPTIONAL | 不发送 | `ASC/DESC` | 通常在未指定 `--sort-field` 时使用 | 指定后端默认排序方向 | `query.sortMode` |
| `--page` | int | OPTIONAL | `1` | CLI 从 1 开始 | `1-∞` | CLI 用户侧页码 | `request.page=page-1`，后端 0-based |
| `--pageSize` | int | OPTIONAL | `20` | 条/页，范围 `1-100` | 与 `--page-size` 二选一使用 | 每页记录数 | `request.size` |
| `--page-size` | int | OPTIONAL | `20` | `--pageSize` 的 kebab-case alias | 与 `--pageSize` 二选一使用 | 每页记录数 | 同 `--pageSize` |

JSON/stdin 与分项参数互斥，并复用相同的 tableCode、operator、字段列表、分页和隐藏上下文处理：

```bash
ihr-cli staff entry +search --json '{"state":"pending","page":1,"pageSize":20,"searchItems":[{"searchKey":"staffName","searchParam":"张三","fieldType":"LIKE"}]}'
```

`companyId/userId` 由 gateway/session 注入；三种列表状态条件由 CLI 固定追加，并与用户传入的姓名、手机号、部门、职位或高级查询条件按 AND 组合，不能通过 JSON 输入绕过。查询结果仍受当前用户的功能权限和部门数据范围约束。

## `staff entry +get`

```bash
ihr-cli staff entry +get --entry-form-id "entry-form-id"
ihr-cli staff entry +get --json '{"entryFormId":"entry-form-id"}'
```

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--entry-form-id` | string | CONDITIONAL | 无 | 入职表单业务 ID | 分项参数模式必填；JSON 可提供 `entryFormId` | 指定要读取的入职表单 | `path.entryFormId` |

后端按当前登录用户执行员工数据权限校验；不要传 `companyId/userId`。

数据查询、字段元数据和 table component 配置是不同暴露面；需要更多字段时使用 `--fields`，不要要求列表接口附带整包元数据。Agent 不得绕过公开 shortcut 调用 raw HTTP。
