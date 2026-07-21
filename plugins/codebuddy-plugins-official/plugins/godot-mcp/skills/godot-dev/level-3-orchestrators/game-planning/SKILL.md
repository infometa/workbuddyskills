---
name: game-dev-workflow
description: >
  游戏开发流程引导技能（策划阶段）。**强前置：仅当工作区根目录已存在 project.godot
  且 godot-editor/ 已包含 Godot*.exe 时才可激活**。引导用户按「策划 → 开发 →
  测试」顺序完成游戏。如果工作区是空的、或缺少 project.godot / 缺少 Godot 编辑器，
  **绝对不要启动本技能**，必须先调用 godot-setup（或走 project-init 路由）完成环境装配，
  环境就绪后再进入策划。仅当明确说"开始策划""生成策划文档""设计 XX 系统"
  "完善玩法"等明确调起策划阶段的场景下才调用。
version: 2.0.0
---
    path_pattern: "docs/planning/gameplay_design.md"
  - name: level_design
    type: file
    path_pattern: "docs/planning/level_design.md"
  - name: numerical_design
    type: file
    path_pattern: "docs/planning/numerical_design.md"
---

# 🎮 游戏开发流程引导

## 核心原则

```
📋 策划 → 🎯 确认 → 💻 开发 → 🎮 测试
```

**禁止跳过策划直接写代码！**

---

## 开发流程总览

```
Phase 0: 需求收集     ──→ 本技能引导
Phase 1: 策划文档     ──→ 调用子策划技能
Phase 2: 项目搭建     ──→ project-scaffold
Phase 3: 系统开发     ──→ Level 2 模块技能
Phase 4: 测试迭代     ──→ 运行验证
```

---

## Phase 0: 需求收集

当用户说"帮我做游戏"时，必须先收集以下信息：

### 必问清单

| 问题 | 选项 |
|------|------|
| 游戏类型 | 平台跳跃/RPG/射击/解谜/动作/Roguelike |
| 视角维度 | 2D横版/2D俯视/3D第一人称/3D第三人称 |
| 目标平台 | PC/移动端/Web |
| 开发范围 | 原型(3天)/Demo(2周)/MVP(2月) |
| 参考游戏 | 可选，帮助理解风格 |

### 收集完成后

```
→ 进入 Phase 1，调用策划子技能
```

---

## Phase 1: 策划文档

按顺序调用以下子技能，生成策划文档：

| 步骤 | 技能 | 输出文件 | 说明 |
|------|------|----------|------|
| 1.1 | **interaction-design** | `interaction_design.md` | 输入/UI/反馈 |
| 1.2 | **gameplay-design** | `gameplay_design.md` | 玩法/战斗/成长 |
| 1.3 | **level-design** | `level_design.md` | 关卡/敌人/Boss |
| 1.4 | **numerical-design** | `numerical_design.md` | 属性/公式/经济 |

### 输出结构

```
docs/planning/
├── interaction_design.md
├── gameplay_design.md
├── level_design.md
└── numerical_design.md
```

### 用户确认

生成后展示摘要，等待用户确认：

```markdown
📋 **策划摘要**
- 类型: {type}
- 核心玩法: {core_loop}
- 预计内容: {content_scope}

请确认后继续开发，或提出修改意见。
```

---

## Phase 2: 项目搭建

用户确认策划后，调用 `project-scaffold` 创建项目：

| 步骤 | 操作 | 技能 |
|------|------|------|
| 2.1 | 创建目录结构 | project-scaffold |
| 2.2 | 生成配置文件 | config-generator |
| 2.3 | 创建主场景 | godot-core |
| 2.4 | 配置 InputMap | input-system |

### 输出结构

```
project/
├── scenes/
│   ├── main.tscn
│   ├── levels/
│   └── ui/
├── scripts/
│   ├── systems/
│   ├── entities/
│   └── ui/
├── data/
│   └── config/
└── assets/
```

---

## Phase 3: 系统开发

根据策划文档，按优先级调用 Level 2 模块技能：

### 核心系统 (P0)

| 顺序 | 技能 | 输出 |
|------|------|------|
| 1 | **input-system** | 输入管理器 |
| 2 | **player-system** | 玩家控制器 |
| 3 | **camera-system** | 相机跟随 |

### 玩法系统 (P1)

| 顺序 | 技能 | 输出 |
|------|------|------|
| 4 | **combat** (代码生成) | 战斗系统 |
| 5 | **enemy-ai** (代码生成) | 敌人AI |
| 6 | **level-manager** (代码生成) | 关卡管理 |

### 辅助系统 (P2)

| 顺序 | 技能 | 输出 |
|------|------|------|
| 7 | **ui-system** | UI界面 |
| 8 | **save-system** | 存档系统 |
| 9 | **audio-system** | 音频管理 |

---

## Phase 4: 测试迭代

### 验证清单

- [ ] 项目可运行无报错
- [ ] 玩家可移动/攻击
- [ ] 敌人有基础AI
- [ ] 可完成一个关卡
- [ ] UI可交互

### 迭代循环

```
测试 → 发现问题 → 定位模块 → 修复 → 再测试
```

---

## 快速参考：技能调用链

### 原型开发 (3天)

```
1. game-dev-workflow (本技能)
   ├── 收集需求
   └── 生成最小策划
2. project-scaffold
3. input-system
4. player-system
5. 创建测试场景
6. 运行验证
```

### Demo 开发 (2周)

```
1. game-dev-workflow
   └── 完整策划四件套
2. project-scaffold
3. input-system + player-system + camera-system
4. 战斗系统 + 敌人AI
5. 关卡管理 + 第一关卡
6. 基础UI
7. 测试迭代
```

### MVP 开发 (2月)

```
(同Demo) +
8. save-system
9. audio-system
10. 多关卡内容
11. 完整UI流程
12. 平衡调整
```

---

## 常见游戏类型快速模板

### 2D 平台跳跃

```yaml
必需技能:
  - player-system: platformer_2d
  - camera-system: smooth_follow
  - input-system: [move, jump, attack]
关键策划:
  - 跳跃手感 (浮空时间、跳跃缓冲)
  - 关卡节奏 (难度曲线)
```

### 2D RPG

```yaml
必需技能:
  - player-system: topdown_2d
  - ui-system: inventory, dialog
  - save-system: required
关键策划:
  - 数值平衡 (属性、经济)
  - 任务系统
```

### Roguelike

```yaml
必需技能:
  - procedural-generation (需额外实现)
  - player-system: varies
关键策划:
  - 元进度系统
  - 随机性平衡
```

---

## 对话示例

```
用户: 帮我做一个游戏

AI: 好的！先收集一些信息：
    1. 什么类型？(平台跳跃/RPG/射击/...)
    2. 2D还是3D？
    3. 目标平台？(PC/移动/Web)
    4. 开发范围？(原型/Demo/MVP)
    5. 有参考游戏吗？

用户: 2D横版动作，像空洞骑士，PC，做Demo

AI: 明白！开始生成策划文档...
    
    [调用 interaction-design]
    [调用 gameplay-design]
    [调用 level-design]  
    [调用 numerical-design]
    
    📋 策划摘要：
    - 类型: 2D银河恶魔城
    - 核心: 探索+战斗+能力解锁
    - Demo内容: 1区域+1Boss
    
    确认后开始开发？

用户: 确认

AI: 开始创建项目...
    [调用 project-scaffold]
    [调用 input-system]
    [调用 player-system: platformer_2d]
    ...
```

---

## 下一步

策划技能详情请查看：
- [interaction-design](interaction-design/SKILL.md) - 交互设计
- [gameplay-design](gameplay-design/SKILL.md) - 玩法设计
- [level-design](level-design/SKILL.md) - 关卡设计
- [numerical-design](numerical-design/SKILL.md) - 数值设计
