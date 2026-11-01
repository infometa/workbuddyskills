# 级联选择器 (Cascade Select) 机制说明

> 易点系统中 `select` 字段通过 **filters（过滤条件）** 实现多级联动选择的机制。
> 关于 RelationTable 基础数据来源的逻辑，详见同目录下的 `relation-table-mechanism.md`。

---

## 一、概述

级联选择器是基于 RelationTable 机制的扩展。它的选项仍然来源于关联表单，但在获取数据时额外增加了 **filters（过滤条件）**，使得下级选项随上级选择动态变化。

---

## 二、filters 配置详解

### 2.1 Filter 字段定义

```json
{
  "filters": [
    {
      "type": "字段类型",          // 关联表中被筛选字段的类型
      "param": "关联表字段 model",  // 关联表中被筛选字段的 model
      "condition": "Equal",        // 过滤条件枚举
      "value": {},                  // 运行时占位
      "valueStr": "{\"id\":\"当前表单字段 model\",\"label\":\"当前表单字段名称\",\"type\":\"字段类型\"}"
    }
  ]
}
```

| 字段 | 说明 |
|:---|:---|
| `type` | 关联表中被筛选字段的类型（input / select / employeeSelect 等） |
| `param` | **关联表中**被筛选字段的 model 名称 |
| `condition` | 过滤条件：Equal / NotEqual / Contains / In 等 |
| `value` | 运行时占位对象（前端渲染时填充，定义阶段为空） |
| `valueStr` | JSON 字符串，引用**当前表单**中哪个字段作为过滤值来源 |

### 2.2 valueStr 详解

`valueStr` 声明"用当前表单中哪个字段的值，去过滤关联表"：

```json
{
  "id": "当前表单字段 model",
  "label": "当前表单字段名称",
  "type": "字段类型"
}
```

**翻译成人话**：filters 的意思是：
> "查关联表时，把关联表的 `param` 字段过滤为等于当前表单中 `valueStr.id` 字段的选中值。"

### 2.3 filters 为空数组

```
filters: []
```

表示：
- 该字段是级联链条的**起始级别（根节点）**
- 查询关联表时**不加过滤条件**，取全量数据中的目标字段值作为选项

---

## 三、级联联动逻辑

### 3.1 数据结构拓扑

```
┌─────────── 当前表单 ───────────┐       ┌──────── 关联表 ────────┐
                                │       │
  Level 1: select_A (filters:[]) │       │  P1 (字段 model_1)
           │ filter.valueStr     │       │  P2 (字段 model_2)
           ▼                     │       │  P3 (字段 model_3)
  Level 2: select_B (filter P1)  │       │  ...
           │ filter.valueStr     │       │
           ▼                     │       │
  Level 3: select_C (filter P2)  │       │
                                │       │
  ...                            │       │
└────────────────────────────────┘       └────────────────────────┘
```

### 3.2 各级别的工作方式

| 级别 | Filters | 查询方式 | 选项来源 |
|:---|:---:|:---|:---|
| 起始级 | `[]` | 查关联表全量数据 | 关联表 `P1` 字段的去重值 |
| 第 2 级 | `[{param: P1}]` | 查关联表 WHERE `P1` = 起始级选中值 | 结果中 `P2` 字段的去重值 |
| 第 3 级 | `[{param: P2}]` | 查关联表 WHERE `P2` = 第 2 级选中值 | 结果中 `P3` 字段的去重值 |
| 第 N 级 | `[{param: P(N-1)}]` | 查关联表 WHERE `P(N-1)` = 第 N-1 级选中值 | 结果中 `PN` 字段的去重值 |

### 3.3 参数对应关系

```
当前表单字段       filter.param → 关联表字段      filter.valueStr → 引用当前表单字段
────────────────  ──────────────────────────   ─────────────────────────────────────
Level 1            无                              无（filters: []）
Level 2            关联表.P1                        Level 1 选中的字段
Level 3            关联表.P2                        Level 2 选中的字段
Level N            关联表.P(N-1)                    Level (N-1) 选中的字段
```

### 3.4 级联层级

理论上支持任意 N 级级联，只要有对应的关联表字段和 filter 配置即可。

---

## 四、AI 操作流程

### Step 1：识别级联字段

从 `crud_get_yidea_table_def` 返回的字段定义中，检查 select 字段：

- 有 `options.relationTable` 且 `options.filters.length === 0` → **级联起始字段**
- 有 `options.relationTable` 且 `options.filters.length > 0` → **级联下游字段**

### Step 2：逐级查询选项

对起始级字段，查关联表全量数据，提取目标字段的去重值作为选项。

### Step 3：按级联顺序处理

1. 展示当前级别的选项让用户选择
2. 用户选择后，根据选中值构造过滤条件
3. 再次查询关联表（带过滤），提取下一级目标字段的去重值
4. 重复直到所有级联字段完成选择

### Step 4：提交数据

调用 `crud_yidea_table_add`，select 字段的 `value` 传纯文本值。

---

## 五、关键技术要点

| 要点 | 说明 |
|:---|:---|
| `filters: []` 是级联起始标志 | 空数组 = 根节点，不加过滤条件查全量 |
| `param` 指向**关联表**的列 | 表示"用关联表中这个字段做过滤" |
| `valueStr.id` 指向**当前表单**的列 | 表示"用当前表单中这个字段的值作为过滤依据" |
| 级联不依赖 selectingColumns | 前端自动从查询结果中提取对应字段的去重值 |

---

## 六、后端模型定义

```csharp
public class RobotFilter
{
    /// <summary>关联表中被筛选字段的类型</summary>
    public string Type { get; set; }

    /// <summary>关联表中被筛选字段的 model</summary>
    public string Param { get; set; }

    /// <summary>过滤条件</summary>
    public string Condition { get; set; }

    /// <summary>运行时占位</summary>
    public object Value { get; set; }

    /// <summary>
    /// 引用当前表单字段作为过滤源
    /// 格式: {"id":"当前字段model","label":"当前字段名","type":"字段类型"}
    /// </summary>
    public string ValueStr { get; set; }
}
```

---

*文档版本：v2.1 | 整理日期：2026-07-03 | 基础数据来源机制详见同目录下的 relation-table-mechanism.md*