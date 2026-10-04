# staff flex field

## 什么时候需要

用户提到以下语义时，读取本文件：

- 自定义字段、扩展字段、flex field、flexfield
- 员工自定义字段的值
- 字段含义、字段选项、字段 meta、FlexMetaData
- `CODE_TYPE`、动态字典、`codeTypeId`

## 核心口径

花名册数据查询不再使用 `--includeFlex`。如果需要某个 flex 字段值，把该字段 code 写进 `--fields`：

```bash
ihr-cli staff +search --fields "id,staffName,D_CODE_TYPE_14,D_DATE_2"
```

服务端会按字段 code、权限和脱敏策略返回对应值。Agent 不应默认拉取所有 flex 字段。

## 字段 Meta 策略

数据查询不使用 `--includeMeta`。原因是字段说明、字典来源和动态字段配置体积较大，每次列表/详情都返回会浪费。

处理规则：

1. 需要调用数据接口时，只传该接口真实支持的业务查询参数；只有 `staff +search` 使用 `--fields` 选择返回字段。
2. 需要解释员工档案字段类型、CODE_TYPE 或 optionSource 时，优先使用 `staff +flexMeta*`。
3. 其他不在 flex field 中维护的字段，可按 interface meta 中的本地 `STATIC` 或明确 `API` optionSource 解释；HttpDB 只用于设计期校准。
4. 不要让列表/详情每次返回 meta。

## 主数据字段识别

固定字段只使用已确认覆盖，不按 `xxxId` 后缀猜测：

| Staff 字段 | 主数据类型 |
| --- | --- |
| `id` / `staffId` / `supervisorId` | `STAFF` |
| `departmentId` | `DEPARTMENT` |
| `corporationId` | `CORPORATION` |
| `positionId` | `POSITION` |
| `jobTitleId` | `JOB_TITLE` |
| `positionLevelId` | `POSITION_GRADE` |
| `companySiteId` | `COMPANY_SITE` |
| `jobCategory` | `JOB_CATEGORY` |

`companyId` 是租户上下文，绝不映射为 `CORPORATION`。

租户 Flex 字段先读取 `staff +flexMetaGet` 返回的 `fieldGroupList[].fieldList[]`，以真实 `fieldName` 作为 Roster 字段键、以 `fieldType` 判断语义。首期只把 `DEPARTMENT` 和 `JOBCATEGORY` 识别为主数据；`JOBCATEGORY` 规范化为 `JOB_CATEGORY`。`DIM_ORG_*`、`DIM_POSITION_*` 和未知类型保持 raw。

只要用户提供了 FlexMetaData ID 并要求查询动态字段，就必须先实际执行 `staff +flexMetaGet`，再执行 `staff +search --fields`；不能因为用户同时说出了字段 code，或本地文档已有示例，就跳过 Meta 请求并声称已经确认字段类型。

Staff Roster 有一个必须遵守的响应差异：聚合层会把请求字段中的 `D_DEPARTMENT_*` 值从部门 ID 转成部门名称后再返回。因此：

1. Flex Meta 仍可说明该字段原始语义是 `DEPARTMENT`。
2. `staff +search` 返回的 `flexAttributes.D_DEPARTMENT_*` 已是名称文本，不再拿它调用 `master-data +batch-get`。
3. Flex `JOBCATEGORY` 当前没有同类自动名称转换；如果 Roster 只返回 ID 且最终答案需要名称，再调用 `master-data +batch-get --type JOB_CATEGORY`。
4. Flex Meta 获取失败、字段不在当前权限过滤后的 Meta 中、或类型未知时，不猜测字段类型，不影响原始 Staff 查询；最终答案保留 raw 值并说明未解析。

`JOBCATEGORY` 的格式化必须走统一 `master-data +batch-get`。不要调用 `organization +jobCategories` 或其他 Organization 列表建立旁路映射，也不要逐个 ID 调 Search/Get。

动态 Schema 只在当前单次执行内按 `metaDataId/metaCode + 版本标识 + fields` 复用，不写入 `~/.ihr-cli`。

## Flex Meta 命令

```bash
ihr-cli staff +flexMetaList
ihr-cli staff +flexMetaList --kind custom
ihr-cli staff +flexMetaGet --meta-data-id "meta-001"
ihr-cli staff +flexMetaSortableFields --meta-data-id "meta-001"
ihr-cli staff +flexMetaValueList --code-value-id "cv-001"
ihr-cli staff +flexMetaValueTree --code-type-id "ct-001" --group-code "group-001"
```

各命令的完整 Flag 类型、条件必填、默认值、JSON 字段和请求映射见 [`ihr-staff-flex-meta.md`](ihr-staff-flex-meta.md)。`staff +search` 的 `--fields`、分页 alias 和筛选字段完整映射见 [`ihr-staff-search.md`](ihr-staff-search.md)。

自定义档案字段元信息也用 `flex-meta get`，不要创建或使用 `staff subset meta`。

## CODE_TYPE 规则

`CODE_TYPE` 表示选项型字段。无论它出现在稳定字段还是 flex 字段中，都不要把 value 直接当展示文案。

处理规则：

1. 优先保留原始 value。
2. 用户明确要求展示含义、中文名或选项列表时，再查询字段说明或字典。
3. 如果 interface meta 里带有 `optionSource`，按该来源取 options。
4. 如果字段来自 FlexMetaData 或 flexField，优先使用 `flex-meta value-list/value-tree`。
5. 如果没有字段说明，不要编造 label。

## 常见错误

| 错误 | 修正 |
| --- | --- |
| 为了拿 flex 值使用 `--includeFlex` | 花名册列表改为把 flex 字段 code 写进 `staff +search --fields`；档案数据先查 `flex-meta` |
| 每次列表/详情都要求返回 `includeMeta` | 改为按需读取 interface meta 或 `staff +flexMeta*` |
| 使用顶层 `subset` 命令查自定义档案元数据 | 改为 `staff +flexMetaList/+flexMetaGet` |
| 把 `CODE_TYPE` value 当 label | 先查询字段说明或字典 options |
| 用 `base +selectStaffs` 查员工档案字段 | 改用 `staff +search`、`staff +get` 或 `staff +archive*` |

实际执行必须使用公开 shortcut 或 metadata command，不得改用 raw HTTP。
