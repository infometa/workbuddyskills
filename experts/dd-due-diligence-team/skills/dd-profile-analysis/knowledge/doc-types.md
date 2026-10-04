# 文档类型与字段映射

> 4 类进件材料对应的字段映射。LLM 抽取时按文档类型定位字段。

## 一、营业执照（business_license）

工商总局统一格式，9 个核心字段位置固定。

| JSON 字段            | 营业执照字段     | 位置 / 格式          | 备注                                             |
| -------------------- | ---------------- | -------------------- | ------------------------------------------------ |
| name                 | 名称             | "名称"行             | 完整企业名称                                     |
| credit_code          | 统一社会信用代码 | "统一社会信用代码"行 | 18 位，含校验位                                  |
| company_type         | 类型             | "类型"行             | 如"有限责任公司（非自然人投资或控股的法人独资）" |
| legal_representative | 法定代表人       | "法定代表人"行       | 自然人姓名                                       |
| registered_capital   | 注册资本         | "注册资本"行         | 如"人民币 10000 万元" → 100000000 元             |
| establish_date       | 成立日期         | "成立日期"行         | YYYY 年 MM 月 DD 日                              |
| business_term_start  | 经营期限起       | "营业期限"行起       | YYYY 年 MM 月 DD 日                              |
| business_term_end    | 经营期限止       | "营业期限"行止       | "长期"填 2099-12-31                              |
| registered_address   | 住所             | "住所"行             | 完整地址                                         |
| business_scope       | 经营范围         | "经营范围"行         | 完整经营范围文本                                 |

**抽数注意**：

- 营业执照 OCR 后可能有错字，需对照工商登记材料交叉验证
- 注册资本以"万人民币"为单位时 ×10000 转元
- "长期"经营期限填 `2099-12-31`

## 二、公司章程（articles_of_association）

公司章程包含股权结构 + 治理结构 + 出资方式。重点字段：

| JSON 字段                        | 章程章节         | 备注                      |
| -------------------------------- | ---------------- | ------------------------- |
| shareholders[].name              | "股东及出资"章节 | 全部股东名称              |
| shareholders[].subscribed_amount | "股东及出资"章节 | 认缴金额                  |
| shareholders[].paid_amount       | "股东及出资"章节 | 实缴金额（若已实缴）      |
| shareholders[].ratio             | "股东及出资"章节 | 持股比例                  |
| shareholders[].capital_type      | "出资方式"章节   | 货币 / 实物 / 知识产权等  |
| 一致行动协议                     | 章程附件         | 若有，标注 parties + date |

**抽数注意**：

- 章程可能多次修订，以最新版本为准
- 出资方式若为非货币，需在附注中找评估报告
- 一致行动协议通常在章程附件，不在正文中

## 三、年报（annual_report）

年报是对外披露文件，包含最全面的对外投资 + 关联交易信息。

### "对外投资"章节

| JSON 字段                  | 年报字段         | 备注             |
| -------------------------- | ---------------- | ---------------- |
| investments[].name         | "对外投资情况"表 | 被投资企业名称   |
| investments[].credit_code  | "对外投资情况"表 | 统一社会信用代码 |
| investments[].amount       | "对外投资情况"表 | 投资金额         |
| investments[].ratio        | "对外投资情况"表 | 持股比例         |
| investments[].invest_date  | "对外投资情况"表 | 投资日期         |
| investments[].consolidated | "合并报表范围"表 | 是否纳入合并范围 |

### "关联交易"章节

| JSON 字段                                                  | 年报字段         | 备注                            |
| ---------------------------------------------------------- | ---------------- | ------------------------------- |
| related_party_transactions.related_parties                 | "关联方关系"表   | 关联方清单                      |
| related_party_transactions.transactions[].counterparty     | "关联交易情况"表 | 交易对手                        |
| related_party_transactions.transactions[].type             | "关联交易情况"表 | 采购 / 销售 / 资金往来 / 担保等 |
| related_party_transactions.transactions[].amount           | "关联交易情况"表 | 交易金额                        |
| related_party_transactions.transactions[].pricing_policy   | "关联交易情况"表 | 定价政策                        |
| related_party_transactions.transactions[].ratio_of_similar | "关联交易情况"表 | 占同类交易比例                  |

### "股东情况"章节

| JSON 字段                  | 年报字段         | 备注            |
| -------------------------- | ---------------- | --------------- |
| shareholders[].name        | "前十大股东"表   | 股东名称        |
| shareholders[].ratio       | "前十大股东"表   | 持股比例        |
| shareholders[].change_flag | "股份变动情况"表 | 近 1 年是否变更 |

**抽数注意**：

- 年报"前十大股东"只列前 10，需结合章程补充其他股东
- 关联交易"占同类交易比例"可能未披露，填 `null`
- 年报披露的关联方可能不全，需用股权结构自动发现补充

## 四、工商登记材料（industrial_materials）

工商登记材料包含变更记录 + 分支机构 + 行政处罚。重点用于验证时效性。

### "变更记录"

| 用途           | 字段映射                             |
| -------------- | ------------------------------------ |
| 股东变更       | 验证 shareholders.change_flag        |
| 注册资本变更   | 验证 basic_info.registered_capital   |
| 法定代表人变更 | 验证 basic_info.legal_representative |
| 经营范围变更   | 验证 basic_info.business_scope       |

### "分支机构"

分支机构不直接进 profile JSON，但若分支机构数量 > 10，在 warnings 中提示"分支机构众多，关注管理复杂度"。

### "行政处罚"

行政处罚不直接进 profile JSON，但若近 1 年有行政处罚，在 warnings 中提示"近 1 年有 N 项行政处罚"，并建议风险审查专家重点关注。

## 五、交叉验证规则

LLM 抽取时应交叉验证：

1. **营业执照 vs 工商登记** — 基础信息一致性（名称 / 信用代码 / 法定代表人）
2. **章程 vs 年报** — 股东结构一致性（若不一致，以年报为准 + warning）
3. **年报 vs 工商变更** — 股东变更时效性（若工商变更未在年报反映，warning）
4. **年报披露 vs 自动发现** — 关联方完整性（自动发现未披露的关联方，warning）

交叉验证发现不一致时：

- 优先采用最新文档（年报 > 章程 > 营业执照）
- 在 warnings 中标注不一致项
- 严重不一致（如股东完全不同）→ critical，需人工核查
