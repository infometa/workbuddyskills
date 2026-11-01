# query\_ 类型字段处理协议 (Query Field Protocol)

## 核心原则

遇到 `query_` 开头的字段，**不要问用户要填什么**，直接按以下 **3 个原子步骤** 依次执行，前一步完成再进下一步。

---

## 步骤 1：解析关联 ID

从 `crud_get_yidea_table_def` 返回的表单 Schema 中，找到该 `query_xxx` 字段的 `relationTable.id` 值。

**输出**：关联表单 ID（`formId`）

## 步骤 2：自动查询候选数据

立即调用 `crud_yidea_table_search` 查询该关联表单：

- 参数：`{ request: { formId: "<步骤1获取的formId>", pageIndex: "1", take: "5" } }`
- 禁止跳过此步或要求用户手动输入

**输出**：候选列表（最多 5 条）

### `filters`（内置过滤条件）

`query_` 字段的 Schema 中可能包含 `filters` 数组，这是**系统预设的查询筛选条件**，在执行查询时应该一并应用：

```json
"filters": [
  {
    "type": "select",      // 字段类型
    "param": "select_1720408479877_4e37",  // 被筛选的字段 model
    "condition": "Equal",   // 筛选条件
    "valueStr": "{\"value\":\"未开始\",\"label\":\"未开始\"}"  // 筛选值
  }
]
```

每个 filter 包含：
- `param`：关联表中要过滤的字段名（model）
- `condition`：过滤条件（Equal、Contains 等）
- `valueStr`：过滤值的 JSON 字符串

查询时应将此条件加入到 `crud_yidea_table_search` 的搜索条件中。

## 步骤 3：展示并提交

### `selectingColumns`（回显列定义）

`query_` 字段的 Schema 中可能包含 `selectingColumns` 数组，定义用户选定后要**回显展示的列**：

```json
"selectingColumns": [
  { "field": "serialNo", "title": "需求池流水号" },
  { "field": "input_xxx", "title": "申请单号" },
  ...
]
```

- `field`：关联表中对应字段的 model 名
- `title`：展示给用户看的列标题

这个 `selectingColumns` 中的值需要传到 `crud_yidea_table_search` 的同名参数中。

展示候选数据时，优先使用 `selectingColumns` 指定的字段来构建表格（而不是把所有字段都抛出来），让用户看得更聚焦。

### 提交值

- 用户选择后，提交时 `value` **必须用原始 ID**（UUID 字符串），不要用名称

## 关于 `filters` 的实战用法

`filters` 是 `query_` 字段定义中的**预设过滤条件声明**，告诉你在查询关联表时应该筛选哪些数据。

查询时需通过 `items` 参数传入过滤条件，**关键格式**：

```json
// ✅ 正确的格式
"items": [{
  "name": "select_1720408479877_4e37",   // 字段 model
  "values": ["未开始"],                    // 值用数组，不是字符串！
  "methodType": "Equal"                   // 必须指定条件类型
}]

// ❌ 错误的格式
"items": [{
  "name": "select_1720408479877_4e37",
  "value": "未开始"   // 应该用 values: ["未开始"]
}]
```

注意 `values` 是**数组**，不是 `value` 字符串。这适用于 select、input 等类型字段的过滤。

## 降级策略

如果查询返回空结果或失败 → 告知用户"未找到匹配的关联记录，请检查数据或联系管理员"。
