#!/usr/bin/env node
'use strict';

// A local draft check, NOT a hook into WorkBuddy's final message transport.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const MAX_BYTES = 32 * 1024 * 1024;
const sha256 = text => crypto.createHash('sha256').update(text, 'utf8').digest('hex');
// Only platform line endings and one editor-added terminal newline are benign.
const canonical = text => text.replace(/\r\n/g, '\n').replace(/\n$/, '');

function readText(file) {
  const stat = fs.statSync(file);
  if (!stat.isFile() || stat.size > MAX_BYTES) throw new Error('交付文件不是普通文件或超过 32 MiB');
  return fs.readFileSync(file, 'utf8');
}

function metrics(text) {
  const count = regex => (text.match(regex) || []).length;
  return {
    bytes: Buffer.byteLength(text, 'utf8'),
    tableRows: count(/^\|\s*\d+\s*\|/gm),
    pcLinks: count(/\[PC 端预订\]\(/g),
    mobileLinks: count(/\[手机打开\]\(/g),
    qrLinks: count(/\[二维码(?:图片)?\]\(/g)
  };
}

function withDeliveryCheck(manifest, markdown) {
  if (manifest.expertStage !== 'rendered') throw new Error('仅最终渲染产物可生成交付契约');
  const source = readText(manifest.markdownFilePath);
  if (source !== markdown) throw new Error('最终 Markdown 与渲染结果不一致');
  const chunks = manifest.markdownChunkFiles;
  if (!Array.isArray(chunks) || !chunks.length || chunks.length !== manifest.markdownChunkCount
      || chunks.map(readText).join('') !== source) throw new Error('Markdown 分片不完整或顺序错误');
  const contractFilePath = manifest.markdownFilePath + '.delivery.json';
  const draftFilePath = manifest.markdownFilePath + '.reply-draft.md';
  const contract = {
    type: 'tc_chengxin_delivery_contract', version: 1,
    markdownFilePath: path.resolve(manifest.markdownFilePath),
    markdownChunkFiles: chunks.map(file => path.resolve(file)),
    markdownChunkCount: chunks.length,
    sourceSha256: sha256(source),
    expected: { ...metrics(source), resources: manifest.resourceDisplay?.total ?? manifest.stats?.total ?? 0 }
  };
  fs.writeFileSync(contractFilePath, JSON.stringify(contract, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
  return {
    ...manifest,
    deliveryCheck: {
      script: __filename, contractFilePath, draftFilePath, expected: contract.expected,
      args: ['--contract', contractFilePath, '--draft', draftFilePath],
      instruction: '完整读取分片后，把实际准备发送的原文正文写入 draftFilePath，用 script 和 args 校验。ok=true 后逐字发送该草稿，不再总结；HTML 不能替代正文。校验只验证草稿，不代表宿主已经发送。'
    },
    responsePolicy: { ...manifest.responsePolicy, draftCheckRequired: true, forbidRewriteAfterDraftCheck: true },
    finalAnswerInstruction: manifest.finalAnswerInstruction + ' 发送前执行 deliveryCheck 校验实际回复草稿；ok=true 后只发送这份原文，禁止另写推荐摘要或省略链接。'
  };
}

function checkDelivery(contractPath, draftPath) {
  const contract = JSON.parse(readText(contractPath));
  if (contract.type !== 'tc_chengxin_delivery_contract' || contract.version !== 1
      || !Array.isArray(contract.markdownChunkFiles) || !contract.markdownChunkFiles.length
      || contract.markdownChunkFiles.length !== contract.markdownChunkCount
      || !/^[a-f0-9]{64}$/.test(contract.sourceSha256 || '')) throw new Error('交付契约无效');
  const source = readText(contract.markdownFilePath);
  if (sha256(source) !== contract.sourceSha256) throw new Error('原始 Markdown 已改变，不能用修改后的原文放行草稿');
  const chunks = contract.markdownChunkFiles.map(readText).join('');
  if (chunks !== source) throw new Error('Markdown 分片缺失、改写或顺序错误');
  const draftReal = fs.realpathSync(draftPath);
  if ([contract.markdownFilePath, ...contract.markdownChunkFiles, contractPath]
    .some(file => fs.realpathSync(file) === draftReal)) throw new Error('请校验独立回复草稿，不能把原文或契约文件冒充草稿');
  const draft = readText(draftPath);
  const expected = canonical(source), actual = canonical(draft);
  const ok = actual === expected;
  let difference = 0;
  while (difference < expected.length && difference < actual.length && expected[difference] === actual[difference]) difference++;
  return {
    type: 'tc_chengxin_delivery_check', ok, scope: 'draft_only',
    code: ok ? 'DRAFT_VERIFIED' : 'DRAFT_DIFFERS_FROM_RENDERED_MARKDOWN',
    sourceSha256: contract.sourceSha256, draftSha256: sha256(draft),
    expected: { ...metrics(source), resources: contract.expected.resources }, actual: metrics(draft),
    ...(ok ? {} : { firstDifferentLine: expected.slice(0, difference).split('\n').length }),
    instruction: ok
      ? '草稿完整性通过。现在逐字发送已验证草稿，不加开场白、不另写摘要；预览失败的真实说明只能放在完整原文之后。本结果不证明宿主实际发送成功。'
      : '不要发送该草稿。按原分片恢复全部正文、资源表、原始链接及专家解读，最多修正一次再校验；仍失败如实说明，不能把摘要或 HTML 当作完整交付。'
  };
}

function run(argv = process.argv.slice(2)) {
  const options = {};
  for (let i = 0; i < argv.length; i += 2) {
    if (!['--contract', '--draft'].includes(argv[i]) || !argv[i + 1] || options[argv[i]]) throw new Error('需要 --contract <契约文件> --draft <实际回复草稿>');
    options[argv[i]] = path.resolve(argv[i + 1]);
  }
  if (!options['--contract'] || !options['--draft']) throw new Error('需要 --contract <契约文件> --draft <实际回复草稿>');
  const result = checkDelivery(options['--contract'], options['--draft']);
  console.log(JSON.stringify(result));
  return result.ok ? 0 : 1;
}

if (require.main === module) {
  try { process.exitCode = run(); } catch (error) {
    console.error(JSON.stringify({ type: 'tc_chengxin_delivery_check', ok: false, scope: 'draft_only', code: 'INVALID_DELIVERY_INPUT', message: error.message }));
    process.exitCode = 1;
  }
}
module.exports = { withDeliveryCheck, checkDelivery, metrics, run };
