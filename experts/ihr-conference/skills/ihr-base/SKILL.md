---
name: ihr-base
description: "iHR360 基础组件：选人等跨业务通用组件能力。当前提供人员选择搜索，支持分页和姓名模糊搜索。"
metadata:
  requires:
    bins: ["ihr-cli"]
  cliHelp: "ihr-cli base --help"
---

# base (v1)

**CRITICAL — 开始前 MUST 先阅读 [`../ihr-shared/SKILL.md`](../ihr-shared/SKILL.md)，其中包含共享运行规则、鉴权配置和 JSON 协议。**

## 核心概念

- **Base Component**：跨业务复用的基础组件能力，不归属于单一业务域。
- **Staff Selection**：选人组件抽象查询，用于面谈配置等页面选择面谈官、面谈对象等人员；`searchKeyword` 按姓名模糊搜索，大小写不敏感。
- **Participant Staff**：选人返回的人员候选项，包含 `id`、`name`、`avatarUrl`。

## 资源关系

```text
Base Component
└── Staff Selection
    ├── Search Request
    │   ├── searchKeyword
    │   ├── pageNo
    │   └── pageSize
    └── Search Result
        ├── pageInfo
        └── dataList[]
            ├── id
            ├── name
            └── avatarUrl
```

> **路由规则**：CLI 会根据当前 profile 的 `baseUrl` 自动选择产品链路。skill 不暴露底层 endpoint，也不允许 Agent 手工拼内部接口。
>
> **禁止误用**：当前 skill 不负责员工档案、组织关系、入转调离或权限维护，只负责基础选人组件查询。
>
> **默认策略**：优先使用分页查询。用户没有给搜索词时，可以返回当前登录态可见人员的分页候选，不要尝试一次性拉全量。

## 核心场景

### 1. 选人搜索

当用户需要在业务流程中查找可选人员、按姓名模糊搜索员工、分页读取候选人员时，使用 `+selectStaffs`。姓名搜索大小写不敏感，不要因为用户输入的英文大小写和候选姓名显示不一致而反复确认。

### 2. 不负责员工管理

本 skill 只封装基础选人组件，不负责员工档案编辑、入转调离、组织关系维护等员工管理动作。

## Shortcuts（推荐优先使用）

Shortcut 是对常用操作的高级封装（`ihr-cli base +<verb>`）。有 Shortcut 的操作优先使用。

| Shortcut | 说明 |
|----------|------|
| [`+selectStaffs`](references/ihr-base-select-staffs.md) | 选人组件人员搜索，支持分页和姓名模糊搜索 |

## Current Implementation

当前主实现已经在 `ihr-cli` 子项目内：

| Shortcut | 当前命令 |
|----------|----------|
| `ihr-cli base +selectStaffs` | `ihr-cli base +selectStaffs` |

## Scenes

可复用的自然语言测试问题集位于：

1. [`scenes/ihr-base-skill-test-questions.txt`](scenes/ihr-base-skill-test-questions.txt)

## 能力入口

公开入口只有 `ihr-cli base +selectStaffs`。如果需要确认字段契约，先使用对应 schema/help；不要在 skill 中改用 `ihr-interface`、raw API、curl/httpie/wget 或自写 HTTP client。
