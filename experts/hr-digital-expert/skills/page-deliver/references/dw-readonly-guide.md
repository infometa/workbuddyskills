# dw-readonly 模板 Plan 编写指南

> 当 `needs_dw=true` 时，Task "填充数仓 SQL" 应遵循以下约定。
> 本文档由 `writing-plans.md` 在 `needs_dw=true` 时引用。

## 数据加载架构

**必须**使用 `batchQueryDW` 并行查询，禁止串行 await 多个 queryDW：

```
✅ 正确：
  const data = await batchQueryDW([
    ['ageDist', 'SELECT age_range, COUNT(*) cnt FROM ... GROUP BY age_range'],
    ['levelDist', 'SELECT pro_position_level_name, COUNT(*) cnt FROM ... GROUP BY ...'],
  ]);

❌ 错误：
  const ageData = await queryDW('SELECT ...');
  const levelData = await queryDW('SELECT ...');
```

## 首屏 vs 渐进渲染

Plan 中应区分两类数据的加载时机：

| 数据类型 | 加载阶段 | 示例 |
|----------|----------|------|
| 首屏数据 | `loadData()` 返回前必须完成，阻塞渲染 | 概览卡片（总人数、平均年龄） |
| 渐进数据 | `loadData()` 返回后 `nextTick` + 渲染 | ECharts 图表、明细表格 |

Plan 的 Step 中应明确标注每个查询属于哪一类，避免 Agent 自行拆分成两个数据加载阶段。

## 状态机策略

Plan 应说明各状态的页面表现：
- **loading**: 全屏 spinner（模板已内置，只需在 `loadData` 中查询）
- **error**: 错误信息 + 重试按钮（模板已内置 `initPage` 自动切换）
- **empty**: 空数据提示（模板已内置，`loadData` 返回 `false` 时自动切换）
- **done**: 正常数据展示

Plan 不需要为这些状态单独写 CSS/HTML，模板已提供。

## 图表渲染

Plan 中图表渲染 Step 的写法示例：

```
**Step N: 渲染年龄分布图表**

使用模板内置的 useChart + buildBarOption：
- chart = useChart('ageDistChart')
- chart.render(buildBarOption(labels, series))

验证：页面上可见年龄分布柱状图，数据标签显示人数
```

## 验证 Step 要求

数仓 Task 的验证 Step 必须包含：
1. 用 MCP `starrocks_query` 验证 SQL 语法正确
2. 确认查询返回了预期的列（`age_range`, `cnt` 等）
3. 确认列名与后续 transform 逻辑一致（不要在代码里用 `col_0` 硬编码）
