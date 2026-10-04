#!/usr/bin/env node
'use strict';

const childProcess = require('child_process');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');

const execFile = promisify(childProcess.execFile);
const START_MARKER = 'WORKBUDDY_VISUAL_JSON_START';
const END_MARKER = 'WORKBUDDY_VISUAL_JSON_END';
const ALLOWED = new Set(['traffic-query.js', 'hotel-query.js', 'scenery-query.js']);

function parseArgs(argv) {
  const index = argv.indexOf('--requests');
  if (index < 0 || !argv[index + 1]) throw new Error('缺少 --requests <completion-requests.json>');
  return { requestsFile: path.resolve(argv[index + 1]) };
}

function parseReceipt(stdout) {
  const text = String(stdout || '');
  const start = text.indexOf(START_MARKER);
  const end = text.indexOf(END_MARKER, start + START_MARKER.length);
  if (start < 0 || end < 0) return null;
  return JSON.parse(text.slice(start + START_MARKER.length, end).trim());
}

function validatePayload(payload) {
  if (!payload || payload.version !== 1 || !Array.isArray(payload.requests)) {
    throw new Error('补查请求文件格式无效');
  }
  if (payload.requests.length < 1 || payload.requests.length > 3) {
    throw new Error('一次只能补查 1–3 个资源分类');
  }
  for (const request of payload.requests) {
    const scriptName = path.basename(request && request.queryScriptPath || '');
    if (!request || !ALLOWED.has(scriptName)) {
      throw new Error('补查脚本不在允许列表');
    }
    const canonicalPath = require('./expert-pipeline').completionScriptPath(scriptName);
    if (path.resolve(request.queryScriptPath) !== path.resolve(canonicalPath)) {
      throw new Error(`补查脚本路径不受信任: ${request.queryScriptPath}`);
    }
    if (!Array.isArray(request.args) || request.args.some((item) => typeof item !== 'string')) {
      throw new Error('补查参数必须是字符串数组');
    }
    if (request.canRun === false) throw new Error(request.blockedReason || '补查请求缺少关键槽位');
    if (!fs.existsSync(request.queryScriptPath)) throw new Error(`补查脚本不存在: ${request.script}`);
  }
  return payload;
}

async function runRequest(request, options = {}) {
  const wrapper = options.wrapper || path.join(__dirname, 'run-query-with-analysis.js');
  try {
    const result = await (options.execFile || execFile)(process.execPath, [
      wrapper,
      '--query-script', request.queryScriptPath,
      '--', ...request.args
    ], {
      cwd: options.cwd || process.cwd(),
      env: options.env || process.env,
      timeout: options.timeout || 120000,
      maxBuffer: 32 * 1024 * 1024
    });
    const receipt = parseReceipt(result.stdout);
    if (!receipt) throw new Error('补查未返回结构化回执');
    return { category: request.category, ok: true, receipt };
  } catch (error) {
    const output = `${error.stdout || ''}\n${error.stderr || ''}`;
    return {
      category: request.category,
      ok: false,
      authRequired: output.includes('TC_CHENGXIN_REAUTH_REQUIRED'),
      message: error.message
    };
  }
}

async function execute(requestsFile, options = {}) {
  const payload = validatePayload(JSON.parse(fs.readFileSync(requestsFile, 'utf8')));
  const results = await Promise.all(payload.requests.map((request) => runRequest(request, options)));
  const successful = results.filter((item) => item.ok);
  const failed = results.filter((item) => !item.ok);
  const authRequired = failed.some((item) => item.authRequired);
  const snapshotFilePaths = [
    payload.mainSnapshotFilePath,
    ...successful.map((item) => item.receipt.snapshotFilePath)
  ].filter(Boolean);
  const decisionFiles = [
    ...(payload.mainDecisionFiles || []),
    ...successful.flatMap((item) => item.receipt.decisionFiles || [])
  ];
  const mainSnapshot = payload.mainSnapshotFilePath || snapshotFilePaths[0] || path.join(path.dirname(requestsFile), 'itinerary.snapshot.json');
  const snapshotStem = path.basename(mainSnapshot).replace(/\.snapshot\.json$/i, '').replace(/\.json$/i, '');
  const planFilePath = path.join(path.dirname(mainSnapshot), `${snapshotStem}.plan.json`);
  const renderArgs = [
    ...snapshotFilePaths.flatMap(snapshot => ['--snapshot', snapshot]),
    '--plan', planFilePath
  ];
  const allowedReads = [...decisionFiles, payload.planContract, payload.planModeContract].filter(Boolean);
  const renderCall = { script: payload.renderScript, args: renderArgs, after: `write_json:${planFilePath}` };
  const readyForPlan = !authRequired && !failed.length;
  return {
    type: 'workbuddy_completion_batch',
    stage: authRequired ? 'auth_required' : failed.length ? 'partial_resources' : 'awaiting_plan',
    nextAction: authRequired ? 'auth_required' : failed.length ? 'stop_with_partial_result' : 'write_plan',
    snapshotFilePaths,
    decisionFiles,
    planContract: payload.planContract,
    planModeContract: payload.planModeContract,
    planFilePath,
    renderScript: payload.renderScript,
    allowedReads,
    allowedWrites: readyForPlan ? [{ path: planFilePath, format: 'json' }] : [],
    allowedCalls: authRequired
      ? [{ skill: 'tc-chengxin-auth' }]
      : failed.length ? [] : [renderCall],
    actionSequence: authRequired
      ? [{ step: 1, action: 'invoke_skill', skill: 'tc-chengxin-auth' }]
      : failed.length ? [] : [
        { step: 1, action: 'read_files', files: allowedReads },
        { step: 2, action: 'write_json', path: planFilePath, templateSource: 'allowedReads 中的 itinerary 契约' },
        { step: 3, action: 'run_script', ...renderCall }
      ],
    forbiddenActions: ['run_help', 'read_source', 'read_unlisted_files', 'rerun_query', 'run_completion_batch_again'],
    retryBudget: { auth: 1, completionBatch: 0, renderCorrection: 1, present: 1 },
    results,
    instruction: authRequired
      ? '按授权 Skill 完成一次授权，成功后只重试本批补查一次。'
      : failed.length
        ? '不要重复补查；使用已成功资源交付部分结果，并明确列出缺失分类。'
        : '并行补查已完成。严格按 actionSequence 一次写 itinerary plan 并渲染；不要探索脚本或帮助。'
  };
}

async function main(argv = process.argv.slice(2)) {
  const { requestsFile } = parseArgs(argv);
  const receipt = await execute(requestsFile);
  process.stdout.write(`${START_MARKER}\n${JSON.stringify(receipt, null, 2)}\n${END_MARKER}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stderr.write(`行程补查失败：${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = { execute, parseArgs, parseReceipt, runRequest, validatePayload };
