#!/usr/bin/env node
/**
 * container-scripts/find-available-port.js
 *
 * 容器端：在指定范围内找一个可用 TCP 端口
 *
 * 协议：
 *   node find-available-port.js --input '<json>'
 *
 *   input: {
 *     start?: number;       // 默认 8080
 *     end?: number;         // 默认 8200
 *     exclude?: number[];   // 跳过的端口
 *     host?: string;        // 默认 0.0.0.0
 *   }
 *
 * 输出：
 *   {"status":"success","data":{"port":8081}}
 *   {"status":"failed","error":{"code":"NO_FREE_PORT", ...}}
 *
 * 算法：
 *   依次试 [start, end]，用 net.createServer().listen(port, host)，
 *   能 listen 上即视为可用，立刻 close 并返回；
 *   listen 报 EADDRINUSE 跳下一个。
 */
'use strict';

const net = require('node:net');

function emitSuccess(data) {
  process.stdout.write(JSON.stringify({ status: 'success', data }) + '\n');
  process.exit(0);
}
function emitFailure(code, message, hint) {
  const err = { code, message };
  if (hint) err.hint = hint;
  process.stdout.write(JSON.stringify({ status: 'failed', error: err }) + '\n');
  process.exit(1);
}

function parseInput(argv) {
  const i = argv.indexOf('--input');
  if (i < 0) return {};
  const v = argv[i + 1];
  if (v === undefined) return {};
  try {
    return JSON.parse(v);
  } catch (e) {
    emitFailure('BAD_INPUT', '--input is not valid JSON: ' + e.message);
  }
}

function isValidPort(p) {
  return Number.isInteger(p) && p >= 1 && p <= 65535;
}

/**
 * 探测某个端口是否可用
 * @returns Promise<boolean>
 */
function probe(port, host) {
  return new Promise((resolve) => {
    const s = net.createServer();
    s.unref();
    s.once('error', () => {
      // EADDRINUSE / EACCES 等都视为不可用
      resolve(false);
    });
    s.listen(port, host, () => {
      s.close(() => resolve(true));
    });
  });
}

async function main(argv) {
  const input = parseInput(argv);
  const start = typeof input.start === 'number' ? input.start : 8080;
  const end = typeof input.end === 'number' ? input.end : 8200;
  const host = typeof input.host === 'string' ? input.host : '0.0.0.0';
  const exclude = new Set(
    Array.isArray(input.exclude) ? input.exclude.filter(Number.isInteger) : [],
  );

  if (!isValidPort(start)) {
    emitFailure('BAD_INPUT', 'start out of range 1-65535: ' + start);
  }
  if (!isValidPort(end)) {
    emitFailure('BAD_INPUT', 'end out of range 1-65535: ' + end);
  }
  if (start > end) {
    emitFailure(
      'BAD_INPUT',
      'start (' + start + ') > end (' + end + ')',
    );
  }

  for (let port = start; port <= end; port++) {
    if (exclude.has(port)) continue;
    // eslint-disable-next-line no-await-in-loop
    const ok = await probe(port, host);
    if (ok) {
      emitSuccess({ port, host, range: { start, end } });
    }
  }

  emitFailure(
    'NO_FREE_PORT',
    'No free port in range [' + start + ', ' + end + ']',
    '扩大范围或释放占用的端口',
  );
}

main(process.argv.slice(2)).catch((e) => {
  emitFailure('UNCAUGHT', (e && e.message) || String(e));
});
