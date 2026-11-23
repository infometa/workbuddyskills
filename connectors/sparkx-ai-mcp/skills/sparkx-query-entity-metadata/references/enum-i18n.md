# Enum i18n Reference — `get_entity_metadata`

Display labels for enum values returned in the `{field}Text` companion fields. Source of truth: `EnumTranslator.java`.

## campaignState / adGroupState / targetState / portfolioState / productAdState

| API value | EN | ZH | JA |
|---|---|---|---|
| `enabled` | Enabled | 已启用 | 有効 |
| `paused` | Paused | 已暂停 | 一時停止 |
| `archived` | Archived | 已存档 | アーカイブ |

## campaignType

| API value | EN | ZH | JA |
|---|---|---|---|
| `sponsoredProducts` | Sponsored Products | 商品推广 SP | スポンサープロダクト広告 SP |
| `sponsoredBrands` | Sponsored Brands | 品牌推广 SB | ブランド広告 SB |
| `sponsoredDisplay` | Sponsored Display | 展示型推广 SD | スポンサーディスプレイ広告 SD |

## biddingStrategy

| API value | EN | ZH | JA |
|---|---|---|---|
| `legacyForSales` | SP Dynamic bids - down only | SP动态竞价-仅降低 | SP動的入札-減少のみ |
| `autoForSales` | SP Dynamic bids - up and down | SP动态竞价-提高和降低 | SP動的入札-増加と減少 |
| `manual` | SP Fixed bids | SP固定竞价 | SP固定入札 |
| `ruleBased` | Rule Based | 基于规则 | ルールベース |
| `autoForSalesSb` | SB Automated bidding | SB自动竞价 | SB自動入札 |
| `maximizeImmediateSales` | Maximize Immediate Sales | 最大化即时销售 | 即時売上最大化 |
| `maximizeNewToBrandCustomers` | Maximize New-to-Brand Customers | 最大化品牌新客 | ブランド新規顧客最大化 |

## targetingType

| API value | EN | ZH | JA |
|---|---|---|---|
| `manual` | Manual | 手动 | マニュアル |
| `auto` | Auto | 自动 | オート |
| `keyword` | Keyword | 关键词 | キーワード |
| `target` | Product Targeting | 商品投放 | 商品ターゲティング |

## costType

| API value | EN | ZH | JA |
|---|---|---|---|
| `cpc` | CPC | CPC | CPC |
| `vcpm` | VCPM | VCPM | VCPM |
| `fixedprice` | Fixed Price | 固定价格 | 固定価格 |

## isAiCreate

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | Not AI Created | 非AI创建 | AI未作成 |
| `1` | AI Created | AI创建 | AI作成 |

## sdBidOptimization

| API value | EN | ZH | JA |
|---|---|---|---|
| `conversions` | Optimize for Conversions | 转化优化 | コンバージョン最適化 |
| `clicks` | Optimize for Clicks | 点击优化 | クリック最適化 |
| `reach` | Optimize for Reach | 覆盖优化 | リーチ最適化 |

## targetMatchType

| API value | EN | ZH | JA |
|---|---|---|---|
| `broad` | Keyword-Broad | 关键词-广泛 | キーワード-広範 |
| `phrase` | Keyword-Phrase | 关键词-词组 | キーワード-フレーズ |
| `exact` | Keyword-Exact | 关键词-精准 | キーワード-完全一致 |
| `asinSameAs` | PAT-Individual Product | 商品-单个商品 | 商品-単一商品 |
| `asinExpandedFrom` | ASIN-Expanded | 商品-扩展ASIN | ASIN-拡張 |
| `asinCategorySameAs` | PAT-Category | 商品-品类 | 商品-カテゴリ |
| `asinAccessoryRelated` | Auto-Complements | 自动-关联商品 | 自動-関連商品 |
| `asinSubstituteRelated` | Auto-Substitutes | 自动-同类商品 | 自動-類似商品 |
| `queryHighRelMatches` | Auto-Close Match | 自动-紧密匹配 | 自動-密なマッチ |
| `queryBroadRelMatches` | Auto-Loose Match | 自动-宽泛匹配 | 自動-緩いマッチ |
| `similarProduct` | Similar Product | 相似商品 | 類似商品 |
| `keywordGroupSameAs` | SP-Keyword Group | SP-关键词组 | SP-キーワードグループ |

## placement

**The value set depends on `campaignType`**, and `topOfSearch` appears in both meaning
different things. Each row also carries `writeField`, the field name to use when writing.

**SP** (`sponsoredProducts`)

| API value | writeField | EN (console) | ZH (console) | JA |
|---|---|---|---|---|
| `topOfSearch` | `topAdjustment` | Top of search (first page) | 搜索结果顶部（首页） | 検索結果上部（1ページ目） |
| `productPage` | `productPageAdjustment` | Product pages | 商品页面 | 商品ページ |
| `restOfSearch` | `restOfSearchAdjustment` | Rest of search | 搜索结果的其余位置 | 検索結果ページのその他の位置 |
| `siteAmazonBusiness` | `siteAmazonBusinessAdjustment` | Amazon Business | 企业购 | Amazon Business |

**SB** (`sponsoredBrands`)

| API value | writeField | EN (console) | ZH (console) | JA |
|---|---|---|---|---|
| `topOfSearch` | (empty — the write side is `topOfSearchAdjustment`) | Top of search | 搜索结果顶部 | 検索結果上部 |
| `other` | `otherAdjustment` | Rest of search | 搜索结果的其余位置 | 検索結果ページのその他の位置 |
| `home` | `homeAdjustment` | Home | 首页 | ホーム |
| `detailPage` | `detailPageAdjustment` | Product page | 商品页面 | 商品ページ |

⚠️ **首页 means two different things.** SP's 搜索结果顶部（**首页**） is the first *page* of
search results; SB's **首页** is the Amazon *homepage* (`home`). Always pair the Chinese label
with its campaign type, and never carry a value across campaign types.

⚠️ `placementText` is only translated for the SP values — SB rows come back with the raw
`home` / `detailPage` / `other`. Use this table for SB labels.

Sponsored Display has no placement rows. The **performance** entity
(`get_ads_perf(factEntity='placement')`) uses a different value set again (`SP-`/`SB-` prefixed
display strings) — the two are not interchangeable.

## portfolioServingStatus

| API value | EN | ZH | JA |
|---|---|---|---|
| `PORTFOLIO_STATUS_ENABLED` | Delivering | 投放中 | 配信中 |
| `PORTFOLIO_OUT_OF_BUDGET` | Portfolio Out of Budget | 广告组合超预算 | ポートフォリオ予算超過 |
| `PORTFOLIO_ENDED` | Portfolio Ended | 广告组合已结束 | ポートフォリオ終了 |
| `PORTFOLIO_PENDING_START_DATE` | Portfolio Pending | 广告组合未开始 | ポートフォリオ配信待ち |
| `ADVERTISER_PAYMENT_FAILURE` | Payment Failure | 付款失败 | 支払い失敗 |
| `ADVERTISER_ARCHIVED` | Advertiser Archived | 广告主已存档 | 広告主アーカイブ |
| `ADVERTISER_EXCEED_SPENDS_LIMIT` | Advertiser Exceed Spends Limit | 广告主超支出限额 | 広告主支出限度超過 |

## portfolioBudgetType

| API value | EN | ZH | JA |
|---|---|---|---|
| `dateRange` | Date Range | 日期范围 | 日付範囲 |
| `monthlyRecurring` | Monthly Recurring | 按月 | 月次 |

## aiStatus

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | AI Never Turned On | 未开启 | AI未使用 |
| `1` | AI Currently Running | 已开启 | AI運用中 |
| `2` | AI Turned Off | 已暂停 | AI一時停止中 |

## aiTargetType (targetType)

Increase sales / 扩大销量 and Drive efficiency / 控制成本 are UI category headings, not values
of `targetType`. Use the selected option in the user's language as the primary value. Do not
replace `targetType=2` with its category or copy the English option into a Chinese answer.

| API value | EN option | ZH option | JA | UI category |
|---|---|---|---|---|
| `1` | Drive growth | 推动增长 | 成長の推進 | Increase sales / 扩大销量 |
| `2` | Optimize ROAS | 保持订单稳定 | 安定の維持 | Drive efficiency / 控制成本 |
| `3` | Promotion sales boost | 活动冲量 | キャンペーンの推進 | Increase sales / 扩大销量 |

## aiPersonality

The labels below are parsing references. In customer-facing managed-group or schedule output,
display the API value itself (`AI 人格：1` through `AI 人格：5`) and do not replace or append it
with these descriptive labels.

| API value | EN | ZH | JA |
|---|---|---|---|
| `1` | Very Conservative | 非常保守 | 非常に保守的 |
| `2` | Conservative | 保守 | 保守的 |
| `3` | Balanced | 平衡 | バランス |
| `4` | Aggressive | 激进 | 積極的 |
| `5` | Very Aggressive | 非常激进 | 非常に積極的 |

## AI Action Space feature switches (aiGroup)

These mappings support parsing. For customer-facing names and UI grouping, use
[`managed-group-display.md`](managed-group-display.md); do not expose the backend field column by
default. Brand/non-brand/competitor mode is separate from AI Action Space.

All are `0`/`1` except `targetPausedAddStatus` which is `0`/`1`/`2`.

**Common 0/1 values**: `0` = Off (关闭 / オフ), `1` = On (开启 / オン)

| Field | EN | ZH | JA |
|---|---|---|---|
| `bidAdPlaceStatus` | Placement multiplier | 广告位调价 | 掲載位置入札調整 |
| `bidDaypartStatus` | Bid dayparting | 分时调价 | 時間帯別入札調整 |
| `bidPerformanceStatus` | Adjust base bids based on performance | 按表现调价 | パフォーマンスに基づく入札調整 |
| `bidOptimizationStatus` | Bid optimization | 竞价优化 | 入札最適化 |
| `budgetDaypartStatus` | Budget dayparting | 分时预算 | 時間帯別予算 |
| `budgetDynamicStatus` | Adjust budget by performance | 按表现调预算 | パフォーマンスに基づく予算調整 |
| `budgetRedistributeStatus` | Budget reallocation | 预算重新分配 | 予算再分配 |
| `negativeTargetStatus` | Add negative targets | 添加否定定向 | 除外ターゲティング追加 |
| `structOptimizationStatus` | Structure optimization | 结构优化 | 構造最適化 |
| `structPauseProductStatus` | Pause underperforming products | 暂停表现不佳的商品 | パフォーマンス低下商品の一時停止 |
| `structPauseCampaignStatus` | Pause underperforming campaigns & ad groups | 暂停表现不佳的广告活动和广告组 | パフォーマンス低下キャンペーン＆広告グループの一時停止 |
| `competitorStatus` | Competitor keyword library | 竞品词库 | 競合キーワードライブラリ |

### targetPausedAddStatus — special 3-value field

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | Pause targets off | 定向暂停关闭 | ターゲティングの一時停止：オフ |
| `1` | Pause targets on; targeting supplementation unchecked | 定向暂停开启，不勾选定向补充 | ターゲティングの一時停止：オン、ターゲティング補充は未選択 |
| `2` | Pause targets on; targeting supplementation checked | 定向暂停开启，勾选定向补充 | ターゲティングの一時停止：オン、ターゲティング補充を選択 |

## Automation rule / Rule-based automation terms

| Code / concept | EN | ZH | Notes |
|---|---|---|---|
| `aiAutomation` | Rule-based automation settings | 自动化规则设置 | Readable on `aiGroup` / `aiGroup_schedule`; rule config is not writable through MCP. |
| `2` | Bid dayparting | 分时调价 | Automation template and action-space ruleType. |
| `3` | Budget rules (legacy/deprecated) | 预算规则（老版废弃） | Standalone legacy automation rule; keep for interpreting historical campaigns, not for new setup. |
| `4` | Target harvesting | 定向收割 | Managed-group customer label; standalone template name is Add Search Keywords / 添加搜索词. |
| `5` | Add negative targets | 添加否定定向 | Managed-group customer label; standalone template name is Add Negative Keywords / 添加否定词. |
| `13` | Budget dayparting | 分时预算 | Automation template and action-space ruleType. |
| `15` / `18` | Targeting rules | 定向规则 | Standalone automation rule types; new targeting rule is `18`. |
| `17` | Adjust budget by performance | 按表现调预算 | Managed-group customer label; the Help Center's standalone template may use Budget Rules. |
| `19` | Placement bid adjustment | 广告位调价 | Managed-group customer label; standalone template name is Placement Rules / 广告位规则. |
| `20` | Pause campaigns and ad groups | 暂停广告活动和广告组 | Managed-group customer label; standalone automation has a broader activation/pausing name. |
| `181` | Bid by performance | 按表现调价 | Managed-group action-space ruleType. |
| `182` | Pause targets | 定向暂停 | Rule mode exposes pause behavior; supplementation is AI-only. |
| Product inventory rules | Product inventory rules | 商品库存规则 | Standalone automation; not an AI Action Space switch. |
| Frequency settings / Execution frequency | Frequency settings / Execution frequency | 频率设置 / 执行频次 | Rule schedule settings. |
| Associate Campaigns | Associate Campaigns | 关联广告活动 | Campaign-template binding. |
| Applicable objects | Applicable objects | 生效对象 | Campaigns, selected ad groups, selected targets, or another rule-specific scope. For rule 4/5 use the `isSelf` table in `automation-rule-reading.md`. |
| Condition group | Condition group | 条件组 | Groups are OR; conditions inside one group are AND. Preserve the returned connectors. |
| Data period / Data cycle | Data period / Data cycle | 数据周期 | Past N store-local dates ending yesterday; today is not included. |
| Exclusion period | Exclusion period | 排除时间范围 | Most recent X dates removed from inside the N-day lookback; the range is not shifted to keep N dates. |
| Strategy based on real-time data of the current day | Strategy based on real-time data of the current day | 基于当日实时数据的策略设置 | Evaluates data from store-day 00:00 through the current execution time. |
| Strategy based on historical data | Strategy based on historical data | 基于历史数据的策略设置 | Evaluates a configured historical lookback window. |
| Timed budget changes | Timed budget changes | 定时变更预算 | Scheduled part of Budget Rules (`ruleType=17`), distinct from Budget Dayparting (`13`). |
| Budget utilization | Budget utilization | 预算利用率 | Current-day spend divided by the latest daily budget at execution time. |
| Custom budget reset | Custom budget reset | 自定义设置 / 次日回调预算 | When enabled, sets the budget to the configured value at the next store-local 00:00; residual config is inactive when its switch is off. |

## asinInventoryStatus

| API value | EN | ZH | JA |
|---|---|---|---|
| `Active` | Active | 有货 | 販売中 |
| `Inactive` | Inactive | 无货 | 販売停止 |
| `Incomplete` | Incomplete | 不完整 | 不完全 |

## asinSpEligibilityStatus / asinSbEligibilityStatus / asinSdEligibilityStatus

| API value | EN (SP example) | ZH (SP example) | JA (SP example) |
|---|---|---|---|
| `ELIGIBLE` | SP Eligible | SP 符合广告条件 | SP 広告対象 |
| `INELIGIBLE` | SP Ineligible | SP 不符合广告条件 | SP 広告対象外 |

## asinIsDelete

> ⚠️ **This tool never returns this field.** `asinIsDelete` is a **filter parameter only** on `get_entity_metadata` — it is not in the `asin` entity's output field list, and putting it in `select` is silently ignored (`meta.hint` says `Unknown select fields ignored: [asinIsDelete]` and the call still succeeds). Use it as a filter (`{"asinIsDelete": 1}` returns the deleted ones), or read the value from `get_ads_perf`'s dimension `asin.asinIsDelete_`. The labels below apply to those two uses.

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | Active | 正常 | 有効 |
| `1` | Deleted | 已删除 | 削除済み |

## profileUseBudgetCap

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | No Budget Cap | 不限预算 | 予算上限なし |
| `1` | Budget Cap Enabled | 有预算上限 | 予算上限あり |

## countryCode (profile)

| API value | EN | ZH | JA |
|---|---|---|---|
| `US` | United States | 美国 | アメリカ |
| `CA` | Canada | 加拿大 | カナダ |
| `MX` | Mexico | 墨西哥 | メキシコ |
| `JP` | Japan | 日本 | 日本 |
| `UK` | United Kingdom | 英国 | イギリス |
| `DE` | Germany | 德国 | ドイツ |
| `FR` | France | 法国 | フランス |
| `IT` | Italy | 意大利 | イタリア |
| `ES` | Spain | 西班牙 | スペイン |
| `NL` | Netherlands | 荷兰 | オランダ |
| `AU` | Australia | 澳大利亚 | オーストラリア |
| `SG` | Singapore | 新加坡 | シンガポール |
| `BR` | Brazil | 巴西 | ブラジル |
| `SE` | Sweden | 瑞典 | スウェーデン |
| `AE` | UAE | 阿联酋 | アラブ首長国連邦 |
| `PL` | Poland | 波兰 | ポーランド |
| `IN` | India | 印度 | インド |
| `TR` | Turkey | 土耳其 | トルコ |
| `SA` | Saudi Arabia | 沙特 | サウジアラビア |
| `BE` | Belgium | 比利时 | ベルギー |
| `EG` | Egypt | 埃及 | エジプト |
| `ZA` | South Africa | 南非 | 南アフリカ |
