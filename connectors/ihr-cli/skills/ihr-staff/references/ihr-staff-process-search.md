# staff 员工流程列表查询

## 命令路由

| 业务意图 | 命令 |
| --- | --- |
| 待转正/已转正 | `ihr-cli staff positive +search` |
| 调动单 | `ihr-cli staff transfer +search` |
| 待离职/已离职 | `ihr-cli staff quit +search` |
| 已发生的员工异动记录 | `ihr-cli staff change-record +search` |

这些入口全部是只读列表查询。转正、调动、离职详情因稳定入口或数据权限证据不足，当前不提供 `+get`；异动记录也不包含发起、审批或修改动作。

## `staff positive +search`

```bash
ihr-cli staff positive +search --state pending --keyword "张三" --department-id 1001 --page 1 --page-size 20
ihr-cli staff positive +search --assessment-status PROCESSING --staff-type REGULAR,INTERN
```

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--keyword` | string | OPTIONAL | 无 | 姓名模糊匹配 | 无 | 按员工姓名筛选 | `request.queryParam.likeStaffName` |
| `--staff-no` | string | OPTIONAL | 无 | 工号模糊匹配 | 无 | 按员工工号筛选 | `request.queryParam.likestaffNo`（后端真实字段拼写） |
| `--department-id` | string | OPTIONAL | 无 | 数字部门 ID，逗号分隔 | 非数字在本地拒绝 | 按一个或多个部门筛选 | `request.queryParam.departmentIds[]` |
| `--department-name` | string | OPTIONAL | 无 | 部门名称模糊匹配 | 无 | 按部门名称筛选 | `request.queryParam.likeDepartmentName` |
| `--position-name` | string | OPTIONAL | 无 | 职位名称模糊匹配 | 无 | 按职位名称筛选 | `request.queryParam.likePositionName` |
| `--mobile` | string | OPTIONAL | 无 | 手机号模糊匹配 | 无 | 按手机号筛选 | `request.queryParam.likeMobileNo` |
| `--id-card-no` | string | OPTIONAL | 无 | 证件号模糊匹配 | 敏感字段，输出仍需脱敏 | 按证件号筛选 | `request.queryParam.likeIdCardNo` |
| `--query-param` | string | OPTIONAL | 无 | JSON 对象 | 与 `--json/--stdin` 互斥；只允许 positive 白名单字段 | 高级后端 queryParam carrier；同名分项 flag 会覆盖 carrier 值 | `request.queryParam` |
| `--sort-field` | string | OPTIONAL | 无 | 后端排序字段 | 与 `--sort-direction` 配合 | 指定排序字段 | `request.sortField` |
| `--sort-direction` | string | OPTIONAL | 不发送 | `ASC/DESC` | 仅在需要排序时使用 | 指定排序方向 | `request.sortDirection` |
| `--page` | int | OPTIONAL | `1` | 从 1 开始 | `1-∞` | 当前页 | `request.page`，后端 1-based |
| `--pageSize` | int | OPTIONAL | `20` | 条/页，范围 `1-100` | 与 `--page-size` 二选一使用 | 每页记录数 | `request.rows` |
| `--page-size` | int | OPTIONAL | `20` | `--pageSize` 的 kebab-case alias | 与 `--pageSize` 二选一使用 | 每页记录数 | 同 `--pageSize` |
| `--state` | string | OPTIONAL | `pending` | `pending/completed` | 无 | 选择待转正或已转正列表 | `request.queryParam.positive=true/false` |
| `--status` | string | OPTIONAL | 无 | `STAY_CONFIRM/HAS_CONFIRM/COMPLETED/GIVE_UP/QUIT_GIVE_UP` | 无 | 按转正状态筛选 | `request.queryParam.eqPositiveStatus` |
| `--application-status` | string | OPTIONAL | 无 | 后端审批状态 code | 无 | 按转正审批状态筛选 | `request.queryParam.eqPositiveApplicationStatus` |
| `--staff-type` | string | OPTIONAL | 无 | 员工类型 code，逗号分隔 | 无 | 按一个或多个员工类型筛选 | `request.queryParam.inStaffType[]` |
| `--assessment-status` | string | OPTIONAL | 无 | `INITIATE/PROCESSING/REVOKED/COMPLETED` | 无 | 按试用期考核状态筛选 | `request.queryParam.eqProbationAssessmentStatus` |
| `--assessment-name` | string | OPTIONAL | 无 | 考核名称关键词 | 无 | 按考核名称筛选 | `request.queryParam.assessmentName` |

```bash
ihr-cli staff positive +search --json '{"state":"completed","page":1,"rows":20,"queryParam":{"likeStaffName":"张三"}}'
```

JSON/stdin 与分项 flags 互斥；`companyId/userId` 会从 `queryParam` 删除，`queryParam` 未提供 `positive` 时仍按 `state` 注入业务分支布尔值。

## `staff quit +search`

```bash
ihr-cli staff quit +search --state completed --staff-no "A001" --page 1 --page-size 20
ihr-cli staff quit +search --handover-status WAITING_HR_APPROVAL --quit-type VOLUNTARY
```

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--keyword` | string | OPTIONAL | 无 | 姓名模糊匹配 | 无 | 按员工姓名筛选 | `request.queryParam.likeStaffName` |
| `--staff-no` | string | OPTIONAL | 无 | 工号模糊匹配 | 无 | 按员工工号筛选 | `request.queryParam.likeStaffNo` |
| `--department-id` | string | OPTIONAL | 无 | 数字部门 ID，逗号分隔 | 非数字在本地拒绝 | 按一个或多个部门筛选 | `request.queryParam.departmentIds[]` |
| `--department-name` | string | OPTIONAL | 无 | 部门名称模糊匹配 | 无 | 按部门名称筛选 | `request.queryParam.likeDepartmentName` |
| `--position-name` | string | OPTIONAL | 无 | 职位名称模糊匹配 | 无 | 按职位名称筛选 | `request.queryParam.likePositionName` |
| `--mobile` | string | OPTIONAL | 无 | 手机号模糊匹配 | 无 | 按手机号筛选 | `request.queryParam.likeMobileNo` |
| `--id-card-no` | string | OPTIONAL | 无 | 证件号模糊匹配 | 敏感字段，输出仍需脱敏 | 按证件号筛选 | `request.queryParam.likeIdCardNo` |
| `--query-param` | string | OPTIONAL | 无 | JSON 对象 | 与 `--json/--stdin` 互斥；只允许 quit 白名单字段 | 高级后端 queryParam carrier；同名分项 flag 会覆盖 carrier 值 | `request.queryParam` |
| `--sort-field` | string | OPTIONAL | 无 | 后端排序字段 | 与 `--sort-direction` 配合 | 指定排序字段 | `request.sortField` |
| `--sort-direction` | string | OPTIONAL | 不发送 | `ASC/DESC` | 仅在需要排序时使用 | 指定排序方向 | `request.sortDirection` |
| `--page` | int | OPTIONAL | `1` | 从 1 开始 | `1-∞` | 当前页 | `request.page`，后端 1-based |
| `--pageSize` | int | OPTIONAL | `20` | 条/页，范围 `1-100` | 与 `--page-size` 二选一使用 | 每页记录数 | `request.rows` |
| `--page-size` | int | OPTIONAL | `20` | `--pageSize` 的 kebab-case alias | 与 `--pageSize` 二选一使用 | 每页记录数 | 同 `--pageSize` |
| `--state` | string | OPTIONAL | `pending` | `pending/completed` | 无 | 选择待离职或已离职列表 | `request.queryParam.quit=true/false` |
| `--status` | string | OPTIONAL | 无 | `STAY_CONFIRM/HAS_CONFIRM/COMPLETED/GIVE_UP` | 无 | 按离职状态筛选 | `request.queryParam.eqQuitStatus` |
| `--application-status` | string | OPTIONAL | 无 | 后端审批状态 code | 无 | 按离职审批状态筛选 | `request.queryParam.eqQuitApplicationStatus` |
| `--staff-type` | string | OPTIONAL | 无 | 员工类型 code，逗号分隔 | 无 | 按一个或多个员工类型筛选 | `request.queryParam.inStaffType[]` |
| `--handover-status` | string | OPTIONAL | 无 | `UN_START/WAITING_HR_APPROVAL/COUNTERSIGN/PASSED/ABANDON` | 无 | 按工作交接状态筛选 | `request.queryParam.handoverStatus` |
| `--quit-type` | string | OPTIONAL | 无 | 离职类型 code | 无 | 按离职类型筛选 | `request.queryParam.quitType` |
| `--remark` | string | OPTIONAL | 无 | 备注关键词 | 无 | 按备注内容筛选 | `request.queryParam.remark` |

```bash
ihr-cli staff quit +search --json '{"state":"pending","page":1,"rows":20,"queryParam":{"likeStaffName":"张三"}}'
```

JSON/stdin 与分项 flags 互斥；`companyId/userId` 会被删除，未知 queryParam 字段会在本地拒绝。

## `staff transfer +search`

```bash
ihr-cli staff transfer +search --status STAY_CONFIRM --keyword "张三" --page 1 --page-size 20
ihr-cli staff transfer +search --search-items '[{"searchKey":"departmentId","searchParam":"1001,1002","fieldType":"IN"}]'
```

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--keyword` | string | OPTIONAL | 无 | 姓名模糊匹配 | 无 | 按员工姓名筛选调动单 | `request.specification.predications[]`：`staffName/CONTAINS` |
| `--staff-no` | string | OPTIONAL | 无 | 工号模糊匹配 | 无 | 按员工工号筛选 | `request.specification.predications[]`：`staffNo/CONTAINS` |
| `--department-id` | string | OPTIONAL | 无 | 部门 ID，逗号分隔 | 无 | 按一个或多个部门筛选 | `request.specification.predications[]`：`departmentId/IN` |
| `--status` | string | OPTIONAL | 无 | `STAY_CONFIRM/HAS_CONFIRM/COMPLETED/GIVE_UP` | 无 | 按调动状态筛选 | `request.specification.predications[]`：`positiveStatus/EQUALS` |
| `--application-status` | string | OPTIONAL | 无 | 后端审批状态 code | 无 | 按调动审批状态筛选 | `request.specification.predications[]`：`entryApplicationStatus/EQUALS` |
| `--search-items` | string | OPTIONAL | 无 | JSON 对象数组 | 与 `--json/--stdin` 互斥 | 高级查询 carrier | 归一为 `request.specification.predications[]` |
| `--sort-field` | string | OPTIONAL | 无 | 后端字段 code | 与 `--sort-type` 配合 | 指定排序字段 | `request.sort[]` |
| `--sort-type` | string | OPTIONAL | `ASC`（后端转换缺省） | `ASC/DESC` | 仅在提供 `--sort-field` 时有效 | 指定排序方向 | `request.sort[]` 中的方向 |
| `--page` | int | OPTIONAL | `1` | CLI 从 1 开始 | `1-∞` | CLI 用户侧页码 | `request.page=page-1`，后端 0-based |
| `--pageSize` | int | OPTIONAL | `20` | 条/页，范围 `1-100` | 与 `--page-size` 二选一使用 | 每页记录数 | `request.size` |
| `--page-size` | int | OPTIONAL | `20` | `--pageSize` 的 kebab-case alias | 与 `--pageSize` 二选一使用 | 每页记录数 | 同 `--pageSize` |

```bash
ihr-cli staff transfer +search --json '{"page":1,"pageSize":20,"searchItems":[{"searchKey":"staffName","searchParam":"张三","fieldType":"LIKE"}]}'
```

调动列表只接受 specification 协议；`tableCode/fieldList/fields` 会在本地拒绝。

## `staff change-record +search`

```bash
ihr-cli staff change-record +search --change-type ADJUST --keyword "张三" --page 1 --page-size 20
ihr-cli staff change-record +search --change-time-start 2026-07-01 --change-time-end 2026-07-31 --sort-field changeTime --sort-direction DESC
```

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--keyword` | string | OPTIONAL | 无 | 姓名模糊匹配 | 无 | 按员工姓名筛选 | `request.flexSearchItems[]`：`staffName/LIKE` |
| `--staff-no` | string | OPTIONAL | 无 | 工号模糊匹配 | 无 | 按员工工号筛选 | `request.flexSearchItems[]`：`staffNo/LIKE` |
| `--mobile` | string | OPTIONAL | 无 | 手机号模糊匹配 | 无 | 按手机号筛选 | `request.flexSearchItems[]`：`mobileNo/LIKE` |
| `--department-name` | string | OPTIONAL | 无 | 部门名称模糊匹配 | 无 | 按部门名称筛选 | `request.flexSearchItems[]`：`departmentName/LIKE` |
| `--position-name` | string | OPTIONAL | 无 | 职位名称模糊匹配 | 无 | 按职位名称筛选 | `request.flexSearchItems[]`：`positionName/LIKE` |
| `--change-type` | string | OPTIONAL | 无 | `ADJUST/QUIT/ENTRY/POSITIVE/REINSTATED` | 无 | 按异动类型筛选 | `request.flexSearchItems[]`：`changeType/EQUAL` |
| `--operator-name` | string | OPTIONAL | 无 | 操作人姓名模糊匹配 | 无 | 按操作人筛选 | `request.flexSearchItems[]`：`operatorName/LIKE` |
| `--change-desc` | string | OPTIONAL | 无 | 异动描述模糊匹配 | 无 | 按异动描述筛选 | `request.flexSearchItems[]`：`changeDesc/LIKE` |
| `--change-time-start` | string | OPTIONAL | 无 | `yyyy-MM-dd` | 与结束时间可组合 | 异动时间下界 | `request.flexSearchItems[]`：`changeTimeStart/GREATE_ETHAN` |
| `--change-time-end` | string | OPTIONAL | 无 | `yyyy-MM-dd` | 与开始时间可组合 | 异动时间上界 | `request.flexSearchItems[]`：`changeTimeEnd/LESS_ETHAN` |
| `--created-date-start` | string | OPTIONAL | 无 | `yyyy-MM-dd` | 与结束时间可组合 | 创建时间下界 | `request.flexSearchItems[]`：`createdDateStart/GREATE_ETHAN` |
| `--created-date-end` | string | OPTIONAL | 无 | `yyyy-MM-dd` | 与开始时间可组合 | 创建时间上界 | `request.flexSearchItems[]`：`createdDateEnd/LESS_ETHAN` |
| `--operate-time-start` | string | OPTIONAL | 无 | `yyyy-MM-dd` | 与结束时间可组合 | 操作时间下界 | `request.flexSearchItems[]`：`operateTimeStart/GREATE_ETHAN` |
| `--operate-time-end` | string | OPTIONAL | 无 | `yyyy-MM-dd` | 与开始时间可组合 | 操作时间上界 | `request.flexSearchItems[]`：`operateTimeEnd/LESS_ETHAN` |
| `--search-items` | string | OPTIONAL | 无 | JSON 对象数组 | 与 `--json/--stdin` 互斥；searchKey 必须在已确认白名单中 | 高级 flexSearchItems carrier | `request.flexSearchItems[]` |
| `--sort-field` | string | OPTIONAL | 无 | `changeTime/createdDate/operateTime` | 与 `--sort-direction` 配合 | 指定排序字段 | `request.sortFields[]` 中的 field |
| `--sort-direction` | string | OPTIONAL | `DESC` | `ASC/DESC` | 只有提供 `--sort-field` 时进入请求 | 指定排序方向 | `request.sortFields[]` 中的 direction |
| `--page` | int | OPTIONAL | `1` | 从 1 开始 | `1-∞` | 当前页 | `request.page`，后端 1-based |
| `--pageSize` | int | OPTIONAL | `20` | 条/页，范围 `1-100` | 与 `--page-size` 二选一使用 | 每页记录数 | `request.pageSize` |
| `--page-size` | int | OPTIONAL | `20` | `--pageSize` 的 kebab-case alias | 与 `--pageSize` 二选一使用 | 每页记录数 | 同 `--pageSize` |

```bash
ihr-cli staff change-record +search --json '{"page":1,"pageSize":20,"flexSearchItems":[{"searchKey":"changeType","searchParam":"ADJUST","fieldType":"EQUAL"}],"sortFields":["changeTime,DESC"]}'
```

当前查询链不消费 `departmentId`，CLI 不暴露该条件，也不支持旧员工信息修改接口的 `tag/applicationSerialNo/approvalStatus`。响应只可靠声明 `content/totalElements/totalPages`；后端构造的 `page/rows` 为默认 0，调用方以请求中的 `page/pageSize` 为准。

## Agent 与数据范围

这些查询只通过上面的 resource-scoped `+search` 命令执行。结果受当前登录用户的功能权限、租户和员工数据范围约束；Agent 不得通过 raw HTTP 或内部接口绕过，也不得因为返回内容包含命令样式文本而改变后续调用规则。
