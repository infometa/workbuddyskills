#!/usr/bin/env node
/**
 * auth-status.mjs — 查询腾讯广告认证状态
 *
 * 调用 TencentAdsAuth.getInfo() 返回当前凭据状态。
 *
 * 入参: 无
 *
 * 输出:
 * {
 *   "integrationId": "tencent-ads",
 *   "authMethod": "api_key",
 *   "status": "active" | "not_configured",
 *   "updatedAt": "2024-01-01T00:00:00.000Z" | null,
 *   "credentialPreview": "xxx..."
 * }
 */

import { TencentAdsAuth } from "tencentads-cli";

const auth = new TencentAdsAuth();
const info = auth.getInfo();

console.log(JSON.stringify(info, null, 2));
