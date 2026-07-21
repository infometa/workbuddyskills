# 2D 横版平台跳跃游戏开发规范（AI 必读）

本项目是 2D 横版平台跳跃类游戏，使用 Godot 4.6 引擎开发。

每次修改或新增文件前，必须先确认放置路径符合本文档规范。

---

## 目录结构

```
godot-project/
├── project.godot
├── icon.svg
├── addons/              ← Godot 插件，不要在这里放游戏代码
├── assets/
│   ├── audio/           ← 音效、音乐
│   ├── fonts/           ← 字体文件
│   ├── textures/        ← 贴图、精灵图
│   │   ├── characters/  ← 角色精灵
│   │   ├── tiles/       ← 瓦片贴图
│   │   └── ui/          ← UI 图片
│   └── tilesets/        ← TileSet 资源
├── data/                ← 配置数据（关卡数据等）
├── docs/                ← 文档
├── scenes/
│   ├── entities/        ← 玩家、敌人、道具场景
│   ├── levels/          ← 关卡场景（使用 TileMap）
│   ├── main/            ← 主场景入口
│   └── ui/              ← UI 场景
└── scripts/
    ├── autoload/        ← 全局单例（GameManager 等）
    ├── components/      ← 实体脚本（玩家控制、敌人AI）
    ├── systems/         ← 系统级逻辑
    └── ui/              ← UI 逻辑
```

---

## 核心规则

### 1. 2D 平台跳跃游戏约定
- 玩家角色使用 `CharacterBody2D` 节点
- 地面/平台使用 `TileMapLayer` 或 `StaticBody2D`
- 敌人使用 `CharacterBody2D` 或 `Area2D`（视碰撞需求）
- 收集品使用 `Area2D`

### 2. 物理层划分
| 层 | 名称 | 用途 |
|---|---|---|
| Layer 1 | Player | 玩家碰撞 |
| Layer 2 | Ground | 地面/平台碰撞 |
| Layer 3 | Enemy | 敌人碰撞 |
| Layer 4 | Collectible | 可收集物品 |

### 3. 输入映射
| Action | 按键 | 用途 |
|---|---|---|
| move_left | A | 左移 |
| move_right | D | 右移 |
| jump | Space | 跳跃 |

### 4. scenes 和 scripts 严格分离
- `.tscn` 文件 → 只放 `scenes/` 下
- `.gd` 文件 → 只放 `scripts/` 下
