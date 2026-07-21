# Godot 空项目开发规范（AI 必读）

这是一个空白项目模板，适合从零开始构建任何类型的游戏。

每次修改或新增文件前，必须先确认放置路径符合本文档规范。

---

## 目录结构

```
godot-project/
├── project.godot
├── addons/              ← Godot 插件
├── assets/              ← 资源文件
├── data/                ← 配置数据
├── docs/                ← 文档
├── scenes/              ← 场景文件
└── scripts/             ← 脚本文件
```

## 核心规则

1. `.tscn` 文件只放 `scenes/` 下
2. `.gd` 文件只放 `scripts/` 下
3. 资源文件归 `assets/` 对应子目录
