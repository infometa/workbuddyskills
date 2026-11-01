# Workflow — 快速问答

> 适用档位：L2 场景分析 / L2 归因诊断（L1 简单取数由 system prompt 路由自执行，本 workflow 不处理 L1）
> 输出格式：Markdown 表格 + 文字解读
> 前置条件：system prompt 路由判定为 L2，domain / tier / time_expr 已确定

---

## 场景路由（L2 专用，读完再进入执行步骤）

L1 快速查数不需要路由，直接进入步骤 1。

L2 按触发词匹配命中场景后，读对应 scene 文件（含 SQL 组合 + 诊断规则 + 建议模板），再进入步骤 1：

| 场景 | 触发词 | 读取文件 |
|------|--------|---------|
| 经营概览（日/周/月） | 日报、今天表现、昨天怎么样、周报快览、上周表现、这周怎么样、月报快览、本月表现、这个月怎么样 | `references/scenes/scene_1_daily.md` |
| 流量下钻 | 流量分析、PV UV、渠道流量、引流效果 | `references/scenes/scene_2_traffic.md` |
| 支付下钻 | 支付分析、GMV 拆解、订单分析 | `references/scenes/scene_3_payment.md` |
| 用户下钻 | 用户分析、新老客、用户画像、用户结构 | `references/scenes/scene_4_user.md` |
| 商品下钻 | 商品分析、品类表现、品类转化、SPU 分析 | `references/scenes/scene_5_commodity.md` |
| 营销下钻 | 营销分析、活动效果、优惠券分析 | `references/scenes/scene_6_marketing.md` |
| 分销下钻 | 分销分析、推广效果、佣金分析 | `references/scenes/scene_7_cps.md` |
| 归因诊断 | GMV 为什么跌/涨、下降原因、业绩下滑、品类为什么跌、用户为什么少了、留存下降、复购下降、渠道为什么跌、转化率为什么降、客单价为什么降、退款率为什么涨/降、退款原因、退款集中在哪 | `references/scenes/scene_8_attribution.md` |

---

## 执行步骤

```
1. 确认参数
   → 业务域（domain）、查询表（按 SKILL.md 域路由查询表确认）、时间范围（调 Bash 获取日期后按 time_expr 换算）、筛选条件（filters）
   → 按上方场景路由表匹配 scene 文件，读取 SQL 组合 + 诊断规则 + 建议模板，再进入步骤 2

2. 输出分析计划（3~5 行，输出后立即执行，不等用户确认）
   → 说明识别到的问题分类（L1/L2 + 业务域 + 具体场景名）
   → 列出将执行的 SQL 模板编号和数量（如"Q-1 + A-2 + A-3，共 3 条"）
   → 列出核心指标口径，标注来源为"用户指定"或"系统默认"

3. 执行 SQL
   → 先调 当前运行时的 Capability 分析执行器(action=table_structure)确认表结构和字段，只用返回的字段写 SQL
   → L2 场景分析：读 references/sql_templates_A.md，按场景文件的 SQL 组合执行 2~4 条
   → L2 归因诊断：读 references/sql_templates_D.md，按场景文件的 SQL 组合执行 2~4 条
   → 将互相独立的 SQL 合并为一次 当前运行时的 Capability 分析执行器(action=sql_batch)（本地编码形态参数由 encode_sql.py --batch 生成，服务端编码形态明文直传）；依赖前序结果的 SQL 分批提交
   → SQL 报错时读 references/sql-few-shots.md 获取 6 类错误修正方法（最多修正重试 1 次）
   → 查询前检查：tag_type WHERE 条件、activity_type 空数据、品类退款用 SPU 表

4. Markdown 回复（概览 + 图表 + 诊断 + 建议）
   → ① 输出前准备：参考 references/chart-protocol.md 了解图表数据结构（本技能的对话输出不使用 XML 标签，改用 Markdown 表格呈现）
   → ② 数值格式化：金额保留 2 位小数 + 千分位（如 12,345.67 元）；百分比 1~2 位小数 + "%"；整数用千分位（如 1,234 人）
   → ② 数据概览：按 scene 文件的输出结构组织数据，用 Markdown 表格呈现（不使用 XML 标签）
   → ③ 分析诊断：按 scene 文件的诊断规则扫描信号，命中的输出诊断结论，未命中的跳过
   → ④ 优化建议：按 scene 文件的建议模板，选取 2~3 条最相关的输出
   → 数据为空的角度/维度跳过并标注原因（如"用户分群数据暂无，跳过"）
   → 基本校验：漏斗自洽、率值 ≤ 1.0、关键指标非零；异常标注 ⚠️，不中止回复

5. 支持追问
   → 追问：+1~2 条 SQL，复用已有上下文，逐步加深分析
   → 用户明确说"出一份报告" → 升级到 L3，复用已查数据
```

> L1 快速取数由 system prompt 路由自执行，本 Skill 不涉及。
