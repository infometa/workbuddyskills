---
name: tencentads-auth
description: 腾讯营销（原腾讯广告）技能鉴权凭证管理技能，负责检查 APIKEY 是否有效，当腾讯营销(tencent-ads)系列技能返回认证错误时引导用户提供 APIKEY 并保存(⚠️重要提醒⚠️：腾讯营销 APIKEY 必须通过该技能保存)，所有 tencent-ads 技能共享。
license: MIT. See LICENSE for full terms.
compatibility: any
metadata:
  author: Tencent Ads Delivery Team
  version: "0.5.7"
  icon: key
  category: tencent-ads
  openclaw:
    emoji: "🔑"
---

# 腾讯广告鉴权引导

> **前置依赖**：需安装 `tencentads-cli`（Node.js ≥ 20）。执行 `npm install -g tencentads-cli@latest` 安装或升级；版本过低时 `tencentads` 会给出提示。

> **安全原则**: API Key 等敏感凭证不应在对话窗口中回显。Agent 收到 API Key 后应立即调用保存脚本，不要在回复中重复展示凭据内容。

本技能引导用户完成腾讯广告 API Key 鉴权配置。

## CLI 版本说明

`tencentads-cli` 包含两个不同的命令入口，功能和版本线完全独立：

| 命令 | 说明 | 状态 |
|------|------|------|
| `tencentads` | 基于 Go 实现的新版 CLI，支持 `tencentads auth` 一键授权 | **当前推荐** |
| `tencentads-cli` | 基于 Node.js/TypeScript 实现的旧版 CLI | 不再升级，仅作向后兼容 |

安装 `tencentads-cli@latest` 后两个命令均可用，但**本技能所有授权操作均使用 `tencentads` 命令**。

### 检查 CLI 版本

```bash
tencentads --version
```

如版本过低，`tencentads` 执行时会自动提示，按提示执行 `npm install -g tencentads-cli@latest` 升级。

## 鉴权方式

使用 `X-MKT-API-Key` header 直接调用 `api.e.qq.com` API。

## 一键授权（推荐）

使用 `tencentads auth` 命令完成授权，无需手动传入 API Key：

```bash
tencentads auth login
```

执行后会打开浏览器引导用户在腾讯广告平台完成授权。授权完成后自动保存凭据，所有腾讯营销投放（`tencentads-*`）技能即可使用。

### 验证授权状态

```bash
tencentads auth status
```

返回 `"status": "active"` 表示授权有效。

### 退出授权

```bash
tencentads auth logout
```

## 手动配置 API Key（备用方式）

如无法使用浏览器授权，可在对话中手动提供 API Key：

### 脚本调用说明

执行脚本前需先 `cd` 到技能根目录：

```bash
cd skills/tencentads-auth
```

- 不要向脚本传 JSON 字符串，避免不同操作系统和终端下的转义/引号兼容性问题
- 统一使用显式命令行参数，例如 `--api-key <value>`
- `auth-status.mjs` 无需额外参数

### 前置检查

```bash
node scripts/auth-status.mjs
```

如果返回 `"status": "active"`，说明凭据仍有效，无需重新鉴权。

### 步骤

1. 告知用户：

   > 请提供你的腾讯广告 API Key（格式：`mkt_` 开头的字符串）。
   > API Key 可从腾讯广告平台的开发者设置中获取。

2. 收到用户发送的 API Key 后，**不要在回复中回显凭据内容**，立即调用保存脚本：

   ```bash
   node scripts/auth-save-apikey.mjs --api-key <用户发送的API Key>
   ```

3. 验证保存成功：

   ```bash
   node scripts/auth-status.mjs
   ```

## 鉴权流程总结

1. 优先使用 `tencentads auth login` 完成一键授权
2. 如无法使用浏览器，改用手动提供 API Key 方式
3. 所有腾讯营销投放（`tencentads-*`）技能自动共享该凭据（通过 `callApi` 内部自动读取）

## 认证失败处理

当 `callApi` 返回以下错误时，应触发本技能重新鉴权：

- `未找到腾讯广告认证凭据` — 凭据未配置
- `AUTH_REQUIRED` — 凭据未配置
- `AUTH_EXPIRED` — 凭据已过期或无效
- `Authentication is not valid` — 服务端拒绝认证

### 处理流程

1. 告知用户认证已失效，需要重新配置
2. 优先引导用户执行 `tencentads auth login` 重新授权
3. 如无法使用浏览器，引导用户提供新的 API Key 并调用 `auth-save-apikey.mjs` 保存
4. 鉴权成功后，自动重试引发错误的原始操作

## 相关技能

- 所有腾讯营销投放（`tencentads-*`）技能在遇到认证错误时应引用本技能
- 鉴权凭据由 `callApi` 内部自动读取，各技能脚本无需手动处理鉴权
