---
name: preference-load
description: 用户偏好画像加载与增量学习 · 加载 user_profile.json / 首次走 BOOTSTRAP 极简 3 题问卷 / 每次对话后从对话内容自动抽取增量 / 顺便做数据源体检。这是 agent 跨次复用的护城河。
version: 1.0.0
author:
tags: [travel, preference, profile, bootstrap, deps-check]
license: MIT
triggers:
  - agent 首次激活（检测 user_profile.json 不存在）
  - 用户说"重置我的偏好"
  - 每次对话结束时（增量学习）
  - 03 / 04 / 06 / 09 任一 skill 调用前需要读取偏好
inputs:
  - name: mode
    type: string
    enum: [load, bootstrap, update, ensure_deps]
    required: true
  - name: conversation_log
    type: file
    formats: [json]
    doc: update 模式下传入对话日志，从中抽取偏好
    required: false
outputs:
  - name: user_profile
    type: file
    format: json
    path: data/user_profile.json
---

# 偏好画像加载与增量学习（preference-load）

## 我解决什么问题

通用 AI 每次对话都要重新解释一遍"我不爱排队 / 不吃辣 / 必须有星巴克"。
我把偏好沉淀到 `data/user_profile.json`，跨次会话复用，且每次对话后自动学新东西。

**这是 agent 真正的护城河之一**——通用 AI 没法做。

## 🔴 任务前硬规则：必读 user_profile

**每次进入新任务，agent 在阶段 1 第一句话之前，必须先调一次 `load_profile.py`。**

为什么必读：
- 老用户在 `data/user_profile.json` 里可能有 history.completed_trips（去过哪些城市/拒过哪些 POI/惯用预算档）
- 不读 → 重复问用户已知信息（"你预算多少？"用户上次明明说过 standard 档）→ 体验差
- 不读 → 跳过快通道（老用户应该直接进阶段 2 而不是走 BOOTSTRAP 问卷）

命中已有 profile 时的正确开场：
```
我看到你之前去过成都/重庆，偏好是 standard 档 + 不爱排队。
这次还按这个吗？说一下目的地/日期/人数就可以开始。
```

❌ 反例：用户名明明已知，agent 还问"你叫什么名字"；预算偏好已知还问"预算多少"。

## 四种调用模式

### mode=load（默认）

读 `data/user_profile.json`，输出给上游 skill 使用。
文件不存在时自动跳到 mode=bootstrap。

### mode=bootstrap（首次启动）

走 BOOTSTRAP.md 定义的极简 3 题问卷：
- Q1 节奏（暴走/正常/躺平）
- Q2 禁忌（多选/留空）
- Q3 预算档位

把答案写入 `data/user_profile.json`。

**关键约束**：
- 只问这 3 题，不要变成 10 题问卷
- 留空允许（用户可以不回答 Q2）
- 答完立即进入正题，不要再追问

### mode=update（每次对话结束）

从对话日志里抽取**增量**信息：
- 用户说"这家店看起来不错" → favorite_pois +1
- 用户说"这家不要" → rejected_pois +1
- 用户拒绝 3 个网红店 → 在 tastes.scene_dislikes 里加 "crowded_check_in_spot"
- 用户多次问"附近有星巴克吗" → constraints.must_have_starbucks_or_equivalent = true

**学习规则**：
- 单次拒绝不足以下结论，至少 2 次模式重复才更新
- 学习完后用 markdown 列表告诉用户："我新记下了 X / Y / Z，对吧？" 给用户确认机会
- 用户否认 → 不写

### mode=ensure_deps（依赖体检）

检查当前 session 的 `<available_skills>` 列表，确认哪些数据源可用：
- meituan-travel 是否在列表中
- xhs-explore 是否在列表中
- online-search 是否在列表中

不可用的数据源在产物里标注降级，并主动告知用户如何开通。

体检结果写入 `data/.cache/deps_check.json`，下次启动时读取。

## 增量学习的反作用力

每次更新后：
- 在 SKILL 输出里告知用户："我新记了 ___，是吗？"
- 用户否认 → 立即回滚
- 跨 3 次会话都没用到的偏好，自动降权（避免画像越长越偏）

## 退出码

- 0 = 正常
- 2 = 需要用户操作（缺连接器 / 缺 key / 需扫码）
- 3 = profile 文件损坏（备份 + 重建）

## 反模式

- ❌ 一次问 10 题（违反 BOOTSTRAP 极简原则）
- ❌ 不告诉用户就更新偏好（必须告知 + 让用户有撤回机会）
- ❌ 把临时情绪当作长期偏好（"今天不想吃辣"≠永久不吃辣）
- ❌ 把出行特定决策写到全局偏好（如"这次想去海边"是 trip_request 不是 profile）

---

_用户偏好画像是 agent 区别于通用 AI 的根本。每多一条沉淀，下次出方案就少问一个问题。_
