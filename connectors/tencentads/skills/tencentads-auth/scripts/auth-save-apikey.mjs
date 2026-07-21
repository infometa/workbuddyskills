#!/usr/bin/env node
/**
 * auth-save-apikey.mjs — 保存腾讯广告 API Key 到本地文件
 *
 * 将用户提供的 API Key 写入 ~/.tencent-ads/credentials.json，
 * 供 callApi() 内部自动读取。
 *
 * 推荐入参:
 *   --api-key mkt_xxx
 * 或:
 *   --api-key=mkt_xxx
 *
 * 兼容旧版 JSON 调用，但不再推荐。
 *
 * 输出:
 * {
 *   "success": true,
 *   "message": "API Key 已保存",
 *   "storagePath": "~/.tencent-ads/credentials.json"
 * }
 */

import { TencentAdsAuth } from "tencentads-cli";

function getApiKeyFromArgs(argv) {
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];

    if (arg === "--api-key") {
      return argv[i + 1];
    }

    if (arg.startsWith("--api-key=")) {
      return arg.slice("--api-key=".length);
    }
  }

  const legacyArg = argv[2];
  if (legacyArg && legacyArg.trim().startsWith("{")) {
    try {
      const input = JSON.parse(legacyArg);
      return input.api_key;
    } catch {
      return undefined;
    }
  }

  return undefined;
}

const apiKey = getApiKeyFromArgs(process.argv);

if (!apiKey || typeof apiKey !== "string" || !apiKey.trim()) {
  console.log(JSON.stringify({
    error: "缺少 api_key 参数",
    usage: [
      "node scripts/auth-save-apikey.mjs --api-key mkt_xxx",
      "node scripts/auth-save-apikey.mjs --api-key=mkt_xxx",
    ],
  }, null, 2));
  process.exit(1);
}

const auth = new TencentAdsAuth();
auth.saveApiKey(apiKey.trim());

console.log(JSON.stringify({
  success: true,
  message: "API Key 已保存",
  storagePath: auth.credentialsFilePath,
}));
