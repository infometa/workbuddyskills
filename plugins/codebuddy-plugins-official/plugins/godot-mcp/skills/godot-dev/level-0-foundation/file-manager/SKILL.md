---
name: file-manager
description: >
  文件系统操作技能。提供项目文件的读取、写入、复制、移动等操作能力。
  支持 Godot 项目的资源文件管理。
version: 1.0.0
dependencies:
  - godot-core
triggers:
  - pattern: "文件|目录|文件夹|创建文件|读取文件|复制|移动"
inputs:
  - name: path
    type: string
    required: true
    description: 文件或目录路径（支持 res:// 或绝对路径）
outputs:
  - name: result
    type: object
    description: 操作结果
---

# 文件管理技能

提供 Godot 项目文件系统的管理能力。

## 路径格式

### Godot 资源路径
- 格式：`res://path/to/file`
- 映射到项目根目录
- 示例：`res://scripts/player.gd` → `{project_root}/scripts/player.gd`

### 用户数据路径
- 格式：`user://path/to/file`
- 映射到用户数据目录
- Windows: `%APPDATA%/Godot/app_userdata/{project_name}/`

### 绝对路径
- 完整的文件系统路径
- 示例：`D:/Projects/MyGame/assets/texture.png`

---

## 文件操作

### 创建文件

```gdscript
# 创建空文件
func create_file(path: String) -> bool:
    var file = FileAccess.open(path, FileAccess.WRITE)
    if file:
        file.close()
        return true
    return false

# 创建带内容的文件
func create_file_with_content(path: String, content: String) -> bool:
    var file = FileAccess.open(path, FileAccess.WRITE)
    if file:
        file.store_string(content)
        file.close()
        return true
    return false
```

### 读取文件

```gdscript
func read_file(path: String) -> String:
    var file = FileAccess.open(path, FileAccess.READ)
    if file:
        var content = file.get_as_text()
        file.close()
        return content
    return ""
```

### 文件存在检查

```gdscript
func file_exists(path: String) -> bool:
    return FileAccess.file_exists(path)

func dir_exists(path: String) -> bool:
    return DirAccess.dir_exists_absolute(path)
```

### 目录操作

```gdscript
# 创建目录（递归）
func make_dir_recursive(path: String) -> bool:
    var dir = DirAccess.open("res://")
    if dir:
        return dir.make_dir_recursive(path) == OK
    return false

# 列出目录内容
func list_directory(path: String) -> Array:
    var files = []
    var dir = DirAccess.open(path)
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            files.append({
                "name": file_name,
                "is_dir": dir.current_is_dir()
            })
            file_name = dir.get_next()
        dir.list_dir_end()
    return files
```

### 复制和移动

```gdscript
# 复制文件
func copy_file(from: String, to: String) -> bool:
    var dir = DirAccess.open("res://")
    if dir:
        return dir.copy(from, to) == OK
    return false

# 移动/重命名文件
func move_file(from: String, to: String) -> bool:
    var dir = DirAccess.open("res://")
    if dir:
        return dir.rename(from, to) == OK
    return false

# 删除文件
func remove_file(path: String) -> bool:
    var dir = DirAccess.open("res://")
    if dir:
        return dir.remove(path) == OK
    return false
```

---

## 标准项目目录结构

创建新项目时，建议创建以下目录结构：

```
res://
├── scripts/
│   ├── autoload/          # 自动加载单例
│   ├── core/              # 核心框架
│   ├── entities/          # 游戏实体
│   ├── systems/           # 游戏系统
│   ├── ui/                # UI 脚本
│   └── data/              # 数据类
├── scenes/
│   ├── main/              # 主场景
│   ├── levels/            # 关卡场景
│   ├── ui/                # UI 场景
│   └── prefabs/           # 预制体
├── resources/             # 自定义资源 (.tres)
├── assets/
│   ├── textures/          # 贴图
│   ├── models/            # 3D 模型
│   ├── animations/        # 动画
│   ├── audio/
│   │   ├── music/         # 音乐
│   │   └── sfx/           # 音效
│   └── fonts/             # 字体
├── config/
│   ├── schemas/           # JSON Schema
│   └── data/              # 配置数据 JSON
└── docs/
    └── design/            # 设计文档
```

### 初始化项目目录

```gdscript
func init_project_structure() -> void:
    var dirs = [
        "res://scripts/autoload",
        "res://scripts/core",
        "res://scripts/entities",
        "res://scripts/systems",
        "res://scripts/ui",
        "res://scripts/data",
        "res://scenes/main",
        "res://scenes/levels",
        "res://scenes/ui",
        "res://scenes/prefabs",
        "res://resources",
        "res://assets/textures",
        "res://assets/models",
        "res://assets/animations",
        "res://assets/audio/music",
        "res://assets/audio/sfx",
        "res://assets/fonts",
        "res://config/schemas",
        "res://config/data",
        "res://docs/design"
    ]
    
    for dir_path in dirs:
        make_dir_recursive(dir_path)
```

---

## JSON 文件操作

### 读取 JSON

```gdscript
func load_json(path: String) -> Variant:
    var file = FileAccess.open(path, FileAccess.READ)
    if file:
        var json_string = file.get_as_text()
        file.close()
        var json = JSON.new()
        var error = json.parse(json_string)
        if error == OK:
            return json.data
        else:
            push_error("JSON parse error at line %d: %s" % [json.get_error_line(), json.get_error_message()])
    return null
```

### 保存 JSON

```gdscript
func save_json(path: String, data: Variant, indent: String = "\t") -> bool:
    var file = FileAccess.open(path, FileAccess.WRITE)
    if file:
        var json_string = JSON.stringify(data, indent)
        file.store_string(json_string)
        file.close()
        return true
    return false
```

---

## 资源扫描

### 扫描指定类型文件

```gdscript
func scan_files_by_extension(root_path: String, extension: String) -> Array:
    var results = []
    var dir = DirAccess.open(root_path)
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            var full_path = root_path.path_join(file_name)
            if dir.current_is_dir() and not file_name.begins_with("."):
                results.append_array(scan_files_by_extension(full_path, extension))
            elif file_name.ends_with(extension):
                results.append(full_path)
            file_name = dir.get_next()
        dir.list_dir_end()
    return results

# 使用示例
var all_scripts = scan_files_by_extension("res://scripts", ".gd")
var all_scenes = scan_files_by_extension("res://scenes", ".tscn")
var all_configs = scan_files_by_extension("res://config", ".json")
```

---

## 注意事项

1. **路径分隔符**：Godot 统一使用 `/`，即使在 Windows 上
2. **资源导入**：新增资源文件后，Godot 会自动生成 `.import` 文件
3. **编辑器刷新**：文件操作后可能需要调用 `EditorInterface.get_resource_filesystem().scan()` 刷新
4. **权限问题**：`res://` 路径在导出后的游戏中只读，运行时写入使用 `user://`
