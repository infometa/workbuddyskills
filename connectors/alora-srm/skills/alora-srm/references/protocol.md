# 全局参数协议

以下规则适用于所有业务操作，优先级最高。

---

## ⛔ 命令构造禁令

### 零容忍：禁止猜参数

**遇到任何工具调用，必须先查 `yidea_tools` 中该工具的 `inputSchema`，再构造参数。**

- ❌ 不查 schema，靠记忆/推测写参数 → **必须禁止**
- ❌ API 报错后不查 schema，直接推断

**禁止在执行 HTTP 调用脚本时附加任何管道命令（如 `| jq .`、`| python3 -m json.tool`、`| grep` 等）。**

- `yidea-http.js` 返回的已经是结构化 JSON，无需再格式化。
- 附加管道命令可能导致输出阻塞或命令超时失败。

---

## 🔥 核心规则（每次操作前必读）

### 规则 1：参数值必须转 String

所有 API 参数值（`value`, `subId`, `formId` 等）**必须为字符串**，禁止数字/布尔。

- ✅ `"value": "22"`
- ❌ `"value": 22`

### 规则 2：必须先查 Schema，禁止猜参数

**每次调用工具前，必须先查真实 inputSchema**。直接推测参数名会导致调用失败。

**正确做法**（必须执行）：

- 登录成功后，上下文中的 `yidea_tools` 数组已包含所有工具的 `name`、`description` 和 `inputSchema`
- 定位目标工具的 `inputSchema.properties`，确认字段名、嵌套层级、枚举值后再构造参数

**示例**：`crud_yidea_table_search` 的顶层参数是一个包裹的 `request` 对象，不是 `tableId`、`take`。

- ❌ 猜测：`{ tableId: "...", take: 5 }` → 失败
- ✅ 按 schema：`{ request: { formId: "...", pageIndex: "1", take: "5" } }` → 成功

### 规则 3（新增）：`items` 搜索条件的正确格式

`crud_yidea_table_search` 的 `items` 参数用于过滤查询结果，**关键陷阱**：

```json
// ✅ 正确：values 是数组，value 是字符串
"items": [{
  "name": "select_xxx",          // 要过滤的字段 model
  "values": ["未开始"],           // ⚠ 数组，不是字符串！
  "methodType": "Equal"          // 必须指定：Equal / Contains 等
}]

// ❌ 错误：value 是字符串不是数组
"items": [{
  "name": "select_xxx",
  "value": "未开始"    // 报 500：Unexpected token 'A', "An error o"...
}]
```

完整示例：
```json
{
  "request": {
    "formId": "d9db0f48-...",
    "items": [{
      "name": "select_1720408479877_4e37",
      "values": ["未开始"],
      "methodType": "Equal"
    }],
    "pageIndex": 1,
    "take": 10,
    "returnColumns": []
  }
}
```

> 此规则记不住易出错，**每次构建 `items` 搜索条件时，务必回头核对此节**。

### 规则 4：displayForAI 字段过滤原则

每个表单字段的 `crud_get_yidea_table_def` 返回结果中，`options.displayForAI` 控制该字段是否对 AI 操作可见。

**强制性约束：**

| 操作阶段 | 行为规则 |
| :------- | :------- |
| **展示表单定义**（Step 2） | 仅展示 `options.displayForAI === true` 的字段，过滤掉 `false` 或缺失的字段 |
| **新增/修改数据**（Step 3） | 构造 `items` / `rowItems` 时，仅提交 `displayForAI === true` 的字段 |
| **查询/展示结果** | 仅在 `returnColumns` 中指定 `displayForAI === true` 的字段 model |

> ⚠️ **禁止**：不要将 `displayForAI: false` 的字段展示给用户或在增改接口中提交其值。
> ⚠️ **注意**：子表单 (`table` 类型) 的 `tableColumns` 中每个字段也各自携带 `options.displayForAI`，同样需要逐列检查。

---

### 规则 5：displayForAI 速查示例

以下为 `crud_get_yidea_table_def` 返回中字段的典型结构：

```json
{
  "type": "input",
  "name": "询价项目名称",
  "model": "input_1699239453512",
  "options": {
    "displayForAI": true,   // ← 关键标记
    "required": true
  }
}
```

过滤逻辑：
- `displayForAI: true` ✅ → 展示 & 可操作
- `displayForAI: false` ❌ → 隐藏 & 不提交
- `displayForAI` 缺失（`undefined`）❌ → 等同于 false，过滤

---

### 规则 6：字段前缀识别

| 前缀                | 字段类别   | 处理方法                              |
| :------------------ | :--------- | :------------------------------------ |
| `employeeSelect_`   | 员工类     | 先调 `crud_get_yidea_employee_list`        |
| `companySelect_`    | 公司类     | 先调 `crud_get_yidea_company_list`         |
| `departmentSelect_` | 部门类     | 先调 `crud_get_yidea_department_list`      |
| `query_`            | 关联查询类 | 见 `query-field.md`，**必须自动完成** |

### 规则 7：`currentUser: true` 字段取值确认

当字段的 `options.currentUser === true` 时（见于 `employeeSelect_`、`departmentSelect_`、`companySelect_` 类型的字段），AI 必须调用 `crud_get_current_user` 接口获取当前登录用户的数据，并将实际值填入提交参数。

**强制性行为：**

1. **必须调用 `crud_get_current_user` 接口**确认当前用户信息，不得跳过此步骤
2. 展示给客户确认：将接口返回的 `employeeName`（员工姓名）告知客户并确认
3. 客户确认后，提交时的取值规则如下：

| 类型 | 取值规则 | 示例值 |
|:---|:---|:---|
| `employeeSelect_` + `currentUser: true` | 传 `employeeNo`（工号字符串） | `"01"` |
| `departmentSelect_` + `currentUser: true` | **传查到的部门编码**，不应传空字符串 | `"A0012"` |
| `companySelect_` + `currentUser: true` | **传查到的公司编码**，不应传空字符串 | `"01"` |

> ⚠️ **禁止**：
> - 不查询 `crud_get_current_user` 就直接猜测或跳过该字段
> - 客户说"当前用户"就直接跳过查询，仍需调用 `crud_get_current_user` 确认信息后再提交
> - `departmentSelect_` / `companySelect_` 传空字符串 `""`，期望后端自动填充（后端不会自动填充，且会导致提交后字段值为空 `{}`）

## 通用 MCP 调用方式

所有 MCP 工具调用统一使用 **HTTP 直连**，通过 `yidea-http.js` 脚本：

```bash
node yidea-http.js <工具名> '<JSON参数>'
```

示例：
```bash
# 获取表单列表
node yidea-http.js crud_get_yidea_func_list '{ "menuArray": "招采管理" }'

# 获取表单定义
node yidea-http.js crud_get_yidea_table_def '{ "tableId": "xxx" }'

# 查询数据
node yidea-http.js crud_yidea_table_search '{ "request": { "formId": "xxx", "pageIndex": "1", "take": "10" } }'

# 新增数据
node yidea-http.js crud_yidea_table_add '{ "request": { "formId": "xxx", "items": [...] } }'
```

> **脚本位置**：`references/yidea-http.js`（相对 skill 目录）

---

## 完整参数提交规则

所有调用 `crud_yidea_table_add`、`crud_yidea_table_update` 以及涉及子表单操作时，参数值必须全部为字符串类型。

## InputSchema 强制检查（速查指南）

1. 从上下文的 `yidea_tools` 数组中定位目标工具的 `inputSchema.properties`
2. 确认字段名、嵌套层级（如 `request.formId`）、枚举值
3. 基于 schema 构造 JSON 参数，严禁猜测

## 字段前缀识别规则（详细版）

遇到前缀字段时严禁盲目猜测值，必须先查询再填写。

---

**优先级**：本文内容及 `query-field.md` 中的规则优先级最高，与其他文件冲突时以本文为准。