---
name: numerical-design
description: >
  数值系统策划技能。生成属性系统、伤害公式、经济系统、掉落概率等数值设计文档，
  并提供对应的 GDScript 代码模板。
version: 2.0.0
dependencies:
  - game-dev-workflow
  - file-manager
triggers:
  - pattern: "数值设计|属性设计|伤害公式|经济系统"
inputs:
  - name: game_type
    type: string
    required: true
  - name: modules
    type: array
    description: "需要的数值模块，按需选取"
    items:
      enum: ["attributes", "damage_formula", "economy", "equipment", "elemental", "loot", "ttk", "progression"]
    required: false
outputs:
  - name: numerical_design
    type: file
    path_pattern: "docs/planning/numerical_design.md"
---

# 数值系统策划

## 输出模板

```markdown
# {游戏名称} - 数值设计

## 1. 属性系统

### 基础属性
| 属性 | 缩写 | 范围 | 说明 |
|------|------|------|------|
| 生命 | HP | 100-10000 | 生存能力 |
| 攻击 | ATK | 10-1000 | 伤害基础 |
| 防御 | DEF | 0-500 | 减伤能力 |
| 速度 | SPD | 50-200 | 行动速度 |

### 衍生属性
| 属性 | 基础值 | 上限 |
|------|--------|------|
| 暴击率 | 5% | 75% |
| 暴击伤害 | 150% | 300% |
| 命中率 | 95% | 100% |
| 闪避率 | 5% | 50% |

## 2. 伤害公式

### 基础伤害
```
伤害 = ATK × 技能倍率 × (100 / (100 + DEF))
```

### 暴击加成
```
最终 = 基础伤害 × (暴击 ? 暴击伤害 : 1.0)
```

### 属性克制
| 攻击 | 被克制 | 克制 |
|------|--------|------|
| 火 | 水×0.7 | 风×1.3 |
| 水 | 土×0.7 | 火×1.3 |
| 土 | 风×0.7 | 水×1.3 |
| 风 | 火×0.7 | 土×1.3 |

## 3. 时间杀伤 (TTK)

| 场景 | TTK |
|------|-----|
| 玩家 vs 小怪 | 1-3秒 |
| 玩家 vs 精英 | 15-30秒 |
| 玩家 vs Boss | 2-5分钟 |
| 小怪 vs 玩家 (无操作) | 10-15秒 |

## 4. 经济系统

### 货币
- **金币**: 主要货币，战斗获取
- **宝石**: 稀有货币，成就/付费

### 每小时预算
| 阶段 | 金币 | 经验 |
|------|------|------|
| 前期 | 1000-1500 | 500-1000 |
| 中期 | 2000-3000 | 2000-3000 |
| 后期 | 5000+ | 5000+ |

### 消耗平衡
- 收入略>支出 (前期)
- 收入≈支出 (中期)
- 收入<支出 (后期，促进挑战)

## 5. 掉落概率

### 稀有度掉落
| 品质 | 概率 |
|------|------|
| 白 | 60% |
| 绿 | 25% |
| 蓝 | 10% |
| 紫 | 4% |
| 橙 | 1% |

### 保底机制
- 软保底: 连续未出，概率递增
- 硬保底: 50次必出紫，100次必出橙
```

---

## 代码模板

```gdscript
## 伤害计算器
class_name DamageCalc

enum Element { NONE, FIRE, WATER, EARTH, WIND }

const ELEMENT_CHART := {
    Element.FIRE: { Element.WIND: 1.3, Element.WATER: 0.7 },
    Element.WATER: { Element.FIRE: 1.3, Element.EARTH: 0.7 },
    Element.EARTH: { Element.WATER: 1.3, Element.WIND: 0.7 },
    Element.WIND: { Element.EARTH: 1.3, Element.FIRE: 0.7 },
}

static func calc(atk: float, def: float, mult := 1.0, 
                 crit_rate := 0.05, crit_dmg := 1.5,
                 atk_elem := Element.NONE, def_elem := Element.NONE) -> Dictionary:
    
    # 基础伤害
    var base = atk * mult * (100.0 / (100.0 + def))
    
    # 属性克制
    var elem_mult = 1.0
    if ELEMENT_CHART.has(atk_elem):
        elem_mult = ELEMENT_CHART[atk_elem].get(def_elem, 1.0)
    base *= elem_mult
    
    # 暴击
    var is_crit = randf() < crit_rate
    if is_crit:
        base *= crit_dmg
    
    # 浮动 ±10%
    base *= randf_range(0.9, 1.1)
    
    return { "damage": int(max(1, base)), "crit": is_crit }
```

```gdscript
## 掉落系统
class_name LootSystem

var tables: Dictionary = {}
var pity: Dictionary = {}

func roll(table_id: String) -> Array:
    var table = tables.get(table_id, {})
    var drops := []
    
    # 保底掉落
    for item in table.get("guaranteed", []):
        drops.append(_make_drop(item))
    
    # 随机掉落
    var random_pool = table.get("random", [])
    if random_pool.size() > 0:
        var rolled = _weighted_random(random_pool)
        if rolled:
            drops.append(_make_drop(rolled))
    
    return drops

func _weighted_random(items: Array) -> Dictionary:
    var total = 0.0
    for i in items:
        total += i.get("weight", 1.0)
    
    var roll = randf() * total
    var current = 0.0
    for i in items:
        current += i.get("weight", 1.0)
        if roll <= current:
            return i
    return {}

func _make_drop(data: Dictionary) -> Dictionary:
    var amount = data.get("amount", 1)
    if amount is String and "-" in amount:
        var parts = amount.split("-")
        amount = randi_range(int(parts[0]), int(parts[1]))
    return { "item": data.get("item", ""), "amount": amount }
```

---

## 配置JSON示例

```json
{
  "characters": {
    "warrior": {
      "base_hp": 150, "hp_growth": 10,
      "base_atk": 15, "atk_growth": 2,
      "base_def": 10, "def_growth": 1.5
    }
  },
  "enemies": {
    "slime": {
      "hp": 50, "atk": 8, "def": 2,
      "exp": 10, "gold": [5, 10]
    }
  },
  "loot_tables": {
    "slime": {
      "guaranteed": [{ "item": "gold", "amount": "5-10" }],
      "random": [
        { "item": "slime_gel", "weight": 50 },
        { "item": "potion", "weight": 30 }
      ]
    }
  }
}
```
