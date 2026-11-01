# 主站商品详情字段

最终展示以 `get_product` / `product get --product-id <ID>` 的返回值为准。它与主站商品详情使用同一服务，返回 `{ product, latestAttempt, hookReelJobs }`。`get_product_parse_run` 的 `items[].product` 和 `list_products` 的 `items[]` 用来定位商品 ID 与状态；逐个查询详情后再输出。保持服务端的文字、顺序、数值和 URL，不用自行生成的摘要覆盖原字段。

| 主站区域   | 返回字段                                                                                                                                                                                                     | 展示规则                                                                                                                    |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| 标题       | `product.title`、`product.platformProductId`                                                                                                                                                                 | 标题为空时才用平台商品 ID。                                                                                                 |
| 顶部信息   | `product.status`、`product.region`、`product.lastParsedAt`                                                                                                                                                   | 按实际状态、地区、解析时间展示。                                                                                            |
| 原商品链接 | `latestAttempt.sourceUrl`、`product.sourceUrl`                                                                                                                                                               | 优先最近一次解析的链接。                                                                                                    |
| 商品图片   | `product.images`、`product.originalImages`                                                                                                                                                                   | 优先 `images`，为空时用 `originalImages`；数量取所选数组长度，逐张保留 URL 和顺序。                                         |
| 商品描述   | `product.aiDescription`                                                                                                                                                                                      | 完整照录原文；为空时写“暂无商品描述”。不要用 `descriptionSource` 代替正文。                                                 |
| 核心卖点   | `product.keySellingPoints`                                                                                                                                                                                   | 按原顺序逐条照录。                                                                                                          |
| 商品概览   | `product.metadata.tiktok_shop.price.current` / `.original` / `.currency` / `.discount`，`.sales.soldText` / `.combinedSalesVolume` / `.soldCount`，`.categoryName`，`.review.rating` / `.review.reviewCount` | 对应当前价、原价、折扣、销量、类目、评分 / 评价。价格带上返回的币种；销量按所列字段依次取首个有值项，不自行计算折扣或销量。 |
| 商品规格   | `product.metadata.tiktok_shop.skuSummary.skuCount` / `.salePropCount`，`product.specifications[]`                                                                                                            | 先列 SKU、规格组，再按数组原顺序列出每个名称和值。                                                                          |
| 店铺与口碑 | `product.metadata.tiktok_shop.seller.name` / `.location` / `.rating` / `.productCount` / `.salesText`                                                                                                        | 对应店铺、地区、店铺评分、商品数、店铺销量。                                                                                |
| 物流摘要   | `product.metadata.tiktok_shop.logistics.shipFrom` / `.freeShipping` / `.deliveryMinDays` / `.deliveryMaxDays` / `.shippingFeeText`                                                                           | 对应发货地、免邮、预计送达、运费；只展示有值项。                                                                            |
| 关联视频   | `hookReelJobs[]`                                                                                                                                                                                             | 有值时展示每项名称、状态和创建时间，可附上对应 ID；无值时省略该区域。                                                       |

解析失败时按 `product.errorZh` / `product.errorEn` 展示服务端错误。其他空字段与主站一样省略对应项或区域；不要把空值写成肯定陈述。展示区块顺序为：顶部信息与图片、商品描述、核心卖点、商品概览、商品规格、店铺与口碑、物流摘要、关联视频。

## 本次解析费用与结算

结算优先展示 `get_product_parse_run` / `get_product_parse_request` 返回的 `run.entitlement` 整单快照；逐链接或 Excel 原行号的费用取对应 `items[].attempt.entitlement`。商品详情中的 `product.entitlement` / `latestAttempt.entitlement` 仅解释该历史记录，不替代本次运行快照。整单汇总与行级金额不相加，免费复用按本次 `reused` 和真实结算说明，不把商品历史费用算成本次收费。

| 展示项 | 字段与规则 |
| --- | --- |
| 实际扣除 | `researchCreditsCharged` 研策专用积分、`generalCreditsCharged` 通用积分；`creditsCharged` 是合计，不能再次加到两者上，也不能当作通用积分实扣 |
| 退回或释放 | `researchCreditsRefunded`、`generalCreditsRefunded`，按真实来源分别展示；这些字段包括释放未使用预占，不能一概称为成功扣费后退款，更不能承诺跨期补发已到期专用积分 |
| 状态 | `status=reserved` 表示预占中，尚非最终实扣；`partial` / `unknown` 展示当前已确认金额与结算未决，不能声称全额扣除、免费或已全退；`released` 说明预占已释放，具体退回取实际字段 |
| 父流程内含 | `billingSource=workflow_included` 表示费用含于父工作流，不另列一次按需收费 |
| 信息缺失 | 缺少结算快照或积分拆分时标注暂未提供，不填 0，不用预估费用冒充实际扣费；仅按本次响应展示已有信息，不为补齐结算重新执行 |

任务失败不代表所有单元都免费，部分成功或未决时按本次快照解释。未知创建仍查原 `request_id`，不为取得完整结算重复提交。
