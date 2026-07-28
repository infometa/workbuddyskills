---
name: infimind-video-analysis
display_name: 极睿视频分析
display_name_en: Infimind Video Analysis
description: 对用户主动提供的视频执行结构化拆解，安全创建分析任务、跟踪状态并交付脚本、风格、卖点和可复用提示词。
description_zh: 适用于极睿视频的商品视频拆解、品牌内容复盘、卖点与爆款结构提取，以及生成提示词整理。
description_en: Analyze a user-selected video into script, style, selling points, viral structure, and a reusable generation prompt with explicit billing authorization.
category: design # 暂用分类；最终枚举待 WorkBuddy 团队确认
version: 1.0.0
author: 极睿科技（Infimind）
permissions:
  provisional: true
  read:
    - "仅限当前对话中用户主动选择的视频"
  network:
    - "仅通过已启用的极睿视频 Connector 调用 get_user_info、create_video_analysis_task 与 get_video_analysis_status"
---

# 极睿视频分析

## 能力范围

本 Skill 使用 `infimind-video` Connector 提供的以下工具：

- `get_user_info`：检查 Token、账户和积分；不接收参数。
- `create_video_analysis_task`：使用一个 `videoFile` 创建分析任务；该工具没有 `dryRun`。
- `get_video_analysis_status`：使用创建结果中的 `analysisId` 查询状态与分析结果。

如用户要创建新视频或改写后立即生成，应先完成分析交付，再由 `infimind-video-generation` 独立完成预检和付费授权。

## 适用场景

- 拆解商品视频的脚本结构、镜头节奏和卖点表达。
- 分析品牌视频的视觉风格、叙事方式和传播结构。
- 从已有视频提取可复用但不照搬具体人物或品牌的生成提示词。
- 跟踪当前对话中已经创建的视频分析任务。
- 将分析结果整理为后续创作的结构化输入。

## 非适用场景

- 用户要生成或编辑视频而不需要先分析已有视频。
- 没有用户主动提供的视频，或本地文件和公网 URL 均不可访问。
- 请求识别人脸真实身份、推断敏感属性、实施监控、欺诈或侵权复刻。
- 用户要求把不确定推断包装成视频中的已证实事实。
- 用户只需人工观感建议且不愿产生积分消耗；此时可提供基于可见信息的非工具建议。

## 事实与合规边界

1. 只交付工具真实返回的分析字段。不得把分析推断写成视频事实，也不得虚构脚本台词、品牌主张、人物身份或传播数据。
2. 工具输出是内容分析，不是版权、肖像权、商标权或广告合规的法律结论。涉及第三方作品、音乐、人物或品牌时，提醒用户自行确认授权。
3. 涉及公众人物时，不协助制作冒充、虚假新闻、政治操纵、诈骗或虚假代言内容；不根据画面猜测私人信息。
4. 对未成年人、裸露、暴力、仇恨、违法活动和其他敏感内容采取保守判断；不复述不必要的敏感细节。
5. 生成提示词应抽象结构和风格，不默认复制可识别人物、受保护角色、商标、独特台词或未经许可的品牌资产。
6. Token 只应在 WorkBuddy Connector 凭证设置中填写。不得索取或要求用户在对话中粘贴 Token，也不得回显、记录或写入结果。

## 输入检查

1. 确认用户希望分析的具体视频和用途，例如商品复盘、品牌审核或提示词提取。
2. 本地视频必须是用户在当前对话中主动选择的文件；远程地址必须是可安全读取的公网 HTTP/HTTPS URL。不要猜测本地路径。
3. 检查视频是否可访问、是否为服务支持的格式；不上传无关文件，不尝试读取当前任务以外的目录。
4. 若视频可能包含未授权的第三方作品、人物、商标或敏感内容，先说明使用边界并请用户确认其有权处理。
5. 调用 `get_user_info` 检查 Token、账户和积分。失败时停止，不创建分析任务。
6. 确认用户需要的是工具分析，而不是无需付费的文字建议。

## 工具参数

### `get_user_info`

不传参数。仅使用返回的账户状态和积分判断是否可以继续；不展示或保存认证值。

### `create_video_analysis_task`

- 只传 `videoFile`。
- `videoFile` 必须对应用户本次明确选定且可访问的视频，不用其他素材替代。
- 工具没有 `dryRun`；调用成功即创建可能产生积分消耗的分析任务。
- 调用后保存真实 `analysisId`、`creditsUsed` 和 `remainingCredits`；字段缺失时不自行补值。

### `get_video_analysis_status`

- 只传创建响应中的真实 `analysisId`。
- 不猜测 ID，不查询其他用户或其他对话的任务。
- `pending` / `processing` 时按服务节奏适度查询，不固定高频轮询。
- 到达 `completed` 或 `failed` 后立即停止轮询。

## 费用授权

1. `create_video_analysis_task` 没有 `dryRun`，无法在创建前通过该工具获取本次具体积分消耗。
2. 在账户、输入与合规检查后，明确告诉用户“正式创建会消耗积分，当前无法提供创建前的具体数值”；不得编造具体积分。
3. 单独询问用户是否现在创建分析任务。最初的“分析”“拆解”“总结”请求不等于扣费授权。
4. 用户拒绝、未回复或授权不明确时不得创建。
5. 收到明确肯定答复后只创建一次。若素材改变、上次结果不明确或需要重新创建，必须再次说明风险并取得新的单独确认。

## 结果结构

完成后按服务真实返回值依次整理：

1. 视频脚本 `script`
2. 视觉与叙事风格 `style`
3. 卖点话术 `sellingPoints`
4. 爆款结构 `viralFormula`
5. 可复用生成提示词 `generatedPrompt`

字段为空时明确写“本次分析未返回该字段”。可以在保留原始 `generatedPrompt` 的前提下，把商品、人群、卖点和场景替换成清晰占位符，但必须标注这是后续整理，不是工具原始输出。

## 状态与错误处理

- 创建成功：记录真实 `analysisId`、工具返回的实际消耗与剩余积分，不自行计算。
- `pending` / `processing`：只报告工具返回的状态与 `conversionProgress`；没有进度时不估算百分比。
- `completed`：按五类结果交付，并区分工具原始字段与后续整理。
- `failed`：展示可安全公开的 `errorMessage`，说明没有可用最终结果；不暴露内部堆栈、Token 或路径。
- 超时或网络结果不明确：若有 `analysisId`，先查询原任务；无法确认是否创建成功时不重复创建。
- 本地文件不存在、格式不支持或公网 URL 不可访问：请用户重新上传或更换地址，不自行替换素材。
- 任何可能再次扣费的重试都需重新获得单独确认。
- 鉴权失败：引导用户访问 `https://aigc-next.iclip.cn/mcp-tokens` 撤销失效 Token 或创建新 Token，再到 Connector 设置更新凭证并重新连接。

## 输出模板

### 创建结果

- 分析 ID：真实 `analysisId`
- 本次消耗：工具返回的 `creditsUsed`，未返回则明确说明
- 剩余积分：工具返回的 `remainingCredits`，未返回则明确说明

### 分析结果

- 脚本：`script` 或“本次分析未返回该字段”
- 风格：`style` 或“本次分析未返回该字段”
- 卖点：`sellingPoints` 或“本次分析未返回该字段”
- 爆款结构：`viralFormula` 或“本次分析未返回该字段”
- 原始生成提示词：`generatedPrompt` 或“本次分析未返回该字段”
- 后续整理：如有，明确标注为基于原始输出的编辑

## 示例

用户说“分析这个商品视频并给我可复用提示词”，应先确认视频、用途与素材权利，再检查账户；说明分析没有预检并会消耗积分，得到单独确认后只调用一次 `create_video_analysis_task`。保存 `analysisId` 并查询状态，完成后按脚本、风格、卖点、爆款结构和提示词五部分交付，缺失字段如实说明。

For English requests, apply the same media checks, rights boundary, credit disclosure, separate authorization, single-create rule, status tracking, and fact-versus-inference distinction. Never request a token in chat and return only fields actually provided by the service.
