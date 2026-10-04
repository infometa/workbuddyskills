# dd-profile-analysis 输出规范

## 输出目录：工作空间 profile/

## 文件清单（每个 section 一对 .md + .html，共 13 个文件）

| 文件                   | 类型    | 说明                                                       |
| ---------------------- | ------- | ---------------------------------------------------------- |
| overview.md / .html    | MD+HTML | 概况：工商基本信息、主营业务、客户标签、资质证书、知识产权 |
| equity.md / .html      | MD+HTML | 股权结构：股东表、持股比例                                 |
| controller.md / .html  | MD+HTML | 实控人：认定结果、依据                                     |
| related.md / .html     | MD+HTML | 关联方：清单、关联交易、财务快照                           |
| governance.md / .html  | MD+HTML | 高管治理：团队表、治理评级、指标                           |
| events.md / .html      | MD+HTML | 重大事项：日期、描述、类型（ok/warn/info）                 |
| credit.md / .html      | MD+HTML | 征信融资：征信详情、融资历史                               |
| changes.md / .html     | MD+HTML | 工商变更：历史变更列表                                     |
| negative.md / .html    | MD+HTML | 负面信息：涉诉、失信、行政处罚                             |
| cooperation.md / .html | MD+HTML | 与本行合作：历史合作记录                                   |
| esg.md / .html         | MD+HTML | ESG 评价：评分、各维度详情                                 |
| collateral.md / .html  | MD+HTML | 押品资产：资产清单                                         |
| risks.json             | JSON    | 风险要点（数组）                                           |

## HTML class 约束（必须在模板中使用的 class）

### 主容器

```html
<div class="pcf-section">...</div>
```

### 指标卡片

```html
<div class="pcf-section__metrics">
  <div class="pcf-section__metric">
    <div class="pcf-section__metric-label">标签</div>
    <div class="pcf-section__metric-value">
      数值<span class="pcf-section__metric-unit">单位</span>
    </div>
  </div>
</div>
```

### 网格字段

```html
<div class="pcf-section__grid">
  <div class="pcf-section__field">
    <div class="pcf-section__label">字段名</div>
    <div class="pcf-section__value">字段值</div>
  </div>
</div>
```

### 数据块

```html
<div class="pcf-section__data-block">
  <table>
    ...
  </table>
</div>
```

### 研判块

```html
<div class="pcf-section__insight">
  <div class="pcf-section__insight-title">标题</div>
  <div class="pcf-section__insight-item pcf-section__insight-item--ok">ok</div>
  <div class="pcf-section__insight-item pcf-section__insight-item--warn">warn</div>
  <div class="pcf-section__insight-item pcf-section__insight-item--info">info</div>
  <div class="pcf-section__insight-item pcf-section__insight-item--risk">risk</div>
</div>
```

### 评级

```html
<div class="pcf-section__rating">
  <div class="pcf-section__rating-num">87<small>/100</small></div>
  <div class="pcf-section__rating-tier">A</div>
  <div class="pcf-section__rating-note">说明</div>
</div>
```

### 摘要 / 补充

```html
<div class="pcf-section__summary">摘要文字</div>
<div class="pcf-section__supplement">补充说明</div>
```

### 数据来源文件溯源（必须）

每个 section 的 HTML **末尾必须**包含文件溯源区块，列出该 section 数据所依赖的进件文件。

```html
<div class="pcf-section__source">
  <div class="pcf-section__source-title">数据来源文件</div>
  <div class="pcf-section__source-list">
    <span class="pcf-section__source-item">营业执照.pdf</span>
    <span class="pcf-section__source-item">公司章程.pdf</span>
    <span class="pcf-section__source-item">征信报告.pdf</span>
  </div>
</div>
```

- **必须列出该 section 实际使用到的所有进件文件**，以精确文件名为单位（如 "营业执照.pdf"、"企业年报2025.pdf"）
- **禁止使用概括性描述**（如 "企业年报"、"现场调查"），必须使用进件文件的精确文件名
- 文件列表用 `<span class="pcf-section__source-item">` 标签包裹
- 如果多个 section 共用同一批文件，每个 section 也要独立列出
- 风险要点(risks.json)不需要此溯源区块
- **禁止使用 `pcf-section__evidence` 证据链块**，统一使用 `pcf-section__source` 文件溯源块

## HTML 禁止项

- ❌ 禁止 `<!DOCTYPE html>`、`<html>`、`<head>`、`<body>`、`<style>`、`<script>`
- ❌ 禁止自创 CSS class（只能使用上述 pcf-section__* class）
- ❌ HTML 必须是片段，不是完整文档
