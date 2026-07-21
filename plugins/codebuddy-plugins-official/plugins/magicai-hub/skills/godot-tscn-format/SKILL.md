---
name: godot-tscn-format
description: "Godot .tscn 场景文件格式规范。让 AI 能够直接读写 Godot 场景文件，理解节点树结构、外部/内嵌资源引用、Transform 变换、信号连接等。当需要创建或修改 .tscn 文件时使用此 Skill。"
version: 1.0.0
---

# Godot .tscn 场景文件格式规范

> **用途**：让 AI 能够直接读写 Godot 场景文件  
> **版本**：v1.0 · 2026-04-24  
> **适用引擎**：Godot 4.x

---

## 核心原则

**Godot 场景文件是纯文本**，AI 可以直接通过 `write_to_file` 和 `replace_in_file` 操作，无需任何中间层。

---

## 一、文件结构总览

```
[gd_scene load_steps=N format=3 uid="uid://xxx"]    ← 头部（必需）

[ext_resource type="Type" path="res://..." id="ID"]  ← 外部资源引用（可选）
[ext_resource ...]

[sub_resource type="Type" id="ID"]                   ← 内嵌资源定义（可选）
property = value
[sub_resource ...]

[node name="Name" type="Type"]                       ← 根节点（必需）
property = value

[node name="Child" type="Type" parent="."]           ← 子节点
property = value

[connection signal="sig" from="Node" to="Target" method="func"]  ← 信号连接（可选）
```

---

## 二、头部声明

### 2.1 基本格式

```
[gd_scene load_steps=4 format=3]
```

| 字段 | 说明 |
|------|------|
| `load_steps` | 资源加载步数 = ext_resource 数 + sub_resource 数 + 1（场景本身） |
| `format` | 固定为 `3`（Godot 4.x） |
| `uid` | 可选，Godot 自动生成的唯一 ID，创建时可省略 |

### 2.2 计算 load_steps

```python
load_steps = len(ext_resources) + len(sub_resources) + 1
```

示例：2 个外部资源 + 3 个内嵌资源 → `load_steps=6`

---

## 三、外部资源引用 (ext_resource)

### 3.1 格式

```
[ext_resource type="Type" path="res://path/to/file" id="ID"]
```

### 3.2 常见类型

| type | 文件类型 | 示例 |
|------|----------|------|
| `Script` | GDScript | `path="res://scripts/player.gd"` |
| `PackedScene` | 场景 | `path="res://scenes/enemy.tscn"` |
| `Material` | 材质资源 | `path="res://materials/floor.tres"` |
| `Texture2D` | 2D 纹理 | `path="res://textures/icon.png"` |
| `AudioStream` | 音频 | `path="res://audio/shoot.wav"` |
| `Shader` | 着色器 | `path="res://shaders/outline.gdshader"` |

### 3.3 ID 命名规范

AI 生成时使用有意义的 ID：
```
[ext_resource type="Script" path="res://scripts/player.gd" id="1_player_script"]
[ext_resource type="Material" path="res://resources/floor_mat.tres" id="2_floor_mat"]
[ext_resource type="PackedScene" path="res://scenes/bullet.tscn" id="3_bullet_scene"]
```

---

## 四、内嵌资源定义 (sub_resource)

### 4.1 格式

```
[sub_resource type="Type" id="ID"]
property1 = value1
property2 = value2
```

### 4.2 常用碰撞形状

```
# 胶囊体（角色常用）
[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_player"]
radius = 0.35
height = 1.8

# 球体
[sub_resource type="SphereShape3D" id="SphereShape3D_001"]
radius = 0.5

# 盒子
[sub_resource type="BoxShape3D" id="BoxShape3D_floor"]
size = Vector3(10, 0.2, 10)

# 圆柱体
[sub_resource type="CylinderShape3D" id="CylinderShape3D_001"]
height = 2.0
radius = 0.5

# 2D 形状
[sub_resource type="RectangleShape2D" id="RectangleShape2D_001"]
size = Vector2(32, 32)

[sub_resource type="CircleShape2D" id="CircleShape2D_001"]
radius = 16.0
```

### 4.3 常用网格

```
# 盒子网格
[sub_resource type="BoxMesh" id="BoxMesh_001"]
size = Vector3(1, 1, 1)

# 球体网格
[sub_resource type="SphereMesh" id="SphereMesh_001"]
radius = 0.5
height = 1.0

# 胶囊网格
[sub_resource type="CapsuleMesh" id="CapsuleMesh_001"]
radius = 0.5
height = 2.0

# 圆柱网格
[sub_resource type="CylinderMesh" id="CylinderMesh_001"]
top_radius = 0.5
bottom_radius = 0.5
height = 2.0

# 平面网格
[sub_resource type="PlaneMesh" id="PlaneMesh_001"]
size = Vector2(10, 10)
```

### 4.4 材质（内嵌）

```
[sub_resource type="StandardMaterial3D" id="Material_red"]
albedo_color = Color(1, 0, 0, 1)
roughness = 0.8
metallic = 0.2

# 发光材质
[sub_resource type="StandardMaterial3D" id="Material_glow"]
emission_enabled = true
emission = Color(1, 0.8, 0, 1)
emission_energy_multiplier = 2.0
```

---

## 五、节点声明 (node)

### 5.1 根节点

```
[node name="Player" type="CharacterBody3D"]
script = ExtResource("1_player_script")
```

### 5.2 子节点

```
[node name="ChildName" type="NodeType" parent="."]
property = value
```

| parent 值 | 含义 |
|-----------|------|
| `.` | 直接子节点（父节点是根） |
| `ParentName` | 指定父节点名 |
| `Parent/Child` | 嵌套路径 |

### 5.3 引用资源

```
# 引用外部资源
script = ExtResource("1_player_script")
mesh = ExtResource("2_mesh")

# 引用内嵌资源
shape = SubResource("CapsuleShape3D_player")
mesh = SubResource("BoxMesh_001")
```

### 5.4 实例化场景

```
[node name="Enemy1" parent="Enemies" instance=ExtResource("4_enemy_scene")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 5, 0, -10)
```

---

## 六、Transform 变换

### 6.1 Transform3D 格式

```
transform = Transform3D(bx.x, bx.y, bx.z, by.x, by.y, by.z, bz.x, bz.y, bz.z, ox, oy, oz)
```

| 参数 | 含义 |
|------|------|
| bx (1-3) | X 轴基向量 |
| by (4-6) | Y 轴基向量 |
| bz (7-9) | Z 轴基向量 |
| o (10-12) | 位置 (origin) |

### 6.2 常用变换

```
# 单位变换（默认位置）
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)

# 仅位置
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 5, 2, -10)

# 位置 + 缩放 0.5
transform = Transform3D(0.5, 0, 0, 0, 0.5, 0, 0, 0, 0.5, 5, 2, -10)

# 绕 Y 轴旋转 90°（sin90=1, cos90=0）
transform = Transform3D(0, 0, 1, 0, 1, 0, -1, 0, 0, 0, 0, 0)
```

### 6.3 Transform2D 格式

```
transform = Transform2D(cos, sin, -sin, cos, x, y)

# 单位变换
transform = Transform2D(1, 0, 0, 1, 100, 200)

# 旋转 45° 位于 (100, 200)
transform = Transform2D(0.707, 0.707, -0.707, 0.707, 100, 200)
```

---

## 七、常用属性值格式

### 7.1 基础类型

```
# 布尔
visible = true
enabled = false

# 整数
health = 100

# 浮点
speed = 10.5

# 字符串
name = "Player"
```

### 7.2 向量

```
# Vector2
position = Vector2(100, 200)
size = Vector2(32, 32)

# Vector3
position = Vector3(0, 1.5, 0)
target_position = Vector3(0, 0, -100)

# Vector4
custom_data = Vector4(1, 2, 3, 4)
```

### 7.3 颜色

```
# Color(R, G, B, A) 范围 0.0-1.0
light_color = Color(1, 0.85, 0.3, 1)
albedo_color = Color(0.25, 0.25, 0.3, 1)

# 半透明
modulate = Color(1, 1, 1, 0.5)
```

### 7.4 数组

```
# PackedStringArray
config/features = PackedStringArray("4.6", "Forward Plus")

# PackedVector2Array
polygon = PackedVector2Array(0, 0, 100, 0, 100, 100, 0, 100)

# 普通数组
groups = ["enemy", "damageable"]
```

---

## 八、信号连接 (connection)

### 8.1 格式

```
[connection signal="signal_name" from="NodePath" to="TargetPath" method="method_name"]
```

### 8.2 示例

```
# 同级节点连接
[connection signal="timeout" from="ShootCooldown" to="." method="_on_shoot_cooldown_timeout"]

# 子节点连接到根
[connection signal="body_entered" from="HitArea" to="." method="_on_hit_area_body_entered"]

# 带 flags
[connection signal="pressed" from="Button" to="." method="_on_button_pressed" flags=1]
```

---

## 九、完整示例模板

### 9.1 3D 角色场景

```
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1_script"]

[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_001"]
radius = 0.35
height = 1.8

[node name="Player" type="CharacterBody3D"]
script = ExtResource("1_script")

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.9, 0)
shape = SubResource("CapsuleShape3D_001")

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.6, 0)
fov = 75.0

[node name="MeshInstance3D" type="MeshInstance3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.9, 0)
```

### 9.2 2D 角色场景

```
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/player_2d.gd" id="1_script"]
[ext_resource type="Texture2D" path="res://sprites/player.png" id="2_texture"]

[sub_resource type="RectangleShape2D" id="RectangleShape2D_001"]
size = Vector2(32, 48)

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1_script")

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("2_texture")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("RectangleShape2D_001")
```

### 9.3 UI 场景

```
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/hud.gd" id="1_script"]

[node name="HUD" type="CanvasLayer"]
script = ExtResource("1_script")

[node name="MarginContainer" type="MarginContainer" parent="."]
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 20.0
offset_top = 20.0
offset_right = -20.0
offset_bottom = -20.0

[node name="VBoxContainer" type="VBoxContainer" parent="MarginContainer"]
layout_mode = 2

[node name="ScoreLabel" type="Label" parent="MarginContainer/VBoxContainer"]
layout_mode = 2
text = "Score: 0"

[node name="TimeLabel" type="Label" parent="MarginContainer/VBoxContainer"]
layout_mode = 2
text = "Time: 60"
```

---

## 十、AI 操作指南

### 10.1 创建新场景

```python
# AI 直接使用 write_to_file
write_to_file("res://scenes/new_scene.tscn", """
[gd_scene load_steps=1 format=3]

[node name="Root" type="Node3D"]
""")
```

### 10.2 修改现有场景

```python
# 使用 replace_in_file 修改属性
replace_in_file("res://scenes/player.tscn",
    old_str='fov = 75.0',
    new_str='fov = 90.0'
)
```

### 10.3 添加节点

```python
# 在场景末尾添加节点（信号连接之前）
replace_in_file("res://scenes/player.tscn",
    old_str='[connection signal=',
    new_str='''[node name="NewChild" type="Node3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)

[connection signal='''
)
```

### 10.4 常见错误排查

| 错误 | 原因 | 修复 |
|------|------|------|
| `load_steps` 不匹配 | 资源数计算错误 | 重新计算 ext + sub + 1 |
| `id not found` | 引用了不存在的资源 ID | 检查 ExtResource/SubResource ID |
| 场景无法加载 | parent 路径错误 | 检查节点层级关系 |
| 属性无效 | 类型拼写错误 | 查阅 Godot 文档确认属性名 |

---

## 十一、快速参考

### 常用节点类型

| 类别 | 3D | 2D |
|------|-----|-----|
| 基础 | Node3D | Node2D |
| 物理角色 | CharacterBody3D | CharacterBody2D |
| 刚体 | RigidBody3D | RigidBody2D |
| 静态体 | StaticBody3D | StaticBody2D |
| 碰撞形状 | CollisionShape3D | CollisionShape2D |
| 网格 | MeshInstance3D | - |
| 精灵 | - | Sprite2D |
| 相机 | Camera3D | Camera2D |
| 灯光 | DirectionalLight3D, OmniLight3D, SpotLight3D | PointLight2D, DirectionalLight2D |

### 常用 UI 节点

| 节点 | 用途 |
|------|------|
| Control | UI 基类 |
| CanvasLayer | UI 层 |
| Label | 文本 |
| Button | 按钮 |
| TextureRect | 图片 |
| ProgressBar | 进度条 |
| VBoxContainer / HBoxContainer | 布局容器 |
| MarginContainer | 边距容器 |
