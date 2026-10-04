---
name: grain-print
description: 连接 GrainPrint 配送打印终端，查询今日待打印配送单并预览/确认打印。
---

# GrainPrint 配送打印连接器

本连接器面向蔬果生鲜配送商，连接本地的 GrainPrint 打印终端，把"今天有哪些客户要送货、各自打什么单"用自然语言搞定。打印动作会真实出纸，属于高风险操作，必须走「预览 → 确认」两段式。

## 前置条件

- 用户已安装并登录 GrainPrint 桌面打印终端（相当于打印机驱动），且处于在线状态。
- 连接时已填写连接器凭证（GRAIN_TOKEN）与 API 基础地址（GRAIN_API_BASE）。凭证由管理员用登录会话调用后台 `POST /api/connector/credential/issue` 签发，明文仅返回一次，用户需向管理员索取。配送商归属由凭证在服务端解析，无需单独填写 disId。
- 用 `get_app_status` 可随时确认终端是否在线。终端不在线时不要继续打印，先提示用户打开 GrainPrint。

## 工具 Usage

### get_delivery_customers
列出今日有待打印配送单的客户（部门）清单，每个客户带回 `requiresPrintModeChoice` 标记。
- 返回字段含：客户/部门 id、名称、订单数、金额、是否含子部门。
- 这是所有打印操作的入口：先调它拿到今日客户，再决定下一步。

### preview_delivery_order
预览某客户的配送单内容，不真正出纸。
- 参数：`department_id`（必填）、`print_mode`（`all`=全店 / `sub`=分部门，默认 `all`）、`sub_department_id`（print_mode=sub 时生效）。
- 单部门客户可直接进入确认；多子部门客户（`requiresPrintModeChoice=true`）预览后须让用户选择范围，再确认。

### confirm_print_delivery_order
受理打印：**先校验凭证与 GrainPrint 当前会话一致性，再生成可查询的打印任务（入队），不直接出纸**。出纸由 GrainPrint 执行端领取任务后完成。
- 参数同 `preview_delivery_order`，另含 `reprint`（默认 false；`true`=用户确认后的补打，强制新建任务不受去重约束）。
- 返回 `taskId` 与初始状态 `pending`（已受理）。用 `get_print_task_status` 跟踪 `pending→accepted→done/failed`。
- **调用前必须确认**：单部门客户可直接确认；多子部门客户必须先问用户选 `all` 还是 `sub`（或逐项），不得自行默认全部打印，避免误打大量单据。
- 若连接器凭证与 GrainPrint 当前登录配送商不一致，将拒绝受理。

### print_each_subdepartment_delivery_order
对父门店下每个子部门各入队一次打印任务（内部多次 confirm，间隔 `interval_ms` 默认 2800ms），用于需要在每个子部门小票上分别出纸的场景。
- 参数：`department_id`（父部门 id，误传子部门会自动归并到所属父行）、`interval_ms`（可选）。
- 属于批量打印，务必在确认用户确实要"逐子部门打印"后再调用。

### get_app_status
获取 GrainPrint 终端连接状态与登录信息。任何打印前的健康自检都先调用它。

### get_print_task_status
查询已受理打印任务的状态（`pending`/`accepted`/`done`/`failed`）与执行结果。
- 参数：`task_id`（来自 `confirm` / `print_each` 返回）。
- **受理 ≠ 打印完成**：`pending`/`accepted` 仅代表已受理/已领取，`done` 才代表出纸成功，`failed` 代表出纸失败。

## 高风险确认规则

1. 打印前一律先 `preview` 给用户看内容。
2. 多子部门（`requiresPrintModeChoice=true`）**必须**回问用户打印范围（全部 / 指定子部门 / 逐项），不可静默全打。
3. `confirm_print_delivery_order` 与 `print_each_subdepartment_delivery_order` 会真实消耗纸张，调用前用一句话复述"将打印 XX 客户（范围：all/sub）"，取得确认。
4. 终端离线（`get_app_status` 异常/未登录）时中止打印流程，提示用户开启 GrainPrint 桌面端。

## 常见错误与恢复

| 现象 | 含义 | 处理 |
|---|---|---|
| 凭证无效 / 已过期 / 已撤销 | GRAIN_TOKEN 失效 | 让用户向管理员重新签发凭证后重连 |
| 403 资源不属于当前配送商 | 传入的部门不属于凭证绑定的 disId | 用 `get_delivery_customers` 重新取部门，不要手工构造 id |
| 终端离线 / 未登录 | GrainPrint 桌面端没开或没登录 | 提示用户打开并登录桌面端，再用 `get_app_status` 复检 |
| 任务长期停在 `pending` | 桌面端未领取任务 | 确认桌面端在线；不要重复 confirm，先用 `get_print_task_status` 跟踪 |

## 典型流程

1. 用户："今天有啥要打的" → `get_delivery_customers`
2. 用户："打 3 号客户" → `preview_delivery_order(department_id=3)`，展示内容
3. 用户确认 → `confirm_print_delivery_order(department_id=3)`
4. 遇到多子部门客户，先问范围再 confirm。
