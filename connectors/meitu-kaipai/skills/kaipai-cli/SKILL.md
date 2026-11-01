---
name: kaipai-cli
description: 通过开拍 CLI 调用美图的智能视频创作与媒体处理能力，支持登录、会话续聊、任务查询、恢复和下载。明确使用 kaipai 或处理已有开拍任务时使用；具体媒体处理优先使用已安装的对应业务 Skill，缺少专用入口时按本指南执行。
metadata:
  author: 开拍
  version: 1.0.13
  cli-package: meitu-kaipai-cli
  cli-tested-version: 0.1.14
  cli-compatible-range: ">=0.1.12"
---

# 开拍 CLI 使用说明

依赖 `meitu-kaipai-cli@latest`，测试基线为 `0.1.14`，运行最低版本为 `0.1.12`。通过随包[启动脚本](scripts/run-cli.mjs)在每次调用前解析 latest；后续 CLI 发布无需逐次更新连接器。测试基线不代表未来版本已验证，具体命令以当前 help/contracts 为准。这是命令导航指南，没有单一业务输入表。默认简体中文，用户指定其他语言时跟随用户。

首次执行读取[平台接入](references/platform.md)，解析入口、检查版本和所需命令 help，正式提交前完成登录检查。JSON 字段或媒体限制不明确时，按平台说明查询 `kaipai contracts` 的对应条目；使用通用创作、登记素材或配置诊断时读取[命令使用补充](references/commands.md)；遇到输出解析、问询或异常时读取[运行与恢复](references/runtime.md)。

## 按意图选择入口

已安装对应业务 Skill 时优先使用其完整业务流程；通过本连接器承接的任务仍统一使用本指南的启动脚本，不执行其他 Skill 的固定版本准备脚本或旧全局入口。未安装时按下表及本指南独立执行，不假定存在其他 Skill 的文件。

| 用户意图 | 业务 Skill／命令 |
| --- | --- |
| 一般视频创作、封面或自然语言续聊 | `chat`，向服务端传达素材与创作目标 |
| 已有视频整体包装／增强氛围／多条分别套模板 | `smart-template`／`smartedit`，交付成片 |
| 动态字幕 | `dynamic-caption`／`subtitle` |
| 图片、视频或混合素材剪成视频 | `smart-montage`／`mixed-cut analyze`，方案确认后 `generate` |
| 图片／视频画质修复 | `kaipai-image-repair`／`tool image-repair`；`kaipai-video-repair`／`tool video-repair` |
| 图片文字及文字水印消除 | `kaipai-image-remove-watermark`／`tool image-remove-text` |
| 普通视频去字幕／去水印、自动消除 | `kaipai-video-remove-subtitle`／`kaipai-video-remove-watermark`，均使用 `tool video-remove-auto` |
| 明确指定专用 CLI 命令 | `tool video-remove-subtitle` 或 `tool video-remove-watermark`；属于独立模式，按实际请求选择 |
| 查询会话／当前交互／任务及最新产物 URL | `history / history-detail / task-progress` |
| 回复当前问询或批准／拒绝 | `reply`；先读取实际交互并核对授权 |
| 明确取消远端执行／本地保存／权益入口 | `cancel / download / purchase` |
| 查询账号／客服入口 | `user-info / feedback` |

视频去字幕／去水印统一使用 `video-remove-auto`，由服务端自动识别、清理并修复画面。素材和目标明确时按已有授权直接执行；指定保留元素等要求按平台说明核对调用方式。用户明确指定专用 CLI 命令时，使用对应独立模式。

图片文字消除用于清理文字遮挡并修复背景；图片和视频修复用于增强清晰度、细节与视觉质量。画面噪点和音轨噪声按各自能力选择入口，具体调用参数查询当前 help 与 contracts。

## 收集、上传与提交

1. 从当前请求取得真实素材和明确目标。单素材工具／字幕每次一个；目标不明才询问，不自动代选。混剪支持 1–20 个图片／视频，保留选择顺序，不能套用单素材规则。已授权逐个处理时分别调用并记录任务，不擅自扩大批次。
2. 本地素材通过 `--image-file / --video-file` 传入；所有远程素材先按平台说明下载原资源，包含历史产物及混剪接字幕的视频 URL。下载失败时请用户自行下载并提供本地文件，收到后继续；只有媒体 ID 时先查询原会话取得真实 URL，再下载。
3. 新任务省略会话；续聊或继续处理添加 `-r '<session_id>'`。CLI 先校验本地素材、上传取得自有 CDN URL，再提交业务；常规 `chat / tool / subtitle / mixed-cut analyze` 不先 `create-room / add-media`。
4. 默认按当前命令 help 直接传独立参数。复杂嵌套输入可使用参数文件；只检查或诊断时，在支持的命令上按需追加 `--validate-only --json`，两者均非普通提交的必经步骤。参数文件不能与业务 flags 混用；`chat / reply` 等不支持预检的命令不添加该选项。
5. 普通创作可用 `kaipai chat -p '用户的实际需求'`；附件先准备成本地文件，使用当前 help 支持的文件参数。按平台说明应用默认值并完成登录检查，用户已授权且输入齐全时直接执行，不额外重复确认。
6. 保留原始 URL／用户文件、实际本地路径、`session_id / room_url` 和全部 Task ID。混剪保留完整素材顺序和重复项，缺失时等待补充；处理结束且无需恢复后清理本次临时文件，保留用户原文件。

## 网感模板：生成与交付

已有视频整体包装、组合字幕／音乐／贴纸使用网感模板；仅字幕走字幕，多素材合成一条走混剪。仅“多条视频剪辑”无法区分两者时补问。目标和视频齐全直接执行，不需要 Brief 确认。

1. 每条真实本地视频调用 `kaipai smartedit --video-file '<路径>'`；远程视频先下载。未指定、空白或要求随机时省略模板参数，告知采用随机模板；指定真实 SEC ID 才加 `--template-material-id '<ID>'`。不按名称／截图猜 ID，不查询内网池。CLI 仅验证视频类型，不套用字幕的本地媒体上限。
2. 多条分别用 `--detach` 受理后继续下一条，每条独立 Session。CLI 上传视频后通过 URL references 直接调用 chat，由服务端创建独立会话；不要手工预先创建会话或登记素材。保存输入、Session、Run、Task、实际模板和成片 URL。一条失败不阻塞其余任务。
3. 以本次 `TASK_STATE_COMPLETED` 和 ready 视频确认成片；有 `smartedit_result` 时记录实际模板 ID；配方与工程信息不作为交付条件。accepted 不是完成；只有 Session 时用 history-detail 恢复，有 Task 时用 task-progress，run_id 不能代替 Task。
4. 成功一条即交付一条，提供完整可播放或下载的成片链接，保留 URL 查询参数。不创建或打开编辑项目，不拼接编辑链接。
5. 生成断流／超时不重发收费请求；无效模板 ID 展示原错误，不自动改 random 再生成。下载失败只刷新原结果 URL 或重试下载，部分失败保留其他成功成片；费用与权益以服务端实际结果为准。

## 字幕与混剪的业务关口

- 字幕根据可识别语音或已有可用字幕时间轴生成；未配置有效 `subtitleMaterialId` 时告知采用随机样式。具体文字或样式编辑要求先核对当前命令和可用样式；清理原画面字幕时按用户目标衔接视频去字幕流程。
- 混剪先分析素材与主题，不能将图片输入误判为缺少口播。读取真实 `mixed_cut_brief`，按 `(session_id, brief_id)` 更新；pending 时只读恢复，failed、缺失或未知类型不生成。
- 展示 ready 的真实方案：`talking_mixed_cut` 展示主视频、补充素材、目标时长与只读 `a_roll_text`；`material_mixed_cut` 展示实际素材安排、脚本、配音信息与目标时长。笼统创作授权不能替代当前方案确认；确认后沿用原会话和 Brief 生成。
- 仅口播分支可用生成请求中的 `answer` 对象调整当前方案已分析素材和 5–180 秒目标时长；素材分支省略 `answer`。媒体项使用真实 `short_id / kind`，嵌套结构查询当前生成命令契约，不传 URL 或本地路径。新增／替换源素材或修改素材分支要求时，先下载远程原资源，再在原会话重新分析完整本地列表并确认新方案。
- 分析用于产出创作方案；按真实 Brief 的 ready 状态和用户确认执行生成，预检与 `reply --approve / --answer` 均不替代该步骤。节奏、口误优化、画幅和目标时长等要求完整写入分析 Prompt，字幕按用户需要衔接。

## 跟进与交付

- 分别读取原命令 stdout 的完整 HTTP JSON／SSE 帧和 stderr 的 `source:"cli"` 事件，默认持续观察，不同时开启第二个轮询。
- 媒体任务需 `TASK_STATE_COMPLETED` 且有本次可用产物 URL 才交付；HTTP 200、退出码 0、流结束、Session idle 或 `end.reason=result` 不单独证明成功。无 Task 的文本可能在请求澄清，按实际内容处理，未知状态不视为完成。
- 及时交付全部可用 Part，优先宿主原生预览／附件，否则提供完整链接并保留查询参数；部分成功先交付，有实际 `room_url` 时附会话入口。下载核对逐项结果，不把封面、输入或历史结果当新产物。
- 断线、超时或未知提交状态时先查询原任务，不自动重发业务命令；仅在失败原因已修复且用户授权后重试。字幕或下载失败不重做已成功生成；具体恢复、交互和本地保存方式见运行说明。
