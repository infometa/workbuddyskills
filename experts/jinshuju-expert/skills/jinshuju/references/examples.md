# 金数据 MCP 示例手册

收录 10 个典型场景的 prompt 模板和预期结果，帮助用户快速上手。

---

## 一、表单搭建

### 1.1 活动报名表

**Prompt：**

> 帮我建一个"2026 春季发布会报名表"，字段：
> - 姓名（必填）
> - 手机号（必填、校验）
> - 公司
> - 职位
> - 参会城市（下拉：北京/上海/深圳/线上）
> - 感兴趣议题（多选：产品发布/技术架构/客户案例/圆桌讨论）
> - 备注
>
> 主题用蓝色简洁风格，创建完成给我链接。

**AI 调用**：`create_form`（字段类型用 `NameField` / `MobileField` / `TextField` / `DropDown` / `CheckBox` / `TextArea`）→ `edit_theme`

**预期输出**：

```
✅ 已创建表单"2026 春季发布会报名表"
链接：https://jinshuju.net/f/XXXXXX
字段（7）：姓名*、手机号*（校验）、公司、职位、参会城市、感兴趣议题、备注
主题：蓝色简洁
```

### 1.2 问卷（NPS 调研）

**Prompt：**

> 建一份"产品 NPS 调研"，第一题：您向朋友推荐我们的可能性（0-10 打分），第二题：主要原因（多行文本），第三题：邮箱（选填）。

**AI 调用**：`create_form`。NPS 题直接用 `NpsField`（可加 `minimum_ratings_display_text="非常不可能"` / `maximum_ratings_display_text="非常可能"`），原因用 `TextArea`，邮箱用 `EmailField`。也可以用 `RatingField` + `rating_max=10` 模拟 NPS 打分。

> 💡 矩阵类字段（`LikertField` / `MatrixField` / `MatrixScaleField`）现已支持创建，每种字段的完整 schema 和示例见 [`tools.md`](tools.md) 的 create_form 章节。

### 1.3 复制已有表单并改造

**Prompt：**

> 把"2025 年会报名表"复制一份，改名成"2026 年会报名表"，去掉签到字段，新增"是否带家属"（是/否）。

**AI 调用**：`list_forms`（name 正则匹配） → `copy_form` → `get_form`（拿到旧字段的 api_code，确认"签到"字段的 api_code 再 remove） → `edit_form`（`fields: { remove: [签到字段.api_code], add: [{type:"RadioButton", label:"是否带家属", choices:[{value:"是"},{value:"否"}]}] }`）

> ⚠️ `fields.remove` 传的是 api_code 数组，不是 label。
>
> ⚠️ 这里删的是刚复制出来的新表（没有数据），可直接删。但若是删一张**已有提交数据**的表单的字段 / 选项，必须先用 `check_field_data` 查，`has_data=true` 时把影响告诉用户、确认后再删。

---

## 二、数据查询

### 2.1 条件筛选 + 排序 + 投影

**Prompt：**

> 查"客户登记表"里本周新增且来自上海的记录，按时间倒序前 20 条，只要姓名、手机号、公司。

**AI 调用**：
1. `get_form`：拿字段结构，记下"参会城市"字段的 `api_code`（如 `field_city`）和"上海"选项的 `choices[].api_code`（如 `city_sh`）
2. `list_entries` **用 filters 把过滤条件下推到数据库**，省掉拉全量再本地过滤：
   ```
   filters=[
     {"field": "field_city", "operator": "eq", "value": "city_sh"},
     {"field": "created_at", "operator": "gte", "value": "<本周起始 ISO 时间>"}
   ]
   ```
   服务端按 `created_at` 升序返回，单次 50 条，用 `next` 翻页拿全部命中
3. 在对话侧只做剩下的：倒序（filters 不支持任意字段倒序）、取前 20、投影姓名 / 手机号 / 公司

**预期输出**：Markdown 表格 + 手机号默认脱敏 + 总匹配数。

> ⚠️ 关键约束：
> - 选项字段的 value 传**选项 api_code**（`city_sh`），不是 label（`"上海"`）
> - `filters` 多条件是 **AND** 关系；operator 跟字段类型不匹配会 400 拒并列出可用 operator
> - `list_entries` 不支持任意字段排序——倒序、取前 N 仍需本地做
> - `like` 是子串匹配（不区分大小写），不是 SQL 通配符——传 `"张"` 就行，不要传 `"张%"`

### 2.2 汇总统计

**Prompt：**

> 统计"春季发布会报名表"里各参会城市的报名人数，按人数倒序。

**AI 调用**：
1. `get_form` 拿"参会城市"字段及其 `choices[]`（存 api_code → label 的映射用于展示）
2. `list_entries` 用 filters 把时间范围下推（如果只统计某段时间）：
   ```
   filters=[{"field": "created_at", "operator": "gte", "value": "<起始时间>"}]
   ```
   翻页拉回需要的范围
3. 对话侧按城市字段的 api_code 分组计数，输出时把 api_code 映射回 label

（MCP 没有 group by / count 类聚合接口，聚合必须在对话侧做；但**前置条件能用 filters 收缩就用**——把数据量在数据库这一层先打下来再算）

### 2.3 查看单条详情

**Prompt：**

> 给我"订单登记表"里订单号 ORD-20260417-001 的完整信息。

**AI 调用**：
1. `get_form` 拿"订单号"字段的 `api_code`（如 `field_order_no`）
2. `list_entries` **直接用 filters 命中那一条**：
   ```
   filters=[{"field": "field_order_no", "operator": "eq", "value": "ORD-20260417-001"}]
   ```
   返回数据（通常 0 或 1 条）
3. 拿到 `serial_number` 后，调 `get_entry(form_token, serial_number)` 拿完整详情（如果 list_entries 返回的 api_value 已经够用，可以省略这步）

> ⚠️ `get_entry` / `update_entry` / `delete_entry` 都靠 **`serial_number`**（整数）定位，不是 token、不是 id。

---

## 三、数据修改

### 3.1 批量更新状态

**Prompt：**

> 把"报名表"里手机号以 138 开头、跟进状态还不是"已联系"的记录，跟进状态都改成"已联系"。

**AI 流程**：
1. `get_form` 拿三样东西：
   - 手机号字段的 `api_code`（如 `field_mobile`）
   - 跟进状态字段的 `api_code`（如 `field_status`）
   - "已联系"选项的 `choices[].api_code`（如 `status_contacted`）
2. `list_entries` **用 filters 直接拉出命中集**，避免拉全量：
   ```
   filters=[
     {"field": "field_mobile", "operator": "like", "value": "138"},
     {"field": "field_status", "operator": "ne", "value": "status_contacted"}
   ]
   ```
   翻页拿全部命中（`like` 不需要 SQL 通配符；`ne "status_contacted"` 跳过已处理记录避免无效写入）
3. 展示前 10 条 + 总数
4. 向用户确认："共 N 条，确认都改为'已联系'？"
5. 用户确认后**逐条循环**：`update_entry(form_token, serial_number, entry={field_status: "status_contacted"}, is_put=false)`
   - ⚠️ 保持 `is_put=false`（默认 PATCH），**绝不传 `is_put=true`**，否则会把其他字段全部清空
   - ⚠️ 选项字段 value 用**选项 api_code**（`"status_contacted"`），不是 label（`"已联系"`）
6. 每 20 条汇报一次进度，结束时汇总成功 / 失败条数

### 3.2 补录数据

**Prompt：**

> 在"客户登记表"里加一条：姓名 王\*\*、手机号 139\*\*\*\*8888、公司 C 集团、来源"线下展会"。

**AI 流程**：
1. `get_form` 拿各字段 api_code 和"来源"字段中"线下展会"选项的 api_code
2. `create_entry(form_token, entry={field_name: "王**", field_mobile: "13900008888", field_company: "C 集团", field_source: "source_offline"})`
   - ⚠️ entry 的 key 是 **api_code**（不是中文 label），选项字段 value 是**选项 api_code**
   - ⚠️ 用户给的手机号如果是脱敏的星号或保留测试号段（如 13800138000），要让用户给真实号码，否则被号段正则拒

### 3.3 批量删除（高风险）

**Prompt：**

> 删掉"测试表单"里所有备注字段包含"test"的记录。

**AI 流程**：
1. `get_form` 拿"备注"字段的 api_code（如 `field_notes`）
2. `list_entries` **用 filters 直接命中**：
   ```
   filters=[{"field": "field_notes", "operator": "like", "value": "test"}]
   ```
   翻页拿全部命中的 `serial_number`
3. **必须**得到用户显式"确认删除"回复
4. >50 条时分批并再次确认
5. **逐条循环**：`delete_entry(form_token, serial_number)`
6. 每 20 条汇报一次进度，结束时汇总成功 / 失败条数 + 回执

---

## 四、串联型任务

### 4.1 一次性完成"建表单 + 拉数据 + 出摘要"

**Prompt：**

> 复制"2025 年会报名表"为"2026 年会报名表"，去掉签到字段。同时给我 2025 年会报名表的数据摘要，按部门分组统计人数。

**AI 调用**：
1. `list_forms`（`name` 模糊匹配到 2025 年会报名表）
2. `copy_form`（name="2026 年会报名表"）
3. `get_form`（旧表）拿到"签到"和"部门"字段的 api_code
4. `edit_form`（新表，`fields={remove: [签到.api_code]}`）
5. `list_entries`（旧表）—— 如果有时间窗约束，用 `filters` 把范围下推；翻页拉回需要分组的记录
6. 对话侧按"部门"api_code 分组聚合、映射回 label 展示

（`list_entries` 不支持 group by，聚合必须在本地做；但**前置条件能用 filters 收窄就用**）

**价值**：一条 prompt 搞定**原来需要 5-8 步操作的流程**，且中间结果可以在对话里随时确认。

### 4.2 AI 生成表单头图

**Prompt：**

> 给"春季发布会报名表"换个头图，用蓝紫色科技感的主题图。

**AI 调用**：`edit_theme(form_token, generate_header_image={prompt: "蓝紫色科技感主题，适合发布会报名表的横幅头图"})`

Yoshi AI 会按 prompt（或自动从表单标题 / 描述推断）生成一张头图并绑到表单 header 上。也支持直接传 `header.header_image_url`（外链图片）——**不建议**传 `header_image_base64`，LLM 容易截断导致图片损坏。

### 4.3 一键配置表单状态 / 提交限制 / 访问密码

**Prompt：**

> "2026 春季发布会报名表"先关一下提交，等到 5 月 1 号 9 点再开放，5 月 31 号晚 6 点截止；每个 IP 一天最多提交 3 次；加访问密码 `spring2026`。

**AI 调用**：单次 `edit_form` 一次性写入 `setting` 即可，无需多次调用：

```json
{
  "setting": {
    "by_time_range_close_rule": {
      "start_time": "2026-05-01T09:00:00+08:00",
      "end_time": "2026-05-31T18:00:00+08:00"
    },
    "fill_frequency": {
      "fill_type": "repeatable",
      "condition": "by_ip",
      "cycle_period": "every_day",
      "limited_time": 3
    },
    "password_required": true,
    "access_password": "spring2026"
  }
}
```

> ⚠️ `manually_close_rule` / `by_time_range_close_rule` / `by_entries_close_rule` 三类关闭规则**互斥**：写任意一类会清掉其他规则。但发 `manually_close_rule: { closed: false }` 而当前并无手动关闭规则时，服务端会跳过——不会误清已有的定时关闭。
>
> ⚠️ 启用密码时**必须**同时传 `access_password`（或表单已有密码），否则 400 拒绝；要在保留密码字段的同时关闭密码闸，发 `password_required: false`，服务端会自动清空 `access_password`。
>
> ⚠️ `fill_frequency.condition=by_fields` 时必须同时给 `limited_field_api_codes`，否则被拒。

### 4.4 把表单整理进 / 移出文件夹

**Prompt：**

> 把刚建的"春季发布会报名表"放到"市场活动" 文件夹下。

**AI 调用**：

1. `list_folders()` 拿到所有文件夹（name + token）
2. 在对话侧匹配"市场活动" → 拿到对应 `folder_token`
3. `move_form(form_token, folder_token=<上一步的 token>)`

**Prompt（移回根目录）：**

> 把"产品 NPS 调研"从文件夹里拿出来。

**AI 调用**：`move_form(form_token)`（省略 `folder_token`，或显式传空字符串 `folder_token=""`）—— 表单会回到根目录。

---

## 五、Prompt 模板速查

| 场景 | 模板 |
| --- | --- |
| 创建表单 | `帮我建一个"<名称>"，字段：<字段列表>，主题<风格>` |
| 列出数据 | `查"<表单名>"里 <条件>，按<字段>倒序前 <N> 条，只要<字段>` |
| 修改数据 | `把"<表单名>"里 <条件> 的记录，<字段>都改成 "<值>"` |
| 复制改造 | `复制"<A>"成"<B>"，<修改点>` |
| 生成头图 | `给"<表单名>"换个头图，<风格描述>` |
| 移动表单 | `把"<表单名>"放到"<文件夹>"` / `把"<表单名>"从文件夹里拿出来` |
| 配置表单设置 | `<表单名> 的提交限制 / 关闭规则 / 访问密码 / Webhook 改成 ...` |
