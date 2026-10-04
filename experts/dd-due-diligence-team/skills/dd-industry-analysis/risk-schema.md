# 行业风险要点输出规范

## ⚠️⚠️⚠️ 强制约束：风险要点必须严格使用"等级+类别+标题+证据+建议"表格形态 ⚠️⚠️⚠️

> **这是不可违反的硬性规则**：风险要点的 HTML 输出必须使用 `<table>` 表格渲染，每一行对应一条风险，
> 列固定为：等级 | 类别 | 标题 | 证据 | 建议。**禁止使用 `<ul>/<li>` 列表结构，禁止使用卡片式布局。**

## 风险要点 JSON 结构

```json
{
  "level": "medium",
  "category": "market",
  "title": "价格战：组件均价同比 -22%",
  "detail": "2024 年组件均价降至 0.8 元/W，同比 -22%，二三线企业盈利承压。[IEA · P.42]",
  "suggest": "关注企业成本曲线与现金储备，评估价格战持续 12 个月的生存能力。"
}
```

## 字段规范

| 字段     | 类型                                  | 必填 | 说明                                                                                       |
| -------- | ------------------------------------- | ---- | ------------------------------------------------------------------------------------------ |
| level    | `high` \| `medium` \| `low` \| `note` | ✓    | 风险等级                                                                                   |
| category | string                                | ✓    | 归属维度：`market` / `competition` / `policy` / `technology` / `supply_chain` / `capacity` |
| title    | string                                | ✓    | 一句话风险描述（≤ 30 字）                                                                  |
| detail   | string                                | ✓    | 支撑证据（引用具体数据 + 数据来源 `[文献名 · P.页码]`）                                    |
| suggest  | string                                | ✓    | 建议动作（补充材料 / 现场核查 / 关注不作决策）                                             |

## 风险等级定义

| level  | 含义     | 触发条件示例                                                     |
| ------ | -------- | ---------------------------------------------------------------- |
| high   | 高风险   | 命中制裁名单 / 行业进入衰退期 / CR5 > 90% 寡头垄断且本企业不在内 |
| medium | 中风险   | 增速连续 2 年下降 / 贸易壁垒升级 / 产能开工率 < 70%              |
| low    | 低风险   | 增速略放缓 / 技术路线存在替代可能但非紧迫                        |
| note   | 关注提示 | 建议补充材料 / 数据滞后提醒（不构成风险）                        |

## category 维度

| category     | 对应 E 维度 | 示例                           |
| ------------ | ----------- | ------------------------------ |
| market       | E1/E2       | 市场规模萎缩 / 增速下降        |
| competition  | E5          | 价格战 / 寡头垄断 / 新进入者   |
| policy       | E4          | 贸易壁垒 / 补贴退坡 / 环保收紧 |
| technology   | E3          | 技术替代 / 路线迭代            |
| supply_chain | E8          | 上游集中度过高 / 下游客户集中  |
| capacity     | E1/E3       | 产能过剩 / 开工率低            |

## 数量要求

- 最少 3 条，最多 8 条
- 至少覆盖 2 个不同的 category
- high 级别的风险要点必须有明确的 suggest

## ⚠️ risks.html 输出格式（表格形态，强制执行）

**risks.html 必须使用 `<table>` 表格渲染，严禁使用列表。** 表头固定为：等级 | 类别 | 标题 | 证据 | 建议。

示例：

```html
<div class="analysis-risk-points">
  <table class="analysis-risk-points__table">
    <thead>
      <tr>
        <th>等级</th>
        <th>类别</th>
        <th>标题</th>
        <th>证据</th>
        <th>建议</th>
      </tr>
    </thead>
    <tbody>
      <tr class="analysis-risk-points__row analysis-risk-points__row--high">
        <td>
          <span class="analysis-risk-points__level analysis-risk-points__level--high">高</span>
        </td>
        <td>policy</td>
        <td>集采政策影响</td>
        <td>仿制药价格年均下降 15%，集采范围持续扩大 [NMPA · 2024年集采公告]</td>
        <td>关注企业创新药占比提升进度</td>
      </tr>
      <tr class="analysis-risk-points__row analysis-risk-points__row--medium">
        <td>
          <span class="analysis-risk-points__level analysis-risk-points__level--medium">中</span>
        </td>
        <td>capacity</td>
        <td>产能过剩风险</td>
        <td>部分环节开工率低于 70% [CPIA · 2025报告 · P.28]</td>
        <td>关注企业产能利用率与去库存节奏</td>
      </tr>
    </tbody>
  </table>
</div>
```
