#!/usr/bin/env node
'use strict';

// Optional, targeted detail expansion. No API calls, no ad-hoc extraction code.
const path = require('path');
const { loadSnapshots, catalogue } = require('./expert-pipeline');
const { writePages } = require('./decision-evidence');

function redact(value) {
  if (Array.isArray(value)) return value.map(redact);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value)
    .filter(([k]) => !/url|link|token|secret|authorization|cookie/i.test(k)).map(([k, v]) => [k, redact(v)]));
  return typeof value === 'string' ? value.replace(/(?:https?:\/\/|file:\/\/|tctclient:\/\/|hap:\/\/)[^\s<>"']+/gi, '[链接留在产物]') : value;
}
function run(argv) {
  const files = [], refs = [];
  for (let i = 0; i < argv.length; i += 2) {
    if (!argv[i + 1]) throw new Error('需要 --snapshot <快照> --ref <资源编号>，可重复');
    if (argv[i] === '--snapshot') files.push(path.resolve(argv[i + 1]));
    else if (argv[i] === '--ref') refs.push(argv[i + 1]);
    else throw new Error('未知参数');
  }
  if (!refs.length || refs.length > 10) throw new Error('一次展开1–10项与当前决策有关的资源');
  const records = catalogue(loadSnapshots(files));
  const selected = refs.map(ref => { const r = records.find(r => r.ref === ref); if (!r) throw new Error(`未知资源 ${ref}`); return {ref, data: redact(r.item.raw)}; });
  const detailFiles = writePages(selected, path.dirname(files[0]), 'selected-details');
  return { detailFiles, instruction: '同一轮读取全部detailFiles，不再取数；textParts按序连接，完整来源仍为快照。' };
}
if (require.main === module) { try { console.log(JSON.stringify(run(process.argv.slice(2)), null, 2)); } catch (e) { console.error(e.message); process.exitCode = 1; } }
module.exports = { run };
