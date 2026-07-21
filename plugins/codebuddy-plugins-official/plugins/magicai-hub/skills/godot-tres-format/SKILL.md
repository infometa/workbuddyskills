---
name: godot-tres-format
description: "Godot .tres 资源文件格式规范。让 AI 能够直接读写 Godot 资源文件（材质、环境、物理材质、渐变、曲线、样式盒、着色器、动画、粒子等）。当需要创建或修改 .tres 文件时使用此 Skill。"
version: 1.0.0
---

# Godot .tres 资源文件格式规范

> **用途**：让 AI 能够直接读写 Godot 资源文件  
> **版本**：v1.0 · 2026-04-24  
> **适用引擎**：Godot 4.x

---

## 核心原则

**Godot 资源文件是纯文本**，AI 可以直接通过 `write_to_file` 创建材质、形状、环境等资源。

---

## 一、文件结构

```
[gd_resource type="ResourceType" format=3 uid="uid://xxx"]

[resource]
property1 = value1
property2 = value2
```

---

## 二、材质资源 (StandardMaterial3D)

### 2.1 基础材质

```
[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(0.8, 0.2, 0.2, 1)
roughness = 0.8
metallic = 0.0
```

### 2.2 金属材质

```
[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(0.9, 0.9, 0.9, 1)
roughness = 0.3
metallic = 0.9
metallic_specular = 0.5
```

### 2.3 发光材质

```
[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(1, 0.8, 0, 1)
emission_enabled = true
emission = Color(1, 0.8, 0, 1)
emission_energy_multiplier = 3.0
```

### 2.4 透明材质

```
[gd_resource type="StandardMaterial3D" format=3]

[resource]
transparency = 1
albedo_color = Color(0.2, 0.5, 1, 0.5)
```

### 2.5 无光照材质

```
[gd_resource type="StandardMaterial3D" format=3]

[resource]
shading_mode = 0
albedo_color = Color(1, 1, 1, 1)
```

### 2.6 带纹理材质

```
[gd_resource type="StandardMaterial3D" load_steps=2 format=3]

[ext_resource type="Texture2D" path="res://textures/brick.png" id="1_albedo"]

[resource]
albedo_texture = ExtResource("1_albedo")
roughness = 0.9
```

---

## 三、常用材质属性参考

| 属性 | 类型 | 说明 |
|------|------|------|
| `albedo_color` | Color | 基础颜色 |
| `albedo_texture` | Texture2D | 颜色贴图 |
| `roughness` | float (0-1) | 粗糙度，0=光滑，1=粗糙 |
| `metallic` | float (0-1) | 金属度 |
| `metallic_specular` | float (0-1) | 金属高光 |
| `emission_enabled` | bool | 启用发光 |
| `emission` | Color | 发光颜色 |
| `emission_energy_multiplier` | float | 发光强度倍数 |
| `transparency` | int | 0=不透明, 1=Alpha, 2=预乘Alpha |
| `cull_mode` | int | 0=背面剔除, 1=正面剔除, 2=不剔除 |
| `shading_mode` | int | 0=无光照, 1=逐顶点, 2=逐像素(默认) |
| `normal_enabled` | bool | 启用法线贴图 |
| `normal_texture` | Texture2D | 法线贴图 |
| `normal_scale` | float | 法线强度 |

---

## 四、环境资源 (Environment)

### 4.1 基础室外环境

```
[gd_resource type="Environment" format=3]

[resource]
background_mode = 1
background_color = Color(0.4, 0.6, 0.9, 1)
ambient_light_source = 2
ambient_light_color = Color(0.5, 0.5, 0.6, 1)
ambient_light_energy = 0.5
tonemap_mode = 2
tonemap_white = 6.0
ssao_enabled = true
ssil_enabled = true
glow_enabled = true
```

### 4.2 室内环境

```
[gd_resource type="Environment" format=3]

[resource]
background_mode = 1
background_color = Color(0.1, 0.1, 0.15, 1)
ambient_light_source = 1
ambient_light_color = Color(0.3, 0.3, 0.35, 1)
ambient_light_energy = 0.3
ssao_enabled = true
ssao_intensity = 2.0
```

### 4.3 带天空盒环境

```
[gd_resource type="Environment" load_steps=2 format=3]

[sub_resource type="Sky" id="Sky_001"]
sky_material = SubResource("ProceduralSkyMaterial_001")

[sub_resource type="ProceduralSkyMaterial" id="ProceduralSkyMaterial_001"]
sky_top_color = Color(0.3, 0.5, 0.9, 1)
sky_horizon_color = Color(0.7, 0.8, 0.95, 1)
ground_bottom_color = Color(0.2, 0.2, 0.2, 1)
ground_horizon_color = Color(0.5, 0.5, 0.5, 1)
sun_angle_max = 30.0

[resource]
background_mode = 2
sky = SubResource("Sky_001")
ambient_light_source = 3
tonemap_mode = 2
```

---

## 五、物理材质 (PhysicsMaterial)

```
[gd_resource type="PhysicsMaterial" format=3]

[resource]
friction = 0.8
rough = true
bounce = 0.2
absorbent = false
```

| 属性 | 说明 |
|------|------|
| `friction` | 摩擦力 (0-1) |
| `rough` | 粗糙模式 |
| `bounce` | 弹性 (0-1) |
| `absorbent` | 吸收模式 |

---

## 六、渐变资源 (Gradient)

### 6.1 线性渐变

```
[gd_resource type="Gradient" format=3]

[resource]
offsets = PackedFloat32Array(0, 0.5, 1)
colors = PackedColorArray(1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1)
```

### 6.2 用于粒子的渐变

```
[gd_resource type="Gradient" format=3]

[resource]
offsets = PackedFloat32Array(0, 0.3, 0.7, 1)
colors = PackedColorArray(1, 1, 1, 1, 1, 0.8, 0.2, 1, 1, 0.2, 0, 0.5, 0.5, 0.1, 0, 0)
```

---

## 七、曲线资源 (Curve)

### 7.1 基础曲线

```
[gd_resource type="Curve" format=3]

[resource]
min_value = 0.0
max_value = 1.0
_data = [Vector2(0, 0), 0.0, 0.0, 0, 0, Vector2(0.5, 1), 0.0, 0.0, 0, 0, Vector2(1, 0), 0.0, 0.0, 0, 0]
point_count = 3
```

### 7.2 淡入淡出曲线

```
[gd_resource type="Curve" format=3]

[resource]
_data = [Vector2(0, 0), 0.0, 2.0, 0, 1, Vector2(0.2, 1), 0.0, 0.0, 0, 0, Vector2(0.8, 1), 0.0, 0.0, 0, 0, Vector2(1, 0), -2.0, 0.0, 1, 0]
point_count = 4
```

---

## 八、样式盒资源 (StyleBox)

### 8.1 扁平样式盒

```
[gd_resource type="StyleBoxFlat" format=3]

[resource]
bg_color = Color(0.2, 0.2, 0.25, 1)
border_width_left = 2
border_width_top = 2
border_width_right = 2
border_width_bottom = 2
border_color = Color(0.4, 0.4, 0.5, 1)
corner_radius_top_left = 8
corner_radius_top_right = 8
corner_radius_bottom_right = 8
corner_radius_bottom_left = 8
```

### 8.2 按钮样式

```
[gd_resource type="StyleBoxFlat" format=3]

[resource]
bg_color = Color(0.3, 0.5, 0.8, 1)
corner_radius_top_left = 4
corner_radius_top_right = 4
corner_radius_bottom_right = 4
corner_radius_bottom_left = 4
shadow_color = Color(0, 0, 0, 0.3)
shadow_size = 2
shadow_offset = Vector2(0, 2)
```

---

## 九、着色器材质 (ShaderMaterial)

### 9.1 内联着色器

```
[gd_resource type="ShaderMaterial" load_steps=2 format=3]

[sub_resource type="Shader" id="Shader_001"]
code = "shader_type spatial;

uniform vec4 albedo_color : source_color = vec4(1.0);
uniform float metallic : hint_range(0, 1) = 0.0;

void fragment() {
    ALBEDO = albedo_color.rgb;
    METALLIC = metallic;
}
"

[resource]
shader = SubResource("Shader_001")
shader_parameter/albedo_color = Color(1, 0, 0, 1)
shader_parameter/metallic = 0.5
```

### 9.2 引用外部着色器

```
[gd_resource type="ShaderMaterial" load_steps=2 format=3]

[ext_resource type="Shader" path="res://shaders/custom.gdshader" id="1_shader"]

[resource]
shader = ExtResource("1_shader")
shader_parameter/speed = 2.0
shader_parameter/amplitude = 0.1
```

---

## 十、动画资源 (Animation)

### 10.1 简单位置动画

```
[gd_resource type="Animation" format=3]

[resource]
resource_name = "move_right"
length = 1.0
loop_mode = 0
tracks/0/type = "value"
tracks/0/imported = false
tracks/0/enabled = true
tracks/0/path = NodePath(".:position")
tracks/0/interp = 1
tracks/0/loop_wrap = true
tracks/0/keys = {
"times": PackedFloat32Array(0, 1),
"transitions": PackedFloat32Array(1, 1),
"update": 0,
"values": [Vector3(0, 0, 0), Vector3(5, 0, 0)]
}
```

### 10.2 颜色动画

```
[gd_resource type="Animation" format=3]

[resource]
resource_name = "flash_red"
length = 0.5
tracks/0/type = "value"
tracks/0/path = NodePath("MeshInstance3D:material_override:albedo_color")
tracks/0/keys = {
"times": PackedFloat32Array(0, 0.1, 0.5),
"values": [Color(1, 1, 1, 1), Color(1, 0, 0, 1), Color(1, 1, 1, 1)]
}
```

---

## 十一、字体资源 (FontFile)

字体通常是导入的，但可以创建 FontVariation：

```
[gd_resource type="FontVariation" load_steps=2 format=3]

[ext_resource type="FontFile" path="res://fonts/main.ttf" id="1_font"]

[resource]
base_font = ExtResource("1_font")
variation_opentype = {
"wght": 700
}
spacing_glyph = 2
spacing_top = -2
```

---

## 十二、粒子材质 (ParticleProcessMaterial)

```
[gd_resource type="ParticleProcessMaterial" format=3]

[resource]
emission_shape = 1
emission_sphere_radius = 0.5
direction = Vector3(0, 1, 0)
spread = 30.0
initial_velocity_min = 5.0
initial_velocity_max = 10.0
gravity = Vector3(0, -9.8, 0)
scale_min = 0.5
scale_max = 1.5
color = Color(1, 0.8, 0, 1)
```

---

## 十三、AI 操作指南

### 13.1 创建材质

```python
write_to_file("res://resources/enemy_mat.tres", """
[gd_resource type="StandardMaterial3D" format=3]

[resource]
albedo_color = Color(0.8, 0.2, 0.2, 1)
roughness = 0.7
emission_enabled = true
emission = Color(0.3, 0, 0, 1)
emission_energy_multiplier = 0.5
""")
```

### 13.2 创建环境

```python
write_to_file("res://resources/game_env.tres", """
[gd_resource type="Environment" format=3]

[resource]
background_mode = 1
background_color = Color(0.05, 0.05, 0.1, 1)
ambient_light_color = Color(0.2, 0.2, 0.3, 1)
ambient_light_energy = 0.5
ssao_enabled = true
glow_enabled = true
glow_intensity = 0.5
""")
```

### 13.3 创建物理材质

```python
write_to_file("res://resources/bouncy.tres", """
[gd_resource type="PhysicsMaterial" format=3]

[resource]
friction = 0.3
bounce = 0.9
""")
```

---

## 十四、资源类型速查表

| 类型 | 用途 | 文件 |
|------|------|------|
| `StandardMaterial3D` | 3D 材质 | `*.tres` |
| `CanvasItemMaterial` | 2D 材质 | `*.tres` |
| `ShaderMaterial` | 自定义着色器材质 | `*.tres` |
| `Environment` | 环境设置 | `*.tres` |
| `PhysicsMaterial` | 物理材质 | `*.tres` |
| `Gradient` | 渐变 | `*.tres` |
| `Curve` | 曲线 | `*.tres` |
| `StyleBoxFlat` | UI 样式盒 | `*.tres` |
| `ParticleProcessMaterial` | 粒子材质 | `*.tres` |
| `Animation` | 动画 | `*.tres` 或 `*.anim` |
| `AudioBusLayout` | 音频总线布局 | `*.tres` |
| `Theme` | UI 主题 | `*.tres` |

---

## 十五、颜色速查表

### 常用颜色

```
# 基础色
红色: Color(1, 0, 0, 1)
绿色: Color(0, 1, 0, 1)
蓝色: Color(0, 0, 1, 1)
白色: Color(1, 1, 1, 1)
黑色: Color(0, 0, 0, 1)

# 游戏常用
生命条红: Color(0.9, 0.2, 0.2, 1)
能量条蓝: Color(0.2, 0.5, 0.9, 1)
金币黄: Color(1, 0.85, 0, 1)
毒药绿: Color(0.3, 0.9, 0.2, 1)
暗紫色: Color(0.5, 0.2, 0.7, 1)

# UI 色
暗灰背景: Color(0.15, 0.15, 0.2, 1)
边框灰: Color(0.4, 0.4, 0.5, 1)
高亮蓝: Color(0.3, 0.6, 1, 1)
警告橙: Color(1, 0.6, 0.2, 1)
错误红: Color(0.9, 0.3, 0.3, 1)
成功绿: Color(0.3, 0.8, 0.4, 1)
```
