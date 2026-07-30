#!/usr/bin/env node

/**
 * prosearch.js — ProSearch 联网搜索脚本
 *
 * 替代 curl 命令，通过 Node.js http.request 调用本地 Auth Gateway 代理，
 * 彻底避免 Windows PowerShell 下 curl 的 UTF-8 编码问题。
 *
 * 用法（两种模式，推荐使用 --key=value 模式）:
 *
 *   模式 1: --key=value（推荐，跨平台无转义问题）
 *   node prosearch.cjs --keyword=搜索关键词
 *   node prosearch.cjs --keyword="AI news" --cnt=20
 *   node prosearch.cjs --keyword=最新新闻 --from_time=1710000000 --to_time=1711000000
 *   node prosearch.cjs --keyword=最新新闻 --freshness=24h
 *   node prosearch.cjs --keyword=最新新闻 --freshness=7d
 *
 *   模式 2: JSON 参数（向后兼容，macOS/Linux 可用）
 *   node prosearch.cjs '{"keyword":"搜索关键词"}'
 *
 * 环境变量:
 *   AUTH_GATEWAY_PORT — Auth Gateway 端口（默认 19000）
 */

'use strict';

const http = require('http');

// ── 配置 ────────────────────────────────────────────────────────────────────

const PROXY_PORT = process.env.AUTH_GATEWAY_PORT || '19000';
const PROXY_HOST = '127.0.0.1';
const API_PATH = '/proxy/prosearch/search';
const REQUEST_TIMEOUT = 10000; // 10 秒超时

// ── 参数解析 ─────────────────────────────────────────────────────────────────

/**
 * 解析 --key=value 格式的命令行参数
 * 支持: --keyword=xxx --cnt=10 --from_time=123 --to_time=456
 * 数字值自动转为 Number 类型
 */
function parseCliArgs(argv) {
  const params = {};
  for (const arg of argv) {
    const match = arg.match(/^--([a-z_]+)=(.+)$/i);
    if (match) {
      const key = match[1];
      let value = match[2];
      // 数字类型自动转换（cnt, mode, from_time, to_time）
      if (/^\d+$/.test(value)) {
        value = Number(value);
      }
      params[key] = value;
    }
  }
  return params;
}

/**
 * 处理 --freshness 快捷参数
 * 支持: 24h, 1d, 7d, 30d, 1y
 * 自动计算 from_time 和 to_time
 */
function applyFreshness(params) {
  if (!params.freshness) return;

  const now = Math.floor(Date.now() / 1000);
  const freshnessMap = {
    '24h': 86400,
    '1d': 86400,
    '7d': 604800,
    '30d': 2592000,
    '1y': 31536000,
  };

  const seconds = freshnessMap[params.freshness];
  if (seconds) {
    params.from_time = now - seconds;
    params.to_time = now;
  }
  delete params.freshness;
}

const args = process.argv.slice(2);

if (args.length === 0) {
  const errorResult = {
    success: false,
    message: '缺少搜索参数。\n用法:\n  node prosearch.cjs --keyword=搜索关键词\n  node prosearch.cjs --keyword="AI news" --cnt=20\n  node prosearch.cjs --keyword=最新新闻 --freshness=7d\n  node prosearch.cjs \'{"keyword":"搜索关键词"}\' (仅限 bash/zsh)'
  };
  console.log(JSON.stringify(errorResult));
  process.exit(1);
}

let params;

// 判断参数模式：--key=value 模式 vs JSON 模式
if (args[0].startsWith('--')) {
  // ── 模式 1: --key=value（推荐，跨平台安全） ──
  params = parseCliArgs(args);
  applyFreshness(params);
} else {
  // ── 模式 2: JSON 参数（向后兼容） ──
  const rawArg = args[0];
  try {
    params = JSON.parse(rawArg);
  } catch (e) {
    const errorResult = {
      success: false,
      message: `JSON 参数解析失败: ${e.message}\n提示: Windows PowerShell 环境建议使用 --key=value 模式:\n  node prosearch.cjs --keyword=搜索关键词`
    };
    console.log(JSON.stringify(errorResult));
    process.exit(1);
  }
}

if (!params.keyword) {
  const errorResult = {
    success: false,
    message: '缺少必填参数 keyword。\n用法: node prosearch.cjs --keyword=搜索关键词'
  };
  console.log(JSON.stringify(errorResult));
  process.exit(1);
}

// ── 构建请求体（只保留有效参数）──────────────────────────────────────────────

const body = {};
body.keyword = params.keyword;
if (params.mode !== undefined) body.mode = params.mode;
if (params.cnt !== undefined) body.cnt = params.cnt;
if (params.site !== undefined) body.site = params.site;
if (params.from_time !== undefined) body.from_time = params.from_time;
if (params.to_time !== undefined) body.to_time = params.to_time;
if (params.industry !== undefined) body.industry = params.industry;

const requestBody = JSON.stringify(body);

// ── 发送请求 ─────────────────────────────────────────────────────────────────

const req = http.request(
  {
    host: PROXY_HOST,
    port: Number(PROXY_PORT),
    path: API_PATH,
    method: 'POST',
    timeout: REQUEST_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(requestBody),
    },
  },
  (res) => {
    let data = '';
    res.setEncoding('utf8'); // 关键：强制 UTF-8 解码，避免编码问题
    res.on('data', (chunk) => {
      data += chunk;
    });
    res.on('end', () => {
      // 直接输出响应 JSON
      console.log(data);
    });
  }
);

req.on('timeout', () => {
  req.destroy();
  const errorResult = {
    success: false,
    message: `搜索请求超时（${REQUEST_TIMEOUT / 1000}秒）。请稍后重试。`
  };
  console.log(JSON.stringify(errorResult));
  process.exit(1);
});

req.on('error', (err) => {
  const errorResult = {
    success: false,
    message: `搜索请求失败: ${err.message}`
  };
  console.log(JSON.stringify(errorResult));
  process.exit(1);
});

req.write(requestBody);
req.end();
