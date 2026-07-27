# 金数据表格 MCP 示例手册

收录典型场景的 prompt 模板和预期结果，帮助用户快速上手数据表格操作。

---

## 一、建表

### 1.1 客户跟进表

**Prompt：**

> 帮我建一张"客户跟进表"，列：
> - 客户名称（文本）
> - 联系电话（手机号）
> - 跟进状态（单选：待跟进 / 跟进中 / 已成交 / 已流失）
> - 下次跟进日期（日期）
> - 备注（文本）

**AI 调用**：`create_table`，`fields`：

```json
[
  {"type": "TextArea", "label": "客户名称"},
  {"type": "MobileField", "label": "联系电话"},
  {"type": "RadioButton", "label": "跟进状态", "choices": [
    {"value": "待跟进"}, {"value": "跟进中"}, {"value": "已成交"}, {"value": "已流失"}
  ]},
  {"type": "DateTimeField", "label": "下次跟进日期", "precision": "day"},
  {"type": "TextArea", "label": "备注"}
]
```

**预期输出**：返回表结构，含各列 `api_code`（如 `field_1`…）与「跟进状态」选项的 `choices[].api_code`。

### 1.2 带公式列的项目管理表

**Prompt：**

> 建一张"项目预算表"，列：项目名称、预算金额（数字）、已用金额（数字），再加一列公式列「已用占比」= 已用金额 / 预算金额。

**AI 调用**：`create_table`。公式列引用同一请求里新增的列时，给被引用列加 `cid`，公式用 `<gd-field data-cid="…">` 引用（此时新列还没有 `api_code`）：

```json
[
  {"type": "TextArea", "label": "项目名称"},
  {"type": "NumberField", "label": "预算金额", "cid": "c_budget"},
  {"type": "NumberField", "label": "已用金额", "cid": "c_used"},
  {"type": "FormulaField", "label": "已用占比",
   "formula_display": "<gd-field data-cid=\"c_used\"></gd-field> / <gd-field data-cid=\"c_budget\"></gd-field>"}
]
```

> ⚠️ 公式列只读，不能写入 entry；它的值随预算 / 已用列自动计算。

---

## 二、改列

### 2.1 给已有表加列

**Prompt：**

> 给"项目预算表"加一列「负责人」（文本）和一列「是否验收」（勾选）。

**AI 调用**：`get_table`（确认表 token 与现有列）→ `edit_table`：

```json
{
  "table_token": "<表 token>",
  "fields": {
    "add": [
      {"type": "TextArea", "label": "负责人"},
      {"type": "BooleanField", "label": "是否验收"}
    ]
  }
}
```

### 2.2 改选项文案（保留 api_code）

**Prompt：**

> 把"客户跟进表"里跟进状态的「已流失」改名成「暂缓」。

**AI 调用**：`get_table` 拿「跟进状态」列及「已流失」选项的 `api_code` → `edit_table` 用 `fields.update_choices` 的 update（**保留 api_code**）改名，而不是 remove+add。

> ⚠️ 用 remove+add 会换 api_code，历史行里引用旧选项的数据会失联。

### 2.3 删列（先确认数据）

**Prompt：**

> 把"客户跟进表"的备注列删掉。

**AI 流程**：`get_table` 拿「备注」列 `api_code` → 告知用户"删除该列会永久清除已有行里这一列的数据，不可恢复" → 用户确认后 `edit_table`，`fields.remove: ["<备注 api_code>"]`。

---

## 三、行数据

### 3.1 条件查询 + 投影

**Prompt：**

> 把"客户跟进表"里跟进状态=待跟进、且下次跟进日期在本周的行列出来，只要客户名称、联系电话、下次跟进日期。

**AI 调用**：
1. `get_table`：记下「跟进状态」列 `api_code`（如 `field_status`）、"待跟进"选项 `api_code`（如 `status_pending`）、「下次跟进日期」列 `api_code`（如 `field_next`）
2. `list_entries`（`form_token` 填表 token）用 filters 下推：
   ```
   filters=[
     {"field": "field_status", "operator": "eq", "value": "status_pending"},
     {"field": "field_next", "operator": "between", "value": ["<本周一 ISO>", "<本周日 ISO>"]}
   ]
   ```
   `next` 翻页拿全部命中
3. 对话侧投影三列，手机号脱敏，Markdown 表格展示 + 总数

> ⚠️ 选项列 value 传**选项 api_code** 不是 label；`list_entries` 不支持任意列排序，倒序 / 取前 N 在对话侧做。

### 3.2 补录一行

**Prompt：**

> 在"客户跟进表"加一行：客户名称 A 科技、电话 13900008888、状态 跟进中、下次跟进 2026-08-01。

**AI 调用**：`get_table` 拿列 api_code 和"跟进中"选项 api_code → `create_entry`：

```json
{
  "form_token": "<表 token>",
  "entry": {
    "field_name": "A 科技",
    "field_mobile": "13900008888",
    "field_status": "status_following",
    "field_next": "2026-08-01"
  }
}
```

> ⚠️ entry 的键是列 `api_code`；选项列 value 是选项 `api_code`；手机号要真实号段，测试号段（13800138000）会被拒。

### 3.3 批量导入行

**Prompt：**

> 把这 50 个客户导入"客户跟进表"（贴了一份名单）。

**AI 流程**：`get_table` 拿列 api_code → 把每行整理成 `{api_code: value}` → `create_entries`（一次 ≤200）→ 读 `created_count` + `errors`，向用户汇总成功 / 失败（按 `errors` 下标只补失败行，不整批重发）。

### 3.4 批量更新行

**Prompt：**

> 把"客户跟进表"里下次跟进日期已经过期、状态还是「跟进中」的行，状态都改成「待跟进」。

**AI 流程**：
1. `get_table` 拿「跟进状态」「下次跟进日期」列 api_code 和目标选项 api_code
2. `list_entries` + filters 拉命中集：
   ```
   filters=[
     {"field": "field_status", "operator": "eq", "value": "status_following"},
     {"field": "field_next", "operator": "lt", "value": "<今天 ISO>"}
   ]
   ```
3. 展示前 10 行 + 总数，向用户确认
4. 确认后 `patch_entries` 一次提交（每行 `{serial_number, entry: {field_status: "status_pending"}}`，每批 ≤200）
5. 读 `updated_count` + `failed_rows`，汇总成功 / 失败

### 3.5 批量删除行（高风险）

**Prompt：**

> 删掉"客户跟进表"里状态是「已流失」的所有行。

**AI 流程**：`get_table` → `list_entries` + filters 命中，拿全部 `serial_number` → **必须**得到用户显式"确认删除" → 逐行循环 `delete_entry`（无批量版）→ 每 20 行汇报进度、结束汇总。

---

## 四、Prompt 模板速查

| 场景 | 模板 |
| --- | --- |
| 建数据表 | `帮我建一张"<表名>"，列：<列列表>` |
| 加列 | `给"<表名>"加一列"<列名>"（<类型>）` |
| 改选项 | `把"<表名>"里 <列> 的"<旧选项>"改名成"<新选项>"` |
| 查行 | `查"<表名>"里 <条件> 的行，只要<列>` |
| 改行 | `把"<表名>"里 <条件> 的行，<列>都改成"<值>"` |
| 导入行 | `把这些数据导入"<表名>"` |
| 删行 | `删掉"<表名>"里 <条件> 的行` |
