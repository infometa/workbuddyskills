# 分析报告字段

来源为 `get_viral_analysis` / `get_viral_analysis_request` 返回的 `job`，不从页面标题推导缺失内容。生成提示词读取同一响应顶层的 `generated_prompt`。

| 展示内容 | 字段 |
| --- | --- |
| 任务与来源 | `id`、`status`、`platform`、`sourceInput`、`sourceUrl`、`jobKind` |
| 视频规格 | `analysisResult.videoInfo` 的 `duration`、`resolution`、`coverUrl`、`videoUrl`；可补充任务实际 `videoDuration` / `videoResolution` |
| 内容策略 | `analysisResult.analysis` 的 `hookType`、`hookStrategy`、`visualPacing`、`productDemoMethod`、`ctaStyle`、`successFactors`、`detectedLanguage` |
| 逐镜拆解 | `analysisResult.scriptBreakdown.scenes` 原顺序：`startSeconds`、`endSeconds`、`sceneType`、`visualDirection`、`voiceover`、`textOverlay`、`notes` |
| 生成提示词（必展示） | 响应顶层 `generated_prompt`；主站共享 `buildVideoPromptFromAnalysis` 组装的文本，独立代码块完整原样展示，不重写、不翻译；空值说明未提供 |
| 音乐方向 | `analysisResult.scriptBreakdown.musicDirection` |
| 平台公开数据 | `analysisResult.platformMeta` 或任务 `platformMeta` 中的作者、发布时间、标签与 `statistics`；TikTok 专用字段在 `analysisResult.tiktokMeta` |
| 费用与结算 | `estimatedCredits`、`consumedCredits`、`entitlement`、`refundedAt`；未知状态不能推断已退款 |
| 错误 | `errorZh` / `errorEn`，只报告实际返回信息 |

建议报告顺序：视频概况 → 摘要 → 开头钩子与内容策略 → 时间轴分镜表 → 平台数据 → 创意启发 → 生成提示词 → 缺失字段与实际结算。创意启发若由 Agent 归纳，须明确标为建议，并对应已有分析证据。原始口播与字幕保留原语言，不调用翻译工具。`metadata_only` 报告没有 AI 拆解时如实说明，不编造 `analysis` 或 `scriptBreakdown`。

生成提示词沿用主站最多 10 个场景、4500 字符的组装限制，服务端文本若带截断说明须保留；“完整展示”指完整照录返回文本。不得因此截断前面的完整分镜报告，也不把这段提示词视为再次生成视频的授权。
