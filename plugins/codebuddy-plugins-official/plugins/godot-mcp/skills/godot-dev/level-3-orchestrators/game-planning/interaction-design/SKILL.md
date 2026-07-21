---
name: interaction-design
description: >
  交互模式策划技能。生成输入映射、输入增强、反馈系统、UI导航等交互设计文档，
  并提供对应的 GDScript 代码模板。
version: 2.0.0
dependencies:
  - game-dev-workflow
  - file-manager
triggers:
  - pattern: "交互设计|输入设计|操控|反馈"
inputs:
  - name: game_type
    type: string
    required: true
  - name: modules
    type: array
    description: "需要的交互模块，按需选取"
    items:
      enum: ["input_mapping", "input_buffer", "coyote_time", "screen_shake", "feedback", "ui_navigation"]
    required: false
outputs:
  - name: interaction_design
    type: file
    path_pattern: "docs/planning/interaction_design.md"
---

# 交互模式策划

## 输出模板

```markdown
# {游戏名称} - 交互设计

## 1. 输入映射

| 动作 | 键盘 | 手柄 | 描述 |
|------|------|------|------|
| move | WASD/方向键 | 左摇杆 | 移动 |
| jump | Space | A | 跳跃 |
| attack | J/左键 | X | 攻击 |
| dash | Shift | B | 闪避 |
| interact | E | A | 交互 |
| pause | Esc | Start | 暂停 |

## 2. 输入增强

### 输入缓冲
- 缓冲时间: 0.1秒
- 适用: 跳跃、攻击、闪避

### 浮空时间 (Coyote Time)
- 时间: 0.08-0.12秒
- 离开平台后仍可跳跃

## 3. 反馈系统

| 事件 | 视觉 | 音效 | 震动 |
|------|------|------|------|
| 受伤 | 红闪+闪白 | 受击音 | 中 |
| 攻击命中 | 顿帧+数字 | 打击音 | 轻 |
| 死亡 | 变灰+慢放 | 死亡音 | 强 |

### 屏幕震动
- 轻击: 3px, 0.1s
- 重击: 8px, 0.3s
- 爆炸: 10px, 0.5s

## 4. UI导航

- 方向键/摇杆: 切换焦点
- 确认: Enter/A
- 取消: Esc/B
- 始终有焦点指示
```

---

## 代码模板

```gdscript
## 输入管理器
class_name InputManager
extends Node

const BUFFER_TIME := 0.1
const COYOTE_TIME := 0.1

var _buffers: Dictionary = {}
var _coyote: Dictionary = {}

func is_buffered(action: String) -> bool:
    return _buffers.get(action, 0.0) > 0.0

func consume_buffer(action: String) -> bool:
    if is_buffered(action):
        _buffers[action] = 0.0
        return true
    return false

func start_coyote(action: String) -> void:
    _coyote[action] = COYOTE_TIME

func in_coyote(action: String) -> bool:
    return _coyote.get(action, 0.0) > 0.0

func _process(delta: float) -> void:
    for key in _buffers:
        _buffers[key] = max(0, _buffers[key] - delta)
    for key in _coyote:
        _coyote[key] = max(0, _coyote[key] - delta)

func _input(event: InputEvent) -> void:
    for action in ["jump", "attack", "dash"]:
        if event.is_action_pressed(action):
            _buffers[action] = BUFFER_TIME
```

```gdscript
## 屏幕震动
class_name ScreenShake
extends Node

var _camera: Camera2D
var _trauma := 0.0

@export var max_offset := Vector2(10, 8)
@export var decay := 1.0

func shake(amount: float) -> void:
    _trauma = min(_trauma + amount, 1.0)

func _process(delta: float) -> void:
    if _camera and _trauma > 0:
        var shake = _trauma * _trauma
        _camera.offset = Vector2(
            randf_range(-1, 1) * max_offset.x * shake,
            randf_range(-1, 1) * max_offset.y * shake
        )
        _trauma = max(0, _trauma - decay * delta)
```
