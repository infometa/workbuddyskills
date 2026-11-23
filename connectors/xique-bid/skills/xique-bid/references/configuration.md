# Configuration reference

## Required mappings

| 中文配置 | MCP value | xq-cli |
|---|---:|---|
| 极短篇（50–100页） | 极短篇 | `--page-scope -1` |
| 超短篇（100–200页） | 超短篇 | `--page-scope 0` |
| 短篇（200–350页） | 短篇 | `--page-scope 1` |
| 中篇（350–500页） | 中篇 | `--page-scope 2` |
| 中长篇（500–800页） | 中长篇 | `--page-scope 3` |
| 长篇（800–1200页） | 长篇 | `--page-scope 4` |
| 超长篇（1200–1500页） | 超长篇 | `--page-scope 5` |
| 标准写作 | 标准 | `--writing-quality 0`（同时 `--base 0`） |
| 专家智笔 | 专家智笔 | `--writing-quality 1`（同时 `--base 1`） |
| 旗舰智笔 | 旗舰智笔 | `--writing-quality 2`、`--base 0`、`deepThinkingFlowVersion=1` |
| 增强图文 | 增强图文 | `--theme-style 1` |
| 全表格式 | 全表格式 | `--theme-style 2` |
| 丰富图文 | 丰富图文 | `--theme-style 3` |
| 基础配图 | 基础配图 | `--theme-style 4` |
| 纯文字 | 纯文字 | `--theme-style 5` |
| 表格无/少量/丰富 | 同名中文值 | `--table-quantity 0/1/2` |
| 合并式响应 | 候选依据阶段选择 | `plan reference-select --reference-type 0` |
| 仅格式要求 | 候选依据阶段选择 | `plan reference-select --reference-type 1` |
| 仅评分要求 | 候选依据阶段选择 | `plan reference-select --reference-type 2` |
| 模板1｜章节目次（第一章→第一节→一、） | 模板1 | `--template 1` |
| 模板2｜中文层级（一、→（一）→1） | 模板2 | `--template 2` |
| 模板3｜全数字分级（1→1.1→1.1.1） | 模板3 | `--template 3` |
| 模板4｜章节+数字（第一章→1→1.1） | 模板4 | `--template 4` |
| 模板5｜自定义编号（可视化设置） | 配置卡和导出设置卡可用 | 选择后展开五级标题、正文四级编号、字体、字号、对齐、加粗、分页/换行和起始值；生成结构化编号配置，不要求用户填写 JSON |
| 常规/全表/精排 | 同名中文值 | `--layout 0/1/2` |

## Optional mappings

- 表格颜色：黑色、蓝色、红色、绿色、紫色、青色、橙色。
- 表格样式：纯净版、表头强化、斑马条纹、全底色白框。
- WorkBuddy 计划模式必须展示 `快速/规划`。配置消息有该字段时原样提交给 `--plan-mode`（规划=`1`、快速=`0`）；只有字段缺失时才默认快速。
- 自动编号、修改标记和图片开关：开启、关闭。
- 图片开关：我的图库=`knowledgeImg`，但仅当 `xique_gallery_status` 返回
  `available=true` 时可开启；图库为空或查询失败时仍展示该项但固定为关闭。
  实拍风格图同时控制 `sceneImg` 和 `onlineImg`；PPT式插图=`infoImg`；
  流程图=`mermaidImg`。不要单独展示联网搜图。
- 流程图样式：灰色、紫色、蓝色、绿色、橙色、红色。
- WorkBuddy 首次标书配置卡将实拍风格图、PPT式插图、联网搜图、我的图库和流程图等图片来源直接展示，用户打开配置页即可选择；表格样式、表格颜色、流程图样式、导出模板、模板5自定义编号、导出布局、自动编号、修改标记、页边距和图片尺寸统一放在默认收起的“导出格式设置”中，默认值会直接生效，只有需要调整时再展开。
- 选择模板5后，“模板5自定义编号”字段会在“导出格式设置”中显示；模板1-4不会要求填写这些字段。
- 正文完成后的二次导出设置卡保留同样的编号、页边距和图片尺寸字段，可修改后重新下载。
- 页边距支持上/下/左/右四项（cm）；图片尺寸支持横向宽度/最大高度、纵向宽度/最大高度（cm）。

## Explicit default profile

Use this profile only after the user explicitly authorizes defaults:

- 篇幅=短篇
- 写作质量=标准写作
- 风格=基础配图
- 表格=丰富
- 响应依据：等待后台生成候选目录后，在独立依据选择卡中选择（通常推荐合并式响应）
- 表格颜色=蓝色
- 表格样式=纯净版
- 计划模式=快速
- 图片设置=基础配图默认（仅流程图开启）
- 导出=模板1+常规
- 自动编号=开启
- 修改标记=关闭
- 输出路径=默认

## Issue bypasses

These values default to `false` and require exact user authorization:

- `ignoreShortRequirement`: ignore a short requirement section.
- `ignoreMissingBill`: continue without a bill of quantities.
- `ignoreMissingScore`: continue without scoring criteria.
- `ignoreDirectoryBasis`: continue without directory basis.

Never turn on several bypasses because the user approved only one.
