# 意图判定、版本路由与通用规则

## 何时使用

任何与「报告 / 周报 / 月报 / 季报 / 年报 / 年中报告」相关的请求，先读本 reference 完成意图判定和链路判定，再按需读取其它 reference。

## 一、意图判定（最高优先级）

自上而下命中即止，命中后不再二次询问。

### 1. B 链路（查询与管理已有报告）——禁止采集业务数据

消息中出现以下任一信号即走 B：

`查看` / `查询` / `列表` / `共享给我的` / `团队` / `下属` / `成员` / `某某某的报告` / `已提交` / `发布` / `撤回` / `修改` / `提醒他们交报告`。

B 链路只调用报告侧 operation，**禁止**因为「报告」二字去调用 IM消息、日报、日程、会议、项目任务、客户营销、流程等业务模块采集数据。

### 2. A 链路（生成与汇总报告）——必须采集业务数据

未命中 B 链路任何信号，且同时满足以下两个要素时走 A：

- 动词要素：汇总 / 生成 / 写 / 整理 / 总结 / 帮我出一份；
- 对象要素：周期词（周报 / 月报 / 季报 / 年报 / 周 / 月 / 季度 / 本周 / 上周 / 本月 / 上月 / 本季度 / 上季度）+ 内容词（报告 / 周报 / 内容 / 工作 / 总结）。

### 3. 默认值规则

动词为「汇总 / 生成 / 写 / 整理」，对象含周期与报告类名词，且未命中 B 链路信号时，一律按 A 处理，默认采集**当前登录人自己**的业务数据。以下说法直接归入 A：

- 汇总上周报告、汇总本周报告、汇总上月报告、汇总上季度报告；
- 生成上周报告、生成本周报告、帮我写周报 / 写月报 / 写季报 / 写年报；
- 帮我整理上周工作写报告、把上周的工作总结成周报。

A 链路的完整作业步骤见 [`plan-collect-and-compose.md`](plan-collect-and-compose.md)。

## 二、版本路由与租户缓存

报告侧接口分标准版与 e10-ebuilder 版两套链路，由 CLI 统一判定，Agent **不要手工选择链路**。

| 步骤 | 行为 |
| --- | --- |
| 1 | 优先读租户隔离、有效期 1 天的版本判定缓存；命中且未过期直接复用，跳过版本接口 |
| 2 | 缓存缺失或过期时调用 `plan_searchAppver`，读取返回字段 `ver_name` |
| 3 | `ver_name = V2` → 全部报告侧接口走 **e10-ebuilder 链路**；其它情况 → **标准版链路** |
| 4 | 把判定结果写入租户缓存，有效期 1 天 |

禁止行为：不读缓存直接调版本接口；缓存过期不重新拉取；跳过版本判定硬编码链路；eb 链路命中后混用标准版接口。

- 查看当前判定结果：`plan.version.check`（或 `plan route`），返回 `link`（`standard` / `eb`）、`verName`、`cached`、`degraded`。
- `degraded: true` 表示版本接口暂不可用、已降级为标准版链路，此时不写缓存，下次会重试。
- **采集业务数据阶段禁止调用版本接口和任何报告侧接口**，只在判定为 B 链路、或 A 链路走到「用户确认后做重复性检查」时才允许触发版本路由。

### eb 报告详情页表单 id

eb 链路详情页地址为 `/sp/ebdfpage/card/0/{报告详情 eb 表单 id}/{报告 id}`，其中表单 id 指 **idobjId**（不是 formId）。`plan.eb.form.resolve` 负责解析：

- 应用 appTag：`weaver-wrplan-eb`；报告详情表单 tag：`uf_plan_work_report`。
- 租户 key 为 `tt1pa2w2i3` 时无需动态获取，固定为 `1029659181695361024`；其它租户按 appTag、表单 tag 动态获取。
- 取到后按租户**长期缓存**，后续直接使用，不再动态获取。

`plan.report.get` 与 `plan.report.page` 已在 `detailUrl` 中返回拼好的详情页地址，Agent 直接用即可。

## 三、operation 总表

| operation | 风险 | 说明 |
| --- | --- | --- |
| `plan.version.check` | read | 判定租户报告链路，命中缓存则跳过接口调用 |
| `plan.eb.form.resolve` | read | 解析 eb 报告详情表单 id（idobjId） |
| `plan.report.get` | read | 按 id 或按周期查询单份报告详情，附带评论总条数 |
| `plan.report.page` | read | 分页查询报告列表 |
| `plan.comment.list` | read | 查询报告评论内容（标准版链路） |
| `plan.report.create.prepare` / `.apply` | read-before-write / high-risk-write | 新建报告 |
| `plan.report.update.prepare` / `.apply` | read-before-write / high-risk-write | 修改报告 |
| `plan.report.publish.prepare` / `.apply` | read-before-write / high-risk-write | 发布报告 |
| `plan.report.withdraw.prepare` / `.apply` | read-before-write / high-risk-write | 撤回报告（标准版链路） |
| `plan.report.remind.prepare` / `.apply` | read-before-write / high-risk-write | 发送提交提醒（标准版链路） |

字段细节以 `weaver-work-cli --profile eteams plan schema` 为准。

## 四、通用基础规则（两条链路均生效）

1. **周期计算**：周报年份、周数严格遵循 ISO8601，1 月 4 日所在周为当年第 1 周。未明确周期类型时先向用户确认周/月/季/年，确认前不得臆造区间。
2. **跳转能力**：报告新建、查询、修改、发布、撤回成功后，必须把 `detailUrl` 呈现为可点击链接。
3. **分页表格输出**：分页接口返回的列表必须用表格展示，固定列为 **报告名称 / 报告创建人名称 / 发布时间**；报告名称可点击，直接跳转 `detailUrl`。
4. **人员 ID 规则**：所有传递和获取人员 id 的地方，都取 `id` 或 `employeeId` 字段，**禁止取 `userId`**。人员信息通过 weaver-e10-hrm-connector skill 获取。
5. **雪花 ID 传参**：请求体中的雪花 ID（人员 ID、报告 ID 等）必须加引号包裹为字符串，避免数字精度丢失。CLI 已完成归一化，业务输入按字符串传更安全。
6. **重复性判断**：判断当前人员是否提交某个周期的报告，**只能**通过 `plan.report.get` 按周期查询（必须传报告年份、报告类型、报告周期，创建人缺省为当前登录人）。
7. **不得重复创建**：当且仅当用户确认需要创建某个周期的报告时才判断是否已创建；若已创建，不得重复创建，需明确告知用户并征询是否改为编辑。
8. **字段名禁止项**：任何执行阶段和最终创建的报告内容中，决不允许出现报告相关的数据库英文字段名。CLI 已把 eb 链路返回值归一化为业务字段（`reportId` / `title` / `content` / `summary` / `plans` / `year` / `type` / `serialNumber` / `postStatus` / `postTime` / `creator` / `detailUrl`），Agent 只使用这些业务键，不要向用户复述原始接口结构。
9. **认证三件套**：所有请求必须携带完整登录态（Cookie 完整原始串、eteamsid、User-Agent）。由 CLI 托管，禁止输出、索取或写入任何凭证；未登录时先按共享规则读取 `../weaver-e10-shared-connector/references/e10-auth-and-session.md` 并通过 `weaver-work-cli auth ...` 确认会话。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.version.check --input-json '{"refresh":false}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.version.check --input-json '{"refresh":false}'
```

强制重新判定链路：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.version.check --input-json '{"refresh":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.version.check --input-json '{"refresh":true}'
```

## 输出处理

`plan.version.check` 返回示例（字段说明）：

- `link`：`standard` 或 `eb`，本次生效的链路。
- `verName`：版本接口返回的 `ver_name` 原始值。
- `cached`：本次结果是否来自缓存。
- `degraded`：是否因版本接口不可用而降级为标准版。

## 注意

- 报告侧接口链路由 CLI 判定并缓存；Agent 不要缓存或自行推断链路。
- 采集阶段（A 链路第 1~7 步）不得触发版本接口或报告侧接口。

## 失败处理

- `authentication` / `session_expired`：引导用户断开并重新连接本连接器以重新登录。
- `policy` / `link_unsupported`：该能力在当前链路不可用，按 `message` 给出的替代路径处理。
- `endpoint_not_found`（HTTP 404）：当前环境可能未部署「计划报告」相关应用或接口，先向用户说明再决定是否停止。
