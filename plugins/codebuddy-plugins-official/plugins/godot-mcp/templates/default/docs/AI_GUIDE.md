# Godot 项目开发规范（AI 必读）

每次修改或新增文件前，必须先确认放置路径符合本文档规范。

---

## 目录结构

```
godot-project/
├── project.godot
├── icon.svg
├── addons/              ← Godot 插件，不要在这里放游戏代码
├── assets/
│   ├── audio/           ← 音效、音乐（.wav / .ogg / .mp3）
│   ├── fonts/           ← 字体文件（.ttf / .otf）
│   ├── models/          ← 3D 模型（.glb / .obj / .fbx）
│   ├── textures/        ← 贴图、图片（.png / .jpg / .svg）
│   └── ui/              ← UI 专用图片（按钮、图标、背景）
├── data/                ← 配置数据（.tres / .json / .csv）
├── docs/                ← 文档（本文件所在位置）
├── scenes/
│   ├── entities/        ← 所有游戏实体场景（玩家/敌人/道具/子弹等）
│   ├── levels/          ← 关卡场景
│   ├── main/            ← 主场景入口（Main.tscn）
│   └── ui/              ← UI 场景（HUD / 菜单 / 弹窗）
└── scripts/
    ├── autoload/        ← 全局单例脚本（需在 project.godot 注册）
    ├── components/      ← 挂载在节点上的逻辑脚本（实体行为）
    ├── systems/         ← 系统级逻辑脚本（GameManager / 关卡管理等）
    └── ui/              ← UI 逻辑脚本
```

---

## 核心规则

### 1. scenes 和 scripts 严格分离
- `.tscn` 文件 → 只放 `scenes/` 下
- `.gd` 文件 → 只放 `scripts/` 下
- **禁止**将 `.gd` 和 `.tscn` 混放在同一目录

### 2. 资源文件归 assets
- 贴图、音效、字体、模型 → 只放 `assets/` 对应子目录
- **禁止**将资源文件散落在 `scenes/` 或 `scripts/` 中

### 3. 脚本放置判断
| 脚本类型 | 放置位置 |
|---|---|
| 挂载在游戏实体节点上（玩家/敌人/子弹） | `scripts/components/` |
| 系统管理类（GameManager / SpawnSystem） | `scripts/systems/` |
| 全局单例（Global / AudioManager） | `scripts/autoload/` |
| UI 逻辑（HUD / Menu） | `scripts/ui/` |

### 4. 场景放置判断
| 场景类型 | 放置位置 |
|---|---|
| 玩家、敌人、NPC、道具、子弹等 | `scenes/entities/` |
| 关卡、地图 | `scenes/levels/` |
| 游戏主入口 | `scenes/main/` |
| HUD、菜单、弹窗 | `scenes/ui/` |

### 5. res:// 路径规范
所有 `preload` / `load` 路径必须使用完整 `res://` 路径，例如：
```gdscript
# ✓ 正确
const BULLET = preload("res://scenes/entities/Bullet.tscn")
const PLAYER = preload("res://scripts/components/Player.gd")

# ✗ 错误：路径不完整或目录错误
const BULLET = preload("Bullet.tscn")
const PLAYER = preload("res://Player.gd")
```

### 6. 新增游戏类型时的扩展方式
如需新增实体类型，**不要新建顶层目录**，在现有目录内自行创建子文件夹：
```
scenes/entities/
├── player/
├── enemies/
└── projectiles/
```

---

## 禁止事项

- ❌ 不在项目根目录散落 `.gd` / `.tscn` 文件
- ❌ 不在 `addons/` 下放游戏业务代码
- ❌ 不新建 `src/` 目录（Godot 项目不需要）
- ❌ 不将 `scripts/` 和 `scenes/` 合并
- ❌ 不在 `assets/` 下放脚本文件
