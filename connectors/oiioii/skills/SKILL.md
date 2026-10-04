---
name: oiioii-cli
description: 使用 OiiOii CLI 创建和管理 AI 图片、视频与音频，并处理工作空间、生成任务、资源和积分信息。
version: "1.0.0"
---

# OiiOii CLI Skill

## 产品简介

OiiOii 是全球首个 AI 动画/真人视频创作 Agent。用户只需描述创意，OiiOii 的影视级专业 Agents 团队即可将零散想法转化为完整故事、广告成片；同时支持视频转绘出海、剧本本土化出海、多剧集拆分到成片等短漫剧工作流。

## 使用范围

在用户需要通过 OiiOii 完成以下任务时使用本 Skill：

- 文本生成图片或编辑已有图片。
- 文本生成视频、图片生成视频或使用混合参考生成视频。
- 生成音频或音乐。
- 上传本地图片、视频或音频。
- 创建、选择或查询 OiiOii Workspace。
- 查询异步生成任务并下载生成结果。
- 查询可用模型、积分余额、预估费用或实际费用。

不要假设 OiiOii CLI 支持全局资源搜索、资源删除或风格预设管理。

## 典型用户请求

- 帮我做个小故事：一个转学生来到异世界高中，发现同学们都有各种超能力。
- 根据这份产品介绍，制作一条 30 秒的动画宣传片。
- 把这个故事脚本扩展成一部竖屏 AI 仿真人剧，并生成第一集。
- 根据上传的角色参考图，制作一段角色形象一致的多镜头动画。
- 将这份教育材料改编成适合中学生观看的动画讲解视频。
- 为这款游戏设计一段 45 秒的开场过场动画。
- 把这篇品牌故事改编成包含旁白、音乐和音效的动画短片。

这些示例描述的是用户目标。执行时必须将目标拆解到当前 CLI 实际支持的图片、视频、音频、上传、Workspace 和任务命令；如果完成目标需要当前 CLI 未提供的剧本扩写、多集编排、旁白合成或成片剪辑能力，应明确说明缺口，不得声称已经完成端到端制作。

## 通用调用规则

1. 所有自动化调用都添加 `--json`。
2. 首先检查 JSON 顶层 `ok` 字段。
3. 失败时根据 `error.code` 处理，不从错误文案猜测状态。
4. 如果输出包含 `next`，优先使用其中建议的后续命令。
5. 不得在回复、日志或文档中显示 API Key。
6. 不得把真实 API Key 写入命令示例。
7. 生成属于可能消耗积分的外部操作；提交前先报价，并在需要时获得用户确认。
8. 提交生成请求后保存任务 ID，避免因超时或重复操作造成重复提交。

## 认证

WorkBuddy 安装 Connector 时负责运行认证流程。正常任务中不要要求用户在聊天里提供 API Key。

```bash
oiioii auth status --json
```

如果状态命令返回未认证，提示用户在 WorkBuddy 中重新连接 OiiOii Connector。

## Workspace 准备

执行生成或上传前检查当前 Workspace：

```bash
oiioii workspace current --json
```

如果尚未配置 Workspace，可根据用户要求创建并设为当前 Workspace：

```bash
oiioii workspace create --name "<workspace-name>" --language zh --set-current --json
```

也可以选择已有 Workspace：

```bash
oiioii workspace set <workspace_id> --json
```

## 图片

文本生成图片：

```bash
oiioii image text --prompt "<prompt>" --json
```

编辑已有图片：

```bash
oiioii image edit --image <hogi-image-uri> --prompt "<prompt>" --json
```

## 视频

文本生成视频：

```bash
oiioii video text --prompt "<prompt>" --json
```

图片生成视频：

```bash
oiioii video image --image <hogi-image-uri> --prompt "<prompt>" --json
```

混合参考生成视频：

```bash
oiioii video generate --prompt "<prompt>" --image <hogi-image-uri> --video <hogi-video-uri> --audio <hogi-audio-uri> --json
```

仅在所选模型支持对应参考类型时传入图片、视频或音频参数。

## 音频

```bash
oiioii audio generate --prompt "<prompt>" --json
```

具体模型参数应先通过模型查询确认，不要编造模型名称或能力。

## 上传

```bash
oiioii upload file <local-path> --json
```

上传前确认文件路径存在，且文件类型受 CLI 支持。

## 模型与能力

```bash
oiioii inspect capabilities --json
oiioii inspect models --json
```

模型目录可能变化。涉及模型选择时，以 `inspect models` 的当前结果为准。

## 积分与费用

查询余额：

```bash
oiioii points balance --json
```

提交付费生成前使用对应参数进行报价：

```bash
oiioii points quote <generation arguments> --json
```

生成完成后按任务或资源查询实际费用：

```bash
oiioii points cost <task-or-resource-id> --json
```

报价是预估值，最终以生成完成后的实际扣费结果为准。

## 任务与结果

查询任务：

```bash
oiioii task status <task_id> --json
```

等待任务完成：

```bash
oiioii task wait <task_id> --json
```

不要把“请求已提交”解释为“生成成功”。只有终态成功并返回有效资源 URI 才算完成。

查询或下载生成资源：

```bash
oiioii record get <hogi-uri> --json
oiioii record open <hogi-uri> --no-open --json
```

## 错误处理

- 未认证：提示用户在 WorkBuddy 中重新连接 Connector。
- Workspace 缺失：查询、创建或选择 Workspace 后重试。
- 参数无效：根据结构化错误修正参数，不重复原请求。
- 余额不足：报告余额或费用信息，不继续提交。
- 网络超时：先查询已有任务状态，不直接重复创建任务。
- API Key 失效：停止业务调用并提示重新认证。
