# 📖 CLI 参考手册

> 本文件是 `cli-spec.md` 的补充参考，包含完整的字段类型映射表、操作符枚举和详细示例。
> **仅在构造复杂 conditions 且不确定字段类型或操作符时加载。** 日常查询优先使用 `cli-spec.md`。

---

## 0. 新增：统计 API

以下为 Cordys CRM 统计 API 速查表：

| 端点 | 方法 | 用途 | 响应关键字段 |
|------|------|------|------------|
| `/home/statistic/lead` | POST | 线索统计 | `{thisYearClue, thisMonthClue, thisWeekClue, todayClue}` 各含 `count` + 上期 |
| `/home/statistic/opportunity` | POST | 商机统计 | 同上 + `amount` |
| `/home/statistic/opportunity/success` | POST | 赢单统计 | 同上 |
| `/home/statistic/opportunity/underway` | POST | 进行中商机 | 同上 |
| `/contract/statistic` | POST | 合同金额统计 | `{amount, averageAmount}` |
| `/contract/payment-record/statistic` | POST | 回款金额统计 | `{amount, averageAmount}` |
| `/opportunity/statistic` | POST | 商机金额统计 | `{amount, averageAmount}` |
| `/order/statistic` | POST | 订单金额统计 | `{amount, averageAmount}` |
| `/global/search/module/count?keyword=X` | GET | 全局搜索命中数 | 各模块命中条数 |
| `/account/contract/statistic/{id}` | GET | 客户合同总额 | `{totalAmount}` |
| `/account/contract/payment-record/statistic/{id}` | GET | 客户回款概览 | `{totalAmount, receivedAmount, pendingAmount}` |
| `/account/invoice/statistic/{id}` | GET | 客户开票概览 | `{contractAmount, uninvoicedAmount, invoicedAmount}` |
| `/contract/invoice/statistic/{contractId}` | GET | 合同发票统计 | 同上 |

> ⚠️ 使用 `cordys.sh raw` 调用。首次使用确认 API Key 认证兼容性。

---

## 1. 操作符总表

以下是所有可用操作符（enum 枚举值，**全大写**）：

| 操作符 | 含义 | 适用字段类型 |
|--------|------|-------------|
| `EQUALS` | 精确等于 | INPUT, TEXTAREA, PHONE, LINK, SERIAL_NUMBER, INPUT_NUMBER |
| `NOT_EQUALS` | 不等于 | 同上 |
| `CONTAINS` | 包含（模糊匹配） | INPUT, TEXTAREA, PHONE, LINK, SERIAL_NUMBER, ATTACHMENT, INPUT_MULTIPLE |
| `NOT_CONTAINS` | 不包含 | 同上 |
| `GT` | 大于 | INPUT_NUMBER, DATE_TIME |
| `LT` | 小于 | INPUT_NUMBER, DATE_TIME |
| `GE` | 大于等于 | INPUT_NUMBER |
| `LE` | 小于等于 | INPUT_NUMBER |
| `BETWEEN` | 在区间内 | DATE_TIME（时间戳数组 `[ts1, ts2]`） |
| `IN` | 在集合中（多选） | RADIO, SELECT, CHECKBOX, MEMBER, DEPARTMENT, DATA_SOURCE, SELECT_MULTIPLE, MEMBER_MULTIPLE, DEPARTMENT_MULTIPLE, DATA_SOURCE_MULTIPLE, LOCATION |
| `NOT_IN` | 不在集合中 | 同上 |
| `COUNT_GT` | 多值数量大于 | INPUT_MULTIPLE |
| `COUNT_LT` | 多值数量小于 | INPUT_MULTIPLE |
| `EMPTY` | 为空 | 除分割线/图片/公式/子表外的所有字段 |
| `NOT_EMPTY` | 不为空 | 同上 |
| `DYNAMICS` | 动态时间（需配合 `TIME_RANGE_PICKER` 类型） | DATE_TIME |

---

## 2. 字段类型 → 支持的操作符映射

> 本表是 Cordys CRM 后端的核心规则，**构造 conditions 时必须查询目标字段的实际类型，然后按此表选择合法操作符。**

| 字段类型 | 中文名 | 支持的操作符 |
|----------|--------|-------------|
| `INPUT` | 单行输入 | `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `NOT_CONTAINS`, `EMPTY`, `NOT_EMPTY` |
| `TEXTAREA` | 多行输入 | `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `NOT_CONTAINS`, `EMPTY`, `NOT_EMPTY` |
| `PHONE` | 电话 | `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `NOT_CONTAINS`, `EMPTY`, `NOT_EMPTY` |
| `LINK` | 链接 | `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `NOT_CONTAINS`, `EMPTY`, `NOT_EMPTY` |
| `SERIAL_NUMBER` | 流水号 | `EQUALS`, `NOT_EQUALS`, `CONTAINS`, `NOT_CONTAINS`, `EMPTY`, `NOT_EMPTY` |
| `INPUT_NUMBER` | 数字 | `EQUALS`, `NOT_EQUALS`, `GT`, `LT`, `GE`, `LE` |
| `ATTACHMENT` | 附件 | `CONTAINS`, `NOT_CONTAINS`, `EMPTY`, `NOT_EMPTY` |
| `DATE_TIME` | 日期时间 | `BETWEEN`, `GT`, `LT`, `EMPTY`, `NOT_EMPTY`，（另支持 `DYNAMICS` + `TIME_RANGE_PICKER`） |
| `INPUT_MULTIPLE` | 多值输入 | `COUNT_LT`, `COUNT_GT`, `CONTAINS`, `NOT_CONTAINS`, `EMPTY`, `NOT_EMPTY` |
| `RADIO` | 单选 | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `SELECT` | 单选下拉 | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `CHECKBOX` | 多选 | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `MEMBER` | 成员（单选） | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `DEPARTMENT` | 部门（单选） | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `DATA_SOURCE` | 数据源（单选） | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `SELECT_MULTIPLE` | 多选下拉 | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `MEMBER_MULTIPLE` | 多选成员 | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `DEPARTMENT_MULTIPLE` | 多选部门 | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `DATA_SOURCE_MULTIPLE` | 多选数据源 | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `LOCATION` | 地址 | `IN`, `NOT_IN`, `EMPTY`, `NOT_EMPTY` |
| `DIVIDER` | 分割线 | **无操作符**（纯展示字段，不可查询） |
| `PICTURE` | 图片 | **无操作符**（不可作为查询条件） |
| `INDUSTRY` | 行业 | **无操作符** |
| `FORMULA` | 公式 | **无操作符**（计算字段，不可查询） |
| `SUB_PRODUCT` | 子表-产品 | **无操作符**（子表结构，不可单独查询） |
| `SUB_PRICE` | 子表-价格 | **无操作符**（子表结构，不可单独查询） |

### 操作符归属速查

| 归属组 | 字段类型 | 可用操作符 |
|--------|----------|-----------|
| **文本类** | INPUT, TEXTAREA, PHONE, LINK, SERIAL_NUMBER | EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS, EMPTY, NOT_EMPTY |
| **数字类** | INPUT_NUMBER | EQUALS, NOT_EQUALS, GT, LT, GE, LE |
| **日期类** | DATE_TIME | BETWEEN, GT, LT, EMPTY, NOT_EMPTY, DYNAMICS |
| **附件类** | ATTACHMENT | CONTAINS, NOT_CONTAINS, EMPTY, NOT_EMPTY |
| **多值文本类** | INPUT_MULTIPLE | COUNT_LT, COUNT_GT, CONTAINS, NOT_CONTAINS, EMPTY, NOT_EMPTY |
| **单选/枚举类** | RADIO, SELECT, CHECKBOX, MEMBER, DEPARTMENT, DATA_SOURCE, SELECT_MULTIPLE, MEMBER_MULTIPLE, DEPARTMENT_MULTIPLE, DATA_SOURCE_MULTIPLE, LOCATION | IN, NOT_IN, EMPTY, NOT_EMPTY |
| **不可查询** | DIVIDER, PICTURE, INDUSTRY, FORMULA, SUB_PRODUCT, SUB_PRICE | （无） |

---

## 3. 各字段类型详细示例

### 文本类（INPUT / TEXTAREA / PHONE / LINK / SERIAL_NUMBER）

```json
// 精确匹配
{"value": "张三", "operator": "EQUALS", "name": "name", "type": "INPUT"}

// 模糊包含
{"value": "科技", "operator": "CONTAINS", "name": "company", "type": "INPUT"}

// 不包含
{"value": "测试", "operator": "NOT_CONTAINS", "name": "description", "type": "TEXTAREA"}

// 为空/不为空
{"value": "", "operator": "EMPTY", "name": "phone", "type": "PHONE"}
{"value": "", "operator": "NOT_EMPTY", "name": "website", "type": "LINK"}
```

### 数字类（INPUT_NUMBER）

```json
{"value": 100000, "operator": "EQUALS", "name": "amount", "type": "INPUT_NUMBER"}
{"value": 50000, "operator": "GT", "name": "amount", "type": "INPUT_NUMBER"}
{"value": 1000, "operator": "GE", "name": "quantity", "type": "INPUT_NUMBER"}
{"value": 10000, "operator": "LE", "name": "quantity", "type": "INPUT_NUMBER"}
```

### 日期类（DATE_TIME）

```json
// 时间戳区间（毫秒）
{"value": [1700000000000, 1700100000000], "operator": "BETWEEN", "name": "createTime", "type": "DATE_TIME"}

// 晚于某个时间
{"value": 1700000000000, "operator": "GT", "name": "createTime", "type": "DATE_TIME"}

// 动态时间
{"value": "MONTH", "operator": "DYNAMICS", "name": "createTime", "type": "TIME_RANGE_PICKER"}

// 为空/不为空
{"value": "", "operator": "EMPTY", "name": "followTime", "type": "DATE_TIME"}
```

> **时间格式**：`GT`/`LT`/`BETWEEN` 使用**毫秒级时间戳**；`DYNAMICS` 使用时间常量字符串。

### 附件类 / 多值输入 / 枚举类

```json
// 附件
{"value": "合同", "operator": "CONTAINS", "name": "attachment", "type": "ATTACHMENT"}

// 多值输入
{"value": 2, "operator": "COUNT_GT", "name": "tags", "type": "INPUT_MULTIPLE"}
{"value": "VIP", "operator": "CONTAINS", "name": "tags", "type": "INPUT_MULTIPLE"}

// 枚举（单选/多选/成员/部门/数据源）
{"value": ["Qualification", "Negotiation"], "operator": "IN", "name": "stage", "multipleValue": false, "type": "SELECT"}
{"value": ["user123"], "operator": "IN", "name": "ownerId", "multipleValue": false, "type": "MEMBER"}
{"value": ["dept_a", "dept_b"], "operator": "IN", "name": "departmentId", "multipleValue": false, "type": "TREE_SELECT"}
```

### 动态时间常量表

| 常量 | 含义 | | 常量 | 含义 |
|------|------|-|------|------|
| `TODAY` | 今天 | | `YESTERDAY` | 昨天 |
| `WEEK` | 本周 | | `LAST_WEEK` | 上周 |
| `MONTH` | 本月 | | `LAST_MONTH` | 上个月 |
| `QUARTER` | 本季度 | | `LAST_QUARTER` | 上季度 |
| `YEAR` | 本年度 | | `LAST_YEAR` | 上年度 |
| `LAST_SEVEN` | 过去7天 | | `LAST_THIRTY` | 过去30天 |

自定义天数：`["CUSTOM", 90, "BEFORE_DAY"]`

---

## 4. 审批 API 完整参考

### 审批代办端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/approval-todo/pending/page` | POST | 待我审批分页 |
| `/approval-todo/processed/page` | POST | 我已处理的审批分页 |
| `/approval-todo/initiated/page` | POST | 我发起的审批分页 |
| `/approval-todo/cc/page` | POST | 抄送我的审批分页 |
| `/approval-todo/pending/count` | GET | 待审批统计 |

### 审批操作端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/approval-action/approve` | POST | 同意 |
| `/approval-action/reject` | POST | 驳回 |
| `/approval-action/back` | POST | 退回 |
| `/approval-action/sign` | POST | 加签 |
| `/approval-action/revoke` | POST | 撤回 |
| `/approval-action/batch-approve` | POST | 批量同意 |
| `/approval-action/batch-reject` | POST | 批量驳回 |

**请求体结构：**

```json
// 同意/驳回（单个）
{"resourceId":"审批资源ID", "remark":"审批意见"}

// 退回
{"resourceId":"审批资源ID", "backNodeId":"目标节点ID", "remark":"退回原因"}

// 加签
{"resourceId":"审批资源ID", "signUserIds":["user1","user2"], "remark":"加签说明"}

// 批量
{"resourceIds":["id1","id2"], "remark":"批量意见"}
```

### 审批资源端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/approval-resource/push` | POST | 提审 |
| `/approval-resource/revoke` | POST | 撤销 |
| `/approval-resource/simple-detail/{resourceId}` | GET | 列表详情 |
| `/approval-resource/detail/{resourceId}` | GET | 完整记录详情（含审批流进度） |

### 审批流端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/approval-flow/page` | POST | 审批流列表 |
| `/approval-flow/add` | POST | 新建审批流 |
| `/approval-flow/update` | POST | 更新审批流 |
| `/approval-flow/get/{id}` | GET | 审批流详情 |
| `/approval-flow/delete/{id}` | GET | 删除审批流 |
| `/approval-flow/enable/{id}` | GET | 启用/禁用 |
| `/approval-flow/get-by-form-type/{formType}` | GET | 按表单类型获取 |
| `/approval-flow/status-permission/setting/{formType}` | GET | 状态权限配置 |
| `/approval-flow/webhook/test` | POST | webhook 测试 |

### 审批代办响应字段

| 字段 | 说明 |
|------|------|
| `resourceId` | 审批资源ID |
| `resourceName` | 审批标题/名称 |
| `resourceType` | 资源类型（QUOTATION/CONTRACT/ORDER/INVOICE） |
| `status` | 审批状态 |
| `initiatorName` | 发起人 |
| `createTime` | 创建时间 |
| `currentApproverName` | 当前审批人 |
