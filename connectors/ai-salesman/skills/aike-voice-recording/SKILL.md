---
name: aike-voice-recording
display_name: 上传对话录音
display_name_en: Voice Recording
description: 查看与上传对话录音（AI 快记）：查询录音的转写全文、AI 总结、关键词与关联客户，支持按客户名/展会名/快记编号/客户绑定状态筛选近期快记；用户提供了录音文件时，可上传并自动转写生成快记。当用户说"看看最近的录音""这条录音的 AI 总结是什么""转写这段对话""帮我把这段录音上传存档"时触发。
description_zh: 查询录音的转写/AI 总结/关键词与近期快记列表；提供录音文件时可上传并自动转写。
description_en: Query recording transcripts, AI summaries and recent voice memos; upload a recording for transcription when the user provides the file.
category: sales-mobile
version: 1.4.0
author: AI销客
---

# 上传对话录音

当用户需要查看录音的转写/AI 总结/近期快记，或上传对话录音转写存档时，按以下步骤执行：

## 场景一：查询快记（优先尝试）

1. **确认工具可用**：本技能依赖 gsales 连接器的 `get_recording` / `list_recent_recordings` / `presign_file_upload` / `upload_recording` 工具。当前环境没有这些工具时，引导用户先安装并连接「外贸销客」连接器；**不要编造录音数据**。
2. **列表**：`list_recent_recordings({ ... })`（时间倒序）按需筛选：
   - `customerName`（按客户名）/ `exhibitionName`（按展会名）/ `recordCode`（按快记编号）/ `status`（如 `"recognized"`）
   - `hasCustomerAssociation`：客户绑定状态，`"bound"`=仅已关联 / `"unbound"`=仅未关联（**字符串枚举**，不要传布尔值）
   - `page`（默认 1）/ `pageSize`（默认 10，上限 50）/ `full`
   - 返回 `{ total, page, pageSize, items[] }`，`items` 每项：`id` / `recordCode` / `name` / `status` / `aiSummary` / `aiKeywords` / `durationSeconds` / `createdAt` / `customerNames` / `exhibitionName`
3. **详情**：`get_recording({ "id": "<uuid>", "full": false })`——恒返回 `id` / `status` / `recognizeError`；识别完成后追加 `name`（标题）/ `durationSeconds` / `startTime` / `endTime` / `transcript`（转写全文）/ `transcriptChat`（对话式转写）/ `aiSummary`（AI 总结）/ `aiKeywords` / `customerNames`（关联客户）/ `recognizedAt` / `skillResults`（技能卡）
4. **呈现**：先给 AI 总结 + 关键词 + 关联客户，用户要全文再给完整 `transcript`，不要整段倾倒。**空列表**时如实告知"暂无快记记录"，**不要编造**。

## 场景二：上传转写

1. **前提**：工具可用，且**文件真实存在于当前环境**（对话附件/文件路径）。用户说"上传录音"但未提供任何文件时：请用户提供录音文件（在对话里发送文件），或引导其在外贸销客 App 内上传（App 内同样自动转写生成快记），并可先帮用户查询已有快记；**不要虚构文件路径，不要在无文件时调用上传工具**。
2. **申请直传凭证**：`presign_file_upload({ "kind": "audio", "file_ext": "m4a" })`（`file_ext` 传裸扩展名，不带点）拿到 `uploadUrl` / `objectUrl` / `contentType`；凭证 **10 分钟**有效，过期重新申请。
3. **直传字节**：用 Bash 执行 `curl -T <录音文件路径> "<uploadUrl>" -H "Content-Type: <contentType>"`。**curl 失败或当前环境不可出网时停止上传流程**，如实告知用户，并引导其在外贸销客 App 内上传。
4. **交接**：直传成功后 `upload_recording({ "object_url": "<objectUrl>" })`，返回 `id` + 初始状态。可选 `exhibition_id`（uuid）关联展会、`start_time` / `end_time`（ISO 8601，东八区）标注对话时间。
5. **轮询识别结果**：周期性 `get_recording({ "id": "<id>" })` 直到 `status` 变为 `recognized`。`recognizeError` 有值表示识别失败，如实转述原因并建议重新上传；长时间停在 `recognizing` 时告知用户"已上传，转写完成后可在快记里查看，稍后问我即可"。
6. **回复**：上传后明确告知"已上传，正在转写"；转写完成后按场景一步骤 4 呈现。

## 链路自检（仅当用户要求演示或测试本功能时）

1. 用 python 生成 1 秒静音测试音频：`python -c "import wave; w=wave.open('test-audio.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(b'\x00'*16000); w.close()"`（python 不可用则如实说明并跳过自检）
2. 按场景二流程上传该测试文件（`file_ext: "wav"`），逐步汇报 presign / 直传 / 交接 / 轮询各步结果，完整走通即为链路正常。
3. 测试音频会进入用户自己的快记列表，转写结果为空或识别失败属正常现象，如实说明即可。**严禁把演示数据冒充真实对话录音**；正式场景永远使用用户提供的真实文件。

## 关键边界（必须遵守）

- **上传入参没有客户字段**：录音与客户的关联由系统自动识别生成；`upload_recording` 仅支持 `exhibition_id` 关联展会。未关联的快记会出现在仪表盘"未关联快记提醒"里，可后续补挂客户。
- **上传后不会立即返回转写**：识别是异步的，必须轮询 `get_recording`。
- `upload_recording` 也支持 `file_path`（服务器侧文件路径）形态与 `object_url` 二选一，仅限本地部署形态使用；WorkBuddy 环境一律走 presign 直传。

## 错误与恢复

- **401**（授权无效/过期/已断开）：引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）。
- **403**（无权限）：多为用户角色未配置 `mobile:ai_records:add`（上传）/ `mobile:ai_records:list`（查询）权限码，联系管理员开通。
- **直传 403**：多为未带 `Content-Type` 头或与 presign 返回值不一致——按 presign 返回的 `contentType` 原样带上重试；凭证过期（10 分钟）则重新 `presign_file_upload`。
