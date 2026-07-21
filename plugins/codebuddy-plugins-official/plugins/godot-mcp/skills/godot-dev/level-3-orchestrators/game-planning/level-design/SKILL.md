---
name: level-design
description: >
  关卡设计策划技能。生成关卡架构、敌人配置、Boss设计、难度曲线等关卡设计文档，
  并提供对应的 GDScript 代码模板。
version: 2.0.0
dependencies:
  - game-dev-workflow
  - file-manager
triggers:
  - pattern: "关卡设计|地图设计|Boss设计|敌人配置"
inputs:
  - name: game_type
    type: string
    required: true
  - name: modules
    type: array
    description: "需要的关卡模块，按需选取"
    items:
      enum: ["level_structure", "enemy_config", "boss_design", "difficulty_curve", "checkpoint", "loot_placement"]
    required: false
outputs:
  - name: level_design
    type: file
    path_pattern: "docs/planning/level_design.md"
---

# 关卡设计策划

## 输出模板

```markdown
# {游戏名称} - 关卡设计

## 1. 关卡架构

### 总览
```
World 1: 初始之地 (教程)
├── 1-1: 觉醒之村 [教程]
├── 1-2: 幽林小径 [战斗]
├── 1-3: 古老遗迹 [探索]
└── 1-B: 守护者 [Boss]

World 2: ...
```

### 解锁规则
- 完成关卡 → 解锁下一关
- 收集钥匙 → 解锁隐藏关
- 全星通关 → 解锁困难模式

## 2. 单关卡模板

### 关卡信息
- ID: 1-2
- 名称: 幽林小径
- 类型: 战斗关
- 时长: 5分钟
- 难度: 3/10

### 区域流程
1. **入口区** (30秒): 无敌人，提供回复
2. **战斗区** (3分钟): 主要战斗
3. **探索区** (1分钟): 谜题/秘密
4. **出口** (30秒): 奖励结算

### 敌人配置
| 敌人 | 数量 | 位置 | 触发 |
|------|------|------|------|
| 史莱姆 | 5 | 战斗区 | 进入触发 |
| 哥布林 | 3 | 战斗区 | 第二波 |
| 精英狼 | 1 | 出口前 | 击杀前面 |

### 物品配置
| 物品 | 位置 | 条件 |
|------|------|------|
| 小药水×2 | 入口 | 可见 |
| 宝箱 | 探索区 | 解谜后 |

## 3. 敌人设计

### 普通敌人
```
名称: 史莱姆
HP: 50 | ATK: 8 | DEF: 2
行为: 巡逻 → 发现玩家 → 追击 → 攻击
攻击: 弹跳 (1.0伤害, 2秒CD)
掉落: 金币5-10, 史莱姆凝胶50%
```

### Boss模板
```
名称: 森林守护者
HP: 2000 | ATK: 25 | DEF: 15

Phase 1 (100%-50%):
- 三连斩: 近战连击
- 冲锋: 直线冲刺

Phase 2 (50%-0%):
- 狂暴: ATK+30%, SPD+20%
- 新技能: 根须陷阱

弱点: 攻击后硬直2秒
奖励: 500EXP, 200-300金币, Boss材料
```

## 4. 难度曲线

```
难度
│                    ╱
│               ╱───╱
│         ╱────╱
│    ╱───╱
│───╱
└─────────────────────→ 进度
  教学  入门  中期  后期
```

关键节点:
- 10%: 首次可能死亡
- 25%: 教学结束
- 50%: 中期高峰
- 90%: 最高难度
```

---

## 代码模板

```gdscript
## 关卡管理器
class_name LevelManager
extends Node

signal level_completed(level_id, stars)
signal checkpoint_reached(cp_id)

var current_level: String
var checkpoints: Dictionary = {}
var objectives: Dictionary = {}

func load_level(level_id: String) -> void:
    current_level = level_id
    objectives.clear()
    # 加载关卡场景和数据

func update_objective(obj_id: String, amount := 1) -> void:
    objectives[obj_id] = objectives.get(obj_id, 0) + amount
    _check_completion()

func reach_checkpoint(cp_id: String) -> void:
    checkpoints[current_level] = cp_id
    checkpoint_reached.emit(cp_id)

func _check_completion() -> void:
    # 检查是否完成所有目标
    pass
```

```gdscript
## 敌人AI基类
class_name EnemyAI
extends CharacterBody2D

enum State { IDLE, PATROL, CHASE, ATTACK, HURT, DEAD }

@export var max_hp := 100
@export var atk := 10
@export var detection_range := 200.0
@export var attack_range := 50.0
@export var move_speed := 100.0

var hp: int
var state := State.IDLE
var target: Node2D

func _ready() -> void:
    hp = max_hp

func _physics_process(delta: float) -> void:
    match state:
        State.IDLE, State.PATROL:
            _look_for_target()
        State.CHASE:
            _chase_target(delta)
        State.ATTACK:
            _attack()

func _look_for_target() -> void:
    var players = get_tree().get_nodes_in_group("player")
    for p in players:
        if global_position.distance_to(p.global_position) < detection_range:
            target = p
            state = State.CHASE

func _chase_target(delta: float) -> void:
    if not target:
        state = State.IDLE
        return
    var dist = global_position.distance_to(target.global_position)
    if dist <= attack_range:
        state = State.ATTACK
    else:
        velocity = global_position.direction_to(target.global_position) * move_speed
        move_and_slide()

func _attack() -> void:
    # 子类实现具体攻击
    pass

func take_damage(amount: int) -> void:
    hp -= amount
    if hp <= 0:
        state = State.DEAD
        queue_free()
    else:
        state = State.HURT
```
