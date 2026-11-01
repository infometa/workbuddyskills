# 营销域 — 导购等级与绑定设置写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-flow.md`
> 覆盖导购等级 CRUD、等级全局配置、导购绑定设置（分享场景/自动分配/有效期/客户墙）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-level-settings-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide-level.create 新增导购等级 🟡 · guide-level.update 编辑导购等级 🟡 · guide-level.delete 删除导购等级 🔴 · guide-level.update-config 更新等级全局配置 🟡 · guide-bind-settings.update 更新绑定设置 🔴

---

## ✅ 新增等级 — `ops.marketing.guide-level.create`

- **风险**：🟡 可逆写
- **前置**：当前等级数 <6（超限报错）；等级名称租户内唯一（重名报错）。创建后即启用。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| levelName | String | ✅ | 等级名称，≤50 字符 |
| levelSort | Integer | ✅ | 排序序号，≥0，越大等级越高 |
| description | String | 否 | 描述，≤500 字符 |
| iconUrl | String | 否 | 图标地址，≤500 字符 |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| id | 新建等级 ID |

### 调用示例

```json
{"capability":"ops.marketing.guide-level.create","input":{"levelName":"金牌导购","levelSort":100,"description":"业绩与客户数达标的高级导购等级"},"summary":"新增金牌导购等级"}
```

---

## ✅ 编辑等级 — `ops.marketing.guide-level.update`

- **风险**：🟡 可逆写
- **前置**：等级存在；名称变更时租户内唯一（排除自身）。
- **注意**：编辑校验与创建一致——**levelName 与 levelSort 仍必填**；description/iconUrl 传 null 表示不更新。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 等级 ID（路径参数） |
| levelName | String | ✅ | 等级名称，≤50 字符 |
| levelSort | Integer | ✅ | 排序序号，≥0 |
| description | String | 否 | 描述，≤500 字符 |
| iconUrl | String | 否 | 图标地址，≤500 字符 |

### 出参（原始数据）

更新后的等级完整对象（字段同列表项）。

### 调用示例

```json
{"capability":"ops.marketing.guide-level.update","input":{"id":"5200000000000000001","levelName":"金牌导购","levelSort":100},"summary":"调整金牌导购排序"}
```

---

## ✅ 删除等级 — `ops.marketing.guide-level.delete`

- **风险**：🔴 不可逆——删除后无法恢复
- **前置**：该等级下**无关联的非归档导购**（有关联时服务端拒绝并提示）；执行前先查等级列表确认 `guideCount` 为 0。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 等级 ID（路径参数） |

### 出参（原始数据）

无（成功即空）。

### 调用示例

```json
{"capability":"ops.marketing.guide-level.delete","input":{"id":"5200000000000000001"},"summary":"删除无关联导购的等级"}
```

---

## ✅ 更新等级全局配置 — `ops.marketing.guide-level.update-config`

- **风险**：🟡 可逆写——但关闭 enabled 后等级列表立即返回空，前端等级选择将无选项
- **前置**：建议先查询现配置再全量提交（只传变更字段时其余保持原值——三个字段均为可选、非空才更新）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | Boolean | 否 | 是否启用等级管理 |
| autoEvaluate | Boolean | 否 | 是否自动评估等级 |
| evaluateConfig | String | 否 | 自动评估配置 JSON 字符串（纯透传存储，服务端不解析；关闭自动评估时传 `null`，开启时仅在用户给出完整既有配置 JSON 时原样透传——不得自行构造） |

### 出参（原始数据）

无（成功即空）。

### 调用示例

```json
{"capability":"ops.marketing.guide-level.update-config","input":{"enabled":true,"autoEvaluate":false},"summary":"启用等级管理，暂不开自动评估"}
```

---

## ✅ 更新绑定设置 — `ops.marketing.guide-bind-settings.update`

- **风险**：🔴 商业影响——改变全租户客户绑定行为（自动绑定/自动分配/有效期/客户墙），且为**全量覆盖**
- **前置**：**先查询现设置、修改后整包提交** **硬门禁：全租户/全局生效写——提交前必须发确认卡复述「现值 → 目标值」取得明确确认，指令参数齐全不豁免。**

### 入参

#### 区域一 shareScene — 导购分享给客户访问的场景

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| shareScene.shareGuideAutoBind | Boolean | 否 | 客户绑定分享导购：自动绑定开关 |
| shareScene.exclusiveAutoBind | Boolean | 否 | 客户绑定专属导购：自动绑定开关 |
| shareScene.autoBindScenes | String[] | 否 | 升级专属触发场景：collect_coupon/collect_card/place_order/wework_friend |
| shareScene.customerLimitType | String | 否 | unlimited-不限/specified-指定客户标签 |
| shareScene.specifiedUserTagIds | String[] | 否 | 标签值 ID 列表，仅 customerLimitType=specified 时有效 |

#### 区域二 autoAssign — 客户主动访问的场景

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| autoAssign.autoAssignMethod | String | 否 | auto-自动分配/none-不分配 |
| autoAssign.autoAssignStrategy | String | 否 | nearest-就近/round_robin-轮流，仅 auto 时有效 |
| autoAssign.autoAssignRadius | Integer | 否 | 就近搜索半径（公里），仅 nearest 时有效 |

#### 区域三 expire — 绑定有效期设置

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| expire.shareExpireDays | Integer | 否 | 分享导购关系有效期 1..30 天 |
| expire.exclusiveExpireType | String | 否 | permanent-永久/specified-指定天数 |
| expire.exclusiveExpireDays | Integer | 否 | 专属导购指定天数，仅 specified 时有效 |
| expire.autoRenew | Boolean | 否 | 触发绑定场景时自动续期 |

#### 区域四 customerWall — 客户墙设置

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customerWall.allowCustomerSwitch | Boolean | 否 | 允许客户主动换绑 |
| customerWall.allowCustomerUnbind | Boolean | 否 | 允许客户主动解绑 |

### 出参（原始数据）

无（成功即空）。**查询接口返回的 specifiedUserTagNames 为富化字段，提交时无需回传。**

### 调用示例

```json
{"capability":"ops.marketing.guide-bind-settings.update","input":{"shareScene":{"shareGuideAutoBind":true,"exclusiveAutoBind":true,"autoBindScenes":["collect_coupon","place_order"],"customerLimitType":"unlimited"},"autoAssign":{"autoAssignMethod":"auto","autoAssignStrategy":"nearest","autoAssignRadius":5},"expire":{"shareExpireDays":7,"exclusiveExpireType":"permanent","autoRenew":false},"customerWall":{"allowCustomerSwitch":false,"allowCustomerUnbind":false}},"summary":"开启分享自动绑定与自动分配，专属关系永久"}
```

---
