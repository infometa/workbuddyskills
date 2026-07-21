---
name: animation-system
description: >
  动画系统技能。管理游戏动画，包括骨骼动画、精灵动画、AnimationTree 状态机等。
version: 1.0.0
dependencies:
  - godot-core
triggers:
  - pattern: "动画|Animation|骨骼|Sprite|AnimationTree|动画状态机"
inputs:
  - name: animation_type
    type: string
    enum: ["sprite_2d", "skeletal_2d", "skeletal_3d", "procedural"]
    required: true
outputs:
  - name: animation_controller
    type: file
    path_pattern: "res://scripts/systems/animation/{type}_controller.gd"
---

# 动画系统技能

管理游戏中的各种动画系统。

## 动画类型概览

| 类型 | 维度 | 适用场景 | Godot 节点 |
|------|------|----------|------------|
| 精灵动画 | 2D | 像素游戏、简单 2D | AnimatedSprite2D |
| 精灵帧动画 | 2D | 复杂精灵、特效 | Sprite2D + AnimationPlayer |
| 骨骼动画 2D | 2D | 角色动画 | Skeleton2D + AnimationPlayer |
| 骨骼动画 3D | 3D | 3D 角色 | Skeleton3D + AnimationPlayer |
| 程序化动画 | 2D/3D | 物理效果、IK | 代码控制 |

---

## AnimationPlayer 动画控制

### animation_controller.gd

```gdscript
## 动画控制器
##
## 封装 AnimationPlayer，提供便捷的动画播放和混合功能
## @author AI Generated
## @version 1.0.0
class_name AnimationController
extends Node

# region 信号
signal animation_started(anim_name: String)
signal animation_finished(anim_name: String)
signal animation_changed(old_anim: String, new_anim: String)
# endregion

# region 导出变量
@export var animation_player: AnimationPlayer
@export var default_blend_time: float = 0.1
# endregion

# region 状态
var current_animation: String = ""
var _animation_queue: Array = []
var _is_locked: bool = false
# endregion

# region 生命周期
func _ready() -> void:
    if animation_player:
        animation_player.animation_finished.connect(_on_animation_finished)
# endregion

# region 播放控制
## 播放动画（可选混合时间）
func play(anim_name: String, blend_time: float = -1, from_end: bool = false) -> void:
    if _is_locked:
        return
    
    if not animation_player.has_animation(anim_name):
        push_warning("Animation not found: " + anim_name)
        return
    
    if blend_time < 0:
        blend_time = default_blend_time
    
    var old_anim = current_animation
    current_animation = anim_name
    
    if from_end:
        animation_player.play_backwards(anim_name)
    else:
        animation_player.play(anim_name, blend_time)
    
    if old_anim != anim_name:
        animation_changed.emit(old_anim, anim_name)
    animation_started.emit(anim_name)

## 播放动画并锁定（不可被打断）
func play_locked(anim_name: String, blend_time: float = -1) -> void:
    if _is_locked:
        return
    
    _is_locked = true
    play(anim_name, blend_time)

## 添加到队列
func queue_animation(anim_name: String) -> void:
    _animation_queue.append(anim_name)

## 停止动画
func stop() -> void:
    animation_player.stop()
    _is_locked = false

## 暂停动画
func pause() -> void:
    animation_player.pause()

## 继续动画
func resume() -> void:
    animation_player.play()
# endregion

# region 查询
func is_playing(anim_name: String = "") -> bool:
    if anim_name.is_empty():
        return animation_player.is_playing()
    return animation_player.is_playing() and current_animation == anim_name

func get_animation_length(anim_name: String) -> float:
    if animation_player.has_animation(anim_name):
        return animation_player.get_animation(anim_name).length
    return 0.0

func get_current_position() -> float:
    return animation_player.current_animation_position

func get_progress() -> float:
    var length = get_animation_length(current_animation)
    if length > 0:
        return animation_player.current_animation_position / length
    return 0.0
# endregion

# region 速度控制
func set_speed_scale(scale: float) -> void:
    animation_player.speed_scale = scale

func get_speed_scale() -> float:
    return animation_player.speed_scale
# endregion

# region 事件处理
func _on_animation_finished(anim_name: String) -> void:
    _is_locked = false
    animation_finished.emit(anim_name)
    
    # 播放队列中的下一个动画
    if not _animation_queue.is_empty():
        var next_anim = _animation_queue.pop_front()
        play(next_anim)
# endregion
```

---

## AnimationTree 状态机

### 场景结构

```
Character
├── Sprite2D / MeshInstance3D
├── AnimationPlayer
└── AnimationTree
    └── AnimationNodeStateMachine (root)
        ├── Idle
        ├── Walk
        ├── Run
        ├── Jump
        ├── Fall
        └── Attack (BlendSpace / OneShot)
```

### animation_tree_controller.gd

```gdscript
## AnimationTree 状态机控制器
##
## 通过状态机管理复杂动画转换
## @author AI Generated
## @version 1.0.0
class_name AnimationTreeController
extends Node

# region 信号
signal state_changed(old_state: String, new_state: String)
# endregion

# region 导出变量
@export var animation_tree: AnimationTree
@export var state_machine_path: String = "parameters/playback"
# endregion

# region 状态
var _state_machine: AnimationNodeStateMachinePlayback
var current_state: String = ""
# endregion

func _ready() -> void:
    if animation_tree:
        animation_tree.active = true
        _state_machine = animation_tree.get(state_machine_path)

# region 状态控制
## 切换到指定状态
func travel(state_name: String) -> void:
    if not _state_machine:
        return
    
    var old_state = current_state
    _state_machine.travel(state_name)
    current_state = state_name
    
    if old_state != state_name:
        state_changed.emit(old_state, state_name)

## 立即切换状态（无过渡）
func start(state_name: String, reset: bool = true) -> void:
    if not _state_machine:
        return
    
    var old_state = current_state
    _state_machine.start(state_name, reset)
    current_state = state_name
    
    if old_state != state_name:
        state_changed.emit(old_state, state_name)

## 停止状态机
func stop() -> void:
    if _state_machine:
        _state_machine.stop()
# endregion

# region 参数控制
## 设置混合参数
func set_blend_position(param_path: String, position: Vector2) -> void:
    animation_tree.set(param_path, position)

func set_blend_amount(param_path: String, amount: float) -> void:
    animation_tree.set(param_path, amount)

## 触发 OneShot
func trigger_oneshot(param_path: String) -> void:
    animation_tree.set(param_path + "/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)

## 中止 OneShot
func abort_oneshot(param_path: String) -> void:
    animation_tree.set(param_path + "/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_ABORT)

## 设置时间缩放
func set_time_scale(param_path: String, scale: float) -> void:
    animation_tree.set(param_path, scale)
# endregion

# region 查询
func get_current_state() -> String:
    if _state_machine:
        return _state_machine.get_current_node()
    return ""

func is_in_state(state_name: String) -> bool:
    return get_current_state() == state_name

func get_travel_path() -> PackedStringArray:
    if _state_machine:
        return _state_machine.get_travel_path()
    return PackedStringArray()

func is_playing() -> bool:
    if _state_machine:
        return _state_machine.is_playing()
    return false
# endregion
```

---

## 2D 精灵动画

### AnimatedSprite2D 控制器

```gdscript
## 精灵动画控制器
class_name SpriteAnimationController
extends Node

signal animation_finished(anim_name: String)
signal frame_changed(frame: int)

@export var animated_sprite: AnimatedSprite2D

var current_animation: String = ""
var _locked: bool = false

func _ready() -> void:
    if animated_sprite:
        animated_sprite.animation_finished.connect(_on_animation_finished)
        animated_sprite.frame_changed.connect(_on_frame_changed)

func play(anim_name: String, from_frame: int = 0) -> void:
    if _locked:
        return
    
    if not animated_sprite.sprite_frames.has_animation(anim_name):
        push_warning("Animation not found: " + anim_name)
        return
    
    current_animation = anim_name
    animated_sprite.play(anim_name)
    if from_frame > 0:
        animated_sprite.frame = from_frame

func play_locked(anim_name: String) -> void:
    _locked = true
    play(anim_name)

func stop() -> void:
    animated_sprite.stop()
    _locked = false

func pause() -> void:
    animated_sprite.pause()

func set_flip_h(flip: bool) -> void:
    animated_sprite.flip_h = flip

func set_flip_v(flip: bool) -> void:
    animated_sprite.flip_v = flip

func _on_animation_finished() -> void:
    _locked = false
    animation_finished.emit(current_animation)

func _on_frame_changed() -> void:
    frame_changed.emit(animated_sprite.frame)
```

### SpriteFrames 生成

```gdscript
## 从精灵表生成 SpriteFrames
static func create_sprite_frames_from_sheet(
    texture: Texture2D,
    frame_size: Vector2i,
    animations: Dictionary  # {"walk": {"row": 0, "frames": 8, "fps": 10, "loop": true}}
) -> SpriteFrames:
    var sprite_frames = SpriteFrames.new()
    
    var columns = texture.get_width() / frame_size.x
    
    for anim_name in animations:
        var anim_data = animations[anim_name]
        sprite_frames.add_animation(anim_name)
        sprite_frames.set_animation_speed(anim_name, anim_data.get("fps", 10))
        sprite_frames.set_animation_loop(anim_name, anim_data.get("loop", true))
        
        var row = anim_data.get("row", 0)
        var frame_count = anim_data.get("frames", 1)
        var start_frame = anim_data.get("start", 0)
        
        for i in range(frame_count):
            var atlas = AtlasTexture.new()
            atlas.atlas = texture
            atlas.region = Rect2(
                (start_frame + i) * frame_size.x,
                row * frame_size.y,
                frame_size.x,
                frame_size.y
            )
            sprite_frames.add_frame(anim_name, atlas)
    
    return sprite_frames
```

---

## 3D 骨骼动画

### 动画混合控制器

```gdscript
## 3D 动画混合控制器
##
## 支持上下半身分离、叠加动画等
class_name Animation3DController
extends Node

@export var animation_tree: AnimationTree

# 混合参数路径
const LOCOMOTION_BLEND = "parameters/locomotion/blend_position"
const UPPER_BODY_BLEND = "parameters/upper_body/blend_amount"
const ACTION_ONESHOT = "parameters/action/request"

var _velocity: Vector2 = Vector2.ZERO

func _process(delta: float) -> void:
    _update_locomotion_blend()

func set_velocity(velocity: Vector3) -> void:
    _velocity = Vector2(velocity.x, velocity.z)

func _update_locomotion_blend() -> void:
    # 2D 混合空间：根据速度设置动画混合
    animation_tree.set(LOCOMOTION_BLEND, _velocity)

func play_upper_body_animation(blend: float = 1.0) -> void:
    animation_tree.set(UPPER_BODY_BLEND, blend)

func trigger_action(action_name: String) -> void:
    # 切换到对应动作状态
    var state_machine = animation_tree.get("parameters/playback")
    state_machine.travel(action_name)

func play_oneshot_action() -> void:
    animation_tree.set(ACTION_ONESHOT, AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)
```

---

## 程序化动画

### 弹簧动画

```gdscript
## 弹簧动画
##
## 用于平滑过渡、晃动效果等
class_name SpringAnimation
extends RefCounted

var position: float = 0.0
var velocity: float = 0.0
var target: float = 0.0

var stiffness: float = 100.0  # 弹性系数
var damping: float = 10.0     # 阻尼系数
var mass: float = 1.0         # 质量

func update(delta: float) -> float:
    var force = (target - position) * stiffness
    var damping_force = -velocity * damping
    var acceleration = (force + damping_force) / mass
    
    velocity += acceleration * delta
    position += velocity * delta
    
    return position

func set_target(value: float) -> void:
    target = value

func snap_to(value: float) -> void:
    position = value
    velocity = 0.0
    target = value

func is_at_rest(threshold: float = 0.001) -> bool:
    return abs(position - target) < threshold and abs(velocity) < threshold
```

### 2D 弹簧动画

```gdscript
## 2D 弹簧动画
class_name SpringAnimation2D
extends RefCounted

var position: Vector2 = Vector2.ZERO
var velocity: Vector2 = Vector2.ZERO
var target: Vector2 = Vector2.ZERO

var stiffness: float = 100.0
var damping: float = 10.0
var mass: float = 1.0

func update(delta: float) -> Vector2:
    var force = (target - position) * stiffness
    var damping_force = -velocity * damping
    var acceleration = (force + damping_force) / mass
    
    velocity += acceleration * delta
    position += velocity * delta
    
    return position

func set_target(value: Vector2) -> void:
    target = value

func snap_to(value: Vector2) -> void:
    position = value
    velocity = Vector2.ZERO
    target = value
```

### 挤压拉伸效果

```gdscript
## 挤压拉伸动画
class_name SquashStretch
extends Node

@export var target: Node2D
@export var default_scale: Vector2 = Vector2.ONE

var _spring: SpringAnimation2D

func _ready() -> void:
    _spring = SpringAnimation2D.new()
    _spring.stiffness = 200.0
    _spring.damping = 15.0
    _spring.snap_to(default_scale)

func _process(delta: float) -> void:
    target.scale = _spring.update(delta)

## 挤压效果（落地）
func squash(intensity: float = 0.3) -> void:
    _spring.position = Vector2(
        default_scale.x * (1 + intensity),
        default_scale.y * (1 - intensity)
    )
    _spring.set_target(default_scale)

## 拉伸效果（跳跃）
func stretch(intensity: float = 0.3) -> void:
    _spring.position = Vector2(
        default_scale.x * (1 - intensity * 0.5),
        default_scale.y * (1 + intensity)
    )
    _spring.set_target(default_scale)

## 自定义变形
func deform(scale_offset: Vector2) -> void:
    _spring.position = default_scale + scale_offset
    _spring.set_target(default_scale)
```

---

## 动画事件系统

### animation_event_handler.gd

```gdscript
## 动画事件处理器
##
## 处理 AnimationPlayer 中的方法调用轨道
class_name AnimationEventHandler
extends Node

signal footstep(foot: String)
signal attack_hit
signal attack_end
signal effect_spawn(effect_name: String, position: Vector3)

## 脚步声事件（在动画中调用）
func on_footstep(foot: String = "left") -> void:
    footstep.emit(foot)

## 攻击命中帧
func on_attack_hit() -> void:
    attack_hit.emit()

## 攻击结束
func on_attack_end() -> void:
    attack_end.emit()

## 生成特效
func on_spawn_effect(effect_name: String, local_pos: Vector3 = Vector3.ZERO) -> void:
    var world_pos = get_parent().global_position + local_pos
    effect_spawn.emit(effect_name, world_pos)

## 播放音效
func on_play_sound(sound_name: String) -> void:
    AudioManager.play_sfx(sound_name)

## 屏幕震动
func on_screen_shake(intensity: float = 0.5, duration: float = 0.2) -> void:
    var camera = get_viewport().get_camera_3d()
    if camera and camera.has_method("shake"):
        camera.shake(intensity, duration)
```

---

## 配置示例

### animation_config.json

```json
{
  "characters": {
    "player": {
      "animations": {
        "idle": { "loop": true, "speed": 1.0 },
        "walk": { "loop": true, "speed": 1.0 },
        "run": { "loop": true, "speed": 1.2 },
        "jump": { "loop": false, "speed": 1.0 },
        "fall": { "loop": true, "speed": 1.0 },
        "attack_1": { "loop": false, "speed": 1.0, "can_cancel_after": 0.5 },
        "attack_2": { "loop": false, "speed": 1.0, "can_cancel_after": 0.4 },
        "attack_3": { "loop": false, "speed": 1.0, "can_cancel_after": 0.6 },
        "hurt": { "loop": false, "speed": 1.0 },
        "death": { "loop": false, "speed": 1.0 }
      },
      "blend_times": {
        "idle->walk": 0.1,
        "walk->run": 0.1,
        "any->jump": 0.05,
        "any->hurt": 0.0
      }
    }
  }
}
```

---

## 使用示例

### 创建角色动画状态机

```
创建一个 2D 平台游戏角色的动画系统：
- 支持 Idle, Walk, Run, Jump, Fall, Attack 动画
- 使用 AnimationTree 状态机管理转换
- 攻击可以打断移动，但不能被移动打断
- 跳跃和下落可以播放攻击动画（叠加）
```
