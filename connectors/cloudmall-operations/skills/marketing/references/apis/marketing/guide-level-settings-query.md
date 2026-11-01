# 营销域 — 导购等级与绑定设置查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-flow.md`
> 覆盖导购等级 CRUD、等级全局配置、导购绑定设置（分享场景/自动分配/有效期/客户墙）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide-level.list 导购等级列表（≤6 个） · guide-level.get-config 等级全局配置（功能开关/自动评估） · guide-bind-settings.get 绑定设置查询（四区域，含系统默认值）
> 写操作见 `guide-level-settings-action.md`。

---

## 等级语义

- 单租户最多 **6 个**等级；等级名称租户内唯一；等级编码系统自动生成，无需传入。
- `levelSort` 值越大等级越高；等级功能关闭（全局配置 enabled=false）时等级列表返回**空数组**（等级数据仍在，重新开启后恢复）。
- 等级删除前置：该等级下不存在**非归档**导购，否则服务端拒绝。

---

## 绑定设置四区域语义

| 区域 | 控制点 |
|------|--------|
| shareScene 分享场景 | 导购分享触发的自动绑定（共享/专属）、升级专属的触发场景、生效客户范围（不限/指定标签） |
| autoAssign 自动分配 | 客户主动访问商城时是否自动分配专属导购及策略 |
| expire 有效期 | 共享关系天数（1..30，默认 7）、专属关系永久或指定天数、触发场景自动续期 |
| customerWall 客户墙 | 是否允许客户主动换绑/主动解绑 |

---

## ⛔ 未开放端点

| 端点 | 不开放理由 |
|------|-----------|
| 无 | 本控制器（等级/绑定设置）全部端点均已开放 |

---

## ✅ 等级列表 — `ops.marketing.guide-level.list`

- **说明**：全量等级（不分页），按 levelSort 升序；等级功能关闭时返回空数组。

### 入参

无（空对象）。

### 出参（数组，原始数据）

- **路径参数来源**：`[].id`（→ 等级编辑/删除路径 ID；也作为导购编辑入参 levelId 的取值来源）
- **枚举字段**：`status`（0-禁用/1-启用）
- **格式敏感字段**：`levelSort`（整数，越大等级越高）、`guideCount`（该等级下非归档导购数——**非 0 时删除会被拒绝**）

### 调用示例

```json
{"capability":"ops.marketing.guide-level.list","input":{},"summary":"查询导购等级列表"}
```

---

## ✅ 等级全局配置查询 — `ops.marketing.guide-level.get-config`

- **说明**：等级功能开关与自动评估配置。

### 入参

无（空对象）。

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| enabled | 是否启用等级管理 |
| autoEvaluate | 是否自动评估等级 |
| evaluateConfig | 自动评估配置 JSON 字符串——⚠️ **服务端与运营端前端均不解析该字段**（纯透传存储，无固定结构定义）；唯一确定的实际用法：关闭自动评估时随 `autoEvaluate: false` 传 `null`。Agent **不得自行编造结构**；仅当用户从管理后台取得完整配置 JSON 时原样透传 |

### 调用示例

```json
{"capability":"ops.marketing.guide-level.get-config","input":{},"summary":"查询等级全局配置"}
```

---

## ✅ 绑定设置查询 — `ops.marketing.guide-bind-settings.get`

- **说明**：当前租户绑定设置；未配置过时返回系统默认值。

### 入参

无（空对象）。

### 出参（原始数据，四区域嵌套结构）

- **枚举字段**：
  - `shareScene.customerLimitType`（unlimited-不限/specified-指定客户标签）
  - `autoAssign.autoAssignMethod`（auto-自动分配/none-不分配）、`autoAssign.autoAssignStrategy`（nearest-就近/round_robin-轮流，仅 auto 时有效）
  - `expire.exclusiveExpireType`（permanent-永久/specified-指定天数）
- **格式敏感字段**：`shareScene.autoBindScenes`（升级专属触发场景数组，取值 collect_coupon-领券/collect_card-领卡/place_order-下单/wework_friend-企微加好友）、`shareScene.specifiedUserTagIds`（标签值 ID 字符串数组）与 `specifiedUserTagNames`（查询接口富化的名称，一一对应）、`autoAssign.autoAssignRadius`（就近搜索半径，公里整数）
- **系统默认值**（未配置时）：分享/专属自动绑定均关、客户范围不限、不自动分配、共享有效期 7 天、专属永久、不自动续期、客户墙换绑/解绑均关。

### 调用示例

```json
{"capability":"ops.marketing.guide-bind-settings.get","input":{},"summary":"查询导购绑定设置"}
```

---
