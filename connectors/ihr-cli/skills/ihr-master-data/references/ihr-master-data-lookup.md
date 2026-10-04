# 主数据查询命令

主数据类型、ID kind、展示字段和解析接口以 CLI 二进制内嵌的 `metadata/master-data/registry.json` 为准；`ihr-cli master-data --help` 展示当前运行版本支持的 canonical type。下面的类型表是当前版本的可读摘要，若与运行时不一致，以当前二进制内嵌 Registry 和命令 help 为准。

## 支持的主数据类型

| canonical type | 业务含义 | ID kind |
| --- | --- | --- |
| `CORPORATION` | 法律实体 | `STRING` |
| `DEPARTMENT` | 部门 | `INT64` |
| `STAFF` | 员工 | `STRING` |
| `POSITION` | 职位 | `STRING` |
| `JOB_TITLE` | 职务 | `STRING` |
| `JOB_CATEGORY` | 职务分类 | `STRING` |
| `POSITION_GRADE` | 职级 | `STRING` |
| `COST_CENTER` | 成本中心 | `STRING` |
| `COMPANY_SITE` | 工作地点 | `STRING` |

Registry alias：`JOBCATEGORY` 归一为 `JOB_CATEGORY`。Schema 或 Flex Meta 给出的类型必须先匹配 canonical type 或 alias；未注册类型不得调用 `master-data`。

`POSITION_LEVEL`、`GRADE_SEQUENCE`、`GRADE_SYSTEM` 当前都不是已注册的 canonical type，不得自动映射为 `POSITION_GRADE` 或其他主数据类型。其中 `POSITION_LEVEL` 保留为“职层”语义，未来满足 Registry 和 Resolver 契约后可以独立登记。

三个命令同时支持分项 flags、`--json` 和 `--stdin`。JSON/stdin 与业务 flags 互斥，并进入同一归一化逻辑；JSON 数字保持整数精度。

```bash
ihr-cli master-data +search --json '{"type":"DEPARTMENT","keyword":"研发3组","limit":20,"permissionCode":"timeManage.dailyReport.view","filters":{}}'
printf '%s' '{"type":"DEPARTMENT","id":123}' | ihr-cli master-data +get --stdin
ihr-cli master-data +batch-get --json '{"type":"DEPARTMENT","ids":[123,456],"permissionCode":"timeManage.dailyReport.view"}'
```

JSON 字段：Search 使用 `type/keyword/limit/permissionCode/filters`，Get 使用 `type/id/permissionCode`，BatchGet 使用 `type/ids/permissionCode`。`filters` 必须是 JSON object，`ids` 可使用 JSON array 或逗号分隔字符串，未知字段会被拒绝。

`permissionCode` 是目标业务查询用于取得数据权限范围的功能点 Code。Domain Skill 从目标业务公开 Command 契约中取得业务查询实际使用的值后直接传入；不要根据业务名称猜测，也不要由 Resolver 自动选择 `functionCodes` 的第一项。对 `DEPARTMENT`，Resolver 调用组织树接口时会将显式 `permissionCode` 映射为 `functionCode`；未传时该调用固定使用 `organization.structure.manage.view`，不改变本命令公开输入模型。

## search

```bash
ihr-cli master-data +search --type DEPARTMENT --keyword "研发3组" --limit 20 --permission-code timeManage.dailyReport.view
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--type` | 是 | canonical 主数据类型 |
| `--keyword` | 是 | 名称、编码或关键词 |
| `--limit` | 否 | 候选上限，默认 20 |
| `--permission-code` | 否 | 目标业务查询实际使用的数据权限功能点 Code；由 Domain Skill 从业务公开 Command 契约中取得 |
| `--filters` | 否 | Provider 支持的显式 JSON object 条件；不会自动注入生效日期，也不能携带权限范围、租户、用户、令牌或鉴权控制字段 |

零候选返回空 `candidates`，由 Skill 按 NOT_FOUND 语义处理；多候选必须根据名称、编码、路径等信息消歧，不自动选第一条。候选优先级依次为 ID 精确、编码精确、名称精确、前缀和包含匹配。

## get

```bash
ihr-cli master-data +get --type STAFF --id staff-001
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--type` | 是 | canonical 主数据类型 |
| `--id` | 是 | 主数据业务 ID；`DEPARTMENT` 接受十进制数字文本 |
| `--permission-code` | 否 | 目标业务查询实际使用的数据权限功能点 Code |

## batch-get

```bash
ihr-cli master-data +batch-get --type DEPARTMENT --ids 1001,1002 --permission-code timeManage.dailyReport.view
ihr-cli master-data +batch-get --type STAFF --ids '["staff-1","staff-2"]'
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `--type` | 是 | canonical 主数据类型 |
| `--ids` | 是 | 逗号分隔或 JSON array 的主数据 ID |
| `--permission-code` | 否 | 目标业务查询实际使用的数据权限功能点 Code |

命令去重并保持首次出现顺序；`CHUNKED` Provider 按 Registry batchSize 分块，`FULL_SCAN` Provider 单次拉取全集后过滤。遗漏 ID 在 `missing` 中返回；多个分块中只有部分上游调用失败时，已成功记录仍返回，并在 `warnings` 中按错误码和 ID 标记部分失败；失败分块不进入 negative cache。同一业务查询的输入解析与输出格式化必须使用相同的 permissionCode。

`DEPARTMENT` 接受十进制数字或数字字符串，并规范化为 JSON number。其他首期主数据 ID 使用 JSON string，trim 首尾空格但保留大小写。

权限不足、上游失败或部分 ID 未找到时，不得伪造名称。业务原查询已经成功时，主数据格式化失败不能改写原业务结果；最终答案保留 ID 并附 warning。

主要错误码：`MASTER_DATA_TYPE_UNSUPPORTED`、`MASTER_DATA_ID_INVALID`、`MASTER_DATA_NOT_FOUND`、`MASTER_DATA_PERMISSION_DENIED`、`MASTER_DATA_UPSTREAM_UNAVAILABLE`、`MASTER_DATA_RESPONSE_INVALID`。这些错误都不得触发 secondparty/raw API 降级。
