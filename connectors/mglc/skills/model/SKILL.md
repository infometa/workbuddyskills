---
name: mglc-model
description: 灵创模型管理技能 - 查看可用的图片、视频和音频模型列表和模型能力参数
version: "1.0.0"
author: "灵创 AI"
---

# 灵创模型管理 Skill

本 Skill 提供灵创平台模型管理能力，可查询可用的图片、视频和音频模型。

## 模型类型

- `image`：图片模型
- `video`：视频模型
- `audio`：音频模型

## 模型支持的生成模式

### 视频模型支持的生成模式
- `text2video`：根据文本生成视频
- `firstFrame`：根据第一帧生成视频
- `lastFrame`：根据最后一帧生成视频
- `firstLastFrame`：根据第一帧和最后一帧生成视频
- `subjectRef`：参考设定生成视频
- `allMediaRef`：参考音频、视频、图片等多模态内容生成视频
- `videoRef`：参考视频内容生成视频
- `videoEdit`：在原视频的基础上，进行编辑生成新视频
- `videoExtend`：在原视频的基础上，进行扩展生成新视频

### 音频模型支持的生成模式
- `music`：生成音乐，如歌曲、纯音乐等
- `dubbing`：生成配音，将文本转换为语音
- `score`：生成配乐，为视频、图片等进行配乐

## 可用命令

### model list - 列出模型

列出当前可用的图片、视频和音频模型。视频模型和音频模型支持生成模式筛选。

**命令**：
```bash
# 列出所有模型
mglc model list

# 列出图片模型
mglc model list --type image

# 列出视频模型
mglc model list --type video

# 列出音频模型
mglc model list --type audio
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --type | string | - | 按模型类型筛选：image / video / audio |
| --mode | string | - | 按模型支持的生成模式筛选，视频模型和音频模型支持此参数 |
| --page | int | - | 页码，默认 1 |
| --page-size | int | - | 每页数量，默认 20 |

**使用示例**：
- 查看所有可用的 AI 绘图模型
- 查看所有可用的 AI 视频生成模型
- 查看所有可用的 AI 音频生成模型

### model - 查看模型能力

查看指定模型支持的参数能力。

**命令**：
```bash
# 查看图片模型能力
mglc model --type image --model-id <model_id>

# 查看视频模型能力
mglc model --type video --model-id <model_id>

# 查看音频模型能力
mglc model --type audio --model-id <model_id>
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| --type | string | ✓ | 模型类型：image / video / audio |
| --model-id | int64 | ✓ | 模型 ID |

**使用示例**：
- 查看某个图片模型支持的分辨率和比例
- 查看视频模型支持的生成模式
- 查看音频模型支持的生成模式
- 获取模型的详细参数配置用于生成任务
