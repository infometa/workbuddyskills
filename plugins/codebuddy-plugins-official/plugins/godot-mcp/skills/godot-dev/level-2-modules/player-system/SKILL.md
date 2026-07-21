---
name: player-system
description: >
  玩家控制系统技能。生成完整的玩家控制器，包括移动、跳跃、攻击、状态机等功能。
  支持 2D 和 3D 多种控制模式。
version: 1.0.0
dependencies:
  - godot-core
  - code-generator
  - input-system
triggers:
  - pattern: "玩家控制|角色控制|移动系统|Player|玩家移动"
inputs:
  - name: player_type
    type: string
    enum: ["platformer_2d", "topdown_2d", "third_person_3d", "first_person_3d"]
    required: true
  - name: features
    type: array
    items:
      enum: ["movement", "jump", "double_jump", "dash", "attack", "interact", "crouch", "climb", "swim"]
    required: false
outputs:
  - name: player_scene
    type: file
    path_pattern: "res://scenes/prefabs/player/player.tscn"
  - name: player_script
    type: file
    path_pattern: "res://scripts/entities/player/player.gd"
  - name: player_states
    type: directory
    path_pattern: "res://scripts/entities/player/states/"
---

# 玩家控制系统技能

生成完整的玩家控制系统，包含移动、状态机、输入处理等功能。

## 支持的控制器类型

### Platformer 2D（平台跳跃）

**适用游戏**：横版动作、银河恶魔城、平台跳跃

**特点**：
- 基于 CharacterBody2D
- 重力物理系统
- 可配置浮空时间（Coyote Time）
- 跳跃缓冲（Jump Buffer）
- 可变跳跃高度

**生成文件**：
```
res://scenes/prefabs/player/player_2d.tscn
res://scripts/entities/player/player_2d.gd
res://scripts/entities/player/player_2d_controller.gd
res://scripts/entities/player/states/
    ├── player_state.gd
    ├── idle_state.gd
    ├── run_state.gd
    ├── jump_state.gd
    ├── fall_state.gd
    └── ...
```

### Top-down 2D（俯视角）

**适用游戏**：RPG、动作冒险、射击游戏

**特点**：
- 8 方向移动
- 可选瞄准系统
- 平滑旋转

### Third Person 3D（第三人称）

**适用游戏**：动作 RPG、冒险游戏

**特点**：
- 与摄像机联动的移动方向
- 斜坡处理
- 阶梯检测

### First Person 3D（第一人称）

**适用游戏**：FPS、探索游戏、恐怖游戏

**特点**：
- 鼠标视角控制
- 头部摇摆
- 可选武器系统

---

## Platformer 2D 完整实现

### 玩家场景结构

```
Player (CharacterBody2D)
├── CollisionShape2D
├── Sprite2D / AnimatedSprite2D
├── AnimationPlayer
├── StateMachine
│   ├── IdleState
│   ├── RunState
│   ├── JumpState
│   ├── FallState
│   ├── DashState (可选)
│   └── AttackState (可选)
├── Hitbox (Area2D) - 攻击判定
├── Hurtbox (Area2D) - 受伤判定
├── CoyoteTimer (Timer)
├── JumpBufferTimer (Timer)
└── Camera2D (可选)
```

### 玩家主脚本 (player_2d.gd)

```gdscript
## 2D 平台跳跃玩家控制器
##
## 包含移动、跳跃、攻击等核心功能
## @author AI Generated
## @version 1.0.0
class_name Player2D
extends CharacterBody2D

# region 信号
signal died
signal health_changed(old_value: int, new_value: int)
signal state_changed(old_state: String, new_state: String)
signal jumped
signal landed
signal attacked
# endregion

# region 常量
const GRAVITY: float = 980.0
# endregion

# region 导出变量 - 移动
@export_group("Movement")
@export var move_speed: float = 200.0
@export var acceleration: float = 1500.0
@export var friction: float = 1200.0
@export var air_friction: float = 600.0
# endregion

# region 导出变量 - 跳跃
@export_group("Jump")
@export var jump_velocity: float = -350.0
@export var max_jumps: int = 1
@export var coyote_time: float = 0.1
@export var jump_buffer_time: float = 0.1
@export var variable_jump_multiplier: float = 0.5
# endregion

# region 导出变量 - 冲刺
@export_group("Dash")
@export var dash_enabled: bool = true
@export var dash_speed: float = 400.0
@export var dash_duration: float = 0.2
@export var dash_cooldown: float = 1.0
# endregion

# region 导出变量 - 属性
@export_group("Stats")
@export var max_health: int = 100
# endregion

# region 状态变量
var current_health: int:
    set(value):
        var old = current_health
        current_health = clampi(value, 0, max_health)
        health_changed.emit(old, current_health)
        if current_health <= 0:
            _die()

var is_alive: bool:
    get: return current_health > 0

var facing_direction: int = 1  # 1 = 右, -1 = 左
var jumps_remaining: int = 0
var can_coyote_jump: bool = false
var jump_buffered: bool = false
var can_dash: bool = true
var is_dashing: bool = false
# endregion

# region 节点引用
@onready var sprite: Sprite2D = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var state_machine: Node = $StateMachine
@onready var coyote_timer: Timer = $CoyoteTimer
@onready var jump_buffer_timer: Timer = $JumpBufferTimer
# endregion

# region 生命周期
func _ready() -> void:
    current_health = max_health
    jumps_remaining = max_jumps
    _setup_timers()

func _physics_process(delta: float) -> void:
    if not is_alive:
        return
    
    # 重力
    if not is_on_floor() and not is_dashing:
        velocity.y += GRAVITY * delta
    
    # 更新朝向
    var input_dir = Input.get_axis("move_left", "move_right")
    if input_dir != 0:
        facing_direction = signi(input_dir)
        sprite.flip_h = facing_direction < 0
    
    move_and_slide()
    
    # 检测落地
    if is_on_floor():
        jumps_remaining = max_jumps
        if jump_buffered:
            jump()

func _unhandled_input(event: InputEvent) -> void:
    if not is_alive:
        return
    
    if event.is_action_pressed("jump"):
        _handle_jump_input()
    
    if event.is_action_released("jump"):
        _handle_jump_release()
    
    if event.is_action_pressed("dash") and dash_enabled:
        _handle_dash_input()
    
    if event.is_action_pressed("attack"):
        attacked.emit()
# endregion

# region 移动
func apply_movement(delta: float, direction: float) -> void:
    if direction != 0:
        velocity.x = move_toward(velocity.x, direction * move_speed, acceleration * delta)
    else:
        var current_friction = friction if is_on_floor() else air_friction
        velocity.x = move_toward(velocity.x, 0, current_friction * delta)

func apply_gravity(delta: float, multiplier: float = 1.0) -> void:
    if not is_on_floor():
        velocity.y += GRAVITY * multiplier * delta
# endregion

# region 跳跃
func _handle_jump_input() -> void:
    if is_on_floor() or can_coyote_jump:
        jump()
    elif jumps_remaining > 0:
        jump()
    else:
        # 缓冲跳跃
        jump_buffered = true
        jump_buffer_timer.start(jump_buffer_time)

func _handle_jump_release() -> void:
    # 可变跳跃高度
    if velocity.y < 0:
        velocity.y *= variable_jump_multiplier

func jump() -> void:
    velocity.y = jump_velocity
    jumps_remaining -= 1
    jump_buffered = false
    can_coyote_jump = false
    jumped.emit()

func start_coyote_time() -> void:
    can_coyote_jump = true
    coyote_timer.start(coyote_time)
# endregion

# region 冲刺
func _handle_dash_input() -> void:
    if can_dash and not is_dashing:
        dash()

func dash() -> void:
    is_dashing = true
    can_dash = false
    velocity = Vector2(facing_direction * dash_speed, 0)
    
    await get_tree().create_timer(dash_duration).timeout
    is_dashing = false
    
    await get_tree().create_timer(dash_cooldown).timeout
    can_dash = true
# endregion

# region 伤害与死亡
func take_damage(amount: int, knockback: Vector2 = Vector2.ZERO) -> void:
    if not is_alive:
        return
    
    current_health -= amount
    
    if knockback != Vector2.ZERO:
        velocity = knockback

func heal(amount: int) -> void:
    current_health += amount

func _die() -> void:
    died.emit()
    # 播放死亡动画或处理
# endregion

# region 工具方法
func _setup_timers() -> void:
    coyote_timer.one_shot = true
    coyote_timer.timeout.connect(func(): can_coyote_jump = false)
    
    jump_buffer_timer.one_shot = true
    jump_buffer_timer.timeout.connect(func(): jump_buffered = false)

func get_input_direction() -> float:
    return Input.get_axis("move_left", "move_right")
# endregion
```

### 状态机基类 (state_machine.gd)

```gdscript
## 通用状态机
class_name StateMachine
extends Node

signal state_changed(old_state: State, new_state: State)

@export var initial_state: State

var current_state: State
var states: Dictionary = {}

func _ready() -> void:
    # 收集所有子状态
    for child in get_children():
        if child is State:
            states[child.name.to_lower()] = child
            child.state_machine = self
            child.player = get_parent()
    
    # 设置初始状态
    if initial_state:
        current_state = initial_state
        current_state.enter()

func _process(delta: float) -> void:
    if current_state:
        current_state.update(delta)

func _physics_process(delta: float) -> void:
    if current_state:
        current_state.physics_update(delta)
        
        # 检查状态转换
        var next_state_name = current_state.get_transition()
        if next_state_name != &"":
            transition_to(next_state_name)

func _unhandled_input(event: InputEvent) -> void:
    if current_state:
        current_state.handle_input(event)

func transition_to(state_name: StringName) -> void:
    var new_state = states.get(str(state_name).to_lower())
    if new_state == null:
        push_error("State not found: " + str(state_name))
        return
    
    if new_state == current_state:
        return
    
    var old_state = current_state
    current_state.exit()
    current_state = new_state
    current_state.enter()
    
    state_changed.emit(old_state, new_state)
```

### 状态基类 (state.gd)

```gdscript
## 状态基类
class_name State
extends Node

var state_machine: StateMachine
var player: CharacterBody2D

func enter() -> void:
    pass

func exit() -> void:
    pass

func update(_delta: float) -> void:
    pass

func physics_update(_delta: float) -> void:
    pass

func handle_input(_event: InputEvent) -> void:
    pass

func get_transition() -> StringName:
    return &""
```

### Idle 状态 (idle_state.gd)

```gdscript
## 待机状态
class_name IdleState
extends State

func enter() -> void:
    player.animation_player.play("idle")

func physics_update(delta: float) -> void:
    player.apply_movement(delta, 0)

func get_transition() -> StringName:
    if not player.is_on_floor():
        return &"fall"
    
    if player.get_input_direction() != 0:
        return &"run"
    
    return &""
```

### Run 状态 (run_state.gd)

```gdscript
## 奔跑状态
class_name RunState
extends State

func enter() -> void:
    player.animation_player.play("run")

func physics_update(delta: float) -> void:
    var direction = player.get_input_direction()
    player.apply_movement(delta, direction)

func get_transition() -> StringName:
    if not player.is_on_floor():
        player.start_coyote_time()
        return &"fall"
    
    if player.get_input_direction() == 0:
        return &"idle"
    
    return &""
```

### Jump 状态 (jump_state.gd)

```gdscript
## 跳跃状态
class_name JumpState
extends State

func enter() -> void:
    player.animation_player.play("jump")

func physics_update(delta: float) -> void:
    var direction = player.get_input_direction()
    player.apply_movement(delta, direction)
    player.apply_gravity(delta)

func get_transition() -> StringName:
    if player.velocity.y >= 0:
        return &"fall"
    
    return &""
```

### Fall 状态 (fall_state.gd)

```gdscript
## 下落状态
class_name FallState
extends State

func enter() -> void:
    player.animation_player.play("fall")

func physics_update(delta: float) -> void:
    var direction = player.get_input_direction()
    player.apply_movement(delta, direction)
    player.apply_gravity(delta)

func get_transition() -> StringName:
    if player.is_on_floor():
        player.landed.emit()
        if player.get_input_direction() != 0:
            return &"run"
        else:
            return &"idle"
    
    return &""
```

---

## Top-down 2D 实现

### 玩家脚本 (player_topdown.gd)

```gdscript
## 俯视角 2D 玩家控制器
class_name PlayerTopdown
extends CharacterBody2D

# region 信号
signal died
signal health_changed(old_value: int, new_value: int)
# endregion

# region 导出变量
@export_group("Movement")
@export var move_speed: float = 200.0
@export var acceleration: float = 2000.0
@export var friction: float = 1800.0

@export_group("Stats")
@export var max_health: int = 100
# endregion

# region 状态
var current_health: int:
    set(value):
        var old = current_health
        current_health = clampi(value, 0, max_health)
        health_changed.emit(old, current_health)
        if current_health <= 0:
            _die()

var look_direction: Vector2 = Vector2.RIGHT
# endregion

# region 节点引用
@onready var sprite: Sprite2D = $Sprite2D
@onready var animation_player: AnimationPlayer = $AnimationPlayer
# endregion

func _ready() -> void:
    current_health = max_health

func _physics_process(delta: float) -> void:
    var input_dir = Input.get_vector("move_left", "move_right", "move_up", "move_down")
    
    if input_dir != Vector2.ZERO:
        look_direction = input_dir.normalized()
        velocity = velocity.move_toward(input_dir * move_speed, acceleration * delta)
        _update_animation("walk")
    else:
        velocity = velocity.move_toward(Vector2.ZERO, friction * delta)
        _update_animation("idle")
    
    # 更新朝向
    _update_sprite_direction()
    
    move_and_slide()

func _update_animation(anim_base: String) -> void:
    var direction_suffix = _get_direction_suffix()
    var anim_name = anim_base + "_" + direction_suffix
    if animation_player.has_animation(anim_name):
        animation_player.play(anim_name)

func _get_direction_suffix() -> String:
    # 8方向动画
    var angle = look_direction.angle()
    if angle < -2.75 or angle > 2.75:
        return "left"
    elif angle < -1.96:
        return "up_left"
    elif angle < -1.18:
        return "up"
    elif angle < -0.39:
        return "up_right"
    elif angle < 0.39:
        return "right"
    elif angle < 1.18:
        return "down_right"
    elif angle < 1.96:
        return "down"
    else:
        return "down_left"

func _update_sprite_direction() -> void:
    sprite.flip_h = look_direction.x < 0

func take_damage(amount: int) -> void:
    current_health -= amount

func _die() -> void:
    died.emit()
```

---

## Third Person 3D 实现

### 玩家脚本 (player_3d.gd)

```gdscript
## 第三人称 3D 玩家控制器
class_name Player3D
extends CharacterBody3D

# region 信号
signal died
signal health_changed(old_value: int, new_value: int)
# endregion

# region 导出变量
@export_group("Movement")
@export var move_speed: float = 5.0
@export var sprint_speed: float = 8.0
@export var acceleration: float = 10.0
@export var rotation_speed: float = 10.0

@export_group("Jump")
@export var jump_velocity: float = 4.5
@export var gravity_multiplier: float = 1.0

@export_group("Stats")
@export var max_health: int = 100

@export_group("References")
@export var camera_pivot: Node3D
# endregion

# region 状态
var current_health: int
var is_sprinting: bool = false
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
# endregion

# region 节点引用
@onready var mesh: MeshInstance3D = $MeshInstance3D
@onready var animation_tree: AnimationTree = $AnimationTree
# endregion

func _ready() -> void:
    current_health = max_health
    Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _physics_process(delta: float) -> void:
    # 重力
    if not is_on_floor():
        velocity.y -= gravity * gravity_multiplier * delta
    
    # 跳跃
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = jump_velocity
    
    # 冲刺
    is_sprinting = Input.is_action_pressed("sprint") and is_on_floor()
    
    # 移动输入
    var input_dir = Input.get_vector("move_left", "move_right", "move_up", "move_down")
    
    # 相对于摄像机的移动方向
    var camera_basis = camera_pivot.global_transform.basis
    var direction = (camera_basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    direction.y = 0
    
    if direction:
        var target_speed = sprint_speed if is_sprinting else move_speed
        velocity.x = move_toward(velocity.x, direction.x * target_speed, acceleration * delta)
        velocity.z = move_toward(velocity.z, direction.z * target_speed, acceleration * delta)
        
        # 旋转角色朝向移动方向
        var target_rotation = atan2(-direction.x, -direction.z)
        rotation.y = lerp_angle(rotation.y, target_rotation, rotation_speed * delta)
    else:
        velocity.x = move_toward(velocity.x, 0, acceleration * delta)
        velocity.z = move_toward(velocity.z, 0, acceleration * delta)
    
    move_and_slide()
    
    # 更新动画
    _update_animations()

func _update_animations() -> void:
    if animation_tree:
        var speed = Vector2(velocity.x, velocity.z).length() / sprint_speed
        animation_tree.set("parameters/blend_position", speed)

func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_pressed("ui_cancel"):
        Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func take_damage(amount: int) -> void:
    var old = current_health
    current_health = clampi(current_health - amount, 0, max_health)
    health_changed.emit(old, current_health)
    if current_health <= 0:
        died.emit()
```

---

## 输入映射配置

生成玩家系统时，自动在 project.godot 中添加输入映射：

```ini
[input]

move_left={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":65,"physical_keycode":0,"key_label":0,"unicode":0,"echo":false,"script":null)
, Object(InputEventJoypadMotion,"resource_local_to_scene":false,"resource_name":"","device":-1,"axis":0,"axis_value":-1.0,"script":null)
]
}
move_right={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"window_id":0,"keycode":68,"script":null)
, Object(InputEventJoypadMotion,"resource_local_to_scene":false,"resource_name":"","device":-1,"axis":0,"axis_value":1.0,"script":null)
]
}
move_up={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"keycode":87,"script":null)
, Object(InputEventJoypadMotion,"resource_local_to_scene":false,"resource_name":"","device":-1,"axis":1,"axis_value":-1.0,"script":null)
]
}
move_down={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"keycode":83,"script":null)
, Object(InputEventJoypadMotion,"resource_local_to_scene":false,"resource_name":"","device":-1,"axis":1,"axis_value":1.0,"script":null)
]
}
jump={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"keycode":32,"script":null)
, Object(InputEventJoypadButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"button_index":0,"pressure":0.0,"pressed":false,"script":null)
]
}
dash={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"keycode":4194325,"script":null)
, Object(InputEventJoypadButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"button_index":4,"script":null)
]
}
attack={
"deadzone": 0.5,
"events": [Object(InputEventMouseButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"button_index":1,"pressed":false,"script":null)
, Object(InputEventJoypadButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"button_index":5,"script":null)
]
}
interact={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"keycode":69,"script":null)
, Object(InputEventJoypadButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"button_index":3,"script":null)
]
}
sprint={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"keycode":4194325,"script":null)
]
}
```

---

## 使用示例

### 生成 Platformer 2D 玩家

```
创建一个 2D 平台跳跃玩家控制器：
- 支持移动、跳跃、二段跳
- 支持冲刺
- 支持攻击
- 包含完整状态机
```

### 生成 Third Person 3D 玩家

```
创建一个第三人称 3D 玩家：
- WASD 移动，空格跳跃
- 与摄像机方向联动
- 支持冲刺
- 简单的攻击动作
```
