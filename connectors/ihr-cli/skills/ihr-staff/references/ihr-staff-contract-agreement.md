# staff 合同与协议列表

合同和协议是两个独立 resource，但共享经过确认的 `page/pageSize/searchFields` 查询协议。两者都只提供列表，不提供详情 `+get`。

## `staff contract +search`

```bash
ihr-cli staff contract +search --keyword "张三" --page 1 --page-size 20
ihr-cli staff contract +search --search-items '[{"fieldName":"departmentId","fieldValue":"1001,1002","fieldType":"IN"}]'
```

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--keyword` | string | OPTIONAL | 无 | 姓名模糊匹配 | 无 | 按员工姓名筛选合同 | `request.searchFields[]`：`staffName/LIKE` |
| `--staff-id` | string | OPTIONAL | 无 | 员工业务 ID | 无 | 按员工 ID 精确筛选 | `request.searchFields[]`：`staffId/EQUAL` |
| `--staff-no` | string | OPTIONAL | 无 | 工号模糊匹配 | 无 | 按员工工号筛选 | `request.searchFields[]`：`staffNo/LIKE` |
| `--department-id` | string | OPTIONAL | 无 | 数字部门 ID，逗号分隔 | 非数字在本地拒绝 | 按一个或多个部门筛选 | `request.searchFields[]`：`departmentId/IN` |
| `--search-items` | string | OPTIONAL | 无 | JSON 对象数组 | 与 `--json/--stdin` 互斥 | 高级 SearchField carrier；接受 `fieldName/fieldValue/fieldType`，兼容 `searchKey/searchParam` 输入名 | `request.searchFields[]` |
| `--page` | int | OPTIONAL | `1` | 从 1 开始 | `1-∞` | 当前页 | `request.page`，后端 1-based |
| `--pageSize` | int | OPTIONAL | `20` | 条/页，范围 `1-100` | 与 `--page-size` 二选一使用 | 每页记录数 | `request.pageSize` |
| `--page-size` | int | OPTIONAL | `20` | `--pageSize` 的 kebab-case alias | 与 `--pageSize` 二选一使用 | 每页记录数 | 同 `--pageSize` |

```bash
ihr-cli staff contract +search --json '{"page":1,"pageSize":20,"searchFields":[{"fieldName":"staffName","fieldValue":"张三","fieldType":"LIKE"}]}'
```

查询结果受合同查看权限和员工数据范围约束；用户显式部门条件仍会与后端数据范围取交集。

合同列表固定追加 `staffStatus IN IN_SERVICE,QUIT`，因此默认、`--search-items`、`--json` 和 `--stdin` 都不会返回 `DELETE` 员工的合同；调用方传入的 `staffStatus` 条件只能进一步收窄该范围。

## `staff agreement +search`

```bash
ihr-cli staff agreement +search --staff-id "staff-id"
ihr-cli staff agreement +search --department-id 1001,1002 --page 1 --page-size 20
```

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--keyword` | string | OPTIONAL | 无 | 姓名模糊匹配 | 无 | 按员工姓名筛选协议 | `request.searchFields[]`：`staffName/LIKE` |
| `--staff-id` | string | OPTIONAL | 无 | 员工业务 ID | 无 | 按员工 ID 精确筛选 | `request.searchFields[]`：`staffId/EQUAL` |
| `--staff-no` | string | OPTIONAL | 无 | 工号模糊匹配 | 无 | 按员工工号筛选 | `request.searchFields[]`：`staffNo/LIKE` |
| `--department-id` | string | OPTIONAL | 无 | 数字部门 ID，逗号分隔 | 非数字在本地拒绝 | 按一个或多个部门筛选 | `request.searchFields[]`：`departmentId/IN` |
| `--search-items` | string | OPTIONAL | 无 | JSON 对象数组 | 与 `--json/--stdin` 互斥 | 高级 SearchField carrier；接受 `fieldName/fieldValue/fieldType`，兼容 `searchKey/searchParam` 输入名 | `request.searchFields[]` |
| `--page` | int | OPTIONAL | `1` | 从 1 开始 | `1-∞` | 当前页 | `request.page`，后端 1-based |
| `--pageSize` | int | OPTIONAL | `20` | 条/页，范围 `1-100` | 与 `--page-size` 二选一使用 | 每页记录数 | `request.pageSize` |
| `--page-size` | int | OPTIONAL | `20` | `--pageSize` 的 kebab-case alias | 与 `--pageSize` 二选一使用 | 每页记录数 | 同 `--pageSize` |

```bash
ihr-cli staff agreement +search --json '{"page":1,"pageSize":20,"searchFields":[{"fieldName":"staffId","fieldValue":"staff-001","fieldType":"EQUAL"}]}'
```

查询结果受协议查看权限和员工数据范围约束；用户显式部门条件仍会与后端数据范围取交集。

协议列表固定限制为 `IN_SERVICE,QUIT`。若调用方传入 `staffStatus`，CLI 会先与该公开可见集合取交集，再仅发送一个最终 `staffStatus IN` 条件；因此默认、`--search-items`、`--json` 和 `--stdin` 都不会返回 `DELETE` 员工，且 `IN_SERVICE` 不会扩大为包含 `QUIT`。

## 共同约束

1. `--search-items` item 使用后端真实 `SearchField` 协议；CLI 会把 `searchKey/searchParam` 输入别名转换回 `fieldName/fieldValue`。
2. `departmentId` 无论通过 flag、`--search-items` 或 JSON 传入，都必须是数字 ID；多个 ID 使用逗号分隔。
3. 当前列表执行链只消费 `page/pageSize/searchFields`。请求 VO 中未生效的 `sortField/sortType/isResultPage` 不属于公开契约。
4. `--json/--stdin` 与分项 flags 互斥，并进入相同的 SearchField/operator/部门 ID 校验。
5. 合同和协议详情尚未完成同等级员工数据权限复核，当前不提供 `+get`。

Agent 不得绕过公开 shortcut 直接调用 raw HTTP。
