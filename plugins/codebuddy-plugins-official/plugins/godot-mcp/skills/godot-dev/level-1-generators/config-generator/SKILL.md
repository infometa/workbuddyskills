---
name: config-generator
description: >
  配置表生成技能。生成符合 JSON Schema 规范的配置文件，
  支持物品、关卡、角色等游戏数据的结构化配置。
version: 1.0.0
dependencies:
  - godot-core
  - file-manager
triggers:
  - pattern: "配置表|配置文件|JSON配置|数据表|物品表|关卡配置"
inputs:
  - name: config_type
    type: string
    enum: ["items", "levels", "characters", "enemies", "skills", "dialogues", "quests", "shops"]
    required: true
  - name: entries
    type: array
    required: false
outputs:
  - name: config_path
    type: string
    description: 生成的配置文件路径
  - name: schema_path
    type: string
    description: 对应的 Schema 文件路径
---

# 配置表生成技能

生成结构化的 JSON 配置文件，实现逻辑与数值分离。

## 配置表系统架构

```
config/
├── schemas/                  # JSON Schema 定义
│   ├── base_schema.json      # 基础类型定义
│   ├── items.schema.json
│   ├── levels.schema.json
│   ├── characters.schema.json
│   ├── enemies.schema.json
│   ├── skills.schema.json
│   ├── dialogues.schema.json
│   └── quests.schema.json
│
├── data/                     # 实际配置数据
│   ├── items.json
│   ├── levels.json
│   ├── characters.json
│   ├── enemies.json
│   ├── skills.json
│   ├── dialogues.json
│   └── quests.json
│
└── validator/                # 验证工具
    └── config_validator.gd
```

---

## Schema 定义

### 基础 Schema (base_schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "base_schema.json",
  "definitions": {
    "id": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "minLength": 1,
      "maxLength": 64
    },
    "localized_string": {
      "type": "object",
      "properties": {
        "key": { "type": "string" },
        "default": { "type": "string" }
      },
      "required": ["key", "default"]
    },
    "resource_path": {
      "type": "string",
      "pattern": "^res://.*$"
    },
    "color": {
      "type": "string",
      "pattern": "^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$"
    },
    "vector2": {
      "type": "object",
      "properties": {
        "x": { "type": "number" },
        "y": { "type": "number" }
      },
      "required": ["x", "y"]
    },
    "vector3": {
      "type": "object",
      "properties": {
        "x": { "type": "number" },
        "y": { "type": "number" },
        "z": { "type": "number" }
      },
      "required": ["x", "y", "z"]
    },
    "range": {
      "type": "object",
      "properties": {
        "min": { "type": "number" },
        "max": { "type": "number" }
      },
      "required": ["min", "max"]
    }
  }
}
```

### 物品配置 Schema (items.schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "items.schema.json",
  "title": "Items Configuration",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "name", "type"],
    "properties": {
      "id": {
        "$ref": "base_schema.json#/definitions/id",
        "description": "唯一标识符"
      },
      "name": {
        "$ref": "base_schema.json#/definitions/localized_string",
        "description": "物品名称"
      },
      "description": {
        "$ref": "base_schema.json#/definitions/localized_string",
        "description": "物品描述"
      },
      "type": {
        "type": "string",
        "enum": ["consumable", "equipment", "material", "quest", "key"],
        "description": "物品类型"
      },
      "subtype": {
        "type": "string",
        "description": "子类型（如装备的部位：weapon, helmet, armor...）"
      },
      "rarity": {
        "type": "integer",
        "minimum": 1,
        "maximum": 5,
        "default": 1,
        "description": "稀有度 1-5"
      },
      "icon": {
        "$ref": "base_schema.json#/definitions/resource_path",
        "description": "图标路径"
      },
      "model": {
        "$ref": "base_schema.json#/definitions/resource_path",
        "description": "3D 模型路径"
      },
      "stackable": {
        "type": "boolean",
        "default": true
      },
      "max_stack": {
        "type": "integer",
        "minimum": 1,
        "maximum": 9999,
        "default": 99
      },
      "price": {
        "type": "object",
        "properties": {
          "buy": { "type": "integer", "minimum": 0 },
          "sell": { "type": "integer", "minimum": 0 }
        }
      },
      "effects": {
        "type": "array",
        "items": { "$ref": "#/definitions/effect" }
      },
      "requirements": {
        "type": "object",
        "properties": {
          "level": { "type": "integer", "minimum": 1 },
          "stats": { "type": "object" }
        }
      },
      "stats": {
        "type": "object",
        "description": "装备提供的属性加成"
      },
      "tags": {
        "type": "array",
        "items": { "type": "string" }
      }
    },
    "allOf": [
      {
        "if": { "properties": { "type": { "const": "consumable" } } },
        "then": { "required": ["effects"] }
      },
      {
        "if": { "properties": { "type": { "const": "equipment" } } },
        "then": { "required": ["subtype", "stats"] }
      }
    ]
  },
  "definitions": {
    "effect": {
      "type": "object",
      "required": ["type", "value"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["heal_hp", "heal_mp", "buff", "debuff", "damage", "teleport", "summon"]
        },
        "value": { "type": "number" },
        "duration": { "type": "number", "default": 0 },
        "target": {
          "type": "string",
          "enum": ["self", "enemy", "ally", "all"],
          "default": "self"
        }
      }
    }
  }
}
```

### 关卡配置 Schema (levels.schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "levels.schema.json",
  "title": "Levels Configuration",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "name", "scene_path"],
    "properties": {
      "id": {
        "$ref": "base_schema.json#/definitions/id"
      },
      "name": {
        "$ref": "base_schema.json#/definitions/localized_string"
      },
      "description": {
        "$ref": "base_schema.json#/definitions/localized_string"
      },
      "scene_path": {
        "$ref": "base_schema.json#/definitions/resource_path"
      },
      "chapter": {
        "type": "integer",
        "minimum": 1
      },
      "order": {
        "type": "integer",
        "minimum": 1
      },
      "unlock_requirements": {
        "type": "object",
        "properties": {
          "previous_level": { "type": "string" },
          "player_level": { "type": "integer" },
          "items_required": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "item_id": { "type": "string" },
                "amount": { "type": "integer" }
              }
            }
          }
        }
      },
      "enemies": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "enemy_id": { "type": "string" },
            "count": { "$ref": "base_schema.json#/definitions/range" },
            "spawn_points": {
              "type": "array",
              "items": { "$ref": "base_schema.json#/definitions/vector3" }
            }
          }
        }
      },
      "rewards": {
        "type": "object",
        "properties": {
          "exp": { "type": "integer" },
          "gold": { "$ref": "base_schema.json#/definitions/range" },
          "items": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "item_id": { "type": "string" },
                "amount": { "type": "integer" },
                "drop_rate": { "type": "number", "minimum": 0, "maximum": 1 }
              }
            }
          }
        }
      },
      "time_limit": {
        "type": "integer",
        "description": "时间限制（秒），0 表示无限制"
      },
      "objectives": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "enum": ["kill_all", "kill_count", "survive", "collect", "reach_point", "protect"]
            },
            "target": { "type": "string" },
            "count": { "type": "integer" },
            "optional": { "type": "boolean", "default": false }
          }
        }
      },
      "environment": {
        "type": "object",
        "properties": {
          "music": { "$ref": "base_schema.json#/definitions/resource_path" },
          "ambience": { "$ref": "base_schema.json#/definitions/resource_path" },
          "lighting": { "type": "string", "enum": ["day", "night", "dungeon", "custom"] }
        }
      }
    }
  }
}
```

### 角色配置 Schema (characters.schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "characters.schema.json",
  "title": "Characters Configuration",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "name", "class", "base_stats"],
    "properties": {
      "id": { "$ref": "base_schema.json#/definitions/id" },
      "name": { "$ref": "base_schema.json#/definitions/localized_string" },
      "class": {
        "type": "string",
        "enum": ["warrior", "mage", "archer", "rogue", "healer"]
      },
      "description": { "$ref": "base_schema.json#/definitions/localized_string" },
      "portrait": { "$ref": "base_schema.json#/definitions/resource_path" },
      "model": { "$ref": "base_schema.json#/definitions/resource_path" },
      "base_stats": {
        "type": "object",
        "required": ["hp", "mp", "attack", "defense", "speed"],
        "properties": {
          "hp": { "type": "integer", "minimum": 1 },
          "mp": { "type": "integer", "minimum": 0 },
          "attack": { "type": "integer", "minimum": 1 },
          "defense": { "type": "integer", "minimum": 0 },
          "speed": { "type": "integer", "minimum": 1 },
          "critical_rate": { "type": "number", "minimum": 0, "maximum": 1 },
          "critical_damage": { "type": "number", "minimum": 1 }
        }
      },
      "growth_rates": {
        "type": "object",
        "description": "每级成长率",
        "properties": {
          "hp": { "type": "number" },
          "mp": { "type": "number" },
          "attack": { "type": "number" },
          "defense": { "type": "number" },
          "speed": { "type": "number" }
        }
      },
      "skills": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "skill_id": { "type": "string" },
            "unlock_level": { "type": "integer" }
          }
        }
      },
      "equipment_slots": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["weapon", "helmet", "armor", "gloves", "boots", "accessory1", "accessory2"]
        }
      }
    }
  }
}
```

### 敌人配置 Schema (enemies.schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "enemies.schema.json",
  "title": "Enemies Configuration",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "name", "type", "stats"],
    "properties": {
      "id": { "$ref": "base_schema.json#/definitions/id" },
      "name": { "$ref": "base_schema.json#/definitions/localized_string" },
      "type": {
        "type": "string",
        "enum": ["normal", "elite", "boss", "miniboss"]
      },
      "model": { "$ref": "base_schema.json#/definitions/resource_path" },
      "stats": {
        "type": "object",
        "required": ["hp", "attack", "defense"],
        "properties": {
          "hp": { "type": "integer" },
          "attack": { "type": "integer" },
          "defense": { "type": "integer" },
          "speed": { "type": "integer" },
          "exp_reward": { "type": "integer" },
          "gold_reward": { "$ref": "base_schema.json#/definitions/range" }
        }
      },
      "level_scaling": {
        "type": "object",
        "description": "属性随等级的缩放系数"
      },
      "behavior": {
        "type": "object",
        "properties": {
          "ai_type": {
            "type": "string",
            "enum": ["aggressive", "defensive", "passive", "patrol", "guard"]
          },
          "detection_range": { "type": "number" },
          "attack_range": { "type": "number" },
          "attack_interval": { "type": "number" }
        }
      },
      "skills": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "skill_id": { "type": "string" },
            "cooldown": { "type": "number" },
            "use_condition": { "type": "string" }
          }
        }
      },
      "drops": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "item_id": { "type": "string" },
            "amount": { "$ref": "base_schema.json#/definitions/range" },
            "drop_rate": { "type": "number", "minimum": 0, "maximum": 1 }
          }
        }
      },
      "resistances": {
        "type": "object",
        "description": "元素/状态抗性"
      },
      "weaknesses": {
        "type": "array",
        "items": { "type": "string" }
      }
    }
  }
}
```

### 技能配置 Schema (skills.schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "skills.schema.json",
  "title": "Skills Configuration",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "name", "type", "effects"],
    "properties": {
      "id": { "$ref": "base_schema.json#/definitions/id" },
      "name": { "$ref": "base_schema.json#/definitions/localized_string" },
      "description": { "$ref": "base_schema.json#/definitions/localized_string" },
      "icon": { "$ref": "base_schema.json#/definitions/resource_path" },
      "type": {
        "type": "string",
        "enum": ["active", "passive", "ultimate"]
      },
      "element": {
        "type": "string",
        "enum": ["physical", "fire", "ice", "lightning", "holy", "dark", "none"]
      },
      "target_type": {
        "type": "string",
        "enum": ["self", "single_enemy", "single_ally", "all_enemies", "all_allies", "area"]
      },
      "cost": {
        "type": "object",
        "properties": {
          "mp": { "type": "integer" },
          "hp": { "type": "integer" },
          "special": { "type": "integer" }
        }
      },
      "cooldown": {
        "type": "number",
        "minimum": 0
      },
      "cast_time": {
        "type": "number",
        "minimum": 0
      },
      "range": {
        "type": "number"
      },
      "area_of_effect": {
        "type": "object",
        "properties": {
          "shape": { "type": "string", "enum": ["circle", "cone", "line", "rectangle"] },
          "size": { "type": "number" }
        }
      },
      "effects": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "enum": ["damage", "heal", "buff", "debuff", "dot", "hot", "knockback", "stun", "summon"]
            },
            "value": { "type": "number" },
            "scaling": {
              "type": "object",
              "properties": {
                "stat": { "type": "string" },
                "ratio": { "type": "number" }
              }
            },
            "duration": { "type": "number" },
            "tick_interval": { "type": "number" }
          }
        }
      },
      "animation": { "$ref": "base_schema.json#/definitions/resource_path" },
      "sound_effect": { "$ref": "base_schema.json#/definitions/resource_path" },
      "visual_effect": { "$ref": "base_schema.json#/definitions/resource_path" }
    }
  }
}
```

---

## 配置数据示例

### items.json 示例

```json
[
  {
    "id": "potion_health_small",
    "name": { "key": "ITEM_HEALTH_POTION_SMALL", "default": "小型生命药水" },
    "description": { "key": "ITEM_HEALTH_POTION_SMALL_DESC", "default": "恢复少量生命值" },
    "type": "consumable",
    "rarity": 1,
    "icon": "res://assets/textures/items/potion_health_small.png",
    "stackable": true,
    "max_stack": 99,
    "price": { "buy": 50, "sell": 25 },
    "effects": [
      { "type": "heal_hp", "value": 50, "target": "self" }
    ],
    "tags": ["consumable", "healing", "common"]
  },
  {
    "id": "sword_iron",
    "name": { "key": "ITEM_SWORD_IRON", "default": "铁剑" },
    "description": { "key": "ITEM_SWORD_IRON_DESC", "default": "普通的铁制长剑" },
    "type": "equipment",
    "subtype": "weapon",
    "rarity": 2,
    "icon": "res://assets/textures/items/sword_iron.png",
    "model": "res://assets/models/items/sword_iron.glb",
    "stackable": false,
    "price": { "buy": 200, "sell": 100 },
    "requirements": { "level": 5 },
    "stats": {
      "attack": 15,
      "critical_rate": 0.05
    },
    "tags": ["weapon", "sword", "iron"]
  }
]
```

---

## 配置验证器

### GDScript 验证器

```gdscript
## 配置表验证器
class_name ConfigValidator
extends RefCounted

var _schemas: Dictionary = {}
var _errors: Array = []

func load_schemas(schema_dir: String = "res://config/schemas/") -> void:
    var dir = DirAccess.open(schema_dir)
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if file_name.ends_with(".schema.json"):
                var schema_path = schema_dir.path_join(file_name)
                var schema_name = file_name.replace(".schema.json", "")
                _schemas[schema_name] = _load_json(schema_path)
            file_name = dir.get_next()
        dir.list_dir_end()

func validate_config(config_name: String, data: Array) -> Dictionary:
    _errors.clear()
    
    if not _schemas.has(config_name):
        return {"valid": false, "errors": ["Schema not found: " + config_name]}
    
    var schema = _schemas[config_name]
    
    for i in range(data.size()):
        var item = data[i]
        _validate_item(item, schema, "[%d]" % i)
    
    return {
        "valid": _errors.is_empty(),
        "errors": _errors.duplicate()
    }

func _validate_item(item: Dictionary, schema: Dictionary, path: String) -> void:
    var item_schema = schema.get("items", {})
    var required = item_schema.get("required", [])
    var properties = item_schema.get("properties", {})
    
    # 检查必需字段
    for field in required:
        if not item.has(field):
            _errors.append("%s: Missing required field '%s'" % [path, field])
    
    # 检查每个字段的类型和约束
    for key in item.keys():
        if properties.has(key):
            var prop_schema = properties[key]
            _validate_property(item[key], prop_schema, "%s.%s" % [path, key])

func _validate_property(value: Variant, schema: Dictionary, path: String) -> void:
    var expected_type = schema.get("type", "")
    
    # 类型检查
    match expected_type:
        "string":
            if typeof(value) != TYPE_STRING:
                _errors.append("%s: Expected string, got %s" % [path, type_string(typeof(value))])
            elif schema.has("pattern"):
                var regex = RegEx.new()
                regex.compile(schema.pattern)
                if not regex.search(value):
                    _errors.append("%s: Value does not match pattern" % path)
            if schema.has("enum") and value not in schema.enum:
                _errors.append("%s: Value must be one of %s" % [path, schema.enum])
        "integer", "number":
            if typeof(value) not in [TYPE_INT, TYPE_FLOAT]:
                _errors.append("%s: Expected number, got %s" % [path, type_string(typeof(value))])
            else:
                if schema.has("minimum") and value < schema.minimum:
                    _errors.append("%s: Value must be >= %s" % [path, schema.minimum])
                if schema.has("maximum") and value > schema.maximum:
                    _errors.append("%s: Value must be <= %s" % [path, schema.maximum])
        "boolean":
            if typeof(value) != TYPE_BOOL:
                _errors.append("%s: Expected boolean" % path)
        "array":
            if typeof(value) != TYPE_ARRAY:
                _errors.append("%s: Expected array" % path)
        "object":
            if typeof(value) != TYPE_DICTIONARY:
                _errors.append("%s: Expected object" % path)

func _load_json(path: String) -> Variant:
    var file = FileAccess.open(path, FileAccess.READ)
    if file:
        var json = JSON.new()
        json.parse(file.get_as_text())
        file.close()
        return json.data
    return null
```

---

## 配置管理器

```gdscript
## 配置管理器 - Autoload
class_name ConfigManager
extends Node

var _configs: Dictionary = {}
var _validator: ConfigValidator

func _ready() -> void:
    _validator = ConfigValidator.new()
    _validator.load_schemas()
    _load_all_configs()

func _load_all_configs() -> void:
    var config_files = [
        "items",
        "levels", 
        "characters",
        "enemies",
        "skills"
    ]
    
    for config_name in config_files:
        var path = "res://config/data/%s.json" % config_name
        if FileAccess.file_exists(path):
            var data = _load_json(path)
            if data:
                var result = _validator.validate_config(config_name, data)
                if result.valid:
                    _configs[config_name] = _index_by_id(data)
                else:
                    push_error("Config validation failed for %s: %s" % [config_name, result.errors])

func _index_by_id(data: Array) -> Dictionary:
    var indexed = {}
    for item in data:
        if item.has("id"):
            indexed[item.id] = item
    return indexed

func get_item(id: String) -> Dictionary:
    return _configs.get("items", {}).get(id, {})

func get_level(id: String) -> Dictionary:
    return _configs.get("levels", {}).get(id, {})

func get_character(id: String) -> Dictionary:
    return _configs.get("characters", {}).get(id, {})

func get_enemy(id: String) -> Dictionary:
    return _configs.get("enemies", {}).get(id, {})

func get_skill(id: String) -> Dictionary:
    return _configs.get("skills", {}).get(id, {})

func get_all(config_name: String) -> Dictionary:
    return _configs.get(config_name, {})

func _load_json(path: String) -> Variant:
    var file = FileAccess.open(path, FileAccess.READ)
    if file:
        var json = JSON.new()
        if json.parse(file.get_as_text()) == OK:
            file.close()
            return json.data
        file.close()
    return null
```

---

## 使用示例

### 生成物品配置

```
生成一组 RPG 物品配置：
- 3 种恢复药水（小/中/大）
- 2 把武器（铁剑、魔法杖）
- 1 套防具（皮甲）
```

### 生成关卡配置

```
生成第一章的 5 个关卡配置，难度递增：
- 第 1 关：新手教程，3 只史莱姆
- 第 2 关：森林入口，5 只哥布林
- ...
```
