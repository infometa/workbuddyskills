# 属性批量创建

> 工具 `metadata.field-create` · 命令 `sensors metadata field-create` · 类型 写入

## 用途

在一个已存在的 schema 下批量创建普通属性（固定 `MAIN_TABLE_COLUMN` 直接列映射）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--schema-name` | 字符串 | 是 | — | 完整 schema 名且必须已存在，如 `events.order_submit`、`users`；CLI 不自动查找、补全或建 schema | `events.trading_day_management` |
| `--items` | JSON 数组 | 是 | — | 待创建属性数组，JSON array 或 `@file.json`；所有元素都归属同一 `--schema-name`，单字段创建也必须传单元素数组 | `[{"name":"order_amount","display_name":"订单金额","data_type":"NUMBER","created_by":"meta_tester",…}]` |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON 并退出，不调用创建接口 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata field-create --help`。

## 输入 Schema

`--items` 每个元素的字段：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `name` | 字符串 | 是 | 属性名；同一批内不能重复，不能为空字符串或纯空白 | `order_amount` |
| `display_name` | 字符串 | 是 | 属性显示名，在所属 schema 内需保持唯一 | `订单金额` |
| `data_type` | 字符串 | 是 | 数据类型，仅支持 `STRING` / `NUMBER` / `BOOL` / `DATE` / `DATETIME`（比较前会归一化为大写） | `NUMBER` |
| `created_by` | 字符串 | 是 | 属性元数据生产方标识，如 `sensorsdata.horizon.meta` | `meta_tester` |
| `identity` | 布尔 | 否 | 是否为识别键 | `false` |
| `required` | 布尔 | 否 | 是否必填 | `false` |
| `visible` | 布尔 | 否 | 是否可见 | `true` |
| `enable` | 布尔 | 否 | 是否启用 | `true` |
| `remark` | 字符串 | 否 | 属性示例或说明，对应 field 列表返回的 `remark` | `示例：99.90，单位为元` |

- 不支持创建：`DECIMAL` / `TIMESTAMP` / `OBJECT_ARRAY` 等复杂类型、扩展表字段、复杂表达式字段、维度字典属性。
- 以 `--schema` 实时输出为最终事实源；本命令无 `--schema` 时以 `--dry-run` 打印的请求 JSON 为准。

## 构造流程

从业务输入到批量创建的步骤化映射（确认挂载目标 → 构造 items → dry-run 预览 → 确认 → 执行 → 回读）：

### 1. 确认挂载目标

用 `metadata.schema-get` / `metadata.fields` 确认 `--schema-name`（如 `events.order_submit`、`users`）已存在；本命令不建 schema，多个 schema 的属性分多次调用。

### 2. 构造 --items 数组

每个待创建属性一个元素，单字段创建也传单元素数组：

| 业务输入 | `items[]` 键 | 映射规则 |
|---|---|---|
| 属性英文变量名 | `name` | 同一批内不可重复 |
| 属性中文名 | `display_name` | schema 内需唯一 |
| 值类型（字符串 / 数值 / 布尔 / 日期 / 日期时间） | `data_type` | 映射为 `STRING` / `NUMBER` / `BOOL` / `DATE` / `DATETIME`（比较前归一化为大写） |
| 生产方标识 | `created_by` | 如 `meta_tester` |
| 识别键 / 必填 / 可见 / 启用 | `identity` / `required` / `visible` / `enable` | 布尔，仅显式传入时写入 |
| 属性示例或说明 | `remark` | 请求中映射为 `custom_params.meta_desc` |

CLI 固定按 `MAIN_TABLE_COLUMN` 直连列映射创建，不暴露挂载方式参数。

### 3. dry-run 预览

```bash
sensors metadata field-create --ai-session-id <ai_session_id> --schema-name events.order_submit \
  --items '[{"name":"order_amount","display_name":"订单金额","data_type":"NUMBER","created_by":"meta_tester","remark":"示例：99.90，单位为元"}]' \
  --dry-run
```

多字段一次提交时把元素逐个追加进同一数组（字段多时写文件后 `--items @file.json`），预览逐项核对 `fields[]` 的名称、类型与挂载 schema。

### 4. 确认与执行

向调用方展示待创建清单（schema、字段名、显示名、类型）与待执行命令，收到精确回复 `Approved` 后用相同输入执行。

### 5. 回读

用 `metadata.field-get` / `metadata.event-fields` 回读确认创建结果。

## 输出

- `--dry-run`：输出请求体 JSON——`fields[].schema_name`、`fields[].field.name` / `display_name` / `data_type.type` / `created_by`（`identity` / `required` / `visible` / `enable` 显式传入时输出）、`fields[].field.custom_params.meta_desc`（显式传 `remark` 时）、`fields[].field.data_mapping.source_type`（固定 `MAIN_TABLE_COLUMN`）。
- 真实执行：输出请求级摘要——`schema_name`、`requested_count`、`requested_field_names`、`data`（服务端原始返回，成功场景通常为空对象）；创建结果以回读为准。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| UsageError（JSON / 校验失败） | `--items` 非数组、元素缺必填键、`data_type` 超范围、`name` 重复、数组为空 | 按错误信息修正输入后重试，此阶段不会发起请求 |
| Schema 不存在 | `--schema-name` 未注册 | 先用 `metadata.fields` / `metadata.schema-get` 确认 schema 存在；不假设 CLI 会自动建 schema |
| display_name 冲突 / 服务端拒绝 | 显示名已被占用或权限不足 | 读取现状后把冲突交回调用方决定 |

## 使用约束

- 同一 `--items` 数组内不能混入多个 schema 的属性；所有元素必须归属当前 `--schema-name`。
- 真实执行按 SKILL.md「写操作安全联锁」：先 `--dry-run` 预览，向调用方展示变更摘要与待执行命令，取得精确回复 `Approved`（提示语固定为「如确认执行，请回复：Approved」）后才执行；输入或目标变化后旧确认失效。
- 执行成功后用 `metadata.field-get` / `metadata.event-fields` 回读确认；回读失败时不得宣称最终状态已验证。
- CLI 当前不提供字段删除命令；删除类请求返回不支持，不寻找旁路。
