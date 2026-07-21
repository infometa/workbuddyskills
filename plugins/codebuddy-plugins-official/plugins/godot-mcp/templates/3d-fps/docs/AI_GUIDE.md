# 3D FPS 射击游戏开发规范（AI 必读）

本项目是 3D 第一人称射击类游戏，使用 Godot 4.6 引擎 Forward+ 渲染管线开发。

每次修改或新增文件前，必须先确认放置路径符合本文档规范。

---

## 目录结构

```
godot-project/
├── project.godot
├── icon.svg
├── addons/              ← Godot 插件
├── assets/
│   ├── audio/           ← 音效、音乐
│   │   ├── sfx/         ← 枪声、脚步声等
│   │   └── music/       ← 背景音乐
│   ├── fonts/           ← 字体文件
│   ├── models/          ← 3D 模型（.glb / .fbx）
│   │   ├── characters/  ← 角色模型
│   │   ├── weapons/     ← 武器模型
│   │   └── environment/ ← 环境模型
│   ├── textures/        ← 贴图（PBR 材质等）
│   └── ui/              ← UI 图片
├── data/                ← 配置数据（武器数据、关卡数据等）
├── docs/                ← 文档
├── scenes/
│   ├── entities/        ← 玩家、敌人、武器场景
│   ├── levels/          ← 关卡场景
│   ├── main/            ← 主场景入口
│   └── ui/              ← UI 场景（HUD/菜单）
└── scripts/
    ├── autoload/        ← 全局单例
    ├── components/      ← 实体脚本（玩家控制器、敌人AI、武器系统）
    ├── systems/         ← 系统级逻辑
    └── ui/              ← UI 逻辑
```

---

## 核心规则

### 1. 3D FPS 游戏约定
- 玩家使用 `CharacterBody3D` + `Camera3D`
- 武器挂载在 Camera3D 子节点
- 敌人使用 `CharacterBody3D` + `NavigationAgent3D`
- 子弹使用 `RigidBody3D` 或射线检测（hitscan）

### 2. 物理层划分
| 层 | 名称 | 用途 |
|---|---|---|
| Layer 1 | Player | 玩家碰撞 |
| Layer 2 | Environment | 环境碰撞 |
| Layer 3 | Enemy | 敌人碰撞 |
| Layer 4 | Projectile | 子弹/弹药碰撞 |
| Layer 5 | Interactable | 可交互物品 |

### 3. 输入映射
| Action | 按键 | 用途 |
|---|---|---|
| move_forward | W | 前进 |
| move_backward | S | 后退 |
| move_left | A | 左移 |
| move_right | D | 右移 |
| jump | Space | 跳跃 |

### 4. scenes 和 scripts 严格分离
- `.tscn` 文件 → 只放 `scenes/` 下
- `.gd` 文件 → 只放 `scripts/` 下
