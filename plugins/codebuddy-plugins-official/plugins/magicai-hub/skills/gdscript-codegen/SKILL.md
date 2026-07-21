---
name: gdscript-codegen
description: AI 生成高质量 GDScript 代码的规范和模板。当用户要求生成、修改或审查 GDScript 代码时使用此 Skill。涵盖 Godot 4.x 类型系统、信号声明、导出变量、代码模板和最佳实践。
version: 1.0.1
---

# GDScript 代码生成 Skill

> **用途**：AI 生成高质量 GDScript 代码的规范和模板  
> **版本**：v1.0 · 2026-04-22  
> **适用引擎**：Godot 4.5/4.6

---

## 一、GDScript 4.x 核心规范

### 1.1 类型系统

Godot 4.x 使用强类型 GDScript，AI 生成代码时必须遵循：

```gdscript
# ✅ 推荐：显式类型标注
var health: int = 100
var speed: float = 10.0
var player_name: String = "Player"
var position: Vector3 = Vector3.ZERO
var enemies: Array[Node3D] = []
var weapon_data: Dictionary = {}

# ✅ 推荐：函数参数和返回值标注
func take_damage(amount: int) -> void:
    health -= amount

func get_health_ratio() -> float:
    return float(health) / float(max_health)

# ❌ 避免：无类型标注（编译器警告）
var health = 100  # 类型推断，但不推荐
```

### 1.2 类型推断陷阱

```gdscript
# ❌ 错误：for 循环迭代变量无法推断
for x in [-1.0, 1.0]:
    var pos := center + Vector2(x, 0) * radius  # 报错！

# ✅ 正确：显式标注迭代变量
for x: float in [-1.0, 1.0]:
    var pos := center + Vector2(x, 0) * radius

# ❌ 错误：字典值类型无法推断
var data = {"a": 1, "b": 2}
var value := data["a"]  # 报错！

# ✅ 正确：显式标注或使用 as
var value: int = data["a"]
var value := data["a"] as int
```

### 1.3 信号声明

```gdscript
# Godot 4.x 信号语法
signal health_changed(current: int, maximum: int)
signal died
signal damage_taken(amount: int, remaining: int)
signal weapon_changed(weapon_index: int)
```

### 1.4 导出变量

```gdscript
# 基础类型
@export var health: int = 100
@export var speed: float = 10.0

# 范围限制
@export_range(0, 100, 1) var health: int = 100
@export_range(0.0, 10.0, 0.1) var speed: float = 5.0

# 枚举
@export_enum("Easy", "Normal", "Hard") var difficulty: int = 1

# 资源
@export var weapon_resource: WeaponResource
@export var projectile_scene: PackedScene

# 分组
@export_group("Combat")
@export var damage: int = 10
@export var fire_rate: float = 0.5
```

### 1.5 @onready 和节点引用

```gdscript
# ✅ 推荐：@onready 延迟初始化
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var health_bar: ProgressBar = $UI/HealthBar

# ✅ 推荐：运行时获取（更灵活）
var player: Node3D
func _ready() -> void:
    player = get_tree().get_first_node_in_group("player")

# ❌ 避免：硬编码路径（易断裂）
var health_label = $"../UI/GameHUD/HealthPanel/HealthLabel"
```

---

## 二、常用代码模板

### 2.1 组件脚本模板

```gdscript
# health_component.gd
extends Node
class_name HealthComponent

## 生命值组件 - 可挂载到任何需要 HP 的实体

signal health_changed(current: int, maximum: int)
signal died
signal damage_taken(amount: int, remaining: int)

@export var max_health: int = 100
@export var invincible: bool = false
@export var invincible_time: float = 0.0

var current_health: int
var is_dead: bool = false
var _invincible_timer: float = 0.0

func _ready() -> void:
    current_health = max_health

func take_damage(amount: int) -> void:
    if is_dead or invincible:
        return
    if _invincible_timer > 0:
        return
    
    current_health = max(0, current_health - amount)
    damage_taken.emit(amount, current_health)
    health_changed.emit(current_health, max_health)
    
    if current_health <= 0:
        is_dead = true
        died.emit()

func heal(amount: int) -> void:
    if is_dead:
        return
    current_health = min(max_health, current_health + amount)
    health_changed.emit(current_health, max_health)
```

### 2.2 Manager 脚本模板

```gdscript
# arena_manager.gd
extends Node
class_name ArenaManager

## 竞技场管理器 - 处理限时刷分模式的核心逻辑

signal arena_started
signal arena_ended(final_score: int, rating: String)
signal score_changed(score: int, combo: int)
signal time_changed(remaining: float)

@export var match_duration: float = 60.0
@export var combo_window: float = 3.0

var _score: int = 0
var _combo: int = 0
var _time_remaining: float = 0.0
var _is_active: bool = false

func _ready() -> void:
    set_process(false)

func start_arena() -> void:
    _score = 0
    _combo = 0
    _time_remaining = match_duration
    _is_active = true
    set_process(true)
    arena_started.emit()
```

---

## 三、信号连接规范

```gdscript
# 方法引用（推荐）
button.pressed.connect(_on_button_pressed)

# Lambda（简单逻辑）
timer.timeout.connect(func(): print("Timeout!"))

# 带参数绑定
enemy.died.connect(_on_enemy_died.bind(spawn_point, enemy))

# 一次性连接
button.pressed.connect(_on_one_time_press, CONNECT_ONE_SHOT)
```

---

## 四、代码生成检查清单

AI 生成 GDScript 代码后，检查以下项目：

### 语法检查
- [ ] 所有变量有类型标注
- [ ] for 循环迭代变量有类型标注
- [ ] 函数参数和返回值有类型标注
- [ ] 信号声明格式正确
- [ ] 缩进使用 Tab（不是空格）

### 最佳实践检查
- [ ] 避免硬编码节点路径
- [ ] 使用 @onready 或 _ready() 获取节点
- [ ] 信号连接有错误处理
- [ ] 资源加载有空值检查

### 命名规范检查
- [ ] 类名 PascalCase
- [ ] 变量名 snake_case
- [ ] 私有变量 _snake_case
- [ ] 常量 UPPER_SNAKE_CASE
- [ ] 信号名 snake_case

---

## 五、编辑器警告规避（真实踩过的坑，避免打扰用户）

这一节列的都是 Godot 4 **编辑器错误面板里最常见**、并且**生成式 AI 最容易犯**的警告。每条都给出修复模式，生成代码时直接避开。

### 5.1 变量名与 built-in function 重名

```gdscript
# ❌ 警告：The variable "hash" has the same name as a built-in function.
var hash := _hash_cell(x, z)

# ✅ 改名避开
var cell_hash := _hash_cell(x, z)
# 或在辅助函数内部用 1 字母短名
var h := _hash_u32(seed)
```

**触发名单**（非完全列表）：`hash`、`len`、`str`、`int`、`float`、`bool`、
`print`、`abs`、`sin`、`cos`、`min`、`max`、`clamp`、`lerp`、`sign`、
`type_of`、`range`、`load`、`preload`。生成代码前，**避免用 GDScript
全局函数名做局部变量名**。

### 5.2 局部变量 shadow 基类属性

```gdscript
# ❌ 警告：The local variable "basis" is shadowing an already-declared
#          property in the base class "Node3D".
var basis := Basis(Vector3.UP, yaw)

# ✅ 改名
var cell_basis := Basis(Vector3.UP, yaw)
```

**`Node3D` 高风险属性**：`transform`、`basis`、`position`、`rotation`、
`scale`、`global_transform`、`global_position`、`global_basis`。
**`CanvasItem` 高风险**：`visible`、`modulate`、`material`。
**`Node` 高风险**：`name`、`owner`、`tree`。

生成挂在 Node 继承树上的脚本时，**不要用这些名字做局部变量**。

### 5.3 函数参数未使用

```gdscript
# ❌ 警告：The parameter "threshold" is never used in the function ...
func compute(value: float, threshold: float) -> float:
    return value * 2.0

# ✅ 接口必须保留该参数（callback / signal / polymorphism）时加下划线
func compute(value: float, _threshold: float) -> float:
    return value * 2.0

# ✅ 如果不需要保留签名，直接删掉参数
func compute(value: float) -> float:
    return value * 2.0
```

**判断原则**：
- 参数是为了匹配 signal 签名 / callback 接口 / 多态重载 → 加 `_` 前缀
- 参数确实是历史残留、没人调用指定它 → 删掉

### 5.4 整数除法警告

```gdscript
# ❌ 警告：Integer division. Decimal part will be discarded.
var x_groups := int((size.x - 1) / 8) + 1

# ✅ 选项 A：如果这就是故意的（如 GPU dispatch 组数、tile index 计算）
@warning_ignore("integer_division")
var x_groups := int((size.x - 1) / 8) + 1

# ✅ 选项 B：如果其实想要浮点结果
var x_groups_f := (size.x - 1) / 8.0

# ✅ 选项 C：显式用 @GlobalScope 的 int div 语义更清晰
var x_groups := ((size.x - 1) / 8) + 1  # 全 int 操作数，结果也是 int
```

**判断原则**：除数 / 被除数任一方是 float **则永远不报** ——
`1.0 / 3.0` 安全；`1 / 3` 报警告。

### 5.5 赋值未使用

```gdscript
# ❌ 警告：The value of "result" is never used.
var result := compute()
return

# ✅ 不关心返回值就别赋
compute()
return
```

### 5.6 未使用的 signal

```gdscript
# ❌ 警告：The signal "health_changed" is declared but never used.
signal health_changed(hp: int)

# 生成时：只声明你真正会 emit 的 signal。若是占位留给将来，加注释 +
# @warning_ignore
@warning_ignore("unused_signal")
signal health_changed(hp: int)  # TODO(v2): emit after HP system lands
```

### 5.7 `@warning_ignore` 使用守则

只在**三种情况**使用，别当万灵药：

1. **故意如此**（整数除法 / shadow 是有意的 API 对齐）
2. **接口约束**（签名必须保留某个参数）
3. **待办占位**（signal/field 下个版本才接）

**禁止**：用 `@warning_ignore` 来"压住一个自己没搞清楚的警告"。警告是
Godot 在告诉你某处有 bug 风险 —— 先理解，再决定豁免。

### 5.8 生成前自检清单

AI 在输出 GDScript 前**务必**过一遍：

- [ ] 没有 `var hash / var len / var str / var range / var load / var print` 等重名
- [ ] 如果 `extends Node3D` → 没有 `var basis / var transform / var position / var rotation / var scale`
- [ ] 如果 `extends CanvasItem` / `Control` → 没有 `var visible / var modulate / var material`
- [ ] 函数参数全部有用；接口参数加 `_` 前缀
- [ ] `int / int` 表达式：显式 `@warning_ignore("integer_division")` 或改成 `float`
- [ ] signal 全部会 `emit()`，或显式标记占位
- [ ] 没有"写着玩"的 `var result = foo()` 却不用 result
