# DramaBuddy MCP 工具映射与事实

基于 `dramabuddy` 连接器（`https://aicomic.yuewen.com/mcp`，type http）的实测行为。工具名在 WorkBuddy 中以 `mcp__dramabuddy__<tool>` 暴露。

## 已验证工具映射

| 目的 | 工具 | 实测约束 |
|---|---|---|
| 查询全画布 | `getCanvasData` | 返回 nodes、edges、viewport 和 `nodeHistoryCountMap`；操作前后都应调用 |
| 查询节点详情 | `getNodeDetail` | 返回完整 input/output、`aiStatus`、`errorMsg` |
| 查询可用模型 | `listModels` | 创建生成节点前调用；类型 `t2i/i2i/t2v/i2v/f2v/mp2v/t2a` |
| 创建节点 | `addNode` | 参数 `nodeType`（text/image/video/audio）+ `name` 必填；`input`、`output` 都是 JSON 字符串；可选 positionX/positionY（不传服务端自动排布） |
| 修改节点 | `updateNode` | `nodeId` + `nodeType`（需与 addNode 时一致）必填；input/output 传完整对象；未传字段由 MCP 保持原值；可传 positionX/positionY（不传保留原值） |
| 创建连线 | `addRelation` | 素材到生成节点必须传 `role="reference"` |
| 删除连线 | `deleteRelation` | 按 relationId 删除 |
| 删除节点 | `deleteNodes` | 可批量删除，并自动删除相关连线 |
| 预览积分 | `previewNodeTask` | 参数 `nodeIds` 为 string[] 数组；当前实测只支持单节点预览，每次只传一个 ID |
| 执行生成 | `runNodeTask` | 参数 `nodeItems` 为 JSON 字符串，必须使用最近一次预览返回的 nodeId 与积分字段原样构造 |
| 上传素材 | `getUploadUrl` | 参数 `fileSuffix`（不带点，如 png/mp4）。仅用于用户要求上传本地素材时；返回 cosPath / uploadUrl / accessUrl / expiredTime |

## 参数与返回值事实

- 创建或更新生成节点前，先按能力调用 `listModels`，只选 `isOpen=true` 的模型；分辨率默认 720p（若该档位不存在则取最接近的可用档位并向用户说明）；resolution 与 duration 必须属于该模型返回的可用档位。
- 生成模型默认策略：图片按 `showName` 精确选择 `Seedream 5.0 pro`；视频在当前 `t2v/i2v/f2v/mp2v` 对应列表中按 `showName` 精确选择 `Seedance 2.0 畅享版`（modelCode `100007`），均要求 `isOpen=true`，并以当次 `listModels` 返回的该条目信息（code / 可用 resolution / duration）为准。若列表中没有此模型或已置灰，不得把不兼容能力的模型强行用于节点，也不得静默切换高价模型；应列出可用备选模型及积分预览，请用户选择或确认。
- 对外传参使用可读枚举，例如 ratio=`"9:16"`、generateType=`"t2i"` 或 `"i2v"`。服务端在节点详情中可能归一化为数字，例如实测 `9:16 → 5`、`t2i → 2`、`i2v → 1`、`mp2v → 3`；这是正常现象，不要误判为被篡改。
- 文字节点使用 `output={"text":[{"content":"正文"}]}`；图像、视频节点把生成参数放在 input，首次创建时 output 留空。
- `@[节点名]` 要求名称完全匹配，只控制 prompt 内素材编号和顺序；真正的素材引用关系依靠 `addRelation(role="reference")`，不能只写 @ 引用而不连线。`addRelation` 参数为 `sourceNodeId`（素材节点）/ `targetNodeId`（生成节点）。
- **素材上传三步流程（getUploadUrl）**：1) `addNode` 建素材节点（input 至少填 prompt，output={}）；2) `getUploadUrl(fileSuffix)` 用返回的 `uploadUrl` 做 `HTTP PUT` 直传（`Content-Type` 设为文件 MIME，如 image/png、video/mp4；Body 为文件字节；无需额外鉴权头，签名约 1 小时有效）；3) `updateNode(nodeId, nodeType, output={"images":[{"cosPath":"..."}]})` 回填（视频用 videos，音频用 audios）。三个返回字段的分工：`cosPath` 只用于 updateNode 回填；`uploadUrl` 只用于 PUT 上传，绝不能写入节点数据；`accessUrl` 是 CDN 签名 URL，前端读取时自动生成，客户端通常不需要。授权仅限本次返回的单个 cosPath 对象，禁止覆盖已有文件。
- 图像成功结果位于 `output.images[]`；视频成功结果位于 `output.videos[]`，通常同时含 `cosPath` 和临时签名 URL。以 cosPath 作为稳定资源标识，不承诺签名 URL 永久有效。
- 已实测 `aiStatus=0` 表示待执行、`1` 表示生成中、`2` 表示成功；其他值不得自行解释，应保留原值并结合 `errorMsg` 说明。
- 当前服务没有独立的节点历史详情工具；`nodeHistoryCountMap` 只能表明历史数量。用户要求历史明细时，应明确能力缺口，不得伪造记录。
- 每次变更后用 `getNodeDetail` 或 `getCanvasData` 核验节点 ID、类型、内容、位置和连线；工具报错时保留已完成结果并报告原始错误。

## 画布布局

默认从左到右按制作流水线布局，并避免节点重叠：

1. 小说原文/需求（如画布已有则复用）
2. 单集剧本文字节点
3. 角色、道具、场景的文字节点
4. 与每个主体一一对应的图像节点
5. 按镜号排列的视频分镜节点
6. 已生成结果保持在原节点或工具规定的结果位置

同类节点纵向排列；节点较多时分区并预留间距。创建前先查询当前画布，优先复用语义相同的已有节点，避免重复创建；但发现与请求重复/高度相似的生成节点时，必须先询问用户选择（下载已有素材 / 改节点重新生成 / 新增节点），不得静默复用或新建。

## 节点命名约定（供下载文件命名使用）

- 角色设定：`角色设定｜名称`；角色图：`角色图｜名称`
- 道具设定：`道具设定｜名称`；道具图：`道具图｜名称`
- 场景设定：`场景设定｜名称`；场景图：`场景图｜名称`
- 视频节点：`EP{X}-S{XX}｜镜头摘要`
- 单图/单视频直出节点：`图片｜内容摘要`、`视频｜内容摘要`

下载文件名据此转为：`角色图-角色名.png` / `道具图-道具名.png` / `场景图-场景名.png` / `第{X}集-分镜{XX}-镜头摘要.mp4`（封面加 `-封面.jpg`）/ `图片-内容摘要.png` / `视频-内容摘要.mp4`。
