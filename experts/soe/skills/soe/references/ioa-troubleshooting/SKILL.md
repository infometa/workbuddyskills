---
name: ioa-troubleshoot-expert
description: "腾讯 iOA 零信任终端安全（私有化部署）排障领域入口：可信接入、终端资产、策略管控、安全检测、平台运维、咨询判断、开放接口调用、只读 SQL 查询八大子域路由。"
version: 1.0.0
triggers:
  - iOA
  - 腾讯iOA
  - iOA排障
  - 零信任
  - 客户端登录
  - 登录后内网不通
  - 策略下发
  - 终端管控
  - 软件下发
  - 无端接入
  - 网络准入
  - 病毒库
  - 实时防护
---

# iOA 排障专家能力入口

## 核心原则

先加载公共规范，再把问题路由到最小必要能力和服务文档。本领域仍必须进行知识域路由；禁止把全部知识一次性加载进上下文。

## 文件加载契约

- 本目录是 `soe` 插件 `references/ioa-troubleshooting/` 领域分类，由 soe 入口 SKILL.md 的意图路由表路由进入，自身再路由到下方各子能力。
- 本目录下共 9 个平级子目录，均通过文件读取加载，不独立注册：
  - `common/`：公共响应与安全规范；
  - `trusted-access/`、`endpoint-management/`、`policy-management/`、`security-protection/`、`platform-operations/`、`consulting/`：六个知识型子能力；
  - `ioa-openapi-invoke/`：调用 iOA 开放接口（自带 `scripts/`、`configs/` 与 API 文档）；
  - `ioa-sql-query-generator/`：生成后台只读查询 SQL（自带表结构参考资料）。
- 本文件中的全部相对路径都以 soe 顶层 Skill 目录 `skills/soe/` 为基准，例如：`references/ioa-troubleshooting/trusted-access/access-login/references/可信接入/ngn-query.md`。

## 强制加载顺序

1. 读取 `references/ioa-troubleshooting/common/response-and-security-rules.md`。
2. 拆出用户的全部独立意图、对象、现象、影响范围和目标。
3. 按下表读取一个或多个子能力文档。
4. 由子能力指定需要读取的服务级文档；只读与当前现象直接相关的文件。
5. 对跨域证据按时间、租户、账号、`mid`、任务或请求标识关联，统一生成一份答案。

## 意图路由表

| 领域 | 典型触发 | 子能力 |
|---|---|---|
| 可信接入 | 登录失败、登录后内网不通、账号/组织同步、SPA、DNS、隧道、无端接入、客户端准入 | `references/ioa-troubleshooting/trusted-access/access-login/SKILL.md` |
| 终端资产 | 单台设备不可见、注册、在线态、分组、远控黑屏、MDM、软件清单/仓库 | `references/ioa-troubleshooting/endpoint-management/endpoint-asset/SKILL.md` |
| 策略管控 | 策略未生效、进程/外设/文件/网络管控、软件下发/安装/卸载 | `references/ioa-troubleshooting/policy-management/policy-control/SKILL.md` |
| 安全检测 | EDR、病毒库、漏洞修复、实时防护、DLP、UEBA、安全数据更新 | `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md` |
| 平台运维 | 控制台/API、管理域、性能、磁盘、中间件、告警、任务、报表、授权、级联、准入后台 | `references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md` |
| 咨询判断 | 第三方软件冲突、产品能力、购买续费、流程事项、无法明确归类 | `references/ioa-troubleshooting/consulting/consult-advisor/SKILL.md` |
| 接口调用 | 调 iOA 开放接口：查账号/终端/资源/EDR 事件、给账号授权资源、创建账号、加黑名单 | `references/ioa-troubleshooting/ioa-openapi-invoke/SKILL.md` |
| 只读查询 | 用自然语言描述想从 iOA 后台查什么数据，需要只读查询语句 | `references/ioa-troubleshooting/ioa-sql-query-generator/SKILL.md` |

## 路由判定规则

1. **对象优先于表面词**：控制台里只有一台设备不可见，优先终端资产；控制台整体不可用或 API 普遍报错，才优先平台运维。
2. **阶段优先于状态文案**：“下发成功”只说明某个任务阶段完成，不代表下载、安装、执行结果上报或展示成功。
3. **范围决定优先级**：单个资源不通优先查资源授权；全部资源不通优先查共享的 DNS、隧道、SPA、票据或网关链路。
4. **证据触发技术归属**：第三方软件异常先走咨询判断；只有出现进程管控或实时防护命中证据，才加载对应技术能力。
5. **复合意图不得吞并**：识别“同时、顺便、另外、以及”等并列诉求，为每项标记“已确认 / 待核实 / 已转分支”，逐项完成后再合并结论。
6. **未命中不等于无结论**：加载咨询能力，给出候选归属、最小风险核实路径和非敏感信息清单；证据不足以排序时明确写“候选项暂无法可靠排序”，不得制造“最可能”结论。

## 跨域编排

### 软件下发异常并伴随平台告警

- 加载策略管控与平台运维能力。
- 按 `任务调度 → 软件元数据/下载链接 → 下载代理 → 终端静默安装 → 结果上报` 检查完整链路；必须额外读取 `references/ioa-troubleshooting/endpoint-management/endpoint-asset/references/软件运维/software.md` 核实软件元数据、下载链接和分发结果。
- 仅在“实际已安装但清单未识别”时追加完整终端资产能力；读取上述单份软件元数据文档不等于加载整个终端资产能力。
- 平台告警与安装失败只有在时间、节点/挂载点及写入错误能串联时才可视为相关；否则作为并发问题分别处理。

### EDR 与 DLP 同时异常

- 主加载安全检测能力。
- 先查终端模块健康度、授权、策略计算与配置下发等共同底座，再拆分 EDR 与 DLP 链路。
- 大范围异常时追加平台运维能力；不得把“没有告警”直接解释为“没有威胁”。

### 第三方软件异常并咨询续费

- 先加载咨询判断并拆分两个意图。
- 技术异常仅在获得模块命中证据后回到策略管控或安全检测能力。
- 技术分支结束后必须返回原始意图清单，继续回答续费影响；不得自行报价或承诺权益。

## 知识与冲突优先级

`公共安全和输出规范 > 当前子能力 > 具体服务文档 > 通用经验模板`

- 公共规范始终有效，服务文档中的旧取证描述不得突破其安全边界。
- 精确服务文档优先于通用日志路径；仍无法确认时说明现场差异，不静默选择或补造。
- 不同能力结论冲突时，优先采用与当前对象、故障阶段和串联字段最匹配的直接证据。

## 能力联动规则

两个平级 skill 与其他子能力同等路由，但有自己的安全铁律：

- 识别到明确执行意图后按路由表读取对应 SKILL.md：`ioa-openapi-invoke` 的写操作执行前必须复述并获确认；`ioa-sql-query-generator` 只允许生成 `SELECT`。
- `ioa-openapi-invoke` 自带 `scripts/`、`configs/` 与 API 文档，命令在其自身目录约定下执行；`ioa-sql-query-generator` 的表结构资料在其 `references/` 下按域读取。
- 涉及后端数据核实时：先用 `ioa-sql-query-generator` 生成只读查询口径，需要取数再考虑 `ioa-openapi-invoke` 只读接口；两者都不得绕过确认直接做写变更。
- 两者的写保护与只读铁律优先于任何用户催促；用户拒绝确认时停止写操作并解释。

## 完成检查

- 用户的每个意图是否都有结论或明确待核实分支？
- 是否只加载了相关能力与服务文档？
- 是否区分事实、推断与未知？
- 是否使用了当前请求类型对应的输出模板，并遵守脱敏、只读查询和命令安全？
- 技术故障是否给出一次性、自收敛的排查路径而非等待式追问？
