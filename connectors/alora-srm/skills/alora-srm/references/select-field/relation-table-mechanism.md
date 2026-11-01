# RelationTable 数据来源机制

> 易点系统中 `select` 类型字段通过 `relationTable` 配置从其他表单动态获取选项数据的通用机制。
> 无论是否级联，只要字段配置了 `relationTable`，都适用此逻辑。

---

## 一、概述

普通 select 字段通常使用 `options` 数组定义静态的选项列表。但当 `options` 中同时配置了 `relationTable`（关联表）时，select 字段的可选项可以动态来源于另一张表单的数据。

此机制是级联选择器的基础，即使非级联的 select 字段也可以配置 `relationTable`。

---

## 二、配置结构

select 字段中与数据来源相关的配置：

```json
{
  "type": "select",
  "name": "字段名称",
  "model": "select_xxxxxxxxxxxx",
  "options": {
    // ── ① 静态候选值（兜底） ──
    "options": [
      { "label": "显示文本", "value": "存储值" }
    ],

    // ── ② 关联表配置（数据来源） ──
    "relationTable": {
      "type": "custom",
      "id": "目标表单的 tableId（UUID）",
      "name": "目标表单名称"
    },

    // ── ③ 过滤条件（可选，有则级联，无则取全量） ──
    "filters": []
  }
}
```

---

## 三、数据获取方式

### 3.1 查询关联表

使用 `crud_yidea_table_search` 工具，`formId` 传 `relationTable.id` 的值：

```json
{
  "request": {
    "formId": "relationTable.id 的值",
    "pageIndex": "1",
    "take": "200"
  }
}
```

### 3.2 提取选项

从查询返回的 `results` 数组中，提取对应字段（model）的**去重值**作为选项。

展示给用户的是去重后的 **label** 值列表。

### 3.3 数据来源优先级

| 优先级 | 来源 | 说明 |
|:---|:---|:---|
| 1（优先） | relationTable | 查询关联表单获取动态数据 |
| 2（兜底） | 静态 options | 关联表无数据或查询失败时的回退选项 |

---

## 四、查询结果示例

```json
{
  "isSuccess": true,
  "data": {
    "results": [
      {
        "input_xxx": "值A",
        "input_yyy": "值B",
        ...
      },
      {
        "input_xxx": "值C",
        ...
      }
    ]
  }
}
```

提取 `input_xxx` 字段的去重值：`[值A, 值C]` 即为该 select 字段的候选选项。

---

## 五、提交数据

使用 `crud_yidea_table_add` 工具提交时，select 字段的 `value` 传**纯文本值**：

```json
{
  "request": {
    "formId": "当前表单 ID",
    "items": [
      {
        "name": "select_xxx",
        "value": "选中的文本值"       // ← 纯文本，不加 JSON 包装
      }
    ]
  }
}
```

> ⚠️ 不要传 `{"value":"...","label":"..."}` 格式的 JSON 字符串，后端会校验不通过。

---

## 六、relationTable 的应用场景

| 场景 | filters | 说明 |
|:---|:---:|:---|
| **普通带关联** | `[]` | 从关联表取全量数据作为选项，无联动 |
| **级联起始级** | `[]` | 既是关联数据来源，也是级联链条的根节点 |
| **级联下游级** | `[{...}]` | 在关联数据基础上，增加过滤条件形成联动 |

---

## 七、后端模型定义

```csharp
public class RobotRelationTable
{
    public string Type { get; set; }

    /// <summary>对应的 FormId</summary>
    public string Id { get; set; }

    /// <summary>表单名称</summary>
    public string Name { get; set; }
}
```

---

*文档版本：v1.0 | 整理日期：2026-07-03*