#!/usr/bin/env node
//
// member dump parallel — 按数据量均分时间区间，并行启动多个 dump 任务
//
// 适用场景：数据量极大时，单个 dump 任务的探测与拉取串行推进较慢；
//           通过将整体时间范围切成 N 段并各自启动独立 dump 任务，
//           可充分利用 API 并发配额，大幅缩短整体导出耗时。
//
// 用法：
//   node skills/youzan-member/scripts/member_dump_parallel.js \
//     --concurrency 4 \
//     --output-dir ./members-out \
//     [--format ndjson|csv] \
//     [--is-member 1] \
//     [--created-at-start <秒时间戳>] \
//     [--created-at-end   <秒时间戳>] \
//     [... 其余 member dump start 支持的过滤参数 ...]
//
// 分段算法（贪心二分）：
//   1. 探测整体时间区间总条数 total
//   2. 目标每段 target = ceil(total / N)
//   3. 从左到右贪心：对每个分割点，在 [prevStart, Tn] 上二分查找
//      最大时间戳 t，使 count(prevStart, t) <= target
//   4. 最后一段兜底取剩余区间
//
// 输出（stdout JSON）：每个子任务的 taskId、输出文件、时间区间
// 进度（stderr）：分割探测过程日志
//
// 任务完成后合并：
//   # NDJSON
//   cat ./members-out/part-*.ndjson > ./members-all.ndjson
//   # CSV（注意只保留第一个文件的表头）
//   head -1 ./members-out/part-0.csv > ./members-all.csv
//   tail -n +2 -q ./members-out/part-*.csv >> ./members-all.csv

'use strict';

const { Command }       = require('commander');
const { execFileSync }  = require('child_process');
const fs                = require('fs');
const path              = require('path');
const auth              = require('../../../scripts/auth');

const CLI_BIN    = path.resolve(__dirname, '../../../bin/youzan-cli.js');

function parseCsvNumber(value) {
  return String(value).split(',').map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n));
}

// ─── 探测区间总条数 ───────────────────────────────────────

async function probeTotal(start, end, baseBody, token, httpOpts) {
  const args = [
    CLI_BIN,
    'member', 'dump', 'start',
    ...process.argv.slice(2).filter((v, i, a) => (
      !['--concurrency', '--output-dir'].some((k) => v === k || v.startsWith(k + '=') || a[i - 1] === k)
    )),
    '-o', '/dev/null',
    '--dry-run',
    '--created-at-start', String(start),
    '--created-at-end', String(end),
  ];
  return JSON.parse(execFileSync(process.execPath, args, { encoding: 'utf-8' }).trim())._dump_plan.estimatedTotal;
}

// ─── 贪心二分：将 [T0, Tn] 切成 N 个数据量近似相等的区间 ─

async function splitIntervals(T0, Tn, N, total, baseBody, token, httpOpts) {
  if (N <= 1) return [{ start: T0, end: Tn }];

  const target    = Math.ceil(total / N);
  const intervals = [];
  let   prevStart = T0;

  process.stderr.write(`[parallel] 总量 ${total} 条，目标每段 ~${target} 条，切 ${N} 段\n`);

  for (let i = 0; i < N - 1; i++) {
    if (prevStart > Tn) break;

    // 二分找最大 t，使 count(prevStart, t) <= target
    let lo = prevStart;
    let hi = Tn;

    while (lo < hi) {
      const mid   = Math.floor((lo + hi + 1) / 2);
      const count = await probeTotal(prevStart, mid, baseBody, token, httpOpts);
      if (count <= target) {
        lo = mid;
      } else {
        hi = mid - 1;
      }
    }

    intervals.push({ start: prevStart, end: lo });
    process.stderr.write(
      `[parallel]   段 ${i + 1}/${N}: ${prevStart} ~ ${lo}\n`,
    );
    prevStart = lo + 1;
  }

  // 最后一段兜底
  if (prevStart <= Tn) {
    intervals.push({ start: prevStart, end: Tn });
    process.stderr.write(
      `[parallel]   段 ${intervals.length}/${N}: ${prevStart} ~ ${Tn}（兜底）\n`,
    );
  }

  return intervals;
}

// ─── 启动单个 dump start 任务 ──────────────────────────────

function startDumpTask(interval, partIdx, opts) {
  const ext     = opts.format === 'csv' ? 'csv' : 'ndjson';
  const outFile = path.resolve(opts.outputDir, `part-${partIdx}.${ext}`);

  const args = [
    CLI_BIN,
    'member', 'dump', 'start',
    '-o',               outFile,
    '--format',         opts.format,
    '--created-at-start', String(interval.start),
    '--created-at-end',   String(interval.end),
  ];

  // 透传过滤参数（与 member dump start 保持一致）
  if (opts.isMember  !== undefined && opts.isMember  !== '') args.push('--is-member',  opts.isMember);
  if (opts.gender    !== undefined && opts.gender    !== '') args.push('--gender',     opts.gender);
  if (opts.source)                                            args.push('--source',     opts.source);
  if (opts.tagIds)                                            args.push('--tag-ids',    opts.tagIds);
  if (opts.ascriptionKdtIds)                                  args.push('--ascription-kdt-ids', opts.ascriptionKdtIds);
  if (opts.hasMobile !== undefined && opts.hasMobile !== '') args.push('--has-mobile', opts.hasMobile);
  if (opts.sortField)                                         args.push('--sort-field', opts.sortField);
  if (opts.sortOrder)                                         args.push('--sort-order', opts.sortOrder);
  if (opts.timeout)                                           args.push('--timeout',    opts.timeout);
  if (opts.retry)                                             args.push('--retry',      opts.retry);

  try {
    const stdout = execFileSync(process.execPath, args, { encoding: 'utf-8' });
    const result = JSON.parse(stdout.trim());
    return { partIdx, interval, outFile, ...result };
  } catch (e) {
    const msg = e.stdout ? (() => { try { return JSON.parse(e.stdout).error?.message; } catch { return e.stdout.trim(); } })() : e.message;
    return { partIdx, interval, outFile, error: msg || e.message };
  }
}

// ─── 构造 API 请求基础 body ───────────────────────────────

function buildBaseBody(opts, config) {
  const body = { kdt_id: parseInt(config.kdtId, 10) };
  if (opts.sortField) body.sort_field = opts.sortField;
  if (opts.sortOrder) body.sort_order = opts.sortOrder;
  if (opts.gender    !== undefined && opts.gender    !== '') body.gender    = parseInt(opts.gender,    10);
  if (opts.source)    body.source   = opts.source;
  if (opts.isMember  !== undefined && opts.isMember  !== '') body.is_member = parseInt(opts.isMember, 10);
  if (opts.tagIds) {
    body.tag_ids = parseCsvNumber(opts.tagIds);
  }
  if (opts.ascriptionKdtIds) body.ascription_kdt_ids = parseCsvNumber(opts.ascriptionKdtIds);
  if (opts.hasMobile !== undefined && opts.hasMobile !== '') {
    body.has_mobile = opts.hasMobile === 'true' || opts.hasMobile === '1';
  }
  return body;
}

// ─── main ─────────────────────────────────────────────────

async function main() {
  const program = new Command();

  program
    .name('member-dump-parallel')
    .description('按数据量均分时间区间，并行启动多个 member dump 任务')
    .requiredOption('--concurrency <n>',     '并行任务数（即时间分段数）')
    .requiredOption('--output-dir <dir>',    '输出目录，各段文件写入该目录（part-0.ndjson / part-1.ndjson …）')
    .option('--format <fmt>',                '输出格式: ndjson | csv',              'ndjson')
    .option('--is-member <0|1>',             '是否为会员：0 非会员，1 会员')
    .option('--gender <n>',                  '性别：0 未知，1 男，2 女')
    .option('--source <id>',                 '来源渠道')
    .option('--tag-ids <ids>',               '标签 ID，逗号分隔')
    .option('--ascription-kdt-ids <ids>',    '客户归属店铺 kdt_id，逗号分隔')
    .option('--has-mobile <true|false>',     '是否有手机号')
    .option('--created-at-start <ts>',       '成为客户时间起始（秒时间戳）；未传默认 2015-01-01')
    .option('--created-at-end <ts>',         '成为客户时间截止（秒时间戳）；未传默认当前时间')
    .option('--sort-field <field>',          '排序字段，如 created_at')
    .option('--sort-order <asc|desc>',       '排序方向')
    .option('--timeout <ms>',                '请求超时毫秒',                         '30000')
    .option('--retry <n>',                   '重试次数',                             '2')
    .option('--dry-run',                     '仅打印分段计划，不启动任务')
    .addHelpText('after', `
Examples:
  # 4 路并行导出全量会员
  $ node skills/youzan-member/scripts/member_dump_parallel.js \\
      --concurrency 4 --output-dir ./members-out --is-member 1

  # 干跑：只查看分段计划
  $ node skills/youzan-member/scripts/member_dump_parallel.js \\
      --concurrency 4 --output-dir ./members-out --is-member 1 --dry-run

  # 指定时间范围 + CSV 格式
  $ node skills/youzan-member/scripts/member_dump_parallel.js \\
      --concurrency 6 --output-dir ./members-out --format csv \\
      --is-member 1 \\
      --created-at-start 1420070400 --created-at-end 1735689600

  # 任务启动后逐个查看进度
  $ youzan-cli member dump status <taskId>

  # 全部完成后合并（NDJSON）
  $ cat ./members-out/part-*.ndjson > ./members-all.ndjson

  # 全部完成后合并（CSV，只保留第一个文件表头）
  $ head -1 ./members-out/part-0.csv > ./members-all.csv
  $ tail -n +2 -q ./members-out/part-*.csv >> ./members-all.csv`);

  program.parse(process.argv);
  const opts = program.opts();

  const N = parseInt(opts.concurrency, 10);
  if (isNaN(N) || N < 1) {
    process.stderr.write('--concurrency 必须是正整数\n');
    process.exit(1);
  }

  const config    = auth.loadConfig();
  const httpOpts  = { timeout: parseInt(opts.timeout, 10), retries: parseInt(opts.retry, 10) };
  const tokenData = await auth.getValidToken(config);
  const token     = tokenData.access_token;
  const baseBody  = buildBaseBody(opts, config);

  const T0 = opts.createdAtStart ? parseInt(opts.createdAtStart, 10) : 1420070400;
  const Tn = opts.createdAtEnd   ? parseInt(opts.createdAtEnd,   10) : Math.floor(Date.now() / 1000);

  process.stderr.write(`[parallel] 探测总量（时间范围 ${T0} ~ ${Tn}）...\n`);
  const total = await probeTotal(T0, Tn, baseBody, token, httpOpts);

  if (total === 0) {
    console.log(JSON.stringify({ ok: true, total: 0, intervals: [], tasks: [], hint: '无符合条件的数据' }));
    return;
  }

  const actualN   = Math.min(N, total);
  const intervals = await splitIntervals(T0, Tn, actualN, total, baseBody, token, httpOpts);

  if (opts.dryRun) {
    const targetPerSeg = Math.ceil(total / intervals.length);
    console.log(JSON.stringify({
      _plan: {
        total,
        concurrency:      N,
        actualSegments:   intervals.length,
        targetPerSegment: targetPerSeg,
        intervals:        intervals.map((iv, i) => ({ partIdx: i, ...iv })),
        outputDir:        opts.outputDir,
        format:           opts.format,
      },
    }, null, 2));
    return;
  }

  if (!fs.existsSync(opts.outputDir)) fs.mkdirSync(opts.outputDir, { recursive: true });

  process.stderr.write(`[parallel] 启动 ${intervals.length} 个 dump 任务...\n`);

  const tasks = intervals.map((interval, i) => {
    const t = startDumpTask(interval, i, opts);
    if (t.taskId) {
      process.stderr.write(`[parallel]   part-${i}: taskId=${t.taskId}  → ${t.outFile}\n`);
    } else {
      process.stderr.write(`[parallel]   part-${i}: 启动失败 — ${t.error}\n`);
    }
    return t;
  });

  const allOk = tasks.every((t) => !t.error);

  console.log(JSON.stringify({
    ok:          allOk,
    total,
    concurrency: N,
    tasks: tasks.map((t) => ({
      partIdx:    t.partIdx,
      taskId:     t.taskId,
      status:     t.status,
      outputFile: t.outFile,
      interval:   t.interval,
      statusCmd:  t.taskId ? `youzan-cli member dump status ${t.taskId}` : undefined,
      error:      t.error  || undefined,
    })),
    hint: [
      '用 youzan-cli member dump status <taskId> 逐个查看进度',
      '全部完成后执行: cat ' + opts.outputDir + '/part-*.ndjson > merged.ndjson',
    ],
  }, null, 2));
}

main().catch((e) => {
  process.stderr.write(`[parallel] 错误: ${e.message}\n`);
  process.exit(1);
});
