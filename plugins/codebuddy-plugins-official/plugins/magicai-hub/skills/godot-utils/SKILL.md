---
name: godot-utils
description: GDScript 工具函数库。提供常用的辅助函数，可直接复制到项目中使用，或通过 Autoload 全局访问。
version: 1.0.0
---

# GDScript 工具函数库

> **用途**：提供可复用的 GDScript 工具函数，加速游戏开发  
> **版本**：v1.0 · 2026-04-24  
> **适用**：Godot 4.x

---

## 目录

1. [数学工具](#1-数学工具)
2. [向量工具](#2-向量工具)
3. [随机工具](#3-随机工具)
4. [时间工具](#4-时间工具)
5. [字符串工具](#5-字符串工具)
6. [数组工具](#6-数组工具)
7. [节点工具](#7-节点工具)
8. [文件工具](#8-文件工具)
9. [调试工具](#9-调试工具)
10. [缓动工具](#10-缓动工具)

---

## 使用方式

### 方式 1：复制到项目
直接复制需要的函数到你的脚本中。

### 方式 2：Autoload
创建 `res://autoload/utils.gd`，在项目设置中注册为 Autoload（名称 `Utils`），然后全局调用 `Utils.xxx()`。

---

## 1. 数学工具

```gdscript
class_name MathUtils

## 线性插值，支持 clamp
static func lerp_clamped(from: float, to: float, weight: float) -> float:
    return lerpf(from, to, clampf(weight, 0.0, 1.0))

## 平滑阻尼（类似 Unity 的 SmoothDamp）
static func smooth_damp(current: float, target: float, velocity: float, smooth_time: float, delta: float) -> Array:
    var omega := 2.0 / smooth_time
    var x := omega * delta
    var exp_factor := 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
    var change := current - target
    var temp := (velocity + omega * change) * delta
    var new_velocity := (velocity - omega * temp) * exp_factor
    var new_value := target + (change + temp) * exp_factor
    return [new_value, new_velocity]

## 重映射值从一个范围到另一个范围
static func remap(value: float, from_min: float, from_max: float, to_min: float, to_max: float) -> float:
    return to_min + (value - from_min) * (to_max - to_min) / (from_max - from_min)

## 重映射并 clamp
static func remap_clamped(value: float, from_min: float, from_max: float, to_min: float, to_max: float) -> float:
    var t := clampf((value - from_min) / (from_max - from_min), 0.0, 1.0)
    return lerpf(to_min, to_max, t)

## 角度归一化到 [-180, 180]
static func normalize_angle(degrees: float) -> float:
    degrees = fmod(degrees + 180.0, 360.0)
    if degrees < 0:
        degrees += 360.0
    return degrees - 180.0

## 角度归一化到 [0, 360]
static func normalize_angle_positive(degrees: float) -> float:
    degrees = fmod(degrees, 360.0)
    if degrees < 0:
        degrees += 360.0
    return degrees

## 弧度归一化到 [-PI, PI]
static func normalize_radians(radians: float) -> float:
    radians = fmod(radians + PI, TAU)
    if radians < 0:
        radians += TAU
    return radians - PI

## 检查两个浮点数是否近似相等
static func approx_equal(a: float, b: float, epsilon := 0.0001) -> bool:
    return absf(a - b) < epsilon

## 检查值是否在范围内
static func in_range(value: float, min_val: float, max_val: float) -> bool:
    return value >= min_val and value <= max_val

## 取模（支持负数，结果总是正数）
static func positive_mod(a: int, b: int) -> int:
    return ((a % b) + b) % b

## 取模浮点版
static func positive_fmod(a: float, b: float) -> float:
    return fmod(fmod(a, b) + b, b)
```

---

## 2. 向量工具

```gdscript
class_name VectorUtils

## Vector2 平滑阻尼
static func smooth_damp_v2(current: Vector2, target: Vector2, velocity: Vector2, smooth_time: float, delta: float) -> Array:
    var result_x := MathUtils.smooth_damp(current.x, target.x, velocity.x, smooth_time, delta)
    var result_y := MathUtils.smooth_damp(current.y, target.y, velocity.y, smooth_time, delta)
    return [Vector2(result_x[0], result_y[0]), Vector2(result_x[1], result_y[1])]

## Vector3 平滑阻尼
static func smooth_damp_v3(current: Vector3, target: Vector3, velocity: Vector3, smooth_time: float, delta: float) -> Array:
    var result_x := MathUtils.smooth_damp(current.x, target.x, velocity.x, smooth_time, delta)
    var result_y := MathUtils.smooth_damp(current.y, target.y, velocity.y, smooth_time, delta)
    var result_z := MathUtils.smooth_damp(current.z, target.z, velocity.z, smooth_time, delta)
    return [Vector3(result_x[0], result_y[0], result_z[0]), Vector3(result_x[1], result_y[1], result_z[1])]

## 获取 Vector2 的垂直向量（顺时针）
static func perpendicular_cw(v: Vector2) -> Vector2:
    return Vector2(v.y, -v.x)

## 获取 Vector2 的垂直向量（逆时针）
static func perpendicular_ccw(v: Vector2) -> Vector2:
    return Vector2(-v.y, v.x)

## 将 Vector2 旋转指定角度（弧度）
static func rotate_v2(v: Vector2, radians: float) -> Vector2:
    return v.rotated(radians)

## 计算两个向量之间的有符号角度（弧度，-PI 到 PI）
static func signed_angle(from: Vector2, to: Vector2) -> float:
    return atan2(from.cross(to), from.dot(to))

## 3D 世界坐标转 2D 俯视坐标 (Y 轴向上时)
static func world_to_top_down(world_pos: Vector3) -> Vector2:
    return Vector2(world_pos.x, world_pos.z)

## 2D 俯视坐标转 3D 世界坐标 (指定高度)
static func top_down_to_world(pos_2d: Vector2, height := 0.0) -> Vector3:
    return Vector3(pos_2d.x, height, pos_2d.y)

## 计算点到线段的最近点
static func closest_point_on_segment(point: Vector2, seg_start: Vector2, seg_end: Vector2) -> Vector2:
    var seg := seg_end - seg_start
    var len_sq := seg.length_squared()
    if len_sq < 0.0001:
        return seg_start
    var t := clampf((point - seg_start).dot(seg) / len_sq, 0.0, 1.0)
    return seg_start + seg * t

## 计算点到线段的距离
static func distance_to_segment(point: Vector2, seg_start: Vector2, seg_end: Vector2) -> float:
    return point.distance_to(closest_point_on_segment(point, seg_start, seg_end))

## 限制向量长度
static func clamp_length(v: Vector2, max_length: float) -> Vector2:
    if v.length_squared() > max_length * max_length:
        return v.normalized() * max_length
    return v

## Vector3 版本
static func clamp_length_v3(v: Vector3, max_length: float) -> Vector3:
    if v.length_squared() > max_length * max_length:
        return v.normalized() * max_length
    return v
```

---

## 3. 随机工具

```gdscript
class_name RandomUtils

## 从数组中随机选择一个元素
static func pick(arr: Array) -> Variant:
    if arr.is_empty():
        return null
    return arr[randi() % arr.size()]

## 从数组中随机选择 N 个不重复元素
static func pick_n(arr: Array, n: int) -> Array:
    var shuffled := arr.duplicate()
    shuffled.shuffle()
    return shuffled.slice(0, mini(n, shuffled.size()))

## 带权重随机选择
static func pick_weighted(items: Array, weights: Array[float]) -> Variant:
    if items.is_empty() or items.size() != weights.size():
        return null
    
    var total := 0.0
    for w in weights:
        total += w
    
    var r := randf() * total
    var cumulative := 0.0
    for i in items.size():
        cumulative += weights[i]
        if r <= cumulative:
            return items[i]
    
    return items[-1]

## 随机布尔值
static func random_bool(true_chance := 0.5) -> bool:
    return randf() < true_chance

## 随机范围内的整数
static func random_int(min_val: int, max_val: int) -> int:
    return randi_range(min_val, max_val)

## 随机范围内的浮点数
static func random_float(min_val: float, max_val: float) -> float:
    return randf_range(min_val, max_val)

## 随机单位圆内的点
static func random_in_circle(radius := 1.0) -> Vector2:
    var angle := randf() * TAU
    var r := sqrt(randf()) * radius  # sqrt 使分布均匀
    return Vector2(cos(angle), sin(angle)) * r

## 随机圆环上的点
static func random_on_circle(radius := 1.0) -> Vector2:
    var angle := randf() * TAU
    return Vector2(cos(angle), sin(angle)) * radius

## 随机单位球内的点
static func random_in_sphere(radius := 1.0) -> Vector3:
    var theta := randf() * TAU
    var phi := acos(2.0 * randf() - 1.0)
    var r := pow(randf(), 1.0/3.0) * radius
    return Vector3(
        r * sin(phi) * cos(theta),
        r * sin(phi) * sin(theta),
        r * cos(phi)
    )

## 随机球面上的点
static func random_on_sphere(radius := 1.0) -> Vector3:
    var theta := randf() * TAU
    var phi := acos(2.0 * randf() - 1.0)
    return Vector3(
        radius * sin(phi) * cos(theta),
        radius * sin(phi) * sin(theta),
        radius * cos(phi)
    )

## 高斯/正态分布随机数（Box-Muller 变换）
static func random_gaussian(mean := 0.0, std_dev := 1.0) -> float:
    var u1 := randf()
    var u2 := randf()
    var z := sqrt(-2.0 * log(u1)) * cos(TAU * u2)
    return mean + z * std_dev

## 随机颜色
static func random_color(alpha := 1.0) -> Color:
    return Color(randf(), randf(), randf(), alpha)

## 随机 HSV 颜色（更好看）
static func random_color_hsv(s_range := Vector2(0.5, 1.0), v_range := Vector2(0.5, 1.0), alpha := 1.0) -> Color:
    var h := randf()
    var s := randf_range(s_range.x, s_range.y)
    var v := randf_range(v_range.x, v_range.y)
    return Color.from_hsv(h, s, v, alpha)
```

---

## 4. 时间工具

```gdscript
class_name TimeUtils

## 格式化秒数为 MM:SS
static func format_time_mmss(total_seconds: float) -> String:
    var minutes := int(total_seconds) / 60
    var seconds := int(total_seconds) % 60
    return "%02d:%02d" % [minutes, seconds]

## 格式化秒数为 HH:MM:SS
static func format_time_hhmmss(total_seconds: float) -> String:
    var hours := int(total_seconds) / 3600
    var minutes := (int(total_seconds) % 3600) / 60
    var seconds := int(total_seconds) % 60
    return "%02d:%02d:%02d" % [hours, minutes, seconds]

## 格式化秒数为 MM:SS.mmm（含毫秒）
static func format_time_precise(total_seconds: float) -> String:
    var minutes := int(total_seconds) / 60
    var seconds := int(total_seconds) % 60
    var millis := int((total_seconds - int(total_seconds)) * 1000)
    return "%02d:%02d.%03d" % [minutes, seconds, millis]

## 解析 MM:SS 字符串为秒数
static func parse_time_mmss(time_str: String) -> float:
    var parts := time_str.split(":")
    if parts.size() != 2:
        return 0.0
    return float(parts[0]) * 60 + float(parts[1])

## 创建一次性定时器
static func create_timer(node: Node, duration: float, callback: Callable) -> SceneTreeTimer:
    var timer := node.get_tree().create_timer(duration)
    timer.timeout.connect(callback)
    return timer

## 等待指定时间（协程用）
static func wait(node: Node, duration: float) -> Signal:
    return node.get_tree().create_timer(duration).timeout
```

**使用示例**：
```gdscript
# 协程等待
await TimeUtils.wait(self, 1.5)
print("1.5 秒后执行")

# 一次性定时器
TimeUtils.create_timer(self, 2.0, func(): print("2 秒后执行"))
```

---

## 5. 字符串工具

```gdscript
class_name StringUtils

## 首字母大写
static func capitalize_first(s: String) -> String:
    if s.is_empty():
        return s
    return s[0].to_upper() + s.substr(1)

## 转换为 Title Case
static func to_title_case(s: String) -> String:
    var words := s.split(" ")
    var result := PackedStringArray()
    for word in words:
        result.append(capitalize_first(word.to_lower()))
    return " ".join(result)

## snake_case 转 PascalCase
static func snake_to_pascal(s: String) -> String:
    var parts := s.split("_")
    var result := ""
    for part in parts:
        result += capitalize_first(part)
    return result

## PascalCase 转 snake_case
static func pascal_to_snake(s: String) -> String:
    var result := ""
    for i in s.length():
        var c := s[i]
        if c == c.to_upper() and i > 0:
            result += "_"
        result += c.to_lower()
    return result

## 截断字符串（加省略号）
static func truncate(s: String, max_length: int, suffix := "...") -> String:
    if s.length() <= max_length:
        return s
    return s.substr(0, max_length - suffix.length()) + suffix

## 检查是否为有效的标识符（变量名）
static func is_valid_identifier(s: String) -> bool:
    if s.is_empty():
        return false
    var first := s[0]
    if not (first.is_valid_identifier() and not first.is_valid_int()):
        return false
    for i in range(1, s.length()):
        if not s[i].is_valid_identifier():
            return false
    return true

## 移除所有空白字符
static func remove_whitespace(s: String) -> String:
    return s.replace(" ", "").replace("\t", "").replace("\n", "").replace("\r", "")

## 格式化数字（加千位分隔符）
static func format_number(n: int, separator := ",") -> String:
    var s := str(abs(n))
    var result := ""
    var count := 0
    for i in range(s.length() - 1, -1, -1):
        if count > 0 and count % 3 == 0:
            result = separator + result
        result = s[i] + result
        count += 1
    return ("-" if n < 0 else "") + result

## 重复字符串 N 次
static func repeat(s: String, times: int) -> String:
    var result := ""
    for i in times:
        result += s
    return result

## 安全获取子字符串
static func safe_substr(s: String, from: int, length := -1) -> String:
    if from < 0:
        from = 0
    if from >= s.length():
        return ""
    if length < 0:
        return s.substr(from)
    return s.substr(from, mini(length, s.length() - from))
```

---

## 6. 数组工具

```gdscript
class_name ArrayUtils

## 查找满足条件的第一个元素
static func find(arr: Array, predicate: Callable) -> Variant:
    for item in arr:
        if predicate.call(item):
            return item
    return null

## 查找满足条件的所有元素
static func filter(arr: Array, predicate: Callable) -> Array:
    var result := []
    for item in arr:
        if predicate.call(item):
            result.append(item)
    return result

## 映射数组
static func map(arr: Array, transform: Callable) -> Array:
    var result := []
    for item in arr:
        result.append(transform.call(item))
    return result

## 规约/折叠数组
static func reduce(arr: Array, accumulator: Callable, initial: Variant) -> Variant:
    var result := initial
    for item in arr:
        result = accumulator.call(result, item)
    return result

## 求和
static func sum(arr: Array) -> float:
    return reduce(arr, func(acc, x): return acc + x, 0.0)

## 求平均值
static func average(arr: Array) -> float:
    if arr.is_empty():
        return 0.0
    return sum(arr) / arr.size()

## 求最大值
static func max_value(arr: Array) -> Variant:
    if arr.is_empty():
        return null
    var result = arr[0]
    for i in range(1, arr.size()):
        if arr[i] > result:
            result = arr[i]
    return result

## 求最小值
static func min_value(arr: Array) -> Variant:
    if arr.is_empty():
        return null
    var result = arr[0]
    for i in range(1, arr.size()):
        if arr[i] < result:
            result = arr[i]
    return result

## 去重
static func unique(arr: Array) -> Array:
    var result := []
    for item in arr:
        if item not in result:
            result.append(item)
    return result

## 分块
static func chunk(arr: Array, size: int) -> Array[Array]:
    var result: Array[Array] = []
    var i := 0
    while i < arr.size():
        result.append(arr.slice(i, i + size))
        i += size
    return result

## 展平嵌套数组（一层）
static func flatten(arr: Array) -> Array:
    var result := []
    for item in arr:
        if item is Array:
            result.append_array(item)
        else:
            result.append(item)
    return result

## 数组差集（a - b）
static func difference(a: Array, b: Array) -> Array:
    var result := []
    for item in a:
        if item not in b:
            result.append(item)
    return result

## 数组交集
static func intersection(a: Array, b: Array) -> Array:
    var result := []
    for item in a:
        if item in b and item not in result:
            result.append(item)
    return result

## 检查所有元素是否满足条件
static func all(arr: Array, predicate: Callable) -> bool:
    for item in arr:
        if not predicate.call(item):
            return false
    return true

## 检查是否存在满足条件的元素
static func any(arr: Array, predicate: Callable) -> bool:
    for item in arr:
        if predicate.call(item):
            return true
    return false

## 计算满足条件的元素个数
static func count(arr: Array, predicate: Callable) -> int:
    var result := 0
    for item in arr:
        if predicate.call(item):
            result += 1
    return result
```

---

## 7. 节点工具

```gdscript
class_name NodeUtils

## 安全获取节点（不存在返回 null，不报错）
static func get_node_safe(from: Node, path: NodePath) -> Node:
    if from.has_node(path):
        return from.get_node(path)
    return null

## 递归查找第一个指定类型的子节点
static func find_child_of_type(node: Node, type: GDScript) -> Node:
    for child in node.get_children():
        if is_instance_of(child, type):
            return child
        var found := find_child_of_type(child, type)
        if found:
            return found
    return null

## 递归查找所有指定类型的子节点
static func find_children_of_type(node: Node, type: GDScript) -> Array[Node]:
    var result: Array[Node] = []
    for child in node.get_children():
        if is_instance_of(child, type):
            result.append(child)
        result.append_array(find_children_of_type(child, type))
    return result

## 获取节点到根的路径（调试用）
static func get_full_path(node: Node) -> String:
    var path := node.name
    var parent := node.get_parent()
    while parent:
        path = parent.name + "/" + path
        parent = parent.get_parent()
    return path

## 安全 queue_free（检查有效性）
static func safe_free(node: Node) -> void:
    if is_instance_valid(node):
        node.queue_free()

## 延迟调用（下一帧）
static func call_deferred_frame(node: Node, callback: Callable) -> void:
    node.get_tree().process_frame.connect(callback, CONNECT_ONE_SHOT)

## 移除节点的所有子节点
static func remove_all_children(node: Node) -> void:
    for child in node.get_children():
        child.queue_free()

## 重新设置父节点（保持世界位置）
static func reparent_keep_global(node: Node3D, new_parent: Node) -> void:
    var global_transform := node.global_transform
    node.get_parent().remove_child(node)
    new_parent.add_child(node)
    node.global_transform = global_transform

## 2D 版本
static func reparent_keep_global_2d(node: Node2D, new_parent: Node) -> void:
    var global_transform := node.global_transform
    node.get_parent().remove_child(node)
    new_parent.add_child(node)
    node.global_transform = global_transform

## 禁用/启用节点及其所有子节点的处理
static func set_process_recursive(node: Node, enabled: bool) -> void:
    node.set_process(enabled)
    node.set_physics_process(enabled)
    node.set_process_input(enabled)
    for child in node.get_children():
        set_process_recursive(child, enabled)
```

---

## 8. 文件工具

```gdscript
class_name FileUtils

## 检查文件是否存在
static func file_exists(path: String) -> bool:
    return FileAccess.file_exists(path)

## 检查目录是否存在
static func dir_exists(path: String) -> bool:
    return DirAccess.dir_exists_absolute(path)

## 读取文本文件
static func read_text(path: String) -> String:
    var file := FileAccess.open(path, FileAccess.READ)
    if file:
        return file.get_as_text()
    return ""

## 写入文本文件
static func write_text(path: String, content: String) -> bool:
    var file := FileAccess.open(path, FileAccess.WRITE)
    if file:
        file.store_string(content)
        return true
    return false

## 追加文本到文件
static func append_text(path: String, content: String) -> bool:
    var file := FileAccess.open(path, FileAccess.READ_WRITE)
    if file:
        file.seek_end()
        file.store_string(content)
        return true
    return false

## 读取 JSON 文件
static func read_json(path: String) -> Variant:
    var text := read_text(path)
    if text.is_empty():
        return null
    var json := JSON.new()
    if json.parse(text) == OK:
        return json.data
    return null

## 写入 JSON 文件
static func write_json(path: String, data: Variant, indent := "\t") -> bool:
    return write_text(path, JSON.stringify(data, indent))

## 获取目录下所有文件（递归可选）
static func list_files(dir_path: String, recursive := false, extension := "") -> PackedStringArray:
    var result := PackedStringArray()
    var dir := DirAccess.open(dir_path)
    if not dir:
        return result
    
    dir.list_dir_begin()
    var file_name := dir.get_next()
    while file_name != "":
        if file_name != "." and file_name != "..":
            var full_path := dir_path.path_join(file_name)
            if dir.current_is_dir():
                if recursive:
                    result.append_array(list_files(full_path, true, extension))
            else:
                if extension.is_empty() or file_name.ends_with(extension):
                    result.append(full_path)
        file_name = dir.get_next()
    
    return result

## 确保目录存在（递归创建）
static func ensure_dir(path: String) -> bool:
    if DirAccess.dir_exists_absolute(path):
        return true
    return DirAccess.make_dir_recursive_absolute(path) == OK

## 获取文件大小
static func get_file_size(path: String) -> int:
    var file := FileAccess.open(path, FileAccess.READ)
    if file:
        return file.get_length()
    return -1

## 复制文件
static func copy_file(from: String, to: String) -> bool:
    return DirAccess.copy_absolute(from, to) == OK

## 移动文件
static func move_file(from: String, to: String) -> bool:
    return DirAccess.rename_absolute(from, to) == OK

## 删除文件
static func delete_file(path: String) -> bool:
    return DirAccess.remove_absolute(path) == OK
```

---

## 9. 调试工具

```gdscript
class_name DebugUtils

## 打印带时间戳的日志
static func log(message: String) -> void:
    var time := Time.get_time_dict_from_system()
    print("[%02d:%02d:%02d] %s" % [time["hour"], time["minute"], time["second"], message])

## 打印变量名和值
static func print_var(name: String, value: Variant) -> void:
    print("%s = %s" % [name, str(value)])

## 打印分隔线
static func print_separator(char := "=", length := 50) -> void:
    print(StringUtils.repeat(char, length))

## 打印字典（格式化）
static func print_dict(d: Dictionary, indent := 0) -> void:
    var prefix := StringUtils.repeat("  ", indent)
    for key in d:
        var value = d[key]
        if value is Dictionary:
            print("%s%s:" % [prefix, key])
            print_dict(value, indent + 1)
        else:
            print("%s%s: %s" % [prefix, key, str(value)])

## 断言（调试版本有效）
static func assert_true(condition: bool, message := "Assertion failed") -> void:
    if OS.is_debug_build() and not condition:
        push_error(message)
        assert(false, message)

## 计时器开始
static var _timers := {}
static func timer_start(name: String) -> void:
    _timers[name] = Time.get_ticks_msec()

## 计时器结束并打印
static func timer_end(name: String) -> void:
    if name in _timers:
        var elapsed := Time.get_ticks_msec() - _timers[name]
        print("[TIMER] %s: %d ms" % [name, elapsed])
        _timers.erase(name)

## 性能计数（帧时间内调用次数）
static var _counters := {}
static var _counter_frame := 0
static func count(name: String) -> void:
    var frame := Engine.get_process_frames()
    if frame != _counter_frame:
        if not _counters.is_empty():
            print("[COUNTERS] Frame %d:" % _counter_frame)
            for key in _counters:
                print("  %s: %d" % [key, _counters[key]])
        _counters.clear()
        _counter_frame = frame
    _counters[name] = _counters.get(name, 0) + 1

## 绘制调试点（需要在 _draw 中调用）
static func draw_debug_point(canvas: CanvasItem, pos: Vector2, color := Color.RED, size := 5.0) -> void:
    canvas.draw_circle(pos, size, color)

## 绘制调试箭头
static func draw_debug_arrow(canvas: CanvasItem, from: Vector2, to: Vector2, color := Color.RED, width := 2.0) -> void:
    canvas.draw_line(from, to, color, width)
    var dir := (to - from).normalized()
    var perp := Vector2(-dir.y, dir.x)
    var arrow_size := 10.0
    canvas.draw_line(to, to - dir * arrow_size + perp * arrow_size * 0.5, color, width)
    canvas.draw_line(to, to - dir * arrow_size - perp * arrow_size * 0.5, color, width)
```

---

## 10. 缓动工具

```gdscript
class_name EaseUtils

## 常用缓动函数

static func ease_in_quad(t: float) -> float:
    return t * t

static func ease_out_quad(t: float) -> float:
    return 1.0 - (1.0 - t) * (1.0 - t)

static func ease_in_out_quad(t: float) -> float:
    return 2.0 * t * t if t < 0.5 else 1.0 - pow(-2.0 * t + 2.0, 2) / 2.0

static func ease_in_cubic(t: float) -> float:
    return t * t * t

static func ease_out_cubic(t: float) -> float:
    return 1.0 - pow(1.0 - t, 3)

static func ease_in_out_cubic(t: float) -> float:
    return 4.0 * t * t * t if t < 0.5 else 1.0 - pow(-2.0 * t + 2.0, 3) / 2.0

static func ease_in_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    return -pow(2, 10 * t - 10) * sin((t * 10 - 10.75) * (TAU / 3))

static func ease_out_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * sin((t * 10 - 0.75) * (TAU / 3)) + 1

static func ease_out_bounce(t: float) -> float:
    const n1 := 7.5625
    const d1 := 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

static func ease_in_bounce(t: float) -> float:
    return 1 - ease_out_bounce(1 - t)

## 应用缓动到值
static func apply(from: float, to: float, t: float, ease_func: Callable) -> float:
    return lerpf(from, to, ease_func.call(clampf(t, 0.0, 1.0)))

## 应用缓动到 Vector2
static func apply_v2(from: Vector2, to: Vector2, t: float, ease_func: Callable) -> Vector2:
    var eased := ease_func.call(clampf(t, 0.0, 1.0))
    return from.lerp(to, eased)

## 应用缓动到 Vector3
static func apply_v3(from: Vector3, to: Vector3, t: float, ease_func: Callable) -> Vector3:
    var eased := ease_func.call(clampf(t, 0.0, 1.0))
    return from.lerp(to, eased)

## 应用缓动到 Color
static func apply_color(from: Color, to: Color, t: float, ease_func: Callable) -> Color:
    var eased := ease_func.call(clampf(t, 0.0, 1.0))
    return from.lerp(to, eased)
```

**使用示例**：
```gdscript
# 手动应用缓动
var progress := 0.0
func _process(delta: float) -> void:
    progress += delta * 0.5  # 2 秒完成
    position.x = EaseUtils.apply(0, 500, progress, EaseUtils.ease_out_elastic)

# 或者直接使用 Tween（内置缓动）
var tween := create_tween()
tween.tween_property(self, "position:x", 500, 2.0).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_ELASTIC)
```

---

## 完整 Autoload 脚本

如果你想一次性使用所有工具，可以创建一个合并的 Autoload：

```gdscript
# autoload/utils.gd
extends Node

# 导入所有工具类
const Math := preload("res://utils/math_utils.gd")
const Vector := preload("res://utils/vector_utils.gd")
const Random := preload("res://utils/random_utils.gd")
const Time := preload("res://utils/time_utils.gd")
const Str := preload("res://utils/string_utils.gd")
const Arr := preload("res://utils/array_utils.gd")
const Node := preload("res://utils/node_utils.gd")
const File := preload("res://utils/file_utils.gd")
const Debug := preload("res://utils/debug_utils.gd")
const Ease := preload("res://utils/ease_utils.gd")
```

然后这样使用：
```gdscript
var random_item = Utils.Random.pick(my_array)
var formatted = Utils.Str.format_number(1234567)
Utils.Debug.log("Something happened")
```

---

## 快速参考

| 工具类 | 常用函数 |
|--------|----------|
| MathUtils | `remap`, `normalize_angle`, `approx_equal` |
| VectorUtils | `smooth_damp_v2/v3`, `perpendicular_cw`, `world_to_top_down` |
| RandomUtils | `pick`, `pick_weighted`, `random_in_circle`, `random_gaussian` |
| TimeUtils | `format_time_mmss`, `create_timer`, `wait` |
| StringUtils | `truncate`, `format_number`, `snake_to_pascal` |
| ArrayUtils | `find`, `filter`, `map`, `reduce`, `unique` |
| NodeUtils | `find_child_of_type`, `safe_free`, `reparent_keep_global` |
| FileUtils | `read_json`, `write_json`, `list_files`, `ensure_dir` |
| DebugUtils | `log`, `timer_start/end`, `draw_debug_arrow` |
| EaseUtils | `ease_out_elastic`, `ease_out_bounce`, `apply` |
