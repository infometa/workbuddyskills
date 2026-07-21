---
name: audio-system
description: >
  音频系统技能。管理游戏音频播放，包括背景音乐、音效、语音等。
  支持音频池、淡入淡出、3D 音效等功能。
version: 1.0.0
dependencies:
  - godot-core
triggers:
  - pattern: "音频|音乐|音效|BGM|SFX|AudioManager"
inputs:
  - name: audio_type
    type: string
    enum: ["music", "sfx", "voice", "ambient"]
    required: false
outputs:
  - name: audio_manager
    type: file
    path_pattern: "res://scripts/autoload/audio_manager.gd"
---

# 音频系统技能

管理游戏中的所有音频播放。

## 音频总线配置

在 Godot 中配置以下音频总线：

```
Master
├── Music      # 背景音乐
├── SFX        # 音效
├── Voice      # 语音
└── Ambient    # 环境音
```

---

## 音频管理器

### audio_manager.gd (Autoload)

```gdscript
## 音频管理器
##
## 统一管理所有音频播放
## @author AI Generated
## @version 1.0.0
class_name AudioManager
extends Node

# region 信号
signal music_started(track_name: String)
signal music_stopped
signal music_changed(old_track: String, new_track: String)
# endregion

# region 常量
const MUSIC_BUS = "Music"
const SFX_BUS = "SFX"
const VOICE_BUS = "Voice"
const AMBIENT_BUS = "Ambient"
# endregion

# region 导出变量
@export var sfx_pool_size: int = 16
@export var default_music_fade_time: float = 1.0
# endregion

# region 节点引用
var _music_player: AudioStreamPlayer
var _music_player_2: AudioStreamPlayer  # 用于交叉淡化
var _voice_player: AudioStreamPlayer
var _ambient_player: AudioStreamPlayer
var _sfx_pool: Array[AudioStreamPlayer] = []
var _sfx_pool_3d: Array[AudioStreamPlayer3D] = []
# endregion

# region 状态
var current_music: String = ""
var _music_volume: float = 1.0
var _sfx_volume: float = 1.0
var _voice_volume: float = 1.0
var _is_music_fading: bool = false
var _active_player: AudioStreamPlayer = null
# endregion

# region 预加载音频缓存
var _audio_cache: Dictionary = {}
# endregion

# region 生命周期
func _ready() -> void:
    _setup_music_players()
    _setup_sfx_pool()
    _setup_voice_player()
    _setup_ambient_player()

func _setup_music_players() -> void:
    _music_player = AudioStreamPlayer.new()
    _music_player.bus = MUSIC_BUS
    add_child(_music_player)
    
    _music_player_2 = AudioStreamPlayer.new()
    _music_player_2.bus = MUSIC_BUS
    add_child(_music_player_2)
    
    _active_player = _music_player

func _setup_sfx_pool() -> void:
    for i in range(sfx_pool_size):
        var player = AudioStreamPlayer.new()
        player.bus = SFX_BUS
        add_child(player)
        _sfx_pool.append(player)
        
        var player_3d = AudioStreamPlayer3D.new()
        player_3d.bus = SFX_BUS
        add_child(player_3d)
        _sfx_pool_3d.append(player_3d)

func _setup_voice_player() -> void:
    _voice_player = AudioStreamPlayer.new()
    _voice_player.bus = VOICE_BUS
    add_child(_voice_player)

func _setup_ambient_player() -> void:
    _ambient_player = AudioStreamPlayer.new()
    _ambient_player.bus = AMBIENT_BUS
    add_child(_ambient_player)
# endregion

# region 音乐播放
## 播放背景音乐
func play_music(track_path: String, fade_time: float = -1, loop: bool = true) -> void:
    if fade_time < 0:
        fade_time = default_music_fade_time
    
    var stream = _get_audio_stream(track_path)
    if not stream:
        push_error("Music not found: " + track_path)
        return
    
    var old_track = current_music
    current_music = track_path
    
    if fade_time > 0 and _active_player.playing:
        _crossfade_music(stream, fade_time, loop)
    else:
        _active_player.stream = stream
        _active_player.play()
    
    music_started.emit(track_path)
    if old_track != track_path:
        music_changed.emit(old_track, track_path)

## 停止背景音乐
func stop_music(fade_time: float = -1) -> void:
    if fade_time < 0:
        fade_time = default_music_fade_time
    
    if fade_time > 0:
        _fade_out_music(fade_time)
    else:
        _active_player.stop()
    
    current_music = ""
    music_stopped.emit()

## 暂停背景音乐
func pause_music() -> void:
    _active_player.stream_paused = true

## 继续背景音乐
func resume_music() -> void:
    _active_player.stream_paused = false

## 交叉淡化
func _crossfade_music(new_stream: AudioStream, duration: float, loop: bool) -> void:
    _is_music_fading = true
    
    var old_player = _active_player
    var new_player = _music_player if _active_player == _music_player_2 else _music_player_2
    
    new_player.stream = new_stream
    new_player.volume_db = -80
    new_player.play()
    
    var tween = create_tween()
    tween.set_parallel(true)
    tween.tween_property(old_player, "volume_db", -80, duration)
    tween.tween_property(new_player, "volume_db", linear_to_db(_music_volume), duration)
    
    await tween.finished
    
    old_player.stop()
    old_player.volume_db = linear_to_db(_music_volume)
    _active_player = new_player
    _is_music_fading = false

func _fade_out_music(duration: float) -> void:
    var tween = create_tween()
    tween.tween_property(_active_player, "volume_db", -80, duration)
    await tween.finished
    _active_player.stop()
    _active_player.volume_db = linear_to_db(_music_volume)
# endregion

# region 音效播放
## 播放 2D 音效
func play_sfx(sound_path: String, volume: float = 1.0, pitch: float = 1.0) -> AudioStreamPlayer:
    var stream = _get_audio_stream(sound_path)
    if not stream:
        push_error("SFX not found: " + sound_path)
        return null
    
    var player = _get_available_sfx_player()
    if player:
        player.stream = stream
        player.volume_db = linear_to_db(volume * _sfx_volume)
        player.pitch_scale = pitch
        player.play()
    
    return player

## 播放带随机音高的音效
func play_sfx_pitched(sound_path: String, pitch_range: Vector2 = Vector2(0.9, 1.1), volume: float = 1.0) -> AudioStreamPlayer:
    var pitch = randf_range(pitch_range.x, pitch_range.y)
    return play_sfx(sound_path, volume, pitch)

## 播放 3D 音效
func play_sfx_3d(sound_path: String, position: Vector3, volume: float = 1.0, pitch: float = 1.0) -> AudioStreamPlayer3D:
    var stream = _get_audio_stream(sound_path)
    if not stream:
        push_error("SFX not found: " + sound_path)
        return null
    
    var player = _get_available_sfx_player_3d()
    if player:
        player.stream = stream
        player.global_position = position
        player.volume_db = linear_to_db(volume * _sfx_volume)
        player.pitch_scale = pitch
        player.play()
    
    return player

## 播放 3D 音效（附加到节点）
func play_sfx_at_node(sound_path: String, node: Node3D, volume: float = 1.0) -> AudioStreamPlayer3D:
    return play_sfx_3d(sound_path, node.global_position, volume)

func _get_available_sfx_player() -> AudioStreamPlayer:
    for player in _sfx_pool:
        if not player.playing:
            return player
    
    # 如果所有都在使用，返回第一个（会被覆盖）
    return _sfx_pool[0]

func _get_available_sfx_player_3d() -> AudioStreamPlayer3D:
    for player in _sfx_pool_3d:
        if not player.playing:
            return player
    
    return _sfx_pool_3d[0]
# endregion

# region 语音播放
## 播放语音
func play_voice(voice_path: String, on_finished: Callable = Callable()) -> void:
    var stream = _get_audio_stream(voice_path)
    if not stream:
        push_error("Voice not found: " + voice_path)
        return
    
    # 停止当前语音
    if _voice_player.playing:
        _voice_player.stop()
    
    _voice_player.stream = stream
    _voice_player.play()
    
    if on_finished.is_valid():
        await _voice_player.finished
        on_finished.call()

## 停止语音
func stop_voice() -> void:
    _voice_player.stop()

## 检查语音是否在播放
func is_voice_playing() -> bool:
    return _voice_player.playing
# endregion

# region 环境音
## 播放环境音
func play_ambient(ambient_path: String, fade_time: float = 1.0) -> void:
    var stream = _get_audio_stream(ambient_path)
    if not stream:
        return
    
    _ambient_player.stream = stream
    _ambient_player.volume_db = -80
    _ambient_player.play()
    
    var tween = create_tween()
    tween.tween_property(_ambient_player, "volume_db", 0, fade_time)

## 停止环境音
func stop_ambient(fade_time: float = 1.0) -> void:
    var tween = create_tween()
    tween.tween_property(_ambient_player, "volume_db", -80, fade_time)
    await tween.finished
    _ambient_player.stop()
# endregion

# region 音量控制
func set_master_volume(volume: float) -> void:
    var bus_index = AudioServer.get_bus_index("Master")
    AudioServer.set_bus_volume_db(bus_index, linear_to_db(volume))

func set_music_volume(volume: float) -> void:
    _music_volume = volume
    var bus_index = AudioServer.get_bus_index(MUSIC_BUS)
    AudioServer.set_bus_volume_db(bus_index, linear_to_db(volume))

func set_sfx_volume(volume: float) -> void:
    _sfx_volume = volume
    var bus_index = AudioServer.get_bus_index(SFX_BUS)
    AudioServer.set_bus_volume_db(bus_index, linear_to_db(volume))

func set_voice_volume(volume: float) -> void:
    _voice_volume = volume
    var bus_index = AudioServer.get_bus_index(VOICE_BUS)
    AudioServer.set_bus_volume_db(bus_index, linear_to_db(volume))

func get_music_volume() -> float:
    return _music_volume

func get_sfx_volume() -> float:
    return _sfx_volume

func get_voice_volume() -> float:
    return _voice_volume

## 静音/取消静音
func mute_bus(bus_name: String, muted: bool) -> void:
    var bus_index = AudioServer.get_bus_index(bus_name)
    AudioServer.set_bus_mute(bus_index, muted)

func is_bus_muted(bus_name: String) -> bool:
    var bus_index = AudioServer.get_bus_index(bus_name)
    return AudioServer.is_bus_mute(bus_index)
# endregion

# region 音频缓存
func preload_audio(paths: Array) -> void:
    for path in paths:
        _get_audio_stream(path)

func _get_audio_stream(path: String) -> AudioStream:
    if _audio_cache.has(path):
        return _audio_cache[path]
    
    if ResourceLoader.exists(path):
        var stream = load(path)
        _audio_cache[path] = stream
        return stream
    
    return null

func clear_audio_cache() -> void:
    _audio_cache.clear()
# endregion
```

---

## 音效触发器组件

### sfx_trigger.gd

```gdscript
## 音效触发器
##
## 在特定事件时播放音效
class_name SFXTrigger
extends Node

@export var sound_path: String
@export var volume: float = 1.0
@export var pitch_variation: Vector2 = Vector2(1.0, 1.0)
@export var trigger_on_ready: bool = false
@export var cooldown: float = 0.0

var _can_play: bool = true

func _ready() -> void:
    if trigger_on_ready:
        play()

func play() -> void:
    if not _can_play:
        return
    
    var pitch = randf_range(pitch_variation.x, pitch_variation.y)
    AudioManager.play_sfx(sound_path, volume, pitch)
    
    if cooldown > 0:
        _can_play = false
        await get_tree().create_timer(cooldown).timeout
        _can_play = true
```

### 区域音效触发器

```gdscript
## 区域音效触发器
class_name AreaSFXTrigger
extends Area3D

@export var sound_path: String
@export var volume: float = 1.0
@export var one_shot: bool = true

var _triggered: bool = false

func _ready() -> void:
    body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node3D) -> void:
    if one_shot and _triggered:
        return
    
    if body.is_in_group("player"):
        AudioManager.play_sfx_3d(sound_path, global_position, volume)
        _triggered = true
```

---

## 音乐区域

### music_zone.gd

```gdscript
## 音乐区域
##
## 进入区域时切换背景音乐
class_name MusicZone
extends Area3D

@export var music_path: String
@export var fade_time: float = 2.0
@export var priority: int = 0

var _previous_music: String = ""

func _ready() -> void:
    body_entered.connect(_on_body_entered)
    body_exited.connect(_on_body_exited)

func _on_body_entered(body: Node3D) -> void:
    if body.is_in_group("player"):
        _previous_music = AudioManager.current_music
        AudioManager.play_music(music_path, fade_time)

func _on_body_exited(body: Node3D) -> void:
    if body.is_in_group("player"):
        if _previous_music:
            AudioManager.play_music(_previous_music, fade_time)
```

---

## 随机音效播放器

### random_sfx_player.gd

```gdscript
## 随机音效播放器
##
## 从列表中随机播放音效
class_name RandomSFXPlayer
extends Node

@export var sounds: Array[String] = []
@export var volume: float = 1.0
@export var pitch_variation: Vector2 = Vector2(0.9, 1.1)
@export var avoid_repeat: bool = true

var _last_played_index: int = -1

func play() -> void:
    if sounds.is_empty():
        return
    
    var index = randi() % sounds.size()
    
    if avoid_repeat and sounds.size() > 1:
        while index == _last_played_index:
            index = randi() % sounds.size()
    
    _last_played_index = index
    
    var pitch = randf_range(pitch_variation.x, pitch_variation.y)
    AudioManager.play_sfx(sounds[index], volume, pitch)

func play_at_position(position: Vector3) -> void:
    if sounds.is_empty():
        return
    
    var index = randi() % sounds.size()
    if avoid_repeat and sounds.size() > 1:
        while index == _last_played_index:
            index = randi() % sounds.size()
    
    _last_played_index = index
    
    var pitch = randf_range(pitch_variation.x, pitch_variation.y)
    AudioManager.play_sfx_3d(sounds[index], position, volume, pitch)
```

---

## 脚步声系统

### footstep_system.gd

```gdscript
## 脚步声系统
class_name FootstepSystem
extends Node

@export var character: CharacterBody3D
@export var step_interval: float = 0.5
@export var run_step_interval: float = 0.3

var _step_timer: float = 0.0
var _surface_detector: RayCast3D

# 表面类型 -> 音效列表
var _surface_sounds: Dictionary = {
    "default": ["res://assets/audio/sfx/footsteps/concrete_01.ogg"],
    "grass": ["res://assets/audio/sfx/footsteps/grass_01.ogg"],
    "wood": ["res://assets/audio/sfx/footsteps/wood_01.ogg"],
    "metal": ["res://assets/audio/sfx/footsteps/metal_01.ogg"],
    "water": ["res://assets/audio/sfx/footsteps/water_01.ogg"]
}

func _ready() -> void:
    _setup_surface_detector()

func _setup_surface_detector() -> void:
    _surface_detector = RayCast3D.new()
    _surface_detector.target_position = Vector3(0, -1, 0)
    character.add_child(_surface_detector)

func _physics_process(delta: float) -> void:
    if not character.is_on_floor():
        return
    
    var velocity = character.velocity
    var speed = Vector2(velocity.x, velocity.z).length()
    
    if speed < 0.1:
        return
    
    _step_timer += delta
    var interval = run_step_interval if speed > 5.0 else step_interval
    
    if _step_timer >= interval:
        _step_timer = 0.0
        _play_footstep()

func _play_footstep() -> void:
    var surface = _detect_surface()
    var sounds = _surface_sounds.get(surface, _surface_sounds["default"])
    var sound = sounds[randi() % sounds.size()]
    
    AudioManager.play_sfx_pitched(sound, Vector2(0.9, 1.1), 0.7)

func _detect_surface() -> String:
    if _surface_detector.is_colliding():
        var collider = _surface_detector.get_collider()
        if collider.has_meta("surface_type"):
            return collider.get_meta("surface_type")
    
    return "default"
```

---

## 配置示例

### audio_config.json

```json
{
  "music": {
    "main_menu": "res://assets/audio/music/main_menu.ogg",
    "gameplay": "res://assets/audio/music/gameplay.ogg",
    "boss": "res://assets/audio/music/boss.ogg",
    "victory": "res://assets/audio/music/victory.ogg",
    "game_over": "res://assets/audio/music/game_over.ogg"
  },
  "sfx": {
    "ui": {
      "click": "res://assets/audio/sfx/ui/click.ogg",
      "hover": "res://assets/audio/sfx/ui/hover.ogg",
      "confirm": "res://assets/audio/sfx/ui/confirm.ogg",
      "cancel": "res://assets/audio/sfx/ui/cancel.ogg"
    },
    "player": {
      "jump": "res://assets/audio/sfx/player/jump.ogg",
      "land": "res://assets/audio/sfx/player/land.ogg",
      "hurt": "res://assets/audio/sfx/player/hurt.ogg",
      "attack": ["res://assets/audio/sfx/player/attack_01.ogg", "res://assets/audio/sfx/player/attack_02.ogg"]
    }
  },
  "ambient": {
    "forest": "res://assets/audio/ambient/forest.ogg",
    "cave": "res://assets/audio/ambient/cave.ogg",
    "rain": "res://assets/audio/ambient/rain.ogg"
  }
}
```

---

## 使用示例

```gdscript
# 播放背景音乐
AudioManager.play_music("res://assets/audio/music/gameplay.ogg")

# 带淡入淡出切换音乐
AudioManager.play_music("res://assets/audio/music/boss.ogg", 2.0)

# 播放音效
AudioManager.play_sfx("res://assets/audio/sfx/explosion.ogg")

# 播放带随机音高的音效
AudioManager.play_sfx_pitched("res://assets/audio/sfx/hit.ogg")

# 播放 3D 音效
AudioManager.play_sfx_3d("res://assets/audio/sfx/explosion.ogg", enemy.global_position)

# 播放语音
AudioManager.play_voice("res://assets/audio/voice/greeting.ogg", func():
    print("Voice finished")
)

# 调整音量
AudioManager.set_music_volume(0.5)
AudioManager.set_sfx_volume(0.8)
```
