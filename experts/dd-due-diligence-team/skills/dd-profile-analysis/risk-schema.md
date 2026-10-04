# dd-profile-analysis 风险要点输出规范

## ⚠️⚠️⚠️ 强制约束：风险要点必须严格使用"等级+类别+标题+证据+建议"表格形态 ⚠️⚠️⚠️

> **这是不可违反的硬性规则**：风险要点的 HTML 输出必须使用 `<table>` 表格渲染，每一行对应一条风险，
> 列固定为：等级 | 类别 | 标题 | 证据 | 建议。**禁止使用 `<ul>/<li>` 列表结构，禁止使用卡片式布局。**

## 风险要点 JSON 结构（工作空间 profile/risks.json）

```json
[
  {
    "level": "high",
    "category": "股权",
    "title": "风险标题（≤30字）",
    "detail": "支撑证据（具体数据+来源文件名）",
    "suggest": "建议措施（可操作的具体动作）"
  }
]
```

## 字段规范

| 字段     | 类型                                  | 必填 | 说明                                       |
| -------- | ------------------------------------- | ---- | ------------------------------------------ |
| level    | `high` \| `medium` \| `low` \| `note` | ✓    | 风险等级                                   |
| category | string                                | ✓    | 归属类别（见下方分类表）                   |
| title    | string                                | ✓    | 一句话风险描述（≤30字）                    |
| detail   | string                                | ✓    | 支撑证据（引用具体数据+数据来源文件名）    |
| suggest  | string                                | ✓    | 建议动作（补充材料/现场核查/关注不作决策） |

## 风险等级定义

| 等级   | 含义   | 触发条件                                                   |
| ------ | ------ | ---------------------------------------------------------- |
| high   | 高风险 | 涉及实控人变更、重大诉讼、失信记录、股权冻结等实质性风险   |
| medium | 中风险 | 关联交易占比偏高、治理结构不完善、行业竞争加剧等需关注事项 |
| low    | 低风险 | 轻微负面信息、常规经营变动                                 |
| note   | 关注   | 信息补充，不构成风险                                       |

## 风险分类（category 取值）

| 类别 | 示例                                 |
| ---- | ------------------------------------ |
| 股权 | 股权结构复杂、实控人不清晰、代持风险 |
| 征信 | 逾期记录、担保圈、融资集中度         |
| 关联 | 关联交易占比高、关联方风险传导       |
| 变更 | 工商变更频繁、经营范围变更           |
| 负面 | 涉诉、失信、行政处罚                 |
| 治理 | 高管变动频繁、治理结构缺陷           |
| ESG  | 环境处罚、安全事故、社保欠缴         |

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
        <td>股权</td>
        <td>实控人认定存疑</td>
        <td>股权穿透后无法确认最终受益人，存在代持嫌疑（来源：股权结构图）</td>
        <td>建议要求提供代持协议或实控人承诺函</td>
      </tr>
      <tr class="analysis-risk-points__row analysis-risk-points__row--medium">
        <td>
          <span class="analysis-risk-points__level analysis-risk-points__level--medium">中</span>
        </td>
        <td>关联</td>
        <td>关联交易占比偏高</td>
        <td>关联交易占营收 42%，超过 30% 阈值（来源：审计报告 P.15）</td>
        <td>关注关联交易定价公允性，要求提供转让定价报告</td>
      </tr>
    </tbody>
  </table>
</div>
```
