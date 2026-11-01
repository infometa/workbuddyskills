# 商户域 — 自提点写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-store.md`；现值读取（分页/详情）先读 `pickup-site-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：pickup-site.create 新增自提点 · pickup-site.update 编辑自提点 · pickup-site.update-status 自提点启停 · pickup-site.delete 删除自提点 🔴

---

## ✅ 新增自提点 — ops.merchant.pickup-site.create

- 表单确认后调用；**超时处理**：结果不确定时先按名称搜索，确认未创建才可重新提交

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | ≤200 字 |
| province / city / district + 编码 | String | 否 | 地址四级；建议从 region.tree 取 |
| address | String | 否 | 详细地址，≤200 字 |
| contactName | String | 否 | 联系人，≤50 |
| contactPhone | String | 否 | 联系电话，≤20 |
| longitude / latitude | Number | 否 | WGS84 坐标（经度 -180~180、纬度 -90~90）；不传时后端尝试从关联门店兜底 |
| businessHoursJson | String | 否 | 每日营业时间 JSON 字符串，结构：`{"mon":{"enabled":true,"start":"09:00","end":"21:00"},...,"sun":{...}}`，键为 mon/tue/wed/thu/fri/sat/sun |
| fulfillmentTemplateId | String | 否 | 关联履约模板ID（关联后用模板时间配置作履约时间） |
| status | Integer | 否 | 0=禁用 1=启用 |
| storeIds | String[] | 否 | 关联门店ID列表（多对多，权威字段） |
| remark | String | 否 | 备注 |

### 出参（原始返回）

`data` 为新建自提点对象，含 `id`。

### 调用示例

```json
{"capability":"ops.merchant.pickup-site.create","input":{"name":"科技园地铁站自提点","province":"广东省","provinceCode":"440000","city":"深圳市","cityCode":"440300","district":"南山区","districtCode":"440305","address":"科技园地铁站 A 口","storeIds":["6000012345678901234"]},"summary":"创建科技园地铁站自提点"}
```

---

## ✅ 编辑自提点 — ops.merchant.pickup-site.update

- 先读详情回填，全量确认后提交
- **字段注意**：`storeId` 单值字段已弃用——统一用 `storeIds` 列表表达关联门店；`storeIds` 传 null 不动关联、**传空数组会清空全部关联**

### 入参

与创建一致（`id` 必填额外加入；全部字段均可选传入）。

### 出参（原始返回）

无返回数据；执行后回读详情核验。

### 调用示例

```json
{"capability":"ops.merchant.pickup-site.update","input":{"id":"7200012345678901234","name":"科技园地铁站自提点","address":"科技园地铁站 B 口","storeIds":["6000012345678901234"]},"summary":"修改自提点位置到B口"}
```

---

## ✅ 自提点启停 — ops.merchant.pickup-site.update-status

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 自提点ID |
| status | Integer | ✅ | 0=禁用 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.pickup-site.update-status","input":{"id":"7200012345678901234","status":0},"summary":"临时停用自提点"}
```

---

## ✅ 删除自提点 — ops.merchant.pickup-site.delete

- 🔴 不可逆——逻辑删除；确认对象名称后执行

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 自提点ID |

### 调用示例

```json
{"capability":"ops.merchant.pickup-site.delete","input":{"id":"7200012345678901234"},"summary":"删除自提点"}
```
