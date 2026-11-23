# Enum i18n Reference — `get_operation_log`

Display labels for enum values in operation log fields. Used when presenting log entries to users.

### changeBy (changedBy)

> ⚠️ **`manual` is a read-side display value, not a filter value.** It can come back in
> `changedBy`, but passing it in `changeBy.values` is **rejected** (case-insensitive, including
> `IN`, `NOT_IN` and mixed values) — see `field-reference.md` -> changeBy. Every other row in
> this table is valid on both sides.

| API value | EN | ZH | JA |
|---|---|---|---|
| `ai` | AI | AI | AI |
| `Manual` (read side only) | Manual (User) | 手动（用户） | 手動（ユーザー） |
| `automation` | Automation Rule | 自动化规则 | 自動化ルール |
| `aiCustomRule` | AI Custom Rule | AI自定义规则 | AIカスタムルール |
| `budgetManagement` | Budget Management | 预算管理 | 予算管理 |
| `lockRanking` | Lock Ranking | 锁排名 | ランキングロック |
| `amazonConsole` | Amazon Console | 亚马逊后台 | Amazon コンソール |
| `api` | API | API | API |
| `labels` | Labels | 标签 | ラベル |
| `system` | System | 系统 | システム |

### actionType

| API value | EN | ZH | JA |
|---|---|---|---|
| `Added` | Added | 新增 | 追加 |
| `Archived` | Archived | 归档 | アーカイブ |
| `Paused` | Paused | 暂停 | 一時停止 |
| `Enabled` | Enabled | 启用 | 有効化 |
| `Bid Increased` | Bid Increased | 竞价提高 | 入札引き上げ |
| `Bid Decreased` | Bid Decreased | 竞价降低 | 入札引き下げ |
| `Budget Increased` | Budget Increased | 预算提高 | 予算引き上げ |
| `Budget Decreased` | Budget Decreased | 预算降低 | 予算引き下げ |
| `Placement Increased` | Placement Increased | 广告位加价 | 掲載位置引き上げ |
| `Placement Decreased` | Placement Decreased | 广告位减价 | 掲載位置引き下げ |
| `Other Fields Changed` | Other Fields Changed | 其他字段变更 | その他のフィールド変更 |
| `Bidding Strategy Setting` | Bidding Strategy Setting | 竞价策略设置 | 入札戦略設定 |
| `Abnormal Status Changed` | Abnormal Status Changed | 异常状态变更 | 異常ステータス変更 |
| `Bid Adjustment Setting` | Bid Adjustment Setting | 竞价调整设置 | 入札調整設定 |
| `AI Group Setting changed` | AI Group Setting Changed | 托管组设置变更 | 管理グループ設定変更 |

### operationType (common examples)

| API value | EN | ZH | JA |
|---|---|---|---|
| `Campaign Added` | Campaign Added | 广告活动新增 | キャンペーン追加 |
| `Campaign Paused` | Campaign Paused | 广告活动暂停 | キャンペーン一時停止 |
| `Campaign Enabled` | Campaign Enabled | 广告活动启用 | キャンペーン有効化 |
| `Campaign Archived` | Campaign Archived | 广告活动归档 | キャンペーンアーカイブ |
| `AdGroup Bid Increased` | Ad Group Bid Increased | 广告组竞价提高 | 広告グループ入札引き上げ |
| `AdGroup Bid Decreased` | Ad Group Bid Decreased | 广告组竞价降低 | 広告グループ入札引き下げ |
| `Keyword Targeting Bid Increased` | Keyword Bid Increased | 关键词竞价提高 | キーワード入札引き上げ |
| `Keyword Targeting Bid Decreased` | Keyword Bid Decreased | 关键词竞价降低 | キーワード入札引き下げ |
| `Product Targeting Bid Increased` | Product Target Bid Increased | 商品投放竞价提高 | 商品ターゲティング入札引き上げ |
| `Product Targeting Bid Decreased` | Product Target Bid Decreased | 商品投放竞价降低 | 商品ターゲティング入札引き下げ |
| `DailyBudget Increased` | Daily Budget Increased | 日预算提高 | 日次予算引き上げ |
| `DailyBudget Decreased` | Daily Budget Decreased | 日预算降低 | 日次予算引き下げ |
| `Budget Cap Increased` | Budget Cap Increased | 预算上限提高 | 予算上限引き上げ |
| `Keyword Targeting Added` | Keyword Added | 关键词新增 | キーワード追加 |
| `Product Targeting Paused` | Product Target Paused | 商品投放暂停 | 商品ターゲティング一時停止 |
| `Automatic Targeting Enabled` | Auto Targeting Enabled | 自动投放启用 | 自動ターゲティング有効化 |
| `TopSearchAdjustment Increased` | Top of Search Adjustment Increased | 搜索顶部广告位加价 | 検索上部掲載位置引き上げ |
| `ProductPageAdjustment Decreased` | Product Page Adjustment Decreased | 商品页广告位减价 | 商品ページ掲載位置引き下げ |
| `Bidding Strategy Up And Down` | Bidding Strategy: Up and Down | 竞价策略：提高和降低 | 入札戦略：アップ＆ダウン |
| `Bidding Strategy Down Only` | Bidding Strategy: Down Only | 竞价策略：仅降低 | 入札戦略：ダウンのみ |

### entity (in response rows)

| API value | EN | ZH | JA |
|---|---|---|---|
| `campaign` | Campaign | 广告活动 | キャンペーン |
| `adGroup` | Ad Group | 广告组 | 広告グループ |
| `target` | Target | 投放/关键词 | ターゲット |
| `placement` | Placement | 广告位 | 掲載位置 |
| `portfolio` | Portfolio | 广告组合 | ポートフォリオ |
| `profile` | Profile/Store | 店铺 | ストア |
| `aiGroup` | AI Managed Group | AI托管组 | AI管理グループ |
| `productAd` | Product Ad | 推广商品 | 広告商品 |
| `audience` | Audience | 受众 | オーディエンス |
