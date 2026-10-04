# HR 数据源查询

## 何时使用

查询历史时点名册、离职名册、历史曾在职人员、组织编制、控编维度、人员流动分析、人员情况合计、基本状况分析图表时使用。

数据源是一组通过 `formId` 参数化的通用报表接口。四个接口共用同一套输入：

| operation | 说明 |
| --- | --- |
| `ehr.hr.ds.fields` | 取该数据源的字段结构，是构造查询的唯一依据 |
| `ehr.hr.ds.list` | 列表数据 |
| `ehr.hr.ds.count` | 数量统计，返回 `totalCount`/`totalPage`/`pageSize`/`tableId` |
| `ehr.hr.ds.chart` | 图表分布数据 |

## 使用流程

**必须先调 `ehr.hr.ds.fields`**，再构造查询。字段名和操作符都来自 fields 的返回，禁止凭文档名称臆造。

1. `ehr.hr.ds.fields` 传 `formId`，拿到字段列表与可用操作符。
2. 用 `conditions` 组装过滤条件，每个条件含 `field`（字段 name）、`value`、`compareType`。
3. 调用 `ds.list` / `ds.count` / `ds.chart`。

## 输入要点

- `formId` 必填。常量表在 `weaver-work-cli ehr schema` 的 `dataSourceIds` 中，其中历史时点是 `754217732232708651`，组织编制是 `754217732232708751`，控编维度是 `754217732232709056`，人员流动是 `754217732232708655`，人员情况合计是 `754217732232709010`。
- `compareType` 支持 `eq`、`in`、`like`、`gtAndEq`、`ltAndEq`、`between`。范围条件用 `between`，`value` 传逗号分隔的 `"起始值,结束值"`，例如 `"2026-01-01,2026-12-31"`。具体可用操作符以 `ehr.hr.ds.fields` 返回的 `conditionType` 为准。
- `permissionType` 控制人员范围，默认 `personnelStatus=["normal"]`（在职）；传 `["all"]` 表示不限状态。
- **日期范围条件必须拆成 2 个条件**（2026-09-04 修正，此前传法错误）：

  ```json
  "conditions": [
    { "field": "dutyDate", "value": "2026-01-01", "compareType": "gte" },
    { "field": "dutyDate", "value": "2026-12-31", "compareType": "lte" }
  ]
  ```

  引擎取前 2 个 `conditionValue` 作为起止日期。**用单个 `between` 传 "起,止" 会失败或退化为不过滤**（见下）。

- 各数据源必填条件与实测：

  | 数据源 | formId | 必填字段 | 正确传法 | 实测 |
  |---|---|---|---|---|
  | 历史时点名册 | `754217732232708651` | `timePoint` | 单条件 `eq` | eq 2026-06-30 → 2535；eq 2025-01-01 → 0 |
  | 历史曾在职名册 | `754217732232708653` | `dutyDate` | `gte`+`lte` 双条件，`yyyy-MM-dd` | 2026 全年 2535；**2026-06 单月 2534**（不同→过滤生效）；2020 全年 0 |
  | 人员流动分析 | `754217732232708655` | `dateRange` | `gte`+`lte` 双条件，`yyyy-MM-dd` | 2026 上半年 45 |
  | 人员情况合计 | `754217732232709010` | `month` | `gte`+`lte` 双条件，值 `yyyy-MM` | 本租户无数据（count=0）|
  | 离职名册 | `754217732232708654` | `dismissDate`（可选） | `gte`+`lte` 双条件 | 2025~2026 → 9；不传也返回 9 |

- **不要用 `between`**：实测 `timePoint` 传 `between` + "起,止" 时，`_inner_params` 回显为 `paramTp: "2026-01-01,2026-12-31"`（单个字符串），返回 2535 与全量相同——**服务端并未按范围过滤，而是退化为不过滤**。`hw` 等数据源传 `between` 则直接报 500「日期范围过滤条件错误」。范围条件一律用 `gte`+`lte` 两个条件。

- 验证条件是否真生效：看返回记录的 `_inner_params`（如 `paramDutyDate: ["2026-01-01","2026-12-31"]`），它回显服务端实际收到的起止值。不要只看"没报错"就认为过滤成功。

## 命令

先取字段：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.hr.ds.fields --input-json '{"formId":"754217732232708651"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"formId":"754217732232708651"}' | weaver-work-cli --profile eteams --json ehr run ehr.hr.ds.fields --input -
```

查询某历史时点的名册：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.hr.ds.list --input-json '{"formId":"754217732232708651","conditions":[{"field":"timePoint","value":"2026-02-28","compareType":"eq"}],"pageNo":1,"pageSize":100}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"formId":"754217732232708651","conditions":[{"field":"timePoint","value":"2026-02-28","compareType":"eq"}],"pageNo":1,"pageSize":100}' | weaver-work-cli --profile eteams --json ehr run ehr.hr.ds.list --input -
```

## 输出处理

- `ds.count` 返回的是 `totalCount` / `totalPage` / `pageSize` / `tableId`，**不是** `count` 字段。要人数就取 `totalCount`。
- `ds.list` 的分页信息在 `meta.page`，默认 `pageSize=100`、`pageNo=1`。
- `ds.fields` 返回的是**数组**，元素形如 `{ id, name, fields: [...] }`，每个字段的 `conditionType` 列出可用操作符，`usage=query` 标记该字段是查询条件。构造条件前先读它。已实测各数据源字段数：历史时点/离职名册/历史曾在职 107、控编维度 26、组织编制 17、人员流动 14、人员情况合计 12、基本状况分析（年龄/性别）2。
- `ds.chart` 用于基本状况分析（年龄、性别、工龄、学历、婚姻、职称、职级、状态、安全级别）的分布数据。

## 注意

- 数据源接口是 `application/x-www-form-urlencoded` 提交（`sourceType=LOGIC` + `queryDto` 为 JSON 字符串），不是 JSON body。`queryDto` 的构造由 CLI 托管，调用方只传结构化参数，不需要手写 JSON 字符串。
- 若结构化参数无法表达所需查询，可用 `rawQueryDto` 逃生舱直接传完整对象，但传入后会覆盖 `conditions`/`queryFields`/`permissionType` 的构造结果。优先用结构化参数。
- 名册类数据源可能返回大量人员数据，回复用户时给摘要和统计口径，不要原样粘贴完整名册。
- `ds.list` 已走 `/api/bs/hr/ai/ds/getListData`，不要使用旧的 `/api/bs/hr/ds/getListData`（已废弃）。
- 涉及附件、图片或文件内容解析时，必须先说明文件内容可能进入大模型上下文，获得用户**明确确认**后才继续。

## 失败处理

- `form_id_required`：缺少 `formId`。
- `enum_invalid`：`compareType` 不在允许集合内。
- `condition_invalid`：`conditions` 的元素缺少 `field` 或格式不对。
- 查询返回业务失败时，先核对字段 name 与 compareType 是否来自 `ds.fields`，不要反复重试。
