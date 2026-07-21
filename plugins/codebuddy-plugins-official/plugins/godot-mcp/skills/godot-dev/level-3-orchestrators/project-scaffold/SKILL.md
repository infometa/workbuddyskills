---
name: project-scaffold
description: >
  项目脚手架技能。根据游戏类型生成完整的项目结构，
  包括文件目录、核心脚本、配置文件、资源占位等。
version: 1.0.0
dependencies:
  - godot-core
  - file-manager
  - code-generator
  - config-generator
triggers:
  - pattern: "项目结构|初始化项目|项目模板|脚手架|scaffold"
inputs:
  - name: project_type
    type: string
    enum: ["2d_platformer", "2d_topdown", "3d_fps", "3d_tps", "rpg", "puzzle"]
    required: true
  - name: project_name
    type: string
    required: true
outputs:
  - name: project_structure
    type: directory
    path_pattern: "./"
---

# 项目脚手架技能

根据游戏类型创建完整的项目结构。

## 通用项目结构

```
{project_name}/
├── project.godot
├── .gitignore
├── README.md
├── CHANGELOG.md
│
├── addons/                    # 插件
│   └── godot_mcp/            # MCP 插件
│
├── assets/                    # 资源文件
│   ├── audio/
│   │   ├── music/
│   │   └── sfx/
│   ├── fonts/
│   ├── sprites/              # 2D
│   ├── models/               # 3D
│   ├── textures/
│   ├── materials/
│   └── shaders/
│
├── data/                      # 数据配置
│   ├── config/               # JSON 配置
│   │   ├── schemas/          # JSON Schema
│   │   ├── player.json
│   │   ├── enemies.json
│   │   ├── items.json
│   │   └── levels.json
│   ├── i18n/                 # 多语言
│   │   ├── en.csv
│   │   └── zh.csv
│   └── saves/                # 存档模板
│
├── docs/                      # 文档
│   ├── game_design/          # GDD
│   └── technical/            # 技术文档
│
├── scenes/                    # 场景文件
│   ├── main/
│   │   ├── main.tscn
│   │   └── main.gd
│   ├── ui/
│   │   ├── main_menu.tscn
│   │   ├── pause_menu.tscn
│   │   ├── hud.tscn
│   │   └── settings_menu.tscn
│   ├── levels/
│   │   └── level_01.tscn
│   ├── entities/
│   │   ├── player/
│   │   └── enemies/
│   └── components/           # 可复用组件场景
│
├── scripts/                   # 脚本文件
│   ├── autoload/             # 单例
│   │   ├── game_manager.gd
│   │   ├── audio_manager.gd
│   │   ├── save_manager.gd
│   │   ├── event_bus.gd
│   │   └── scene_manager.gd
│   ├── entities/
│   │   ├── player/
│   │   └── enemies/
│   ├── systems/
│   │   ├── input/
│   │   ├── camera/
│   │   └── ui/
│   ├── components/           # 组件脚本
│   │   ├── health_component.gd
│   │   ├── hitbox_component.gd
│   │   └── movement_component.gd
│   ├── resources/            # 自定义资源
│   │   └── item_data.gd
│   └── utils/                # 工具类
│       ├── constants.gd
│       └── helpers.gd
│
└── tests/                     # 测试场景
    └── test_player.tscn
```

---

## 核心脚本模板

### project.godot 配置

```ini
[application]
config/name="{project_name}"
run/main_scene="res://scenes/main/main.tscn"
config/features=PackedStringArray("4.6", "Forward Plus")
config/icon="res://icon.svg"

[autoload]
EventBus="*res://scripts/autoload/event_bus.gd"
GameManager="*res://scripts/autoload/game_manager.gd"
AudioManager="*res://scripts/autoload/audio_manager.gd"
SaveManager="*res://scripts/autoload/save_manager.gd"
SceneManager="*res://scripts/autoload/scene_manager.gd"

[display]
window/size/viewport_width=1920
window/size/viewport_height=1080
window/size/window_width_override=1280
window/size/window_height_override=720
window/stretch/mode="canvas_items"
window/stretch/aspect="keep"

[input]
move_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":65,"key_label":0,"unicode":97,"echo":false,"script":null)
]
}
move_right={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":68,"key_label":0,"unicode":100,"echo":false,"script":null)
]
}
jump={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"echo":false,"script":null)
]
}
attack={
"deadzone": 0.5,
"events": [Object(InputEventMouseButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"button_mask":1,"position":Vector2(0, 0),"global_position":Vector2(0, 0),"factor":1.0,"button_index":1,"canceled":false,"pressed":false,"double_click":false,"script":null)
]
}

[layer_names]
2d_physics/layer_1="player"
2d_physics/layer_2="enemy"
2d_physics/layer_3="projectile"
2d_physics/layer_4="pickup"
2d_physics/layer_5="environment"
2d_physics/layer_6="trigger"

[rendering]
renderer/rendering_method="forward_plus"
textures/canvas_textures/default_texture_filter=0
```

### .gitignore

```gitignore
# Godot 4+ specific ignores
.godot/

# Godot-specific ignores
*.import
.import/
export.cfg
export_presets.cfg

# Mono-specific ignores
.mono/
data_*/
mono_crash.*.json

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Build outputs
builds/
export/

# Local environment
.env
*.local

# Log files
*.log
logs/
```

### event_bus.gd (全局事件总线)

```gdscript
## 事件总线
##
## 全局事件发布/订阅系统
## @author AI Generated
## @version 1.0.0
extends Node

# region 游戏流程
signal game_started
signal game_paused
signal game_resumed
signal game_over
# endregion

# region 玩家事件
signal player_spawned(player: Node)
signal player_died
signal player_respawned
signal player_health_changed(current: int, max: int)
signal player_level_up(new_level: int)
# endregion

# region 战斗事件
signal enemy_spawned(enemy: Node)
signal enemy_died(enemy: Node, killer: Node)
signal damage_dealt(target: Node, amount: int, source: Node)
# endregion

# region 物品事件
signal item_picked_up(item_id: String, amount: int)
signal item_used(item_id: String)
signal item_dropped(item_id: String, position: Vector2)
# endregion

# region UI 事件
signal ui_opened(ui_name: String)
signal ui_closed(ui_name: String)
signal notification_requested(message: String, type: String)
# endregion

# region 场景事件
signal scene_transition_started(from: String, to: String)
signal scene_transition_completed(scene_name: String)
signal checkpoint_reached(checkpoint_id: String)
# endregion

# region 音频事件
signal music_requested(track: String)
signal sfx_requested(sound: String, position: Variant)
# endregion
```

### game_manager.gd

```gdscript
## 游戏管理器
##
## 管理游戏状态和流程
## @author AI Generated
## @version 1.0.0
extends Node

# region 枚举
enum GameState {
    NONE,
    MAIN_MENU,
    PLAYING,
    PAUSED,
    GAME_OVER,
    LOADING
}
# endregion

# region 状态
var current_state: GameState = GameState.NONE
var previous_state: GameState = GameState.NONE
var is_debug: bool = OS.is_debug_build()
# endregion

# region 游戏数据
var score: int = 0
var playtime: float = 0.0
# endregion

# region 生命周期
func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    
func _process(delta: float) -> void:
    if current_state == GameState.PLAYING:
        playtime += delta
# endregion

# region 状态管理
func change_state(new_state: GameState) -> void:
    if new_state == current_state:
        return
    
    previous_state = current_state
    current_state = new_state
    
    match new_state:
        GameState.MAIN_MENU:
            get_tree().paused = false
        GameState.PLAYING:
            get_tree().paused = false
            EventBus.game_started.emit()
        GameState.PAUSED:
            get_tree().paused = true
            EventBus.game_paused.emit()
        GameState.GAME_OVER:
            EventBus.game_over.emit()
        GameState.LOADING:
            pass

func is_playing() -> bool:
    return current_state == GameState.PLAYING

func is_paused() -> bool:
    return current_state == GameState.PAUSED
# endregion

# region 游戏控制
func start_game() -> void:
    score = 0
    playtime = 0.0
    change_state(GameState.PLAYING)

func pause_game() -> void:
    if current_state == GameState.PLAYING:
        change_state(GameState.PAUSED)

func resume_game() -> void:
    if current_state == GameState.PAUSED:
        change_state(GameState.PLAYING)
        EventBus.game_resumed.emit()

func toggle_pause() -> void:
    if current_state == GameState.PLAYING:
        pause_game()
    elif current_state == GameState.PAUSED:
        resume_game()

func game_over() -> void:
    change_state(GameState.GAME_OVER)

func return_to_menu() -> void:
    change_state(GameState.MAIN_MENU)
    SceneManager.goto_scene("res://scenes/ui/main_menu.tscn")

func quit_game() -> void:
    get_tree().quit()
# endregion

# region 分数
func add_score(amount: int) -> void:
    score += amount

func get_score() -> int:
    return score
# endregion
```

### scene_manager.gd

```gdscript
## 场景管理器
##
## 管理场景切换和过渡效果
## @author AI Generated
## @version 1.0.0
extends Node

# region 信号
signal transition_started
signal transition_mid_point  # 适合在此时切换场景
signal transition_finished
# endregion

# region 常量
const TRANSITION_SCENE = "res://scenes/ui/transition.tscn"
# endregion

# region 状态
var current_scene: Node = null
var _transition_layer: CanvasLayer
var _transition_anim: AnimationPlayer
var _target_scene_path: String = ""
var _is_transitioning: bool = false
# endregion

func _ready() -> void:
    var root = get_tree().root
    current_scene = root.get_child(root.get_child_count() - 1)
    _setup_transition_layer()

func _setup_transition_layer() -> void:
    _transition_layer = CanvasLayer.new()
    _transition_layer.layer = 100
    add_child(_transition_layer)
    
    # 简单的颜色渐变过渡
    var color_rect = ColorRect.new()
    color_rect.color = Color.BLACK
    color_rect.modulate.a = 0
    color_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
    _transition_layer.add_child(color_rect)

# region 场景切换
func goto_scene(path: String, transition: bool = true) -> void:
    if _is_transitioning:
        return
    
    _target_scene_path = path
    
    if transition:
        _is_transitioning = true
        await _fade_out()
        _deferred_goto_scene()
        await _fade_in()
        _is_transitioning = false
    else:
        _deferred_goto_scene()

func _deferred_goto_scene() -> void:
    EventBus.scene_transition_started.emit(
        current_scene.scene_file_path if current_scene else "",
        _target_scene_path
    )
    
    current_scene.free()
    
    var new_scene = ResourceLoader.load(_target_scene_path)
    current_scene = new_scene.instantiate()
    get_tree().root.add_child(current_scene)
    get_tree().current_scene = current_scene
    
    EventBus.scene_transition_completed.emit(_target_scene_path)

func _fade_out(duration: float = 0.3) -> void:
    transition_started.emit()
    var color_rect = _transition_layer.get_child(0)
    var tween = create_tween()
    tween.tween_property(color_rect, "modulate:a", 1.0, duration)
    await tween.finished
    transition_mid_point.emit()

func _fade_in(duration: float = 0.3) -> void:
    var color_rect = _transition_layer.get_child(0)
    var tween = create_tween()
    tween.tween_property(color_rect, "modulate:a", 0.0, duration)
    await tween.finished
    transition_finished.emit()
# endregion

# region 场景重载
func reload_current_scene() -> void:
    if current_scene:
        goto_scene(current_scene.scene_file_path)

func preload_scene(path: String) -> void:
    ResourceLoader.load_threaded_request(path)
# endregion
```

---

## 类型特定结构

### 2D 平台游戏

```
scenes/
├── entities/
│   └── player/
│       ├── player.tscn
│       └── player.gd
│   └── enemies/
│       ├── base_enemy.tscn
│       └── slime.tscn
├── levels/
│   ├── level_01.tscn
│   └── tilesets/
│       └── main_tileset.tres
└── components/
    └── hitbox.tscn

scripts/
└── entities/
    └── player/
        ├── player_controller.gd
        └── player_states/
            ├── state_idle.gd
            ├── state_run.gd
            ├── state_jump.gd
            └── state_fall.gd
```

### 3D 第一人称

```
scenes/
├── entities/
│   └── player/
│       ├── player.tscn
│       └── weapons/
│           ├── weapon_holder.tscn
│           └── pistol.tscn
├── levels/
│   └── level_01.tscn
└── pickups/
    ├── health_pickup.tscn
    └── ammo_pickup.tscn

scripts/
└── entities/
    └── player/
        ├── fps_controller.gd
        ├── camera_controller.gd
        └── weapon_manager.gd
```

### RPG

```
scenes/
├── entities/
│   └── characters/
│       ├── player_character.tscn
│       └── npc.tscn
├── battle/
│   └── battle_scene.tscn
├── world/
│   └── overworld.tscn
└── ui/
    ├── inventory.tscn
    ├── character_sheet.tscn
    └── dialogue_box.tscn

scripts/
├── battle/
│   ├── battle_manager.gd
│   └── turn_system.gd
├── inventory/
│   └── inventory_system.gd
└── dialogue/
    └── dialogue_system.gd

data/
├── characters/
├── skills/
├── items/
└── quests/
```

---

## 初始化命令示例

### 创建 2D 平台游戏项目

```
创建一个 2D 平台游戏项目结构：
- 项目名称：ForestAdventure
- 特性：
  - 玩家控制器（状态机）
  - 敌人系统
  - 存档系统
  - 音频管理
  - UI 系统
```

### AI 执行步骤

1. 创建目录结构
2. 生成 project.godot
3. 生成核心 autoload 脚本
4. 生成玩家场景和脚本
5. 生成 UI 场景
6. 生成配置文件骨架
7. 创建 README.md

---

## 验证检查清单

项目结构生成后验证：

- [ ] project.godot 配置正确
- [ ] 所有 autoload 路径存在
- [ ] 主场景可以运行
- [ ] 物理层级配置正确
- [ ] 输入映射已设置
- [ ] 目录结构符合规范
- [ ] .gitignore 已配置
