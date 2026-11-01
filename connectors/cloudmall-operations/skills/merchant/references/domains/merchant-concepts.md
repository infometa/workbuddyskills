# 商户域 — 实体模型与业务规则

> 实体模型、互斥模型、规则结构语义与业务规则要点——构造入参/理解概念时读本文件。
> 状态机与枚举取值（精确拼写/大小写）见 `merchant-enums.md`；能力契约见 `references/apis/merchant/`（操作日志子域见 `references/apis/system/`），操作流程见 `references/flows/`。

商户域覆盖四大子体系：**履约骨架**（组织/门店/仓库/配送）、**供应商体系**（入驻与档案）、**内容与视觉**（装修/导航/风格/素材/搜索运营）、**配置与治理**（渠道/进店/客服/操作日志）。

---

## 一、实体模型与关系

### 1.1 履约骨架

```
组织树 (org)                门店 (store) ──┬── 门店仓绑定 (StoreWarehouse，多对多，含排序=扣减库存顺序)
  HQ（总部，唯一，不可创建）    │            └── 门店自提点绑定 (多对多)
  ├─ REGION（区域）◄─门店必须挂在 REGION 下
  └─ STORE（门店节点，建店自动生成；PICKUP 历史预留不产生）
仓库 (warehouse) ── 配送方式绑定 ── 配送区块/行政区域绑定 ── 运费模板 + 履约模板
自提点 (pickup-site) ── 多对多关联门店（storeIds）
固定区域 (fixed-area)：组织节点 → 推荐地区集合（LBS 进店规则依赖）
行政区划 (region)：树形，编码来自树查询（禁止编造）
```

- **组织节点（OrgNode）**：层级白名单 HQ→REGION→STORE（服务端校验，PICKUP 不可创建）。STORE 节点由建店联动生成。
- **门店（Store）**：type=PHYSICAL/VIRTUAL；挂 REGION 节点下（orgNodeId）；编码可自动生成、编辑不可改；**创建门店同事务自动创建** STORE 组织节点 + 默认门店仓（STORE_WAREHOUSE）+ 绑定，异步建默认自提点——**不要手工重复创建默认资源**；默认仓/默认自提点（isDefault=1）不可解绑。
- **仓库（Warehouse）**：warehouseType（STORE_WAREHOUSE 门店仓/FRONT_WAREHOUSE 前置仓/MAIN_WAREHOUSE 大仓，默认前置仓）；编码必填唯一；配置状态与启停状态**独立**（configStatus 管就绪、status 管可用）。
- **配送方式（DeliveryMethod）**：编码为小写字符串约定值（express/city_express/rider_delivery/self_service）——**交易域和商品域引用此 code**；绑定约束见 `merchant-enums.md` 仓库节。
- **运费模板（FreightTemplate）**：chargeMode 计费模式 + chargeConfig（JSON 字符串）；被区块引用时不可删。
- **履约模板（FulfillmentTemplate）**：templateType 当前固定「预约配送」；timeConfig JSON 字符串。
- **配送区块（DeliveryAreaBlock）**：blockType 1=自定义/2=系统预设；区域为地图多边形绘制产物（**无法手工构造，创建/编辑不开放**）；区域排除机制（isExclude）。
- **门店仓关联（StoreWarehouse）**：绑定记录有独立 id——**sort-warehouses 的 sortedIds 传关联记录 id（非仓库 id）**，传错静默不生效。
- **门店隔离（StoreIsolation）**：多网点模式下的数据互不可见配置；**一条记录 = 一个被隔离门店**（扁平结构）；update 用 isolated 布尔。
- **网店模式（StoreMode）**：租户级单例（single/multi），update 需乐观锁 version。

### 1.2 供应商体系

```
供应商 (Supplier) ── 三分区档案（account 账号 / enterprise 企业资质 / settlement 结算）
  ├── 整行乐观锁 version（三分区共享，任一分区保存后递增）
  ├── 草稿 (Draft)：分区暂存（不做必填校验），与正式保存互斥
  ├── 资料变更单 (ProfileReview)：供应商改 enterprise/settlement 不直接生效 → 生成待复核变更单
  │     └── 分区分槽（enterprise 与 settlement 可并行各持一张；reviewing→approved/rejected）
  ├── 营业执照 OCR：识别结果仅为编辑建议（素材库 materialId 输入）
  └── 自定义字段 (CustomField)：fieldId 定义（field-config 维护）+ 档案分区内的 fieldId→value 值
供应商字段配置 (SupplierFieldConfig)：系统字段 17 项（三分区）+ 自定义字段定义；schemaVersion 乐观锁
```

- 供应商是**平台运营视角**的入驻管理对象（区别于供应商端自己的 /supplier/profile 面）。
- 接口人手机号换绑（contactRebindStatus）：provisioning 期间**禁止编辑手机号**。
- bizSummary（商品/订单/售后数）来自跨服务 Feign，降级为 null——**null ≠ 0**。

### 1.3 内容与视觉

```
装修页面 (DecorationPage) ── 版本 (Version：发布=草稿快照；version≠publishedVersion=有未发布改动) ── 门店绑定 (Binding)
分类导航 (CategoryNav 模板) ── 前台分类树 (FrontCategory，三级，编辑即时落库) ── 分类商品关联 (CategoryProductRel，硬删除)
                                    └── 后台类目关联 (linkMode: dynamic 动态同步 / snapshot 快照导入)
风格配置 (ThemeConfig)：租户单例，草稿→发布；configJson{colors, spacingMode, spacingVars, brandLogo}
底部导航方案 (TabBarScheme)：多方案，同一租户同时仅 1 个 published + 1 个默认兜底
素材 (Material) ── 素材分组 (MaterialGroup，树形)：COS 存储，URL 预签名 60 分钟时效
搜索运营：热搜词 (HotKeyword，搜索联想词) / 暗纹词 (PlaceholderKeyword，搜索框占位提示) / NLU·Rerank 干预 (Intervention)
地图 (Map)：POI 搜索透传腾讯地图（GCJ-02 坐标）；密钥配置为租户级管理面（不开放）
```

- 装修/导航/TabBar 的「发布」语义：把当前草稿置为线上生效；分类导航与 TabBar 发布均有**替换冲突/空分类的二次确认**机制（success=false ≠ 失败，是请求确认）。
- 暗纹词按场景（PlaceholderScene）组织，与热搜词是两个概念：**占位提示 vs 联想词**。
- 前台分类为**单一数据版本**（编辑即时落库，模板未发布前 C 端不可见）——不存在草稿/发布双版本数据。

### 1.4 配置与治理

```
渠道配置 (ChannelConfig)：层级树（channelLevel/parentId 后端忽略，层级由嵌套深度决定）
渠道追踪 (ChannelTrace)：投放追踪单（pushName/channelType/五级归因）+ 自定义渠道字典 + 触达明细 (TraceDetail)
进店规则 (EntryRule)：优先级链 PARAM_STORE→MEMBER_STORE→CACHE_RECENT→LBS_RECOMMEND→DEFAULT_STORE
  └── 固定区域 (FixedArea) 为 LBS_RECOMMEND 的推荐地区来源
推荐配置 (RecommendConfig)：租户单例（推荐开关开→数据上报必开）
客服配置 (CallServiceConfig)：租户单例
店铺信息 (ShopInfo)：租户单例（upsert + 乐观锁；图片字段三态语义）
操作日志 (OperationLog)：全租户审计留痕（/admin/** 非 GET；module/action 无固定枚举，先查 filter-options）
```

## 二、通用业务规则

**门店与仓库**：
- 门店编码：创建可不传（自动生成）；传入须 1~30 位字母数字；编辑不可改。仓库编码：1~50 位字母/数字/下划线/横杠，必填唯一。
- 编辑门店带乐观锁 version；并发冲突报错（重读再提交，不盲目重试）。
- 门店删除：默认门店跳过；其余**级联删除默认仓与默认自提点**；批量删除**不限草稿态**（影响面大于门店本身，务必复述确认）。
- 绑定配送方式为**全量替换**语义（不可传空数组）；移除方式会级联删其区块绑定。
- 行政区划编码必须来自行政区划树查询，禁止编造。

**运费与模板**：
- 运费金额：元，最多 2 位小数，非负；起送金额上限 100 万。
- 模板被区块引用时不可删（服务端拒绝并回显绑定信息）。

**供应商**：
- 分区保存 content 字段名 = 详情 VO 字段去掉 `Masked` 后缀的**明文名**（用户提供明文，不回写脱敏值）。
- OCR 结果仅是编辑建议，未识别字段为 null——不得编造。
- audit 需 idempotencyKey 幂等键（确认重提复用同值）。

**内容与发布**：
- 分类导航/TabBar 发布的 `success=false` + 冲突/警告明细是**二次确认请求**，不得静默 force。
- 装修发布前置：home 类型且非默认首页须有门店绑定。
- 装修版本语义：发布=草稿快照为版本；回滚=历史版本覆写草稿（不自动发布）。
- 素材 URL 为 COS 预签名（60 分钟时效），不持久化、不当稳定链接转述。
- 推荐配置：推荐开关开→数据上报开关必须开；任一开关开需完整凭据；appsecret 留空=不修改。

**导出与导入**：
- 导出仅开放 URL 型（预签名 downloadUrl，60 分钟时效）；文件流型走管理后台。
- 导入均为每行独立事务（部分成功语义，逐项报告失败明细）；门店导入 ≤500 行且有租户级并发锁；供应商 ≤200 行。
- 门店/组织导入为同步执行，`status` 通常为 null——不要当「处理中」。
