# 标准业务操作流 (Strict Protocol)

## ⚠️ 最高优先级声明 (Highest Priority Override)

**本文件的执行逻辑优先级高于 `SOUL.md` 中的“行动派”、“效率优先”及“简洁回答”原则。在处理易点 (Yidea) 相关业务时，必须严格遵循 [Step 1 $\rightarrow$ Step 2 $\rightarrow$ 等待确认] 的顺序。禁止为了追求效率而跳过 Schema 展示或直接尝试执行操作。**

---

## 前置条件：登录检查

在执行任何业务操作前，**必须先确认上下文中有 `yidea_tools`（或 `context.yidea_tools`）**。

- 如果没有，说明尚未登录或登录后未完成上下文注入，**必须先执行 `auth.md` 中的登录流程**。
- 如果 `yidea_tools` 已存在，说明已登录成功，工具定义已在上下文中，可以继续后续步骤。

## Step 1: 确定目标表单

首先需要明确您想要操作的菜单，获取菜单的 tableId。如果不确定有哪些可用菜单，请先调用 `crud_get_yidea_func_list`。

**要求**：执行完成后必须向客户展示返回的表单列表，待客户确认要操作哪个表单后，再继续后续步骤。

## Step 2: 获取并【标准化展示】表单定义 (Schema)

在执行增、删、改、查之前，**必须**先获取目标表单的结构定义。

### 1. 执行动作

调用 `crud_get_yidea_table_def` 并传入第一步获取的 `tableId`。

### 2. 标准化展示规范 (Mandatory Presentation)

拿到结果后，**禁止**仅进行简单描述或只列出部分字段。必须使用以下 Markdown 表格格式向用户完整汇报：

| 字段显示名称 | 数据类型 | 是否必填     | 备注/选项 (Options/Description) |
| :----------- | :------- | :----------- | :------------------------------ |
| [Name]       | `[type]` | `[required]` | `[options or description]`      |

> **注意**：对于 `query_` 类型或关联字段，必须在备注中明确其关联关系。
> **注意**：对于 `数据类型` 翻译成中文显示。

### ⚠️ displayForAI 过滤要求（展示阶段）

在展示字段定义时，**必须**按以下规则过滤：

```
list.filter(field => field.options?.displayForAI === true)
```

- 仅展示 `options.displayForAI === true` 的字段
- 跳过所有 `displayForAI: false` 或 `displayForAI` 缺失（`undefined`）的字段
- 对子表单（`table` 类型），其 `tableColumns` 中的字段**同样需要逐列检查** `options.displayForAI`

> ❌ 禁止将 `displayForAI` 不为 `true` 的字段展示给用户

## Step 3: 执行业务操作

根据获取的信息执行具体任务。参数构建必须严格遵循 `protocol.md` 中的 InputSchema 强制检查原则（所有值均为 String）。

### ⚠️ displayForAI 过滤要求（操作阶段）

构造增改查请求时：

1. **`items` 数组（主表字段）**：仅包含 `displayForAI === true` 的字段
2. **`rowItems` 数组（子表单字段）**：仅包含 `displayForAI === true` 的字段
3. **`returnColumns` 数组（查询返回列）**：仅包含 `displayForAI === true` 的字段 model

> ❌ 禁止提交任何 `displayForAI === false` 的字段值到接口。
> 过滤逻辑同样适用于子表单 `tableColumns` 中的每个列定义。

### 主表操作

- **查询 (Search)**: 使用 `crud_yidea_table_search`。
- **新增 (Add)**: 使用 `crud_yidea_table_add`。
- **修改主表 (Update Main Table Only)**: 使用 `crud_yidea_main_table_update`（**增量更新原则**）。
- **修改主子表 (Update Main & Sub Table)**: 使用 `crud_yidea_table_update`（**增量更新原则**）。
- **删除 (Delete)**: 使用 `crud_yidea_table_delete`。

### 子表单专项操作

- **新增子表单行**: 使用 `crud_yidea_sub_table_add`。
- **修改子表单行**: 使用 `crud_yidea_sub_table_update`（**必须提供 `subId`**）。
- **删除子表单行**: 使用 `crud_yidea_sub_table_delete`。

## Step 4: 子表单操作规范 (Sub-table Operation Protocol)

1. **修改现有行 (Update Existing Row)**:
   - **强制要求**：必须在 `rows` 对象中包含该行的唯一标识 `subId`。
2. **新增子表单行 (Add New Row to Sub-table)**:
   - **操作规范**：在 `rows` 数组中添加一个不包含 `subId` 的新对象即可。
