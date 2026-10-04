#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { render } = require('./expert-pipeline');
const { saveDelivery, deliveryReceipt } = require('./expert-delivery');

async function run(argv = process.argv.slice(2)) {
  const files = [];
  let planFile;
  for (let i = 0; i < argv.length; i += 2) {
    if (!argv[i + 1]) throw new Error('参数缺少值');
    if (argv[i] === '--snapshot') files.push(path.resolve(argv[i + 1]));
    else if (argv[i] === '--plan') planFile = path.resolve(argv[i + 1]);
    else throw new Error(`未知参数 ${argv[i]}`);
  }
  if (!planFile || !files.length) throw new Error('需要 --snapshot <快照> --plan <方案.json>');
  process.env.CHENGXIN_WORKBUDDY_EXPERT = '1';
  const started = Date.now();
  const payload = await render(files, JSON.parse(fs.readFileSync(planFile, 'utf8')), { compactChat: true });
  payload.timings = { renderMs: Date.now() - started };
  const manifest = saveDelivery(payload);
  console.log('WORKBUDDY_VISUAL_JSON_START');
  console.log(JSON.stringify({ ...deliveryReceipt(manifest), renderMs: Date.now() - started }, null, 2));
  console.log('WORKBUDDY_VISUAL_JSON_END');
}

if (require.main === module) run().catch((error) => {
  console.error(JSON.stringify({ type: 'expert_plan_error', stage: 'validation_or_render_failed', message: error.message,
    instruction: '不要展示旧产物。根据错误修正方案后最多重试一次；仍失败则报告问题或询问关键条件，不绕过校验。' }));
  process.exitCode = 1;
});
module.exports = { run };
