---
name: xmind-mindmap
description: 使用 Xmind 官方 MCP 管理团队空间，并创建、读取、编辑和完善 Xmind 在线思维导图。当用户要求查找在线导图、整理内容为导图、调整主题结构与样式、管理画布、文件夹或任务信息时使用；不用于本地 .xmind 文件。
version: "1.0.0"
author: "Xmind"
---

# Xmind 思维导图

使用 Xmind 官方 MCP，在用户授权的 Xmind 国内版团队中管理空间和文件，并创建、读取、编辑在线思维导图。

## 触发条件

在以下场景使用本 Skill：

- 将主题、笔记、会议纪要、文章或项目资料整理为在线思维导图。
- 查找、读取、总结或继续完善已有的 Xmind 在线导图。
- 新增、删除、移动或修改主题、画布、文件及文件夹。
- 添加外框、概要、联系、主题链接、待办或计划任务。
- 调整导图结构、配色、主题样式、图片或主题属性。
- 查询当前授权团队、团队空间或成员信息。

本 Connector 只操作当前授权团队中的 Xmind 在线导图，不读取或修改用户设备上的 `.xmind` 文件。

## 认证与团队边界

- 本 Connector 使用 MCP 原生 OAuth，不需要用户复制 Token，也不在 `connector-meta.json` 中设置 `auth_mode`。
- 首次连接时，WorkBuddy 通过 `https://app.xmind.cn/.well-known/oauth-protected-resource` 和授权服务器元数据发现认证信息，动态注册客户端，并使用授权码流程与 PKCE S256 打开 Xmind 授权页面。
- 授权成功后，WorkBuddy 从 `https://app.xmind.cn/api/oauth/token` 获取访问令牌；访问令牌失效时使用 `refresh_token` 刷新。
- 如果授权被撤销、刷新失败或持续返回 401，提示用户在 WorkBuddy 的 Connector 设置中重新连接 Xmind。不要索取 Xmind 密码、访问令牌或刷新令牌。
- 一次连接只对应一个 Xmind 团队。处理用户提供的文件 ID 前，优先调用 `xmind_whoami` 确认当前可访问的团队；其他团队中的文件需要用户重新授权到对应团队。
- 如果工具调用没有返回成功结果，不要声称已经创建、修改、移动或删除内容。

## 操作原则

1. 用户未明确目标文件时，使用空间、文件夹或最近导图工具定位目标，不猜测 `fileId`、`folderId`、`sheetId`、`topicId` 或标注 ID。
2. 编辑已有导图前先读取当前内容。使用 `xmind_read_mindmap` 返回的 `<!--t:id-->` 等锚点，并在整图编辑时保留未被修改主题的锚点。
3. 同一批主题或文件应尽量合并到一次调用，遵守工具的批量上限，避免逐项调用。
4. 只修改用户要求的范围。删除包含下一级主题的分支、移动文件或清除任务信息前确认对象和影响范围。
5. 图片必须是用户提供或明确授权使用的公开 HTTP(S) 地址；不要擅自上传私密图片到公共图床。
6. 计划任务属于付费能力。只有用户提供了日期、进度或优先级时才设置，不编造负责人、截止日期或完成进度。

## 工具说明与参数

以下内容基于 Xmind 中国生产环境提供的 30 项 MCP Tool Schema。参数标记为“必填”或“可选”；实际调用仍以运行时 Schema 为准。

### 账号、空间与文件管理

#### `xmind_whoami`

确认本次连接授权到哪个 Xmind 团队，并列出用户所属的其他团队。处理用户直接提供的文件 ID 前使用。

- 参数：无。

#### `xmind_list_spaces`

列出当前授权团队中用户可以访问的顶层空间。空间 ID 同时也是该空间的根文件夹 ID。

- 参数：无。

#### `xmind_list_folders`

列出某个空间或文件夹下一级的文件夹，并返回路径信息；一次只返回一层。

- `folderId`（可选）：文件夹 ID 或空间 ID；不填时使用默认空间根目录。
- `cursor`（可选）：上一页返回的 `nextCursor`；继续翻页时必须沿用相同的 `folderId`。

#### `xmind_create_folder`

在当前团队的空间或文件夹中创建新文件夹。

- `name`（必填）：文件夹名称，1–255 个字符。
- `folderId`（可选）：目标文件夹 ID 或空间 ID；不填时在默认空间根目录创建。

#### `xmind_move_file`

将一个或多个思维导图文件移动到指定文件夹或空间。源文件和目标位置必须属于当前授权团队。

- `fileIds`（必填）：要移动的文件 ID 数组，一次 1–100 个。
- `folderId`（必填）：目标文件夹 ID 或空间 ID。

#### `xmind_manage_drive_item`

重命名文件或文件夹，或将文件移入废纸篓、从废纸篓恢复。移入废纸篓是可恢复操作。

- `action`（必填）：`rename_file`、`rename_folder`、`trash_file` 或 `restore_file`。
- `fileId`（条件必填）：`rename_file`、`trash_file`、`restore_file` 的目标文件 ID。
- `folderId`（条件必填）：`rename_folder` 的目标文件夹 ID；空间根目录不能重命名。
- `name`（条件必填）：执行 `rename_file` 或 `rename_folder` 时的新名称，1–255 个字符。

#### `xmind_list_teammates`

列出当前授权团队成员的 `xmindId` 和显示名称，用于将成员名称对应到工具可使用的成员标识；不能邀请、删除成员或修改角色。

- 参数：无。

#### `xmind_list_mindmaps`

不指定文件夹时列出最近打开的导图；指定文件夹时列出该文件夹直接包含的导图，不递归下级文件夹。

- `limit`（可选）：返回数量，1–50，默认 20。
- `folderId`（可选）：目标文件夹 ID 或空间 ID；不填时进入最近打开模式。
- `cursor`（可选）：上一页返回的 `nextCursor`，只与 `folderId` 一起使用。

### 创建与读取导图

#### `xmind_create_mindmap`

根据 Markdown 层级内容创建新的 Xmind 在线思维导图。

- `markdown`（必填）：导图内容。第一个一级标题作为中心主题，标题层级最多 6 级；无序列表用于叶子层级的详细内容。
- `skeleton`（可选）：初始结构，可选 `Mind Map`、`Logic Chart`、`Brace Map`、`Org Chart`、`Tree Chart`、`Timeline`、`Fishbone`。
- `folderId`（可选）：创建位置的文件夹 ID 或空间 ID；不填时使用默认空间。

#### `xmind_read_mindmap`

将指定导图画布读取为 Markdown，并返回用于后续编辑的主题和标注锚点。

- `fileId`（必填）：思维导图文件 ID。
- `sheetId`（可选）：画布 ID；不填时读取第一个画布。

#### `xmind_get_topic`

获取单个主题的完整信息，包括笔记、标记、标签、超链接、图片以及直接下一级主题信息。

- `fileId`（必填）：思维导图文件 ID。
- `topicId`（必填）：主题 ID，可来自读取结果中的 `<!--t:id-->`、`xmind_list_sheets` 的 `rootTopicId` 或本工具返回的下一级主题 ID。

#### `xmind_list_sheets`

列出导图文件中的全部画布，包括画布 ID、标题、根主题 ID 和主题数量。

- `fileId`（必填）：思维导图文件 ID。

#### `xmind_list_resources`

列出导图引用的附件、主题图片、音频笔记、网页链接和本地文件链接，只返回引用信息，不返回资源文件本身。

- `fileId`（必填）：思维导图文件 ID。
- `sheetId`（可选）：只查看指定画布；不填时查看整个文件。
- `limit`（可选）：返回数量，1–500，默认 100；根据返回的 `total` 和 `truncated` 判断是否完整。

### 编辑导图与画布

#### `xmind_edit_mindmap`

用完整 Markdown 更新已有导图。调用前先读取目标画布，并保留需要延续的 `<!--t:id-->` 锚点，以保留主题的笔记、标记和图片。

- `fileId`（必填）：思维导图文件 ID。
- `markdown`（必填）：更新后的完整 Markdown，第一个一级标题为中心主题。
- `sheetId`（可选）：目标画布 ID，必须与之前读取的画布一致；不填时使用第一个画布。
- `skeleton`（暂勿使用）：生产 Schema 保留了此参数，但当前版本标注为尚不支持；需要改变结构时使用 `xmind_set_structure`。

#### `xmind_add_sheet`

在已有导图文件中新增一个画布。创建后调用 `xmind_list_sheets` 获取新画布 ID，再对其进行编辑。

- `fileId`（必填）：思维导图文件 ID。
- `title`（可选）：新画布标题。

#### `xmind_remove_topic`

删除指定主题及其全部下一级内容。批量结构调整优先使用 `xmind_edit_mindmap`。

- `fileId`（必填）：思维导图文件 ID。
- `topicId`（必填）：要删除的主题 ID。
- `confirm`（条件必填）：目标存在下一级主题时必须为 `true`；叶子主题可不填。

### 主题属性、图片与标注

#### `xmind_set_topic_attrs`

批量设置主题的笔记、超链接、标签和标记。主题标题和层级应通过 `xmind_edit_mindmap` 修改。

- `fileId`（必填）：思维导图文件 ID。
- `items`（必填）：1–200 个主题设置项；每项包含 `topicId`（必填），以及 `note`、`href`、`labels`、`markers`（可选）。`note` 为不超过 2KB 的纯文本，较长内容应拆为下一级主题。

#### `xmind_set_topic_image`

为单个主题附加图片，由 Xmind 服务端抓取并存储图片。

- `fileId`（必填）：思维导图文件 ID。
- `topicId`（必填）：目标主题 ID。
- `imageUrl`（必填）：公开可访问的 HTTP(S) 图片地址；支持 PNG、JPG、WebP、GIF、SVG 和 BMP。

#### `xmind_add_relationship`

在两个主题、外框或区域之间添加联系线。

- `fileId`（必填）：思维导图文件 ID。
- `sourceId`（必填）：起点元素 ID。
- `targetId`（必填）：终点元素 ID。
- `title`（可选）：联系线标签。
- `sheetId`（可选）：目标画布 ID；不填时使用第一个画布。

#### `xmind_update_relationship`

修改已有联系的标签或重新指定起点、终点。

- `fileId`（必填）：思维导图文件 ID。
- `relationshipId`（必填）：联系 ID。
- `title`、`sourceId`、`targetId`（至少一项）：新的标签、起点元素 ID 或终点元素 ID。

#### `xmind_add_boundary`

为主题整体添加外框，或为其连续的下一级主题范围添加外框。

- `fileId`（必填）：思维导图文件 ID。
- `topicId`（必填）：外框所属的主题 ID。
- `rangeType`（可选）：`parent` 或 `children`，默认 `parent`。
- `rangeStart`、`rangeEnd`（条件必填）：当 `rangeType` 为 `children` 时使用，分别表示从 0 开始的首个和末个下一级主题索引，末端包含在范围内。

#### `xmind_add_summary`

为某个主题下连续的一组下一级主题添加概要。

- `fileId`（必填）：思维导图文件 ID。
- `topicId`（必填）：这些下一级主题的上一级主题 ID。
- `rangeStart`、`rangeEnd`（必填）：从 0 开始的首尾索引，末端包含在范围内。
- `title`（可选）：概要标题。

#### `xmind_remove_annotation`

删除指定的联系、外框或概要，不会删除主题。

- `fileId`（必填）：思维导图文件 ID。
- `annotationId`（必填）：从 `<!--r:id-->`、`<!--b:id-->` 或 `<!--s:id-->` 锚点取得的标注 ID。

#### `xmind_add_topic_link`

在同一导图内为一个主题添加指向另一主题的内部跳转链接；会替换来源主题已有的超链接。

- `fileId`（必填）：思维导图文件 ID。
- `sourceTopicId`（必填）：承载链接的主题 ID。
- `targetTopicId`（必填）：链接指向的主题 ID。

### 任务管理

#### `xmind_set_todo`

批量设置主题的待办复选状态。同一次调用中的所有主题使用相同状态。

- `fileId`（必填）：思维导图文件 ID。
- `topicIds`（必填）：主题 ID 数组，一次 1–200 个。
- `status`（必填）：`todo` 或 `done`。

#### `xmind_set_planned_task`

批量设置计划任务的开始、截止、持续时间、进度或优先级，并与现有任务信息合并。此能力取决于文件套餐是否支持甘特图编辑。

- `fileId`（必填）：思维导图文件 ID。
- `items`（必填）：1–200 个任务设置项；每项包含 `topicId`（必填），并至少设置 `start`、`due`、`duration`、`progress`、`priority` 中一项。
- `start`、`due`：Unix Epoch 毫秒时间戳；`duration`：毫秒；`progress`：0–1；`priority`：0–9。

#### `xmind_clear_task`

批量清除主题的待办状态和计划任务字段，使其恢复为普通主题。

- `fileId`（必填）：思维导图文件 ID。
- `topicIds`（必填）：主题 ID 数组，一次 1–200 个。

### 结构与视觉样式

#### `xmind_set_structure`

设置整张画布或指定分支的布局结构。

- `fileId`（必填）：思维导图文件 ID。
- `structure`（必填）：`MindMap`、`MindMapUnbalanced`、`LogicChartRight`、`LogicChartLeft`、`BraceMapRight`、`BraceMapLeft`、`OrgChartDown`、`OrgChartUp`、`TreeChartRight`、`TreeChartLeft`、`TreeChartBalanced`、`TreeChartBranchAlignedLeft`、`TreeChartBranchAlignedRight`、`TimelineHorizontal`、`TimelineVertical`、`TimelineHorizontalOffAxis`、`FishboneRight`、`FishboneLeft`、`TreeTable`、`TreeTableTopTitle`、`MatrixRow` 或 `MatrixColumn`。
- `topicId`（可选）：非根主题 ID；传入时只调整该主题的分支，不填时调整整张画布。
- `sheetId`（可选）：整张画布调整时的目标画布 ID；不填时使用第一个画布。
- 限制：`TimelineHorizontal`、`TimelineVertical`、`TimelineHorizontalOffAxis`、`FishboneRight`、`FishboneLeft`、`TreeTable`、`TreeTableTopTitle`、`MatrixRow`、`MatrixColumn` 只能应用于整张画布，不能传入非根 `topicId`。

#### `xmind_set_color_theme`

更换指定画布的整体配色主题，不能只作用于单个分支。

- `fileId`（必填）：思维导图文件 ID。
- `color`（必填）：`Sophisticated`、`Dawn`、`Constancy`、`Cream`、`Candy`、`Dancing`、`Rainbow`、`Hawaii`、`Macaron`、`Code`、`Space`、`CyberPunk`、`DeepSea`、`Vintage`、`Zen`、`Woodland`、`Rainforest`、`Sakura`、`GreenTea`、`Roses`、`Champagne`、`Kimono`、`Vanilla`、`Dessert` 或 `Fire`。
- `sheetId`（可选）：目标画布 ID；不填时使用第一个画布。

#### `xmind_set_topic_style`

为一组主题设置相同的局部样式。局部样式覆盖画布配色主题，并在之后更换配色时保留。

- `fileId`（必填）：思维导图文件 ID。
- `topicIds`（必填）：主题 ID 数组，一次 1–200 个；所有主题应用相同样式。
- `fillColor`、`textColor`、`lineColor`、`borderLineColor`（可选）：六位十六进制颜色 `#RRGGBB`，传 `null` 清除该覆盖。
- `fontWeight`（可选）：`normal`、`bold` 或 `null`。
- `fontStyle`（可选）：`normal`、`italic` 或 `null`。
- `textDecoration`（可选）：`none`、`line-through` 或 `null`。
- `fontSize`（可选）：8–72 pt 的整数，或 `null`；仅在用户明确要求时调整字号。

## 推荐工作流程

### 新建导图

将内容提炼为中心主题、主要分支和下一级主题，选择合适的初始结构，再调用 `xmind_create_mindmap`。主题标题保持简洁，同层级表达方式一致。

### 读取和总结

先通过 `xmind_whoami` 确认团队，再用 `xmind_list_spaces`、`xmind_list_folders` 或 `xmind_list_mindmaps` 定位文件，最后调用 `xmind_read_mindmap`。总结时区分导图原文与 AI 的分析建议。

### 编辑已有导图

先读取目标画布，再调用相应编辑工具。整图结构编辑使用 `xmind_edit_mindmap`；属性、任务、标注和样式修改优先使用对应的专用工具。

### 会议纪要与项目计划

将讨论内容整理成层级结构，将明确的行动项设置为待办。只有原始内容或用户明确提供日期、进度和优先级时，才设置计划任务。

## 中英文描述与使用示例

- 中文描述：通过 AI 对话管理团队空间，并创建、读取和编辑 Xmind 在线思维导图。
- English description: Manage team spaces and create, read, and edit Xmind online mind maps directly from AI conversations.

中文示例：

- “把这份会议纪要整理成一张 Xmind 思维导图。”
- “读取我最近打开的‘产品规划’导图并总结重点。”
- “在默认空间创建‘市场研究’文件夹，并把这三张导图移动进去。”
- “把‘执行计划’画布改成时间轴，并为三个行动项设置截止日期。”

English examples:

- “Turn these meeting notes into an Xmind mind map.”
- “Read my recently opened Product Plan mind map and summarize the key points.”
- “Create a Market Research folder in my default space and move these three mind maps into it.”
- “Change the Execution Plan sheet to a timeline and add due dates to three action items.”

## 错误处理

- 找不到目标团队、文件夹、导图、画布或主题：重新列出并读取最新标识，不猜测。
- OAuth 失效或权限不足：提示用户重新连接，或重新授权到文件所在团队。
- 调用超时：最多重试一次；仍失败时明确说明操作未完成。
- 套餐不支持某项能力：如实说明限制，并提供当前账号可用的替代方式。
- 写入、移动或删除失败：保留原内容，不声称成功，并说明服务端返回的原因。
