---
name: game-config-templates
description: >
  游戏配置文件模板集合。包含角色、敌人、物品、技能、关卡等核心配置的JSON模板。
  供策划和代码生成使用。
version: 1.0.0
dependencies:
  - game-planning
  - config-generator
triggers:
  - pattern: "配置模板|JSON配置|数据表模板"
outputs:
  - name: config_templates
    type: directory
    path_pattern: "data/design/templates/"
---

# 游戏配置文件模板集

## 概述

本文件提供游戏开发中常用的JSON配置模板，确保数据结构一致性。

---

## 1. 角色配置模板

### characters.json

```json
{
  "$schema": "character_schema.json",
  "version": "1.0.0",
  "characters": {
    "player_warrior": {
      "id": "player_warrior",
      "name": "战士",
      "description": "近战物理职业，高生命高防御",
      "class": "melee",
      "rarity": "common",
      
      "base_stats": {
        "hp": 150,
        "mp": 50,
        "atk": 15,
        "def": 12,
        "spd": 100,
        "crit_rate": 0.05,
        "crit_damage": 1.5
      },
      
      "growth_per_level": {
        "hp": 12,
        "mp": 3,
        "atk": 2.5,
        "def": 1.8,
        "spd": 0.5
      },
      
      "starting_skills": ["skill_slash", "skill_block"],
      "skill_tree": "warrior_tree",
      
      "visual": {
        "sprite_sheet": "res://assets/characters/warrior.png",
        "animations": {
          "idle": {"frames": [0, 1, 2, 3], "fps": 8},
          "run": {"frames": [4, 5, 6, 7, 8, 9], "fps": 12},
          "attack": {"frames": [10, 11, 12, 13], "fps": 15},
          "hurt": {"frames": [14, 15], "fps": 10},
          "death": {"frames": [16, 17, 18, 19], "fps": 8}
        }
      }
    }
  }
}
```

---

## 2. 敌人配置模板

### enemies.json

```json
{
  "$schema": "enemy_schema.json",
  "version": "1.0.0",
  "enemies": {
    "slime_green": {
      "id": "slime_green",
      "name": "绿史莱姆",
      "description": "最基础的敌人",
      "type": "mob",
      "element": "none",
      
      "base_level": 1,
      "stats": {
        "hp": 50,
        "atk": 8,
        "def": 2,
        "spd": 80
      },
      
      "scaling": {
        "hp_per_level": 5,
        "atk_per_level": 1,
        "def_per_level": 0.5
      },
      
      "behavior": {
        "ai_type": "simple_chase",
        "detection_range": 150,
        "attack_range": 30,
        "patrol_enabled": true,
        "patrol_range": 100
      },
      
      "attacks": [
        {
          "id": "slime_bounce",
          "name": "弹跳攻击",
          "damage_multiplier": 1.0,
          "cooldown": 2.0,
          "range": 30
        }
      ],
      
      "rewards": {
        "exp": 10,
        "gold": [5, 10],
        "loot_table": "loot_slime"
      },
      
      "visual": {
        "sprite": "res://assets/enemies/slime_green.png",
        "scale": 1.0,
        "color_modulate": "#FFFFFF"
      }
    },
    
    "boss_forest_guardian": {
      "id": "boss_forest_guardian",
      "name": "森林守护者",
      "description": "第一章Boss",
      "type": "boss",
      "element": "earth",
      
      "base_level": 10,
      "stats": {
        "hp": 2000,
        "atk": 25,
        "def": 15,
        "spd": 90
      },
      
      "phases": [
        {
          "hp_threshold": 1.0,
          "name": "Phase 1",
          "attacks": ["ground_slam", "vine_whip"],
          "behavior_modifier": {}
        },
        {
          "hp_threshold": 0.5,
          "name": "Phase 2 - 狂暴",
          "attacks": ["ground_slam", "vine_whip", "root_trap"],
          "behavior_modifier": {
            "atk_multiplier": 1.3,
            "spd_multiplier": 1.2
          }
        }
      ],
      
      "rewards": {
        "exp": 500,
        "gold": [200, 300],
        "guaranteed_drops": ["boss_trophy_forest"],
        "loot_table": "loot_boss_forest"
      }
    }
  }
}
```

---

## 3. 物品配置模板

### items.json

```json
{
  "$schema": "item_schema.json",
  "version": "1.0.0",
  "items": {
    "sword_iron": {
      "id": "sword_iron",
      "name": "铁剑",
      "description": "普通的铁制长剑",
      "type": "weapon",
      "subtype": "sword",
      "rarity": "common",
      
      "stats": {
        "atk": 10
      },
      
      "requirements": {
        "level": 1,
        "class": ["warrior", "knight"]
      },
      
      "price": {
        "buy": 500,
        "sell": 100
      },
      
      "visual": {
        "icon": "res://assets/icons/sword_iron.png",
        "world_sprite": "res://assets/items/sword_iron.png"
      },
      
      "stackable": false,
      "max_stack": 1
    },
    
    "potion_health_small": {
      "id": "potion_health_small",
      "name": "小型生命药水",
      "description": "恢复50点生命值",
      "type": "consumable",
      "subtype": "potion",
      "rarity": "common",
      
      "effect": {
        "type": "heal",
        "value": 50,
        "is_percent": false
      },
      
      "cooldown": 3.0,
      
      "price": {
        "buy": 100,
        "sell": 20
      },
      
      "stackable": true,
      "max_stack": 99
    },
    
    "material_iron_ore": {
      "id": "material_iron_ore",
      "name": "铁矿石",
      "description": "可用于锻造的铁矿石",
      "type": "material",
      "subtype": "ore",
      "rarity": "common",
      
      "price": {
        "buy": 50,
        "sell": 10
      },
      
      "stackable": true,
      "max_stack": 999
    }
  }
}
```

---

## 4. 技能配置模板

### skills.json

```json
{
  "$schema": "skill_schema.json",
  "version": "1.0.0",
  "skills": {
    "skill_slash": {
      "id": "skill_slash",
      "name": "斩击",
      "description": "向前方挥砍，造成{damage}%攻击力的物理伤害",
      "type": "active",
      "category": "attack",
      "element": "physical",
      
      "cost": {
        "mp": 0,
        "cooldown": 0
      },
      
      "targeting": {
        "type": "melee",
        "range": 50,
        "angle": 60,
        "max_targets": 3
      },
      
      "effects": [
        {
          "type": "damage",
          "damage_type": "physical",
          "multiplier": 1.0,
          "base_damage": 0
        }
      ],
      
      "animation": "attack_slash",
      "sound": "sfx_slash",
      
      "upgrades": [
        {"level": 2, "effect_change": {"multiplier": 1.1}},
        {"level": 3, "effect_change": {"multiplier": 1.2}},
        {"level": 4, "effect_change": {"max_targets": 4}},
        {"level": 5, "effect_change": {"multiplier": 1.5}}
      ]
    },
    
    "skill_fireball": {
      "id": "skill_fireball",
      "name": "火球术",
      "description": "发射一枚火球，造成{damage}%攻击力的火焰伤害，并有{burn_chance}%几率施加灼烧",
      "type": "active",
      "category": "attack",
      "element": "fire",
      
      "cost": {
        "mp": 15,
        "cooldown": 3.0
      },
      
      "targeting": {
        "type": "projectile",
        "range": 300,
        "projectile_speed": 400,
        "projectile_scene": "res://scenes/projectiles/fireball.tscn"
      },
      
      "effects": [
        {
          "type": "damage",
          "damage_type": "magical",
          "element": "fire",
          "multiplier": 1.5
        },
        {
          "type": "apply_status",
          "status": "burning",
          "chance": 0.3,
          "duration": 3.0
        }
      ]
    },
    
    "skill_heal": {
      "id": "skill_heal",
      "name": "治愈术",
      "description": "恢复{heal}%最大生命值",
      "type": "active",
      "category": "support",
      
      "cost": {
        "mp": 20,
        "cooldown": 10.0
      },
      
      "targeting": {
        "type": "self"
      },
      
      "effects": [
        {
          "type": "heal",
          "value": 0.2,
          "is_percent": true
        }
      ]
    }
  }
}
```

---

## 5. 关卡配置模板

### levels.json

```json
{
  "$schema": "level_schema.json",
  "version": "1.0.0",
  "worlds": {
    "world_1": {
      "id": "world_1",
      "name": "初始之地",
      "description": "游戏开始的地方",
      "unlock_requirements": [],
      "levels": ["1-1", "1-2", "1-3", "1-B"]
    }
  },
  "levels": {
    "1-1": {
      "id": "1-1",
      "name": "觉醒之村",
      "world": "world_1",
      "type": "tutorial",
      
      "scene_path": "res://scenes/levels/1-1.tscn",
      
      "unlock_requirements": [],
      
      "objectives": {
        "main": {
          "type": "reach_exit",
          "description": "到达村庄出口"
        },
        "secondary": [
          {
            "id": "collect_coins",
            "type": "collect",
            "target": "coin",
            "count": 10,
            "reward": {"gold": 100}
          }
        ]
      },
      
      "star_conditions": [
        {"condition": "complete", "description": "完成关卡"},
        {"condition": "collect_all", "target": "coin", "description": "收集所有金币"},
        {"condition": "no_damage", "description": "无伤通关"}
      ],
      
      "enemy_spawns": [
        {
          "enemy_id": "slime_green",
          "position": [500, 300],
          "spawn_trigger": "on_enter"
        }
      ],
      
      "item_placements": [
        {
          "item_id": "potion_health_small",
          "position": [200, 350]
        }
      ],
      
      "checkpoints": [
        {"id": "cp_1", "position": [600, 300]}
      ],
      
      "rewards": {
        "first_clear": {
          "exp": 100,
          "gold": 200,
          "items": ["sword_wooden"]
        },
        "repeat_clear": {
          "exp": 20,
          "gold": 50
        }
      },
      
      "estimated_duration": 5,
      "difficulty": 1
    }
  }
}
```

---

## 6. 掉落表配置模板

### loot_tables.json

```json
{
  "$schema": "loot_table_schema.json",
  "version": "1.0.0",
  "loot_tables": {
    "loot_slime": {
      "id": "loot_slime",
      "guaranteed": [
        {"item": "gold", "amount": [5, 10]}
      ],
      "random": [
        {"item": "slime_gel", "weight": 50, "amount": [1, 2]},
        {"item": "potion_health_small", "weight": 20, "amount": 1},
        {"item": "gem_green", "weight": 5, "amount": 1}
      ],
      "rare": {
        "chance": 0.01,
        "items": [
          {"item": "slime_crown", "weight": 100}
        ]
      }
    },
    
    "loot_boss_forest": {
      "id": "loot_boss_forest",
      "guaranteed": [
        {"item": "gold", "amount": [200, 300]},
        {"item": "boss_material_forest", "amount": [2, 3]}
      ],
      "random": [
        {"item": "equipment_forest_sword", "weight": 30},
        {"item": "equipment_forest_armor", "weight": 30},
        {"item": "skill_book_nature", "weight": 20},
        {"item": "rare_gem", "weight": 20}
      ]
    },
    
    "loot_chest_common": {
      "id": "loot_chest_common",
      "roll_count": [2, 3],
      "random": [
        {"item": "gold", "weight": 40, "amount": [50, 100]},
        {"item": "potion_health_small", "weight": 30, "amount": [1, 3]},
        {"item": "material_iron_ore", "weight": 20, "amount": [2, 5]},
        {"item": "equipment_random_common", "weight": 10}
      ]
    }
  }
}
```

---

## 7. 状态效果配置模板

### status_effects.json

```json
{
  "$schema": "status_effect_schema.json",
  "version": "1.0.0",
  "status_effects": {
    "burning": {
      "id": "burning",
      "name": "灼烧",
      "description": "每秒受到火焰伤害",
      "type": "debuff",
      "category": "dot",
      "element": "fire",
      
      "duration": 3.0,
      "tick_interval": 1.0,
      
      "effects": [
        {
          "type": "damage_over_time",
          "damage_type": "magical",
          "element": "fire",
          "value": 0.03,
          "is_percent_max_hp": true
        }
      ],
      
      "stacking": {
        "type": "refresh_duration",
        "max_stacks": 1
      },
      
      "visual": {
        "particle": "res://particles/burning.tscn",
        "color_modulate": "#FF6600"
      }
    },
    
    "attack_up": {
      "id": "attack_up",
      "name": "攻击提升",
      "description": "攻击力提升{value}%",
      "type": "buff",
      "category": "stat_modifier",
      
      "duration": 10.0,
      
      "effects": [
        {
          "type": "stat_modifier",
          "stat": "atk",
          "modifier_type": "percent",
          "value": 0.3
        }
      ],
      
      "stacking": {
        "type": "stack_duration",
        "max_stacks": 3
      },
      
      "visual": {
        "icon": "res://assets/icons/buff_attack.png",
        "particle": "res://particles/buff_attack.tscn"
      }
    },
    
    "stunned": {
      "id": "stunned",
      "name": "眩晕",
      "description": "无法行动",
      "type": "debuff",
      "category": "control",
      
      "duration": 2.0,
      
      "effects": [
        {
          "type": "disable",
          "disable_movement": true,
          "disable_attack": true,
          "disable_skills": true
        }
      ],
      
      "boss_resistance": {
        "duration_reduction": 0.7,
        "immunity_after": 3
      }
    }
  }
}
```

---

## 8. 经济配置模板

### economy.json

```json
{
  "$schema": "economy_schema.json",
  "version": "1.0.0",
  
  "currencies": {
    "gold": {
      "id": "gold",
      "name": "金币",
      "icon": "res://assets/icons/gold.png",
      "max_amount": 9999999
    },
    "gem": {
      "id": "gem",
      "name": "宝石",
      "icon": "res://assets/icons/gem.png",
      "max_amount": 99999,
      "premium": true
    }
  },
  
  "shops": {
    "shop_general": {
      "id": "shop_general",
      "name": "杂货店",
      "currency": "gold",
      "items": [
        {"item": "potion_health_small", "stock": -1},
        {"item": "potion_health_medium", "stock": -1},
        {"item": "potion_mana_small", "stock": -1},
        {"item": "teleport_scroll", "stock": 5, "restock_days": 1}
      ]
    }
  },
  
  "upgrade_costs": {
    "equipment_enhance": {
      "formula": "base * (1.5 ^ level)",
      "base": 100,
      "max_level": 15
    },
    "skill_upgrade": {
      "costs": [0, 500, 1000, 2000, 5000]
    }
  },
  
  "daily_income_target": {
    "early_game": {"gold": 2000, "exp": 1000},
    "mid_game": {"gold": 5000, "exp": 5000},
    "late_game": {"gold": 10000, "exp": 15000}
  }
}
```

---

## 使用说明

### 1. 创建新配置文件

```gdscript
# 在代码中加载配置
var config = load_json("res://data/characters.json")
var warrior_data = config.characters.player_warrior
```

### 2. 扩展配置

添加新条目时，确保：
1. ID唯一
2. 必填字段完整
3. 数值在合理范围
4. 引用资源路径正确

### 3. 验证配置

使用 JSON Schema 验证配置文件格式：

```bash
# 验证配置文件
npx ajv validate -s schemas/character_schema.json -d data/characters.json
```

---

## 验收标准

1. **格式正确** - 所有 JSON 文件语法正确
2. **引用有效** - 所有资源路径存在
3. **ID唯一** - 无重复 ID
4. **数值合理** - 数值在设计范围内
5. **字段完整** - 必填字段无缺失
