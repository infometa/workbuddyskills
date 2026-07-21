---
name: save-system
description: >
  存档系统技能。管理游戏进度的保存和加载，支持多存档槽、自动保存、云存档等功能。
version: 1.0.0
dependencies:
  - godot-core
  - file-manager
triggers:
  - pattern: "存档|保存|加载|Save|Load|进度"
inputs:
  - name: save_type
    type: string
    enum: ["simple", "full", "cloud"]
    required: false
outputs:
  - name: save_manager
    type: file
    path_pattern: "res://scripts/autoload/save_manager.gd"
---

# 存档系统技能

管理游戏进度的保存和加载。

## 存档系统架构

```
user://
└── saves/
    ├── settings.cfg        # 全局设置
    ├── slot_1/
    │   ├── save.json       # 主存档数据
    │   ├── screenshot.png  # 存档截图
    │   └── meta.json       # 元数据（时间、游戏时长等）
    ├── slot_2/
    │   └── ...
    ├── slot_3/
    │   └── ...
    └── autosave/
        └── ...
```

---

## 存档管理器

### save_manager.gd (Autoload)

```gdscript
## 存档管理器
##
## 管理游戏数据的保存和加载
## @author AI Generated
## @version 1.0.0
class_name SaveManager
extends Node

# region 信号
signal save_started
signal save_completed(slot: int)
signal save_failed(slot: int, error: String)
signal load_started
signal load_completed(slot: int)
signal load_failed(slot: int, error: String)
signal autosave_triggered
# endregion

# region 常量
const SAVE_DIR = "user://saves/"
const SETTINGS_FILE = "user://saves/settings.cfg"
const MAX_SLOTS = 3
const AUTOSAVE_SLOT = -1
const SAVE_VERSION = "1.0.0"
# endregion

# region 导出变量
@export var autosave_enabled: bool = true
@export var autosave_interval: float = 300.0  # 5分钟
@export var encrypt_saves: bool = false
@export var encryption_password: String = "your_secret_key"
# endregion

# region 状态
var current_slot: int = -1
var game_data: Dictionary = {}
var _autosave_timer: Timer
var _is_saving: bool = false
var _is_loading: bool = false
# endregion

# region 生命周期
func _ready() -> void:
    _ensure_save_directory()
    _setup_autosave_timer()

func _ensure_save_directory() -> void:
    var dir = DirAccess.open("user://")
    if not dir.dir_exists("saves"):
        dir.make_dir("saves")
    
    for i in range(MAX_SLOTS):
        var slot_dir = "saves/slot_%d" % (i + 1)
        if not dir.dir_exists(slot_dir):
            dir.make_dir(slot_dir)
    
    if not dir.dir_exists("saves/autosave"):
        dir.make_dir("saves/autosave")

func _setup_autosave_timer() -> void:
    _autosave_timer = Timer.new()
    _autosave_timer.wait_time = autosave_interval
    _autosave_timer.timeout.connect(_on_autosave_timer)
    add_child(_autosave_timer)
    
    if autosave_enabled:
        _autosave_timer.start()
# endregion

# region 保存
func save_game(slot: int) -> bool:
    if _is_saving:
        return false
    
    _is_saving = true
    save_started.emit()
    
    var slot_path = _get_slot_path(slot)
    
    # 收集所有需要保存的数据
    var save_data = _collect_save_data()
    
    # 添加元数据
    save_data["_meta"] = {
        "version": SAVE_VERSION,
        "timestamp": Time.get_unix_time_from_system(),
        "datetime": Time.get_datetime_string_from_system(),
        "playtime": game_data.get("playtime", 0)
    }
    
    # 保存主数据
    var success = _write_save_file(slot_path + "/save.json", save_data)
    
    if success:
        # 保存元数据
        _write_save_file(slot_path + "/meta.json", save_data["_meta"])
        
        # 保存截图
        _save_screenshot(slot_path + "/screenshot.png")
        
        current_slot = slot
        save_completed.emit(slot)
    else:
        save_failed.emit(slot, "Failed to write save file")
    
    _is_saving = false
    return success

func _collect_save_data() -> Dictionary:
    var data = {}
    
    # 收集基础游戏数据
    data["game_data"] = game_data.duplicate(true)
    
    # 通知所有可保存节点
    get_tree().call_group("saveable", "on_save", data)
    
    return data

func _write_save_file(path: String, data: Dictionary) -> bool:
    var json_string = JSON.stringify(data, "\t")
    
    if encrypt_saves:
        json_string = _encrypt(json_string)
    
    var file = FileAccess.open(path, FileAccess.WRITE)
    if file:
        file.store_string(json_string)
        file.close()
        return true
    
    return false

func _save_screenshot(path: String) -> void:
    # 获取视口截图
    var image = get_viewport().get_texture().get_image()
    image.resize(320, 180)  # 缩略图尺寸
    image.save_png(path)
# endregion

# region 加载
func load_game(slot: int) -> bool:
    if _is_loading:
        return false
    
    _is_loading = true
    load_started.emit()
    
    var slot_path = _get_slot_path(slot)
    var save_data = _read_save_file(slot_path + "/save.json")
    
    if save_data.is_empty():
        load_failed.emit(slot, "Save file not found or corrupted")
        _is_loading = false
        return false
    
    # 版本检查
    var save_version = save_data.get("_meta", {}).get("version", "0.0.0")
    if not _is_version_compatible(save_version):
        load_failed.emit(slot, "Incompatible save version: " + save_version)
        _is_loading = false
        return false
    
    # 恢复游戏数据
    game_data = save_data.get("game_data", {})
    
    # 通知所有可保存节点加载数据
    get_tree().call_group("saveable", "on_load", save_data)
    
    current_slot = slot
    load_completed.emit(slot)
    _is_loading = false
    
    return true

func _read_save_file(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    
    var file = FileAccess.open(path, FileAccess.READ)
    if not file:
        return {}
    
    var content = file.get_as_text()
    file.close()
    
    if encrypt_saves:
        content = _decrypt(content)
    
    var json = JSON.new()
    var error = json.parse(content)
    if error != OK:
        push_error("JSON parse error: " + json.get_error_message())
        return {}
    
    return json.data

func _is_version_compatible(save_version: String) -> bool:
    # 简单的版本兼容性检查
    # 实际项目中可能需要更复杂的迁移逻辑
    var current_parts = SAVE_VERSION.split(".")
    var save_parts = save_version.split(".")
    
    # 主版本号必须相同
    return current_parts[0] == save_parts[0]
# endregion

# region 存档槽管理
func get_slot_info(slot: int) -> Dictionary:
    var slot_path = _get_slot_path(slot)
    var meta_path = slot_path + "/meta.json"
    
    if not FileAccess.file_exists(meta_path):
        return {"empty": true}
    
    var meta = _read_save_file(meta_path)
    meta["empty"] = false
    meta["screenshot_path"] = slot_path + "/screenshot.png"
    
    return meta

func get_all_slots_info() -> Array:
    var slots = []
    for i in range(MAX_SLOTS):
        slots.append(get_slot_info(i + 1))
    return slots

func delete_save(slot: int) -> bool:
    var slot_path = _get_slot_path(slot)
    var dir = DirAccess.open(slot_path)
    
    if not dir:
        return false
    
    # 删除槽内所有文件
    dir.list_dir_begin()
    var file_name = dir.get_next()
    while file_name != "":
        dir.remove(file_name)
        file_name = dir.get_next()
    dir.list_dir_end()
    
    return true

func has_save_data(slot: int = -1) -> bool:
    if slot == -1:
        # 检查是否有任何存档
        for i in range(MAX_SLOTS):
            if not get_slot_info(i + 1).get("empty", true):
                return true
        return false
    
    return not get_slot_info(slot).get("empty", true)

func _get_slot_path(slot: int) -> String:
    if slot == AUTOSAVE_SLOT:
        return SAVE_DIR + "autosave"
    return SAVE_DIR + "slot_%d" % slot
# endregion

# region 自动保存
func _on_autosave_timer() -> void:
    if autosave_enabled and current_slot > 0:
        autosave_triggered.emit()
        save_game(AUTOSAVE_SLOT)

func trigger_autosave() -> void:
    if autosave_enabled:
        save_game(AUTOSAVE_SLOT)

func set_autosave_enabled(enabled: bool) -> void:
    autosave_enabled = enabled
    if enabled:
        _autosave_timer.start()
    else:
        _autosave_timer.stop()
# endregion

# region 加密（简单实现）
func _encrypt(data: String) -> String:
    var bytes = data.to_utf8_buffer()
    var key_bytes = encryption_password.to_utf8_buffer()
    
    for i in range(bytes.size()):
        bytes[i] = bytes[i] ^ key_bytes[i % key_bytes.size()]
    
    return Marshalls.raw_to_base64(bytes)

func _decrypt(data: String) -> String:
    var bytes = Marshalls.base64_to_raw(data)
    var key_bytes = encryption_password.to_utf8_buffer()
    
    for i in range(bytes.size()):
        bytes[i] = bytes[i] ^ key_bytes[i % key_bytes.size()]
    
    return bytes.get_string_from_utf8()
# endregion

# region 快捷方法
func set_value(key: String, value: Variant) -> void:
    game_data[key] = value

func get_value(key: String, default: Variant = null) -> Variant:
    return game_data.get(key, default)

func has_value(key: String) -> bool:
    return game_data.has(key)

func delete_value(key: String) -> void:
    game_data.erase(key)
# endregion
```

---

## 可保存组件

### saveable_component.gd

```gdscript
## 可保存组件
##
## 附加到需要保存/加载数据的节点上
class_name SaveableComponent
extends Node

@export var save_id: String = ""  # 唯一标识符

func _ready() -> void:
    if save_id.is_empty():
        save_id = str(get_path())
    
    add_to_group("saveable")

## 保存数据（由 SaveManager 调用）
func on_save(save_data: Dictionary) -> void:
    var data = _collect_data()
    if not data.is_empty():
        if not save_data.has("components"):
            save_data["components"] = {}
        save_data["components"][save_id] = data

## 加载数据（由 SaveManager 调用）
func on_load(save_data: Dictionary) -> void:
    var components = save_data.get("components", {})
    if components.has(save_id):
        _apply_data(components[save_id])

## 子类重写：收集需要保存的数据
func _collect_data() -> Dictionary:
    return {}

## 子类重写：应用加载的数据
func _apply_data(_data: Dictionary) -> void:
    pass
```

### 示例：玩家可保存组件

```gdscript
## 玩家存档组件
class_name PlayerSaveComponent
extends SaveableComponent

@export var player: CharacterBody2D

func _collect_data() -> Dictionary:
    return {
        "position": {
            "x": player.global_position.x,
            "y": player.global_position.y
        },
        "health": player.current_health,
        "max_health": player.max_health,
        "level": player.level,
        "experience": player.experience
    }

func _apply_data(data: Dictionary) -> void:
    if data.has("position"):
        player.global_position = Vector2(
            data.position.x,
            data.position.y
        )
    
    if data.has("max_health"):
        player.max_health = data.max_health
    
    if data.has("health"):
        player.current_health = data.health
    
    if data.has("level"):
        player.level = data.level
    
    if data.has("experience"):
        player.experience = data.experience
```

### 示例：背包可保存组件

```gdscript
## 背包存档组件
class_name InventorySaveComponent
extends SaveableComponent

func _collect_data() -> Dictionary:
    return {
        "items": InventorySystem.get_all_items(),
        "capacity": InventorySystem.get_capacity()
    }

func _apply_data(data: Dictionary) -> void:
    InventorySystem.load_data(data)
```

---

## 设置管理器

### settings_manager.gd (Autoload)

```gdscript
## 设置管理器
##
## 管理游戏设置（与存档分离）
class_name SettingsManager
extends Node

const SETTINGS_PATH = "user://saves/settings.cfg"

var _settings: Dictionary = {
    # 音频
    "master_volume": 1.0,
    "music_volume": 1.0,
    "sfx_volume": 1.0,
    
    # 视频
    "fullscreen": false,
    "vsync": true,
    "resolution_index": 0,
    
    # 控制
    "sensitivity": 1.0,
    "invert_y": false,
    
    # 游戏
    "language": "auto",
    "subtitles": true,
    "screen_shake": true
}

var _config: ConfigFile

func _ready() -> void:
    _config = ConfigFile.new()
    load_settings()

func load_settings() -> void:
    if _config.load(SETTINGS_PATH) == OK:
        for key in _settings.keys():
            if _config.has_section_key("settings", key):
                _settings[key] = _config.get_value("settings", key)
    
    apply_settings(_settings)

func save_settings() -> void:
    for key in _settings.keys():
        _config.set_value("settings", key, _settings[key])
    
    _config.save(SETTINGS_PATH)

func apply_settings(settings: Dictionary) -> void:
    _settings.merge(settings, true)
    
    # 应用音频设置
    AudioServer.set_bus_volume_db(
        AudioServer.get_bus_index("Master"),
        linear_to_db(_settings.master_volume)
    )
    AudioServer.set_bus_volume_db(
        AudioServer.get_bus_index("Music"),
        linear_to_db(_settings.music_volume)
    )
    AudioServer.set_bus_volume_db(
        AudioServer.get_bus_index("SFX"),
        linear_to_db(_settings.sfx_volume)
    )
    
    # 应用视频设置
    if _settings.fullscreen:
        DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
    else:
        DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
    
    DisplayServer.window_set_vsync_mode(
        DisplayServer.VSYNC_ENABLED if _settings.vsync else DisplayServer.VSYNC_DISABLED
    )

func get_setting(key: String) -> Variant:
    return _settings.get(key)

func set_setting(key: String, value: Variant) -> void:
    _settings[key] = value

func get_all_settings() -> Dictionary:
    return _settings.duplicate()

func reset_to_defaults() -> void:
    _settings = {
        "master_volume": 1.0,
        "music_volume": 1.0,
        "sfx_volume": 1.0,
        "fullscreen": false,
        "vsync": true,
        "resolution_index": 0,
        "sensitivity": 1.0,
        "invert_y": false,
        "language": "auto",
        "subtitles": true,
        "screen_shake": true
    }
    apply_settings(_settings)
    save_settings()
```

---

## 存档 UI 组件

### save_slot_ui.gd

```gdscript
## 存档槽 UI
class_name SaveSlotUI
extends PanelContainer

signal slot_selected(slot: int, action: String)

@export var slot_index: int = 1

@onready var screenshot: TextureRect = $HBox/Screenshot
@onready var info_container: VBoxContainer = $HBox/Info
@onready var datetime_label: Label = $HBox/Info/Datetime
@onready var playtime_label: Label = $HBox/Info/Playtime
@onready var empty_label: Label = $HBox/Info/EmptyLabel
@onready var save_button: Button = $HBox/Buttons/SaveButton
@onready var load_button: Button = $HBox/Buttons/LoadButton
@onready var delete_button: Button = $HBox/Buttons/DeleteButton

var _slot_info: Dictionary = {}

func _ready() -> void:
    save_button.pressed.connect(func(): slot_selected.emit(slot_index, "save"))
    load_button.pressed.connect(func(): slot_selected.emit(slot_index, "load"))
    delete_button.pressed.connect(func(): slot_selected.emit(slot_index, "delete"))
    
    refresh()

func refresh() -> void:
    _slot_info = SaveManager.get_slot_info(slot_index)
    
    if _slot_info.get("empty", true):
        _show_empty_state()
    else:
        _show_filled_state()

func _show_empty_state() -> void:
    screenshot.texture = null
    datetime_label.hide()
    playtime_label.hide()
    empty_label.show()
    empty_label.text = "空存档槽"
    
    load_button.disabled = true
    delete_button.disabled = true

func _show_filled_state() -> void:
    empty_label.hide()
    datetime_label.show()
    playtime_label.show()
    
    datetime_label.text = _slot_info.get("datetime", "Unknown")
    
    var playtime = _slot_info.get("playtime", 0)
    playtime_label.text = "游戏时长: " + _format_playtime(playtime)
    
    # 加载截图
    var screenshot_path = _slot_info.get("screenshot_path", "")
    if FileAccess.file_exists(screenshot_path):
        var image = Image.load_from_file(screenshot_path)
        screenshot.texture = ImageTexture.create_from_image(image)
    
    load_button.disabled = false
    delete_button.disabled = false

func _format_playtime(seconds: int) -> String:
    var hours = seconds / 3600
    var minutes = (seconds % 3600) / 60
    return "%02d:%02d" % [hours, minutes]
```

---

## 使用示例

### 基本使用

```gdscript
# 保存游戏
func _on_save_button_pressed():
    SaveManager.save_game(1)  # 保存到槽 1

# 加载游戏
func _on_load_button_pressed():
    SaveManager.load_game(1)  # 从槽 1 加载

# 存储/读取数据
SaveManager.set_value("player_name", "Hero")
var name = SaveManager.get_value("player_name", "Unknown")

# 检查存档
if SaveManager.has_save_data():
    show_continue_button()
```

### 为节点添加保存功能

```gdscript
# 方式 1：继承 SaveableComponent
class_name ChestSaveComponent
extends SaveableComponent

@export var chest: Node

func _collect_data() -> Dictionary:
    return {"opened": chest.is_opened}

func _apply_data(data: Dictionary) -> void:
    chest.is_opened = data.get("opened", false)
    if chest.is_opened:
        chest.show_opened_state()
```

```gdscript
# 方式 2：直接使用 SaveManager
func _ready():
    add_to_group("saveable")

func on_save(save_data: Dictionary):
    save_data["my_data"] = {"value": 42}

func on_load(save_data: Dictionary):
    var my_data = save_data.get("my_data", {})
    var value = my_data.get("value", 0)
```
