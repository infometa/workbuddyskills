# 会员子域 — 实体模型与业务规则

> 实体模型、互斥模型、规则结构语义与业务规则要点——构造入参/理解概念时读本文件。
> 查状态含义/操作前置/枚举值见 `member-enums.md`；能力契约见 `references/apis/member/`，操作流程见 `references/flows/`。数据标签子域（标签/人群包）的领域知识见 `references/domains/data-tag.md`。
> （基于既有用户运营域文档搬移并按后端源码核验修订，2026-09-09 对齐。）

---

## 核心实体

### 会员（Member）
- 平台注册用户的核心实体，承载基础信息、等级、积分、成长值、标签等。
- 关键字段语义：
  - `id`：会员 ID（雪花 ID，Long→string）；会员详情页各子资源（标签/积分/成长值/地址/优惠券）均以此定位
  - `memberNo`：会员编号（业务编号，与 uid 是两个不同字段）
  - `uid`：外部用户标识（雪花 ID，Long→string）
  - `nickname`/`gender`(0=未知,1=男,2=女)/`birthday`(yyyy-MM-dd)
  - `level`：等级数值（实体概念；**detail 出参实际字段为 `levelId`/`levelName`**，`levelCode` 恒 null 以 search 列表为准）+ `levelName`：等级名称
  - `growthValue`：成长值（整数）；`points`：可用积分（整数，实体概念；**detail 出参实际字段为 `pointsBalance`**）；冻结积分仅资产账户内部概念，**detail 出参无冻结积分字段**
  - `status`：会员状态（见状态机）
  - `phone`：手机号（后端脱敏展示，如 138****0001，不得尝试还原）
- 会员基础信息仅支持编辑昵称/性别/生日三个字段；手机号不可编辑。

### 会员等级（MemberLevel）
- 按成长值阶梯划分的等级体系，等级数量上限 10（预置 V0~V9）。
- 关键字段：
  - `id`：等级 ID（雪花 ID，Long→string）
  - `levelCode`：等级编号，格式 `V + 1~2位数字`（V0/V1/.../V99），创建后不可改
  - `growthValue`：所需成长值（≥0 整数；不同等级不可重复，且须与编号顺序一致：V(n) 的成长值必须大于 V(m) 且小于 V(k)，其中 m<n<k）
  - `pointsMultiplierEnabled`/`pointsMultiplier`：积分倍率开关与倍数（小数）——**列表返回的派生值**（权益域 POINTS_MULTIPLIER 策略动态计算），等级创建/编辑不配置倍率；⚠️ POINTS_MULTIPLIER 已被 POINTS_BOOST（多倍积分）取代，后端标 @Deprecated、无入口无存量，该字段本租户实测恒为 false / 1，**不得据此向用户说明或承诺积分倍率**
  - `cardImage`/`bgImage`/`themeColor`：卡面图/背景图 URL（需 COS 上传，当前 Capability Catalog 未登记上传）与等级色
  - `status`：0=启用，1=停用（整数常量，非枚举类）
- 降级规则（租户级单条配置）：`strategyType` 0=不降级 / 1=按发放日过期（N 年，1~5）/ 2=按自然年到期（第 N 年 1~3、月 1~12、日 1~31）。
- 等级规则描述（`rule-description`）：富文本 HTML，upsert 单条。

### 会员权益（MemberBenefit）
- 权益分两类（v3.0.0 双轨模型）：**系统固定权益**（`GROWTH_ACCEL` 成长加速 / `UPGRADE_GIFT` 升级礼包 / `POINTS_BOOST` 多倍积分，`fixed=true`，由系统内置；`benefit.list` 会返回这三类，多倍积分暂无对应能力）与**自定义权益**（运营可增删改/排序/图标上传/按 id 启停，benefitType 默认 CUSTOM）。
- 固定权益：不可新增/删除/通用编辑（Service 层拦截）；整体启停路径为 `status/{benefitType}`（⚠️ v3.0.0 由 `{benefitType}/status` 迁移，规避与自定义权益 `{id}/status` 的模板冲突）。
- 成长加速配置独立于整体开关：按等级配置 ≤5 组「商品范围 × 门店范围 × 成长倍率(1.0~9.9)」，整体保存带 revision 乐观锁（先删后插）。
- 整体启停只切换开关、保留配置（关闭后停止命中，重新开启即恢复）。
- 自定义权益：关联等级 levelIds 整体替换语义；名称 ≤30 字、说明 ≤150 字、extraConfig JSON ≤2000 字符；排序为全量有序清单替换；图标 JPG/PNG ≤2MB。

### 成长值任务（GrowthTask）
- 会员获取成长值的任务配置，当前仅 `purchase`（购买商品）一种任务类型。
- 任务配置为多态 JSON（taskConfig）：`{taskType:"purchase", perAmt:1, growthValue:100}`；perAmt 固定为 1（分），growthValue 1~9999。
- 全量列表 + 整体保存（upsert），保存即生效。

### 积分资产与流水（Asset / PointFlow）
- 积分按资产账户模型管理（冻结/核销/转账/充值），运营端积分调整走 charge（增加）/ transfer（扣减）。
- 积分明细按时间/手机号/交易类型（tradeType：freeze/rollback/commit/direct-trans/charge…）/活动渠道（channelId）筛选；TCC 中间态（freeze/rollback）在会员维度流水中被过滤。

### 积分活动（PointsActivity）
- 消费送积分活动：`pointsPerYuan`（每消费 1 分获取 X 积分，正整数）+ 商品范围（itemConfigType：0=全部商品/1=按类目/2=按商品 SKU）。
- 进阶字段（仅编辑接口可写，创建时不写入）：limitPeriod（daily/weekly/monthly）、dailyPointsLimit、expiryMode（0=永久/1=固定日期/2=滚动过期）、ruleContent。
- 活动名称同租户唯一；创建后为停用态，需手动启用。

### 积分商城（PointsMall）
- 租户级开关（enabled 0/1）+ 首页头图（bgImageUrl）。
- **积分商品（PointsGoods）**：一个积分商品 = 主记录 + 多个 SKU 子项（items）；分「实物」（goodsType=1，关联 SPU/SKU）与「优惠券」（goodsType=2，关联券模板）两类。
  - 商品编码 `goodsCode` 由后端按 `storeId + (spuId | C+couponTemplateId)` 生成；同门店同编码不允许重复上架。
  - 兑换方式 `redeemMode`：1=纯积分 / 2=积分+现金（redeemAmount 必填）。
  - 有效期 `validType`：1=长期 / 2=时间段（validStartTime/validEndTime 必填，ISO-8601 格式）。
  - 可兑等级 `allowedLevels`：等级编码列表（V0/V1...）。
  - `isHidden` 为派生字段（关联 SPU 隐藏则积分商品视为隐藏，实时查商品中心）。
- **积分兑换订单（PointsExchangeOrder）**：会员用积分兑换商品的订单；实物订单需运营发货。

### 升级礼包（UpgradeGift）
- 按等级配置礼包（giftPoints 积分 + 最多 2 张优惠券 × quantity 1~99），整体保存（先删后插）。
- revision 字段当前为弱化乐观锁（服务端接受传值但不严格校验，已知缺口）。
- **发放门禁两级**（按实现核验）：① 全局开关 `upgrade_gift_config.enabled`（未配置默认 false=关闭；发放链路第一步检查）+ ② 各等级 `levelEnabled`；会员权益行（member_benefit UPGRADE_GIFT）的启停**不参与发放判定**（仅展示口径）。
- 发放记录：`giftType` POINT/COUPON，`issueStatus` 10=待发放/20=成功/30=失败。

### 反馈（Feedback）
- 用户提交的意见反馈：`feedbackType` 六类（PRODUCT_PERFORMANCE/FUNCTION_USAGE/UI_INTERACTION/CONTENT_RECOMMENDATION/TRANSACTION_PAYMENT/OTHER，枚举名字符串）、status 0=待处理/1=已处理（已处理为终态，不可再变更）。

### 客服配置
- 商家级微信小程序客服开关（enabled 布尔，upsert）。

### 微信分享（WxShare）
- 三件套：小程序短链（仅微信内可用）、URL Link（微信外短信/邮件/网页可打开）、太阳码（扫码直达，返回 base64 data URL；**当前未对 Agent 开放**）；依赖租户小程序配置。
- 太阳码 pageUrl 不能带参数（参数放 params，≤500 字符），宽度 280~1280px。

### 会员导入导出任务（MemberImportTask / MemberExportTask）
- **会员导入**：异步受理（HTTP 秒回 taskId，后台线程池执行）；.xlsx 模板两列（手机号* 必填、昵称选填）；上限 5 万行；**同租户同时仅一个进行中任务**；已存在手机号的行失败（已注销账号除外，允许重新导入）；成功行自动补 memberNo/uid 并初始化积分与成长值资产账户。
- **黑名单导入**：同步执行（数据量小）；模板三列（会员编号/UID/手机号，任一可定位）。
- **会员导出**：sync/async 双模式（命中 ≤5000 行同步直接回预签名 URL；>5000 异步回 taskId 轮询）；导出文件 COS 保留 **7 天**，预签名 URL **60 分钟**时效；导出含批量 PII（后端 IMPORTANT 审计留痕）。
- **任务状态两套口径（勿混）**：导入任务为**整数**（0=处理中/1=已完成/2=失败）；导出任务为**字符串**（pending/processing/completed/expired）。
- 任务归属：导入导出任务均**租户维度**（非仅创建人可见）。

---

## 业务规则

### 会员档案
- 会员列表分页（pageSize ≤100，默认 10）；手机号/会员编号/UID 精确匹配，昵称模糊。
- 新建会员仅需手机号（1[3-9] 开头 11 位）+ 可选昵称/性别/生日；手机号是唯一业务键。
- 编辑会员仅 nickname/gender/birthday 三字段可选更新。
- 积分调整：amount 1~99999 正整数；DECREASE 超过当前可用余额会被拒绝；reason ≤10 字符；操作记入会员操作日志与积分流水。
- 会员标签绑定幂等（已绑定跳过、不存在的标签静默跳过）；**⚠️ 标签体系双轨**：本域绑定接口校验会员域本地标签表，而标签管理已迁移至数据标签域（data-tag-center）——跨体系 tagId 会被静默跳过，绑定后必须回读 `ops.member.member.tags` 核验实际生效（详见 apis/member/member-action.md）。
- 会员优惠券列表经促销域券库查询，促销服务不可用时降级返回空页（空 ≠ 无券）。

### 会员等级
- 创建：等级数量上限 10；levelCode 同租户唯一（格式 V+1~2位数字）；levelName 唯一（≤10 字）；growthValue 不可与其他等级重复。
- 编辑：levelName 唯一、growthValue 不可重复且须保持与编号顺序一致；levelCode 不可改（编辑请求无该字段）。
- 等级变更影响全租户会员等级判定，属高危配置写。

### 权益与成长加速
- 成长加速保存是全量替换（先删后插）：levels 为最终全集，空 levels 会清除所有等级配置。
- revision 乐观锁：保存前 revision 必须等于 detail 下发的当前值，冲突报错需刷新重查。
- 成长加速倍率 1.0~9.9（一位小数）；单等级 ≤5 组配置。

### 积分商城
- 积分商品创建按 `storeId + (spuId|C+couponTemplateId)` 分组，每组裂变为独立积分商品——一次请求可能创建多条，返回首条 ID。
- 编辑是「同源/异源拆分」语义：与原 items 同源的（同 skuId 或同 spuId+storeId）原地更新/增删；异源 items 自动拆分创建新积分商品（响应含 spawnedIds）。末个同源 SKU 保护：不允许清空原商品全部 SKU。
- items 上限 200；redeemPoints >0 必填；redeemMode=2 时 redeemAmount 必填。
- 上架前确认库存/积分价；上下架会同步 ES 标记（异步）。
- 兑换订单发货需物流单号；发货后状态不可逆。

### 积分活动
- 活动名称同租户唯一（创建/编辑均校验）。
- 编辑为**部分更新**：未携带的数值/规则字段保留旧值（不置空）；但关联 items 先删后增，可获/不可获清单须按意图完整提交。
- 商品维度配置只存 skuId（SPU→SKU 改造后），名称由详情实时富化。
- 启用中活动不可删除。

### 积分抵扣
- 保存为 upsert；enabled=true 且 minDeductUnit 非空时校验完整规则（minDeductUnit>0、exchangeAmount>0 两位小数、productScope ∈ ALL/SPECIFIED、SPECIFIED 时商品清单必填）。
- **商品关联表每次保存先清后插（无条件）**：SPECIFIED 编辑必须回填全部既有清单；productIds 兼容字段不落库，只传它会静默清空关联。
- 关闭（enabled=false）只传开关时：主配置数值规则保留，但 SPECIFIED 商品关联仍会被清空——需保留清单必须同时回传 productScope=SPECIFIED + 完整 products。

---

## 跨域引用

- **商品域**：积分商品实物类关联商品域 SPU/SKU；isHidden/source/配送方式实时派生自关联 SPU；成长加速指定商品/品类范围取商品域标识。
- **促销域**：会员优惠券经促销域券库查询；升级礼包优惠券 couponId 来源于促销域券模板。
- **数据标签域**：标签与人群包管理已迁移 data-tag-center；本域仅保留会员维度标签绑定的读写。
- **商户域**：积分商品关联门店 storeId 来源于商户域门店。
