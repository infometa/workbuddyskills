---
name: nova-ai
description: 当用户提到 Nova,或想做短剧剧本(原创创作 / 参考剧本改编 / 润色)、剧集统筹表、角色/场景/道具出图、分镜提示词与分镜批量生成视频、广告视频时使用。可在 Nova 中查项目与剧本、上传对话里附的剧本文件和产品图、发起并跟进各类异步生成任务。生成前必须让用户选模型;扣真实积分的动作必须先报预估并取得用户同意。
version: "3.0.0"
author: "Nova"
---

# Nova AI

Nova 是短剧 / 广告创意生产平台。本连接器提供 59 个工具,覆盖从「一句灵感」或「一部参考剧本」到成稿 / 成片的全流程。先判断用户要做哪件事,再走对应链路:

- **原创短剧(OC,`oc_*`)**:一句灵感 → 6 个创意方向 → 总纲 / 人物 / 卡点 → 素材库 → 集纲 → 逐集剧本。每个阶段都能看草稿、修改、确认推进。
- **剧本改编(SI,`si_*`)与润色(`polish_*`)**:一部参考剧本 → 识别拆解 → 换皮方向 → 策划映射 → 集纲 → 逐集新剧本,可导出 DOCX / 映射表 XLSX,再进入润色精修。仅可用于用户有权改编的剧本。
- **统筹表与出图**:从项目剧本提取角色 / 场景 / 道具统筹表,再批量出定妆图、参考图,或单张自定义出图。
- **分镜与批量视频**:统筹表场次 → 分镜提示词 → 全局提示词 → 报价确认 → 批量出视频(与网页「分镜」「生成视频配置」一致)。
- **广告 Agent(`*_ad_agent*`)**:在无限画布上用广告 Agent 生成广告成片,中间有问卷、方案确认、费用确认三道闸门。

## 标记说明

- 🔴 = 扣真实积分。能报价的先报价;报不了价的说明「按实际用量扣费」。都要取得用户明确同意后再调用。
- ◔ = 按大模型用量扣**少量**积分,系统没有预估。调用前如实告知。
- ⚠️ = 不可撤销或会丢数据。先复述要操作的对象,取得用户确认。

## 通用规则

### 先定位,再操作
几乎所有工具都要先拿到 ID,缺了就先查,不要臆造:
- `projectId`:`list_projects`
- 分集 `episodeId`:`get_project` 返回的分集列表
- 剧本 `scriptId`:`list_scripts`
- OC 任务 `taskId`:`oc_get(view=list)`;SI 任务 `taskId`:建任务时返回

### 异步与轮询
生成类工具提交后返回 `taskId` / `batchId` / `jobId`,用对应的查询工具轮询到终态(`ready` / `succeeded` / `done` / `failed` 等)。间隔:文本 / 提示词约 3 秒,图片约 5 秒,视频与分镜作业约 10 秒。到了 `failed` 就停止轮询,按返回的 `hint` 处理。

### 草稿与版本
OC / SI 每个阶段都有草稿和 `version`。改草稿前先用 `oc_get` / `si_get(view=draft)` 取当前 `version`,保存时带上它;返回 409 说明版本冲突,重新取一次再保存,不要把 409 甩给用户。改上游草稿会把下游标记为「待更新」,但不会删掉已有内容。

### 🔴 生成前先让用户选模型
出图(`start_asset_generation_preview` / `generate_asset_image`)、批量视频(`preview_batch_video` / `create_batch_video_job`)、广告 Agent(`start_ad_agent` 的 imageModel / videoModel)的模型参数都是必填。
1. 先调 `list_models(type=image|video)`,把模型名称、特点、可选分辨率 / 画幅 / 时长列给用户。
2. 由用户选定模型和分辨率,再传入。不要替用户决定。
3. 用户明确说「用默认 / 你定」时,才传 `default=true` 的那个 value;广告 Agent 里用户说「交给 Agent 匹配」时传 `auto`。

### 🔴 扣费
凡是让 Nova 生成内容的动作都扣积分。按能否报价分三类处理:
- **先报价再提交**:资产出图(`get_asset_generation(view=preview)` 的 `estimatedCredits` → `approve_asset_generation`)、批量视频(`preview_batch_video` → `create_batch_video_job`)、广告 Agent(`pendingApproval.quoteSnapshot` → `approve_ad_agent_cost`)、统筹表提取(`get_breakdown(view=estimate)` → `start_asset_extraction`)。
- **剧本类先估价**:估价工具免费、与网页端预计积分同源。告知「预计消耗 X 积分,实际按真实 Token 结算、多退少补」,同意后再发起。
  - OC:建任务前 `oc_estimate_credits(action=create)`;确认阶段前 `action=stage`;生成集纲 / 剧本前 `action=outline` / `script`;重写单集前 `action=rewrite`。
  - SI:确认步骤前 `si_estimate_credits(action=stage)`;生成前 `action=outline` / `script`;润色前 `action=polish`。
  - 注意:OC 每次确认阶段会自动生成下一阶段(确认集纲会自动生成前 3 集剧本);SI 确认 upload / decompose / skin / plan 也会自动生成下一阶段(确认 plan = 生成全部集纲)。
- **报不了价**:`si_create_task` 的识别、`polish_run(kind=typos)`、`start_storyboard_job`(须传 `confirm=true`)、`generate_asset_image`(单张提交即扣)、广告 Agent 的规划与每轮对话、出图预览的提示词生成。如实说明「按实际用量扣费、没有精确预估」。

### 本地文件(用户附的剧本或图片)
MCP 参数传不了文件本体。用户附了本地剧本(.txt / .docx / .pdf)或图片(.png / .jpg / .webp)时,固定走三步:
1. `create_upload_ticket` 拿到 `uploadUrl` 和 `commands`。调用前先向用户复述文件名并确认。
2. 用你(宿主)自带的本地命令行执行 `commands.bash`(macOS / Linux)或 `commands.powershell`(Windows),把 `<本地文件绝对路径>` 换成附件的真实路径。
3. `complete_upload(ticketId)` 取结果:剧本得到 `scriptId`,图片得到 `assetId`(传了 canvasId 还有 `canvasNodeId`)。

要点:
- 不要自己读取本地文件内容再塞进 `rawText`,有文件就走上传。
- 图片要求宽高 300~6000px、宽高比 0.4~2.5、≤20MB,不满足会被内容审核拒绝,先提醒用户换图。
- 票据 10 分钟有效、只能用一次。
- 宿主不允许执行命令时如实告知,改为请用户提供公开可下载链接,或到 Nova 网页上传。

### 授权与错误
- 只读授权只能调只读工具;写入和付费工具需要完整授权,否则会返回授权范围不足。
- 出错时**只转述工具返回的那句话**,它已经写明发生了什么、用户能做什么。不要自行推测内部执行顺序、副作用,也不要报内部 ID。
- 积分不足时,告诉用户「本次未扣费」,引导到 https://www.shanhaix.com 充值或联系团队管理员,不要重试。

## 参数约定

- **action**(增删改合并到一个工具):`manage_library`、`edit_breakdown_entry`、`control_asset_image_job`、`oc_annotation`、`polish_annotation`、`oc_task_control`、`si_task_control`、`control_ad_agent`、`control_batch_video_job`、`edit_storyboard(target=global_prompt)`。
- **view**(多种查询合并到一个只读工具):`oc_get`、`si_get`、`get_breakdown`、`get_asset_generation`、`get_storyboard`、`get_ad_agent_status`。`get_batch_video_jobs` 传 jobId 查单个,不传列出全部。
- **target / kind**(选择生成或编辑对象):`oc_generate`、`oc_regenerate`、`si_generate`、`si_regenerate`、`polish_run`、`start_storyboard_job`、`edit_storyboard`、`manage_library`。
- **二选一**:`create_project` 传 scriptTitle 新建,或传 scriptId 把剧本库剧本转成项目;`create_script` 传 rawText 或 fileUrl;`generate_asset_image` 传 prompt 新出,或传 jobId 按原参数重出。
- 每个 action / view / target / kind 有各自的必填参数,缺了工具会直接提示「该动作需要 xxx」,按提示补上即可。
- 分集 ID 参数一律是**数组**,单集也写 `["<id>"]`(`get_storyboard` / `start_storyboard_job` 的 `episodeIds`)。

## 工具分类(共 59 个)

### 项目与剧本库
- 查询:`list_projects`(可按名称搜索,status=active / deleted / all)、`get_project`(项目详情 + 分集列表,含集号、镜头数、分镜提示词就绪度 `promptGate`、是否已有分镜)、`list_scripts`、`get_script`(含正文)、`list_assets`(资产库;`coverAssetId` / `images[].id` 是素材 ID,可作参考图)、`list_models`。
- 新建:`create_project`(传 `scriptTitle` 新建,可带 `scriptContent` 正文;或传 `scriptId` 把剧本库剧本转成带正文和分集的项目,一部剧本只能转一次)、`create_script`(rawText 粘贴全文,或 fileUrl 公开直链,由服务端解析正文和分集)。
- 上传:`create_upload_ticket` → 宿主执行命令 → `complete_upload`(见「本地文件」)。
- 管理(免费):`manage_library(target=project, action=update / delete / restore)` 改标题简介、软删、恢复(`list_projects(status=deleted)` 可看回收站);`manage_library(target=script, action=update / delete)` 改标题、用途、编号、题材、平台、表演备注(正文不在这里改)。⚠️ delete 前复述名称并确认。
- 两种 `purpose` 别混:项目用途 5 选 1(国内真人短剧(默认)/ 海外真人短剧 / 2D3D 漫剧 / 解说漫 / 其他),列给用户挑;剧本用途只有 production(正式,默认)/ reference(参考)。
- 剧本怎么入库,按优先级:用户附了本地文件 → 票据上传;只有公开链接 → `create_script(fileUrl)`;只有粘贴的正文 → `create_script(rawText)`。
- 让新项目带剧本:先入库再 `create_project(scriptId)`(推荐,带分集);或 `create_project` 直接传 `scriptContent`。

### 原创短剧(OC)
- 查询:`oc_get` 的 view:`list` 我的任务、`task` 详情(含 currentPhase)、`status` 生成中的进度(alive 仍在跑 / dead 已终止)、`draft` 阶段草稿(需 stage)、`episodes` 逐集状态与正文、`annotations` 某集批注(需 episodeNo);`oc_export` 导出 DOCX。
- 编辑(免费):`oc_create_task` 的 manual 模式、`oc_save_draft`、`oc_edit_episode`(直接改某集正文)。
- 估价(免费):`oc_estimate_credits`。
- 🔴 生成:`oc_create_task`(inspire 模式,生成 6 个方向)、`oc_confirm_stage`(下一阶段无内容时会自动生成)、`oc_generate(target=outline)` 剩余集纲、`oc_generate(target=script)` 剧本、`oc_regenerate` 的 target:`episode` 重写单集、`outline_episode` 重生单集集纲、`episode_with_outline` 改集纲后重写(**整体覆盖**该集集纲,先 `oc_get(view=draft, stage=outline)` 取现值)、`draft` 带方向重生 plan / setting / material、`card2` 一卡升二卡。
- 批注:`oc_annotation(action=add)` 圈选加批注(免费);`action=refine` AI 精修 🔴;`action=update` 采纳 / 拒绝 / 选版本(免费,其中 regenerate 🔴);`action=delete`。
- 任务控制(免费):`oc_task_control(action=cancel)` 取消逐集剧本生成;⚠️ `action=revert` 回退到某阶段并**清空下游**;⚠️ `action=delete` 删除整个任务。

### 剧本改编(SI)
- 查询:`si_get` 的 view:`task` 详情(含 sourceReady)、`status` 生成进度(权威轮询入口)、`source_digest` 原剧逐集拆解、`draft` 阶段草稿(需 step)、`episodes` 逐集状态;`si_export`(kind=script 剧本 DOCX / mapping 映射表 XLSX)。
- 🔴 建任务:`si_create_task`,rawText(正文)或 fileUrl(公开直链)二选一,提交即扣识别费用。用户附的是本地文件时:先票据上传入库(kind=script),再用 `get_script` 取解析好的正文作为 rawText。
- 编辑(免费):`si_save_draft`。
- 推进:`si_confirm_step`(upload / decompose / skin / plan 会自动生成下一阶段 🔴;outline / script 确认免费)。
- 估价(免费):`si_estimate_credits`。
- 🔴 生成:`si_generate(target=outline / script)` 按集号闭区间生成;`si_regenerate` 的 target:`episode` 重写单集(**已完成的也会被覆盖**)、`step` 重生某阶段(skin 可带 mode)、`retry` 重试失败项(retryKind=generation / recognize / digest_episode)。
- 任务控制(免费):`si_task_control(action=cancel)` 取消逐集剧本生成;⚠️ `action=revert` 回退查看前沿(下游保留不删)。
- 进入润色:`si_polish_ensure`(免费,返回 polishTaskId)。

### 剧本润色(先 `si_polish_ensure`)
- 查询:`polish_get_task`(分集正文、批注与 AI 方案、错别字结果;精修进度靠轮询它)。
- 免费:`polish_annotation`(add / update / delete / apply_proposal;apply_proposal 配 proposalAction=apply 写回正文 / reject / select 切换版本)、`polish_edit_episode`(mode=full 整集覆盖 / mode=typo 把 wrong 改成 right)。
- 🔴 扣费(先 `si_estimate_credits(action=polish)`):`polish_run(kind=revise)` 批量精修、`kind=summary` 方案总结、`kind=regenerate_annotation` 单条批注重生、`polish_instant_refine` 圈选即时精修;`polish_run(kind=typos)` 错别字检查(没有预估)。不传 episodeNo 就是全部集、按全部集计费,能限定集号就限定。

### 统筹表与出图
- 统筹表:`get_breakdown(view=estimate)` 免费报价 → 🔴 `start_asset_extraction` 提取整本 → `get_breakdown(view=status)` 轮询 → `get_breakdown(view=table)` 看结果 / `view=export` 导出 xlsx。
  - 提取模型 modelKey 二选一:gpt-5.6-sol(高质量,缺省)、ep-20260923105549-bzn82(DeepSeek V4.1 Flash,性价比)。两档价格不同,分别报价让用户挑。
  - view=table 返回逐集 markdown 表格,**原样展示给用户,不要改写成小结**;集多时用 episodeOffset / episodeLimit 分页。
- 统筹表编辑(免费):`edit_breakdown_entry(action=update)` 改分集或场次(改前复述);⚠️ `action=delete` 删除分集 / 场次 / 场景 / 角色 / 造型 / 道具,不可恢复。
- 批量出图:
  1. `list_models(type=image)`,让用户选模型和分辨率。
  2. ◔ `start_asset_generation_preview(model, resolution, scope)`,生成提示词。
  3. `get_asset_generation(view=preview)` 轮询到 ready,拿到 `estimatedCredits`。
  4. 可选:◔ `refine_asset_prompt` 改单条提示词,用 `get_asset_generation(view=refine)` 轮询。
  5. 🔴 报价并取得同意后 `approve_asset_generation`,可按 itemIds / variants / excludeRoleKinds / entityIds 只出一部分。
  6. `get_asset_generation(view=status)` 看进度与图片。
- 单张出图:🔴 `generate_asset_image`(传 prompt 自定义出 1 张,可带参考图 refAssetIds、比例、分辨率;传 jobId 按原参数重出 1 张。提交即扣、没有报价,调用前确认模型并告知扣费);`control_asset_image_job(action=cancel / delete)`(delete 只删任务记录,不删已入库的图)。

### 分镜提示词与全局提示词
- 先看 `get_project` 里该集的 `promptGate.status`:
  - `ready`:可以直接生成分镜提示词。
  - `no_scenes`:还没有统筹表,先 `start_asset_extraction`。
  - `scenes_missing_verbatim`:场次缺剧本原文,◔ 用 `start_storyboard_job(kind=split)` 自动切分,或 `edit_storyboard(target=scene_script)` 手工补录(sceneId 来自 `get_storyboard(view=shots)`)。
- 整集生成分镜提示词:
  1. `get_storyboard(view=prompt_preview, episodeIds)` 看将处理几集、预计多少镜(免费,**没有积分预估**)。
  2. ◔ 说明「按大模型实际用量扣少量积分」并取得同意,调 `start_storyboard_job(kind=prompt, episodeIds, confirm=true)`;要覆盖已有提示词的集,加 includeGenerated=true。
  3. `get_storyboard(view=prompt_job)` 约 10 秒一轮,到 done / partial / interrupted 为止。
  4. `get_storyboard(view=shots)` 核对每镜提示词。
- 单镜手改(免费):`edit_storyboard(target=shot_prompt, shotId)`,content 为新提示词,也可改 title / sourceExcerpt。写入提示词后该分镜即可进批量视频。
- 全局提示词(免费):`get_storyboard(view=global_prompts)` 查看;`edit_storyboard(target=global_prompt, action=create / update / delete)` 新建 / 修改 / ⚠️ 删除。批量视频至少要挂 1 条,项目没有就直接新建,不必让用户回网页。

### 分镜批量生成视频
1. **选分镜**:`get_storyboard(view=shots, episodeIds)`,每次最多 5 集。
   - 后续要传的 shotIds 是 `scenes[].shots[].id`,不是 sceneId 或分镜号。
   - `eligible=false` 是没填提示词,不能生成。
   - `hasVideo=true` 表示已有成片;用户说「只给还没视频的生成」就按 hasVideo=false 筛。已有成片再生成会新出一版,不会覆盖。`hasUsableVideo` 是用户在网页上标记为「可用」的。
   - 把可生成的分镜列给用户,默认全选。
2. **定参数**:`list_models(type=video)` 把模型及其支持的画幅 / 分辨率 / 时长 / 是否出声 / 首帧能力列给用户,由用户选定;再用 `get_storyboard(view=global_prompts)` 选全局提示词(至少 1 条)。
3. **报价**:`preview_batch_video`(不扣费)。复述「将处理 N 条(其中 M 条缺参考资产仍会生成)、单条约 X、共约 Y 积分、余额 Z」并等用户同意。`excludedShots>0` 说明有分镜不能生成,创建前要剔除。报价不含多模态质检费用。
4. 🔴 **创建**:`create_batch_video_job`,模型与各项参数必须和报价时一致。
   - videoMode:reference 全能参考(默认)/ first_frame 首帧。
   - generateAudio 留空且模型支持声音时默认开启。
   - genMax(失败重试)、rewriteMax(合规改写)只能取 0 / 1 / 3 / 5。
   - qcEnabled 多模态质检默认关闭,🔴 开启会在报价之外额外扣费,需用户明确同意。
   - startAt 可定时开始(RFC3339)。
5. **跟进**:`get_batch_video_jobs(jobId)` 约 10 秒一轮,terminal=true 就停。成功的分镜带 videoUrl;`videoUrlsUnavailable=true` 是链接暂时读不到,不代表没生成,稍后重查。不传 jobId 可列出项目所有作业(activeOnly=true 只看进行中)。
6. **控制**:`control_batch_video_job` 的 action:start-now / pause / resume / ⚠️ cancel(已生成的部分不退费)/ 🔴 retry。retry 会**新建一个只含未成功分镜的作业并重新扣费**、返回新 jobId;调用前先对这些分镜 `preview_batch_video` 报价,取得同意后再传 `confirmCharge=true`。

画幅、分辨率、时长不传就用模型默认;传了必须在该模型的可选范围内(durations 含 -1 时可传 -1 自适应),被拒时把工具列出的可选项转告用户。「自动站位模式」暂未开放给 MCP。

### 广告 Agent
- 查询:`get_ad_agent_status(view=status)` 看任务状态、待处理的闸门(问卷 / 方案 / 费用 / 提案)、steps、`stateHint`、`latestReply`(Agent 最新回复);`view=results` 取生成好的图片 / 视频链接(临时签名链接,数小时后失效,需要时重取)。
- 发起:`start_ad_agent`,必填 brief、projectId、imageModel、videoModel(先 `list_models` 让用户选,用户说「交给 Agent 匹配」就传 auto)。可选 aspectRatio / resolution / videoResolution / assetIds / skill。executionMode 保持默认 auto,不要传 manual。
- 推进:`answer_ad_agent_questionnaire` 答问卷;`control_ad_agent(action=confirm_plan, taskId=planningTaskId)` 确认方案(系统随后自动报价);`send_ad_agent_message` 回答追问、要求微调、引用画布上的图片。
- 🔴 费用确认:`approve_ad_agent_cost`(decision=approve 扣费 / reject 拒绝)。
- 控制:`control_ad_agent` 的 action:cancel / retry_failed / continue_after_balance / replan / requote / regenerate / undo / cancel_questionnaire / decide_proposal。其中 🔴 retry_failed、continue_after_balance、replan、regenerate 会再次扣费。
- `stateHint` 会直接告诉你下一步:方案待确认 → confirm_plan;等待费用确认 → approve_ad_agent_cost;余额不足 → 引导充值后 continue_after_balance;失败 → retry_failed;manual 模式 → 建议用 auto 重新发起。
- **产品实拍图**:Agent 要求上传实拍图时,用 `create_upload_ticket(kind=image, projectId, canvasId=该广告画布)` → 执行命令 → `complete_upload` 拿到 `canvasNodeId`,再 `send_ad_agent_message`,**mentionNodeIds=[canvasNodeId],且 content 里写明「产品图」**(如「产品图已上传,请以它为产品参考,继续」)。少了任何一个,Agent 都不会把它当作产品参考。资产库里已有的图用 assetIds(`list_assets` 的 coverAssetId / images[].id)。

## 主流程

### 原创短剧(OC)
1. 🔴 `oc_estimate_credits(action=create)` 报预估,同意后 `oc_create_task`(inspire,给灵感)。
2. `oc_get(view=task)` 轮询到 plan 就绪,`oc_get(view=draft, stage=plan)` 把 6 个方向给用户挑(可用 `oc_save_draft` 编辑)。
3. 🔴 每次 `oc_confirm_stage` 前先 `oc_estimate_credits(action=stage, stage=当前阶段)` 报预估,同意后再确认。依次推进 setting → material → outline;确认 outline 会自动生成前 3 集剧本。
4. 🔴 其余集用 `oc_generate(target=script)` 生成(先 action=script 估价),`oc_get(view=episodes)` 跟进度。
5. `oc_export` 导出。

任一阶段显示「生成中」时,用 `oc_get(view=status)` 查:alive 就隔一会儿再查,告诉用户「仍在生成,通常 2~3 分钟」,不要催、不要重复发起;dead 就停止等待,按 reason 告诉用户失败或已取消。不要没查就只回一句「稍等再来」。

### 剧本改编(SI)
1. 🔴 告知「建任务会对参考剧本做识别,按用量扣少量积分」,同意后 `si_create_task`(rawText 或 fileUrl)。
2. `si_get(view=task)` 轮询到 sourceReady=true,`si_get(view=source_digest)` 看原剧拆解。
3. 🔴 每次 `si_confirm_step` 前先 `si_estimate_credits(action=stage, step=当前步骤)` 报预估,同意后再确认。依次推进 upload → decompose → skin → plan → outline → script;upload 确认时可设定目标集数与时长;确认 plan 会自动生成全部集纲。
4. 🔴 `si_generate(target=script)` 按集号区间生成(先 action=script 估价),用 `si_get(view=status)` 和 `si_get(view=episodes)` 跟进度。
5. `si_export` 导出;要精修就 `si_polish_ensure` 进入润色。

### 广告 Agent
1. ◔ 告知「Agent 规划与对话按用量扣少量积分,生成图片和视频前会再报价确认」。
2. `list_models(type=image)` 和 `list_models(type=video)` 让用户选模型(或交给 Agent 匹配),然后 `start_ad_agent`。
3. `get_ad_agent_status` 看到问卷后,`answer_ad_agent_questionnaire` 作答。
4. 轮询到 `latestReply` 显示「方案已就绪」。此时只有方案,还没开始生成。
5. 把方案要点讲给用户,同意后 `control_ad_agent(action=confirm_plan, canvasId, taskId=planningTaskId)`。
6. 轮询到 `stateHint`=等待费用确认、出现 `pendingApproval`,把 `quoteSnapshot` 的预计扣费告诉用户。
7. 🔴 用户同意后 `approve_ad_agent_cost(decision=approve)`,系统开始生成图片和视频,继续轮询到完成。
8. `get_ad_agent_status(view=results)` 取图片 / 视频链接给用户。

注意:
- **只发起、不确认,就只有方案没有成片。**
- 费用报价大约 15 分钟内有效,要提醒用户尽快确认。过期后 approve 会返回「确认已过期」:先 `get_ad_agent_status` 刷新,按最新的 `stateHint` 处理,不要拿旧的 approvalId 反复提交。
- 实物产品(手机、自行车、服饰等需要真实外观)Agent 会要求实拍图,请用户附上正面和侧面图,按「产品实拍图」流程上传。不要凭文字臆造真实产品外观。

### 出图
1. `list_models(type=image)` 把模型(名称、特点、可选分辨率)列给用户选。
2. ◔ 告知「预览阶段的提示词由大模型生成,按用量扣少量积分」,然后 `start_asset_generation_preview(model, resolution, scope)`。
3. `get_asset_generation(view=preview)` 轮询到 ready,把 `estimatedCredits` 告诉用户;可以只出一部分(itemIds / variants / excludeRoleKinds)。
4. 🔴 同意后 `approve_asset_generation`。
5. 某张不满意:用 `generate_asset_image(jobId)` 重出(jobId 见 `get_asset_generation(view=status)`)。要完全自定义(自己写提示词、指定参考图、比例、分辨率):用 `generate_asset_image(prompt)`。

### 分镜批量视频
`get_project` 看 promptGate → 按情况补统筹表 / 切分场次 / 生成分镜提示词 → `get_storyboard(view=shots)` 选分镜 → `list_models(type=video)` 让用户选模型和参数 → 选全局提示词(没有就新建)→ `preview_batch_video` 报价并取得同意 → 🔴 `create_batch_video_job` → `get_batch_video_jobs(jobId)` 轮询到 terminal → 把 videoUrl 给用户。细节见「分镜批量生成视频」。

## 主动引导用户(每轮回复都要做)

每次工具返回结果后,**用用户听得懂的话给出 2~3 个下一步建议**,让用户知道接下来能做什么。不要只丢一堆数据,也不要只问一句「还需要什么吗」。

- **说动作,不说工具名**:用户不认识 `start_asset_extraction`,要说「生成角色 / 场景 / 道具统筹表」。
- **结合当前结果给具体建议**,并且能一步接着做(用户回「1」或「生成统筹表」你就能继续)。
- **会扣费的建议要注明**:出图 / 视频 / 广告 / 统筹表写「(会扣积分,先报预估再确认)」;剧本生成写「(会扣积分,先报预估再确认,实际按 Token 结算多退少补)」。
- 一般给 2~3 条,最相关的放最前;确实已经到终点时才只做小结。

常见场景的建议示例(按实际结果调整):

- **列出项目 / 剧本后**:①看某个项目的分集与剧本 ②为它生成统筹表 ③用一句灵感创作一部原创短剧
- **项目详情后**:①生成统筹表 ②给角色批量出定妆图(会扣积分,先报预估)③为某集生成分镜提示词并批量出视频
- **统筹表生成后**:①挑角色或场景批量出图(会扣积分,先报预估)②导出统筹表 ③生成分镜提示词
- **分镜提示词生成后**:①查看或修改某镜提示词 ②选分镜批量生成视频(会扣积分,先报价)③补一条全局提示词
- **OC / SI 任务详情后**:①查看当前阶段草稿 ②确认推进到下一阶段 ③生成集纲或剧本(会扣积分,先报预估再确认)
- **用户附了文件或图片后**:①上传到 Nova(会先复述文件名请你确认)②剧本上传后转成项目或发起改编 ③图片上传后作为广告参考图
- **出图 / 成片完成后**:①对某张不满意就重出 ②继续出下一类资产 ③导出成品或取链接
- **广告 Agent 卡住时**:余额不足 → 充值后继续;部分失败 → 重试失败项;方案不满意 → 重新规划(会再扣费)或取消
- **剧本某集不满意**:①改集纲后重写该集 ②直接重写该集(会扣费)③加批注让 AI 精修

## 发起创作前先引导用户(OC / SI 必看)

用户想「写原创短剧」或「改编剧本」时,**不要空手直接调 `oc_create_task` / `si_create_task`,也不要只说一句「请提供信息」**。用下面的模板告诉用户:要给什么、举个例子、会得到什么、从哪步开始扣费。用户给了灵感或剧本就可以开始,可选项不必逼着填满。

### 原创短剧——用户说「我想做原创短剧 / 帮我写个短剧」时

> 好的,创作一部原创短剧我需要:
> - **剧本名**(必填):比如「豪门弃妇的逆袭」
> - **一句创作灵感**(必填,越具体越好):比如「60 集,豪门联姻,女主被退婚后重生复仇、打脸渣男贱女」「战神归来,隐藏身份进城当赘婿,受尽白眼后暴露实力」
> - 可选补充(不填就按默认):目标集数、题材(都市 / 古装 / 悬疑等)、主题关键词(最多 3 个)、每集长度(快进 / 标准 / 细展)、方向侧重(爽感节奏 / 情感浓度等)
>
> 之后会怎样:我会先生成 **6 个创意方向**给你挑;选定后逐阶段推进——**总纲·人物·卡点 → 素材库 → 集纲 → 逐集剧本**,每一步你都能看草稿、修改、再确认。⚠️ 从生成 6 个方向开始,**每一步推进都会扣真实积分**。每一步我都会先告诉你预计消耗多少(实际按真实 Token 结算、多退少补),你同意后再做。

用户给出灵感后再调 `oc_create_task`(inspire 模式)。用户只说「随便写一个」时,就用一个具体的示例灵感开始,并说明随时可以调整,不要卡住不动。

### 剧本改编——用户说「把这个剧本改编 / 换皮成新短剧」时

> 改编需要一部**参考剧本**:
> - 直接**把剧本文件附在对话里**(.txt / .docx / .pdf,≤50MB,我来上传到 Nova),或**粘贴全文**,或给一个**可下载链接**
> - 可选:目标集数、题材、目标市场
>
> 之后会怎样:我先识别拆解原剧(识别按用量扣少量积分),然后逐步推进——**换皮方向 → 策划映射 → 集纲 → 逐集新剧本**,可以按集号区间生成,也可以导出剧本或映射表。⚠️ 每次确认推进、生成集纲或剧本都**扣真实积分**,我会先告诉你预计消耗多少(实际按真实 Token 结算、多退少补),你同意后再做。仅可用于你有权改编的剧本。

### 通则

- 发起任何生成任务前,用一句话说清:大概要等多久、会产出什么、会不会扣费。
- 用户信息不全时,先用默认值跑起来,并告诉用户「我先用默认的 X,想改随时说」,不要反复追问。**例外:生成用的模型必须由用户选**(除非用户明确说「用默认 / 你定」)。

## 附录 · 参数细节(调用前按需查阅)

### 广告 Agent
- `control_ad_agent` 各 action:
  - confirm_plan:方案就绪时确认,taskId 传 planningTaskId;不扣费,系统随后建工作流并自动报价。
  - cancel:取消进行中的任务,不扣费。
  - retry_failed:部分失败或失败时重试失败步骤。🔴 收费步骤会重新报价并出现 pendingApproval。
  - continue_after_balance:余额不足、用户已充值后继续。🔴 会重新报价。
  - replan:重新规划,可带 adjustmentPrompt(≤4000 字)和 targetStepKey。🔴 可能再次触发方案确认与报价。
  - requote:对某一步(targetStepKey,即 steps[].stepKey)重新报价。
  - regenerate:对某一步原位重生,只支持 generateReferenceImages / generateCharacterImages / generateVideos,可带 adjustmentPrompt。🔴 会重新报价。
  - undo:撤销任务写到画布上的节点,不扣费也不退费,taskId 取 undoableTaskId。
  - cancel_questionnaire:需要 questionnaireId,以及 version 或 sessionId 之一。
  - decide_proposal:需要 proposalId + decision。apply 可用 itemIds 只应用部分;reject 可带 reason(≤500 字)。决定前先向用户复述提案内容。
- 凡是重新报价的,都要复述新的预估、取得同意后再 `approve_ad_agent_cost`(需 approvalId + version)。
- skill 取值(以服务端为准,传错会返回可用清单):product-story-ad 高端商业广告 TVC(默认)/ story-advertising-original-canvas 短剧剧情广告 / ecom-product-visual-kit 产品视觉全案。
- assetIds 传 `list_assets` 的 coverAssetId 或 images[].id(不是资产 id),最多 10 个,并在 content 里写明素材用途。
- 画面偏好:aspectRatio = smart(默认)/ 1:1 / 16:9 / 9:16 / 4:3 / 3:4;图片 resolution = smart / 1K / 2K / 4K;videoResolution = smart / 480P / 720P / 1080P / 4K。
- executionMode:auto(推荐)确认方案后自动报价、确认费用后自动生成;manual 只搭工作流,媒体要到网页逐个节点生成,不推荐。
- `answer_ad_agent_questionnaire` 的 answers 写法:`[{"questionKey":"media.aspect_ratio","optionIds":["ratio_16_9"]},{"questionKey":"free_text_q","customText":"..."}]`。optionIds 取 pendingQuestionnaire 里题目的 options[].id,必答题要全部覆盖。
- `view=results` 的链接是临时签名链接,数小时后失效;urlSource=graph 表示没能重新签名,链接可能已过期。

### 原创短剧 OC
- `oc_create_task`:inspiration 如「60 集狼人契约婚姻…」;genre 如「高手下山类」「豪门恩怨类」;background 如「现代都市」「古代架空」;role 如「霸道总裁」「战神」;themes 如 ["复仇","隐藏身份"](超过 3 项会截断);episodeDensity:fast 约 600 字 / standard 800~1000 字(默认)/ detailed 约 1200 字;segmentMode:card1 一卡 / card2 二卡;manual 模式直接进入 setting 手填。
- 确认阶段会自动生成什么:确认 plan → 总纲与人物;确认 setting → 素材库;确认 material → 一卡段集纲;确认 outline → 前 3 集剧本。
- `oc_get` 的 stage:plan 6 个创意方向 / setting 总纲·卡点·人物 / material 素材库 / outline 集纲 / script 剧本。view=status 里 alive 看 lastActivityAt,长时间没动静多半是慢而不是卡住。批注状态:pending / refining / done / adopted / rejected。
- `oc_generate`:target=outline 只用于 inspire 二卡模式,生成剩余集纲。target=script 的 mode:range 闭区间(需 fromEp / toEp)、all 重生全部有集纲的集、missing 只补未完成的集(续跑不重复计费)、留空由后端自动分段。部分集失败就用 missing 续跑,不要对失败的任务一直轮询。
- `oc_regenerate`:
  - episode:重写单集正文,direction 只对本次有效。
  - outline_episode:重生单集集纲,该集剧本会被标为待更新。
  - episode_with_outline:用 core / hookText **整体覆盖**该集集纲(不是合并),必须先取现值再改;core ≤2000 字、hookText ≤500 字、reason ≤1500 字,hookType 不会保存。
  - draft:清空并重生 plan / setting / material 草稿,direction ≤2000 字;任务生成中会返回 409。
  - card2:仅 inspire 模式且总纲含第二卡点时可用。
- `oc_annotation`:add 的 startOffset / endOffset 是该集正文的字符位置(先 `oc_get(view=episodes)` 取正文),后端会扩到整行;tag ≤50 字、note ≤2000 字。refine 异步执行、按 Token 结算,精修中再调会返回 409。update 的 proposalAction:adopt / reject / selectVersion(vidx 从 0 开始)免费,regenerate 🔴。删除批注不影响已采纳写回的正文。
- `oc_task_control`:cancel 可重复调用,只取消逐集剧本生成;revert 会丢弃下游全部产物且不会自动重生;delete 删除整个任务及其全部草稿、集纲、剧本、批注,不可恢复,先复述标题确认。
- `oc_export` 只导出已生成且正文非空的集,eps 写法如「1,2,5」。`oc_edit_episode` 的 content 会整集替换。
- `oc_estimate_credits` 的 action 与扣费工具对应:create → oc_create_task;stage → oc_confirm_stage;outline → oc_generate(target=outline);script → oc_generate(target=script)(配 fromEp / toEp 或 mode);rewrite → oc_regenerate(target=episode)。

### 剧本改编 SI
- `si_create_task`:fileUrl 必须是 http / https、公开、未过期、无防盗链的直链;与 rawText 同时给时以 fileUrl 为准。识别按 Token 计费、没有预估;返回的 nextStepEstimatedCredits 是下一步确认 upload 的预估。market:domestic 国内(默认)/ overseas_na 北美 / overseas_sea 东南亚 / overseas_me 中东 / overseas_jk 日韩。
- `si_confirm_step`:outline / script 确认免费;确认 plan = 生成全部集纲;确认 upload 时可修正目标集数与时长区间。
- `si_get`:view=task 含 currentPhase / sourceReady / staleOverview;view=status 没有运行中的任务时返回 status=none(正常),失败时按 error 处理,不要一直轮询;view=source_digest 未完成时返回 {};逐集状态 pending / queued / generating / done / failed;step:decompose 原剧拆解 / skin 换皮方向 / plan 策划映射表。
- `si_generate`:可以先生成一卡区间,再分段生成剩余集;失败只重发失败的那段。
- `si_regenerate`:episode 即使已完成也会覆盖重写并计费,只想补未完成的集请用 `si_generate(target=script)`;step 重生 decompose / skin / plan / outline 且不回拨前沿,step=script 只清除待更新标记;mode(keep_genre 保留题材 / swap_shell 换外壳 / same_type_variant 同类差异化)只在 step=skin 时可填;retry 的 retryKind:generation 需要 generationId(来自 `si_get(view=status)`),recognize 用于上传阶段识别失败(轮询 sourceReady),digest_episode 需要 sourceEpisodeNo(原剧集号,不是目标集号)。
- `si_estimate_credits`:stage 对应 si_confirm_step(upload = 原剧摘要 + 拆解;decompose → 换皮;skin → 策划;plan → 全部集纲);script 预估含关键集加价与首卡自审;polish 的 kind:revise / summary / regenerate / instant,revise / summary 可传 annotationCount(默认取待处理批注数),错别字检查没有预估。
- `si_export`:mapping 是人物 / 卡点 / 名场面映射表 XLSX,下载链接短期有效。`si_polish_ensure` 在剧本还没生成时返回 422。

### 剧本润色
- `polish_annotation`:add 需要 episodeId / startOffset / endOffset(可选 originalSegment / tag / note);update 需要 annotationId,可改 tag 和 note,没传的字段保持不变;delete 需要 annotationId;apply_proposal 需要 annotationId + proposalAction(apply 写回正文 / reject / select 切换版本,需 currentIdx,从 0 开始)。tag 可选:精简 / 扩写 / 改台词 / 加冲突 / 调节奏 / 人设一致 / 逻辑连贯 / 删除。
- `polish_run`:各 kind 都扣积分;regenerate_annotation 需要 annotationId,可带 direction。标准流程:`si_polish_ensure` → `polish_get_task` → `polish_annotation(action=add)` → `si_estimate_credits(action=polish, kind=revise, annotationCount=N)` → `polish_run(kind=revise)` → 轮询 `polish_get_task` 看 annotations[].proposal → `polish_annotation(action=apply_proposal)`。
- `polish_instant_refine`:参数与 add 相同,另加 direction,一步完成「加批注 + 出方案」。
- `polish_edit_episode`:mode=full 先用 `polish_get_task` 取 finalText 再整集覆盖;mode=typo 需要 wrong 和 right,可带 context 帮助定位。

### 项目 / 剧本 / 统筹表管理
- `manage_library`:target=project 时,update 改 title / description(description 传空串可清空),delete 软删到回收站,restore 恢复;target=script 时,update 改 title / purpose / scriptNo / genre / platform / performanceNote,delete 软删。⚠️ delete 前复述名称确认。
- 项目用途 purpose 取值:domestic_live_action 国内真人短剧(默认)/ overseas_live_action 海外真人短剧 / animation_2d_3d 2D/3D 漫剧 / narrated_comic 解说漫 / other 其他。
- `edit_breakdown_entry`:entryId 来自 `get_breakdown(view=table)`。update 只支持 episode(idx / title,可为 null)和 shot(shotNumber / timeOfDay / intExt / type / script / notes / mainLocationName / subLocationName,以及 characterNames / itemNames / transportNames / extraNames / specialSpeciesNames 这些数组会整组替换,outfitPairs 写成 [{character,outfit}]);patch 只放要改的字段,不支持的字段会被拒绝并列出。delete 删除资产实体时会解除场次里的引用;返回 needsConfirmation + pendingOrphans 时,可以再调 delete 清理。

### 上传 / 模型 / 出图
- 上传限制:kind=script 支持 .txt / .docx / .pdf,≤50MB,可带 purpose / title;kind=image 支持 .png / .jpg / .jpeg / .webp,≤20MB,宽高 300~6000px,比例 0.4~2.5,projectId 必填,带 canvasId 会同时放到画布上。
- `list_models`:type=image 的 value 用于出图工具的 model,type=video 的 value 用于批量视频的 videoModel。default=true 是平台默认(只在用户说「用默认」时选);value=auto 是智能路由;durations 含 -1 表示支持自适应时长;分辨率不区分大小写;refImage / maxRefImages 决定能否用参考图、最多几张。
- `start_asset_generation_preview` 的 scope:character / scene / item,可逗号分隔多选(选角色会包含其全部造型)。
- `approve_asset_generation` 只出一部分:itemIds(items[].itemId)/ variants(face_closeup 定妆照、full_body_lookbook 造型全身、extra_group 群演群像、creature 特殊物种、scene、item、vehicle)/ excludeRoleKinds(extra 群演、special_species 特殊物种、supporting 配角)/ entityIds;多个条件取交集,不传就是全部,按实际条数计费;items 可覆盖单条提示词。预估是下限,参考图输入可能有少量额外费用。
- `refine_asset_prompt`:传了 positivePrompt 就以它为基础,再按 userNote 改写。
- `get_asset_generation(view=status)`:状态 pending / running / succeeded / failed / cancelled,用 nextCursor 翻页。
- `generate_asset_image`:ratio 如 1:1 / 16:9 / 9:16,留空用模型默认;refAssetIds 取 `list_assets` 的 coverAssetId / images[].id,数量受 maxRefImages 限制,且模型需支持参考图(refImage=true)。
- `control_asset_image_job`:cancel 取消运行中的任务(已完成的部分不退费);delete 只删任务记录,不删已入库的图,先确认。

### 分镜提示词 / 批量视频
- `start_storyboard_job(kind=split)`:前提是该集已有统筹表场次、且项目剧本里能定位到这一集;每次最多 20 集;includeGenerated=true 会强制重切已就绪的集(覆盖已有场次原文)。
- `start_storyboard_job(kind=prompt)`:要求 promptGate=ready;includeGenerated=true 才覆盖已有提示词的集;modelCode 留空用项目设置或平台默认。
- `create_batch_video_job`:shotIds / videoModel / ratio / resolution / durationSec / videoMode / generateAudio 必须与报价时完全一致;first_frame 需要模型支持;startAt 写法如 2026-10-15T00:00:00+08:00;name 会显示在任务中心;shotIds 最多 1000 个。
