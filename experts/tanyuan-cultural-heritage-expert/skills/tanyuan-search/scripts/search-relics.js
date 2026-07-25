#!/usr/bin/env node
/**
 * search-relics.js
 * ------------------------------------------------------------
 * 调用腾讯探元「文物 / 世界遗产数据库生成式检索」接口 (searchRelics)。
 * Text2SQL 由后端完成；脚本只透传自然语言问题，不在本地拆词或生成 SQL。
 *
 * Usage:
 *   node search-relics.js "<query>" [datasourceType]
 *
 * Args:
 *   query           必填，保留检索条件与返回意图的自然语言问题
 *                   （例："故宫博物院收藏的明代青铜器有哪些，请返回名称、年代和馆藏机构"）
 *   datasourceType  可选，默认 0；0=文物数据库，1=世界遗产数据库
 *
 * Output (stdout, JSON):
 *   {
 *     "requestId": "<链路 ID>",
 *     "rowCount":  <number>,
 *     "items": [ { ...解析后的对象 }, ... ]
 *   }
 *
 * Exit codes:
 *   0  成功
 *   1  HTTP 错误 / 超时 / API 业务错误
 *   2  参数缺失或非法
 *
 * Requirements: Node.js >= 18 (内置 fetch, AbortController)
 * ------------------------------------------------------------
 */

'use strict';

const BASE_URL = 'https://api-ai-creation.tanyuan.qq.com';
const ENDPOINT = '/tanyuanAiAssistant/tool/searchRelics';
const TIMEOUT_MS = 30_000;
const MAX_RETRIES = 2; // 网络错误 / 5xx 最多重试 2 次（总请求次数 = 1 + 2 = 3）

function usage() {
  process.stderr.write(
    'Usage: node search-relics.js "<query>" [datasourceType]\n' +
      '  query:          required, full natural-language question with filters and return intent\n' +
      '  datasourceType: optional, 0 (cultural relics, default) or 1 (world heritage)\n'
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
    const text = await resp.text();
    if (!resp.ok) {
      // 5xx 才重试；4xx 直接失败
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
    // 网络错误（TypeError: fetch failed 之类）重试
    if (err instanceof TypeError && attempt < MAX_RETRIES) {
      return retry(payload, attempt);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

async function retry(payload, attempt) {
  const backoff = 500 * Math.pow(2, attempt); // 500ms, 1000ms
  await new Promise((r) => setTimeout(r, backoff));
  return callApi(payload, attempt + 1);
}

/**
 * 把 API 原始响应转换为扁平化输出。
 * 上游响应形如：
 *   { response: { requestId, data: { rowCount, rows: ["{...json...}", "{...json...}"] }, error? } }
 * 但也兼容 error/data 直接位于顶层的情况。
 */
function flatten(raw) {
  const root = raw && raw.response ? raw.response : raw || {};
  if (root.error) {
    const msg =
      typeof root.error === 'string' ? root.error : JSON.stringify(root.error);
    throw new Error(`API error: ${msg}`);
  }
  const data = root.data || {};
  const rows = Array.isArray(data.rows) ? data.rows : [];
  const warnings = [];
  const items = rows.map((row, idx) => {
    if (typeof row !== 'string') return row; // 若接口已返回对象，直接透传
    try {
      return JSON.parse(row);
    } catch (e) {
      warnings.push(`row[${idx}] parse failed: ${e.message}`);
      return { _raw: row };
    }
  });
  const out = {
    requestId: root.requestId || null,
    rowCount: typeof data.rowCount === 'number' ? data.rowCount : items.length,
    items,
  };
  if (warnings.length) out._warnings = warnings;
  return out;
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
