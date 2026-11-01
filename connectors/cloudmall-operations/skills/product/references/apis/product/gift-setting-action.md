# 商品域 — 赠品（送礼玩法）写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-gift-setting.md`；现态读取（配置/白名单校验）先读 `gift-setting-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：gift-setting.save 送礼配置保存 🔴

---

## ✅ 送礼配置保存 — ops.product.gift-setting.save

- 🔴 商业影响档位（全局配置）；金额区间/祝福语/分享素材先确认；编辑前先 `gift-setting.get` 读现态，修改范围向用户确认
- **语义**：保存送礼玩法配置（校验 + 保存 + 清缓存；⚠️ 控制器注释提及的「内容审核」**当前无实现**，服务端不做内容审核）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | Boolean | ✅ | 送礼玩法开关 |
| minAmount | Number | ✅ | 可送礼商品最低金额（元，≥0，两位小数） |
| maxAmount | Number | ✅ | 可送礼商品最高金额（元，≥0，两位小数） |
| excludedCategoryCodes | Set&lt;String&gt; | — | 排除商品类目编码集合（来自类目树） |
| whitelistSkuIds | Set&lt;String&gt; | — | 商品白名单 SKU ID 集合 |
| defaultBlessing | String | ✅ | 默认祝福语（≤100 字） |
| shareTitle | String | ✅ | 微信分享文案（≤20 字） |
| shareImageUrl | String | ✅ | 微信分享图片 URL（≤512 字符） |
| posterImageUrl | String | ✅ | 分享海报图片 URL（≤512 字符） |
| receiveSuccessImageUrl | String | — | 领取成功图片 URL |
| receiveFailureImageUrl | String | — | 领取失败图片 URL |

### 调用示例

```json
{"capability":"ops.product.gift-setting.save","input":{"enabled":true,"minAmount":10.00,"maxAmount":999.00,"defaultBlessing":"送你一份心意","shareTitle":"好友送你一份礼物","shareImageUrl":"https://cos.example.com/gift/share.png","posterImageUrl":"https://cos.example.com/gift/poster.png"},"summary":"开启送礼玩法并设置金额区间10~999元"}
```
