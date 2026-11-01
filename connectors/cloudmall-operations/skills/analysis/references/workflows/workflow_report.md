# Workflow — 报告工作流

> L3 完整报告 · HTML → PDF · 存入 本地工作目录 · 1~5 分钟
> 前置条件：本技能报告路由判定为 L3（固定模板或动态报告）
> 新增报告类型：路由表加一行 + schema_examples/ 加一个 JSON + report_plugins/ 加一个 py

---

## 报告路由

根据用户触发词匹配能力编号，确定 capability_id 和 SQL 序列后进入执行步骤：

| 能力 | capability_id | 触发词 | SQL 序列 | 说明 |
|------|--------------|--------|---------|------|
| 经营日报 | 3 | 经营日报/出日报/发日报 | Q-1 → A-2 → Q-4 → Q-2 | 昨日KPI + 漏斗 + 用户结构 + 品类 |
| 日常经营看板 | 1 | 经营周报/经营月报/经营报告 | Q-1 → A-2 → A-3 | 大盘KPI + 同环比 + 逐日趋势 |
| 门店分析报告 | 2 | 门店对标/区域对标/门店报告 | Q-3 → A-8 | 门店排行 + 门店效率对比 |

---

## 执行步骤

```
1. 确认参数
   → 匹配路由表得到 capability_id + SQL 序列
   → 确认时间范围（调 date '+%Y%m%d'（服务端编码形态）或 scripts/encode_sql.py --today（本地编码形态））、环比期、输出路径（demo-reports/{能力名}-{日期}/）
   → 确定报告文件名：云Mall商城_{报告标题}_{yyyyMMdd}（如 云Mall商城_经营周报_20260422）

2. 向用户说明即将执行的内容（说明后立即执行，不等确认）
   → 报告名称 + 分析维度 + 输出路径

3. 执行 SQL + 收集结果
   → 读 references/sql_templates_Q.md / references/sql_templates_A.md 获取 SQL 模板
   → 按路由表 SQL 序列通过 当前运行时的 Capability 分析执行器(action=sql_batch)（本地编码形态参数由 encode_sql.py --batch 生成，服务端编码形态明文直传）一次性提交，保留返回结果
   → 查询前检查：dim_type WHERE 条件、activity_type 空数据、品类退款用 SPU 表
   → SQL 报错时：① 先重新调 当前运行时的 Capability 分析执行器(action=table_structure)查表结构确认字段 ② 再读 references/sql-few-shots.md（最多修正重试 1 次）

4. 组装 JSON（先读 references/gate_check_rules.md；审查完整性、漏斗、率值、对比期、截断与缺失，保存自审结论，未通过时标注限制）
   → 读 references/domains/trade/schema_examples/cap_{capability_id}.json
   → 按示例结构将 SQL 结果填入对应 key，补充 meta 和文案字段
   → 保存为 {输出目录}/report_data.json

5. 生成分析概览（Markdown，先输出给用户）
   → 从 report_data.json 提取，不额外执行 SQL
   → 包含：
     ① 一句话总结（核心结论 + 关键变化 + 需关注的风险）
     ② 3~4 个核心 KPI（含环比变化）
     ③ 异常提醒（基于异常波动阈值筛选，有异常都需给出，上限 12 条）

6. 生成报告（HTML → PDF，存入本地工作目录）
   → 调用技能脚本：
     Bash: python3 "<技能目录>/scripts/generate_report.py" --data-file "<本地输出目录>/report_data.json" --output-dir "<本地输出目录>" --name "report"
   → 该脚本自动完成：
     ① ecommerce_report.py: JSON → HTML
     ② html2pdf.js: HTML → PDF（失败则跳过，降级使用 HTML）
   → 文件写入用户当前本地工作目录；交付脚本实际返回的绝对路径 Markdown 链接。
   → 文件写入用户当前本地工作目录；交付脚本实际返回的绝对路径 Markdown 链接。
```
