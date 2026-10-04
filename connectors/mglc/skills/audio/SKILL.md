---
name: mglc-audio
description: 灵创音频生成技能 - 生成音乐、配乐和配音，并查询异步任务结果
version: "1.0.0"
author: "灵创 AI"
---

# 灵创音频生成 Skill

通过 `mglc` 生成音乐、配乐和配音。生成接口是异步的，提交后必须使用 `mglc task status` 查询最终音频。

## 音频生成公共参数
* 模型code: --model-code，必填，通过 `mglc model list --type audio` 查看
* 音频名称： --audio-name，必填
* 参考素材： --ref-audio`、`--ref-video`、`--ref-image` 参考素材支持 COS 路径或本地文件
* 会话ID： --session-id，可选，用于关联会话
* 项目ID： --project-id，可选，用于关联项目
* 项目主体设定相关： 
  * --subject-type <scene|role|prop>，可选，用于关联对应的项目主体（场景、角色、道具）设定。
  * --subject-id，可选，用于关联对应的项目主体ID。

## 生成音乐

```bash
mglc audio music --model-code <code> --audio-name "片尾音乐" --prompt "舒缓的木吉他与弦乐"
```

### 支持的模式 --lyrics-mode <smart|custom|instrumental>
* smart：智能模式，模型根据提示词智能选择生成的音乐类型（如纯音乐、配乐等，可在提示词里填充歌词）
* custom: 自定义歌词模式，需要传入 `--lyrics` 参数。模型按照传入的歌词生成音乐。
* instrumental：纯音乐模式，模型根据提示词生成纯音乐，不包含歌词。

---

## 生成配乐

```bash
mglc audio score --model-code <code> --audio-name "纪录片配乐" --prompt "温暖、舒缓"
```
### 参数限制
配乐只支持提示词、参考图片或参考视频及公共关联参数。`--ref-image` 与 `--ref-video` 不能同时参考。

## 生成配音

```bash
mglc audio dubbing --model-code <code> --audio-name "旁白" \
  --input-text "今天，我们从一段故事开始。" --timbre-code <code>
```
### 参数限制
* 配音文本：--input-text，可选，具体请参考模型详情`supportInputText`
* 提示词：--prompt，可选，具体请参考模型详情`supportPrompt`,提示词中可包含配音文本，如：参考 @音频1 的风格，用 @音频2 的音色，快乐的语气说：“你好”
* 参考音频：--ref-audio，具体请参考模型详情参考限制
* 音色：--timbre-code，通过(timbre)音色库命令查看/管理音色。
* 语速: --speech-rate <0.5~2.0>，浮点数，值越大，语速越快。
* 音高: --pitch <-12~12>，整数，值越大，音高越高。

### 配音文本技巧
* 支持停顿，如：<#0.5#>，表示停顿0.5秒。
* 支持情绪，如：<happy>哈哈哈</happy>，表示包裹的文本用happy的情绪配音。支持的情绪包括
  * 英文：happy, sad, angry, fearful, disgusted, surprised, calm, fluent, whisper
  * 中文别名：高兴、悲伤、愤怒、害怕、厌恶、惊讶、中性、生动、低语
* 支持语气词标签，如：你好(laughs)，表示你好之后会接自然的笑声。完整的语气词标签：
  * (laughs) 笑声
  * (chuckle) 轻笑
  * (coughs) 咳嗽
  * (clear-throat) 清嗓子
  * (groans) 呻吟
  * (breath) 正常换气
  * (pant) 喘气
  * (inhale) 吸气
  * (exhale) 呼气
  * (gasps) 倒吸气
  * (sniffs) 吸鼻子
  * (sighs) 叹气
  * (snorts) 喷鼻息
  * (burps) 打嗝
  * (lip-smacking) 咂嘴
  * (humming) 哼唱
  * (hissing) 嘶嘶声
  * (emm) 嗯
  * (sneezes) 喷嚏

**完整示例** <happy>今天终于见到你了</happy><#0.5#>我真的很开心(laughs)。

## 模型与任务

先用 `mglc model list --type audio` 查看模型；按模式筛选：

```bash
mglc model list --type audio --mode music
mglc model list --type audio --mode score
mglc model list --type audio --mode dubbing
```

提交成功后，通过 `mglc task status` 查询任务状态：

```bash
mglc task status --task-id <task_id>
```
