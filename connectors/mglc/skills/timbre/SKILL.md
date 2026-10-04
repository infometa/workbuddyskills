---
name: mglc-timbre
description: 灵创音色库技能 - 提供音色查询、收藏、创建等功能
version: "1.0.0"
author: "灵创 AI"
---

# 音色库 Skill

音色库有两类用途：使用已有音色，以及创建新的我的音色。
创建新音色必须遵循固定流程：提交任务 -> 查询候选 -> 保存音色。

## 一、使用已有音色

### 1. 查询音色
* 支持按语言、性别、年龄、风格、关键词等过滤，关键词支持模糊匹配
  - 支持的语言：`中文 (普通话)`, `中文 (粤语)`, `乌克兰文`, `俄文`, `印地文`, `印尼文`, `土耳其语`, `希腊文`, `德文`, `意大利语`, `捷克文`,`日文`,`法文`,`波兰文`,`泰文`,`罗马尼亚文`,`芬兰文`,`英文`,`荷兰文`,`葡萄牙语`,`西班牙文`,`越南语`,`韩文`
  - 支持的性别：`男`、`女`、`角色`
  - 支持的年龄：`儿童`、`青年`、`中年`、`老年`
  - 支持的风格：`商务/知性`, `娱乐/个性`,`情感/角色`,`播报/主持`,`方言/地域`,`氛围/质感`,`生活/日常`,`角色/卡通`
* 列表支持分页参数 `--page`、`--page-size`

#### 1.1 查询预设音色：

```bash
mglc timbre preset list --language 中文(普通话) --gender 女 --style "商务/知性"
```

#### 1.2 查询我的音色：

```bash
mglc timbre mine list --language 中文(普通话) --gender 女 --style "商务/知性"
```

### 2. 收藏管理

```bash
mglc timbre favorites list
mglc timbre favorites add --timbre-code <code> --source preset
mglc timbre favorites remove --timbre-code <code> --source mine
```
收藏操作的 `--source` 只能是 `preset` 或 `mine`。

## 二、设计/克隆音色

设计/克隆音色结果先是只能试听的候选，不能直接用于 TTS。设计和克隆都必须完成以下三步：

```text
提交任务 -> 查询候选 -> 选择候选并保存
```

保存成功后才得到可用于配音的永久 `timbreCode`。

### A. 音色设计

1. 提交设计任务：

```bash
mglc timbre design create \
  --prompt "温柔、知性、适合纪录片旁白" \
  --preview-text "今天，我们从一段故事开始。" \
  --voice-name "我的设计音色"
```

2. 查询设计候选：

```bash
mglc timbre design result --task-id <task_id>
```
当设计任务状态`status` = 2 且 `candidates` 不为空时，代表音色设计任务完成，可选择保存候选。
如果`status` = 1，代表音色设计任务进行中，需要稍后再查询。
如果`status` = 3，代表音色设计任务失败，需要重新提交任务或提示用户。

3. 保存选中的候选：

```bash
mglc timbre design save \
  --user-style-id <user_style_id> \
  --voice-id <voice_id> \
  --preview-url <preview_url> \
  --tts-provider-id <provider_id> \
  --name "纪录片旁白" \
  --session-id <session_id> \
  --language <language> \
  --gender <gender> \
  --style <style> \
  --age-desc <age_desc>
```

设计任务固定生成 1 个候选。保存参数中的 `user-style-id`、`voice-id`、`preview-url`、`tts-provider-id` 必须原样取自同一个候选。

### B. 音色克隆

1. 提交克隆任务。推荐传本地音频，CLI 会自动直传 COS 并将返回的路径提交给克隆接口：

```bash
mglc timbre clone create \
  --audio ./voice-sample.wav \
  --preview-text "欢迎使用灵创 CLI。" \
  --voice-name "我的克隆音色"
```

也可直接传 COS 路径：

```bash
mglc timbre clone create --audio <registered_cos_path>
```

2. 查询克隆候选：

```bash
mglc timbre clone result --task-id <task_id>
```

当克隆任务状态`status` = 2 且 `candidates` 不为空时，代表音色克隆任务完成，可选择保存候选。
如果`status` = 1，代表音色克隆任务进行中，需要稍后再查询。
如果`status` = 3，代表音色克隆任务失败，需要重新提交任务或提示用户。

3. 保存选中的候选：

```bash
mglc timbre clone save \
  --user-style-id <user_style_id> \
  --voice-id <voice_id> \
  --preview-url <preview_url> \
  --tts-provider-id <provider_id> \
  --name "我的克隆音色"
```

## 三、保存设计/克隆音色到我的音色库

`design save` 和 `clone save` 使用相同的保存参数：

- 必填：`--user-style-id`、`--voice-id`、`--preview-url`、`--tts-provider-id`、`--name`
- 可选：`--session-id`、`--language`、`--accent`、`--gender`、`--age-desc`、`--description`

保存后，用`mglc timbre detail --user-style-id <user_style_id>` 查询音色详情，只有当音色状态为 `registered` 且 `timbreCode` 不为空时才能使用。
