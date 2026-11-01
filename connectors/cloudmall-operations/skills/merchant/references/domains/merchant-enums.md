# 商户域 — 状态机与枚举字典

> 查值字典：状态机迁移与前置、枚举值精确拼写（大小写与取值以本表为准）。
> 查状态含义、确认操作前置、取枚举值时读本文件；实体模型/规则结构/业务约束见 `merchant-concepts.md`。
> 能力契约见 `references/apis/merchant/`（操作日志子域见 `references/apis/system/`），操作流程见 `references/flows/`。

---

## 门店状态（status，字符串）

```
新建门店 → SUSPENDED（初始态，创建即暂停营业）
SUSPENDED ──→ ACTIVE（激活，可逆回暂停）
ACTIVE ──→ SUSPENDED / CLOSED
SUSPENDED ──→ CLOSED
CLOSED = 终态，不可恢复
```

- 新建初始为 **SUSPENDED**（不是 DRAFT；DRAFT 为预留枚举当前不出现）；流转合法性服务端校验；设默认门店要求 ACTIVE。

## 仓库配置状态（configStatus，字符串）

```
UNCONFIGURED（新建默认）──→ DRAFT（绑定任一配送方式后自动）──→ READY（完成配置全量校验后）
```

- 就绪三前置：①至少一个配送方式；②每方式至少一个区块；③每区块绑运费模板（**仅 express 豁免履约模板**）。
- 仓库启停 status（整数 0/1）独立于 configStatus。

## 供应商审核状态（auditStatus，小写字符串）

```
pending（待审核）──→ approved（已通过）
                ──→ rejected（已驳回）
```

- **单向状态机，审核后不可回退**；仅 rejected/approved 允许账户启停（status: enabled/disabled）与删除。
- 资料变更单状态：reviewing（待复核）→ approved / rejected；**驳回后 payload 原地留存**，仅 reviewing 可执行复核。

## 素材审核状态（auditStatus，小写字符串）

```
auditing（审核中）──→ approved（通过）
                 ──→ rejected（驳回）
                 ──→ manual_review（人工复审）──→ approved / rejected
```

## 装修页面 / 分类导航 / TabBar 方案状态（小写字符串，三同构）

```
draft（草稿）──→ published（已发布）──→ offline（已下线）
                        ↑                    │
                        └────────────────────┘（已下线可重新发布）
```

- 分类导航：仅 draft/offline 可删；**默认兜底模板不可下线/删除**。
- TabBar：仅 draft/offline 且**非默认兜底**可删；同一租户同时仅 1 个 published（新发布顶替）。
- 装修页面 status 为**整数** 0/1/2（与上三者字符串不同）。

## 主题配置状态（status，整数）

```
0（草稿）──→ 1（已发布）
```

## 启停类状态（整数 0/1，注意不是字符串）

仓库、自提点、配送方式、履约模板、配送区块、热搜词、NLU/Rerank 干预规则均为 **0=停用/禁用、1=启用** 的整数。运费模板（enabled）、进店规则（enabled）、推荐配置（dataReportSwitch/recommendSwitch）、客服配置（enabled）用布尔 true/false。

---

## 枚举字典（大小写敏感，严格按此取值）

### 门店

| 枚举 | 取值 | 说明 |
|------|------|------|
| 门店类型 type | `PHYSICAL` / `VIRTUAL` | 实体店 / 虚拟店；PHYSICAL 必填省市区+详细地址（服务端校验） |
| 门店状态 status | `DRAFT` / `ACTIVE` / `SUSPENDED` / `CLOSED` | 见状态机 |

### 仓库

| 枚举 | 取值 | 说明 |
|------|------|------|
| 仓库类型 warehouseType | `STORE_WAREHOUSE` / `FRONT_WAREHOUSE` / `MAIN_WAREHOUSE` | 门店仓（建店自动生成）/ 前置仓 / 主仓 |
| 配置状态 configStatus | `UNCONFIGURED` / `DRAFT` / `READY` | 见状态机 |

**配送方式与仓库类型的绑定约束**：门店仓（STORE_WAREHOUSE）可绑定骑手配送（rider_delivery）、到店自提（self_service）、快递（express）、同城快递（city_express）四种，最多 3 项，其中 `rider_delivery` 与 `self_service` 互斥二选一、可再叠加快递类；前置仓/主仓仅可绑定 `express`/`city_express`（最多 2 项）。编码为小写。

### 运费模板（chargeMode，大写）

| 取值 | 说明 |
|------|------|
| `BY_QUANTITY` | 按件计费 |
| `BY_WEIGHT` | 按重量计费 |
| `BY_VOLUME` | 按体积计费——**服务端暂未开放，创建/编辑会被拒绝** |
| `FIXED` | 固定运费 |
| `FREE` | 包邮（无需计费配置） |

### 履约模板

- 模板类型 templateType 当前取值为中文「`预约配送`」（前端固定值）。
- 时间配置 timeConfig 为 JSON 字符串，结构见 `apis/merchant/delivery-action.md`。

### 配送区块

| 枚举 | 取值 | 说明 |
|------|------|------|
| 区块类型 blockType | `1` = 自定义 / `2` = 系统预设 | 整数 |
| 区块绑定类型（仓库侧 bindType） | `2` = 全国可送 / `3` = 行政区域 | 整数 |
| 区块记录类型（配置返回 blockType） | `1`=电子围栏, `2`=全国可送, `3`=省可送, `4`=市可送, `5`=区可送 | 整数 |
| 区域排除 isExclude | `0` = 配送区域 / `1` = 排除区域 | 整数 |

### 组织节点

| 枚举 | 取值 | 说明 |
|------|------|------|
| 节点类型 type | `HQ` / `REGION` / `STORE` | 层级白名单：HQ→建 REGION、REGION→建 STORE、STORE 下不可再建（服务端校验）；HQ 不可手动创建（一级节点仅允许 HQ）；门店挂 REGION 下；**PICKUP 暂不在组织树（历史预留，创建会被拒）** |
| 节点状态 status | `ACTIVE` / `INACTIVE` | 注意与门店四态状态区分 |

### 进店规则（ruleType，大写）

| 取值 | 优先级 | 参数 |
|------|--------|------|
| `PARAM_STORE` | 1（最高） | 无参数；可禁用、可拖拽重排 |
| `MEMBER_STORE` | 2 | lockMode：`LOCKED` / `ALLOW_SWITCH`（大写） |
| `CACHE_RECENT` | 3 | cacheDays：1~90 |
| `LBS_RECOMMEND` | 4 | enableFixedAreaRecommend：布尔 |
| `AREA_RECOMMEND` | —（**当前租户种子未初始化该行，list 不返回**） | 无参数——占位实现，规则命中即跳过，无实际效果 |
| `DEFAULT_STORE` | 末位（priority=可排序数+1，当前种子为 5） | defaultStoreId + defaultStoreName；**不可禁用、不可参与排序**；修改 defaultStoreId 等效于直接切换默认门店 |

### 搜索干预（全部小写）

| 枚举 | 取值 | 说明 |
|------|------|------|
| NLU 规则类型 ruleType | `nlu_rewrite` / `nlu_synonym` / `nlu_spell` / `nlu_suffix_replace` | 改写 / 同义词 / 纠错 / 后缀替换 |
| Rerank 规则类型 ruleType | `rerank_manual` / `rerank_category_boost` / `rerank_diversity` | 人工干预 / 类目加权 / 多样性 |
| Rerank 动作类型 actionType | `pin_items` / `filter_items` / `boost_items` / `penalty_items` / `boost_factor` / `penalty_factor` | 置顶 / 过滤 / 提升 / 降权 / 加权因子 / 降权因子 |
| Rerank 匹配类型 matchType | `exact` / `contains` | 精确 / 包含 |
| 日志分类 ruleCategory | `nlu` / `rerank` | — |

### 固定区域（level，小写）

- 推荐地区层级 level：`province` / `city` / `district`（小写）。

### 热搜词角标（badgeType，整数）

- `0` = 无角标，`1` = 「新」，`2` = 「热」。

### 装修页面（status/pageType，混合）

- 页面状态 `status`（整数）：`0` 草稿 / `1` 已发布 / `2` 已下线。
- 页面类型 `pageType`（小写）：`home` 首页 / `activity` 活动页 / `custom` 自定义页 / `profile` 个人中心页。
- 版本状态（版本记录 `status`，整数）：`1` 当前线上 / `0` 历史。
- 绑定类型 `bindingType`（整数）：`1` 按小程序 / `2` 按门店。
- **注意**：页面列表的 `scheduledPublishTime`/`scheduledOfflineTime` 为**毫秒时间戳**（与商户域多数 `yyyy-MM-dd HH:mm:ss` 字段不同）。

### 素材库（fileType/auditStatus，小写）

- 素材类型 `fileType`：`image` / `video` / `audio`。
- 审核状态 `auditStatus`：`auditing` 审核中 / `approved` 已通过 / `rejected` 已驳回 / `manual_review` 人工复审。

### 供应商（auditStatus/status/contactRebindStatus，小写）

- 审核状态 `auditStatus`：`pending` 待审核 → `approved` 已通过 / `rejected` 已驳回——**单向状态机，审核后不可逆向回退**；仅 rejected/approved 状态允许账户启停与删除。
- 账户状态 `status`：`enabled` / `disabled`。
- 档案结构：三分区（`account` 账号 / `enterprise` 企业资质 / `settlement` 结算），**整行乐观锁**（version 三分区共享，任一分区保存成功后递增，其他分区本地缓存需刷新，否则误报乐观锁冲突）。
- 资料变更复核：供应商修改 enterprise/settlement 不直接生效，生成**分区分槽变更单**（enterprise 与 settlement 可并行各持一张；`status`: `reviewing` 待复核 / `rejected` 已驳回——驳回后 payload 原地留存不抹除，仅 reviewing 状态可执行复核操作）。
- 接口人手机号换绑 `contactRebindStatus`：`provisioning` 换绑同步中（**禁止再编辑手机号**）/ `completed` 完成 / `retryable_failed` 可自动重试失败 / `terminal_failed` 结构性失败需人工介入；缺省=从未换绑。
- 自定义字段类型：`text` / `number` / `date` / `file` / `select`；`hasData=true`（已有录入数据）的字段禁止变更类型或删除。
- 服务类目 `categoryIds` 指供应商服务类目（与商品类目区分）。

### 分类导航（status/layoutMode/linkMode，混合大小写）

- 模板状态 `status`（小写）：`draft` 草稿 → `published` 已发布 → `offline` 已下线；**已下线可重新发布**；另有 `disabled`。默认兜底模板全租户仅一个（未命中可见性规则的门店走默认模板）。
- 布局模式 `layoutMode`（大写）：`CLASSIC` 经典 / `THREE_LEVEL` 三级 / `BRAND` 品牌——**创建后不可更改**。
- 门店可见性 `storeScope`（大写）：`ALL` 全部 / `SPECIFIED` 指定门店（与已发布模板的门店冲突时需 forceUpdate/confirmReplace 二次确认，替换旧关联）。
- 图标形状 `iconShape`（小写）：`circle` / `square`。
- 前台分类：三级层级（level 1/2/3）；**分类编辑即时落库（单一数据版本）**——模板未发布前 C 端不可见，publish 后生效；分类删除会级联删除其商品关联。
- 商品来源 `source`（小写）：`manual` 手动添加 / `id_import` 类目关联导入；后台类目关联模式 `linkMode`（小写）：`dynamic` 动态同步（类目商品变化实时反映）/ `snapshot` 快照导入（导入当时的一次性集合）。
- 单分类商品上限由后端约束（preview 出参 `maxProductCount`）；`sortBy`/`sortDirection` 为服务端白名单校验。

### 门店隔离与网店模式

- 网店模式 `mode`（小写）：`single` 单网点 / `multi` 多网点——全租户级配置，影响 C 端门店选择与运营视图；update 需携带 `version` 乐观锁（来自 get 出参）。
- 门店隔离：多网点模式下配置门店间数据互不可见的关系；**每条隔离记录 = 一个被隔离门店**（扁平结构，含 storeId/storeName/isolated 等字段）；已隔离门店不可重复配置（先查 store-ids 全集）。

### 风格与导航（theme/tabbar，混合大小写）

- 风格配置状态 `status`（整数）：`0` 草稿 / `1` 已发布——租户级单例；detail 优先草稿态；publish 生效并清 C 端缓存；间距模式 `spacingMode`：compact/airy/premium/custom（小写）。
- TabBar 方案状态（小写）：`draft` → `published` → `offline`（已下线可重新发布）；**同一租户同时仅 1 个 published**（新发布顶替旧发布）；默认兜底仅 1 个；**仅 draft/offline 且非默认兜底可删除**；样式枚举全小写（navStyle normal/stereo、bgColorMode system/custom、cornerRadius straight/round/large-round、iconColorMode system/custom、pageType preset/custom）；**同一方案 stereo Tab 最多 1 个**。

### 暗纹词（placeholder，小写）

- 场景 `code`：`^[a-z][a-z0-9_]{1,31}$`；场景 status 整数启停；暗纹词按场景组织、`sortWeight` 排序轮换；与热搜词（hot-keyword）不同——暗纹词是搜索框**占位提示文案**，热搜词是搜索**联想词**。

### 渠道追踪（channel-trace）

- 追踪单 = 一次投放的追踪配置（pushName/channelType/五级层级归因）；渠道类型含系统内置 + 自定义渠道字典（custom-channel 维护）；useStatus 整数启停；明细数据（channel-trace-detail）按追踪单查询触达与会员行为；时间筛选为**毫秒时间戳**。

### 地图

- POI 搜索透传腾讯地图 API（坐标 GCJ-02——门店坐标系；自提点为 WGS84，混用时需换算并如实说明）；地图密钥配置（WS_KEY/WS_SK/GLJS_KEY）为租户级密钥管理面（SK 加密存储），不开放给 Agent。
