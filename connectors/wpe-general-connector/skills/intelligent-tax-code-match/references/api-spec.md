# 智能税收分类编码匹配服务规范（wpe-third-server）

## 1. 接口

| 项 | 值 |
|---|---|
| MCP 接口 key | `intelligent_tax_coding` |
| 方法 | POST |
| 路径 | `/third/shuihang/v1/intelligentCoding` |
| Consul 服务 | `wpe-third-server`（实例地址由 Consul 随机负载均衡解析） |
| 入参 | `productName`（string，必填，驼峰；后端 `@NotBlank`，不能是纯空白） |

调用方式（MCP）：

```json
{ "api": "intelligent_tax_coding", "params": { "productName": "笔记本电脑" } }
```

## 2. 响应信封

腾讯云信封结构，**没有 `code` 字段**，成功判定看 `Response.Error`：

| 字段 | 含义 |
|---|---|
| `Response.Error` | `null` = 调用成功；非 null 为业务错误 |
| `Response.RequestId` | 链路追踪号，排障时必须一并给出 |
| `Response.Data.detailList` | 结果数组，**永远恰好 1 条，从不为空** |

`detailList[]` 字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `taxClassCode` | string | 19 位税收分类编码 |
| `productName` | string | 匹配到的**标准品名**（不是你传入的名称） |
| `taxRate` | string | 税率，**已是百分比字符串**如 `"13%"`，直接展示、不要做任何换算 |
| `productAbbreviation` | string | 简称/大类，如「电子计算机」「谷物加工品」 |
| `taxPreferentialType` | string | 税收优惠类型，如「免税、按2%简易征收」；空串表示无优惠 |
| `matchedDegree` | string | 匹配度百分比字符串，如 `"92%"`；**不可当置信度** |

⚠️ 与对外微信支付接口的区别：对外接口返回 `tax_class_code_list` 且税率是万分之一整数（`1300`=13%），
本服务返回 `Response.Data.detailList` 且税率已是字符串 `"13%"`。**不要照搬对外接口的解析方式。**

`taxRate` 是**一般纳税人一般计税口径下的税率**；`taxPreferentialType` 用于推导其他纳税人类型的
可用税率（一般纳税人简易计税、小规模征收率、免税等），推导规则见 `SKILL.md`「按纳税人类型给出可用税率」。

## 3. 调用通道与鉴权

**唯一通道**：MCP 连接器 `wpe-general-connector`（腾讯数电发票），通过它的 `call_internal_api` 工具调用。
税号在连接器的连接头里，不在接口参数里：

| 项 | 值 |
|---|---|
| 连接器 | `wpe-general-connector`（中文名「腾讯数电发票」） |
| 头名 | `X-Subject-Id`（兼容别名 `X-Merchant-Id` / `X-Tax-No`） |
| 令牌头 | `Authorization: Bearer <明文令牌>` 或 `x-mcp-token` |
| 生效方式 | 远端 HTTP MCP，授权/改连接头后生效 |

> ⚠️ **禁止**用脚本（`node scripts/*.mjs`）、curl 或其它连接器直连网关 `server.wpe.tencent.com`——
> 功能只能通过 `wpe-general-connector` 连接器实现。

### 连接器定位与授权

1. 当前会话没有 `wpe-general-connector` 工具时，用连接器名称 `wpe-general-connector`（或「腾讯数电发票」）
   在连接器列表里查找并加载该 MCP。
2. 首次调用不带 token（探活）；返回 **HTTP 401** 即未授权，停下提示用户去完成 MCP 授权，
   授权通过后再继续。

接入状态门槛（服务端 `[access]` 配置）：

| 配置项 | 值 |
|---|---|
| `enabled` | `true`（发布中的环境可能为 false，判断以实际调用结果为准） |
| `ok_status` | `00` |
| 表 | `acti_enterprise_apply_info` |
| 税号列 / 状态列 | `tax_payer_no` / `access_status` |

鉴权中间件挂在**每一个 POST /mcp** 上，不存在「initialize 过了后续就放行」。
税号没有 `access_status = 00` 的记录 → **403 / JSON-RPC `-32007`**，
原文形如「当前商户接入状态为 01，请完成接入后再使用」。

### 故障排查顺序

1. `health_check` 看 `caller.subject_id` 是否为目标税号、`access.statuses` 是否为 `00`。
   - ⚠️ `access.allowed=false` 不等于"现在调不通"：滚动发布中会有过渡态，老 Pod 仍放行。
2. 连接器不可用时：按「连接器定位与授权」一节，用名称 `wpe-general-connector` 重新加载连接器；
   若仍拿不到工具，检查是否未授权（HTTP 401），提示用户完成 MCP 授权后再试。
   服务端是**无状态模式**，每一步都要带 `X-Subject-Id`。

## 4. 已知不可信点（实测）

- 传无意义字符串「zzzz不存在的商品xxx」会返回「其他日用杂品」且匹配度 82%。
- 泛称匹配度低：「服务」33%（错配到「修理修配服务」）、「大米」57%。
- 高匹配度也会错类：「粳米」73% →「植物类饮片」（中药饮片），类别完全跑偏。
