---
name: code-generator
description: >
  代码生成技能。根据模板和需求生成 GDScript 代码，支持自动补全、
  模块化代码生成和代码规范检查。
version: 1.0.0
dependencies:
  - godot-core
  - file-manager
triggers:
  - pattern: "生成代码|创建脚本|写一个|实现.*功能|.*控制器|.*管理器"
inputs:
  - name: template_type
    type: string
    enum: ["singleton", "entity", "component", "state", "ui_controller", "system", "data_class"]
    required: true
  - name: class_name
    type: string
    required: true
  - name: features
    type: array
    required: false
outputs:
  - name: script_path
    type: string
    description: 生成的脚本文件路径
---

# 代码生成技能

根据模板和需求自动生成 GDScript 代码。

## 代码规范

### 命名约定

| 类型 | 命名方式 | 示例 |
|------|----------|------|
| 类名 | PascalCase | `PlayerController`, `GameManager` |
| 函数名 | snake_case | `get_health()`, `apply_damage()` |
| 变量名 | snake_case | `max_health`, `current_speed` |
| 常量 | UPPER_SNAKE_CASE | `MAX_SPEED`, `DEFAULT_HEALTH` |
| 信号 | snake_case | `health_changed`, `died` |
| 枚举 | PascalCase (类型), UPPER_SNAKE_CASE (值) | `enum State { IDLE, RUNNING }` |

### 文件组织

```gdscript
## 类描述（文档注释）
## 
## 详细说明
## @author AI Generated
## @version 1.0.0
class_name ClassName
extends BaseClass

# region 信号
signal signal_name(param: Type)
# endregion

# region 常量
const MAX_VALUE: int = 100
# endregion

# region 导出变量
@export var exported_var: Type
@export_group("Group Name")
@export var grouped_var: Type
# endregion

# region 公共变量
var public_var: Type
# endregion

# region 私有变量
var _private_var: Type
# endregion

# region 生命周期方法
func _ready() -> void:
    pass

func _process(delta: float) -> void:
    pass

func _physics_process(delta: float) -> void:
    pass
# endregion

# region 公共方法
func public_method() -> ReturnType:
    pass
# endregion

# region 私有方法
func _private_method() -> void:
    pass
# endregion
```

---

## 模板类型

### 1. 单例模板 (Singleton)

用于全局管理器，如 GameManager、AudioManager 等。

```gdscript
## {{CLASS_DESCRIPTION}}
##
## 全局单例，通过 Autoload 加载
## @author AI Generated
## @version {{VERSION}}
class_name {{CLASS_NAME}}
extends Node

# region 信号
{{SIGNALS}}
# endregion

# region 常量
{{CONSTANTS}}
# endregion

# region 私有变量
{{PRIVATE_VARS}}
# endregion

# region 生命周期
func _ready() -> void:
    _initialize()

func _initialize() -> void:
    {{INIT_CONTENT}}
# endregion

# region 公共 API
{{PUBLIC_METHODS}}
# endregion

# region 内部方法
{{PRIVATE_METHODS}}
# endregion
```

**使用示例**：
```
生成一个 AudioManager 单例，支持播放背景音乐和音效，支持音量控制
```

### 2. 实体模板 (Entity)

用于游戏实体，如 Player、Enemy 等。

```gdscript
## {{CLASS_DESCRIPTION}}
##
## @author AI Generated
## @version {{VERSION}}
class_name {{CLASS_NAME}}
extends {{BASE_CLASS}}

# region 信号
signal died
signal health_changed(old_value: int, new_value: int)
{{ADDITIONAL_SIGNALS}}
# endregion

# region 导出变量
@export_group("Stats")
@export var max_health: int = 100
@export var move_speed: float = 200.0
{{ADDITIONAL_EXPORTS}}
# endregion

# region 状态变量
var current_health: int:
    set(value):
        var old = current_health
        current_health = clampi(value, 0, max_health)
        health_changed.emit(old, current_health)
        if current_health <= 0:
            _die()
    get:
        return current_health

var is_alive: bool:
    get: return current_health > 0
{{ADDITIONAL_STATE}}
# endregion

# region 组件引用
{{COMPONENT_REFS}}
# endregion

# region 生命周期
func _ready() -> void:
    _setup_components()
    _initialize()

func _physics_process(delta: float) -> void:
    if not is_alive:
        return
    {{PHYSICS_CONTENT}}
# endregion

# region 公共方法
func take_damage(amount: int, source: Node = null) -> void:
    if not is_alive:
        return
    current_health -= amount

func heal(amount: int) -> void:
    if not is_alive:
        return
    current_health += amount
{{ADDITIONAL_PUBLIC}}
# endregion

# region 私有方法
func _setup_components() -> void:
    {{SETUP_COMPONENTS}}

func _initialize() -> void:
    current_health = max_health
    {{INIT_CONTENT}}

func _die() -> void:
    died.emit()
    {{DIE_CONTENT}}
{{ADDITIONAL_PRIVATE}}
# endregion
```

### 3. 组件模板 (Component)

用于可复用的功能组件。

```gdscript
## {{CLASS_DESCRIPTION}}
##
## 组件模式：附加到实体节点上提供特定功能
## @author AI Generated
## @version {{VERSION}}
class_name {{CLASS_NAME}}
extends Node

# region 信号
{{SIGNALS}}
# endregion

# region 导出变量
@export var enabled: bool = true
{{EXPORTS}}
# endregion

# region 私有变量
var _owner_entity: Node
{{PRIVATE_VARS}}
# endregion

# region 生命周期
func _ready() -> void:
    _owner_entity = get_parent()
    if not _owner_entity:
        push_error("{{CLASS_NAME}} must be a child of an entity node")
        return
    _initialize()

func _process(delta: float) -> void:
    if not enabled:
        return
    {{PROCESS_CONTENT}}
# endregion

# region 公共方法
{{PUBLIC_METHODS}}
# endregion

# region 私有方法
func _initialize() -> void:
    {{INIT_CONTENT}}
{{PRIVATE_METHODS}}
# endregion
```

### 4. 状态机状态模板 (State)

用于状态机中的各个状态。

```gdscript
## {{STATE_DESCRIPTION}}
##
## 状态机状态
## @author AI Generated
## @version {{VERSION}}
class_name {{CLASS_NAME}}
extends State

# region 导出变量
{{EXPORTS}}
# endregion

# region 状态生命周期
func enter() -> void:
    {{ENTER_CONTENT}}

func exit() -> void:
    {{EXIT_CONTENT}}

func update(delta: float) -> void:
    {{UPDATE_CONTENT}}

func physics_update(delta: float) -> void:
    {{PHYSICS_UPDATE_CONTENT}}
# endregion

# region 输入处理
func handle_input(event: InputEvent) -> void:
    {{INPUT_CONTENT}}
# endregion

# region 状态转换检查
func get_transition() -> StringName:
    {{TRANSITION_CHECKS}}
    return &""
# endregion
```

### 5. UI 控制器模板 (UI Controller)

用于 UI 界面控制。

```gdscript
## {{CLASS_DESCRIPTION}}
##
## UI 控制器
## @author AI Generated
## @version {{VERSION}}
class_name {{CLASS_NAME}}
extends Control

# region 信号
signal opened
signal closed
{{ADDITIONAL_SIGNALS}}
# endregion

# region 节点引用
{{NODE_REFS}}
# endregion

# region 生命周期
func _ready() -> void:
    _setup_ui()
    _connect_signals()

func _setup_ui() -> void:
    {{SETUP_UI}}

func _connect_signals() -> void:
    {{CONNECT_SIGNALS}}
# endregion

# region 公共方法
func open() -> void:
    show()
    opened.emit()
    {{OPEN_CONTENT}}

func close() -> void:
    hide()
    closed.emit()
    {{CLOSE_CONTENT}}

func refresh() -> void:
    {{REFRESH_CONTENT}}
# endregion

# region 事件处理
{{EVENT_HANDLERS}}
# endregion

# region 数据绑定
{{DATA_BINDING}}
# endregion
```

### 6. 系统模板 (System)

用于游戏系统，如战斗系统、背包系统等。

```gdscript
## {{CLASS_DESCRIPTION}}
##
## 游戏系统
## @author AI Generated
## @version {{VERSION}}
class_name {{CLASS_NAME}}
extends Node

# region 信号
{{SIGNALS}}
# endregion

# region 常量
{{CONSTANTS}}
# endregion

# region 数据存储
{{DATA_STORAGE}}
# endregion

# region 生命周期
func _ready() -> void:
    _load_config()
    _initialize()

func _load_config() -> void:
    {{LOAD_CONFIG}}

func _initialize() -> void:
    {{INIT_CONTENT}}
# endregion

# region 公共 API
{{PUBLIC_API}}
# endregion

# region 内部逻辑
{{INTERNAL_LOGIC}}
# endregion

# region 事件处理
{{EVENT_HANDLERS}}
# endregion

# region 数据持久化
func save_data() -> Dictionary:
    {{SAVE_DATA}}
    return {}

func load_data(data: Dictionary) -> void:
    {{LOAD_DATA}}
# endregion
```

### 7. 数据类模板 (Data Class)

用于定义数据结构。

```gdscript
## {{CLASS_DESCRIPTION}}
##
## 数据类定义
## @author AI Generated
## @version {{VERSION}}
class_name {{CLASS_NAME}}
extends Resource

# region 导出属性
{{PROPERTIES}}
# endregion

# region 构造函数
func _init({{INIT_PARAMS}}) -> void:
    {{INIT_BODY}}
# endregion

# region 序列化
func to_dict() -> Dictionary:
    return {
        {{TO_DICT_BODY}}
    }

static func from_dict(data: Dictionary) -> {{CLASS_NAME}}:
    var instance = {{CLASS_NAME}}.new()
    {{FROM_DICT_BODY}}
    return instance
# endregion

# region 验证
func is_valid() -> bool:
    {{VALIDATION}}
    return true
# endregion
```

---

## 模板变量说明

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{CLASS_NAME}}` | 类名 | `PlayerController` |
| `{{CLASS_DESCRIPTION}}` | 类描述 | `玩家控制器，处理输入和移动` |
| `{{BASE_CLASS}}` | 基类 | `CharacterBody2D` |
| `{{VERSION}}` | 版本号 | `1.0.0` |
| `{{SIGNALS}}` | 信号定义 | `signal attacked(target)` |
| `{{EXPORTS}}` | 导出变量 | `@export var speed: float = 100.0` |
| `{{PRIVATE_VARS}}` | 私有变量 | `var _velocity: Vector2` |
| `{{PUBLIC_METHODS}}` | 公共方法 | - |
| `{{PRIVATE_METHODS}}` | 私有方法 | - |

---

## 生成示例

### 请求
```
生成一个 InventorySystem 系统，支持：
- 物品添加/移除
- 物品堆叠
- 背包容量限制
- 物品使用
- 数据保存/加载
```

### 生成结果

```gdscript
## 背包系统
##
## 管理玩家物品的存储、使用和持久化
## @author AI Generated
## @version 1.0.0
class_name InventorySystem
extends Node

# region 信号
signal item_added(item_id: String, amount: int)
signal item_removed(item_id: String, amount: int)
signal item_used(item_id: String)
signal inventory_full
signal inventory_changed
# endregion

# region 常量
const DEFAULT_CAPACITY: int = 20
# endregion

# region 数据存储
var _items: Dictionary = {}  # item_id -> amount
var _capacity: int = DEFAULT_CAPACITY
var _item_database: Dictionary = {}  # 物品配置缓存
# endregion

# region 生命周期
func _ready() -> void:
    _load_config()
    _initialize()

func _load_config() -> void:
    var config_path = "res://config/data/items.json"
    if FileAccess.file_exists(config_path):
        var file = FileAccess.open(config_path, FileAccess.READ)
        var json = JSON.new()
        if json.parse(file.get_as_text()) == OK:
            for item in json.data:
                _item_database[item.id] = item
        file.close()

func _initialize() -> void:
    _items.clear()
# endregion

# region 公共 API
func add_item(item_id: String, amount: int = 1) -> bool:
    if not _item_database.has(item_id):
        push_error("Unknown item: " + item_id)
        return false
    
    var item_config = _item_database[item_id]
    var current = _items.get(item_id, 0)
    var max_stack = item_config.get("max_stack", 99)
    
    if not item_config.get("stackable", true) and current > 0:
        if get_total_slots_used() >= _capacity:
            inventory_full.emit()
            return false
    
    var new_amount = mini(current + amount, max_stack)
    var added = new_amount - current
    
    if added > 0:
        _items[item_id] = new_amount
        item_added.emit(item_id, added)
        inventory_changed.emit()
        return true
    
    return false

func remove_item(item_id: String, amount: int = 1) -> bool:
    if not _items.has(item_id):
        return false
    
    var current = _items[item_id]
    var new_amount = current - amount
    
    if new_amount <= 0:
        _items.erase(item_id)
    else:
        _items[item_id] = new_amount
    
    item_removed.emit(item_id, mini(amount, current))
    inventory_changed.emit()
    return true

func use_item(item_id: String) -> bool:
    if not has_item(item_id):
        return false
    
    var item_config = _item_database.get(item_id)
    if not item_config:
        return false
    
    # 执行物品效果
    _apply_item_effects(item_config)
    
    # 消耗品则移除
    if item_config.get("type") == "consumable":
        remove_item(item_id, 1)
    
    item_used.emit(item_id)
    return true

func has_item(item_id: String, amount: int = 1) -> bool:
    return _items.get(item_id, 0) >= amount

func get_item_amount(item_id: String) -> int:
    return _items.get(item_id, 0)

func get_all_items() -> Dictionary:
    return _items.duplicate()

func get_total_slots_used() -> int:
    return _items.size()

func get_capacity() -> int:
    return _capacity

func set_capacity(new_capacity: int) -> void:
    _capacity = new_capacity
# endregion

# region 内部逻辑
func _apply_item_effects(item_config: Dictionary) -> void:
    var effects = item_config.get("effects", [])
    for effect in effects:
        match effect.type:
            "heal_hp":
                EventBus.emit_signal("heal_player", effect.value)
            "heal_mp":
                EventBus.emit_signal("restore_mp", effect.value)
            "buff":
                EventBus.emit_signal("apply_buff", effect.buff_id, effect.duration)
# endregion

# region 数据持久化
func save_data() -> Dictionary:
    return {
        "items": _items.duplicate(),
        "capacity": _capacity
    }

func load_data(data: Dictionary) -> void:
    _items = data.get("items", {}).duplicate()
    _capacity = data.get("capacity", DEFAULT_CAPACITY)
    inventory_changed.emit()
# endregion
```

---

## 代码质量检查

生成代码后自动检查：

1. **语法正确性**：通过 Godot 解析器验证
2. **类型完整性**：所有变量和函数都有类型标注
3. **命名规范**：符合 GDScript 命名约定
4. **文档完整性**：有类描述和关键方法注释
5. **信号连接**：检查信号是否正确定义和使用
