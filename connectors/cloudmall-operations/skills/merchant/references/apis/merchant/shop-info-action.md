# 商户域 — 店铺信息写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-config.md`（租户级配置族）；现值读取（店铺信息查询/乐观锁版本）先读 `shop-info-query.md`。
> 店铺信息为**租户级单例**；编辑走 **upsert + 乐观锁**（`version` 必传）；图片字段走**三态语义**（null=保留旧值 / 非 null=更新 / 置入 `resetFields`=主动置空）。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。**图片上传为文件型 multipart 传输形态**。
> 能力索引：shop-info.update 编辑店铺信息 🔴 · shop-info.upload-logo 上传店铺 Logo · shop-info.upload-background 上传登录页背景图

---

## ✅ 编辑店铺信息 — ops.merchant.shop-info.update

- 🔴 全租户公开形象（登录页/品牌展示）——执行前向用户复述关键字段，执行后回读核验
- **说明**：upsert 模式编辑店铺信息（不存在则创建，存在则乐观锁更新）；`version` 必传（来自查询出参）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| shopName | String | 是 | 店铺名称，≤50 字 |
| shopLogo | String | 否 | 店铺 Logo CDN URL（三态语义） |
| loginBackground | String | 否 | 登录页背景图 CDN URL（三态语义） |
| loginBrandLogo | String | 否 | 登录页品牌 Logo CDN URL（三态语义） |
| defaultAvatar | String | 否 | 未登录默认头像 CDN URL（三态语义） |
| loginProtocolText | String | 否 | 登录页协议文案，≤4000 字，含 `{{protocol:N}}` 占位符 |
| miniProgramLink | String | 否 | 小程序链接路径，≤200 字 |
| resetFields | array&lt;String&gt; | 否 | 主动置空字段名数组（白名单：shopLogo/loginBackground/loginBrandLogo/defaultAvatar/loginProtocolText） |
| version | Integer | 是 | 乐观锁版本号（来自查询出参 `version`） |

> **三态语义**：同一字段不能同时传值和置入 `resetFields`（服务端校验拒绝）。

### 调用示例

```json
{"capability":"ops.merchant.shop-info.update","input":{"shopName":"研学营地旗舰店","shopLogo":"https://cos.example.com/shop/logo.png","version":3},"summary":"把店铺名称改为研学营地旗舰店并更新 Logo"}
```

超时或网络错误时结果不确定——先 `shop-info.get` 回读 `version` 与字段现值，确认是否已生效，不盲目重复提交。

---

## ✅ 上传店铺 Logo — ops.merchant.shop-info.upload-logo

- **传输形态**：仅通过当前运行时的文件型 capability 传递文件
- **说明**：上传店铺 Logo 图片，返回 CDN URL（用于 `shop-info.update` 的 `shopLogo` 字段）。

### multipart 入参

| part | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件（png/jpeg/jpg/gif，≤1 MiB；扩展名与 MagicNumber 双校验） |

### 出参（原始数据）

- **展示字段**：`url`（上传后的 CDN URL）、`key`

### 调用示例

```json
{"capability":"ops.merchant.shop-info.upload-logo","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传新的店铺 Logo；文件由客户端 multipart 提供"}
```

> 文件经 `input.file` 提供工作区路径或 `material:{素材ID}` 引用（文件型 capability，见调用示例）；上方 JSON 的其余字段为配套调用元数据。

---

## ✅ 上传登录页背景图 — ops.merchant.shop-info.upload-background

- **传输形态**：仅通过当前运行时的文件型 capability 传递文件
- **说明**：上传登录页背景图，返回 CDN URL（用于 `shop-info.update` 的 `loginBackground` 字段）。

### multipart 入参

| part | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件（png/jpeg/jpg/gif，≤5 MiB；扩展名与 MagicNumber 双校验） |

### 出参（原始数据）

- **展示字段**：`url`、`key`

### 调用示例

```json
{"capability":"ops.merchant.shop-info.upload-background","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传新的登录页背景图；文件由客户端 multipart 提供"}
```

> 文件经 `input.file` 提供工作区路径或 `material:{素材ID}` 引用（文件型 capability，见调用示例）；上方 JSON 的其余字段为配套调用元数据。
