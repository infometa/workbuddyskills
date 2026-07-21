# 小说模板

## 世界观模板

```markdown
# [小说名] 世界观

## 一句话卖点
[一句话说明这篇小说的核心吸引力]

## 背景设定

### 时代/世界
[描述故事发生的时代背景或世界设定]

### 核心规则
[这个世界的运行规则，如：灵气复苏、末法时代]

### 力量体系
[修炼体系、魔法系统等]

## 势力格局

### 势力A
- 特点：
- 目的：
- 代表人物：

### 势力B
- 特点：
- 目的：
- 代表人物：

## 核心冲突
[推动故事发展的根本矛盾]
```

## 人物模板

```markdown
# [角色名]

## 基本信息
- 性别：
- 年龄：
- 身份：

## 外貌
[200字外貌描写]

## 性格
[核心性格特点]

## 目标/动机
[角色想要什么？害怕什么？]

## 弧光
[角色在故事中的成长变化]

## 关键事件
- 事件1：
- 事件2：
```

## 章节规格模板

```yaml
chapter: 001
title: "章节标题"
summary: "200字以内概括本章内容"

before_state:
  characters:
    - {name: "角色名", state: "状态", location: "位置"}
  plot_hooks:
    - "伏笔A"
    - "伏笔B"

after_state:
  characters:
    - {name: "角色名", state: "新状态", location: "新位置"}
  plot_advances:
    - "伏笔A已回收"
    - "新伏笔C"

must_happen:
  - "关键事件1：谁在做什么"
  - "关键事件2"

must_not_happen:
  - "禁止出现的剧情"

tension_curve:
  - {position: 0, value: 3, note: "铺垫"}
  - {position: 30, value: 5, note: "发展"}
  - {position: 70, value: 9, note: "高潮"}
  - {position: 100, value: 4, note: "收尾"}

key_scenes:
  - "场景1：具体描述"
  - "场景2：具体描述"

new_hooks:
  - "本结尾的钩子"

check_against_previous:
  characters_consistent: true
  timeline_consistent: true
  location_consistent: true
```

## 伏笔追踪模板

```markdown
# 伏笔追踪表

| 伏笔ID | 内容 | 埋入章节 | 预期回收 | 状态 |
|-------|------|---------|---------|-----|
| hook_001 | [伏笔内容] | 第X章 | 第Y章 | 待回收 |
| hook_002 | [伏笔内容] | 第X章 | 已回收 |
```
