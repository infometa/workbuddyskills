---
name: xmed-figure-mcp
description: "Scientific figure generation via X-Med MCP. Volcano, PCA, enrichment, survival, correlation. CSV/Excel upload, chart matching, parameter configuration, publication-grade multi-panel."
description_zh: "科研数据可视化：火山图、PCA、富集分析、生存分析，自动匹配发表级输出"
description_en: "Scientific visualization: volcano, PCA, enrichment, survival, and more."
version: 1.0.10
homepage: https://x-med-kyy.dazd.cn
source_type: git
git_url: https://gitlab.dazd.cn/yusm1/xmed-figure-expert.git
---

# 迪安智能科研云 MCP 连接器

> **MCP 连接器**：`xmed-figure-mcp` | 出品方：迪安诊断科研云智能分析平台 | 官网：https://x-med-kyy.dazd.cn

通过智能科研云 MCP 生成科研数据可视化图表。本连接器提供 4 个 MCP 工具，配套的科研绘图专家提供完整的脚本工作流（数据上传、格式转换、结果下载、多面板组图）。

## 1. 图表类型与意图判定

从用户意图匹配 `chartType`，判定优先级：**1.1 场景关键词 → 1.2 歧义消解 → 1.3 数据驱动推断 → 1.4 索引表精确确认**。

### 1.1 场景关键词 → chartType 映射

当用户未明确指定图表名称时，根据分析场景关键词推断候选图表类型：

| 场景关键词 | 候选 chartType | 优先级 |
|-----------|---------------|:--:|
| 差异表达 / 差异分析 / 上调下调 / log2FC / pvalue | volcano | 1 |
| 降维 / 聚类 / 分群 / 样本分布 | pca | 2 |
| 富集分析 / GO / KEGG / 通路 / 功能注释 | enrich_bar, enrich_bubble, enrich_point | 1 |
| 相关性 / 相关系数 | cor_pheatmap, cor_matrix, correlation_network | 2 |
| 韦恩 / 交集 / 并集 | venn, upset | 1 |
| 生存分析 / 生存曲线 / KM | km_risk_table | 1 |
| 随时间变化 / 趋势 / 时间序列 | dotline_columns, stacked_area, gantt | 2 |
| 分类 / 占比 / 组成 | donut, stacked_area | 2 |
| 比较 / 差异 / 对比 | bilateral_bar, dumbbell | 2 |
| 模型评估 / 分类器 / 诊断 | roc, nomogram | 1 |
| 网络 / 关系图 | correlation_network, sankey_diagram | 2 |

### 1.2 歧义消解

当多个候选命中同一优先级时，**展示 Top 2~3 候选的中文名 + 一句话描述让用户选择**，不要自行决定。

示例：
> "您提到'看相关性'，匹配到：① 相关性热图（通过颜色梯度展示变量之间相关性）② 相关性矩阵图（展示多个变量之间两两相关性）③ 相关性网络图（展示变量之间相关性关系），您想用哪个？"

### 1.3 数据驱动推断

当用户上传了数据文件但未指定图表类型时，根据文件名关键词推断：

| 文件名关键词 | 推断 chartType |
|-------------|---------------|
| `*deg*` / `*diff*` / `*差异*` / `*DE*` | volcano |
| `*go*` / `*kegg*` / `*enrich*` / `*富集*` | enrich_bar, enrich_bubble, enrich_point |
| `*survival*` / `*生存*` | km_risk_table |
| `*correlation*` / `*cor*` / `*相关*` | cor_pheatmap, cor_matrix |
| `*venn*` / `*韦恩*` | venn |
| `*pca*` / `*降维*` | pca |

### 1.4 图表类型索引表

精确匹配或确认后，从此表获取 `chartType` 和完整描述：

| 图表名称 | chartType | 描述 |
|----------|-----------|------|
| 火山图 | volcano | 通过散点的位置和颜色展示差异分析结果 |
| 样本-鉴定柱形图 | protein_number | 通过柱形高度展示样本特征或鉴定结果 |
| PCA | pca | 通过降维呈现样本间的相似性和分组结构 |
| 组-CV柱形图 | cv_analysis | 通过柱形高度表示不同组别的数据变异程度 |
| 相关性热图 | cor_pheatmap | 通过颜色梯度展示变量之间相关性 |
| 富集条形图 | enrich_bar | 通过条形长度和颜色展示功能富集分析结果 |
| 富集气泡图 | enrich_bubble | 通过气泡的大小、颜色和位置展示功能富集分析结果 |
| 富集-点图 | enrich_point | 通过点的大小、颜色和位置展示功能富集分析结果 |
| 桑基图 | sankey_diagram | 描述数据的流动、转换、变化过程 |
| 韦恩图 | venn | 用图形直观表示集合之间逻辑关系 |
| 哑铃图 | dumbbell | 比较同一组数据在两个不同条件下的变化情况 |
| 分层聚类图 | cluster_tree | 展示数据层次聚类结果 |
| 堆叠面积图 | stacked_area | 显示不同物种在特定区域内的分布和相对数量 |
| 双向柱状图 | bilateral_bar | 比较方向相反的两组数据 |
| 甘特图 | gantt | 展示项目的进度和成果 |
| 圆环图 | donut | 展示数据的占比关系 |
| 交集关系图 | upset | 通过矩阵布局展示集合的交集大小 |
| 三元组图 | ternary | 以三元组形式表示的关系图 |
| 相关性矩阵图 | cor_matrix | 展示多个变量之间两两相关性 |
| 诺莫图 | nomogram | 将多因素回归分析结果可视化 |
| 分组蜂群图 | beeswarm | 可视化分类数据分布 |
| 分组直方图 | grouped_histogram | 展示多个组数据分布 |
| KM生存分析图 | km_risk_table | 展示不同组别随时间推移的生存概率变化 |
| 雷达图 | radar | 比较多变量数据 |
| ROC 曲线图 | roc | 评估二分类模型预测性能 |
| 散点图 | scatter | 展示两个连续变量之间的关系 |
| 四象限图 | four_quadrant | 分析和比较两个变量关系 |
| 线性回归 | linear_regression | 展示两个变量间线性关系 |
| 点线图 | dotline_columns | 结合数据点与连线 |
| 相关性网络图 | correlation_network | 展示变量之间相关性关系 |

### 1.5 无匹配处理

如果经过 §1.1~§1.4 仍无法匹配到合适的 chartType，**不要自行猜测或强行选择**。向用户明确说明当前支持的图表类型中未找到直接匹配，请用户描述数据维度和分析目的，根据补充重新匹配。

---

## 2. MCP 工具

### `get_chart_input_files`

| 参数 | 类型 | 必填 |
|------|------|------|
| chartType | string | ✅ |

返回 `{inputFiles: [{dataFileName, showFileName}], uploadKey, uploadExpire}`

### `submit_analysis_task`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chartType | string | ✅ | 图表代号 |
| files | map\<string,string\> | ❌ | `{dataFileName: fileId}`；存在时走新实例 |
| instanceId | string | ❌ | 仅在 files 为空时生效；复用已有数据仅重新调参 |
| params | map\<string,object\> | ❌ | 图表参数 JSON |

返回 `{taskId, instanceId, status: "SUMMITED", nextAction, instruction}`

### `wait_for_task`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | string | ✅ | |
| waitSeconds | number | ❌ | 默认 25，上限 25 |

| 返回 status | 含义 |
|-------------|------|
| `ANALYSIS` | 继续轮询 |
| `FINISHED` | 终态，含 `results` URL 数组 |
| `FAILED` | 终态，含 `failReason` |

### `get_task_result`

| 参数 | 类型 | 必填 |
|------|------|------|
| taskId | string | ✅ |

立即返回 `{status, results, failReason, taskDetail}`

---

## 3. 错误处理

### 任务状态

| 状态 | 终态 |
|------|:--:|
| SUMMITED | 否 |
| ANALYSIS | 否 |
| FINISHED | ✅ |
| FAILED | ✅ |

### 错误码与自愈

| 错误码 | 动作 |
|--------|------|
| `UNKNOWN_CHART` | 不要自行猜测或强行选择；引导用户从 §1.4 索引表中重新选择 |
| `NO_INPUT` | 提示用户上传文件或提供历史 instanceId |
| `INPUT_FILES_INCOMPLETE` | 对照 `inputFiles`（含 `showFileName` 中文名）向用户补收缺失文件 |
| `INVALID_PARAMS_JSON` | 检查参数 JSON 格式后重试 |
| `TASK_NOT_FOUND` | 确认 taskId 或重新提交 |
| `UPSTREAM_ERROR` | 告知后端系统异常，建议稍后重试 |
| `MCP_UNAVAILABLE` | MCP 服务不可达时提示用户检查网络，稍后重试，或联系管理员 |