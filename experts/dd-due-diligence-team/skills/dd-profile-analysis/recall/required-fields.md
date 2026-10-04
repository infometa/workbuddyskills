# 企业画像必填字段清单

> 抽取完成后对照此清单自检。缺失必填字段会在沙箱 `/profile/validate` 报 critical error。

## 一、必填字段（缺失即 critical）

### basic_info

| 字段                 | 必填 | 缺失处理                                                                           |
| -------------------- | ---- | ---------------------------------------------------------------------------------- |
| name                 | ✓    | 营业执照 OCR 失败 → 人工补录                                                       |
| credit_code          | ✓    | 营业执照 OCR 失败 → 人工补录                                                       |
| company_type         | ✓    | 从 credit_code 第 1 位推断（1=企业）                                               |
| legal_representative | ✓    | 营业执照 OCR 失败 → 人工补录                                                       |
| registered_capital   | ✓    | 营业执照 OCR 失败 → 人工补录                                                       |
| paid_in_capital      | ✓    | 若章程未披露实缴 → 查工商登记"实收资本" → 仍无则 `null` + warning                  |
| establish_date       | ✓    | 营业执照 OCR 失败 → 从 credit_code 推断（第 5-8 位为登记机关代码，不直接推断日期） |
| business_term_start  | ✓    | 营业执照未明确 → 与 establish_date 一致                                            |
| business_term_end    | ✓    | "长期"填 `2099-12-31`                                                              |
| registered_address   | ✓    | 营业执照 OCR 失败 → 人工补录                                                       |
| business_scope       | ✓    | 营业执照 OCR 失败 → 人工补录                                                       |

### shareholders

每位股东必填：

| 字段              | 必填 | 缺失处理                                                                  |
| ----------------- | ---- | ------------------------------------------------------------------------- |
| name              | ✓    | 必须有                                                                    |
| type              | ✓    | 根据 name 推断（中文姓名 → natural_person，"公司"/"企业" → legal_person） |
| subscribed_amount | ✓    | 章程未披露 → 查年报"前十大股东" → 仍无则 `null` + critical                |
| paid_amount       | ✓    | 若章程未披露实缴 → 填 0 + warning（出资不到位）                           |
| ratio             | ✓    | 必须有，且求和 = 1.0                                                      |
| capital_type      | ✓    | 默认"货币" + warning（若文档未明确）                                      |
| source            | ✓    | 固定填来源文档                                                            |
| change_flag       | ✓    | 默认 false + warning（若无法判断）                                        |

### investments

若企业无对外投资，`investments` 为空数组 `[]`。若有投资，每项必填：

| 字段         | 必填 | 缺失处理                                          |
| ------------ | ---- | ------------------------------------------------- |
| name         | ✓    | 必须有                                            |
| credit_code  | ✓    | 年报未披露 → 查工商登记 → 仍无则 `null` + warning |
| amount       | ✓    | 必须有                                            |
| ratio        | ✓    | 必须有                                            |
| invest_date  | 可选 | 年报未披露 → `null`                               |
| consolidated | ✓    | 年报"合并范围"表判断                              |
| source       | ✓    | 固定填来源文档                                    |

### related_party_transactions

若企业无关联方 / 关联交易，`related_parties` 和 `transactions` 均为空数组。若有：

| 字段                            | 必填 | 缺失处理        |
| ------------------------------- | ---- | --------------- |
| related_parties[].name          | ✓    | 必须有          |
| related_parties[].relationship  | ✓    | 必须有          |
| related_parties[].disclosed     | ✓    | 默认 true       |
| transactions[].counterparty     | ✓    | 必须有          |
| transactions[].type             | ✓    | 必须有          |
| transactions[].amount           | ✓    | 必须有          |
| transactions[].pricing_policy   | 可选 | 未披露 → `null` |
| transactions[].ratio_of_similar | 可选 | 未披露 → `null` |
| transactions[].disclosed        | ✓    | 默认 true       |

## 二、可选字段（缺失仅 warning）

| 字段                            | 影响                           |
| ------------------------------- | ------------------------------ |
| basic_info.paid_in_capital      | 实缴 < 认缴 50% → warning      |
| investments[].invest_date       | 无法计算投资年限 → warning     |
| transactions[].pricing_policy   | 无法判断定价公允性 → warning   |
| transactions[].ratio_of_similar | 无法判断关联交易占比 → warning |

## 三、缺失处理策略

### 策略 1：OCR 失败

营业执照 OCR 识别失败 → 标注 `source: "ocr_failed"` + critical error → 人工补录

### 策略 2：文档未披露

某字段文档中未披露 → 填 `null` + warning → 在报告"关键风险提示"中列出

### 策略 3：交叉验证不一致

多份文档对同一字段披露不一致 → 优先采用最新文档 + warning → 严重不一致 → critical

### 策略 4：无法判断

某字段需推断但无法确定（如 change_flag）→ 填默认值 + warning → 在报告"关键风险提示"中说明

## 四、自检清单

LLM 抽取完成后，对照以下清单自检：

- [ ] basic_info 11 个必填字段全部非 null（除 paid_in_capital 可空）
- [ ] shareholders 数组非空，且 ratio 求和 = 1.0（容差 0.0001）
- [ ] 每位股东 8 个必填字段全部非 null
- [ ] investments 每项 7 个必填字段全部非 null（invest_date 除外）
- [ ] related_party_transactions.related_parties 与 transactions 一致（交易对手都在关联方清单中）
- [ ] 所有字段都标注了 source
- [ ] 金额单位统一为元（不是万元）
- [ ] 日期格式统一为 YYYY-MM-DD
- [ ] 比例用小数（0.35 而非 35）

自检通过后再调用沙箱 `/profile/validate`。若自检失败，先修正抽数，不要把错误数据传给沙箱。
