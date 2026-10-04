---
name: ioa-openapi-invoke
description: Use when the user wants to call Tencent iOA open APIs against their own iOA system, e.g. granting an account access to a resource in one sentence, or querying accounts, devices, business resources, EDR events and compliance status, or creating accounts and adding blacklists. 触发词：给账号授权资源、授权、绑定资源、调用 iOA 接口、iOA OpenAPI、查询账号/终端/设备、调用开放API、ioa api。自带 TC3-HMAC-SHA256 签名、多客户配置切换、写操作确认保护与敏感字段 RSA 加密。
---

# iOA 通用开放 API 调用

把用户「调 iOA 接口 / 查账号·终端·资源 / 授权 / 创建账号 / 加黑名单 / 查 EDR 或合规」的自然语言意图，翻译为对客户自有 iOA 后台的开放 API 调用。安装、配置与排障的完整说明见同级 `README.md`；接口示例与 body 模板见 `references/接口调用速查.md`；全量接口定义见 `references/api-docs/`。

## 适用范围与排除项

- **适用**：调任意云规范 OpenAPI 接口；一句话授权；查询账号/组织/终端/分组/软件/合规/EDR 事件/业务资源；创建账号、改密、启停账号；创建业务资源；资源授权与解绑；设备黑名单增删。
- **排除**：纯故障定位不调接口，转对应排障子能力；需要后台数据查证时先生成只读 SQL 再评估是否走 API，转 `references/ioa-troubleshooting/ioa-sql-query-generator/SKILL.md`。

## 意图分诊

| 意图 | 路径 |
|---|---|
| 「给 张三 授权 OA系统」等一句话授权 | 直接 `grant` 子命令，勿让用户拼接口 |
| 查询类（账号/终端/资源/EDR/合规） | 通用 `call`，只读 |
| 写类（创建/修改/删除/绑定/重置/加黑名单） | 通用 `call` + `--confirm-write`，执行前复述确认 |
| 含密码等敏感字段 | 追加 `--pwd-field <字段名>` 自动 RSA 加密 |

## 工作流程

### 前置：确保有可用配置

调用均需 `--config ../configs/<customer>.json`（或已设 `IOA_BASE_URL/IOA_SECRET_ID/IOA_SECRET_KEY` 环境变量）。

- 客户尚未配置：引导执行 `python ioa_cli.py init --customer <name>`（向导填 base_url + SecretId/SecretKey，私有化下 service 留空）。
- 调用前先 `python ioa_cli.py test --config ../configs/<customer>.json` 验通。

### 一句话授权

用户说「给 张三 授权 OA系统」时直接用 `grant`：

```bash
python ioa_cli.py grant --account <账号> --resource <资源名> --config ../configs/<customer>.json
```

- 多资源：重复 `--resource` 或 `--resource A,B`；同名资源消歧：`--resource-area <资源组>`；只看不下发：`--dry-run`。
- 行为：账号与资源均存在→授权成功；账号不存在→告知并停止；资源不存在→告知并列相似项；同名多项→提示加 `--resource-area`。
- 这是写操作：执行前向用户复述「将给账号 X 授权资源 Y」。

### 自然语言调用任意接口（五步）

1. **找 Action**：先查「常见意图 → Action」表；没有就到 `references/接口调用速查.md`，仍无则到 `references/api-docs/云规范接口/版本：2022-06-01/` 按目录/关键字检索对应 `.md`，读取 Action、输入参数、示例 body。
2. **构造 body**：查询类用 `Condition` 包裹分页：`{"Condition":{"PageNum":1,"PageSize":50,"FilterGroups":[{"Filters":[{"Field":"X","Operator":"eq","Values":["v"]}]}],"Sort":{"Field":"X","Order":"asc"}}}`；操作符 `eq/like/ilike/nlike/gt/egt/lt/elt/array_any`。写类按文档示例填字段。
3. **名称→ID 解析**（关键）：用户给名字、接口要 ID 时，先发一次只读 `call` 换 ID：

   | 名称 | 解析接口 | 取字段 |
   |---|---|---|
   | 账号名/UserId | `Assets/Account/DescribeLocalAccounts` | `AccountId` |
   | 账号分组名 | `Assets/DescribeAccountGroups` | `Id` |
   | 资源名 | `GatewayResource/DescribeBusinessResources`（传 `ServiceName`）| `ServiceId` |
   | 资源组名 | `GatewayResource/DescribeResourceModules` | `AreaId` |
   | 终端名/IP/登录名 | `Assets/Device/DescribeDevices`（8.0+ 默认） | `DeviceId` |
   | 终端分组名 | 枚举平台默认分组 ID（见「服务文档路由」节版本约定）；`Assets/DescribeDevicesGroups` 8.0+ 常返回空 | `GroupId` |

4. **发起调用**：
   - 只读：`python ioa_cli.py call --action <Action> --body '<json>' --config ../configs/<customer>.json`
   - 写操作（Create/Modify/Delete/Save/Add/Remove/Reset/Bind…）：加 `--confirm-write`，**执行前复述并确认**。
   - 含密码等敏感字段：加 `--pwd-field <字段名>` 自动 RSA 加密。
5. **解读响应**：成功取 `Data`；失败按打印的 `API 错误(Code): Message` 说明或调整重试。

### 常见意图 → Action

| 用户这样说 | Action | 写? |
|---|---|---|
| 查账号 / 列账号 | `Assets/Account/DescribeLocalAccounts` | 否 |
| 查组织架构 / 账号分组 | `Assets/DescribeAccountGroups` | 否 |
| 查终端 / 设备列表 | `Assets/Device/DescribeDevices`（默认 8.0+；仅 8.0 以前用 `Assets/DescribeDevices`） | 否 |
| 查终端分组 | 优先枚举平台默认分组 ID；`Assets/DescribeDevicesGroups` 8.0+ 常返回空/路由错误，勿依赖 | 否 |
| 查某终端的软件 | `Assets/DescribeDeviceSoftwares` | 否 |
| 查终端合规状态 | `EndpointControl/DescribeCompliances` | 否 |
| 查 EDR 事件 / 告警 | `EDR/ListEvents` | 否 |
| 查业务资源 | `GatewayResource/DescribeBusinessResources` | 否 |
| 查资源组 | `GatewayResource/DescribeResourceModules` | 否 |
| 查账号已授权资源 | `Assets/DescribeAccountDirectResources` | 否 |
| 创建本地账号 | `Assets/Account/CreateLocalAccount`（Password 加密）| 是 |
| 修改 / 重置 / 启停账号 | `Assets/Account/ModifyLocalAccount` / `ResetLocalAccountPassword` | 是 |
| 创建业务资源 | `GatewayResource/CreateBusinessResource` | 是 |
| 授权 / 解绑资源 | `NGN/SaveAccountResources` / `NGN/DeleteAccountResources` | 是 |
| 设备加 / 移黑名单 | `NGN/AddBlackDevices` / `NGN/RemoveBlackDevices` | 是 |

表中没有的需求，走第一步检索文档后用 `call`。可直接套用的 NL 示例与 body 模板见 `references/接口调用速查.md` 第 6/7 节。

### 命令与参数

| 子命令 | 作用 |
|---|---|
| `init` | 向导生成客户配置 |
| `test` | 连通性 + 签名测试 |
| `grant` | 一句话授权 |
| `call` | 调用任意接口 |
| `encrypt` / `pubkey` | 字段 RSA 加密 / 取公钥 |

`call` 关键参数：`--action`、`--body`/`--body-file`、`--confirm-write`、`--pwd-field`、`--version`、`--raw`、`--config`。

## 服务文档路由

路径以本 SKILL.md 同级目录为基准，按需读取：

- 安装/配置/排障：`README.md`
- 接口速查与 body 模板：`references/接口调用速查.md`
- 全量接口定义：`references/api-docs/云规范接口/版本：2022-06-01/` 与 `references/api-docs/非云规范接口/`
- 错误码：`references/api-docs/云规范接口/版本：2022-06-01/错误码.md`

### 版本约定：默认按 8.0+（无需再兼容 8.0 以前）

- **接口**：`Assets/Device/DescribeDevices`（8.0 以前旧路径 `Assets/DescribeDevices` 在 8.0+ 环境**静默返回空 `[]` 且不报错**，易误判为「环境没终端」，勿再使用）。
- **参数放请求顶层**（不能用 `Condition` 包裹，否则报 `InvalidParameter.RequestParam`）：
  `{"OsType": 0, "GroupId": 1, "PageNum": 1, "PageSize": 50}`
- **总数读取**：响应 `Data.Paging.Total`（`Items` 为明细列表）。`PageSize` 最大 5000。
- **平台默认分组 ID**（私有化固定常量，与 OsType 配对使用）：

  | 平台 | OsType | 全网终端 | 未分组终端 |
  |---|---|---|---|
  | Windows | 0 | 1 | 2 |
  | Linux | 1 | 40000101 | 40000102 |
  | macOS | 2 | 40000201 | 40000202 |
  | Android | 4 | 40000401 | 40000402 |
  | iOS | 5 | 40000501 | 40000502 |

- **统计终端总数**：遍历各平台「全网终端」分组取 `Paging.Total` 求和；「未分组终端」分组通常与全网分组不重叠，可作交叉校验。
- **账号接口无此问题**：`Assets/Account/DescribeLocalAccounts` 等账号类接口新旧版本通用（`Condition` 包裹分页）。
- 异常兜底：若 `Assets/Device/DescribeDevices` 报 `InvalidRequestRoute`（理论上仅 8.0 以前环境出现），才退回旧路径 `Assets/DescribeDevices`。

## 跨能力联动

- 用户只描述「想查什么数据」、需要后台表口径 → 转 `references/ioa-troubleshooting/ioa-sql-query-generator/SKILL.md` 生成只读 SQL。
- 接口报错但语义属排障（登录、策略、终端、平台）→ 转对应排障子能力定位，本能力只负责把调用意图转成接口。
- 共享串联字段：客户名/`--config`、账号、资源名/`ServiceId`、`DeviceId`、`mid`；跨能力操作必须核对同一客户，严禁把 A 客户操作下发到 B 客户。

## 输出验收

- 写操作执行前必须复述目标客户、对象与动作，获用户确认后才加 `--confirm-write` 执行。
- 名称→ID 解析发生在实际调用前，先只读换 ID 再执行目标操作。
- 不打印、不外泄 `secret_key`；真实配置不入库不入包。
- `base_url` 仅指向客户自有 iOA 后台，不连接其它内网地址。
- 失败响应按 `API 错误(Code): Message` 如实转述，不编造错误含义。
