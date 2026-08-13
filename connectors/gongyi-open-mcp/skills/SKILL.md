---
name: gongyi-open-mcp-skill
description: 腾讯公益机构服务平台连接器技能 - 通过 MCP 查询当前机构的用户、机构信息、成员、项目、进展、财务披露与数据字典等机构侧业务数据
version: "1.0.0"
author: "Tencent Charity"
---

# 腾讯公益机构服务平台连接器 Skill

本 Skill 指导 AI 如何使用「腾讯公益机构服务平台」连接器（`gongyi-open-mcp`）提供的 MCP 工具。
连接器采用**标准 MCP OAuth 授权**：用户在WorkBuddy 中点击「连接」后，浏览器会自动打开公益机构平台的
授权页完成登录授权，WorkBuddy 拿到访问令牌后自动注入后续 MCP 请求。返回数据限定在授权用户
所属机构与用户的权限范围内。

## 鉴权说明

- **授权方式**：标准 OAuth 2.1（授权码 + PKCE）。用户在连接器上点击「连接」→ WorkBuddy 通过 MCP Server 的元数据接口自动发现授权页地址并打开浏览器 → 登录并确认授权 → WorkBuddy 自动获取并保存访问令牌，无需用户手动复制粘贴任何 Token。
- 访问令牌代表某个机构下的某个用户身份，由 WorkBuddy 端侧安全存储，并在令牌过期时自动通过 refresh_token 续期，整个过程对用户透明。
- **第 1 层的机构相关工具均无需传机构编号**：授权令牌会在鉴权时自动绑定当前授权用户所属机构。
- 若返回鉴权失败（令牌失效 / 已吊销 / 授权被撤销），WorkBuddy 会自动引导用户重新走授权流程；AI 只需如实提示"授权已失效，请在连接器上重新连接授权"即可。

## 工具调用依赖分层

工具按调用依赖关系分为三层 + 一个辅助查询工具。**同层工具可并行调用**，跨层需先拿到上层返回的标识（`project_no` / `project_id` / `id` / `finance_no`）。

```
第 1 层（零依赖，Token 自动绑定机构，可全部并行）
├── get_user_and_org_info       机构基础身份
├── get_org_detail              机构详细画像（注册地/信用代码/年检/评估/年报/人员规模）
├── get_org_member_list         机构成员列表
└── get_project_list            项目列表（支持按领域编码筛选）

第 2 层（依赖 project_no / project_id）
├── get_project_detail          项目详情（背景/预算/执行地点/受益对象）
├── get_process_list            项目进展列表
└── get_project_financial_list  财务披露列表

第 3 层（依赖第 2 层返回的 id）
├── get_process_detail          单条进展全文详情
└── get_financial_info          单条财披详情（收支明细）

辅助工具（编码解码）
└── get_dictionary              数据字典：编码 → 中文名称映射

反馈提交工具组（跨工具编排：需先拿机构信息 + 反馈分类，再创建反馈单）
├── get_feedback_levels         获取反馈分类树（叶子节点用于 create_feedback 的 level_id/level_name）
└── create_feedback             创建反馈单（依赖 get_user_and_org_info 的 org_no/org_name + get_feedback_levels 的叶子分类）

内置工具（调试用）
└── get_mcp_token               返回当前请求鉴权通过的 Token 原文
```

---

## 第 1 层工具（零依赖）

### get_user_and_org_info - 获取当前用户与机构信息

获取当前 Token 对应的登录用户基本信息及其所属机构信息。**无需入参。**

**参数说明**：无

**返回字段**：

| 字段 | 说明 |
|------|------|
| `name` | 当前登录用户姓名 |
| `account_id` | 当前用户账号 ID |
| `org_no` | 所属机构编号 |
| `org_name` | 所属机构名称 |
| `type_of_organization` | 机构类型（数字枚举，见下方枚举表） |
| `affili_pub_org` | 挂靠公募机构编号（可能为空） |
| `affili_pub_org_name` | 挂靠公募机构名称（可能为空） |

**使用示例**：
- 用户问"我是谁""当前登录的是哪个机构" → 调用 `get_user_and_org_info`

### get_org_detail - 获取机构详细信息

获取当前机构的完整画像，是 `get_user_and_org_info` 的补充。**无需入参。**

**参数说明**：无

**返回字段**（分组返回）：

| 分组.字段 | 说明 |
|------|------|
| `basics.province` / `city` / `area` / `address` | 注册地行政区划编码与详细地址（province/city/area 为数字编码，需对照行政区划表） |
| `basics.establishment_date` | 成立时间 |
| `basics.phone` / `email` | 联系电话 / 邮箱 |
| `detailed.uscc` | 统一社会信用代码（18 位） |
| `detailed.competent_unit` | 主管单位 |
| `detailed.business_scope` | 业务范围 |
| `detailed.corporation_name` | 法人姓名 |
| `detailed.general_name` / `job_title` | 负责人姓名 / 职务 |
| `detailed.is_qualified` | 年检/合格状态（0 不合格，1 合格） |
| `detailed.qualified_start_date` / `qualified_end_date` | 年检有效期 |
| `detailed.evaluation_type` / `evaluation_level` | 评估类型 / 等级（**编码**，需经 `get_dictionary` 解码，见枚举映射） |
| `detailed.evaluation_level_validity_date` | 评估等级有效期 |
| `detailed.total_number` / `fulltime_number` / `parttime_number` / `volunteers_number` | 人员规模：总人数 / 专职 / 兼职 / 志愿者 |
| `annualReport[]` | 年报数组，每项含 `year`、实施报告/财务报告文件名与 PDF 链接（按年份降序） |

**使用示例**：
- 用户问"机构注册在哪里""统一社会信用代码是多少""机构评估等级""近几年年报" → 调用 `get_org_detail`
- 涉及 `evaluation_type` / `evaluation_level` 时，需再调 `get_dictionary` 解码为中文

### get_org_member_list - 获取机构成员列表

获取当前机构的成员明细（姓名、岗位、在职状态等）。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `page_index` | integer | 否 | 页码，从 1 开始，默认 1 |
| `page_size` | integer | 否 | 每页条数，建议 20 |

**使用示例**：
- 用户问"机构有哪些成员""专职人员名单" → 调用 `get_org_member_list`

### get_project_list - 获取项目列表

获取当前机构名下的项目列表，自动绑定到当前登录机构，支持按领域编码服务端筛选。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `type` | integer | 是 | 项目类型，通常填 `1` |
| `page_index` | integer | 否 | 页码，默认 1 |
| `page_size` | integer | 否 | 每页条数，建议 20 |
| `project_code_list` | array | 否 | 领域编码筛选数组，元素为 `ProjectCodeItem`（见下方"项目编码筛选"），不传则返回全量 |

**返回字段**：`project_no`、`project_name`、`status`、`project_intro`、`first_code`、`first_code_name`、`second_code`、`second_code_name`、`fundras_object_second_name`、`project_donate_type`（1 普通 / 2 透明捐 1v1）

**使用示例**：
- 用户问"机构做过哪些项目""有哪些教育助学类项目" → 调用 `get_project_list`（按需带 `project_code_list` 筛选）
- 拿到 `project_no` 后可下钻到 `get_project_detail` / `get_project_financial_list`

> **⚠️ Schema 注意**：`get_project_list` 的入参 JSON Schema 当前有 bug——把 `first_code`、`second_code_list`、`rescue_code` 错误地展示为顶层字段。**正确方式**是用 `project_code_list` 嵌套结构传入（见下方）。

#### 项目编码筛选（ProjectCodeItem）

```json
{
  "project_code_list": [
    {
      "first_code": "PM0103",
      "second_code_list": ["PM010311"],
      "rescue_code": "PM01031JB"
    }
  ]
}
```

三个参数的职责（基于后端 SQL 实现）：

- `second_code_list[]`：**唯一触发筛选的字段**，用 `FIND_IN_SET` 过滤二级编码，空列表 = 无筛选（返回全量）
- `rescue_code`：`AND rescue_code = ?`，**仅当 `first_code` 为 `PM0103` / `PM0104` 时有效**，其余情况被忽略
- `first_code`：不参与 SQL WHERE，仅作为 `rescue_code` 是否生效的开关
- 多个 `ProjectCodeItem` 之间是 **OR** 关系

一级类目速查：`PM0101` 教育助学 / `PM0102` 乡村振兴 / `PM0103` 医疗救助（救助子类型 `PM01031JB` 疾病个案、`PM01032JB` 疾病群体）/ `PM0104` 灾害救援（`PM01041ZH` 紧急救灾、`PM01042ZH` 防灾备灾/灾后重建）/ `PM0105` 自然保护 / `PM0106` 关怀倡导。二级及更细编码需查业务侧编码字典。

---

## 第 2 层工具（依赖 project_no / project_id）

### get_project_detail - 获取项目详情

从 `get_project_list` 拿到 `project_no` 后下钻，获取项目背景、预算、执行地点、受益对象等。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `project_no` | string | 是 | 项目编号（来自 `get_project_list`） |

**返回字段**：`info.project_name`、`info.project_first_name`、`info.project_second_name`、`info.fundras_object_second_name`、`info.online_time`、`detail.project_backdrop`（项目背景）、`detail.proj_implement_res`、`detail.execution_node_list[]`、`donate.beneficiaries`（受益对象）、`donate.assisted_materials`、`donate.budget_supplement`、`budget[]`、`executorSite[]`（执行地省/市/区编码 province_code/city_code/area_code）

**使用示例**：
- 用户问"某个项目的背景/预算/执行地点/受益人群" → 先 `get_project_list` 拿 `project_no`，再 `get_project_detail`

### get_process_list - 获取项目进展列表

获取指定项目的进展（成效/指标/受益人数）列表。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `project_id` | integer | 是 | 项目 ID |
| `platform_version` | integer | 是 | 平台版本，填 `3` |
| `status` | integer | 是 | 进展状态，`-1` 拉取全部状态 |
| `publish_status` | integer | 是 | 发布状态，`-1` 拉取全部发布状态 |
| `size` | integer | 是 | 分页大小，建议 20 |
| `index` | integer | 否 | 页码，从 1 开始 |

**返回字段**：进展标题、摘要、内容、发布时间、执行指标；每条含 `id`（可下钻 `get_process_detail`）

**使用示例**：
- 用户问"项目做出了哪些成效""受益人数""最新进展" → 调用 `get_process_list`（`status=-1`、`publish_status=-1`、`platform_version=3`）

### get_project_financial_list - 获取财务披露列表

获取指定项目的财务披露（财披）列表，用于审计报告 / 资金使用查询。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `project_no` | string | 是 | 项目编号 |
| `page_index` | integer | 否 | 页码，默认 1 |
| `page_size` | integer | 否 | 每页条数，建议 20 |
| `sort` | integer | 否 | 排序，`2` = 按提交时间倒序（最新在前） |
| `disclosure_start_date` | string | 否 | 财披周期起始，格式 `YYYY-MM-DD`，按年份筛选时用 |
| `disclosure_end_date` | string | 否 | 财披周期结束，格式 `YYYY-MM-DD` |
| `audit_status` | integer | 否 | 按审核状态筛选（不填 = 全部；10 审核通过、11 待审核/审核中） |

**返回字段**：`finance_no`（可下钻 `get_financial_info`）、`disclosure_start_date`、`disclosure_end_date`、`fund_income`、`fund_expend`、`audit_status`、`exacutive_rate`、`submit_time`

**"近 N 年审计报告"日期推导示例**（当前 2026 年，要求近 3 年）：
`disclosure_start_date = "2024-01-01"`，`disclosure_end_date = "2026-12-31"`。

---

## 第 3 层工具（依赖第 2 层返回的 id）

### get_process_detail - 获取进展详情

从 `get_process_list` 拿到进展 `id` 后下钻，获取进展全文与结构化执行数据。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `id` | integer | 是 | 进展 ID（来自 `get_process_list`） |

**返回字段**：`content_title`、`desc`、`content`（HTML 全文）、`concrete_info`（结构化执行数据）、`publish_time`、`publish_name`

### get_financial_info - 获取财披详情

从 `get_project_financial_list` 拿到 `finance_no` 后下钻，获取单条财披的收支明细。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `finance_no` | string | 是 | 财披编号（来自 `get_project_financial_list`） |
| `is_edit` | boolean | 否 | 是否编辑模式，查看时填 `false` |

**返回字段**：`project_no`、`project_name`、`disclosure_start_date`、`disclosure_end_date`、`last_period_balance`、`current_period_balance`、`execution_summary`、`total_income`、`total_expend`、`donate_income`（含 `tx_user_donate` 腾讯平台用户捐款 / `tx_nine_and_ent_matching` 99公益日与企业配捐 / `ent_donate` 企业捐款 / `offline_donate` 线下捐款 / `income_total` 收入合计）、`project_expend[]`（`cost_item_one_name` 费用大类 / `execution_content` 执行内容 / `amount`×`price`=`total` / `invoice_pdf_url` 发票链接）、`project_budget[]`

---

## 辅助工具

### get_dictionary - 数据字典查询

将业务编码解码为中文名称（如社会组织评估类型/等级编号）。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `option_parent_code` | string | 是 | 字典父级编码，返回其下所有选项（`option_code` → `option_name`） |

**评估类型/等级两步解码示例**（`get_org_detail` 返回 `evaluation_type="PWP00002"`、`evaluation_level="PWP100022"`）：

```
Step 1: get_dictionary(option_parent_code="PWP00008")
        → 在返回列表中匹配 PWP00002 → option_name（如"社会组织评估等级"）
Step 2: get_dictionary(option_parent_code="PWP00002")
        → 在返回列表中匹配 PWP100022 → option_name（如"4A级"）
```

> 评估等级严禁硬编码名称（字典值可能变更），必须动态解码。`is_next=0` 的评估类型（如"未参与评级"）无需执行 Step 2。

---

## 反馈提交工具组（跨工具编排）

用户**明确表达**需要向平台反馈时（用户主动提出，或调用方询问"是否需要反馈"后用户确认），通过以下 3 步创建平台反馈单：**分类环节全自动**，**不询问用户手动选择分类**——由 AI 根据用户问题语义自动匹配分类；但"是否提交"这一步**必须**先取得用户明确同意，调用方不应在用户尚未表态时就自动触发。

### get_feedback_levels - 获取反馈分类列表

获取平台反馈分类树。**无需入参。**

**参数说明**：无

**返回字段**（`levelTreeItems[]`，树状结构）：

| 字段 | 说明 |
|------|------|
| `level_id` | 分类 ID（`create_feedback` 的 `level_id` 入参） |
| `level_name` | 分类名称（`create_feedback` 的 `level_name` 入参） |
| `level_desc` | 分类描述，用于语义匹配 |
| `auto_reply` | 该分类的自动回复文案（若有，可作为参考，不强制展示给用户） |
| `parent` | 上级分类 `level_id` |
| `leaf` | 是否为叶子节点（`true`/`false`） |

**分类匹配规则**：**只能选`leaf=true` 的叶子节点**作为 `create_feedback` 的 `level_id`/`level_name`；结合用户原始问题描述与 `level_name`/`level_desc` 做语义匹配，选择最贴合的一个；无法判断时选通用/其他类兜底；**严禁**把选择权交给用户。

### create_feedback - 创建反馈单

向平台创建一条反馈工单，供人工客服跟进处理。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `message` | string | 是 | 反馈内容，建议包含用户原始问题 + 已知上下文（AI 已判断的适用条件、已给出的初步结论等），便于客服快速定位无需用户重复描述 |
| `level_id` | string | 是 | 反馈分类 ID，来自 `get_feedback_levels` 返回的叶子节点（`leaf=true`） |
| `level_name` | string | 是 | 反馈分类名称，与 `level_id` 对应 |
| `org_no` | string | 是 | 机构编号，来自 `get_user_and_org_info` |
| `org_name` | string | 是 | 机构名称，来自 `get_user_and_org_info` |
| `imgs` | array | 否 | 反馈图片 URL 列表，无图片则不传或传空数组 |
| `system_replies` | string | 否 | AI 已给出的初步回复/结论摘要，供客服参考上下文 |
| `faq_id` | string | 否 | 使用 FAQ 创建反馈时才填；本场景（AI 主动创建）不使用 |

**返回字段**：`id`（反馈单号，内部记录用，无需在话术中念给用户）

**标准编排流程（3 步，全自动）**：

```
1. get_user_and_org_info()
   → 取 org_no、org_name

2. get_feedback_levels()
   → 取 levelTreeItems[]，在 leaf=true 的节点中按用户问题语义匹配一个最贴合的分类
   （不确定时选通用/其他类兜底，绝不询问用户手动选择）

3. create_feedback(message="<用户问题+已知上下文>", level_id="<步骤2匹配到的leaf.level_id>",
     level_name="<对应level_name>", org_no="<步骤1的org_no>", org_name="<步骤1的org_name>",
     system_replies="<AI已给出的初步结论摘要，如有>")
   → 成功返回 id
```

**成功后话术**：如实告知已提交反馈，并给出查看入口链接 `https://org.gongyi.qq.com/#/feedbacks`（固定的反馈记录页面，不因 `id` 不同而变化，不自动打开，引导用户自行点击查看）。

**失败处理**：任一步骤调用失败时，**不得声称已提交反馈**；如实告知失败原因，可建议稍后重试，或引导用户手动前往 `https://org.gongyi.qq.com/#/feedbacks` 自行提交。

**使用示例**：
- 用户问题超出常规查询/规则咨询能力（需要人工介入、系统故障、审批异常、资金安全、知识库无覆盖且不确定等）→ 先说明原因并询问用户是否需要反馈；**用户明确表示需要后**，按上述 3 步创建反馈（分类环节不询问用户），创建成功后展示查看链接

---

## 内置工具

### get_mcp_token - 获取当前访问令牌

鉴权通过后原样返回当前请求使用的访问令牌（OAuth access_token）原文，主要用于调试确认。**无需入参。**

**参数说明**：无

**使用示例**：
- 用户问"当前用的是哪个令牌" → 调用 `get_mcp_token`

---

## 枚举映射

调用方在展示结果时，需将下列数字/编码枚举转换为中文：

| 字段（来源工具） | 值 | 含义 |
|------|------|------|
| `type_of_organization`（get_user_and_org_info） | 1 / 2 | 公募机构 / 非公募机构 |
| `institution_type`（get_org_detail） | 1 / 2 | 公募机构 / 非公募机构 |
| `is_qualified`（get_org_detail.detailed） | 0 / 1 | 不合格·未通过 / 合格·已通过 |
| `audit_status`（get_project_financial_list） | 10 / 11 | 审核通过 / 待审核·审核中（其他值需实测确认） |
| `project_donate_type`（get_project_list） | 1 / 2 | 普通项目 / 透明捐 1v1 项目 |
| `evaluation_type` / `evaluation_level`（get_org_detail） | 编码 | 需经 `get_dictionary` 两步解码，勿硬编码 |

## 推荐调用顺序

1. **第一波（并行）**：`get_user_and_org_info` + `get_org_detail` + `get_org_member_list` + `get_project_list`
2. **第二波（对关注的每个 project_no 并行）**：`get_project_detail` + `get_process_list` + `get_project_financial_list`
3. **第三波（按需下钻）**：`get_process_detail`（进展全文） / `get_financial_info`（收支明细）

分页建议：`get_project_list` 优先用 `project_code_list` 服务端筛选再取 20 条；`get_process_list` 取最新 20 条不翻页；`get_project_financial_list` 取 20 条按提交时间倒序（`sort=2`）；`get_org_member_list` 取 20 条。

## 参数填写约定

- `object` 类型参数直接填 JSON 对象，`array` 类型直接填 JSON 数组，按工具 inputSchema 声明的真实嵌套结构填写即可。
- `integer` 传数字（如 `1`）而非字符串（`"1"`）；`boolean` 传 `true` / `false`。
- 编码类字段（行政区划、评估类型/等级）返回的是编码，展示前需解码为中文。

## 错误处理

- 鉴权失败（令牌失效/吊销/授权被撤销）：提示用户在连接器上重新点击「连接」完成 OAuth 授权（WorkBuddy 会自动打开授权页），无需手动处理任何 Token。
- 参数缺失：按工具返回的"参数缺失：xxx 为必填参数"提示补齐对应字段（尤其 `get_process_list` 的 `platform_version`/`status`/`publish_status`/`size` 均为必填）。
- 下游转发失败：如实转述错误信息，必要时提示用户稍后重试或联系公益平台支持。
