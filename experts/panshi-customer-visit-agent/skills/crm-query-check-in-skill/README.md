# 拜访打卡记录查询 Skill（crm-query-check-in-skill）

## 📖 简介

基于磐石 CRM 的**拜访打卡记录查询** Skill（原名"签到打卡"已统一改称"拜访打卡"）。通过自然语言对话，自动识别当前用户角色、按需收集查询条件，并以结构化格式展示查询结果，同时标注每条拜访打卡的**绑定状态**（是否已关联跟进记录）。所有接口统一通过 `omp-service` 的 `request_api` 工具转发调用。

## ✨ 核心特性

- 🗂️ **两种查询类型** — `type=2`（默认）我的全部签到；`type=1` 近 15 天且未被关联的签到（可关联池）
- 🔍 **灵活过滤** — 支持按客户、地址、关键词、时间范围等条件过滤
- 🏢 **客户搜索** — 用户提到客户名时，自动搜索换取 cid 后再查询
- 🔗 **绑定状态标注** — 每条记录显示是否已绑定跟进记录及对应记录 ID
- 📄 **分页浏览** — 支持「下一页」「查看第 N 页」翻页
- 🔀 **统一调用** — 全部接口经 `omp-service` 的 `request_api` 转发，凭据由 MCP 层管理

## 🎯 触发场景

当用户表达以下意图时触发：

> 查打卡记录、查签到记录、签到列表、我的签到、打卡列表、看看签到情况、
> 查一下打卡、有哪些签到记录、最近签到、未关联的签到、
> query check-in records、list sign-in records、show check-ins

## 📂 目录结构

| 文件 | 说明 |
|------|------|
| `SKILL.md` | Skill 主文件：角色定义、强制约束、执行流程、交互规范、异常处理 |
| `API_REFERENCE.md` | 接口参数规范、角色鉴权逻辑、finalRole 计算规则、查询接口详情 |
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
| 签到记录查询 | `csm/GetVisitCheckInsListForMcp` |

## 🔒 凭据安全说明

> 本 Skill 不接触、不存储、不传递任何明文凭据。

- **鉴权由 MCP 层统一处理**：访问凭据在 MCP 客户端（CodeBuddy / AnyWork）的 MCP 配置中维护，Skill 文件内不出现任何 `token`、`api_key`、`Bearer` 认证头、`Authorization` 头或密钥。
- **禁止硬编码凭据**：如确需引用凭据，一律通过**环境变量**（如 `${OMP_SERVICE_TOKEN}`）或**外部配置文件**引用，不得写入 Skill 文件或提交到仓库。
- **仅传业务参数**：接口调用只携带 `role`、`cid`、`type`、查询条件等业务参数；其中 RTX 从环境信息自动获取，属于用户标识而非密钥。

## 🚦 执行流程概览

```
Step 1  识别查询类型（type=1 未关联 / type=2 我的全部，默认 2）并收集查询条件；
        提到客户名时先经 request_api 转发调用 csm/GetCustomerListForVisitForMcp 换取 cid
Step 2  通过 request_api 转发调用 csm/GetVisitCheckInsListForMcp 查询拜访打卡记录
        ⚠️ 必传参数：type
Step 3  按格式结构化展示结果，标注绑定状态，支持分页
```

> 详细规则见 `SKILL.md`，接口参数见 `API_REFERENCE.md`。

## 💡 使用示例

| 用户输入 | Skill 行为 |
|---------|-----------|
| 「查一下我的签到记录」 | 默认 `type=2` 查询全部签到记录 |
| 「有哪些未关联的签到」 | `type=1` 查询近 15 天未绑定跟进记录的签到 |
| 「看看腾讯科技的打卡」 | 搜索客户「腾讯科技」→ 换取 cid → 过滤查询 |
| 「查 4 月份在深圳的签到」 | 带时间范围 + 地址/关键词查询 |
| 「下一页」 | 翻到下一页继续展示 |

## 🛟 异常与降级

| 场景 | 处理 |
|------|------|
| 角色查询失败 | 提示「角色权限查询失败，请稍后重试」，终止流程 |
| 客户名未匹配 | 先搜「我相关」再搜「长尾客户」，仍为空则提示确认归属 |
| MCP 调用失败 | 重试 1 次，仍失败提供磐石跳转链接 |
| 权限不足 | 提示联系主销售确认 |

磐石跳转：
- PC：`https://panshi.woa.com/sales-manager/tool/follow-up-record-management?guide-route-business-enumeration-type=crm-system`
- 小程序：磐石 CRM → 跟进拜访管理 → 拜访打卡

## 🏷️ 版本

- **version:** 1.0.0
