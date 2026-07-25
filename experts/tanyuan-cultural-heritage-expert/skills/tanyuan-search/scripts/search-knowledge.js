#!/usr/bin/env node
/**
 * search-knowledge.js
 * ------------------------------------------------------------
 * 调用腾讯探元「知识库检索」接口 (searchKnowledge)。
 *
 * Usage:
 *   node search-knowledge.js "<query>" [datasourceType]
 *
 * Args:
 *   query           必填，检索问题文本（例："三星堆青铜面具背后有什么故事"）
 *   datasourceType  可选，默认 0；0=默认/文物，1=文化遗产
 *
 * Output (stdout, JSON):
 *   {
 *     "requestId": "<链路 ID>",
 *     "text": "<知识库返回的最终文本，Markdown 或纯文本>"
 *   }
 *
 * Exit codes:
 *   0  成功
 *   1  HTTP 错误 / 超时 / API 业务错误
 *   2  参数缺失或非法
 *
 * Requirements: Node.js >= 18 (内置 fetch, AbortController)
 *
 * 备注：接口允许通过 `RequestID` 请求头传入链路 ID。MVP 阶段不启用，由后端自动生成。
 * 如需启用，可在下方 fetch headers 里追加 'RequestID': '<uuid>'.
 * ------------------------------------------------------------
 */

'use strict';

const BASE_URL = 'https://api-ai-creation.tanyuan.qq.com';
const ENDPOINT = '/tanyuanAiAssistant/tool/searchKnowledge';
const TIMEOUT_MS = 30_000;
const MAX_RETRIES = 2;

function usage() {
  process.stderr.write(
    'Usage: node search-knowledge.js "<query>" [datasourceType]\n' +
      '  query:          required, natural language search text\n' +
      '  datasourceType: optional, 0 (default/relics) or 1 (heritage)\n'
  );
}

function parseArgs(argv) {
  const query = argv[2];
  if (!query || typeof query !== 'string' || query.trim() === '') {
    usage();
    process.exit(2);
  }
  let datasourceType = 0;
  if (argv[3] !== undefined) {
    const n = Number(argv[3]);
    if (!Number.isInteger(n) || (n !== 0 && n !== 1)) {
      process.stderr.write(`Invalid datasourceType: ${argv[3]} (must be 0 or 1)\n`);
      process.exit(2);
    }
    datasourceType = n;
  }
  return { query: query.trim(), datasourceType };
}

async function callApi(payload, attempt = 0) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const resp = await fetch(BASE_URL + ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // 'RequestID': '<uuid>', // 可选：显式指定链路 ID
      },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
    const text = await resp.text();
    if (!resp.ok) {
      if (resp.status >= 500 && attempt < MAX_RETRIES) {
        return retry(payload, attempt);
      }
      throw new Error(`HTTP ${resp.status}: ${text.slice(0, 500)}`);
    }
    try {
      return JSON.parse(text);
    } catch (e) {
      throw new Error(`Invalid JSON response: ${text.slice(0, 500)}`);
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      if (attempt < MAX_RETRIES) return retry(payload, attempt);
      throw new Error(`Request timeout after ${TIMEOUT_MS}ms`);
    }
    if (err instanceof TypeError && attempt < MAX_RETRIES) {
      return retry(payload, attempt);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

async function retry(payload, attempt) {
  const backoff = 500 * Math.pow(2, attempt);
  await new Promise((r) => setTimeout(r, backoff));
  return callApi(payload, attempt + 1);
}

function flatten(raw) {
  const root = raw && raw.response ? raw.response : raw || {};
  if (root.error) {
    const msg =
      typeof root.error === 'string' ? root.error : JSON.stringify(root.error);
    throw new Error(`API error: ${msg}`);
  }
  const data = root.data || {};
  return {
    requestId: root.requestId || null,
    text: typeof data.text === 'string' ? data.text : '',
  };
}

async function main() {
  const { query, datasourceType } = parseArgs(process.argv);
  const payload = { query, datasourceType };
  try {
    const raw = await callApi(payload);
    const out = flatten(raw);
    process.stdout.write(JSON.stringify(out, null, 2) + '\n');
  } catch (err) {
    process.stderr.write(`${err.message || String(err)}\n`);
    process.exit(1);
  }
}

main();
