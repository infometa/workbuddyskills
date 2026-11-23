# Enum i18n Reference — `get_ads_perf`

Display labels for enum values returned in the `{field}Text` companion fields. The `language` parameter controls which column is used (`zh`/`en`/`ja`). Source of truth: `EnumTranslator.java`.

## campaignState / adGroupState / targetState / portfolioState / productAdState

| API value | EN | ZH | JA |
|---|---|---|---|
| `enabled` | Enabled | 已启用 | 有効 |
| `paused` | Paused | 已暂停 | 一時停止 |
| `archived` | Archived | 已存档 | アーカイブ |

## campaignType (`campaign.campaignType_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `sponsoredProducts` | Sponsored Products | 商品推广 SP | スポンサープロダクト広告 SP |
| `sponsoredBrands` | Sponsored Brands | 品牌推广 SB | ブランド広告 SB |
| `sponsoredDisplay` | Sponsored Display | 展示型推广 SD | スポンサーディスプレイ広告 SD |

## campaignServingStatus (`campaign.campaignServingStatus_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `CAMPAIGN_STATUS_ENABLED` / `running` | Delivering | 投放中 | 配信中 |
| `CAMPAIGN_PAUSED` / `paused` | Paused | 已暂停 | 一時停止 |
| `CAMPAIGN_ARCHIVED` | Archived | 已存档 | アーカイブ |
| `CAMPAIGN_OUT_OF_BUDGET` | Out of Budget | 超出预算 | 予算超過 |
| `ENDED` / `ended` | Ended | 已结束 | 終了 |
| `PORTFOLIO_OUT_OF_BUDGET` | Portfolio Out of Budget | 广告组合超预算 | ポートフォリオ予算超過 |
| `PORTFOLIO_ENDED` / `portfolioEnded` | Portfolio Ended | 广告组合已结束 | ポートフォリオ終了 |
| `PORTFOLIO_PENDING_START_DATE` | Portfolio Pending | 广告组合未开始 | ポートフォリオ配信待ち |
| `CAMPAIGN_INCOMPLETE` | Campaign Incomplete | 广告活动未完成 | キャンペーン未完了 |
| `ACCOUNT_OUT_OF_BUDGET` | Account Out of Budget | 账户超预算 | アカウント予算超過 |
| `ADVERTISER_PAYMENT_FAILURE` | Payment Failure | 付款失败 | 支払い失敗 |
| `ADVERTISER_ARCHIVED` | Advertiser Archived | 广告主已存档 | 広告主アーカイブ |
| `ADVERTISER_EXCEED_SPENDS_LIMIT` | Advertiser Exceed Spends Limit | 广告主超支出限额 | 広告主支出限度超過 |
| `PENDING_START_DATE` | Scheduled | 未到开始日期 | 予約済み |
| `PENDING_REVIEW` | Pending Review | 审核中 | 審査中 |
| `INELIGIBLE` | Ineligible | 不符合广告资格 | 広告資格なし |
| `rejected` / `REJECTED` | Rejected | 未获批准 | 未承認 |
| `terminated` | Terminated | 已终止 | 終了 |
| `OTHER` / `other` | Other | 其他 | その他 |

## adGroupServingStatus (`adGroup.adGroupServingStatus_`)

Same values as campaignServingStatus above, plus:

| API value | EN | ZH | JA |
|---|---|---|---|
| `CAMPAIGN_PAUSED` | Campaign Paused | 广告活动已暂停 | キャンペーン一時停止 |
| `CAMPAIGN_ARCHIVED` | Campaign Archived | 广告活动已存档 | キャンペーンアーカイブ |

(Other values identical to campaignServingStatus table)

## targetServingStatus (`target.targetServingStatus_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `TARGETING_CLAUSE_STATUS_LIVE` | Delivering | 投放中 | 配信中 |
| `TARGETING_CLAUSE_PAUSED` | Paused | 已暂停 | 一時停止 |
| `TARGETING_CLAUSE_ARCHIVED` | Archived | 已存档 | アーカイブ |
| `CAMPAIGN_PAUSED` | Campaign Paused | 广告活动已暂停 | キャンペーン一時停止 |
| `CAMPAIGN_ARCHIVED` | Campaign Archived | 广告活动已存档 | キャンペーンアーカイブ |
| `CAMPAIGN_OUT_OF_BUDGET` | Out of Budget | 超出预算 | 予算超過 |
| `CAMPAIGN_INCOMPLETE` | Campaign Incomplete | 广告活动未完成 | キャンペーン未完了 |
| `AD_GROUP_PAUSED` | Ad Group Paused | 广告组已暂停 | 広告グループ一時停止 |
| `AD_GROUP_ARCHIVED` | Ad Group Archived | 广告组已存档 | 広告グループアーカイブ |
| `AD_GROUP_INCOMPLETE` | Ad Group Incomplete | 广告组未完成 | 広告グループ未完了 |
| `ENDED` | Ended | 已结束 | 終了 |
| `PORTFOLIO_OUT_OF_BUDGET` | Portfolio Out of Budget | 广告组合超预算 | ポートフォリオ予算超過 |
| `PORTFOLIO_ENDED` | Portfolio Ended | 广告组合已结束 | ポートフォリオ終了 |
| `PORTFOLIO_PENDING_START_DATE` | Portfolio Pending | 广告组合未开始 | ポートフォリオ配信待ち |
| `ACCOUNT_OUT_OF_BUDGET` | Account Out of Budget | 账户超预算 | アカウント予算超過 |
| `ADVERTISER_ARCHIVED` | Advertiser Archived | 广告主已存档 | 広告主アーカイブ |
| `ADVERTISER_PAYMENT_FAILURE` | Payment Failure | 付款失败 | 支払い失敗 |
| `ADVERTISER_EXCEED_SPENDS_LIMIT` | Advertiser Exceed Spends Limit | 广告主超支出限额 | 広告主支出限度超過 |
| `PENDING_START_DATE` | Scheduled | 未到开始日期 | 予約済み |

## biddingStrategy (`campaign.biddingStrategy_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `legacyForSales` | SP Dynamic bids - down only | SP动态竞价-仅降低 | SP動的入札-減少のみ |
| `autoForSales` | SP Dynamic bids - up and down | SP动态竞价-提高和降低 | SP動的入札-増加と減少 |
| `manual` | SP Fixed bids | SP固定竞价 | SP固定入札 |
| `ruleBased` | Rule Based | 基于规则 | ルールベース |
| `autoForSalesSb` | SB Automated bidding | SB自动竞价 | SB自動入札 |
| `maximizeImmediateSales` | Maximize Immediate Sales | 最大化即时销售 | 即時売上最大化 |
| `maximizeNewToBrandCustomers` | Maximize New-to-Brand Customers | 最大化品牌新客 | ブランド新規顧客最大化 |

## targetingType (`campaign.targetingType_` / `target.targetingType_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `manual` | Manual | 手动 | マニュアル |
| `auto` | Auto | 自动 | オート |
| `keyword` | Keyword | 关键词 | キーワード |
| `target` | Product Targeting | 商品投放 | 商品ターゲティング |

## costType (`campaign.costType_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `cpc` | CPC | CPC | CPC |
| `vcpm` | VCPM | VCPM | VCPM |
| `fixedprice` | Fixed Price | 固定价格 | 固定価格 |

## offAmazonBudgetControlStrategy (`campaign.offAmazonBudgetControlStrategy_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `MINIMIZE_SPEND` | Minimize Spend | 最小化站外花费 | 支出を最小化 |
| `MAXIMIZE_REACH` | Maximize Reach | 最大化站外覆盖 | リーチを最大化 |

## siteRestrictions (`campaign.siteRestrictions_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `AMAZON_BUSINESS` | Amazon Business | Amazon企业购 | Amazonビジネス |
| `AMAZON_HAUL` | Amazon Haul | Amazon Haul | Amazon Haul |

## isAiCreate (`campaign.isAiCreate_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | Not AI Created | 非AI创建 | AI未作成 |
| `1` | AI Created | AI创建 | AI作成 |

## sdBidOptimization (`adGroup.sdBidOptimization_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `conversions` | Optimize for Conversions | 转化优化 | コンバージョン最適化 |
| `clicks` | Optimize for Clicks | 点击优化 | クリック最適化 |
| `reach` | Optimize for Reach | 覆盖优化 | リーチ最適化 |

## targetMatchType (`target.targetMatchType_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `broad` | Keyword-Broad | 关键词-广泛 | キーワード-広範 |
| `phrase` | Keyword-Phrase | 关键词-词组 | キーワード-フレーズ |
| `exact` | Keyword-Exact | 关键词-精准 | キーワード-完全一致 |
| `asinSameAs` / `asin` | PAT-Individual Product | 商品-单个商品 | 商品-単一商品 |
| `asinExpandedFrom` / `asinExpanded` / `asin-expanded` | ASIN-Expanded | 商品-扩展ASIN | ASIN-拡張 |
| `asinCategorySameAs` / `category` | PAT-Category | 商品-品类 | 商品-カテゴリ |
| `asinAccessoryRelated` / `complements` | Auto-Complements | 自动-关联商品 | 自動-関連商品 |
| `asinSubstituteRelated` / `substitutes` | Auto-Substitutes | 自动-同类商品 | 自動-類似商品 |
| `queryHighRelMatches` / `close-match` / `closeMatch` | Auto-Close Match | 自动-紧密匹配 | 自動-密なマッチ |
| `queryBroadRelMatches` / `loose-match` / `looseMatch` | Auto-Loose Match | 自动-宽泛匹配 | 自動-緩いマッチ |
| `keywordGroupSameAs` / `keywordGroup` | SP-Keyword Group | SP-关键词组 | SP-キーワードグループ |
| `audience` | Audience | 受众投放 | オーディエンス |
| `views` | Views Remarketing | 浏览再营销 | 閲覧リマーケティング |
| `purchases` | Purchases Remarketing | 购买再营销 | 購入リマーケティング |

## matchType (SearchTerm `matchType_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `broad` | Keyword-Broad | 关键词-广泛 | キーワード-広範 |
| `phrase` | Keyword-Phrase | 关键词-词组 | キーワード-フレーズ |
| `exact` | Keyword-Exact | 关键词-精准 | キーワード-完全一致 |
| `targeting` | Product Targeting | 商品投放 | 商品ターゲティング |
| `SUBSTITUTES` | Auto-Substitutes | 自动-同类商品 | 自動-類似商品 |
| `COMPLEMENTS` | Auto-Complements | 自动-关联商品 | 自動-関連商品 |
| `LOOSE-MATCH` | Auto-Loose Match | 自动-宽泛匹配 | 自動-緩いマッチ |
| `CLOSE-MATCH` | Auto-Close Match | 自动-紧密匹配 | 自動-密なマッチ |

⚠️ **Casing/format verified for these four Auto values, not for the other `matchType` rows above** (`broad`/`phrase`/`exact`/`targeting`/`asin-expanded`/`asin`/`category` are unverified — don't assume they're upper-case too until confirmed). Only `LOOSE-MATCH`/`CLOSE-MATCH` are hyphenated; `SUBSTITUTES`/`COMPLEMENTS` are single words with no hyphen.
| `asin-expanded` / `asinExpanded` | ASIN-Expanded | 商品-扩展ASIN | ASIN-拡張 |
| `asin` | PAT-Individual Product | 商品-单个商品 | 商品-単一商品 |
| `category` | PAT-Category | 商品-品类 | 商品-カテゴリ |

## placement (`placement.placement_`, `factEntity: "placement"`)

| API value | EN (console) | ZH (console) | JA |
|---|---|---|---|
| `SP-Top of Search on-Amazon` | Top of search (first page) | 搜索结果顶部（首页） | 検索結果上部（1ページ目） |
| `SP-Detail Page on-Amazon` | Product pages | 商品页面 | 商品ページ |
| `SP-Other on-Amazon` | Rest of search | 搜索结果的其余位置 | 検索結果ページのその他の位置 |
| `SB-Top of Search on-Amazon` | Top of search | 搜索结果顶部 | 検索結果上部 |
| `SB-Homepage on-Amazon` | Home | 首页 | ホーム |
| `SB-Detail Page on-Amazon` | Product page | 商品页面 | 商品ページ |
| `SB-Other on-Amazon` | Rest of search | 搜索结果的其余位置 | 検索結果ページのその他の位置 |

The EN/ZH columns are what the customer sees on screen — report those, not the API values.
There is no `SD-` row: Sponsored Display is outside placement reporting. `placementText` echoes
the raw API value here, so don't rely on it for a localized label.

⚠️ **首页 means two different things.** SP's 搜索结果顶部（**首页**） is the first *page* of
search results (EN "Top of search (first page)"); SB's **首页** is the Amazon *homepage* (EN
"Home"). Always pair the Chinese label with its campaign type.

The `placement` **metadata** entity uses a completely different value set (`topOfSearch` /
`productPage` / …) — see `sparkx-query-entity-metadata`'s `enum-i18n.md`, and the value-space
table in [`field-reference.md`](field-reference.md).

## portfolioServingStatus (`portfolio.portfolioServingStatus_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `PORTFOLIO_STATUS_ENABLED` | Delivering | 投放中 | 配信中 |
| `PORTFOLIO_OUT_OF_BUDGET` | Portfolio Out of Budget | 广告组合超预算 | ポートフォリオ予算超過 |
| `PORTFOLIO_ENDED` | Portfolio Ended | 广告组合已结束 | ポートフォリオ終了 |
| `PORTFOLIO_PENDING_START_DATE` | Portfolio Pending | 广告组合未开始 | ポートフォリオ配信待ち |
| `ADVERTISER_PAYMENT_FAILURE` | Payment Failure | 付款失败 | 支払い失敗 |
| `ADVERTISER_ARCHIVED` | Advertiser Archived | 广告主已存档 | 広告主アーカイブ |
| `ADVERTISER_EXCEED_SPENDS_LIMIT` | Advertiser Exceed Spends Limit | 广告主超支出限额 | 広告主支出限度超過 |

## portfolioBudgetType (`portfolio.portfolioBudgetType_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `dateRange` | Date Range | 日期范围 | 日付範囲 |
| `monthlyRecurring` | Monthly Recurring | 按月 | 月次 |

## aiStatus (`aiGroup.aiStatus_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | AI Never Turned On | 未开启 | AI未使用 |
| `1` | AI Currently Running | 已开启 | AI運用中 |
| `2` | AI Turned Off | 已暂停 | AI一時停止中 |

## aiTargetType (`aiGroup.aiTargetType_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `1` | Drive Growth | 推动增长 | 成長の推進 |
| `2` | Maintain Stable Orders | 保持订单稳定 | 安定の維持 |
| `3` | Event Boost | 活动冲量 | キャンペーンの推進 |

## aiPersonality (`aiGroup.aiPersonality_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `1` | Very Conservative | 非常保守 | 非常に保守的 |
| `2` | Conservative | 保守 | 保守的 |
| `3` | Balanced | 平衡 | バランス |
| `4` | Aggressive | 激进 | 積極的 |
| `5` | Very Aggressive | 非常激进 | 非常に積極的 |

⚠️ **Query results and reports show the numeric level only** (e.g. **AI 人格：4**) — don't replace or supplement it with this table's text label. This mapping is for understanding a user's own wording ("偏保守", "跑激进点"), not for how you present the value back.

## AI Action Space feature switches (`aiGroup.*Status_`)

All are `0`/`1` except `targetPausedAddStatus` and `targetHarvestStatus` which are `0`/`1`/`2`.

**Common 0/1 values**: `0` = Off (关闭 / オフ), `1` = On (开启 / オン)

| Field (`aiGroup.*`) | EN | ZH | JA |
|---|---|---|---|
| `bidAdPlaceStatus_` | Placement multiplier | 广告位调价 | 掲載位置入札調整 |
| `bidDaypartStatus_` | Bid dayparting | 分时调价 | 時間帯別入札調整 |
| `bidPerformanceStatus_` | Adjust base bids based on performance | 按表现调价 | パフォーマンスに基づく入札調整 |
| `bidAmazonBusinessStatus_` | Amazon Business (B2B) bid optimization | B2B 竞价优化 | Amazon Business（B2B）入札最適化 |
| `btbRangeStatus_` | B2B bid range | B2B 竞价范围 | B2B 入札レンジ |
| `budgetDaypartStatus_` | Budget dayparting | 分时预算 | 時間帯別予算 |
| `budgetDynamicStatus_` | Budget boosting | 预算加注 | 予算ブースト |
| `budgetRedistributeStatus_` | Budget reallocation | 预算重新分配 | 予算再分配 |
| `negativeTargetStatus_` | Add negative targets | 添加否定定向 | 除外ターゲティング追加 |
| `structPauseProductStatus_` | Pause underperforming products | 暂停表现不佳的商品 | パフォーマンス低下商品の一時停止 |
| `structPauseCampaignStatus_` | Pause underperforming campaigns & ad groups | 暂停表现不佳的广告活动和广告组 | パフォーマンス低下キャンペーン＆広告グループの一時停止 |
| `competitorStatus_` | Competitor keyword library | 竞品词库 | 競合キーワードライブラリ |

### targetPausedAddStatus (`aiGroup.targetPausedAddStatus_`) — special 3-value field

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | Pause targets off | 定向暂停关闭 | ターゲティングの一時停止：オフ |
| `1` | Pause targets on; targeting supplementation unchecked | 定向暂停开启，不勾选定向补充 | ターゲティングの一時停止：オン、ターゲティング補充は未選択 |
| `2` | Pause targets on; targeting supplementation checked | 定向暂停开启，勾选定向补充（暂停定向后，立即补充相同数量的定向） | ターゲティングの一時停止：オン、ターゲティング補充を選択 |

### targetHarvestStatus (`aiGroup.targetHarvestStatus_`) — special 3-value field

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | Off | 关闭 | オフ |
| `1` | On (target harvest) | 开启定向收割 | ターゲット収集をオン |
| `2` | On, and add exact negative to source ads | 开启定向收割，且在来源广告添加精准否定 | ターゲット収集をオン、かつ元広告に完全一致の除外を追加 |

## asinInventoryStatus (`asin.asinInventoryStatus_`)

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

(Replace "SP" with "SB"/"SD" for the other two fields.)

## asinIsDelete (`asin.asinIsDelete_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | Active | 正常 | 有効 |
| `1` | Deleted | 已删除 | 削除済み |

## profileUseBudgetCap (`profile.profileUseBudgetCap_`)

| API value | EN | ZH | JA |
|---|---|---|---|
| `0` | No Budget Cap | 不限预算 | 予算上限なし |
| `1` | Budget Cap Enabled | 有预算上限 | 予算上限あり |

## countryCode (`profile.countryCode_`)

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
