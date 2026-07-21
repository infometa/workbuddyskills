# ⚙️ CLI 语义规范

本文件定义了 `cordys` CLI 的全部命令、参数规则和意图映射。
所有 AI 生成的命令必须遵循本规范。

> **目录**
>
> 1. [命令族总览](#1-命令族总览)
> 2. [分页默认结构](#2-分页默认结构)
> 3. [意图 → 命令映射](#3-意图--命令映射)
> 4. [模块推断](#4-模块推断)
> 5. [高级条件处理](#5-高级条件处理)
> 6. [动态参数替换](#6-动态参数替换)
> 7. [排序规则](#7-排序规则)
> 8. [异常处理](#8-异常处理)
> 9. [内置视图与自定义视图](#9-内置视图与自定义视图)
> 10. [部门组织架构展开](#10-部门组织架构展开)
> 11. [全局模糊搜索](#11-全局模糊搜索)
> 12. [审批操作](#12-审批操作)

> 📖 **完整参考**：字段类型→操作符映射表、详细 JSON 示例、审批 API 完整端点 → 见 `core/cli-reference.md`（仅在构造复杂 conditions 或处理审批时按需加载）。

---

## 0. 引擎加载优先级（更新）

```
启动时必加载：
  core/role-engine.md        角色匹配

L2C 场景按需加载：
  core/cli-spec.md           构造命令（每次必用）
  core/output-engine.md      格式化输出（每次必用）
  core/risk-engine.md        扫描风险（展示数据后）
  core/cli-reference.md      字段类型映射（构造 conditions 时）
  core/linkage-engine.md     跨模块关联追踪（追踪链路时）
  core/funnel-engine.md      漏斗分析（看转化/管道时）
  core/workflow-engine.md    工作流（用户说模糊指令时）
```

---

## 1. 命令族总览

所有命令使用 `cordys.sh`（Shell CLI，推荐）执行，`cordys.py` 备用（已弃用）。

```text
cordys.sh crm page    <模块> [关键词|JSON]     分页查询
cordys.sh crm get     <模块> <ID>              获取详情
cordys.sh crm search  <模块> [关键词|JSON]     全局搜索
cordys.sh crm follow  plan|record <模块> <JSON>  跟进计划/记录
cordys.sh crm contact <模块> <ID>              联系人列表
cordys.sh crm product [关键词|JSON]            产品列表
cordys.sh crm org                             组织架构
cordys.sh crm members <JSON>                   部门成员
cordys.sh crm whoami                           当前用户信息
cordys.sh crm verify                           验证 API 密钥
cordys.sh raw          <METHOD> <PATH> [body]  原始 API 调用
```

**审批命令：**

```text
cordys.sh crm approval todo     <类型> [JSON]        审批代办列表
cordys.sh crm approval action   <操作> <JSON>        审批操作
cordys.sh crm approval resource <操作> [参数]         审批资源
cordys.sh crm approval flow     <操作> [参数]         审批流管理
```

> `cordys.sh` 前置路径为 `scripts/cordys.sh`，无需切换目录。

---

## 2. 分页默认结构

所有 page/search 命令使用统一的 JSON body 模板：

```json
{
  "current": 1,
  "pageSize": 30,
  "sort": {},
  "combineSearch": {
    "searchMode": "AND",
    "conditions": []
  },
  "keyword": "",
  "viewId": "ALL",
  "filters": []
}
```

### 自动补全规则
| 条件 | 动作 |
|------|------|
| 只给关键词 | 放入 `keyword`，其余字段填默认值 |
| 给部分 JSON | 补全缺失字段，保留已有字段；若未给 `viewId` 则按语义推断 |
| 给完整 JSON | 原样传递，不修改 |
| 没给任何参数 | 全部默认值 |

---

## 3. 意图 → 命令映射

| 用户说 | 映射命令 | 备注 |
|--------|---------|------|
| 列表、分页查看、看看、有哪些 | `crm page <module>` | 自动追加角色过滤 |
| 搜索、筛选、找一下、找 xxx | `crm search <module> <JSON>` | 关键词→keyword，条件→conditions |
| **模糊搜索（未指定模块）** | **同时搜索 lead, pool/lead, account, opportunity, pool/account, contact** | **见 §11** |
| 详情、查看、打开这个 | `crm get <module> <ID>` | 若有名称无 ID，先搜索 |
| 跟进、跟进计划/记录 | `crm follow <plan\|record> <module> <JSON>` | 需 sourceId |
| 全部、拉全量、查完所有页 | 执行 page，遍历所有页 | 每页后询问是否继续 |
| 原始、自定义 | `cordys raw <METHOD> <PATH>` | 仅限信任域名 |
| **L2C 链路追踪** | `crm get` 起点 → `crm page` 上下游模块 | **见 §13** |
| **漏斗分析** | 多模块并行 `crm page` → 聚合 | **见 §14** |
| **Customer 360** | 全局搜索 + 多模块 page | **见 §15** |

---

## 4. 模块推断

| 用户说 | 模块 | 常用命令 |
|--------|------|---------|
| 线索、潜客 | `lead` | page, get, search, follow |
| 客户、公司、厂商 | `account` | page, get, search, follow, contact |
| 商机、机会 | `opportunity` | page, get, search, follow |
| 合同 | `contract` | page, get, search |
| 回款、回款计划 | `contract/payment-plan` | page |
| 回款记录 | `contract/payment-record` | page |
| 发票 | `invoice` | page |
| 报价单 | `opportunity/quotation` | page |
| 订单 | `order` | page, statistic |
| 工商抬头 | `contract/business-title` | page |
| 产品 | 使用 `product` 命令 | product |
| 组织、部门 | `org` | org |
| 成员、人员 | `members` | members |
| 联系人 | `contact` | contact |
| 线索池 | `pool/lead` | page（需 poolId） |
| 公海 | `pool/account` | page（需 poolId） |

---

## 5. 高级条件处理

### 5.1 两种过滤方式

| 方式 | 位置 | 适用场景 |
|------|------|---------|
| `combineSearch.conditions` | JSON body 内 | **推荐**。支持 AND/OR 组合、所有字段类型、所有操作符 |
| `filters` | JSON body 内下层数组 | 仅支持基础操作符（equals/contains/gte/lte），不建议复杂场景使用 |

> **最佳实践**：所有筛选条件统一放入 `combineSearch.conditions`，`filters` 保持为空数组。

### 5.2 conditions 结构

```json
{
  "value": "xxx",           // 条件值（字符串、数字、布尔、数组）
  "operator": "EQUALS",     // 操作符（大写枚举）
  "name": "fieldName",      // 字段名（API 字段标识，大小写敏感）
  "multipleValue": false,   // 是否允许多值
  "type": "INPUT"           // 字段类型（决定哪些操作符可用）
}
```

### 5.3 常用操作符速查

| 场景 | 操作符 | 示例 |
|------|--------|------|
| 精确等于 | `EQUALS` | 名称等于"张三" |
| 模糊包含 | `CONTAINS` | 行业包含"科技" |
| 大于/小于 | `GT` / `LT` | 金额大于50000 |
| 大于等于/小于等于 | `GE` / `LE` | 数量≤10000 |
| 在集合中 | `IN` | 阶段在 [需求确认, 谈判] |
| 区间 | `BETWEEN` | 创建时间在 [ts1, ts2] |
| 动态时间 | `DYNAMICS` | 本月创建的（type=`TIME_RANGE_PICKER`） |
| 为空/不为空 | `EMPTY` / `NOT_EMPTY` | 电话不为空 |

> 📖 **完整操作符列表和字段类型→操作符映射表** → 见 `core/cli-reference.md`。仅在构造 conditions 且不确定 type 字段值时加载。

### 5.4 动态时间过滤

```json
{"value": "MONTH", "operator": "DYNAMICS", "name": "createTime", "type": "TIME_RANGE_PICKER"}
```

常用时间常量：`TODAY`, `YESTERDAY`, `WEEK`, `LAST_WEEK`, `MONTH`, `LAST_MONTH`, `QUARTER`, `YEAR`, `LAST_SEVEN`, `LAST_THIRTY`

自定义天数：`["CUSTOM", 90, "BEFORE_DAY"]`

### 5.5 组合条件

```json
{
  "combineSearch": {
    "searchMode": "AND",       // AND 或 OR
    "conditions": [
      { "value": "科技", "operator": "CONTAINS", "name": "industry", "type": "INPUT" },
      { "value": "MONTH", "operator": "DYNAMICS", "name": "createTime", "type": "TIME_RANGE_PICKER" }
    ]
  }
}
```

**获取字段类型的方法：**

```bash
cordys.sh raw GET /settings/fields?module=account
cordys.sh crm get account <id>
```

> 📖 `type` 字段决定可用的 `operator`。完整映射表 → `core/cli-reference.md` §2。

---

## 6. 动态参数替换（从 Cordys.md 读取）

| 占位符 | 来源字段 | 示例值 |
|--------|---------|-------|
| `{userId}` | Cordys.md 用户ID | `admin` |
| `{departmentId}` | Cordys.md 部门ID（展开后为数组） | `["dept_a","dept_b"]` |

> 如果 Cordys.md 中没有对应的 ID，则不追加该过滤条件。

---

## 7. 排序规则

```json
{"followTime": "desc"}
{"createTime": "asc"}
```

常用排序字段：`followTime`、`createTime`、`amount`、`stage`

---

## 8. 异常处理

| 响应 | 处理方式 |
|------|---------|
| HTTP 401/403 | 提示密钥可能失效，建议刷新身份 |
| code ≠ 100200 | 读取 message 字段并说明原因 |
| `INVALID_FILTER` | 检查字段名拼写和操作符是否匹配该字段类型 |
| 数据空列表 | 确认是否真的无数据，还是过滤条件太严 |
| CLI 报错 | 检查环境变量和 .env |
| 接口超时 | 提示稍后重试或减小 pageSize（≤200） |

---

## 9. 内置视图与自定义视图

### 9.1 内置系统视图（直接使用）

| viewId | 含义 | 适用模块 |
|--------|------|---------|
| `ALL` | 全部数据（默认） | 所有模块 |
| `SELF` | 我的数据 | `lead`, `account`, `opportunity`, `contract` |
| `CUSTOMER_COLLABORATION` | 协作客户 | `account` 仅 |

### 9.2 viewId 匹配流程

```
1. 匹配内置视图（"我的"→SELF, "全部"→ALL）
2. 未命中 → 调用 `cordys.sh crm view <module>` 获取自定义视图列表
```

### 9.3 典型语义映射

| 用户说 | viewId |
|--------|--------|
| "全部线索" / "所有线索" | `ALL` |
| "我的线索" / "我负责的线索" | `SELF` |
| "我的客户" | `SELF` |
| "协作客户" | `CUSTOMER_COLLABORATION` |

> 优先使用 viewId 而非自己构造 filters。

---

## 10. 部门组织架构展开（含子部门）

当用户按**部门范围**查询时，**必须自动包含该部门下的所有子部门**。

### 操作流程

```
1. 识别目标部门名称，通过 `cordys.sh crm org` 获取组织架构树
2. 在树中定位该部门节点，递归遍历其所有子节点
3. 收集该部门及所有子孙部门的 ID 列表
4. 构造 departmentId 数组过滤器
```

### 部门范围过滤器标准模式

```json
{
  "combineSearch": {
    "searchMode": "AND",
    "conditions": [
      {
        "value": "{departmentId}",
        "operator": "IN",
        "name": "departmentId",
        "multipleValue": false,
        "type": "TREE_SELECT"
      }
    ]
  }
}
```

执行示例（替换后）：
```json
{"value": ["dept_a", "dept_b", "dept_c"], "operator": "IN", "name": "departmentId", "multipleValue": false, "type": "TREE_SELECT"}
```

| 场景 | 行为 |
|------|------|
| "我部门"、不指定部门 | 使用 Cordys.md 的 `{departmentId}`，展开子部门 |
| 指定具体部门名 | 通过 org 树查找该部门ID，展开子部门 |
| "全公司"、"全部" | 不使用部门过滤，viewId 用 `ALL` |
| 部门没有子部门 | `{departmentId}` = 该部门自己的ID数组 `["dept_x"]` |

---

## 11. 全局模糊搜索（多模块并行）

当用户**未明确指定模块**时，并行搜索 6 个模块：

| 中文名 | 模块名 | 优先级 |
|--------|--------|-------|
| 线索 | `lead` | 🔴 高 |
| 线索池 | `pool/lead` | 🔴 高 |
| 客户 | `account` | 🔴 高 |
| 商机 | `opportunity` | 🟡 中 |
| 公海 | `pool/account` | 🟡 中 |
| 联系人 | `contact` | 🟢 低 |

每个模块使用统一模板，`pageSize: 10`。用后台进程 `&` 并行发起，等待全部完成后合并输出。

### 模块明确性判定

- 输入含「线索/客户/商机/联系人/线索池/公海」→ 只搜指定模块
- 仅含公司名/人名/联系方式等 → 执行全局模糊搜索

---

## 12. 审批操作

### 12.1 审批意图映射

| 用户说 | 映射命令 |
|--------|---------|
| 我的待审批、看看谁需要我批 | `approval todo pending` |
| 我处理过的审批 | `approval todo processed` |
| 我发起的 | `approval todo initiated` |
| 抄送我的 | `approval todo cc` |
| 有多少待审批 | `approval todo count` |
| 同意/通过这个审批 | `approval action approve` + `resourceId` |
| 驳回/拒绝 | `approval action reject` + `resourceId` + `remark` |
| 退回/打回 | `approval action back` + `resourceId` + `backNodeId` |
| 加签 | `approval action sign` + `resourceId` + `signUserIds` |
| 撤回申请 | `approval action revoke` + `resourceId` |
| 批量同意 | `approval action batch-approve` + `resourceIds` |
| 提交审批/提审 | `approval resource push` + `resourceId` |
| 审批进度 | `approval resource detail <resourceId>` |
| 审批流设置 | `approval flow list` |

### 12.2 审批代办 JSON 结构

和 CRM page 参数结构一致，额外多一个字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `resourceType` | string | 可选：`ALL` / `QUOTATION` / `CONTRACT` / `ORDER` / `INVOICE` |

```bash
# 示例
cordys.sh crm approval todo pending '{"current":1,"pageSize":30,"resourceType":"CONTRACT"}'
cordys.sh crm approval todo count
cordys.sh crm approval action approve '{"resourceId":"xxx","remark":"同意"}'
cordys.sh crm approval resource detail RESOURCE_ID
```

> 📖 **审批操作完整 JSON body 结构、审批流管理端点** → 见 `core/cli-reference.md` §4。

---

## 13. L2C 链路追踪

> 完整规范见 `core/linkage-engine.md`。本节仅提供命令级摘要。

### 13.1 正向追踪（顺藤摸瓜）

```
1. cordys.sh crm get <module> <id>       获取起点记录（提取关联字段）
2. cordys.sh crm page <target_module>    用关联字段筛选下游数据
3. 逐级向下追踪直到回款/发票
```

### 13.2 反向溯源（追根究底）

```
1. cordys.sh crm get <module> <id>       获取起点记录
2. 提取关联的上游模块字段
3. cordys.sh crm get <upstream_module>   获取上游记录
4. 逐级向上溯源直到线索
```

### 13.3 Customer 360

```
1. 全局搜索公司名（6 模块并行）
2. 锁定 account ID
3. 以 account ID（或公司名）搜索：opportunity, contact, contract
4. 以合同 ID 搜索：payment-plan, invoice
5. 合并输出 360 视图
```

> 完整规范见 `core/linkage-engine.md`。

---

## 14. L2C 漏斗分析

> 完整规范见 `core/funnel-engine.md`。本节仅提供命令级摘要。

### 14.1 漏斗快照

```bash
# 并行查询各阶段本月数据
cordys.sh crm page lead       '{"pageSize":1,"combineSearch":{"conditions":[{"value":"MONTH","operator":"DYNAMICS","name":"createTime","type":"TIME_RANGE_PICKER"}]}}' &
cordys.sh crm page account    '{"pageSize":1,"combineSearch":{"conditions":[{"value":"MONTH","operator":"DYNAMICS","name":"createTime","type":"TIME_RANGE_PICKER"}]}}' &
cordys.sh crm page opportunity '{"pageSize":1,"combineSearch":{"conditions":[{"value":"MONTH","operator":"DYNAMICS","name":"createTime","type":"TIME_RANGE_PICKER"}]}}' &
cordys.sh crm page contract   '{"pageSize":1,"combineSearch":{"conditions":[{"value":"MONTH","operator":"DYNAMICS","name":"signTime","type":"TIME_RANGE_PICKER"}]}}' &
wait
```

> 从各模块响应的 `data.total` 获取计数。

### 14.2 金额汇总

合同/商机金额汇总 → 遍历分页数据，AI 端求和。超过 100 条提示缩小范围。

### 14.3 管道预测

```bash
# 未来 7 天到期回款
cordys.sh crm page contract/payment-plan '{"combineSearch":{"conditions":[
  {"value": [now_ts, now_ts+604800000], "operator": "BETWEEN", "name": "planPayTime", "type": "DATE_TIME"}
]}}'
```

---

## 15. L2C 工作流

> 完整规范见 `core/workflow-engine.md`。

当用户使用模糊指令（"今天做什么"、"这周怎么样"、"团队情况"）时，AI 自动匹配并执行对应工作流。

| 触发词 | 工作流 |
|--------|--------|
| 今天/今日 + 做什么/有什么/看看 | 销售晨会速览 / 财务回款日报 |
| 这周/本周 + 怎么样/情况 | 销售周回顾 / 经理周会 |
| 本月/这个月 + 复盘/情况 | 月度复盘 |
| 团队/部门 + 情况/概览 | 经理团队晨会 |
| 批一下/待审批 | 审批巡检 |
| 回款/欠款/催款 | 财务应收账款 |
| 看看 XX 公司 | 客户深耕 |
| 查查 XX 合同/这笔单子 | 全链路追踪 |
