---
name: salesnail-instructor
description: 通过 SalesNail Connector 完成游戏设计与生成、参数调整、教学材料、上架发布和创建课程的讲师全流程。
version: "0.2.0"
author: "SalesNail Team"
---

# SalesNail 讲师

本 Skill 面向普通讲师、课程设计者和培训运营人员。用户只需要描述培训目标和业务场景，不需要理解 MCP、API、Schema、Token、环境变量或命令行。

## 用户连接

当 Connector 尚未授权或登录已失效时：

1. 请用户点击“连接 SalesNail”。
2. 用户在浏览器中输入自己的 SalesNail 账号并确认读取、写入权限。
3. 授权完成后继续原请求，不要求用户重复描述任务。

不得要求用户在对话中发送密码、访问令牌、环境变量或技术配置。

## 总体操作原则

- 新游戏必须先选择模板、读取设计约束并校验，再开始生成。
- 修改参数、保存教学材料、上架和创建课程都必须先预览，再等待用户明确确认。
- 每次写操作使用稳定且唯一的 clientRequestId，避免重复生成、重复扣费或重复建课。
- 只操作当前登录讲师拥有或可编辑的资源，不猜测 gameId、scriptId、cardId、npcId、chanceId 或 courseId。
- 首次上架可能收费人民币 9.90 元。必须先展示预览返回的实际金额并等待确认。
- 不提供删除工具。取消生成任务也不会删除已经创建的业务数据。
- 课程时间必须使用带时区的绝对时间，默认向用户确认 Asia/Shanghai。
- 完成写操作后必须重新读取结果，向用户说明实际写入状态。

## 推荐完整流程

1. 调用 salesnail_get_teacher_context，确认登录身份、角色和额度。
2. 调用 salesnail_list_game_templates 选择模板。
3. 调用 salesnail_get_game_design_schema 获取模板约束。
4. 收集卖方、客户、项目、标题和五类决策者人数。
5. 调用 salesnail_validate_game_design 展示规范化设计和警告。
6. 用户确认后调用 salesnail_start_game_generation。
7. 轮询 salesnail_get_generation_job，直到 succeeded 或 failed。
8. 调用 salesnail_get_game 检查 NPC、商机、卡牌、轮次、语言和材料。
9. 参数修改使用 salesnail_preview_game_patch，再使用 salesnail_apply_game_patch。
10. 教学材料使用生成、查询、预览、提交四步流程。
11. 上架使用 salesnail_preview_publish_game 和 salesnail_publish_game。
12. 建课使用 salesnail_preview_create_course 和 salesnail_create_course。

常规商务游戏的 decisionMakerCounts 建议为 [5, 3, 3, 3, 3]，预期生成 22 个 NPC。只有用户明确提出其他结构时才调整。

## 可用工具

### 发现与身份

| 工具 | 用途 | 主要参数 | 返回与后续 |
| --- | --- | --- | --- |
| salesnail_get_capabilities | 获取模板、材料类型、写操作和当前限制 | 无 | 用于开始任务前确认能力边界 |
| salesnail_get_teacher_context | 获取当前讲师、角色、课程额度和 AI 余额 | 无 | 登录后优先调用；额度不足时先告知用户 |
| salesnail_list_game_templates | 列出 business、medical、fmcg、english 模板 | 无 | 根据行业和语言选择模板 |
| salesnail_get_game_design_schema | 获取指定模板的设计字段和约束 | template | template 只能是 business、medical、fmcg、english |

### 游戏设计与生成

| 工具 | 用途 | 主要参数 | 返回与后续 |
| --- | --- | --- | --- |
| salesnail_validate_game_design | 校验并规范化设计，不写入 SalesNail | template、title、playerCompany、customer、project、decisionMakerCounts | 展示警告和规范化设计后再生成 |
| salesnail_start_game_generation | 启动真实 Creator 生成流程 | 上述设计字段、clientRequestId，可选 outlineTimeoutMs | 立即返回 jobId；不得在任务运行时重复启动 |
| salesnail_get_generation_job | 查询生成进度、报告、截图和最终游戏引用 | jobId | 持续轮询；成功后读取完整游戏 |
| salesnail_cancel_generation_job | 停止仍连接的生成进程 | jobId | 属于写操作；说明已产生的数据不会被删除 |

title 最多 10 个字符。playerCompany、customer、project 必须包含足够的业务事实。不要替用户虚构会显著影响场景质量的公司、客户或项目事实。

### 游戏读取与参数修改

| 工具 | 用途 | 主要参数 | 返回与后续 |
| --- | --- | --- | --- |
| salesnail_list_games | 查询当前用户可编辑的游戏 | keyword、enabled、pageNum、pageSize | 从返回结果中取得真实 gameId 和 scriptId |
| salesnail_get_game | 获取剧本、轮次、卡牌、NPC、商机和材料 | gameId 或 scriptId | 修改、生成材料、上架或建课前调用 |
| salesnail_preview_game_patch | 校验参数修改并生成确认信息，不写数据 | gameId 或 scriptId、operations | operations 支持 update_game、update_round、update_card、update_npc、update_chance |
| salesnail_apply_game_patch | 应用已预览的修改并回读验证 | confirmationId、clientRequestId | 只有用户确认预览内容后调用 |

单次 preview 最多 10 个 operations。修改卡牌、NPC 或商机时必须使用 salesnail_get_game 返回的真实对象 ID。

### 教学材料

| 工具 | 用途 | 主要参数 | 返回与后续 |
| --- | --- | --- | --- |
| salesnail_start_material_generation | 异步生成教学材料草稿，不立即保存 | gameId 或 scriptId、materialTypes、clientRequestId，可选 modelName | 返回 jobId |
| salesnail_get_material_job | 查询材料生成状态和 HTML 草稿 | jobId | 检查语言、行业一致性和内容完整性 |
| salesnail_preview_material_commit | 预览将追加到剧本的材料及分组 | jobId | 向用户展示标题和目标分组 |
| salesnail_commit_materials | 保存已确认的材料 | confirmationId、clientRequestId | 保存后调用 salesnail_get_game 回读 |

材料类型包括讲师手册、学员任务书和复盘问题等服务端返回的受支持类型。草稿未成功完成时不得提交。

### 上架发布

| 工具 | 用途 | 主要参数 | 返回与后续 |
| --- | --- | --- | --- |
| salesnail_preview_publish_game | 校验上架名称、简介、封面和预计费用 | scriptId、name、details、可选 imageUrl | name 最多 15 字，details 最多 500 字；展示实际费用 |
| salesnail_publish_game | 使用有效确认信息上架 | confirmationId、clientRequestId | 用户明确确认费用和内容后调用，再回读上架状态 |

没有封面地址时不能上架。不得把 preview 当成已经发布。

### 创建课程

| 工具 | 用途 | 主要参数 | 返回与后续 |
| --- | --- | --- | --- |
| salesnail_preview_create_course | 校验已上架剧本和课程参数 | scriptId、courseName、studentNumber、teamNumber、startTime、endTime、courseType、mode、companyName、description | 展示准确日期、时区、人数、组数、类型和模式 |
| salesnail_create_course | 创建已确认的课程 | confirmationId、clientRequestId | 创建后返回并核对 courseId 和课程参数 |

studentNumber 为 1 至 999，teamNumber 为 1 至 99。endTime 必须晚于 startTime。courseType 为 formal 或 demo，mode 为 multi_player 或 single_player。

## 确认要求

以下操作必须等待用户明确表达“确认”“继续”“执行”等同意：

- salesnail_apply_game_patch
- salesnail_commit_materials
- salesnail_publish_game
- salesnail_create_course
- salesnail_cancel_generation_job

不得根据用户沉默、模糊回复或之前对其他步骤的确认推断同意。

## 错误处理

| 错误码 | 处理方式 |
| --- | --- |
| AUTH_REQUIRED | 提示用户重新点击“连接 SalesNail”，不要索取密码或令牌 |
| SCOPE_REQUIRED | 说明当前授权缺少读取或写入权限，引导重新授权 |
| FORBIDDEN_RESOURCE | 停止操作，重新列出当前用户拥有的游戏，不尝试绕过 |
| VALIDATION_FAILED | 用业务语言说明缺失或不合法字段，修正后重新 preview |
| CONFIRMATION_REQUIRED | 重新执行对应 preview 并等待用户确认 |
| CONFIRMATION_EXPIRED | 预览已过期，重新读取当前数据并生成新的 preview |
| NOT_FOUND | 重新列出资源并确认用户选择，不猜测 ID |
| JOB_IN_PROGRESS | 继续轮询现有 jobId，不创建重复任务 |
| JOB_FAILED_RETRYABLE | 只重试失败阶段，并向用户说明原因 |
| JOB_FAILED_TERMINAL | 停止自动重试，提供报告和可恢复步骤 |
| UPSTREAM_TIMEOUT | 保留 jobId 或 clientRequestId，稍后查询状态，避免重复写入 |
| UPSTREAM_ERROR、UPSTREAM_INVALID_RESPONSE | 给出安全的业务错误，不展示内部地址、响应体或堆栈 |
| CONFIG_ERROR、INTERNAL_ERROR | 告知服务暂不可用并建议联系支持，不泄露内部配置 |

## 完成时的用户摘要

最终只向用户展示有业务价值的信息：

- 模板和确认后的游戏设计。
- 生成状态、游戏名称及必要的游戏引用。
- 已应用的参数差异。
- 教学材料标题和保存状态。
- 上架状态及实际或预计费用。
- 课程名称、准确时间、人数、组数和课程引用。
- 尚未完成、需要网页视觉检查或需要平台人员处理的步骤。

## English operating summary

Use the same safe workflow for English-speaking instructors: connect the user's own SalesNail account in the browser, validate a design before generation, poll existing jobs instead of duplicating them, preview every data-changing action, obtain explicit confirmation, and read the result back after applying it. Never request credentials in conversation and never expose internal IDs unless they are needed for troubleshooting or audit.
