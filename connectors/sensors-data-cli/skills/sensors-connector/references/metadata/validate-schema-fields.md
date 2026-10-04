# 埋点 Schema 字段关系校验

> 工具 `metadata.schema-field-validate` · 命令 `sensors metadata schema-field-validate` · 类型 查询（校验）

## 用途

批量校验一份元事件定义与系统内实际 schema 的一致性：事件 schema 是否已注册、每个属性是否存在、`display_name` 与 `data_type` 是否与系统一致。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | JSON / 文件 / stdin | 是 | — | 元事件数组 JSON；传 `-` 从 stdin 读取，传文件路径读取该文件；必须是 JSON array，每项至少包含 `event_name` | `[{"event_name":"trading_day_management",…}]` |
| `--dry-run` | 开关 | 否 | 关闭 | 输出逐元事件将发送的 `schema.field.list` 请求预览，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata schema-field-validate --help`。

## 输入 Schema

`--input` 数组每个元素（元事件对象）：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `event_name` | 字符串 | 是 | 事件英文变量名，内部映射为 `events.<event_name>` 后校验 | `trading_day_management` |
| `display_name` | 字符串 | 否 | 事件显示名；仅透传输入，不参与核心校验 | `交易日历` |
| `platform` | 字符串 | 否 | 应埋点平台；仅透传输入，不参与核心校验 | `ANDROID` |
| `trigger_timing` | 字符串 | 否 | 触发时机；仅透传输入，不参与核心校验 | `用户提交订单成功时` |
| `remark` | 字符串 | 否 | 元事件备注；仅透传输入，不参与核心校验 | `核心事件` |
| `properties` | 数组 | 否 | 属性数组，逐条校验下列三个字段 | `[{"property_name":"is_trading_day",…}]` |

`properties[]` 每个元素：`property_name`（必填，属性名）、`property_display_name`（必填，属性显示名）、`data_type`（必填，属性数据类型；比较时忽略大小写差异）。

- 以 `--schema` 实时输出为最终事实源；本命令无 `--schema` 时以 `--dry-run` 输出的请求预览为准。

## 构造流程

从一份元事件定义到校验载荷的步骤化映射：

### 1. 组织元事件数组

`--input` 是 JSON array（内联、文件路径或 `-` stdin），每个元素对应一个待校验元事件；从采集方案 / 设计稿逐事件搬运转写，不推断方案未给出的属性。

### 2. 事件级字段映射

| 采集方案字段 | `--input` 键 | 校验行为 |
|---|---|---|
| 事件英文变量名 | `event_name`（必填） | 映射为 `events.<event_name>` 后校验 schema 是否已注册 |
| 事件显示名 / 平台 / 触发时机 / 备注 | `display_name` / `platform` / `trigger_timing` / `remark` | 仅透传回显，不参与校验，可省略 |

### 3. 属性级字段映射

每个属性一个 `properties[]` 元素，三键全部必填：`property_name`（属性名，存在性校验）、`property_display_name`（显示名，精确比较）、`data_type`（数据类型，忽略大小写比较）。事件-字段关系用嵌套表达：属性挂在哪个事件的 `properties` 下，就校验哪个 `events.<event_name>` schema 下的字段。

### 4. dry-run 预览后执行

```bash
sensors metadata schema-field-validate --input meta-events.json --dry-run
```

`meta-events.json` 载荷示例：

```json
[
  {
    "event_name": "order_submit",
    "display_name": "提交订单",
    "trigger_timing": "用户提交订单成功时",
    "properties": [
      {"property_name": "order_amount", "property_display_name": "订单金额", "data_type": "NUMBER"}
    ]
  }
]
```

预览输出逐事件的 `schema.field.list` 请求（`requests[].schema_name`）；确认映射目标无误后去掉 `--dry-run` 真实执行，按 `results[]` 逐事件回传校验结论。

## 输出

`results[]` 每个元事件一条：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `results[].event_name` | 输入事件名 | `trading_day_management` |
| `results[].schema_name` | 映射后的 `events.<event_name>` | `events.trading_day_management` |
| `results[].valid` | 当前元事件是否校验通过（无错误项即通过） | `true` |
| `results[].errors[]` | 失败原因数组，成功时为空数组 | `[]` |

`errors[]` 每个元素的结构：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `level` | 失败层级：`event`（事件级）/ `property`（属性级） | `property` |
| `field` | 失败字段：`event_name` / `property_name` / `property_display_name` / `data_type` | `property_name` |
| `error_type` | 失败类型：`not_found`（未注册）/ `mismatch`（不一致）/ `api_error`（上游接口异常） | `not_found` |
| `reason` | 稳定原因码，如 `schema_not_found` / `field_not_found` / `display_name_mismatch` / `data_type_mismatch` / `upstream_api_error` | `field_not_found` |
| `property_name` | 关联属性名，事件级失败时为空 | `not_exist_prop_x` |
| `input_value` / `actual_value` | 输入值与系统实际值 | `not_exist_prop_x` / `null` |
| `message` | 人类可读说明 | `property 'not_exist_prop_x' not found…` |
| `upstream` | 上游 `code` / `message` / `request_id` | `{"code":null,"message":null,"request_id":null}` |

输出解读要点：

- `not_found`（事件级 `schema_not_found` / 属性级 `field_not_found`）表示目标在系统中**未注册**；`mismatch` 表示已注册但定义与输入不一致。
- `valid=true` 仅表示 schema 定义与输入一致，**不代表已有数据上报**；数据上报状态用 `metadata.events --include-empty` 或 `metadata.event-get` 输出的 `has_data` 判定。
- 单个元事件接口异常只影响当前事件结果（记为 `api_error`），不中断同批次其他事件。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| UsageError（输入校验失败） | `--input` 不是 JSON 数组、元素缺 `event_name`、`properties[]` 元素缺必填字段 | 按错误信息修正 JSON 后重试，此阶段不会发起请求 |
| JSON 解析失败 | `--input` 不是合法 JSON | 核对 JSON 语法与文件路径 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |

## 使用约束

- 只读校验，不写入任何 schema 变更；发现不一致后的处理（改名、重建、修正输入）由调用方决定。
- `data_type` 比较忽略大小写；其余字段精确比较。
- 校验结果按 `results[]` 原样传回调用方，不自行汇总删减错误项。
