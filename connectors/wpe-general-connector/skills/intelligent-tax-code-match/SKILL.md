---
name: intelligent-tax-code-match
display_name: 智能税收分类编码匹配
display_name_en: Intelligent Tax Classification Code Matching
description: 根据用户输入的商品名称或开票需求描述，智能匹配合适的税收分类编码，并提供相应纳税人类型的可用税率
description_zh: 根据用户输入的商品名称或开票需求描述，智能匹配合适的税收分类编码，并提供相应纳税人类型的可用税率
description_en: Match the right tax classification code from a product name or invoicing requirement description, and list the applicable tax rates by taxpayer type.
category: data
version: 1.4.0
author: 微信支付电子发票 / 乐企开票
disable: false
agent_created: true
---

# 智能税收分类编码匹配

根据**商品名称**（「手机」「东北大米」）或**开票需求描述**（「停车场场地租赁该开什么编码」），
匹配税收分类编码，并按纳税人类型给出可用税率。

## 1. 认证与连接器定位（先做，别急着说"没有工具"）

唯一依赖连接器 **`wpe-general-connector`（中文名「腾讯数电发票」）**，通过它的 `call_internal_api` 工具调用。

| 项 | 值 |
|---|---|
| 连接器 | `wpe-general-connector`（中文名「腾讯数电发票」） |
| 税号传递 | 连接器请求头 `X-Subject-Id`（兼容 `X-Merchant-Id` / `X-Tax-No`），**不是接口参数** |
| 令牌 | `Authorization: Bearer <token>` 或 `x-mcp-token` |
| 生效方式 | 远端 HTTP MCP，授权/改连接头后生效 |

**定位与授权流程**：

1. 会话中找不到该连接器工具 → 用名称 `wpe-general-connector`（或「腾讯数电发票」）在连接器列表查找并加载 MCP。
2. 加载后**首次调用不带 token**（探活）。返回 **HTTP 401** → 未授权，**停下提示用户完成 MCP 授权**，通过后再继续。
3. 服务端是**无状态模式**，每一步请求都要带 `X-Subject-Id`，不存在「initialize 过了就放行」。

> ⚠️ **禁止**用脚本、curl 或其它连接器直连服务端点（`server.wpe.tencent.com`）——功能只能通过该连接器实现。

## 2. 工具说明

| 工具 | 用途 | 何时用 |
|---|---|---|
| `call_internal_api` | 调用内部 HTTP 接口 | 本技能唯一入口，`api="intelligent_tax_coding"` |
| `health_check` | 服务/DB 就绪检查 + 税号接入状态 | 调用失败时排查 |

### 2.1 `call_internal_api`（唯一调用方式）

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `api` | string | ✅ | 固定 `intelligent_tax_coding` |
| `params.productName` | string | ✅ | 品名，驼峰；后端 `@NotBlank`，不能纯空白 |

**调用示例**：

```json
{"api": "intelligent_tax_coding", "params": {"productName": "笔记本电脑"}}
```

**返回值信封**（腾讯云风格，**没有 `code` 字段**）：

| 字段 | 含义 |
|---|---|
| `Response.Error` | `null`=成功；非 null 为业务错误 |
| `Response.RequestId` | 链路追踪号，排障必须一并给出 |
| `Response.Data.detailList` | 结果数组，**永远恰好 1 条，从不为空** |

`detailList[]` 字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `taxClassCode` | string | 19 位税收分类编码 |
| `productName` | string | 匹配到的**标准品名**（不是传入名称） |
| `productAbbreviation` | string | 简称/大类，如「电子计算机」 |
| `taxRate` | string | 税率，**已是百分比字符串**（`"13%"`），直接展示不要换算 |
| `taxPreferentialType` | string | 税收优惠类型（`"免税、按2%简易征收"`）；空串=无优惠 |
| `matchedDegree` | string | 匹配度（`"92%"`）；**不可当置信度** |

## 3. 执行流程

### 步骤 1：提炼查询品名

- 输入是**商品名** → 直接用，可再补 1~2 个更具体说法备交叉验证。
- 输入是**需求描述** → 先提炼**货物/服务实质名称**（只写"卖的是什么"，不写场景/金额/客户名）：

  | 用户描述 | 提炼品名 |
  |---|---|
  | 给客户做设备维修 | `设备维修服务` |
  | 销售自种大米 | `大米`、`东北大米` |
  | 收一个月房租 | `房屋租赁服务` |
  | 帮客户开发系统 | `软件开发服务` |
  | 卖二手笔记本电脑 | `笔记本电脑`、`二手电脑` |

- 一次提炼 **2~3 个候选品名**逐个调用（一次一个 `productName`），命中同一编码即可交叉验证。

### 步骤 2：调用

```json
{"api": "intelligent_tax_coding", "params": {"productName": "<品名>"}}
```

### 步骤 3：判读（判定以 `productName` 为准，不看 `matchedDegree`）

| 检查项 | 动作 |
|---|---|
| `Error != null` | 报业务错误，连同 `RequestId` 给出 |
| `productName` 与用户输入**同类** | 可信，正常输出 |
| `productName` 明显不符 | 判定错配，**不采用**，换更具体说法重试 |
| `matchedDegree` < 约 60% | 换 2~4 个更具体/同义说法交叉验证（「大米」57% →「东北大米」72%） |
| `matchedDegree` 高但 `productName` 跑偏 | 仍是错配（「粳米」73% →「植物类饮片」），以 `productName` 为准 |

### 步骤 4：输出

按 `templates/report-template.md`：结果表 + **按纳税人类型可用税率表**（必出）+ 交叉验证表（若做）+ 两条风险提示 + 排障信息。

## 4. 按纳税人类型给出可用税率（必须输出）

匹配只给一个 `taxRate`（记为 R），实际能开多少取决于开票方身份。输出时按下表展开，**不得只报一个百分比**：

| 纳税人类型 | 可选用税率 | 推导规则 |
|---|---|---|
| 一般纳税人 | ①一般计税 **R**；②P 含「简易征收」时可选简易计税（P 写明具体率的用该值，如「按2%简易征收」→2%） | 以 R 为主；简易计税一经选择 36 个月不变 |
| 小规模纳税人 | 按现行**征收率**（现行 3%，阶段性优惠减按 1%，以现行政策为准）；P 含「免税」可免征 | 小规模不按 R 计税 |
| 农业生产者（销售自产） | P 含「免税」时免征 | 粮食/蔬菜/鲜活肉蛋等 |
| 销售旧货/使用过固定资产 | P 含「按2%简易征收」时按 2% | 需符合税法情形 |

组合速查：

| `taxPreferentialType` | 一般纳税人 | 小规模纳税人 |
|---|---|---|
| 空（无优惠） | R | 现行征收率 |
| 「简易征收、按2%简易征收」 | R，或 2% | 现行征收率，符合情形可 2% |
| 「免税、按2%简易征收」 | R，或免征/2% | 可免征 |
| 「免税」 | R，或免征 | 可免征 |

三条纪律：①不替用户拍板选税率；②征收率/优惠会随政策调整，具体数字注明「以现行政策为准」；
③纳税人身份未说明时两种口径都列，不要默认。

## 5. 错误场景与边界

| 场景 | 现象 | 处置 |
|---|---|---|
| 税号未接入 | `403 / JSON-RPC -32007`「当前商户接入状态为 01，请完成接入后再使用」 | 该税号 `access_status` 未置 `00`；表现是 WorkBuddy 把**整个连接器下线**（工具从列表消失，易误判成"MCP 挂了"） |
| 连接器未授权 | HTTP 401 | 提示用户完成 MCP 授权（见 §1） |
| 泛称匹配度低 | 「服务」33% 错配到「修理修配服务」 | 品名越具体越准 |
| 无意义输入也返回 | 「zzzz不存在」→「其他日用杂品」82% | 接口永不返空，**不能拿匹配度当置信度** |
| 高匹配度错类 | 「粳米」73% →「植物类饮片」 | 一律以 `productName` 判类 |

**常见品名陷阱**：简称会跨类（笔记本→纸质文具；苹果→水果），开票品名要写完整；
农业类普遍带「免税、按2%简易征收」，电子设备类普遍带「简易征收、按2%简易征收」，
是否适用取决于销售方身份与货物来源，不要替用户拍板。

## 参考

- 接口规范、响应信封、鉴权与已知不可信点：`references/api-spec.md`
- 实测样例（含反例）：`references/examples.md`
- 输出模板：`templates/report-template.md`
