# 🗺️ L2C 工作流引擎

本文件定义了各角色在 L2C 链路中的**典型工作流**，帮助 AI 理解用户意图并提供精准引导。
当用户说"今天要做什么"、"这周重点"、"帮我看看"等模糊指令时，AI 按此文件的工作流自动规划查询。

---

## 1. 销售日常工作流

### 1.1 晨会速览（"看看今天"）

```
用户说："看看今天的情况"

执行流程：
  1. cordys.sh crm follow plan lead '{"myPlan":true,"status":"UNFINISHED"}'
     → 今日跟进计划
  2. cordys.sh crm search lead '{"combineSearch":{"conditions":[
       {"value":"TODAY","operator":"DYNAMICS","name":"createTime","type":"TIME_RANGE_PICKER"}
     ]}}'
     → 今日新增线索
  3. cordys.sh crm page lead '{"viewId":"SELF"}'
     → 我的线索列表（提取总数、检查风险）

输出：今日计划 + 最新线索 + 风险提醒
```

### 1.2 周回顾（"这周怎么样"）

```
执行流程：
  1. 本周新增线索数（DYNAMICS WEEK）
  2. 本周新增商机数 + 金额汇总
  3. 本周签约合同数 + 金额汇总
  4. 本周跟进记录数（可选）
  5. 超期未跟进线索（followTime < 3天前）

输出：漏斗快照 + 跟进行为 + 签约成果
```

### 1.3 跟进优先级排序（"哪些要先跟"）

```
排序规则（按紧急度降序）：
  1. 🚨 超过 7 天未跟进的线索/商机
  2. ⚠️  商机在某个阶段停留超过 7 天
  3. 📋 今日跟进计划中的待办
  4. 🟢 近 3 天新创建的线索

执行：
  1. cordys.sh crm page lead '{"viewId":"SELF","sort":{"followTime":"asc"}}'
     → 按跟进时间升序，最久未跟的排前面
  2. cordys.sh crm page opportunity '{"viewId":"SELF","sort":{"followTime":"asc"}}'
     → 商机同理
```

### 1.4 客户深耕（"看看XX公司"）

```
用户说："看看华星科技"

执行：
  1. 全局搜索找到客户 account ID
  2. 客户360：名下商机、合同、回款、联系人
  3. 跟进历史：最近 5 条跟进记录
  4. 关联线索（如果有）

输出：公司全景视图
```

---

## 2. 销售经理工作流

### 2.1 团队晨会（"团队今天"）

```
执行流程：
  1. cordys.sh crm org → 获取部门树
  2. cordys.sh crm members '{"departmentId":"..."}' → 成员列表
  3. 部门线索总量 + 今日新增
  4. 部门商机总量 + 本月新增
  5. 成员跟进率（需遍历成员）

输出：团队看板 + 关键指标 + 异常成员标记
```

### 2.2 周会数据（"团队这周"）

```
执行流程：
  1. 本周 L2C 漏斗快照（见 funnel-engine.md §3.2）
  2. 成员排名表（线索量、签约量、签约金额）
  3. 周环比（本周 vs 上周）
  4. 风险巡检（低跟进率、低转化、长期未跟）

输出：周报数据 + 排名 + 风险列表
```

### 2.3 月度复盘（"本月复盘"）

```
执行流程：
  1. 本月漏斗（线索→客户→商机→合同→回款）
  2. 团队成员月度排名
  3. 本月 vs 上月对比
  4. 赢单/输单分析（各阶段商机数量分布）
  5. 签约金额汇总 + 回款预测

输出：月度报告 + 趋势分析 + 改进建议
```

### 2.4 审批巡检（"批一下"）

```
执行：
  1. cordys.sh crm approval todo count → 待审批数量
  2. cordys.sh crm approval todo pending → 待审批列表
  3. 对超过 3 天未处理的审批标 ⚠️

输出：待审批列表 + 超期提醒
```

---

## 3. 财务工作流

### 3.1 回款日报（"今天回款情况"）

```
执行流程：
  1. cordys.sh crm page contract/payment-record '{
       "combineSearch":{"conditions":[
         {"value":"TODAY","operator":"DYNAMICS","name":"paymentTime","type":"TIME_RANGE_PICKER"}
       ]}
     }'
     → 今日回款记录
  2. 今日到期回款计划
  3. 逾期回款汇总

输出：今日回款 + 到期提醒 + 逾期汇总
```

### 3.2 应收账款全景（"欠款情况"）

```
执行流程：
  1. cordys.sh crm page contract/payment-plan → 全部回款计划
  2. 筛选状态为"未回款"或"部分回款"
  3. 按到期日排序，逾期优先
  4. 汇总：总应收、已逾期、即将到期（7天内）、正常

输出：AR 全景 + 逾期列表 + 催收优先级
```

### 3.3 合同→现金全链路（"合同回款进度"）

```
执行流程（对指定合同）：
  1. cordys.sh crm get contract {id} → 合同详情
  2. cordys.sh crm page contract/payment-plan → 回款计划
  3. cordys.sh crm page contract/payment-record → 实际回款
  4. cordys.sh crm page invoice → 开票记录
  5. 对比：计划金额 vs 实际回款 vs 开票金额

输出：合同→现金链路图 + 缺口分析
```

### 3.4 月度财报数据

```
执行流程：
  1. 本月签约合同数 + 总金额
  2. 本月回款总额
  3. 本月开票总额
  4. 应收账款余额
  5. 环比数据（本月 vs 上月）

输出：月度财报摘要
```

---

## 4. 高管工作流

> 详细流程见 `profiles/executive.md`

### 4.1 快照速览（"公司情况"）
```
执行：
  1. POST /home/statistic/lead (searchType=ALL) → 全公司线索数
  2. POST /home/statistic/opportunity (searchType=ALL) → 全公司商机+金额
  3. POST /home/statistic/opportunity/success (searchType=ALL) → 赢单
  4. POST /contract/statistic (viewId=ALL, MONTH) → 签约金额
输出：四张卡 + 环比
```

### 4.2 部门排名（"部门怎么样"）
```
执行：
  1. GET /home/statistic/department/tree → 一级部门列表
  2. 每部门 POST /home/statistic/opportunity (searchType=DEPARTMENT)
  3. 每部门 POST /contract/statistic + departmentId filter
输出：排名表 + 环比 + 异常标注
```

### 4.3 目标差距（"目标完成怎么样"）
```
执行：
  1. 季度签约总额 vs 季度目标
  2. 时间进度 vs 业绩进度对比
  3. 商机管道金额 × 历史赢单率 ≈ 预计产出
输出：完成率 + 差距 + 预测
```

## 5. 商务/合同工作流

> 详细流程见 `profiles/contract-admin.md`

### 5.1 合同审批追踪（"审批到哪了"）
```
执行：
  1. POST /contract/page + conditions: approvalStatus 为审批中
  2. 对每个合同 GET /approval-resource/detail/{resourceId}
输出：审批中合同 + 当前节点 + 持续时间
```

### 5.2 签约日报（"今天签了什么"）
```
执行：
  POST /contract/page + conditions: startTime=TODAY
输出：今日签约列表 + 金额汇总
```

### 5.3 到期预警（"哪些快到期了"）
```
执行：
  POST /contract/page + conditions: endTime BETWEEN [now, now+30d]
  按 endTime 升序排列
输出：到期合同列表 + 客户 + 金额 + 续约建议
```

---

## 6. 通用 L2C 工作流

### 4.1 全链路追踪（"查查这笔单子"）

```
用户说："查查合同 CRM-2026-001"

执行：
  1. cordys.sh crm page contract → 用 keyword="CRM-2026-001" 找到合同
  2. cordys.sh crm get contract {id} → 获取详情（含关联字段）
  3. 反向追溯：合同 → 商机 → 客户 → 线索
  4. 正向追踪：合同 → 回款计划 → 回款记录 → 发票
  5. 输出：完整 L2C 时间线

输出示例：
  📋 L2C 全链路：CRM-2026-001
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  线索"XX项目线索" (2025-11-15, 张三)
    → 客户"华星科技" (2025-11-20)
      → 商机"华星采购项目" ¥12万 (2025-12-01)
        → 合同 CRM-2026-001 ¥12万 (2026-01-15 签约)
          → 回款计划：3 期，已回 1 期 ¥4万
          → 发票：已开 1 张 ¥12万
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏱️ 成交周期：61 天（线索→签约）
  💰 回款进度：33%（¥4万/¥12万）
```

### 4.2 搜索即链路（"搜一下XX"）

当用户用全局模糊搜索时，除了分别展示各模块结果，还自动做关联分析：

```
1. 命中 account → 标注"该客户名下发现 N 个商机"
2. 命中 lead + account → 标注"线索XX可能已转化为该客户"
3. 命中 contract → 标注"回款进度 X%"
```

---

## 7. 工作流参数默认值

| 场景 | viewId | 排序 | 时间范围 |
|------|--------|------|---------|
| 销售看自己 | `SELF` | `followTime:asc` | 不限 |
| 经理看团队 | `ALL` + departmentId | `createTime:desc` | 不限 |
| 高管看全公司 | `ALL` | `signTime:desc` | 不限 |
| 商务看合同 | `ALL` | `signTime:desc` | 不限 |
| 财务看回款 | `ALL` | `planPayTime:asc` | 不限 |
| 今日 | 按角色 | - | `TODAY` |
| 本周 | 按角色 | - | `WEEK` |
| 本月 | 按角色 | - | `MONTH` |

---

## 8. 意图 → 工作流映射

| 用户说 | 触发工作流 | 角色增强 |
|--------|-----------|---------|
| "今天做什么" / "有什么要跟的" | §1.1 晨会速览 | 销售 |
| "这周怎么样" / "周报" | §1.2 周回顾 | 销售/经理 |
| "团队情况" / "部门概览" | §2.1 团队晨会 | 经理 |
| "公司情况" / "经营数据" | §4.1 快照速览 | 高管 |
| "目标怎么样" / "季度预测" | §4.6 月度经营会 / §4.7 季度预测 | 高管 |
| "合同审批" / "审批到哪了" | §5.1 合同审批追踪 | 商务 |
| "合同到期" / "续约" | §5.5 到期预警 | 商务 |
| "批一下" / "待审批" | §2.4 审批巡检 | 经理/财务/高管 |
| "回款情况" / "催款" | §3.2 应收账款 | 财务 |
| "这个月做了多少" | §2.3 月度复盘 | 经理 |
| "看看XX公司" | §1.4 客户深耕 | 全部角色 |
| "查查这笔单子" | §4.1 全链路追踪（通用） | 全部角色 |
| "搜一下XX" / "查找XX" | 全局搜索 + §4.2 | 全部角色 |
