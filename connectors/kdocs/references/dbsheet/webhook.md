# Webhook 与开放协作

## 1. dbsheet.list_webhooks

#### 功能说明


**必填 query**：无。

**前置条件**：应用具备订阅查询权限。



#### 调用示例

列出订阅：

```json
{
  "file_id": "string"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | hooks 列表或映射，以实际 data 为准 |


---

## 2. dbsheet.create_webhook

#### 功能说明

**前置条件**：应用具备多维表格 Webhook 能力；`callback_url` 可公网访问且可接收 JSON 格式 POST 请求。



#### 操作约束

- **后置验证**：list_webhooks 确认 webhook 已创建
- **提示**：勿向不可信回调地址泄露事件数据；删除订阅用 dbsheet.delete_webhook

**幂等性**：否 — 重复调用会创建多个订阅，先确认是否已成功

#### 调用示例

创建订阅（新增记录）：

```json
{
  "file_id": "string",
  "body": {
    "command": "create_record",
    "data": {
      "sheet_id": 1234567890
    },
    "callback_url": "https://example.com/dbsheet/webhook"
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `body` (object, 必填): JSON 请求体，包含 command、data、callback_url

**请求体（`body`）字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `command` | string | Hook 订阅命令。可选值：`create_record`（订阅添加记录）、`update_sheet`（订阅修改记录）、`remove_record`（订阅删除记录）、`update_records_parent`（订阅父子记录变动）、`create_field`（订阅新增字段）、`update_field`（订阅更新字段）、`remove_field`（订阅删除字段） |
| `data` | object | Hook 订阅规则，根据 `command` 选择具体规则对象 |
| `callback_url` | string | 回调 URL，用于接收 hook 触发通知；该接口应接受 JSON 格式 POST 请求 |

**Hook 订阅规则详情（`data`）**

- 当 `command = create_record`（数据表内添加记录，HookRuleCreateRecord）

  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `sheet_id` | int64 | 数据表 id |

- 当 `command = update_sheet`（数据表内修改记录，HookRuleUpdateSheet）

  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `sheet_id` | int64 | 数据表 id |
  | `include_formula_result_change` | bool | 是否监听公式结果变化，默认 `false` |
  | `skip_after_match_create_and_fill` | bool | 是否在监听新建或修改记录时避免重复触发，默认 `false`（依然触发） |

- 当 `command = remove_record`（数据表内删除记录，HookRuleRemoveRecord）

  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `sheet_id` | int64 | 数据表 id |
  | `record_ids` | array[string] | 被监听删除的记录 id；监听所有记录删除时传空数组 |

- 当 `command = update_records_parent`（数据表内父子关系变动，HookRuleRecordParent）

  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `sheet_id` | int64 | 数据表 id |
  | `record_ids` | array[string] | 被监听父子关系变动的记录 id；监听所有记录时传空数组 |

- 当 `command = create_field`（数据表内添加字段，HookRuleCreateField）

  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `sheet_id` | int64 | 数据表 id |

- 当 `command = update_field`（数据表内修改字段，HookRuleUpdateField）

  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `sheet_id` | int64 | 数据表 id |
  | `field_id` | string | 被监听修改的字段 id |

- 当 `command = remove_field`（数据表内删除字段，HookRuleRemoveField）

  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `sheet_id` | int64 | 数据表 id |
  | `field_id` | string | 被监听删除的字段 id |


#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 含 hook_id 等，以实际返回为准 |


---

## 3. dbsheet.delete_webhook

#### 功能说明


**前置条件**：`hook_id` 须为当前文档下有效订阅（可先 `dbsheet.list_webhooks`）。



#### 操作约束

- **用户确认**：取消后需重新创建才能接收事件

**幂等性**：否 — 删除失败勿盲目重试，先 list_webhooks 确认 hook_id

#### 调用示例

取消订阅：

```json
{
  "file_id": "string",
  "hook_id": "hook_xxx"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `hook_id` (string, 必填): Hook 订阅 ID
- `body` (object, 可选): JSON 请求体，补充附加字段；可省略或传 {}

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | 接口返回详情 |


---

