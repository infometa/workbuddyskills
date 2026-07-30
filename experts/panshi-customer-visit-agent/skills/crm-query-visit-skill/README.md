# 跟进记录查询 Skill（crm-query-visit-skill）

## 📖 简介

基于磐石 CRM 的**跟进记录（跟进/拜访记录）查询** Skill。通过自然语言对话，自动识别当前用户角色、按需收集查询条件，并以结构化格式展示查询结果。所有接口统一通过 `omp-service` 的 `request_api` 工具转发调用。

## ✨ 核心特性

- 🔍 **多对象查询** — 支持按客户 / 商机 / 线索查询，自动搜索换取对应 ID
- 🕒 **灵活过滤** — 支持时间范围、跟进方式（线下拜访 / 线上沟通 / 跟进进展）等条件
- 📄 **分页浏览** — 支持「下一页」「查看第 N 页」翻页
- 📄 **分页浏览** — 支持「下一页」「查看第 N 页」翻页
- 🔀 **统一调用** — 全部接口经 `omp-service` 的 `request_api` 转发，凭据由 MCP 层管理
- 📄 **分页浏览** — 支持「下一页」「查看第 N 页」翻页

## 🎯 触发场景

当用户表达以下意图时触发：

> 查跟进记录、查询跟进、看跟进记录、最近的跟进、跟进列表、我的跟进、
> 拜访记录查询、查一下跟进、看看跟进情况、有哪些跟进记录、
> query visit records、list follow-up records、show visits

## 📂 目录结构

| 文件 | 说明 |
|------|------|
| `SKILL.md` | Skill 主文件：角色定义、强制约束、执行流程、交互规范、异常处理 |
| `API_REFERENCE.md` | 接口参数规范、角色鉴权逻辑、finalRole 计算规则、各查询接口详情 |
| `ENUMS.md` | 所有枚举值定义（纪要类型、跟进渠道、职位列表等） |
| `FIELDS_CONFIG.md` | 各角色 × 跟进对象 × 跟进方式的字段配置（字段名、必填规则、条件显示逻辑） |
| `README.md` | 本说明文档 |

## ⚙️ 前置配置

本 Skill 依赖 MCP 服务 `omp-service`（地址：`https://omp-service.mcp.it.woa.com/csm`），使用前需在 CodeBuddy 或 AnyWork 的 MCP 设置中预先配置。

**统一调用方式**：所有接口均通过 `omp-service` 的 `request_api` 工具转发调用，原接口名作为 `apiPath` 参数传入：

```
use_mcp_tool(
  serverName="omp-service",
  toolName="request_api",
  arguments={
    "apiPath": "<接口路径>",
    "data": { ...业务参数... }
  }
)
```

涉及的接口（apiPath）：

| 用途 | apiPath |
|------|---------|
| 客户搜索 | `csm/GetCustomerListForVisitForMcp` |
| 跟进记录查询 | `csm/GetVisitListForMcp` |
| 商机搜索 | `ltc.project/list` |
| 线索搜索 | `opportunity_node/get_lead_list` |

## 🔒 凭据安全说明

> 本 Skill 不接触、不存储、不传递任何明文凭据。

- **禁止硬编码凭据**：如确需引用凭据，一律通过**环境变量**（如 `${OMP_SERVICE_TOKEN}`）或**外部配置文件**引用，不得写入 Skill 文件或提交到仓库。
- **仅传业务参数**：接口调用只携带 `role`、`cid`、查询条件等业务参数；其中 RTX 从环境信息自动获取，属于用户标识而非密钥。

## 🚦 执行流程概览

```
Step 1  收集查询条件（可选）：客户/商机/线索、时间范围、跟进方式等；
        对象名先经 request_api 转发调用对应搜索接口换取 ID
Step 2  通过 request_api 转发调用 csm/GetVisitListForMcp 查询跟进记录
        ⚠️ 必传参数：switch_panshi_base=1、tab_type=3
Step 3  按 finalRole 字段配置结构化展示结果，支持分页
```

> 详细规则见 `SKILL.md`，接口参数见 `API_REFERENCE.md`。

## 💡 使用示例

| 用户输入 | Skill 行为 |
|---------|-----------|
| 「查一下我的跟进记录」 | 直接查询当前用户全部跟进记录 |
| 「看看腾讯科技最近的跟进」 | 搜索客户「腾讯科技」→ 换取 cid → 查询该客户跟进记录 |
| 「查 4 月份的线下拜访记录」 | 带时间范围 + 跟进方式（type=10000）查询 |
| 「下一页」 | 翻到下一页继续展示 |

## 🛟 异常与降级

| 场景 | 处理 |
|------|------|
| 客户名未匹配 | 先搜「我相关」再搜「长尾客户」，仍为空则提示确认归属 |
| MCP 调用失败 | 重试 1 次，仍失败提供磐石跳转链接 |
| 权限不足 | 提示联系主销售确认 |

磐石跳转链接：
`https://panshi.woa.com/sales-manager/tool/follow-up-record-management?guide-route-business-enumeration-type=crm-system`

## 🏷️ 版本

- **version:** 1.0.0
