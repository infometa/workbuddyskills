# 营销域 — 弹窗/互动/协议与跨模块实体模型

> 首页弹窗、互动营销活动、奖品模板、协议的实体模型，及异步导出任务/Excel 导入等跨模块通用实体与跨域引用。
> 状态机迁移与枚举值查 `marketing-enums.md`；能力契约见 `references/apis/marketing/`，操作流程见 `references/flows/`。

---

## 核心实体
### 首页弹窗
- 带完整审核链（创建/编辑、提审、审核、投放、暂停/恢复、下线）：`templateType` 六类模板（CENTER_IMAGE/FULLSCREEN/CAROUSEL/CAROUSEL_FULLSCREEN/VIDEO/COUPON）、`templateConfig`（按类型只填对应子结构）、`ruleConfig` 投放规则四要素（audience 人群 + frequency 频次 + page 页面 + store 门店）、`priority`（1..100，越大越优先，默认 50）。
- **创建/编辑/审核是三种不同角色动作，AI 不得代替用户做审核结论**。
- 全局弹窗策略：单次访问最多弹出数/每日最多弹出数/两次弹窗最小间隔秒/同优先级排序——全租户生效。
- 统计口径：`clickRate` 等为百分数（如 12.34=12.34%），不要再乘 100。

---

### 互动营销活动
- **draft/formal 双版本模型**（核心）：同一活动 ID 恒有 draft（运营编辑）副本；发布后追加 formal（C 端运行）副本。编辑只改 draft（需再次发布才生效）；暂停/恢复/结束/库存调整作用于 formal；删除一并删两副本。
- `activityId` 为**业务 ID**（非数据库主键 id）；`activityType` 八类（sudoku-lottery 九宫格 / dzp 大转盘 / newcomer-gift 新人礼包 / open-screen-gift 开屏礼包 / daily-checkin 每日签到 / exchange-code 第三方兑换码 / share-gift 分享有礼 / yqzl 邀请助力），各有"必需玩法桶"约束（configInfo 外层 key：COMMON/PROBABILITY/SIGN/SHARE/INVITE/ASSIST）。
- `prizeInfo`：奖品池（prizeList：templateId 绑定奖品模板 / prizeName / prizeType points|coupon|physical / 多级库存限制 / alertAmount 告警阈值 / onlyOneList 互斥中奖项）。
- 关联应用场景：mini_program_page / push / banner。

---

### 奖品模板
- 互动活动奖品池的素材库（points/coupon/physical 三类）；coupon 类必须关联促销域券模板 ID（`bizTemplateId`）；被"在用"活动引用的模板不可删除。

---

### 协议
- 按类型管理（9 类：1 系统弹窗 / 2 隐私政策 / 3 用户服务协议 / 4 第三方共享个人信息清单 / 5 个人信息收集清单 / 6 未成年人信息保护规则 / 7 预售定金协议 / 8 分销协议 / 9 分销佣金规则）。
- **同类型同时只有一个"已发布"版本**：发布新协议自动结束同类型旧协议。
- 内容为富文本 HTML（≤30000 字符，服务端安全净化）；标题 ≤15 字。

---

### 异步导出任务（跨模块通用）
- 营销域全部导出能力为**异步任务模型**：`*.export` 端点只返回任务 ID（String），不直接返回文件。
- 统一轮询入口 `export-task.get`：`status` 四态（PENDING 待处理 / PROCESSING 处理中 / COMPLETED 已完成 / FAILED 失败）；`COMPLETED` 才返回 `downloadUrl`（约 30 分钟时效）。
- 覆盖：导购/分销员/话术/提成明细/素材复制记录/结算明细（活动与全局）/推广报表/商品推广/分销订单导出。

---

### Excel 导入（跨模块通用）
- 分销员/导购/话术/目标计划四类批量导入走 multipart Excel（≤10MiB），仅**文件型 capability** 可执行。
- 导入模板的列结构以运营端页面下载为准（模板文件流本身不在能力化范围）；导入结果均含成功/失败明细，失败行修正后重导。

---

## 业务规则要点

- **弹窗审核链**：创建恒为 DRAFT；提审做完整性强校验；审核结论必须来自用户明确指示，REJECT 的 reason 必填且 ≥10 字；批量下线/删除为逐条执行部分成功，执行后必须回读核验。
- **互动活动双版本纪律**：编辑只改 draft，需再次 publish 才生效；已发布活动的奖品总量只能增不能减（防超发）；库存调整同样只能调大；formal 处于 TERMINATED/EXPIRED 时不可编辑。
- **金额单位**：本域金额一律**元**（两位小数）——奖励金额、佣金/提成金额、提现金额、业绩值、销售额目标。**佣金率与分成比例为小数比例**（0.1=10%，范围 [0,1]）；**CPS 等级返佣系数为乘数**（1.0000=100% 基准，0..10.00，1 表示 1 倍而非 1%）；提成 fixed 规则的 commissionRate 为元金额；cumulative_ladder 阶梯门槛以万元数值录入（"5"=5 万元）。
- **ID 形态**：CPS 活动奖励与互动活动的 `activityId` 为**业务 ID 字符串**（CPS 为 16 位数字串，互动活动为业务 ID 非数据库主键）；其余雪花 ID（id/uid/groupId/planId/detailIds 等）一律十进制字符串；分销员/客户 `uid` 为字符串会员 ID；活动推广/商品推广/结算明细内部另有数字主键 `id`（出参已序列化为字符串）。
- **临时预签名 URL 不可持久化**：CPS 活动/活动推广图片（60 分钟）、内容素材附件（30 分钟）、奖品模板 image（约 60 分钟）、协议富文本图片 src（约 30 分钟）均为带时效的临时地址，过期需重查。
- **图片/物料地址**：需用户直接提供云MALL 可访问地址（裸地址，服务端会剥离预签名参数）；本域已登记的上传能力仅**协议插图**与**奖品图片**两项（multipart，均要求当前运行时提供文件型 capability），其余物料无上传能力。

---

## 跨域引用
- 引用：商品域（spuId/skuId 选品与佣金配置、类目编码、品牌 ID）、促销域（券模板 ID——弹窗 COUPON 模板/互动活动 coupon 奖品/奖品模板 bizTemplateId/业务素材 coupon 类型 sourceId）、会员/用户域（uid 会员 ID、人群标签值 ID、B 端员工 ID）、商户域（storeId 门店、门店分组 ID）、交易域（订单号——手动结算/提成明细/业绩明细）。
- 被引用：装修域（互动活动/活动推广挂载页面）、导购端小程序（话术/素材/任务消费方）。
- 需要跨域数据时先查对应域技能（商品/促销/用户/商户/交易），不要用营销接口猜测商品、券或会员信息。

---
