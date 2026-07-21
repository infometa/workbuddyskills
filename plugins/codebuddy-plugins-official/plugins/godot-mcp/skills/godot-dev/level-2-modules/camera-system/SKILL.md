---
name: camera-system
description: >
  摄像机系统技能。生成各种类型的摄像机控制器，支持 2D/3D、跟随、轨道等多种模式。
version: 1.0.0
dependencies:
  - godot-core
  - code-generator
triggers:
  - pattern: "摄像机|相机|Camera|视角|镜头|跟随摄像机"
inputs:
  - name: camera_type
    type: string
    enum: ["follow_2d", "follow_3d", "third_person", "first_person", "orbit", "rail", "fixed"]
    required: true
  - name: features
    type: array
    items:
      enum: ["smooth_follow", "screen_shake", "zoom", "look_ahead", "boundaries", "dead_zone"]
    required: false
outputs:
  - name: camera_scene
    type: file
    path_pattern: "res://scenes/prefabs/cameras/{type}_camera.tscn"
  - name: camera_script
    type: file
    path_pattern: "res://scripts/systems/camera/{type}_camera.gd"
---

# 摄像机系统技能

生成各种类型的摄像机控制器。

## 摄像机类型概览

| 类型 | 维度 | 适用场景 | 主要特点 |
|------|------|----------|----------|
| follow_2d | 2D | 平台跳跃、横版动作 | 平滑跟随、边界限制 |
| follow_3d | 3D | 俯视角、等距视角 | 固定角度跟随 |
| third_person | 3D | RPG、动作游戏 | 绕目标旋转、碰撞检测 |
| first_person | 3D | FPS、探索游戏 | 鼠标控制视角 |
| orbit | 3D | 物品展示、编辑器 | 360° 环绕 |
| rail | 3D | 过场动画、固定路线 | 沿路径移动 |
| fixed | 2D/3D | 固定视角游戏 | 静态位置 |

---

## Follow 2D 摄像机

### 场景结构

```
Camera2D
├── ShakeTimer
└── (RemoteTransform2D on target)
```

### 完整脚本 (follow_camera_2d.gd)

```gdscript
## 2D 跟随摄像机
##
## 特点：平滑跟随、前视偏移、屏幕震动、边界限制
## @author AI Generated
## @version 1.0.0
class_name FollowCamera2D
extends Camera2D

# region 信号
signal shake_started
signal shake_ended
# endregion

# region 导出变量 - 跟随
@export_group("Follow")
@export var target: Node2D
@export var follow_speed: float = 5.0
@export var offset: Vector2 = Vector2.ZERO
# endregion

# region 导出变量 - 前视
@export_group("Look Ahead")
@export var look_ahead_enabled: bool = true
@export var look_ahead_distance: float = 50.0
@export var look_ahead_speed: float = 3.0
# endregion

# region 导出变量 - 死区
@export_group("Dead Zone")
@export var dead_zone_enabled: bool = false
@export var dead_zone_size: Vector2 = Vector2(100, 50)
# endregion

# region 导出变量 - 边界
@export_group("Boundaries")
@export var use_boundaries: bool = false
@export var boundary_left: float = -1000
@export var boundary_right: float = 1000
@export var boundary_top: float = -1000
@export var boundary_bottom: float = 1000
# endregion

# region 导出变量 - 震动
@export_group("Screen Shake")
@export var shake_decay: float = 5.0
@export var shake_max_offset: Vector2 = Vector2(100, 75)
# endregion

# region 私有变量
var _current_look_ahead: Vector2 = Vector2.ZERO
var _shake_intensity: float = 0.0
var _shake_offset: Vector2 = Vector2.ZERO
var _target_position: Vector2 = Vector2.ZERO
# endregion

# region 生命周期
func _ready() -> void:
    if target:
        global_position = target.global_position + offset
    make_current()

func _process(delta: float) -> void:
    if not target:
        return
    
    _update_target_position(delta)
    _apply_look_ahead(delta)
    _apply_shake(delta)
    _apply_boundaries()
    
    # 平滑移动
    global_position = global_position.lerp(_target_position + _shake_offset, follow_speed * delta)
# endregion

# region 跟随逻辑
func _update_target_position(delta: float) -> void:
    var target_pos = target.global_position + offset
    
    if dead_zone_enabled:
        var diff = target_pos - global_position
        if abs(diff.x) > dead_zone_size.x:
            _target_position.x = target_pos.x - sign(diff.x) * dead_zone_size.x
        if abs(diff.y) > dead_zone_size.y:
            _target_position.y = target_pos.y - sign(diff.y) * dead_zone_size.y
    else:
        _target_position = target_pos
# endregion

# region 前视偏移
func _apply_look_ahead(delta: float) -> void:
    if not look_ahead_enabled:
        return
    
    if target.has_method("get_velocity"):
        var velocity = target.get_velocity()
        if velocity != Vector2.ZERO:
            var look_ahead_target = velocity.normalized() * look_ahead_distance
            _current_look_ahead = _current_look_ahead.lerp(look_ahead_target, look_ahead_speed * delta)
        else:
            _current_look_ahead = _current_look_ahead.lerp(Vector2.ZERO, look_ahead_speed * delta)
    elif target is CharacterBody2D:
        var velocity = target.velocity
        if velocity != Vector2.ZERO:
            var look_ahead_target = velocity.normalized() * look_ahead_distance
            _current_look_ahead = _current_look_ahead.lerp(look_ahead_target, look_ahead_speed * delta)
        else:
            _current_look_ahead = _current_look_ahead.lerp(Vector2.ZERO, look_ahead_speed * delta)
    
    _target_position += _current_look_ahead
# endregion

# region 屏幕震动
func shake(intensity: float, duration: float = 0.3) -> void:
    _shake_intensity = intensity
    shake_started.emit()
    
    var tween = create_tween()
    tween.tween_property(self, "_shake_intensity", 0.0, duration)
    tween.tween_callback(func(): shake_ended.emit())

func _apply_shake(delta: float) -> void:
    if _shake_intensity > 0:
        _shake_offset = Vector2(
            randf_range(-1, 1) * shake_max_offset.x,
            randf_range(-1, 1) * shake_max_offset.y
        ) * _shake_intensity
    else:
        _shake_offset = Vector2.ZERO
# endregion

# region 边界限制
func _apply_boundaries() -> void:
    if not use_boundaries:
        return
    
    _target_position.x = clampf(_target_position.x, boundary_left, boundary_right)
    _target_position.y = clampf(_target_position.y, boundary_top, boundary_bottom)

func set_boundaries(left: float, right: float, top: float, bottom: float) -> void:
    boundary_left = left
    boundary_right = right
    boundary_top = top
    boundary_bottom = bottom
    use_boundaries = true
# endregion

# region 公共 API
func set_target(new_target: Node2D) -> void:
    target = new_target

func snap_to_target() -> void:
    if target:
        global_position = target.global_position + offset
        _target_position = global_position

func set_offset(new_offset: Vector2) -> void:
    offset = new_offset

func zoom_to(new_zoom: Vector2, duration: float = 0.5) -> void:
    var tween = create_tween()
    tween.tween_property(self, "zoom", new_zoom, duration).set_ease(Tween.EASE_OUT)
# endregion
```

---

## Third Person 3D 摄像机

### 场景结构

```
CameraPivot (Node3D) - 跟随目标
├── SpringArm3D - 碰撞处理
│   └── Camera3D
└── (可选) CrosshairUI
```

### 完整脚本 (third_person_camera.gd)

```gdscript
## 第三人称 3D 摄像机
##
## 特点：鼠标控制旋转、碰撞避免、平滑跟随
## @author AI Generated
## @version 1.0.0
class_name ThirdPersonCamera
extends Node3D

# region 导出变量 - 目标
@export_group("Target")
@export var target: Node3D
@export var follow_speed: float = 10.0
@export var offset: Vector3 = Vector3(0, 1.5, 0)
# endregion

# region 导出变量 - 旋转
@export_group("Rotation")
@export var mouse_sensitivity: float = 0.002
@export var controller_sensitivity: float = 2.0
@export var pitch_min: float = -80.0
@export var pitch_max: float = 80.0
@export var invert_y: bool = false
# endregion

# region 导出变量 - 距离
@export_group("Distance")
@export var default_distance: float = 5.0
@export var min_distance: float = 1.0
@export var max_distance: float = 10.0
@export var zoom_speed: float = 2.0
# endregion

# region 导出变量 - 碰撞
@export_group("Collision")
@export var collision_margin: float = 0.2
@export var collision_mask: int = 1
# endregion

# region 节点引用
@onready var spring_arm: SpringArm3D = $SpringArm3D
@onready var camera: Camera3D = $SpringArm3D/Camera3D
# endregion

# region 私有变量
var _yaw: float = 0.0
var _pitch: float = 0.0
var _target_distance: float
# endregion

# region 生命周期
func _ready() -> void:
    Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
    _target_distance = default_distance
    
    if spring_arm:
        spring_arm.spring_length = default_distance
        spring_arm.margin = collision_margin
        spring_arm.collision_mask = collision_mask
    
    if target:
        global_position = target.global_position + offset

func _process(delta: float) -> void:
    _handle_controller_input(delta)
    _update_position(delta)
    _update_rotation()
    _update_zoom(delta)

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
        _handle_mouse_input(event)
    
    if event is InputEventMouseButton:
        _handle_zoom_input(event)
    
    if event.is_action_pressed("ui_cancel"):
        _toggle_mouse_mode()
# endregion

# region 输入处理
func _handle_mouse_input(event: InputEventMouseMotion) -> void:
    _yaw -= event.relative.x * mouse_sensitivity
    
    var pitch_delta = event.relative.y * mouse_sensitivity
    if invert_y:
        pitch_delta = -pitch_delta
    _pitch -= pitch_delta
    _pitch = clampf(_pitch, deg_to_rad(pitch_min), deg_to_rad(pitch_max))

func _handle_controller_input(delta: float) -> void:
    var look_input = Input.get_vector("look_left", "look_right", "look_up", "look_down")
    if look_input != Vector2.ZERO:
        _yaw -= look_input.x * controller_sensitivity * delta
        
        var pitch_delta = look_input.y * controller_sensitivity * delta
        if invert_y:
            pitch_delta = -pitch_delta
        _pitch -= pitch_delta
        _pitch = clampf(_pitch, deg_to_rad(pitch_min), deg_to_rad(pitch_max))

func _handle_zoom_input(event: InputEventMouseButton) -> void:
    if event.button_index == MOUSE_BUTTON_WHEEL_UP:
        _target_distance = maxf(_target_distance - zoom_speed, min_distance)
    elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
        _target_distance = minf(_target_distance + zoom_speed, max_distance)
# endregion

# region 更新逻辑
func _update_position(delta: float) -> void:
    if not target:
        return
    
    var target_pos = target.global_position + offset
    global_position = global_position.lerp(target_pos, follow_speed * delta)

func _update_rotation() -> void:
    rotation = Vector3(_pitch, _yaw, 0)

func _update_zoom(delta: float) -> void:
    if spring_arm:
        spring_arm.spring_length = lerpf(spring_arm.spring_length, _target_distance, zoom_speed * delta)
# endregion

# region 公共 API
func set_target(new_target: Node3D) -> void:
    target = new_target

func snap_to_target() -> void:
    if target:
        global_position = target.global_position + offset

func set_yaw(value: float) -> void:
    _yaw = value

func set_pitch(value: float) -> void:
    _pitch = clampf(value, deg_to_rad(pitch_min), deg_to_rad(pitch_max))

func get_camera_forward() -> Vector3:
    return -camera.global_transform.basis.z

func get_camera_right() -> Vector3:
    return camera.global_transform.basis.x

func _toggle_mouse_mode() -> void:
    if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
        Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
    else:
        Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
# endregion

# region 屏幕震动
func shake(intensity: float, duration: float = 0.3) -> void:
    var original_offset = camera.position
    
    var tween = create_tween()
    for i in range(int(duration * 60)):
        var shake_offset = Vector3(
            randf_range(-1, 1),
            randf_range(-1, 1),
            randf_range(-1, 1)
        ) * intensity * (1.0 - float(i) / (duration * 60))
        tween.tween_property(camera, "position", original_offset + shake_offset, 1.0/60.0)
    
    tween.tween_property(camera, "position", original_offset, 0.05)
# endregion
```

---

## First Person 3D 摄像机

### 场景结构

```
Player (CharacterBody3D)
├── Head (Node3D) - 头部节点，用于视角旋转
│   └── Camera3D
└── ...
```

### 完整脚本 (first_person_camera.gd)

```gdscript
## 第一人称摄像机控制器
##
## 附加到 Head 节点上，处理视角旋转
## @author AI Generated
## @version 1.0.0
class_name FirstPersonCamera
extends Node3D

# region 导出变量
@export_group("Sensitivity")
@export var mouse_sensitivity: float = 0.002
@export var controller_sensitivity: float = 2.0

@export_group("Limits")
@export var pitch_min: float = -89.0
@export var pitch_max: float = 89.0

@export_group("Head Bob")
@export var head_bob_enabled: bool = true
@export var head_bob_frequency: float = 2.0
@export var head_bob_amplitude: Vector2 = Vector2(0.05, 0.1)

@export_group("Options")
@export var invert_y: bool = false
# endregion

# region 节点引用
@onready var camera: Camera3D = $Camera3D
# endregion

# region 私有变量
var _head_bob_time: float = 0.0
var _initial_camera_pos: Vector3
# endregion

func _ready() -> void:
    Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
    if camera:
        _initial_camera_pos = camera.position

func _process(delta: float) -> void:
    _handle_controller_look(delta)
    _update_head_bob(delta)

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
        _handle_mouse_look(event)
    
    if event.is_action_pressed("ui_cancel"):
        if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
            Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
        else:
            Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _handle_mouse_look(event: InputEventMouseMotion) -> void:
    # 水平旋转 - 旋转整个玩家
    get_parent().rotate_y(-event.relative.x * mouse_sensitivity)
    
    # 垂直旋转 - 只旋转头部
    var pitch_delta = event.relative.y * mouse_sensitivity
    if invert_y:
        pitch_delta = -pitch_delta
    
    rotation.x = clampf(rotation.x - pitch_delta, deg_to_rad(pitch_min), deg_to_rad(pitch_max))

func _handle_controller_look(delta: float) -> void:
    var look_input = Input.get_vector("look_left", "look_right", "look_up", "look_down")
    
    if look_input != Vector2.ZERO:
        get_parent().rotate_y(-look_input.x * controller_sensitivity * delta)
        
        var pitch_delta = look_input.y * controller_sensitivity * delta
        if invert_y:
            pitch_delta = -pitch_delta
        
        rotation.x = clampf(rotation.x - pitch_delta, deg_to_rad(pitch_min), deg_to_rad(pitch_max))

func _update_head_bob(delta: float) -> void:
    if not head_bob_enabled or not camera:
        return
    
    var player = get_parent()
    if player is CharacterBody3D:
        if player.is_on_floor() and player.velocity.length() > 0.1:
            _head_bob_time += delta * head_bob_frequency * player.velocity.length()
            camera.position.x = _initial_camera_pos.x + sin(_head_bob_time) * head_bob_amplitude.x
            camera.position.y = _initial_camera_pos.y + sin(_head_bob_time * 2) * head_bob_amplitude.y
        else:
            camera.position = camera.position.lerp(_initial_camera_pos, 10 * delta)

# region 公共 API
func get_look_direction() -> Vector3:
    return -global_transform.basis.z

func set_sensitivity(value: float) -> void:
    mouse_sensitivity = value

func set_invert_y(value: bool) -> void:
    invert_y = value
# endregion
```

---

## Orbit 摄像机（物品展示）

```gdscript
## 轨道摄像机
##
## 用于物品展示、编辑器等场景
## @author AI Generated
## @version 1.0.0
class_name OrbitCamera
extends Node3D

@export var target: Node3D
@export var distance: float = 5.0
@export var min_distance: float = 2.0
@export var max_distance: float = 20.0
@export var rotation_speed: float = 0.01
@export var zoom_speed: float = 0.5
@export var auto_rotate: bool = false
@export var auto_rotate_speed: float = 0.5

var _yaw: float = 0.0
var _pitch: float = 0.0
var _is_dragging: bool = false

@onready var camera: Camera3D = $Camera3D

func _ready() -> void:
    _update_camera_position()

func _process(delta: float) -> void:
    if auto_rotate and not _is_dragging:
        _yaw += auto_rotate_speed * delta
    _update_camera_position()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_LEFT:
            _is_dragging = event.pressed
        elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
            distance = maxf(distance - zoom_speed, min_distance)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            distance = minf(distance + zoom_speed, max_distance)
    
    if event is InputEventMouseMotion and _is_dragging:
        _yaw -= event.relative.x * rotation_speed
        _pitch -= event.relative.y * rotation_speed
        _pitch = clampf(_pitch, -PI/2 + 0.1, PI/2 - 0.1)

func _update_camera_position() -> void:
    var target_pos = target.global_position if target else Vector3.ZERO
    
    var offset = Vector3(
        cos(_pitch) * sin(_yaw),
        sin(_pitch),
        cos(_pitch) * cos(_yaw)
    ) * distance
    
    camera.global_position = target_pos + offset
    camera.look_at(target_pos)

func set_target(new_target: Node3D) -> void:
    target = new_target
```

---

## 配置文件 (camera_config.json)

```json
{
  "cameras": {
    "follow_2d": {
      "follow_speed": 5.0,
      "look_ahead_enabled": true,
      "look_ahead_distance": 50.0,
      "dead_zone_enabled": false
    },
    "third_person": {
      "default_distance": 5.0,
      "mouse_sensitivity": 0.002,
      "pitch_min": -80.0,
      "pitch_max": 80.0
    },
    "first_person": {
      "mouse_sensitivity": 0.002,
      "head_bob_enabled": true,
      "pitch_min": -89.0,
      "pitch_max": 89.0
    }
  }
}
```

---

## 使用示例

### 创建 2D 跟随摄像机

```
创建一个 2D 跟随摄像机：
- 平滑跟随玩家
- 带前视偏移
- 支持屏幕震动
- 限制在关卡边界内
```

### 创建第三人称摄像机

```
创建第三人称摄像机：
- 鼠标控制旋转
- 滚轮缩放距离
- 自动避免穿墙
- 平滑跟随目标
```
