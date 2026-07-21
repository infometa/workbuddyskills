# MagicAI Hub

Godot 4.x 游戏开发 AI 技能工具包。为 CodeBuddy 提供一组专业技能，帮助 AI 更高效地协助 Godot 项目开发。

## 功能概览

- GDScript 代码生成：按照 Godot 4.x 最佳实践生成高质量 GDScript 代码，涵盖类型系统、信号声明、导出变量等。
- 数据驱动配置：将硬编码数值提取为 Resource 配置表，让设计师可通过 .tres 文件和 Inspector 调整数值。
- 场景文件格式解析：AI 可直接读写 .tscn 场景文件，理解节点树、信号连接、资源引用结构。
- 资源文件格式解析：AI 可直接读写 .tres 资源文件，理解 Resource 属性结构。
- 资产路径修复：修复文件夹重命名/迁移后 Godot 二进制资源中的陈旧绝对路径。
- 无头验证：通过 Godot headless 模式验证项目加载、修复缓存、批量资源操作。
- GDScript 工具函数库：常用辅助函数集合，可直接复制使用或通过 Autoload 全局访问。
- 安全文件操作规范：防止误删文件的关键安全规范和操作流程。

## 使用方式

### 技能

| 技能 | 触发场景 | 说明 |
|---|---|---|
| `gdscript-codegen` | 用户要求生成、修改或审查 GDScript 代码时 | 按 Godot 4.x 规范生成高质量代码 |
| `godot-data-driven-config` | 用户要求提取硬编码数值为配置表时 | 创建 Resource 数据表和管理器 |
| `godot-tscn-format` | 需要创建或修改 .tscn 场景文件时 | 理解 .tscn 文件格式和结构 |
| `godot-tres-format` | 需要创建或修改 .tres 资源文件时 | 理解 .tres 文件格式和结构 |
| `godot-asset-path-surgery` | 报告 "Cannot open file" 或文件夹迁移后引用断裂时 | 修复陈旧路径引用 |
| `godot-headless-verify` | 要求清除缓存、验证项目加载、重构后检查时 | headless 模式验证 |
| `godot-utils` | 需要常用 GDScript 辅助函数时 | 提供可复用的工具函数库 |
| `safe-file-operations` | 涉及文件删除、批量移动等危险操作时 | 安全操作规范和流程 |

## 配置说明

本插件为纯技能插件，不需要额外配置。技能会根据用户意图自动触发。

## 依赖说明

- Godot Engine 4.x（部分技能需要本地安装 Godot 引擎）
- Python >= 3.8（`godot-data-driven-config` 技能的脚手架脚本需要）

## 安全说明

本插件涉及以下本地行为：

- 是否执行本地命令：是，`godot-headless-verify` 会调用 Godot 命令行工具进行项目验证。
- 是否访问文件系统：是，技能会读写项目目录下的 .gd、.tscn、.tres 文件。
- 是否调用外部服务：否。
- 是否上报数据：否。
- 是否需要用户凭据：否。

## 文件结构

```text
magicai-hub/
├── .codebuddy-plugin/
│   └── plugin.json
├── README.md
└── skills/
    ├── gdscript-codegen/
    │   └── SKILL.md
    ├── godot-asset-path-surgery/
    │   └── SKILL.md
    ├── godot-data-driven-config/
    │   ├── SKILL.md
    │   ├── QUICKREF.md
    │   ├── examples/
    │   ├── schemas/
    │   ├── scripts/
    │   └── templates/
    ├── godot-headless-verify/
    │   └── SKILL.md
    ├── godot-tres-format/
    │   └── SKILL.md
    ├── godot-tscn-format/
    │   └── SKILL.md
    ├── godot-utils/
    │   └── SKILL.md
    └── safe-file-operations/
        └── SKILL.md
```

## 版本

当前版本：1.0.0

## 维护者

- MagicAI Team
