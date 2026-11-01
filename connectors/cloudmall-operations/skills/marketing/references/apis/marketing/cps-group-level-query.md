# 营销域 — CPS 分销员分组与等级查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-distributor-flow.md`
> **分组**：分销员归组，配合「全局/定向 × 分组」佣金率体系决定分佣水平（见 `cps-commission-query.md`）。
> **等级**：分销员的等级身份（业务等级号 0 起，自动递增），核心参数是**返佣系数**——对按佣金率算出的佣金再乘以该系数（1.0000=100% 基准，最大 10.00 即 10 倍）。
> 通用约定：列表入参支持 `pageNum`（≥1，默认 1）/`pageSize`（1..100，默认 20）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-group.search 分销员分组列表 · cps-group.options 全部分组（下拉场景，不分页） · cps-level.list CPS 等级列表（返佣系数/考核指标） · cps-level.get-rule 等级升降级规则摘要 · cps-level.get-rule-page 等级规则页富文本（C 端展示）
> 写操作见 `cps-group-level-action.md`。

---

## 等级启停顺序约束（服务端强校验）

- **启用必须从低到高**：启用某等级前，所有更低等级必须已启用；且已启用等级的考核指标必须严格递增、非最低等级至少一项考核指标 > 0。
- **停用必须从高到低**：停用某等级前，所有更高等级必须已停用。

---

## ✅ 分组列表 — `ops.marketing.cps-group.search`

- **说明**：分页查询分销员分组；`groupName` 模糊匹配。分组名称租户内唯一。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| groupName | String | 否 | 分组名称（模糊） |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 编辑/删除分组、分组佣金率配置的 groupId）
- **格式敏感字段**：`records[].createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- 展示型字段：`groupName`/`groupDesc`/`memberCount`（分组人数）可直接透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-group.search","input":{"pageNum":1,"pageSize":20,"groupName":"高佣"},"summary":"按名称搜索分销员分组"}
```

---

## ✅ 全部分组（下拉） — `ops.marketing.cps-group.options`

- **说明**：全量分组列表（不分页），用于新建分销员选分组、配置分组佣金率等下拉场景。

### 入参

无（空对象）。

### 出参（原始数据）

- **路径参数来源**：`[].id`（作为各写操作的 groupId）
- 展示型字段：`groupName`/`groupDesc`/`memberCount` 可直接透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-group.options","input":{},"summary":"获取全部分组用于下拉选择"}
```

---

## ✅ 等级列表 — `ops.marketing.cps-level.list`

- **说明**：全量等级列表（不分页），按业务等级号升序；等级图片/背景图为带签名的临时访问 URL。

### 入参

无（空对象）。

### 出参（原始数据）

- **路径参数来源**：`[].levelId`（业务等级号 → 等级启停路径参数；批量修改的 levels[].levelId）
- **枚举字段**：`[].enabled`（0=停用，1=启用，含 `enabledDesc`）
- **格式敏感字段**：`[].commissionRatio`（返佣系数，1.0000=100% 基准，范围 0..10.00）、`[].levelValue`（考核指标 JSON 字符串）
- `levelPicture`/`backgroundImage` 为临时签名 URL，有时效性，仅作展示。

### 调用示例

```json
{"capability":"ops.marketing.cps-level.list","input":{},"summary":"查看分销员等级配置"}
```

---

## ✅ 获取等级规则 — `ops.marketing.cps-level.get-rule`

- **说明**：查询等级升降级规则摘要（是否允许降级 + 规则描述）。

### 入参

无（空对象）。

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| downgradeEnable | 是否允许降级（Integer，1=允许，0=不允许） |
| ruleDesc | 规则描述文本 |

### 调用示例

```json
{"capability":"ops.marketing.cps-level.get-rule","input":{},"summary":"查看等级升降级规则"}
```

---

## ✅ 获取规则页内容 — `ops.marketing.cps-level.get-rule-page`

- **说明**：查询 C 端展示的等级规则页（富文本 HTML）。

### 入参

无（空对象）。

### 出参（原始数据）

- **格式敏感字段**：`content`（富文本 HTML 字符串，可能含标签，展示时原样渲染）

### 调用示例

```json
{"capability":"ops.marketing.cps-level.get-rule-page","input":{},"summary":"查看等级规则页富文本"}
```

---
