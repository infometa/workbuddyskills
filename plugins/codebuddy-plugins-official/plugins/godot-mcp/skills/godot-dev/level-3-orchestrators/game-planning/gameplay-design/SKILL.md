---
name: gameplay-design
description: >
  玩法内容策划技能。生成核心循环、战斗系统、成长系统等玩法设计文档，
  并提供对应的 GDScript 代码模板。
version: 2.0.0
dependencies:
  - game-dev-workflow
  - file-manager
triggers:
  - pattern: "玩法设计|核心玩法|战斗系统|成长系统"
inputs:
  - name: game_type
    type: string
    required: true
  - name: modules
    type: array
    description: "需要的玩法模块，按需选取"
    items:
      enum: ["core_loop", "combat", "progression", "quest", "skill_tree", "inventory"]
    required: false
outputs:
  - name: gameplay_design
    type: file
    path_pattern: "docs/planning/gameplay_design.md"
---

# 玩法内容策划

## 输出模板

```markdown
# {游戏名称} - 玩法设计

## 1. 核心循环

```
挑战 → 行动 → 反馈 → 奖励 → 成长 → 更大挑战
```

### 循环层级
- **微循环** (秒): 攻击→命中→击杀
- **短循环** (分钟): 清怪→拿装备→前进
- **中循环** (10分钟): 通关→结算→下一关
- **长循环** (小时): 解锁→尝试→挑战更高

## 2. 战斗系统

### 攻击类型
| 类型 | 消耗 | 伤害 | 特点 |
|------|------|------|------|
| 普攻 | 无 | 100% | 主要输出 |
| 蓄力 | 时间 | 200% | 有硬直 |
| 技能 | MP | 150%+ | 特殊效果 |

### 攻击帧数 (60FPS)
- 前摇: 6帧 (可被打断)
- 判定: 3帧
- 后摇: 12帧 (可取消)

### 连招示例
- 基础: 攻击×3
- 衍生: 攻击×2 → 蓄力
- 空中: 跳 → 攻击×2 → 下砸

### 防御系统
| 方式 | 操作 | 效果 |
|------|------|------|
| 闪避 | 方向+闪避键 | 无敌帧 |
| 格挡 | 防御键 | 减伤50% |
| 弹反 | 精准格挡 | 反弹+眩晕 |

## 3. 成长系统

### 等级公式
```
升级经验 = 100 × 等级^2
```

### 属性成长
| 等级 | HP | ATK | DEF |
|------|-----|-----|-----|
| 1 | 100 | 10 | 5 |
| 10 | 200 | 25 | 15 |
| 50 | 600 | 100 | 50 |

### 装备品质
- 白: 无词条
- 绿: 1词条
- 蓝: 2词条
- 紫: 3词条+套装
- 橙: 4词条+特效

## 4. 目标系统

### 任务类型
- 主线: 推进剧情，必须完成
- 支线: 额外奖励，可选
- 日常: 每日重置，稳定收益
```

---

## 代码模板

```gdscript
## 战斗管理器
class_name CombatManager
extends Node

signal damage_dealt(attacker, target, damage)

const HIT_STOP := 0.05

func deal_damage(atk: Node, def: Node, base: float, multiplier := 1.0) -> int:
    var atk_power = atk.get_stat("atk") if atk.has_method("get_stat") else 0
    var def_power = def.get_stat("def") if def.has_method("get_stat") else 0
    
    # 伤害公式: 攻击 × 倍率 × (100 / (100 + 防御))
    var damage = base * multiplier * (1 + atk_power / 100.0)
    damage *= 100.0 / (100.0 + def_power)
    
    var final = int(max(1, damage))
    
    if def.has_method("take_damage"):
        def.take_damage(final)
    
    damage_dealt.emit(atk, def, final)
    _hit_stop()
    return final

func _hit_stop() -> void:
    Engine.time_scale = 0.0
    await get_tree().create_timer(HIT_STOP, true, false, true).timeout
    Engine.time_scale = 1.0
```

```gdscript
## 属性组件
class_name StatsComponent
extends Node

signal level_up(new_level)

@export var base_hp := 100
@export var base_atk := 10
@export var hp_growth := 10.0
@export var atk_growth := 2.0

var level := 1
var exp := 0
var bonuses: Dictionary = {}

func get_stat(stat: String) -> float:
    var base = get("base_" + stat) or 0
    var growth = get(stat + "_growth") or 0
    var bonus = bonuses.get(stat, 0.0)
    return (base + level * growth) * (1 + bonus)

func add_exp(amount: int) -> void:
    exp += amount
    while exp >= _exp_required():
        exp -= _exp_required()
        level += 1
        level_up.emit(level)

func _exp_required() -> int:
    return 100 * level * level
```
