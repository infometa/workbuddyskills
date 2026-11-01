# 商户域 — 租户级配置流程（推荐 / 客服 / 店铺信息）

> 对应契约：`apis/merchant/recommend-config-query.md` / `recommend-config-action.md`（推荐）、`apis/merchant/call-service-config-query.md` / `call-service-config-action.md`（客服）、`apis/merchant/shop-info-query.md` / `shop-info-action.md`（店铺信息）；概念知识：`references/domains/merchant-concepts.md`；写操作共同纪律见 `merchant-core.md`。

---

## ⚠️ 域消歧：推荐配置 vs 商品推荐标记

用户提到"推荐"时，须先区分两个不同概念：
- **推荐配置（本域）**：租户级四力推荐——数据上报开关 + 推荐切换开关 + 凭据（appid/appsecret），用 `recommend-config.get / switches / save` 操作
- **商品推荐标记（商品域）**：单个商品的推荐位标记，用商品域 `ops.product.spu.recommend` 操作

用户说"推荐配置""推荐开关""数据上报"→ 本域；说"把某个商品设为推荐""商品推荐位"→ 商品域。不确定时追问。

---

## 推荐配置（租户级单例）

```
recommend-config.get（密钥脱敏展示）→ switches（只切开关，不动凭据）
```

- 推荐开关开→数据上报开关必须开；任一开关开需完整凭据。
- **凭据（appid/appsecret）修改不开放**：密钥类操作请到管理后台「推荐配置」页面，不走 Agent 通道（明文传输风险）。

## 客服配置（租户级单例）

```
call-service-config.get（电话为完整明文返回）→ 格式预判 → save（enabled=true 时电话与服务时间必填；关闭开关保留原值）
```

- **保存前格式预判（先判后写）**：phoneNumber 仅接受 1 开头 11 位手机号或 `0XX(X)-XXXXXXX(X)(-分机)` 座机；用户给的号码明显不合法（400/800 号、位数不对等）时，直接说明格式要求并请用户更正，**不提交换取服务端拒绝**；serviceTime 缺失同样先追问。

## 店铺信息（租户级单例，upsert + 乐观锁）

```
shop-info.get（取 version 与现值）→ shop-info.update（version 必传；图片字段三态语义：null=保留 / 非 null=更新 / resetFields=置空）→ 回读核验
```

- Logo/背景图先经 `shop-info.upload-logo` / `upload-background`（文件型）取 CDN URL。
