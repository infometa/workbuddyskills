---
name: yunsu-office-assistant
display_name: 企业办公助手
description: 查询企业办公平台的待办事项、流程审批列表和流程详情。当用户询问"我今天要做什么"、"我有哪些待审批的流程"、"这个流程走到哪一步了"、"还差谁审批"时使用。
description_zh: 查询企业办公平台的待办事项、流程审批列表和流程详情，快速了解工作进展和审批状态
description_en: Query pending tasks, approval workflows, and process details from enterprise office platform
version: 1.0.0
author: 云速易连
agent_created: true
allowed-tools: fs_find_todo,fs_process_list,fs_process_detail,get_current_identity
category: productivity
tags:
  - 办公
  - 审批
  - 流程
  - 待办
  - 工作管理
---

# 企业办公助手

## 技能概述

本技能帮助企业用户高效管理办公平台的待办事项和流程审批任务。

## 工具使用说明

### 工具调用方式

本技能依赖的工具由 WorkBuddy 自动发现和加载，无需手动查询 schema。直接在对话中说明需求即可，WorkBuddy 会自动选择合适的工具并传入参数。

**工具列表**：

| 工具名称 | 说明 |
|---------|------|
| `get_current_identity` | 获取当前登录身份 |
| `fs_find_todo` | 查询待办消息 |
| `fs_process_list` | 查询流程列表 |
| `fs_process_detail` | 查询流程详情 |

### 1. get_current_identity（获取当前登录身份）

获取当前登录用户的身份信息，用于确认"我是谁"。

**参数**：无

**返回**：
- `userId`：用户唯一标识
- `userName`：用户姓名
- `boundSystemCodes`：已绑定的系统编码列表（用于跨系统待办过滤）

**使用场景**：
- 确认当前登录用户身份
- 获取已绑定的系统列表（用于 `appName` 参数的合法值）

### 2. fs_find_todo（查询待办消息）

获取当前用户的待办消息和通知提醒。

**参数**：
- `status`（可选）：消息状态（1-待办，2-已办，3-待阅，4-已阅）
- `appName`（可选）：来源系统标识，用于跨系统待办过滤（合法值从 `get_current_identity` 的 `boundSystemCodes` 获取）
- `moduleName`（可选）：来源模块标识
- `offset`（可选）：分页偏移量，默认0
- `pageSize`（可选）：每页条数，默认1000

**返回**：消息列表（字段详见 @references/mcp-tools.md）

**注意**：
- 默认 `pageSize=1000`，如果返回的 `totalSize` 大于实际返回条数，需要翻页查询
- 翻页方式：增加 `offset` 值（如 `offset=1000`、`offset=2000`）

### 3. fs_process_list（查询流程列表）

查询当前用户的流程审批任务列表。

**参数**：
- `queryType`（可选）：查询类型，默认 `myApproving`
  - `myApproving`：我的待办（需要我审批的流程）
  - `myApproved`：我的已办（我已审批的流程）
  - `myCreated`：我发起的（我创建的流程）
  - `myFollowed`：流程跟踪（我关注的流程）
  - `myReading`：流程送阅（需要我阅读的流程）
  - `myDraft`：我的草稿（我保存的草稿）
  - `flow`：流程库（所有流程，需要管理员权限）
- `keyword`（可选）：标题关键词
- `offset`（可选）：分页偏移量，默认0
- `pageSize`（可选）：每页条数，默认20

**返回**：流程列表（字段详见 @references/mcp-tools.md）

**注意**：
- 默认 `pageSize=20`，如果返回的 `totalSize` 大于实际返回条数，需要翻页查询
- 翻页方式：增加 `offset` 值（如 `offset=20`、`offset=40`）
- **当前处理人和当前节点**：读取 `currentHandlerNames` 和 `currentNodeNames`

### 4. fs_process_detail（查询流程详情）

根据流程实例ID查询单个流程的完整信息。

**参数**：
- `fdId`（必填）：流程实例ID，从 `fs_process_list` 返回的 `fdId` 字段获取

**返回**：流程详细信息（字段详见 @references/mcp-tools.md）

## 核心工作流

### 场景 1：每日工作概览

**用户提问**："我今天要做什么？"

**执行步骤**：

1. 调用 `get_current_identity` 确认当前用户身份
2. 调用 `fs_find_todo` 查询待办消息（`status=1`）
3. 检查返回的 `totalSize`，如果大于实际返回条数，翻页查询（`offset=1000`、`offset=2000`）
4. 按紧急程度（todoLevel）排序，优先显示紧急任务
5. 归纳总结待办事项，生成工作清单

### 场景 2：流程审批跟踪

**用户提问**："我有哪些待审批的流程？"

**执行步骤**：

1. 调用 `fs_process_list` 查询流程列表（`queryType=myApproving`）
2. 检查返回的 `totalSize`，如果大于实际返回条数，翻页查询（`offset=20`、`offset=40`）
3. 提取关键信息（流程标题、当前节点、当前处理人）
4. 生成审批任务清单

### 场景 3：流程详情查看

**用户提问**："这个报销申请的具体内容是什么？"

**执行步骤**：

1. 调用 `fs_process_list` 查询流程列表，获取 `fdId`
2. 调用 `fs_process_detail` 查询流程详情（传入 `fdId`）
3. 提取表单自定义字段，生成详细报告

### 场景 4：催办查询

**用户提问**："还差谁审批？"

**执行步骤**：

1. 调用 `fs_process_list` 查询流程列表（`queryType=myApproving`）
2. 提取当前处理人（`currentHandlerNames`）和当前节点（`currentNodeNames`）
3. 生成催办清单

### 场景 5：跨系统待办查询

**用户提问**："只查看人事系统的待办"

**执行步骤**：

1. 调用 `get_current_identity` 获取已绑定的系统列表（`boundSystemCodes`）
2. 从 `boundSystemCodes` 中找到人事系统的编码（如 `hr-system`）
3. 调用 `fs_find_todo` 查询待办消息（`status=1, appName="hr-system"`）
4. 生成跨系统待办清单

## 数据处理

### 时间戳转换

工具返回的时间字段均为毫秒时间戳，使用 `scripts/transform.py` 转换为可读格式。

**使用方法**：

```bash
# 单个时间戳
python scripts/transform.py 1791452769307

# 批量转换多个时间戳（推荐，性能更好）
python scripts/transform.py 1791452769307 1791452769308 1791452769309

# 自定义格式
python scripts/transform.py 1791452769307 --format "%Y-%m-%d"
```

**输出示例**：

```
2026-10-08 17:46:09
```

**降级策略**（Shell 不可用时）：
- AI 直接读取时间戳，手动转换为可读格式
- 转换方法：毫秒时间戳 ÷ 1000 = 秒级时间戳，使用 `datetime.fromtimestamp()` 转换
- **注意时区**：固定使用 GMT+8（北京时间），不要使用本机时区

## 错误处理

### 工具调用失败

如果工具调用失败，返回错误信息给用户，不要编造数据。

### 无数据

如果查询结果为空，明确告知用户"没有找到相关数据"，不要编造数据。

### 流程不存在或已删除

如果查询的流程不存在或已被删除，工具会返回错误。此时应告知用户"该流程不存在或已被删除，请确认流程是否正确"，并建议用户重新查询流程列表获取最新的流程ID。

### 超过 1000 条

如果查询结果超过 1000 条，提示用户"结果过多，请缩小查询范围"（如添加关键词过滤）。

## 输出约定

- **对话输出**：查询结果直接在对话中展示，不要落盘
- **格式化**：使用 Markdown 表格或列表格式化输出
- **时间格式**：统一使用 `yyyy-MM-dd HH:mm:ss` 格式

## 参考资料

- [MCP 工具说明](references/mcp-tools.md)：详细说明四个工具的参数和返回值
- [使用示例](references/examples.md)：更多使用场景和示例

## 依赖说明

- 需要安装 Python 3.x（用于运行 `scripts/transform.py`，Shell 可用时）
- 如果 Shell 不可用，AI 可以直接处理时间戳转换（降级策略）
