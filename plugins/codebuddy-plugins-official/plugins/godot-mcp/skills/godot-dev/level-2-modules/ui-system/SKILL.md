---
name: ui-system
description: >
  UI 系统技能。生成游戏 UI 组件，包括 HUD、菜单、对话框等。
  支持响应式布局和主题系统。
version: 1.0.0
dependencies:
  - godot-core
  - code-generator
triggers:
  - pattern: "UI|界面|菜单|HUD|对话框|血条|按钮"
inputs:
  - name: ui_type
    type: string
    enum: ["hud", "main_menu", "pause_menu", "settings_menu", "inventory_ui", "dialogue_ui", "shop_ui"]
    required: true
outputs:
  - name: ui_scene
    type: file
    path_pattern: "res://scenes/ui/{type}.tscn"
  - name: ui_script
    type: file
    path_pattern: "res://scripts/ui/{type}.gd"
---

# UI 系统技能

生成游戏 UI 组件和界面。

## UI 架构

```
UI (CanvasLayer)
├── HUD (Control) - 游戏中始终显示
│   ├── HealthBar
│   ├── ManaBar
│   ├── Minimap
│   └── QuickSlots
│
├── Menus (Control) - 菜单层
│   ├── MainMenu
│   ├── PauseMenu
│   ├── SettingsMenu
│   └── ...
│
├── Popups (Control) - 弹窗层
│   ├── ConfirmDialog
│   ├── ItemPopup
│   └── ...
│
└── Overlay (Control) - 最上层
    ├── LoadingScreen
    ├── FadeTransition
    └── Notifications
```

---

## UI 管理器

### ui_manager.gd (Autoload)

```gdscript
## UI 管理器
##
## 统一管理所有 UI 界面的显示和隐藏
## @author AI Generated
## @version 1.0.0
class_name UIManager
extends CanvasLayer

# region 信号
signal menu_opened(menu_name: String)
signal menu_closed(menu_name: String)
signal ui_blocked  # UI 阻止游戏输入
signal ui_unblocked
# endregion

# region 节点引用
@onready var hud: Control = $HUD
@onready var menus: Control = $Menus
@onready var popups: Control = $Popups
@onready var overlay: Control = $Overlay
# endregion

# region 状态
var _menu_stack: Array[Control] = []
var _is_ui_blocking: bool = false
# endregion

# region 生命周期
func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _hide_all_menus()

func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_pressed("pause") and not _is_transition_active():
        if _menu_stack.is_empty():
            open_menu("PauseMenu")
        else:
            close_current_menu()
# endregion

# region 菜单管理
func open_menu(menu_name: String, data: Dictionary = {}) -> Control:
    var menu = menus.get_node_or_null(menu_name)
    if not menu:
        push_error("Menu not found: " + menu_name)
        return null
    
    # 隐藏当前菜单（如果有）
    if not _menu_stack.is_empty():
        _menu_stack.back().hide()
    
    # 显示新菜单
    menu.show()
    _menu_stack.append(menu)
    
    # 调用菜单的 open 方法（如果存在）
    if menu.has_method("open"):
        menu.open(data)
    
    _update_blocking_state()
    menu_opened.emit(menu_name)
    
    return menu

func close_current_menu() -> void:
    if _menu_stack.is_empty():
        return
    
    var menu = _menu_stack.pop_back()
    
    # 调用菜单的 close 方法（如果存在）
    if menu.has_method("close"):
        menu.close()
    else:
        menu.hide()
    
    menu_closed.emit(menu.name)
    
    # 显示上一个菜单（如果有）
    if not _menu_stack.is_empty():
        _menu_stack.back().show()
    
    _update_blocking_state()

func close_all_menus() -> void:
    while not _menu_stack.is_empty():
        close_current_menu()

func _hide_all_menus() -> void:
    for child in menus.get_children():
        child.hide()
    _menu_stack.clear()

func _update_blocking_state() -> void:
    var was_blocking = _is_ui_blocking
    _is_ui_blocking = not _menu_stack.is_empty()
    
    if _is_ui_blocking != was_blocking:
        if _is_ui_blocking:
            get_tree().paused = true
            ui_blocked.emit()
        else:
            get_tree().paused = false
            ui_unblocked.emit()

func is_menu_open() -> bool:
    return not _menu_stack.is_empty()

func get_current_menu() -> Control:
    if _menu_stack.is_empty():
        return null
    return _menu_stack.back()
# endregion

# region 弹窗管理
func show_popup(popup_name: String, data: Dictionary = {}) -> Control:
    var popup = popups.get_node_or_null(popup_name)
    if popup and popup.has_method("show_popup"):
        popup.show_popup(data)
    elif popup:
        popup.show()
    return popup

func show_confirm_dialog(title: String, message: String, on_confirm: Callable, on_cancel: Callable = Callable()) -> void:
    var dialog = popups.get_node_or_null("ConfirmDialog")
    if dialog and dialog.has_method("show_dialog"):
        dialog.show_dialog(title, message, on_confirm, on_cancel)

func show_notification(message: String, duration: float = 3.0) -> void:
    var notif = overlay.get_node_or_null("NotificationManager")
    if notif and notif.has_method("show_notification"):
        notif.show_notification(message, duration)
# endregion

# region 过渡效果
var _transition_active: bool = false

func fade_to_black(duration: float = 0.5) -> void:
    _transition_active = true
    var fade = overlay.get_node_or_null("FadeTransition")
    if fade:
        var tween = create_tween()
        tween.tween_property(fade, "modulate:a", 1.0, duration)
        await tween.finished
    _transition_active = false

func fade_from_black(duration: float = 0.5) -> void:
    _transition_active = true
    var fade = overlay.get_node_or_null("FadeTransition")
    if fade:
        var tween = create_tween()
        tween.tween_property(fade, "modulate:a", 0.0, duration)
        await tween.finished
    _transition_active = false

func _is_transition_active() -> bool:
    return _transition_active
# endregion

# region HUD 控制
func show_hud() -> void:
    hud.show()

func hide_hud() -> void:
    hud.hide()

func update_health(current: int, max_value: int) -> void:
    var health_bar = hud.get_node_or_null("HealthBar")
    if health_bar and health_bar.has_method("update_value"):
        health_bar.update_value(current, max_value)

func update_mana(current: int, max_value: int) -> void:
    var mana_bar = hud.get_node_or_null("ManaBar")
    if mana_bar and mana_bar.has_method("update_value"):
        mana_bar.update_value(current, max_value)
# endregion
```

---

## HUD 组件

### 血条组件 (health_bar.gd)

```gdscript
## 血条 UI 组件
class_name HealthBar
extends Control

@export var animate_damage: bool = true
@export var damage_animation_speed: float = 2.0

@onready var background: TextureProgressBar = $Background
@onready var damage_bar: TextureProgressBar = $DamageBar
@onready var health_bar: TextureProgressBar = $HealthBar
@onready var label: Label = $Label

var _target_value: float = 100.0

func _ready() -> void:
    health_bar.value = 100
    damage_bar.value = 100

func _process(delta: float) -> void:
    if animate_damage:
        damage_bar.value = lerpf(damage_bar.value, _target_value, damage_animation_speed * delta)

func update_value(current: int, max_value: int) -> void:
    var percentage = (float(current) / max_value) * 100.0
    _target_value = percentage
    health_bar.value = percentage
    
    if label:
        label.text = "%d / %d" % [current, max_value]

func set_max_value(value: int) -> void:
    health_bar.max_value = value
    damage_bar.max_value = value
    background.max_value = value
```

### 快捷栏组件 (quick_slots.gd)

```gdscript
## 快捷栏 UI
class_name QuickSlots
extends HBoxContainer

signal slot_selected(index: int)
signal slot_used(index: int)

@export var slot_count: int = 5
@export var slot_scene: PackedScene

var _slots: Array[Control] = []
var _selected_index: int = 0

func _ready() -> void:
    _create_slots()

func _create_slots() -> void:
    for i in range(slot_count):
        var slot = slot_scene.instantiate() if slot_scene else _create_default_slot()
        slot.name = "Slot_%d" % i
        add_child(slot)
        _slots.append(slot)
        
        if slot.has_signal("pressed"):
            slot.pressed.connect(func(): _on_slot_pressed(i))

func _create_default_slot() -> Control:
    var slot = Panel.new()
    slot.custom_minimum_size = Vector2(50, 50)
    return slot

func _unhandled_input(event: InputEvent) -> void:
    # 数字键选择
    for i in range(mini(slot_count, 9)):
        if event.is_action_pressed("slot_%d" % (i + 1)):
            select_slot(i)
            return
    
    # 滚轮切换
    if event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP:
            select_slot((_selected_index - 1 + slot_count) % slot_count)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            select_slot((_selected_index + 1) % slot_count)

func select_slot(index: int) -> void:
    if index < 0 or index >= slot_count:
        return
    
    _slots[_selected_index].modulate = Color.WHITE
    _selected_index = index
    _slots[_selected_index].modulate = Color.YELLOW
    
    slot_selected.emit(index)

func _on_slot_pressed(index: int) -> void:
    select_slot(index)
    slot_used.emit(index)

func set_slot_item(index: int, icon: Texture2D, count: int = 1) -> void:
    if index < 0 or index >= slot_count:
        return
    
    var slot = _slots[index]
    # 假设 slot 有 icon 和 count_label 子节点
    var icon_node = slot.get_node_or_null("Icon")
    var count_label = slot.get_node_or_null("Count")
    
    if icon_node and icon_node is TextureRect:
        icon_node.texture = icon
    if count_label and count_label is Label:
        count_label.text = str(count) if count > 1 else ""
        count_label.visible = count > 1

func clear_slot(index: int) -> void:
    set_slot_item(index, null, 0)
```

---

## 菜单组件

### 主菜单 (main_menu.gd)

```gdscript
## 主菜单
class_name MainMenu
extends Control

signal new_game_requested
signal continue_requested
signal settings_requested
signal quit_requested

@onready var new_game_btn: Button = $VBoxContainer/NewGameButton
@onready var continue_btn: Button = $VBoxContainer/ContinueButton
@onready var settings_btn: Button = $VBoxContainer/SettingsButton
@onready var quit_btn: Button = $VBoxContainer/QuitButton
@onready var version_label: Label = $VersionLabel

func _ready() -> void:
    new_game_btn.pressed.connect(_on_new_game)
    continue_btn.pressed.connect(_on_continue)
    settings_btn.pressed.connect(_on_settings)
    quit_btn.pressed.connect(_on_quit)
    
    _update_continue_button()
    _update_version_label()

func _update_continue_button() -> void:
    # 检查是否有存档
    continue_btn.disabled = not SaveManager.has_save_data()

func _update_version_label() -> void:
    if version_label:
        version_label.text = "v" + ProjectSettings.get_setting("application/config/version", "1.0.0")

func _on_new_game() -> void:
    new_game_requested.emit()

func _on_continue() -> void:
    continue_requested.emit()

func _on_settings() -> void:
    settings_requested.emit()
    UIManager.open_menu("SettingsMenu")

func _on_quit() -> void:
    quit_requested.emit()
    get_tree().quit()
```

### 暂停菜单 (pause_menu.gd)

```gdscript
## 暂停菜单
class_name PauseMenu
extends Control

@onready var resume_btn: Button = $Panel/VBoxContainer/ResumeButton
@onready var settings_btn: Button = $Panel/VBoxContainer/SettingsButton
@onready var main_menu_btn: Button = $Panel/VBoxContainer/MainMenuButton

func _ready() -> void:
    resume_btn.pressed.connect(_on_resume)
    settings_btn.pressed.connect(_on_settings)
    main_menu_btn.pressed.connect(_on_main_menu)

func open(_data: Dictionary = {}) -> void:
    show()
    resume_btn.grab_focus()

func close() -> void:
    hide()

func _on_resume() -> void:
    UIManager.close_current_menu()

func _on_settings() -> void:
    UIManager.open_menu("SettingsMenu")

func _on_main_menu() -> void:
    UIManager.show_confirm_dialog(
        "返回主菜单",
        "确定要返回主菜单吗？未保存的进度将丢失。",
        func():
            UIManager.close_all_menus()
            get_tree().paused = false
            get_tree().change_scene_to_file("res://scenes/main/main_menu.tscn")
    )
```

### 设置菜单 (settings_menu.gd)

```gdscript
## 设置菜单
class_name SettingsMenu
extends Control

# region 节点引用
@onready var tab_container: TabContainer = $Panel/TabContainer

# 音频选项卡
@onready var master_slider: HSlider = $Panel/TabContainer/Audio/MasterVolume/Slider
@onready var music_slider: HSlider = $Panel/TabContainer/Audio/MusicVolume/Slider
@onready var sfx_slider: HSlider = $Panel/TabContainer/Audio/SFXVolume/Slider

# 视频选项卡
@onready var fullscreen_check: CheckBox = $Panel/TabContainer/Video/Fullscreen
@onready var vsync_check: CheckBox = $Panel/TabContainer/Video/VSync
@onready var resolution_option: OptionButton = $Panel/TabContainer/Video/Resolution

# 控制选项卡
@onready var sensitivity_slider: HSlider = $Panel/TabContainer/Controls/Sensitivity/Slider
@onready var invert_y_check: CheckBox = $Panel/TabContainer/Controls/InvertY

@onready var back_btn: Button = $Panel/BackButton
@onready var apply_btn: Button = $Panel/ApplyButton
# endregion

var _settings: Dictionary = {}

func _ready() -> void:
    _connect_signals()
    _populate_resolutions()

func open(_data: Dictionary = {}) -> void:
    show()
    _load_settings()
    back_btn.grab_focus()

func close() -> void:
    hide()

func _connect_signals() -> void:
    back_btn.pressed.connect(_on_back)
    apply_btn.pressed.connect(_on_apply)
    
    master_slider.value_changed.connect(func(v): _settings.master_volume = v)
    music_slider.value_changed.connect(func(v): _settings.music_volume = v)
    sfx_slider.value_changed.connect(func(v): _settings.sfx_volume = v)
    
    fullscreen_check.toggled.connect(func(v): _settings.fullscreen = v)
    vsync_check.toggled.connect(func(v): _settings.vsync = v)
    
    sensitivity_slider.value_changed.connect(func(v): _settings.sensitivity = v)
    invert_y_check.toggled.connect(func(v): _settings.invert_y = v)

func _populate_resolutions() -> void:
    var resolutions = [
        Vector2i(1280, 720),
        Vector2i(1920, 1080),
        Vector2i(2560, 1440),
        Vector2i(3840, 2160)
    ]
    
    for res in resolutions:
        resolution_option.add_item("%dx%d" % [res.x, res.y])

func _load_settings() -> void:
    _settings = SettingsManager.get_all_settings()
    
    master_slider.value = _settings.get("master_volume", 1.0)
    music_slider.value = _settings.get("music_volume", 1.0)
    sfx_slider.value = _settings.get("sfx_volume", 1.0)
    
    fullscreen_check.button_pressed = _settings.get("fullscreen", false)
    vsync_check.button_pressed = _settings.get("vsync", true)
    
    sensitivity_slider.value = _settings.get("sensitivity", 1.0)
    invert_y_check.button_pressed = _settings.get("invert_y", false)

func _on_apply() -> void:
    SettingsManager.apply_settings(_settings)
    SettingsManager.save_settings()
    UIManager.show_notification("设置已保存")

func _on_back() -> void:
    UIManager.close_current_menu()
```

---

## 对话系统 UI

### dialogue_ui.gd

```gdscript
## 对话 UI
class_name DialogueUI
extends Control

signal dialogue_started
signal dialogue_ended
signal choice_made(choice_index: int)

@onready var portrait: TextureRect = $Panel/Portrait
@onready var name_label: Label = $Panel/NameLabel
@onready var text_label: RichTextLabel = $Panel/TextLabel
@onready var continue_indicator: Control = $Panel/ContinueIndicator
@onready var choices_container: VBoxContainer = $Panel/ChoicesContainer

var _current_dialogue: Array = []
var _current_index: int = 0
var _is_typing: bool = false
var _typing_speed: float = 0.03

func _ready() -> void:
    hide()

func _unhandled_input(event: InputEvent) -> void:
    if not visible:
        return
    
    if event.is_action_pressed("interact") or event.is_action_pressed("attack"):
        if _is_typing:
            _skip_typing()
        else:
            _advance_dialogue()

func start_dialogue(dialogue_data: Array) -> void:
    _current_dialogue = dialogue_data
    _current_index = 0
    show()
    dialogue_started.emit()
    _show_current_line()

func _show_current_line() -> void:
    if _current_index >= _current_dialogue.size():
        _end_dialogue()
        return
    
    var line = _current_dialogue[_current_index]
    
    # 设置角色信息
    name_label.text = line.get("speaker", "")
    if line.has("portrait"):
        portrait.texture = load(line.portrait)
        portrait.show()
    else:
        portrait.hide()
    
    # 清空选项
    _clear_choices()
    continue_indicator.hide()
    
    # 开始打字效果
    if line.has("text"):
        _type_text(line.text)
    
    # 处理选项
    if line.has("choices"):
        # 等待打字完成后显示选项
        await _typing_finished
        _show_choices(line.choices)

func _type_text(text: String) -> void:
    _is_typing = true
    text_label.text = ""
    text_label.visible_characters = 0
    text_label.text = text
    
    var tween = create_tween()
    tween.tween_property(text_label, "visible_characters", text.length(), text.length() * _typing_speed)
    await tween.finished
    
    _is_typing = false
    _on_typing_finished()

signal _typing_finished

func _on_typing_finished() -> void:
    _typing_finished.emit()
    
    var current_line = _current_dialogue[_current_index]
    if not current_line.has("choices"):
        continue_indicator.show()

func _skip_typing() -> void:
    text_label.visible_characters = -1
    _is_typing = false
    _on_typing_finished()

func _advance_dialogue() -> void:
    _current_index += 1
    _show_current_line()

func _show_choices(choices: Array) -> void:
    for i in range(choices.size()):
        var button = Button.new()
        button.text = choices[i].text
        button.pressed.connect(func(): _on_choice_selected(i, choices[i]))
        choices_container.add_child(button)
        
        if i == 0:
            button.grab_focus()

func _on_choice_selected(index: int, choice: Dictionary) -> void:
    choice_made.emit(index)
    _clear_choices()
    
    if choice.has("next"):
        _current_index = choice.next - 1  # -1 因为 advance 会 +1
    
    _advance_dialogue()

func _clear_choices() -> void:
    for child in choices_container.get_children():
        child.queue_free()

func _end_dialogue() -> void:
    hide()
    dialogue_ended.emit()
```

---

## 通知系统

### notification_manager.gd

```gdscript
## 通知管理器
class_name NotificationManager
extends VBoxContainer

@export var notification_scene: PackedScene
@export var max_notifications: int = 5
@export var default_duration: float = 3.0

func show_notification(message: String, duration: float = -1) -> void:
    if duration < 0:
        duration = default_duration
    
    var notif = notification_scene.instantiate() if notification_scene else _create_default_notification(message)
    add_child(notif)
    move_child(notif, 0)  # 新通知在顶部
    
    if notif.has_method("setup"):
        notif.setup(message, duration)
    
    # 限制数量
    while get_child_count() > max_notifications:
        var oldest = get_child(get_child_count() - 1)
        oldest.queue_free()

func _create_default_notification(message: String) -> Control:
    var panel = PanelContainer.new()
    var label = Label.new()
    label.text = message
    panel.add_child(label)
    
    # 自动消失
    var tween = create_tween()
    tween.tween_interval(default_duration)
    tween.tween_property(panel, "modulate:a", 0.0, 0.3)
    tween.tween_callback(panel.queue_free)
    
    return panel
```

---

## 主题系统

### theme_manager.gd

```gdscript
## 主题管理器
class_name ThemeManager
extends Node

const THEMES_PATH = "res://assets/themes/"

var current_theme: Theme
var _available_themes: Dictionary = {}

func _ready() -> void:
    _load_available_themes()
    apply_theme("default")

func _load_available_themes() -> void:
    var dir = DirAccess.open(THEMES_PATH)
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if file_name.ends_with(".tres"):
                var theme_name = file_name.replace(".tres", "")
                _available_themes[theme_name] = THEMES_PATH + file_name
            file_name = dir.get_next()
        dir.list_dir_end()

func apply_theme(theme_name: String) -> void:
    if not _available_themes.has(theme_name):
        push_error("Theme not found: " + theme_name)
        return
    
    current_theme = load(_available_themes[theme_name])
    
    # 应用到根节点，所有 UI 会继承
    get_tree().root.theme = current_theme

func get_available_themes() -> Array:
    return _available_themes.keys()
```

---

## 使用示例

### 创建 HUD

```
创建游戏 HUD，包含：
- 血条（带受伤动画）
- 魔法条
- 金币显示
- 快捷物品栏（5格）
- 小地图
```

### 创建设置菜单

```
创建设置菜单，包含：
- 音频设置（主音量、音乐、音效）
- 视频设置（分辨率、全屏、垂直同步）
- 控制设置（灵敏度、反转Y轴、按键重映射）
```
