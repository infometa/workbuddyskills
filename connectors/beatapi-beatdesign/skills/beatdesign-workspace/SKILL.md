---
name: beatdesign-workspace
description: 操作本地 BeatDesign 项目中的 Canvas、Assets、生成任务、视频时间线和字幕；在用户要求创作、整理、检查或剪辑媒体时使用。
---

# BeatDesign 本地工作台

BeatDesign MCP 是结构化控制层，浏览器中的 BeatDesign 是用户审核界面；二者操作同一个本地 Project、Assets、Canvas、Timeline 和命令历史。

## 开始任务

1. 如果 BeatDesign 工具不可用，请用户在 WorkBuddy 中重试或重新安装
   Connector。若提示 3020 端口被占用，先关闭正在运行的其他 BeatDesign
   工作台，再重新连接；公共 Connector 不要求用户克隆仓库或运行 pnpm。
2. 目标项目不明确时，先调用 `bdesign_project_list`。
3. 调用一次 `bdesign_project_target` 绑定当前会话；之后可省略
   `projectId`。
4. 任务开始时调用 `bdesign_project_open`，保存返回的
   `workspaceUrl`。
5. Canvas 改动后用 `bdesign_canvas_view` 聚焦对应 `cardId`；时间线改动后用
   `bdesign_editor_view` 定位到相关时间。

如果 WorkBuddy 可以打开网页，则打开返回的 `workspaceUrl`；否则把准确链接交给用户，不要声称页面已经打开。

## 安全修改

- 修改前读取当前 Canvas 或 Editor 状态。
- 只使用带稳定 ID、revision 和幂等键的增量操作，不覆盖完整 Canvas 或 Timeline。
- 返回 `retry` 时，读取最新状态后按说明重试一次，不循环重试。
- 本地媒体先通过 `bdesign_asset_import` 导入，再放进 Canvas 或 Editor。
- 生成结果先成为 Project Asset；是否放进 Canvas/Editor 是下一步操作。

## 字幕

- 完整 SRT 文件或文本优先使用 `bdesign_editor_import_srt`；单条调整才使用
  `bdesign_editor_edit` 的 `upsert_caption`。
- SRT 校验失败不会改变原字幕。报告解析错误，不要清空或部分覆盖字幕轨。
- 导入后用 `bdesign_editor_view` 停在第一条相关字幕，让用户检查文字、时间、换行和预览效果。

## 尾帧续写

- `bdesign_canvas_continue_from_tail` 使用一个稳定 command ID；传输结果不确定时复用同一 ID，避免重复创建帧 Asset 或续写节点。
- 提交生成前，先调用返回的 review tool，让用户检查抽取帧和续写节点。
- 若提示缺少 `ffmpeg`，请用户把它加入 BeatDesign MCP 进程的 `PATH`，或设置绝对路径 `BEATDESIGN_FFMPEG`；环境未改变前不要重复调用。
- 抽帧和放置节点是本地操作；返回的生成请求是单独的远程付费动作，只有用户明确授权后才能提交。
- 生成成功只会创建 Asset。用 `bdesign_canvas_apply` 把输出更新到返回的生成卡片，再调用 `bdesign_canvas_view` 聚焦它。

## 导出权威时间线

- 用户明确授权导出后，先调用 `bdesign_editor_get`，再使用返回的 revision 调用 `bdesign_editor_render`。结果是项目内 MP4 Asset，包含可见 Clip、图片 Overlay、烧录字幕和混合音频。
- 若提示缺少 `ffmpeg` 或 `ffprobe`，请用户把两者加入 MCP 进程的 `PATH`，或设置绝对路径 `BEATDESIGN_FFMPEG` 和 `BEATDESIGN_FFPROBE`；环境未改变前不要重复调用。
- 会影响画面的时间线修改会让上一版当前导出失效，但不会删除历史 Asset。若导出期间时间线发生变化，先读取最新 revision，再询问用户是否重新导出。

## 完成标准

写入后核对返回的 revision 和变更 ID，再调用对应 view tool。Canvas 和 Editor 当前通常会在约两秒内或页面重新聚焦时读到 Agent 修改。最终提供准确的 `workspaceUrl` 供用户审核；仅有数据库 revision 不代表用户已经看到结果。

未获明确授权时，不要导出、提交付费生成或额外创建多个版本。
