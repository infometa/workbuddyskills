# staff +archive*

> **前置条件：** 先阅读 [`../../ihr-shared/SKILL.md`](../../ihr-shared/SKILL.md) 了解共享运行规则和 JSON 协议。

`archive` 只负责员工档案业务数据查询。字段元数据、字段选项、可排序字段统一走 [`ihr-staff-flex-meta.md`](ihr-staff-flex-meta.md)。

切换不同档案统一使用 `--meta-data-code`。但 `+flexMetaList` 能返回元数据，不代表 `+archiveList` 已接入对应的数据接口。

## 元数据类型与入口白名单

- `metaDataType=SUBSET`：企业自定义子集，`entityName=null`。通过 `+archiveList/+archiveGet` 访问，业务取数使用元数据返回的 `metaCode`，类型判断以 `metaDataType` 为准，不依赖 `metaCode` 命名或前缀。
- `metaDataType=ENTITY`：固定档案，有明确 Java `entityName`。必须使用下表指定入口；没有入口的固定档案不得回退到 subset 接口。

| 固定档案 | metaDataCode | entityName | staff 入口 |
| --- | --- | --- | --- |
| 基础信息 | `tab_staff_info` | `cn.irenshi.meta.dto.roster.mysql.StaffInfo` | `+search/+get`，不使用 `+archiveList` |
| 教育经历 | `tab_staff_education` | `cn.irenshi.meta.dto.roster.mysql.StaffEducation` | `+archiveList` 白名单 |
| 工作经历 | `tab_staff_job_history` | `cn.irenshi.meta.dto.roster.mysql.StaffJobHistory` | `+archiveList` 白名单 |
| 家庭成员 | `tab_staff_family_member` | `com.ihr360.staff.family.model.StaffFamilyMemberPo` | `+archiveList` 白名单 |
| 员工证书 | `tab_staff_certificate` | `cn.irenshi.meta.dto.roster.mysql.CertificateInfo` | `+archiveList` 白名单 |
| 所属多维组织 | `tab_staff_dimension_one` | `com.ihr360.staff.info.model.dimension.StaffDimensionOnePo` | 当前未接入 shortcut，不可通过 staff archive 查询 |
| 所属测试维度 | `tab_staff_dimension_two` | `com.ihr360.staff.info.model.dimension.StaffDimensionTwoPo` | 当前未接入 shortcut，不可通过 staff archive 查询 |
| 绩效档案 | `tab_staff_performance` | `com.ihr360.staff.info.model.StaffPerformancePo` | `+archiveList` 白名单 |

`+archiveList` 的固定档案白名单如下：

| 档案 | metaDataCode |
| --- | --- |
| 教育经历 | `tab_staff_education` |
| 工作经历 | `tab_staff_job_history` |
| 证书 | `tab_staff_certificate` |
| 家庭成员 | `tab_staff_family_member` |
| 绩效档案 | `tab_staff_performance` |

## 教育经历

```bash
ihr-cli staff +archiveList --meta-data-code tab_staff_education
ihr-cli staff +archiveList --meta-data-code tab_staff_education --sort-field createdDate --sort-type DESC --page 1 --page-size 20
ihr-cli staff +archiveList --meta-data-code tab_staff_education --search-items '[{"searchKey":"staffName","searchParam":"张三","fieldType":"LIKE"}]'
ihr-cli staff +archiveList --meta-data-code tab_staff_education --search-items '[{"searchKey":"staffNo","searchParam":"GH0001","fieldType":"LIKE"}]'
```

查询单个员工的教育经历时，直接使用教育经历列表的 `staffName/LIKE` 或 `staffNo/LIKE` 条件。不要先通过花名册把姓名或工号解析为 `staffId`；教育经历记录虽然返回 `staffId`，该列表不使用 `staffId/EQUAL` 作为筛选条件。

## 工作经历

```bash
ihr-cli staff +archiveList --meta-data-code tab_staff_job_history
ihr-cli staff +archiveList --meta-data-code tab_staff_job_history --sort-field createdDate --sort-type DESC --page 1 --page-size 20
```

## 证书

```bash
ihr-cli staff +archiveList --meta-data-code tab_staff_certificate --page 1 --page-size 20
ihr-cli staff +archiveList --meta-data-code tab_staff_certificate --search-items '[{"searchKey":"certificateName","searchParam":"CPA","fieldType":"LIKE"}]'
```

证书列表命令侧统一使用 `--search-items`，CLI 会转换为当前封装所需的数据形态。示例里的 `certificateName`、`staffId` 等短字段名是 CLI 入口别名，发往后端前会补成 `tab_staff_certificate.<field>` 形式的 table-component `columnCode`。

## 家庭成员

```bash
ihr-cli staff +archiveList --meta-data-code tab_staff_family_member --page 1 --page-size 20
ihr-cli staff +archiveList --meta-data-code tab_staff_family_member --search-items '[{"searchKey":"staffId","searchParam":"staff-001","fieldType":"EQUAL"}]'
ihr-cli staff +archiveList --meta-data-code tab_staff_family_member --search-items '[{"searchKey":"relationship","searchParam":"PARENT","fieldType":"EQUAL"}]'
```

家庭成员列表命令侧统一使用 `--search-items`，CLI 会转换为当前封装所需的数据形态。示例里的 `memberName`、`relationship`、`staffId` 等短字段名是 CLI 入口别名，发往后端前会补成 `tab_staff_family_member.<field>` 形式的 table-component `columnCode`。

## 绩效档案

```bash
ihr-cli staff +archiveList --meta-data-code tab_staff_performance --page 1 --page-size 20
ihr-cli staff +archiveList --meta-data-code tab_staff_performance --search-items '[{"searchKey":"performanceYear","searchParam":"2026","fieldType":"EQ"}]'
```

绩效档案命令侧统一使用 `--search-items`，CLI 会转换为当前封装所需的数据形态。

## 自定义档案列表

先查元数据列表，选择 `metaDataType=SUBSET` 的目标档案：

```bash
ihr-cli staff +flexMetaList --kind custom
```

- 查询档案业务数据时，使用列表返回的 `metaCode`，传给 `--meta-data-code`。
- `metaDataId`（列表中的 `id`）不用于业务取数；只有需要查看该档案的字段详情时，才执行 `ihr-cli staff +flexMetaGet --meta-data-id <id>`。

再查询自定义档案列表：

```bash
ihr-cli staff +archiveList --meta-data-code "<metaCode>" --meta-data-type SUBSET
ihr-cli staff +archiveList --meta-data-code "<metaCode>" --meta-data-type SUBSET --search-items '[{"searchKey":"D_TEXT_1","searchParam":"A","fieldType":"EQ"}]'
```

CLI 会把 `--meta-data-code` 转为后端 body 中的 `rosterQueryParams.subsetMetaCode`，把 `--page-size` 转为 `rosterQueryParams.rows`，把 `--search-items` 转为 `rosterFlexQueryParams`。`subset` 不作为用户侧协议暴露。

## 自定义档案按员工取数

按员工 ID 查询自定义档案数据：

```bash
ihr-cli staff +archiveGet --staff-id "staff-001" --meta-data-code "<metaCode>" --meta-data-type SUBSET
```

CLI 顶层不暴露 `subset` 概念，统一用 `archive` 表达员工档案业务数据。

## `staff +archiveList` 业务参数

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--meta-data-code` | string | CONDITIONAL | 无 | FlexMetaData `metaCode` | 分项参数模式必填；JSON 可提供 `metaDataCode` | 选择固定档案分支或自定义子集 | 固定档案用于命令内部分支选择；自定义子集映射 `rosterQueryParams.subsetMetaCode` |
| `--meta-data-type` | string | CONDITIONAL | 固定白名单按 `ENTITY` 处理 | `ENTITY/SUBSET` | 自定义子集必须传 `SUBSET`；固定白名单可省略或传 `ENTITY` | 校验固定档案与自定义子集边界，不按 code 前缀猜类型 | CLI routing/validation；写入 dry-run request envelope，不作为统一后端字段 |
| `--search-items` | string | OPTIONAL | 无 | JSON 对象数组 | 与 `--json/--stdin` 互斥 | 统一表达档案查询条件 | 教育/工作/绩效 -> `flexSearchItems`；证书/家庭 -> `specification.predications`；自定义 -> `rosterFlexQueryParams` |
| `--sort-field` | string | OPTIONAL | 无 | 真实可排序字段或字段 code | 自定义子集不支持 | 指定固定档案排序字段 | 教育/工作/绩效 -> `sortField`；证书/家庭 -> `sort[]` |
| `--sort-type` | string | OPTIONAL | 后端分支默认值 | 通常为 `ASC/DESC` | 仅在提供 `--sort-field` 时有效；自定义子集不支持 | 指定固定档案排序方向 | 教育/工作/绩效 -> `sortType`；证书/家庭 -> `sort[]` 中的方向 |
| `--page` | int | OPTIONAL | `1` | CLI 从 1 开始 | `1-∞` | CLI 用户侧页码 | 教育/工作/绩效 -> `page`；证书/家庭 -> `page-1`；自定义 -> `rosterQueryParams.page` |
| `--pageSize` | int | OPTIONAL | `20` | 条/页，范围 `1-100` | 与 `--page-size` 二选一使用 | 每页记录数 | 固定 flex -> `pageSize`；证书/家庭 -> `size`；自定义 -> `rosterQueryParams.rows` |
| `--page-size` | int | OPTIONAL | `20` | `--pageSize` 的 kebab-case alias | 与 `--pageSize` 二选一使用 | 每页记录数 | 同 `--pageSize` |

JSON/stdin 与分项参数互斥，并复用相同的路由、字段别名、操作符和分页转换：

```bash
ihr-cli staff +archiveList --json '{"metaDataCode":"tab_staff_certificate","metaDataType":"ENTITY","searchItems":[{"searchKey":"certificateName","searchParam":"CPA","fieldType":"LIKE"}],"page":1,"pageSize":20}'
```

## `staff +archiveGet` 业务参数

| 参数 | 类型 | 必填状态 | 默认值 | 枚举/格式/单位 | 条件依赖 | 业务说明 | 请求映射 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `--staff-id` | string | CONDITIONAL | 无 | 员工业务 ID | 分项参数模式必填；JSON 可提供 `staffId` | 指定要读取自定义档案的员工 | `query.staffId` |
| `--meta-data-code` | string | CONDITIONAL | 无 | 逗号分隔 `metaCode`，最多 5 个 | 分项参数模式必填；JSON 可提供 `metaDataCode` | 指定一个或多个自定义子集 | `query.dataMetaCodes` |
| `--meta-data-type` | string | CONDITIONAL | 无 | 只能为 `SUBSET` | 分项参数模式必填；JSON 可提供 `metaDataType` | 证明目标是自定义子集，防止固定档案误入通用接口 | CLI-only validation，不发送到后端 query |

```bash
ihr-cli staff +archiveGet --json '{"staffId":"staff-001","metaDataCode":"custom_archive_1","metaDataType":"SUBSET"}'
```

全局输出参数、`--dry-run` 和 JSON 协议遵循 `ihr-shared`。

`search-items[].fieldType` / `operator` 只支持 CLI 已映射的操作符：`EQUAL/EQ/EQUALS`、`LIKE/CONTAINS`、`NOT_LIKE/NOT_CONTAINS`、`NOT_EQUAL/NE/NOT_EQUALS`、`IN`、`NOT_IN`、`GREATE_THAN/GREATER_THAN/GT`、`GREATE_ETHAN/GREATER_THAN_EQUAL/GE/GTE`、`LESS_THAN/LT`、`LESS_ETHAN/LESS_THAN_EQUAL/LE/LTE`、`BETWEEN`、`IS_NULL`、`IS_NOT_NULL`。不要编造其他 `fieldType`；未知值会在本地按参数错误拦截。

## 分页语义

所有档案分支的 CLI 用户侧 `--page` 都从 `1` 开始，`--json`/`--stdin` 使用相同语义。不同档案协议之间的页码和字段转换由 Shortcut 内部完成，Agent 不自行减一或改写分页字段。

## 核心约束

1. `companyId`、`userId` 由 gateway 下传，不需要手动传。
2. `archive list` 支持教育经历、工作经历、证书、家庭成员、绩效这 5 个固定档案白名单，以及 `metaDataType=SUBSET` 的自定义子集；档案业务查询使用 `metaCode`。
3. `archive get` 只支持 `metaDataType=SUBSET` 的自定义子集，一次最多查询 5 个 `meta-data-code`。
4. `+archiveList` 不传 `--fields`；字段含义、可排序字段和选项先走 `+flexMetaGet/+flexMetaSortableFields/+flexMetaValueList/+flexMetaValueTree`，不要让业务数据接口返回 meta。
5. 用户侧统一用 `--search-items`。后端字段名仍按真实接口保留：教育/工作经历/绩效使用 `flexSearchItems`，证书/家庭成员使用 `Ihr360SearchBody.specification.predications`，自定义档案使用 `rosterFlexQueryParams`。
6. 证书/家庭成员的业务字段可写短字段名，但 CLI 会在请求后端前映射为真实 `columnCode`，例如 `certificateName -> tab_staff_certificate.certificateName`、`staffId -> tab_staff_family_member.staffId`。员工主表字段如 `staffName/staffStatus/departmentId` 保持后端现有非限定写法。
