#!/usr/bin/env node
//
// order dump parallel — 按数据量均分时间区间，并行启动多个 dump 任务
//
// 适用场景：数据量极大时，单个 dump 任务的探测与拉取串行推进较慢；
//           通过将整体时间范围切成 N 段并各自启动独立 dump 任务，
//           可充分利用 API 并发配额，大幅缩短整体导出耗时。
//
// 用法：
//   node skills/youzan-order/scripts/order_dump_parallel.js \
//     --concurrency 4 \
//     --output-dir ./orders-out \
//     [--format ndjson|csv] \
//     [--status TRADE_SUCCESS] \
//     [--start-created "2024-01-01 00:00:00"] \
//     [--end-created   "2024-12-31 23:59:59"] \
//     [... 其余 order dump start 支持的过滤参数 ...]
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
//   cat ./orders-out/part-*.ndjson > ./orders-all.ndjson
//   # CSV（注意只保留第一个文件的列头）
//   head -1 ./orders-out/part-0.csv > ./orders-all.csv
//   tail -n +2 -q ./orders-out/part-*.csv >> ./orders-all.csv

'use strict';

const { Command }       = require('commander');
const { execFileSync }  = require('child_process');
const fs                = require('fs');
const path              = require('path');
const auth              = require('../../../scripts/auth');

const CLI_BIN    = path.resolve(__dirname, '../../../bin/youzan-cli.js');

// ─── 时间格式转换 ─────────────────────────────────────────

function formatDate(date) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function parseDate(str) {
  return new Date(str.replace(' ', 'T') + '+08:00');
}

// ─── 探测区间总条数 ───────────────────────────────────────

async function probeTotal(start, end, baseBody, token, httpOpts) {
  const args = [
    CLI_BIN,
    'order', 'dump', 'start',
    ...process.argv.slice(2).filter((v, i, a) => (
      !['--concurrency', '--output-dir'].some((k) => v === k || v.startsWith(k + '=') || a[i - 1] === k)
    )),
    '-o', '/dev/null',
    '--dry-run',
    '--start-created', start,
    '--end-created', end,
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
    if (parseDate(prevStart) > parseDate(Tn)) break;

    // 二分找最大 t，使 count(prevStart, t) <= target
    let lo = parseDate(prevStart);
    let hi = parseDate(Tn);

    while (lo < hi) {
      const mid      = new Date(Math.floor((lo.getTime() + hi.getTime() + 1) / 2));
      const midStr   = formatDate(mid);
      const count    = await probeTotal(prevStart, midStr, baseBody, token, httpOpts);
      if (count <= target) {
        lo = mid;
      } else {
        hi = new Date(mid.getTime() - 1000); // 减 1 秒
      }
    }

    const loStr = formatDate(lo);
    intervals.push({ start: prevStart, end: loStr });
    process.stderr.write(
      `[parallel]   段 ${i + 1}/${N}: ${prevStart} ~ ${loStr}\n`,
    );
    prevStart = formatDate(new Date(lo.getTime() + 1000)); // 加 1 秒
  }

  // 最后一段兜底
  if (parseDate(prevStart) <= parseDate(Tn)) {
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
    'order', 'dump', 'start',
    '-o',               outFile,
    '--format',         opts.format,
    '--start-created',  interval.start,
    '--end-created',    interval.end,
  ];

  // 透传过滤参数（与 order dump start 保持一致）
  if (opts.type)          args.push('--type',          opts.type);
  if (opts.status)        args.push('--status',        opts.status);
  if (opts.orderNo)       args.push('--order-no',      opts.orderNo);
  if (opts.yzOpenId)      args.push('--yz-open-id',    opts.yzOpenId);
  if (opts.receiverPhone) args.push('--receiver-phone',opts.receiverPhone);
  if (opts.receiverName)  args.push('--receiver-name', opts.receiverName);
  if (opts.itemId)        args.push('--item-id',       opts.itemId);
  if (opts.itemTitle)     args.push('--item-title',    opts.itemTitle);
  if (opts.expressType)   args.push('--express-type',  opts.expressType);
  if (opts.keywords)      args.push('--keywords',      opts.keywords);
  if (opts.fields)        args.push('--fields',        opts.fields);
  if (opts.timeout)       args.push('--timeout',       opts.timeout);
  if (opts.retry)         args.push('--retry',         opts.retry);

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
  if (opts.type)          body.type           = opts.type;
  if (opts.status)        body.status         = opts.status;
  if (opts.orderNo)       body.tid            = opts.orderNo;
  if (opts.yzOpenId)      body.yz_open_id     = opts.yzOpenId;
  if (opts.receiverPhone) body.receiver_phone = opts.receiverPhone;
  if (opts.receiverName)  body.receiver_name  = opts.receiverName;
  if (opts.itemId)        body.goods_id       = parseInt(opts.itemId, 10);
  if (opts.itemTitle)     body.goods_title    = opts.itemTitle;
  if (opts.expressType)   body.express_type   = opts.expressType;
  if (opts.keywords)      body.keywords       = opts.keywords;
  return body;
}

// ─── main ─────────────────────────────────────────────────

async function main() {
  const program = new Command();

  program
    .name('order-dump-parallel')
    .description('按数据量均分时间区间，并行启动多个 order dump 任务')
    .requiredOption('--concurrency <n>',     '并行任务数（即时间分段数）')
    .requiredOption('--output-dir <dir>',    '输出目录，各段文件写入该目录（part-0.ndjson / part-1.ndjson …）')
    .option('--format <fmt>',                '输出格式: ndjson | csv',              'ndjson')
    .option('--type <type>',                 '订单类型：NORMAL|PEERPAY|GIFT|FX_CAIGOUDAN 等')
    .option('--status <status>',             '订单状态：WAIT_BUYER_PAY|WAIT_SELLER_SEND_GOODS|TRADE_SUCCESS 等')
    .option('--order-no <orderNo>',          '订单号（即 tid）')
    .requiredOption('--start-created <time>', '创建时间开始（格式：yyyy-MM-dd HH:mm:ss；必填）')
    .requiredOption('--end-created <time>',   '创建时间结束（格式：yyyy-MM-dd HH:mm:ss；必填）')
    .option('--yz-open-id <id>',             '有赞统一 openId')
    .option('--receiver-phone <phone>',      '收货人手机号')
    .option('--receiver-name <name>',        '收货人昵称')
    .option('--item-id <id>',                '商品 itemId（总网商品 ID）；映射开放接口 goods_id')
    .option('--item-title <title>',          '商品名称（支持模糊搜索；映射默认模式 goods_title）')
    .option('--express-type <type>',         '物流类型：EXPRESS|SELF_FETCH|LOCAL_DELIVERY')
    .option('--keywords <text>',             '通用搜索（订单号、收货人手机号、手机号后四位）')
    .option('--fields <modules>',            '指定保留的模块（逗号分隔）：order_info,orders,address_info,pay_info,buyer_info,source_info,remark_info,out_order_info')
    .option('--timeout <ms>',                '请求超时毫秒',                         '30000')
    .option('--retry <n>',                   '重试次数',                             '2')
    .option('--dry-run',                     '仅打印分段计划，不启动任务')
    .addHelpText('after', `
Examples:
  # 4 路并行导出 2024 年订单
  $ node skills/youzan-order/scripts/order_dump_parallel.js \\
      --concurrency 4 --output-dir ./orders-out \\
      --start-created "2024-01-01 00:00:00" --end-created "2024-12-31 23:59:59"

  # 干跑：只查看分段计划
  $ node skills/youzan-order/scripts/order_dump_parallel.js \\
      --concurrency 4 --output-dir ./orders-out \\
      --start-created "2024-01-01 00:00:00" --end-created "2024-12-31 23:59:59" \\
      --dry-run

  # 指定状态 + CSV 格式
  $ node skills/youzan-order/scripts/order_dump_parallel.js \\
      --concurrency 6 --output-dir ./orders-out --format csv \\
      --status TRADE_SUCCESS \\
      --start-created "2024-01-01 00:00:00" --end-created "2024-12-31 23:59:59"

  # 任务启动后逐个查看进度
  $ youzan-cli order dump status <taskId>

  # 全部完成后合并（NDJSON）
  $ cat ./orders-out/part-*.ndjson > ./orders-all.ndjson

  # 全部完成后合并（CSV，只保留第一个文件表头）
  $ head -1 ./orders-out/part-0.csv > ./orders-all.csv
  $ tail -n +2 -q ./orders-out/part-*.csv >> ./orders-all.csv`);

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

  const T0 = opts.startCreated;
  const Tn = opts.endCreated;

  // 校验时间范围不超过 1 年（与 order dump start 保持一致）
  const startDate   = parseDate(T0);
  const endDate     = parseDate(Tn);
  if (adapter.isTimeSpanOverOneYear(startDate, endDate)) {
    process.stderr.write(`[parallel] 错误：时间范围超过 1 年，API 限制每次最多查询 1 年数据\n`);
    process.stderr.write(`[parallel] 当前范围：${T0} ~ ${Tn}，请缩小时间范围或分多次导出\n`);
    process.exit(1);
  }

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
      statusCmd:  t.taskId ? `youzan-cli order dump status ${t.taskId}` : undefined,
      error:      t.error  || undefined,
    })),
    hint: [
      '用 youzan-cli order dump status <taskId> 逐个查看进度',
      '全部完成后执行: cat ' + opts.outputDir + '/part-*.ndjson > merged.ndjson',
    ],
  }, null, 2));
}

main().catch((e) => {
  process.stderr.write(`[parallel] 错误: ${e.message}\n`);
  process.exit(1);
});
