# 会员域 — 会员权益写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-benefit.md`；权益现值读取（列表/成长加速详情/自定义权益详情）先读 `member-benefit-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.benefit.status 固定权益整体启停 🔴 · member.benefit.growth-accel-save 成长加速整体保存 🔴 · member.benefit.create 创建自定义权益 🔴 · member.benefit.update 编辑自定义权益 🔴 · member.benefit.delete 删除自定义权益 🔴 · member.benefit.sort 权益排序 🔴 · member.benefit.status-by-id 自定义权益启停 · member.benefit.upload-icon 权益图标上传

---

## ✅ 固定权益整体启停 — ops.member.benefit.status

- 🔴 全租户配置——只切开关、保留配置，执行前向用户确认影响。**两类权益关闭效果不同（已按实现核验）**：`GROWTH_ACCEL` 关闭→成长加速**停止计算**（加速链路实时读此开关，重新开启不追溯）；`UPGRADE_GIFT` 关闭→**仅权益行展示口径变化**，礼包实际发放由升级礼包全局开关（`upgrade-gift.config-save`）+ 各等级 levelEnabled 门禁决定，本开关不拦截发放
- **⚠️ 路径形态（v3.0.0 迁移）**：实际路径为 `PUT /admin/member-benefit/status/{benefitType}`（benefitType 在 **status 之后**）；旧文档/旧路径 `{benefitType}/status` 已被自定义权益按 id 启停端点捕获，传类型值必然报错——调用时以本契约为准

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| benefitType | String | ✅ | 路径参数：`GROWTH_ACCEL` / `UPGRADE_GIFT`（其他值报错） |
| globalEnabled | Boolean | ✅ | 目标整体开关状态（body 权威字段） |

### 出参（原始返回）

`data` 为 `null`；回读 `benefit.list` 核验 globalEnabled。

### 调用示例

```json
{"capability":"ops.member.benefit.status","input":{"benefitType":"GROWTH_ACCEL","globalEnabled":true},"summary":"开启成长加速权益"}
```

---

## ✅ 成长加速配置保存 — ops.member.benefit.growth-accel-save

- 🔴 全量替换（先删后插）+ revision 乐观锁——先读 `growth-accel-detail`，**空 levels = 清除全部等级配置；未包含在 levels 中的等级其现有配置同样会被删除**，必须以 detail 回读值回填所有需保留的等级

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| globalEnabled | Boolean | ✅ | **必填但仅作审计快照，不改变整体开关**（开关切换须走 `benefit.status`）；传 false 期望关闭加速不会生效 |
| revision | String | ✅ | 乐观锁版本号（来自最近一次 detail 下发值，十进制字符串） |
| levels | Array | — | 各等级配置**最终全集**；空=清空 |
| levels[].levelId | String | ✅ | 等级 ID（来自 `level.list`） |
| levels[].levelEnabled | Boolean | ✅ | 该等级开关 |
| levels[].configs | Array | — | ≤5 组配置 |
| configs[].productScopeType | String | ✅ | `ALL_PRODUCT` / `SPECIFIED` |
| configs[].spuIds / skuIds / categoryIds | String[] | 条件 | SPECIFIED 时至少一项（与商品域标识对应） |
| configs[].storeScopeType | String | ✅ | `ALL_STORE` / `SPECIFIED` |
| configs[].storeIds | String[] | 条件 | storeScopeType=SPECIFIED 时必填 |
| configs[].multiplier | Number | ✅ | 成长倍率 1.0~9.9（一位小数） |

### 出参（原始返回）

保存结果对象（含新 revision）；revision 冲突时返回业务错误（配置已被他人更新），需重新 detail 后与用户确认再提交。回读 `growth-accel-detail` 核验。

### 调用示例

```json
{"capability":"ops.member.benefit.growth-accel-save","input":{"globalEnabled":true,"revision":"3","levels":[{"levelId":"1000012345678901234","levelEnabled":true,"configs":[{"productScopeType":"ALL_PRODUCT","storeScopeType":"ALL_STORE","multiplier":1.5}]}]},"summary":"为黄金会员配置全商品1.5倍成长加速"}
```

---

## ✅ 创建自定义权益 — ops.member.benefit.create

- 🔴 影响权益展示——固定权益类型（GROWTH_ACCEL/UPGRADE_GIFT）由系统内置，**服务端禁止手动新增**（报错）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| benefitName | String | ✅ | 权益名称（≤30 字符，**同租户唯一**——重名返回业务错误） |
| iconUrl | String | ✅ | 图标 URL（≤2000 字符；来自 `upload-icon` 上传或用户提供；入库前自动清洗 COS 预签名参数只存裸 URL） |
| description | String | — | 权益说明（≤150 字符） |
| benefitType | String | — | 权益类型：不传默认 `CUSTOM`；**固定类型 `GROWTH_ACCEL`/`UPGRADE_GIFT` 被服务端拒绝**；可传自定义类型 `POINTS_MULTIPLIER`（积分加速）/ `MEMBER_DISCOUNT`（会员折扣）/ `FREE_SHIPPING`（免费包邮）——仅 `POINTS_MULTIPLIER` 有配置校验，其余类型 `extraConfig` 不做结构校验 |
| extraConfig | String | 条件 | 扩展配置 **JSON 字符串**（≤2000 字符）；结构按 benefitType 策略化（见下表） |
| enabled | Boolean | — | 是否启用，不传默认启用 |
| levelIds | String[] | ✅ | 关联等级 ID 列表（至少一个；来自 `level.list`） |

**`extraConfig` 按 benefitType 的结构（策略校验，源码核验）**：

| benefitType | extraConfig 要求 | 内部结构 |
|------|------|------|
| `POINTS_MULTIPLIER` | ✅ **必填**（缺失报「必须配置倍率」） | `{"multiplier": <Number>}`——积分倍率 **1.1~10.0**（越界/缺 multiplier 字段/JSON 解析失败均报错）；该值驱动等级列表返回的 `pointsMultiplier` |
| `CUSTOM` / `MEMBER_DISCOUNT` / `FREE_SHIPPING` | — | 不做结构校验（自由 JSON 或不传） |

### 出参（原始返回）

创建结果对象（含新权益 `id`，Long→string）。

### 调用示例

```json
{"capability":"ops.member.benefit.create","input":{"benefitName":"生日专属礼","iconUrl":"https://cos.example.com/benefit/birthday.png","description":"会员生日专属礼遇","levelIds":["1000012345678901234"]},"summary":"创建生日专属礼权益"}
```

---

## ✅ 编辑自定义权益 — ops.member.benefit.update

- 🔴 固定权益**服务端禁止通用编辑**（报错）；禁止把自定义权益改成固定权益类型；编辑时先读 `benefit.detail` 回填

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 路径参数：权益 ID |
| benefitName | String | ✅ | 权益名称（≤30 字符） |
| iconUrl | String | ✅ | 图标 URL（≤2000 字符） |
| description | String | — | 权益说明（≤150 字符） |
| benefitType | String | — | 不传不修改；传固定类型值被拒绝；改为 `POINTS_MULTIPLIER` 后 `extraConfig` 必须为合法 `{"multiplier": 1.1~10.0}`（更新路径同样走策略校验） |
| extraConfig | String | — | 扩展配置 JSON 字符串（≤2000 字符），结构同 create 的策略表 |
| enabled | Boolean | — | 不传不修改 |
| levelIds | String[] | ✅ | 关联等级**全集**（整体替换语义，至少一个） |

### 出参（原始返回）

`data` 为 `null`；回读 `benefit.list` / `benefit.detail` 核验。

### 调用示例

```json
{"capability":"ops.member.benefit.update","input":{"id":"7300000000000000001","benefitName":"生日专属礼","iconUrl":"https://cos.example.com/benefit/birthday.png","levelIds":["1000012345678901234","1000012345678901235"]},"summary":"编辑权益并扩展适用等级"}
```

---

## ✅ 删除自定义权益 — ops.member.benefit.delete

- 🔴 不可逆——固定权益**服务端禁止删除**（报错）；删除前向用户复述权益名称

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 路径参数：权益 ID |

### 出参（原始返回）

`data` 为 `null`；回读 `benefit.list` 核验消失。

### 调用示例

```json
{"capability":"ops.member.benefit.delete","input":{"id":"7300000000000000001"},"summary":"删除生日专属礼权益"}
```

---

## ✅ 权益排序 — ops.member.benefit.sort

- 应提交**全部自定义权益 ID 的有序清单**——不存在/重复的 ID 会报错；**漏传的权益不报错但其排序值保持旧值不更新**，因此仍须提交全集

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sortedIds | String[] | ✅ | 排序后的权益 ID 列表（≥1 个；ID 必须全部存在且互不重复，否则报错；漏传项排序值不更新） |

### 出参（原始返回）

`data` 为 `null`；回读 `benefit.list` 核验顺序。

### 调用示例

```json
{"capability":"ops.member.benefit.sort","input":{"sortedIds":["7300000000000000002","7300000000000000001"]},"summary":"调整权益展示顺序"}
```

---

## ✅ 自定义权益启停 — ops.member.benefit.status-by-id

- 语义为**自定义权益按 id 启停**（与固定权益整体启停 `benefit.status` 是两个不同端点）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 路径参数：权益 ID |
| enabled | Integer | ✅ | 0=停用 / 1=启用（body 权威字段，Integer）。⚠️ DTO 无 @NotNull——**漏传不报错且等效停用**（null 被服务端按 0 处理），停用/启用意图必须显式传值 |

### 出参（原始返回）

`data` 为 `null`；回读 `benefit.list` 核验 globalEnabled。

### ⚠️ 边界如实声明

服务端本端点**未拦截固定权益 ID**（按 id 查到即可切换其 enabled 列，效果与按类型整体启停等价）；固定权益启停仍应走 `benefit.status`（benefitType + globalEnabled 语义明确）。

### 调用示例

```json
{"capability":"ops.member.benefit.status-by-id","input":{"id":"7300000000000000001","enabled":0},"summary":"停用自定义权益"}
```

---

## ✅ 权益图标上传 — ops.member.benefit.upload-icon

- multipart 图片上传（无业务副作用，产出 COS URL 供 create/update 的 iconUrl 使用）
- **传输形态特例**：multipart 文件上传

### 入参（multipart 文件）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件 | ✅ | JPG/JPEG/PNG，≤2MB（扩展名与 Content-Type 双重校验） |

### 出参（原始返回）

对象含 `url`（图标访问 URL，→ create/update 的 `iconUrl`）。

### 调用示例

```json
{"capability":"ops.member.benefit.upload-icon","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传权益图标（需配合运行时文件上传通道）"}
```
