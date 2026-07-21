---
name: input-system
description: >
  输入系统技能。管理游戏输入映射、支持键盘/手柄/触屏多种输入方式，
  提供输入缓冲、连招检测等高级功能。
version: 1.0.0
dependencies:
  - godot-core
triggers:
  - pattern: "输入|按键|手柄|控制器|Input|键盘映射"
inputs:
  - name: input_type
    type: string
    enum: ["basic", "advanced", "fighting_game"]
    required: false
outputs:
  - name: input_manager
    type: file
    path_pattern: "res://scripts/autoload/input_manager.gd"
---

# 输入系统技能

管理游戏输入，支持多种输入设备和高级输入处理。

## 标准输入映射

### 动作游戏输入

```ini
[input]

# 移动
move_left = [A, D-Pad Left, Left Stick Left]
move_right = [D, D-Pad Right, Left Stick Right]
move_up = [W, D-Pad Up, Left Stick Up]
move_down = [S, D-Pad Down, Left Stick Down]

# 动作
jump = [Space, A Button (Xbox), X Button (PlayStation)]
attack = [Left Mouse, X Button (Xbox), Square (PlayStation)]
special = [Right Mouse, Y Button (Xbox), Triangle (PlayStation)]
dash = [Shift, LB/L1]
interact = [E, B Button (Xbox), Circle (PlayStation)]

# 视角（3D游戏）
look_left = [Right Stick Left]
look_right = [Right Stick Right]
look_up = [Right Stick Up]
look_down = [Right Stick Down]

# 系统
pause = [Escape, Start]
inventory = [Tab, Back/Select]
```

### 按键码速查

| 按键 | Godot 常量 |
|------|------------|
| A-Z | KEY_A - KEY_Z |
| 0-9 | KEY_0 - KEY_9 |
| F1-F12 | KEY_F1 - KEY_F12 |
| 空格 | KEY_SPACE |
| Enter | KEY_ENTER |
| Escape | KEY_ESCAPE |
| Shift | KEY_SHIFT |
| Ctrl | KEY_CTRL |
| Alt | KEY_ALT |
| Tab | KEY_TAB |
| 方向键 | KEY_LEFT/RIGHT/UP/DOWN |

### 手柄按钮

| 按钮 | Xbox | PlayStation | Godot |
|------|------|-------------|-------|
| 南 | A | × | JOY_BUTTON_A |
| 东 | B | ○ | JOY_BUTTON_B |
| 西 | X | □ | JOY_BUTTON_X |
| 北 | Y | △ | JOY_BUTTON_Y |
| LB | LB | L1 | JOY_BUTTON_LEFT_SHOULDER |
| RB | RB | R1 | JOY_BUTTON_RIGHT_SHOULDER |
| LT | LT | L2 | JOY_AXIS_TRIGGER_LEFT |
| RT | RT | R2 | JOY_AXIS_TRIGGER_RIGHT |

---

## 输入管理器

### input_manager.gd (Autoload)

```gdscript
## 输入管理器
##
## 统一处理所有输入，支持输入缓冲、按键重映射
## @author AI Generated
## @version 1.0.0
class_name InputManager
extends Node

# region 信号
signal input_device_changed(device_type: DeviceType)
signal action_pressed(action: String)
signal action_released(action: String)
# endregion

# region 枚举
enum DeviceType { KEYBOARD_MOUSE, CONTROLLER, TOUCH }
# endregion

# region 常量
const INPUT_BUFFER_TIME: float = 0.15
const COMBO_WINDOW: float = 0.3
# endregion

# region 导出变量
@export var vibration_enabled: bool = true
@export var vibration_strength: float = 1.0
# endregion

# region 状态变量
var current_device: DeviceType = DeviceType.KEYBOARD_MOUSE
var _input_buffer: Dictionary = {}  # action -> timestamp
var _combo_buffer: Array = []
var _last_input_time: float = 0.0
# endregion

# region 生命周期
func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS

func _process(delta: float) -> void:
    _clean_expired_buffer()

func _input(event: InputEvent) -> void:
    _detect_device_change(event)
    _buffer_inputs(event)
# endregion

# region 设备检测
func _detect_device_change(event: InputEvent) -> void:
    var new_device = current_device
    
    if event is InputEventKey or event is InputEventMouse:
        new_device = DeviceType.KEYBOARD_MOUSE
    elif event is InputEventJoypadButton or event is InputEventJoypadMotion:
        new_device = DeviceType.CONTROLLER
    elif event is InputEventScreenTouch:
        new_device = DeviceType.TOUCH
    
    if new_device != current_device:
        current_device = new_device
        input_device_changed.emit(current_device)
# endregion

# region 输入缓冲
func _buffer_inputs(event: InputEvent) -> void:
    for action in InputMap.get_actions():
        if event.is_action_pressed(action):
            _input_buffer[action] = Time.get_ticks_msec() / 1000.0
            action_pressed.emit(action)
            _add_to_combo(action)
        elif event.is_action_released(action):
            action_released.emit(action)

func _clean_expired_buffer() -> void:
    var current_time = Time.get_ticks_msec() / 1000.0
    var expired_actions = []
    
    for action in _input_buffer:
        if current_time - _input_buffer[action] > INPUT_BUFFER_TIME:
            expired_actions.append(action)
    
    for action in expired_actions:
        _input_buffer.erase(action)

## 检查动作是否在缓冲时间内被按下（消耗缓冲）
func consume_buffered_action(action: String) -> bool:
    if _input_buffer.has(action):
        _input_buffer.erase(action)
        return true
    return false

## 检查动作是否在缓冲时间内被按下（不消耗）
func is_action_buffered(action: String) -> bool:
    return _input_buffer.has(action)
# endregion

# region 连招系统
func _add_to_combo(action: String) -> void:
    var current_time = Time.get_ticks_msec() / 1000.0
    
    # 超时则清空连招
    if current_time - _last_input_time > COMBO_WINDOW:
        _combo_buffer.clear()
    
    _combo_buffer.append(action)
    _last_input_time = current_time
    
    # 限制缓冲长度
    if _combo_buffer.size() > 10:
        _combo_buffer.pop_front()

## 检查是否匹配连招序列
func check_combo(sequence: Array) -> bool:
    if sequence.size() > _combo_buffer.size():
        return false
    
    var start_index = _combo_buffer.size() - sequence.size()
    for i in range(sequence.size()):
        if _combo_buffer[start_index + i] != sequence[i]:
            return false
    
    return true

## 消耗并清空连招缓冲
func consume_combo() -> void:
    _combo_buffer.clear()

## 获取当前连招序列
func get_combo_sequence() -> Array:
    return _combo_buffer.duplicate()
# endregion

# region 手柄震动
func vibrate(weak_magnitude: float = 0.5, strong_magnitude: float = 0.5, duration: float = 0.2) -> void:
    if not vibration_enabled:
        return
    
    weak_magnitude *= vibration_strength
    strong_magnitude *= vibration_strength
    
    for device_id in Input.get_connected_joypads():
        Input.start_joy_vibration(device_id, weak_magnitude, strong_magnitude, duration)

func stop_vibration() -> void:
    for device_id in Input.get_connected_joypads():
        Input.stop_joy_vibration(device_id)
# endregion

# region 工具方法
## 获取当前设备的动作图标路径
func get_action_icon(action: String) -> String:
    var base_path = "res://assets/textures/ui/input_icons/"
    
    match current_device:
        DeviceType.KEYBOARD_MOUSE:
            return base_path + "keyboard/" + action + ".png"
        DeviceType.CONTROLLER:
            return base_path + "controller/" + action + ".png"
        DeviceType.TOUCH:
            return base_path + "touch/" + action + ".png"
    
    return ""

## 获取移动输入向量
func get_movement_vector() -> Vector2:
    return Input.get_vector("move_left", "move_right", "move_up", "move_down")

## 获取视角输入向量
func get_look_vector() -> Vector2:
    return Input.get_vector("look_left", "look_right", "look_up", "look_down")

## 检查是否有任意移动输入
func has_movement_input() -> bool:
    return get_movement_vector() != Vector2.ZERO

## 获取当前设备类型名称
func get_device_name() -> String:
    match current_device:
        DeviceType.KEYBOARD_MOUSE:
            return "Keyboard & Mouse"
        DeviceType.CONTROLLER:
            return "Controller"
        DeviceType.TOUCH:
            return "Touch"
    return "Unknown"
# endregion

# region 按键重映射
var _custom_mappings: Dictionary = {}

func remap_action(action: String, event: InputEvent) -> void:
    # 清除现有映射
    for existing in InputMap.action_get_events(action):
        InputMap.action_erase_event(action, existing)
    
    # 添加新映射
    InputMap.action_add_event(action, event)
    _custom_mappings[action] = event
    
    _save_custom_mappings()

func reset_to_defaults() -> void:
    # 重新加载默认输入映射
    InputMap.load_from_project_settings()
    _custom_mappings.clear()
    _save_custom_mappings()

func _save_custom_mappings() -> void:
    var config = ConfigFile.new()
    for action in _custom_mappings:
        var event = _custom_mappings[action]
        config.set_value("input", action, var_to_str(event))
    config.save("user://input_config.cfg")

func _load_custom_mappings() -> void:
    var config = ConfigFile.new()
    if config.load("user://input_config.cfg") == OK:
        for action in config.get_section_keys("input"):
            var event = str_to_var(config.get_value("input", action))
            if event:
                remap_action(action, event)
# endregion
```

---

## 高级输入处理

### 输入缓冲器（单独组件）

```gdscript
## 输入缓冲器
##
## 为单个实体提供输入缓冲功能
class_name InputBuffer
extends Node

@export var buffer_time: float = 0.15

var _buffer: Dictionary = {}

func buffer_action(action: String) -> void:
    _buffer[action] = buffer_time

func _process(delta: float) -> void:
    var to_remove = []
    for action in _buffer:
        _buffer[action] -= delta
        if _buffer[action] <= 0:
            to_remove.append(action)
    
    for action in to_remove:
        _buffer.erase(action)

func consume(action: String) -> bool:
    if _buffer.has(action):
        _buffer.erase(action)
        return true
    return false

func is_buffered(action: String) -> bool:
    return _buffer.has(action)

func clear() -> void:
    _buffer.clear()
```

### 连招定义系统

```gdscript
## 连招定义
class_name ComboDefinition
extends Resource

@export var name: String
@export var sequence: Array[String]
@export var time_window: float = 0.3
@export var result_action: String

func matches(input_sequence: Array) -> bool:
    if sequence.size() > input_sequence.size():
        return false
    
    var start = input_sequence.size() - sequence.size()
    for i in range(sequence.size()):
        if input_sequence[start + i] != sequence[i]:
            return false
    
    return true
```

### 连招检测器

```gdscript
## 连招检测器
class_name ComboDetector
extends Node

signal combo_detected(combo_name: String)

@export var combos: Array[ComboDefinition]
@export var input_window: float = 0.3

var _input_history: Array = []
var _last_input_time: float = 0.0

func _ready() -> void:
    InputManager.action_pressed.connect(_on_action_pressed)

func _on_action_pressed(action: String) -> void:
    var current_time = Time.get_ticks_msec() / 1000.0
    
    if current_time - _last_input_time > input_window:
        _input_history.clear()
    
    _input_history.append(action)
    _last_input_time = current_time
    
    # 检查所有连招
    for combo in combos:
        if combo.matches(_input_history):
            combo_detected.emit(combo.name)
            _input_history.clear()
            break
    
    # 限制历史长度
    if _input_history.size() > 20:
        _input_history.pop_front()
```

---

## 触屏输入支持

### 虚拟摇杆

```gdscript
## 虚拟摇杆
class_name VirtualJoystick
extends Control

signal joystick_input(direction: Vector2)

@export var max_distance: float = 50.0
@export var dead_zone: float = 0.2

var _is_pressed: bool = false
var _touch_index: int = -1
var _center: Vector2
var _current_pos: Vector2

@onready var base: TextureRect = $Base
@onready var knob: TextureRect = $Knob

func _ready() -> void:
    _center = size / 2
    knob.position = _center - knob.size / 2

func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        if event.pressed and _is_point_inside(event.position):
            _is_pressed = true
            _touch_index = event.index
            _update_knob(event.position)
        elif not event.pressed and event.index == _touch_index:
            _release()
    
    elif event is InputEventScreenDrag:
        if event.index == _touch_index:
            _update_knob(event.position)

func _is_point_inside(point: Vector2) -> bool:
    var local_point = point - global_position
    return local_point.length() <= size.x / 2

func _update_knob(touch_pos: Vector2) -> void:
    var local_pos = touch_pos - global_position - _center
    var clamped = local_pos.limit_length(max_distance)
    
    knob.position = _center + clamped - knob.size / 2
    
    var direction = clamped / max_distance
    if direction.length() < dead_zone:
        direction = Vector2.ZERO
    
    joystick_input.emit(direction)

func _release() -> void:
    _is_pressed = false
    _touch_index = -1
    knob.position = _center - knob.size / 2
    joystick_input.emit(Vector2.ZERO)
```

### 触屏按钮

```gdscript
## 触屏动作按钮
class_name TouchActionButton
extends TextureButton

@export var action_name: String

func _ready() -> void:
    pressed.connect(_on_pressed)
    button_up.connect(_on_released)

func _on_pressed() -> void:
    Input.action_press(action_name)

func _on_released() -> void:
    Input.action_release(action_name)
```

---

## 输入设置 UI

```gdscript
## 输入设置界面
class_name InputSettingsUI
extends Control

@onready var action_list: VBoxContainer = $ActionList
@onready var rebind_popup: PopupPanel = $RebindPopup

var _current_rebind_action: String = ""

func _ready() -> void:
    _populate_action_list()

func _populate_action_list() -> void:
    for action in InputMap.get_actions():
        if action.begins_with("ui_"):
            continue  # 跳过系统动作
        
        var row = _create_action_row(action)
        action_list.add_child(row)

func _create_action_row(action: String) -> HBoxContainer:
    var row = HBoxContainer.new()
    
    var label = Label.new()
    label.text = action.capitalize().replace("_", " ")
    label.custom_minimum_size.x = 200
    row.add_child(label)
    
    var button = Button.new()
    button.text = _get_action_key_name(action)
    button.pressed.connect(func(): _start_rebind(action))
    row.add_child(button)
    
    return row

func _get_action_key_name(action: String) -> String:
    var events = InputMap.action_get_events(action)
    if events.size() > 0:
        return events[0].as_text()
    return "Unbound"

func _start_rebind(action: String) -> void:
    _current_rebind_action = action
    rebind_popup.popup_centered()

func _input(event: InputEvent) -> void:
    if _current_rebind_action.is_empty():
        return
    
    if event is InputEventKey or event is InputEventJoypadButton:
        InputManager.remap_action(_current_rebind_action, event)
        rebind_popup.hide()
        _current_rebind_action = ""
        _refresh_ui()

func _refresh_ui() -> void:
    for child in action_list.get_children():
        child.queue_free()
    _populate_action_list()
```

---

## 使用示例

### 基本使用

```gdscript
# 在玩家脚本中
func _physics_process(delta: float) -> void:
    var direction = InputManager.get_movement_vector()
    velocity = direction * speed
    
    # 使用输入缓冲处理跳跃
    if InputManager.consume_buffered_action("jump") and is_on_floor():
        velocity.y = jump_velocity
```

### 连招检测

```gdscript
# 设置连招
var hadouken_combo = ComboDefinition.new()
hadouken_combo.name = "hadouken"
hadouken_combo.sequence = ["move_down", "move_down_right", "move_right", "attack"]

# 监听连招
combo_detector.combo_detected.connect(func(name):
    if name == "hadouken":
        perform_hadouken()
)
```
