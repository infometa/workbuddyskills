# 仪表盘

## 1. dbsheet.dashboard_copy

#### 功能说明


**前置条件**：`dashboard_id` 来自 `dbsheet.dashboard_list`。



#### 操作约束

- **后置验证**：dashboard_list 确认副本已创建

**幂等性**：否 — 重复调用可能产生多个副本，先确认是否已成功

#### 调用示例

复制：

```json
{
  "file_id": "string",
  "dashboard_id": 2,
  "body": {
    "name": "副本-仪表盘"
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `dashboard_id` (integer, 必填): 源仪表盘 ID
- `body` (object, 必填): JSON 请求体，须含 name（新仪表盘名称）

**body 根级必填**

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 新仪表盘名称 |

其它可选字段见 copy-dashboard 文档。


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
| `detail` | object | 新仪表盘 id 等 |


---

## 2. dbsheet.dashboard_list

#### 功能说明


**必填 query**：无。



#### 调用示例

列出仪表盘：

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
| `detail` | object | dashboards 数组 |


---

