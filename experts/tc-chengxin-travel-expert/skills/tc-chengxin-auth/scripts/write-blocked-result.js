#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const START = 'TC_CHENGXIN_BLOCKED_RESULT_START';
const END = 'TC_CHENGXIN_BLOCKED_RESULT_END';

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key.startsWith('--') || !value || value.startsWith('--')) throw new Error(`参数 ${key} 缺少值`);
    result[key.slice(2)] = value;
    index += 1;
  }
  if (!result['output-dir']) throw new Error('缺少 --output-dir');
  if (!result.reason) throw new Error('缺少 --reason');
  return result;
}

function safeText(value, fallback) {
  return String(value || fallback || '').replace(/[\r\n]+/g, ' ').trim();
}

function safeUrl(value) {
  if (!value) return '';
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'https:' ? parsed.toString() : '';
  } catch (_) {
    return '';
  }
}

function writeBlockedResult(args) {
  const outputDir = path.resolve(args['output-dir']);
  fs.mkdirSync(outputDir, { recursive: true });
  const status = safeText(args.status, '待处理');
  const loginUrl = safeUrl(args['login-url']);
  const lines = [
    `状态: ${status}`,
    `已完成: ${safeText(args.completed, '已识别用户需求并保留当前已确认条件')}`,
    `未完成: ${safeText(args.pending, '实时查询与最终推荐尚未完成')}`,
    `原因: ${safeText(args.reason)}`,
    `登录入口: ${loginUrl ? `[登录同程旅行](${loginUrl})` : '暂未生成'}`,
    `下一步: ${safeText(args['next-step'], '完成所需操作后继续原任务')}`,
    ''
  ];
  const preferred = safeText(args.filename, '同程旅行任务状态.md').replace(/[\\/:*?"<>|]/g, '');
  const markdownFilePath = path.join(outputDir, preferred || '同程旅行任务状态.md');
  fs.writeFileSync(markdownFilePath, lines.join('\n'), { encoding: 'utf8', mode: 0o600 });
  return {
    type: 'tc_chengxin_blocked_result',
    stage: 'blocked',
    nextAction: loginUrl ? 'wait_for_user_auth' : 'wait_for_user_input',
    markdownFilePath,
    allowedReads: [markdownFilePath],
    allowedCalls: [],
    retryBudget: { auth: 1 }
  };
}

function main(argv = process.argv.slice(2)) {
  const receipt = writeBlockedResult(parseArgs(argv));
  process.stdout.write(`${START}\n${JSON.stringify(receipt, null, 2)}\n${END}\n`);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`阻塞状态文件生成失败：${error.message}\n`);
    process.exitCode = 1;
  }
}

module.exports = { parseArgs, safeUrl, writeBlockedResult };
