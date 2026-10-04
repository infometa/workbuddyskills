#!/usr/bin/env node
'use strict';

const path = require('path');
const pipeline = require('./expert-pipeline');
const { inputReceipt } = require('./decision-evidence');

const START_MARKER = 'WORKBUDDY_VISUAL_JSON_START';
const END_MARKER = 'WORKBUDDY_VISUAL_JSON_END';

function parseArgs(argv) {
  let snapshotFilePath = '';
  let followUpRequest = '';
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (value === undefined) throw new Error(`${key} 缺少值`);
    if (key === '--snapshot') snapshotFilePath = path.resolve(value);
    else if (key === '--request') followUpRequest = String(value).trim();
    else throw new Error(`未知参数 ${key}`);
  }
  if (!snapshotFilePath) throw new Error('需要 --snapshot <上轮快照路径>');
  if (!followUpRequest) throw new Error('需要 --request <用户本轮筛选或比较需求>');
  if (followUpRequest.length > 3000) throw new Error('用户本轮需求不能超过 3000 字');
  return { snapshotFilePath, followUpRequest };
}

function originalRequestText(snapshot) {
  const request = snapshot.requestParams || {};
  const route = request.departure && request.destination
    ? `${request.departure}到${request.destination}`
    : request.destination || request.departure || '';
  return [route, request.query, request.extra].filter(Boolean).join('；');
}

function buildReceipt(snapshotFilePath, followUpRequest) {
  const resolved = path.resolve(snapshotFilePath);
  const [snapshot] = pipeline.loadSnapshots([resolved]);
  const manifest = {
    type: 'workbuddy_expert_snapshot',
    stage: 'collected',
    snapshotFilePath: resolved,
    snapshotId: snapshot.snapshotId
  };
  const input = pipeline.prepareEvidence(manifest);
  const originalRequest = originalRequestText(snapshot);
  const combinedRequest = [originalRequest, followUpRequest]
    .filter(Boolean).join('；').slice(0, 3000);
  if (input.quickPlanTemplate) {
    input.quickPlanTemplate = { ...input.quickPlanTemplate, userRequest: combinedRequest };
  }
  input.instruction = `本次只分析已有结果，不重新查询或授权。plan.userRequest 合并回执中的 originalRequest 与 followUpRequest；有 quickPlanTemplate 时直接使用其中的 userRequest。${input.instruction}`;
  const receipt = inputReceipt(input);
  return {
    ...receipt,
    responseFlow: 'expert_analysis',
    responseFlowReason: 'follow_up_preference',
    reusedSnapshot: true,
    queryExecuted: false,
    originalRequest,
    followUpRequest
  };
}

function run(argv = process.argv.slice(2)) {
  const { snapshotFilePath, followUpRequest } = parseArgs(argv);
  const receipt = buildReceipt(snapshotFilePath, followUpRequest);
  process.stdout.write(`${START_MARKER}\n${JSON.stringify(receipt, null, 2)}\n${END_MARKER}\n`);
}

if (require.main === module) {
  try {
    run();
  } catch (error) {
    console.error(`复用本次查询结果失败：${error.message}`);
    process.exitCode = 1;
  }
}

module.exports = { buildReceipt, originalRequestText, parseArgs, run };
