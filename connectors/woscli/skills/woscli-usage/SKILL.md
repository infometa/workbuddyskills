---
name: woscli-usage
description: 微盟 WOS CLI 操作技能 - 通过 woscli 命令行工具发现并执行微盟 WOS 业务能力（订单、商品、客户、营销、数据看板等）。内置能力路由：优先复用已安装的微盟专家与 Skill，仅在无可用资产时按 category 限定域检索，避免重复探索导致流程冗长与成本升高。
description_en: Weimob WOS CLI usage - discover and execute Weimob WOS business capabilities (orders, goods, customers, marketing, dashboards, etc.) via the woscli command-line tool. Includes capability routing: reuse installed Weimob experts and skills first, fall back to category-scoped woscli search only when no asset is available, minimizing redundant discovery.
version: "1.1.0"
author: "Weimob WOS"
---

# 微盟 WOS CLI (woscli) Skill

本 Skill 提供通过 `woscli` 命令行工具调用微盟 WOS 业务能力的能力。woscli 是一个命令路由器：它把自然语言任务翻译成对应业务 category 下的具体命令，并通过 Gateway 执行。

> **使用本 Skill 前，先执行第 0 节的「能力路由」判定。** 微盟业务能力存在两层实现：上层的**专家 / Skill 资产**（已封装业务语义、参数校验与话术模板）与底层的 **woscli 命令**（通用但需现场探索）。跳过路由直接用 woscli 从零探索，是流程冗长和成本过高的主要原因。

---

## 0. 能力路由（强制前置步骤）

### 0.1 三层优先级

| 层级 | 手段 | 适用条件 | 探索成本 |
|---|---|---|---|
| L1 资产直达 | 调用已安装的微盟 **专家** 或 **Skill** | 会话中可见该资产 | ≈0（业务语义已封装） |
| L2 语义精搜 | `woscli search "<诉求>" --limit 5 --response-format concise` | 未安装资产；诉求可用一句话描述 | **1 次探索调用**（结果已含必填参数，可直接执行） |
| L3 域内浏览 | `woscli <category> --help --limit 10` | 已确定 category，需了解该域整体能力 | ≥1 次，**存在分页陷阱**，见 §3.2 |

### 0.2 判断资产是否已安装

**以会话中可见的已安装清单为准，不要探测文件系统。**

- **Skill**：会话上下文会列出当前可用的 Skill 清单（名称 + 描述）。对照 §0.3 的资产名称判断是否存在即可。
- **专家**：同理，以会话中已选或可选的专家清单为准。

不要为了确认资产是否存在而遍历目录、读取 `SKILL.md` 的 `name` 字段——资产存储位置属于 WorkBuddy 内部实现，随版本变化，探测既不可靠也额外消耗调用。

### 0.3 诉求 → 资产路由表

命中下表左侧诉求时，若对应资产已安装，**直接调用资产**；未安装则用右侧 category 作为 `search --category <cat>` 的限定域，缩小检索范围。

| 用户诉求 | L1 优先资产（专家 → 内含 Skill） | 兜底 category（用于 search 限定域） |
|---|---|---|
| 经营数据分析、GMV/销量趋势、经营日报、问数、分析报告 | `biz-data-analytics-expert` → `data-analytics` | `chat-bi` / `dashboard` |
| 客户资料、客户列表、按手机号/会员卡号查人 | `customer-member-ops-expert` → `customer-profile` | `customer` |
| 积分方案/积分流水、储值方案/储值流水 | `member-ops` | `customer` |
| 客户跟进话术、导购推荐文案 | `customer-follow-up` | `guide` / `agent-guide` |
| 导购业绩、线索、交易明细 | `guide-management` | `guide` / `team` |
| 查商品、发品、改价、改库存、上下架 | `goods-order-ops-expert` → `goods-ops` | `goods` / `mall-goods` |
| 订单/履约/售后/退款查询与状态变更 | `order-management` | `order` |
| 建活动、促销、优惠券、满减满折、拼团、秒杀 | `marketing-content-expert` → `promotion` | `marketing` / `activity` |
| 写文案、种草文、公众号推文、小红书/朋友圈图文 | `content-creation` | `content` / `smart-content` / `social-content` |
| 商户/门店、店铺经营概览、待办事项 | `merchant-store` | `merchant` / `shops` |
| 页面装修、改组件、搭建 H5 / 移动站 | `renovation` | `cms-page` / `wai-builder` |
| 托管任务查询与关闭 | `hosted-task` | `hosted-task` |
| 微盟产品能力、后台入口、功能配置咨询 | `weimob-knowledge-assistant` → `knowledge-faq` | `faq` |
| 客户标签体系、人群圈选、行为数据 | — | `cdp` |
| 财务账户、交易/退款账单 | — | `finance` |
| 员工/组织/角色权限、渠道 AppID | — | `auth` |
| 礼品卡业务 | — | `giftcard` |
| 图片生成、商品图重绘、图片理解 | — | `image` |
| 跨业务只读查询（活动/商品/订单/客户/门店等） | — | `admin-api` |

### 0.4 未安装资产时的执行原则

1. **不要停下来要求用户先安装资产。** 直接用 L2（必要时 L3）完成当前任务。
2. **仅在任务交付后**做一次轻量提示：说明安装对应专家/Skill 可将该类任务缩短为一步。不要在任务中途插入安装引导。
3. **探索预算上限**：单任务内 woscli 探索类调用（`search` 或 `--help`）累计 **≤ 3 次**。超出后必须停止搜索，向用户确认诉求范围，或基于已有信息给出结论。
4. **批量探测**：涉及多个业务域或子问题时，在**一次工具调用**内串联多条查询，避免多轮往返。

```bash
# Git Bash / Unix：一次调用内探测两个诉求
W="$HOME/.woscli/woscli"; $W search "查询最近订单" --limit 3 --response-format concise; $W search "查询商品库存" --limit 3 --response-format concise
```

```powershell
# PowerShell：一次调用内探测两个诉求
$w = "$env:USERPROFILE\.woscli\woscli.exe"; & $w search "查询最近订单" --limit 3 --response-format concise; & $w search "查询商品库存" --limit 3 --response-format concise
```

5. **不要重复确认**：已通过 `--help` 或 `search` 拿到确切命令名与参数后，直接执行，不做二次探索。

---

## 1. 环境前提

- woscli 已由连接器（CLI 连接器）自动安装到用户目录：
  - Unix：`~/.woscli/woscli`
  - Windows PowerShell：`$env:USERPROFILE\.woscli\woscli.exe`
  - Windows CMD：`%USERPROFILE%\.woscli\woscli.exe`
- 当前会话若刚安装，PATH 可能未生效。验证与调用时**优先使用绝对路径**：
  - Unix：`~/.woscli/woscli ...`
  - Windows PowerShell：`& "$env:USERPROFILE\.woscli\woscli.exe" ...`
  - Windows CMD：`"%USERPROFILE%\.woscli\woscli.exe" ...`
  - 若 `woscli` 已在 PATH 中，可直接使用 `woscli`。

## 2. 登录与鉴权

所有业务命令需要先登录。使用 Bash 工具执行：

```bash
# 登录微盟账号
woscli login

# 查看授权状态与 access token 到期时间
woscli status

# 退出登录
woscli logout
```

> 登录凭证保存在操作系统密钥存储（Windows 凭据管理器 / macOS Keychain / Linux Secret Service），
> 不可用时回退到 `~/.woscli/token.json`（权限 0600）。无需在命令中显式传 token。
> Linux/macOS 使用回退文件时，可执行 `chmod 600 ~/.woscli/token.json` 重新收紧文件权限。
>
> `woscli status` 会显示 `已授权，access token 到期时间：<时间>`；未授权时显示非 `已授权` 字样。
>
> WorkBuddy 连接器配置了 `authSuppressBrowser=true`，不会由连接器自动打开授权页。
> 执行 `woscli login` 后，按终端提示复制授权 URL 到浏览器并完成授权。
>
> **woscli 无自动刷新机制**：access token 到期后不会静默续期，执行命令会报鉴权错误。此时只需重新执行 `woscli login` 完成授权即可，无需其他刷新流程。

## 3. 发现可用命令（关键）

**先发现，再执行；但只发现必要的那一次。** 按 §0.1 的层级选择手段。

### 3.1 首选：语义精搜（一次调用即可执行）

```bash
woscli search "查询最近10笔订单" --limit 5 --response-format concise
woscli search "修改商品库存" --category goods --limit 5 --response-format concise
```

`concise` 输出包含 `CATEGORY / COMMAND / DESCRIPTION / REQUIRED INPUTS` 四列——**必填参数已直接给出**。因此标准路径是两步：

```
search concise（拿到命令名 + 必填参数） → 直接执行
```

只有在需要**可选参数**（分页、排序、时间范围等）时，才追加第三步 `woscli <category> <command> --help`。

### 3.2 次选：域内浏览（注意分页陷阱）

```bash
# 浏览某个业务域下的命令
woscli order --help --limit 10
woscli goods --help --limit 10

# 查看某条命令的详细参数
woscli order <command> --help
woscli goods <command> --help --output-format json
```

> **分页陷阱**：`<category> --help` 默认 **5 条/页**，而大业务域命令量极大（如 `order` 59 条 / 12 页、`goods` 125 条 / 25 页）。翻遍一个域需要十几次调用，是成本失控的主要来源。
> **禁止逐页翻完。** 需要域内检索时，用 `--limit` 提高单页密度（如 `--limit 10`），或**改用 §3.1 的 search 精确命中**。

常用业务域（category）包括：`order`(订单与售后)、`goods`(商品管理)、`customer`(客户资料与关系)、`marketing`(营销活动与优惠权益)、`dashboard`(数据看板)、`cdp`(客户数据与行为)、`content`(内容管理)、`merchant`(商户)、`finance`(财务与资金)、`team`(团队与组织)、`image`(图片创建重绘与理解) 等。完整列表运行 `woscli --help`（其 Categories 段为权威清单，随版本变化）。

> `search` 默认返回详细内容，token 消耗较大。**无特殊需要一律加 `--response-format concise --limit 5`**。

## 4. 执行命令

```bash
# 通用格式
woscli <category> <command> [arguments] [--output-format json|table]

# 完整只读示例：搜索可用优惠券模板
woscli marketing coupon-template-search --keyword "满减" --coupon-type 1 --status 1 --output-format json

# 完整只读示例：查询客户余额明细（替换为已确认的 wid）
woscli customer balance-detail --wid 1001693477 --output-format json
```

- 为保证稳定的机读结果，推荐显式传入 `--output-format json`；不要依赖当前默认输出格式。`--output-format table` 更适合人类阅读。
- 所有命令名、参数名统一为 **kebab-case**（短横线命名），例如 `--output-format`、`--meeting-id`。严禁驼峰。

典型 JSON 响应结构如下；实际 `data` 字段以具体命令返回为准：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 0
  }
}
```

写操作参数示例（仅用于展示参数形态）：

```bash
# 必须先把示例 ID 替换为已核实的目标，展示完整命令与影响范围，并取得用户明确确认
woscli marketing coupon-send --coupon-nums '[{"couponTemplateId":1763208,"num":1}]' --scene 945000 --vid 62265165165 --vid-type 2 --wid 12345678 --output-format json
```

## 5. 使用约定与注意事项

- **路由优先**：先按 §0 判定是否存在可复用资产，再决定是否使用 woscli。命中 L1 后禁止重复探索。
- **先搜索后执行**：遇到不确定的能力，先用 `woscli search` 或 `<category> --help` 确认命令与参数，避免猜测导致报错。
- **参数使用 kebab-case**，与 woscli 规范一致。
- **列表/批量参数**优先用重复 flag（如 `--id a --id b`）；仅在结构复杂且数据量小（< 1KB）时用 JSON 字符串。
- **只读优先**：查询类命令默认安全；写操作（创建/更新/取消/删除）执行前确认影响范围且必须取得用户确认。
- **不可逆操作警示**：删除、核销、发券、上架等操作可能立即影响线上数据或消费者可见内容。执行前必须展示完整命令和目标对象，说明影响范围，并取得用户明确确认；不得用示例 ID 直接执行。**提速不得以跳过写操作确认为代价。**
- **控制输出体积**：列表查询显式传 `--page-size`，避免拉取全量数据后再在上下文中裁剪。
- **超时与调试**：HTTP 超时用 `--timeout <秒>`；排错加 `--debug` 查看请求细节。

## 6. 常见错误与处理

- **鉴权错误（401 / 403）**：多为 access token 失效，执行 `woscli login` 重新授权即可。
- **限流（429）**：稍作退避后重试；如频繁触发，降低并发与请求频率。
- **命令未找到 / PATH 未生效**：用绝对路径调用（见 §1），或新开终端使 PATH 生效。
- **参数错误**：先 `woscli <category> <command> --help` 确认参数，勿凭猜测；同一错误不重复试错超过 2 次。
- **分页 / 列表翻页**：列表类命令通常支持 `--page <n>` 与 `--page-size <n>`（以 `--help` 输出为准），按需翻页获取全量数据。

## 7. 典型工作流

1. 用户提出业务诉求（如"查一下最近 10 笔订单"）。
2. **路由判定**：对照会话中可见的已安装 Skill / 专家 → 有 `order-management` 或 `goods-order-ops-expert` 则直接调用，跳到第 6 步。
3. 无资产时执行 `woscli search "查询最近10笔订单" --limit 5 --response-format concise`，从结果中取 `CATEGORY + COMMAND + REQUIRED INPUTS`。
4. 需要可选参数（时间范围、分页等）时才补一次 `woscli <category> <command> --help`。
5. 用绝对路径执行：`~/.woscli/woscli order <command> --page-size 10 --output-format json`。
6. 解析返回的 JSON 数据，整理后回复用户；若本任务是靠 woscli 完成的，结尾可提示安装对应专家/Skill 的收益。

**成本对照**：同一诉求下，L1 资产直达约 1 次调用；L2 语义精搜 2 次调用；未加约束的自由探索（search → 多次 `--help` 翻页 → 试错）通常 6 次以上。

## 8. 升级与卸载

- 升级：重新执行连接器安装流程。安装脚本只接受与发布清单 SHA256 一致的官方产物；若校验失败，停止安装并联系发布方更新连接器校验值。
- Unix 卸载：确认没有运行中的 `woscli` 进程后删除 `~/.woscli`，并从 shell 配置文件中移除对应的 PATH 行。
- Windows 卸载：确认没有运行中的 `woscli.exe` 后删除 `%USERPROFILE%\.woscli`，并在用户环境变量 PATH 中移除该目录。
