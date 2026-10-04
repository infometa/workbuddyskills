#!/usr/bin/env node
'use strict';

const childProcess = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { resolveClientContext } = require('../../../scripts/client-context');
const { applyTrainDateDefault, classifyResponseFlow, prepareQuery } = require('./request-contract');
const { normalizeResponseMode } = require('./response-mode');

const START_MARKER = 'WORKBUDDY_VISUAL_JSON_START';
const END_MARKER = 'WORKBUDDY_VISUAL_JSON_END';
const MAX_CHUNK_BYTES = 12 * 1024;

function parseArgs(argv) {
  const separator = argv.indexOf('--');
  const control = separator >= 0 ? argv.slice(0, separator) : argv;
  const queryArgs = separator >= 0 ? argv.slice(separator + 1) : [];
  const scriptIndex = control.indexOf('--query-script');
  const legacyQueryIndex = control.indexOf('--query');
  if (scriptIndex >= 0 && legacyQueryIndex >= 0) {
    throw new Error('--query-script 与兼容参数 --query 不能同时使用');
  }
  const selectedIndex = scriptIndex >= 0 ? scriptIndex : legacyQueryIndex;
  const query = selectedIndex >= 0 ? control[selectedIndex + 1] : '';
  const intentIndex = control.indexOf('--intent');
  const responseModeIndex = control.indexOf('--response-mode');
  if (control.filter(value => value === '--response-mode').length > 1) {
    throw new Error('--response-mode 不能重复');
  }
  if (responseModeIndex >= 0
    && (!control[responseModeIndex + 1] || control[responseModeIndex + 1].startsWith('--'))) {
    throw new Error('--response-mode 缺少值');
  }
  return {
    query,
    queryArgs,
    intent: intentIndex >= 0 ? control[intentIndex + 1] : '',
    responseMode: normalizeResponseMode(responseModeIndex >= 0 ? control[responseModeIndex + 1] : 'auto'),
    legacyQueryScriptFlag: scriptIndex < 0 && legacyQueryIndex >= 0
  };
}

// Keep the original query implementation intact. All query runners already accept --surface.
// Consume option values as pairs; do not rewrite channel-like text inside user preferences.
function queryArguments(args, context) {
  const result = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    const key = arg.split('=')[0];
    const isOption = arg.startsWith('--');
    const hasValue = isOption && !arg.includes('=')
      && index + 1 < args.length && !args[index + 1].startsWith('--');
    if (key !== '--surface' && key !== '--channel') {
      result.push(arg);
      if (hasValue) result.push(args[index + 1]);
    }
    if (hasValue) index += 1;
  }
  return [...result, '--channel', 'workbuddy', '--surface', context.surface];
}

function cliInvocation(env = process.env, platform = process.platform) {
  const testCli = env.NODE_ENV === 'test' ? String(env.TC_CHENGXIN_CLI_TEST_PATH || '').trim() : '';
  if (testCli) {
    return /\.js$/i.test(testCli)
      ? { command: process.execPath, prefixArgs: [testCli], testCli }
      : { command: testCli, prefixArgs: [], testCli };
  }
  const pluginRoot = path.resolve(__dirname, '..', '..', '..');
  const bundled = path.join(pluginRoot, 'runtime', 'tc-chengxin-cli', 'bin', 'cli.js');
  if (fs.existsSync(bundled)) return { command: process.execPath, prefixArgs: [bundled] };
  if (env.TC_CHENGXIN_CLI_PATH) {
    return /\.js$/i.test(env.TC_CHENGXIN_CLI_PATH)
      ? { command: process.execPath, prefixArgs: [env.TC_CHENGXIN_CLI_PATH] }
      : { command: env.TC_CHENGXIN_CLI_PATH, prefixArgs: [] };
  }
  const executable = platform === 'win32' ? 'tc-chengxin.cmd' : 'tc-chengxin';
  const workbuddyDir = String(env.WORKBUDDY_CONFIG_DIR || '').trim() || path.join(os.homedir(), '.workbuddy');
  const managed = path.join(workbuddyDir, 'binaries', 'node', 'cli-connector-packages', 'bin', executable);
  return { command: fs.existsSync(managed) ? managed : executable, prefixArgs: [] };
}

function queryEnvironment(env = process.env) {
  const invocation = cliInvocation(env);
  const token = childProcess.spawnSync(invocation.command, [...invocation.prefixArgs, 'token'], {
    env, encoding: 'utf8', windowsHide: true, timeout: 15000
  });
  const apiKey = String(token.stdout || '').trim();
  if (token.status !== 0 || !apiKey) return null;
  const pluginRoot = path.resolve(__dirname, '..', '..', '..');
  const bundledLauncher = path.join(
    pluginRoot,
    'bin',
    process.platform === 'win32' ? 'tc-chengxin.cmd' : 'tc-chengxin'
  );
  return {
    ...env,
    CHENGXIN_API_KEY: apiKey,
    CHENGXIN_OUTPUT_GUARD: 'display_contract',
    CHENGXIN_CALLER_CHANNEL: 'workbuddy',
    CHENGXIN_WORKBUDDY_EXPERT: '1',
    CHENGXIN_EXPERT_PHASE: 'collect',
    ...(invocation.testCli
      ? { TC_CHENGXIN_CLI_PATH: invocation.testCli }
      : fs.existsSync(bundledLauncher) ? { TC_CHENGXIN_CLI_PATH: bundledLauncher } : {})
  };
}

function parseManifest(stdout) {
  const text = String(stdout || '');
  const start = text.indexOf(START_MARKER);
  const end = text.indexOf(END_MARKER, start + START_MARKER.length);
  if (start < 0 || end < 0) return null;
  const jsonText = text.slice(start + START_MARKER.length, end).trim();
  try {
    return JSON.parse(jsonText);
  } catch (_) {
    return null;
  }
}

function stripMarkdown(value) {
  return String(value || '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[*_`]/g, '')
    .replace(/<[^>]+>/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function parseTableCells(line) {
  return String(line || '').trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
}

function isSeparatorRow(cells) {
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));
}

function sectionType(section) {
  if (/机票/.test(section)) return 'flight';
  if (/火车/.test(section)) return 'train';
  if (/汽车/.test(section)) return 'bus';
  if (/酒店/.test(section)) return 'hotel';
  if (/景点/.test(section)) return 'scenery';
  if (/度假/.test(section)) return 'travel';
  if (/攻略|行程/.test(section)) return 'plan';
  return 'other';
}

function extractEvidence(markdown) {
  const lines = String(markdown || '').split(/\r?\n/);
  const itinerary = [];
  const facts = [];
  let section = '';
  let group = '';
  let inAdvice = false;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (/行程安排建议/.test(line)) inAdvice = true;
    if (/^####\s+/.test(line)) {
      section = stripMarkdown(line.replace(/^####\s+/, ''));
      group = '';
      inAdvice = false;
      continue;
    }
    if (/^#####\s+/.test(line)) {
      group = stripMarkdown(line.replace(/^#####\s+/, ''));
      continue;
    }
    if (inAdvice && (/^\*\*📅\s*Day/i.test(line.trim()) || /^-\s+/.test(line.trim()))) {
      itinerary.push(stripMarkdown(line.replace(/^-\s+/, '')));
    }
    if (!/^\s*\|/.test(line) || index + 1 >= lines.length) continue;
    const headers = parseTableCells(line);
    const separator = parseTableCells(lines[index + 1]);
    if (!isSeparatorRow(separator) || separator.length !== headers.length) continue;
    index += 2;
    while (index < lines.length && /^\s*\|/.test(lines[index])) {
      const cells = parseTableCells(lines[index]);
      const fields = {};
      headers.forEach((header, cellIndex) => {
        const key = stripMarkdown(header);
        if (!key || key === '预订') return;
        fields[key] = stripMarkdown(cells[cellIndex] || '');
      });
      facts.push({
        ref: `E${String(facts.length + 1).padStart(3, '0')}`,
        type: sectionType(section),
        section,
        ...(group ? { group } : {}),
        fields
      });
      index += 1;
    }
    index -= 1;
  }

  return {
    type: 'tc_chengxin_expert_evidence',
    version: '1.0',
    source: '从 Skill 原始 Markdown 确定性提取；已移除预订列和链接',
    evidencePolicy: {
      price: '价格均按原文展示价/起价理解。除非原文明确计价单位、人数、房间数和晚数，否则不得乘算或汇总总预算。',
      budget: '用户预算只是筛选约束，不是实际花费。费用项不完整时不得估算总价区间，也不得声称方案在预算内。',
      missing: '儿童价、税费、行李额、门票人数、房间/晚数、市内交通、距离和耗时未出现时均为未知。',
      geography: '不得仅凭同城、同区或名称推断步行可达、顺路、距离或车程。',
      feasibility: '必须交叉校验到达/返程时间与开放时间；换乘或接驳耗时未知时不能断言赶得上。'
    },
    itinerary,
    facts
  };
}

function splitEvidence(context, maxBytes = MAX_CHUNK_BYTES) {
  const header = { ...context };
  const facts = Array.isArray(header.facts) ? header.facts : [];
  delete header.facts;
  if (Buffer.byteLength(JSON.stringify(context, null, 2), 'utf8') <= maxBytes || facts.length === 0) {
    return [context];
  }
  const groups = [];
  let current = [];
  facts.forEach((fact) => {
    const candidate = [...current, fact];
    if (current.length && Buffer.byteLength(JSON.stringify({ ...header, facts: candidate }, null, 2), 'utf8') > maxBytes) {
      groups.push(current);
      current = [fact];
    } else {
      current = candidate;
    }
  });
  if (current.length) groups.push(current);
  return groups.map((group, index) => ({
    ...header,
    chunkIndex: index + 1,
    chunkCount: groups.length,
    facts: group
  }));
}

function uniquePath(directory, preferredName) {
  const ext = path.extname(preferredName);
  const stem = path.basename(preferredName, ext);
  let candidate = path.join(directory, preferredName);
  let index = 2;
  while (fs.existsSync(candidate)) {
    candidate = path.join(directory, `${stem}-${index}${ext}`);
    index += 1;
  }
  return candidate;
}

function splitUtf8(value, maxBytes = MAX_CHUNK_BYTES) {
  const text = String(value || '');
  if (Buffer.byteLength(text, 'utf8') <= maxBytes) return [text];
  const chunks = [];
  let current = '';
  let bytes = 0;
  for (const character of text) {
    const size = Buffer.byteLength(character, 'utf8');
    if (current && bytes + size > maxBytes) {
      chunks.push(current);
      current = '';
      bytes = 0;
    }
    current += character;
    bytes += size;
  }
  if (current || chunks.length === 0) chunks.push(current);
  return chunks;
}

function safeTopic(value) {
  return stripMarkdown(value || '同程旅行查询结果').replace(/[\\/:*?"<>|]/g, '').slice(0, 80) || '同程旅行查询结果';
}

function withArtifactDelivery(inputManifest, env = process.env, cwd = process.cwd(), platform = process.platform) {
  if (!inputManifest || typeof inputManifest !== 'object') return inputManifest;
  const clientContext = resolveClientContext(env, platform);
  const rawHtmlPath = String(inputManifest.htmlFilePath || '').trim();
  const htmlFilePath = rawHtmlPath
    ? (path.isAbsolute(rawHtmlPath) ? path.normalize(rawHtmlPath) : path.resolve(cwd, rawHtmlPath))
    : '';
  const artifactFiles = htmlFilePath ? [htmlFilePath] : [];
  const workspacePath = path.resolve(
    String(env.CODEBUDDY_PROJECT_DIR || env.CLAUDE_PROJECT_DIR || cwd)
  );
  const presentFilesArgs = artifactFiles.length
    ? {
        files: artifactFiles,
        explanation: '同程旅行查询结果 HTML 页面',
        cwd: workspacePath
      }
    : null;
  const desktopRequired = artifactFiles.length > 0 && clientContext.surface === 'desktop';
  const artifactInstruction = artifactFiles.length
    ? (desktopRequired
      ? 'PC 端产物交付为硬门禁：最终回复前必须使用 presentFilesArgs 调用 present_files 并确认成功；多次查询时合并全部 artifactFiles 后一次调用。失败时按原路径仅重试一次，仍失败则明确说明预览失败并交付完整原文。禁止把 outputs/... 或本地路径写进正文代替产物。'
      : '移动端/云端兼容交付：保留完整 Markdown 和原始 HTML。若当前提供 present_files，使用 presentFilesArgs 展示文件卡片或预览；否则使用当前明确可用的文件附件工具交付同一 HTML。工具不可用或失败时不重试 PC 侧边栏，不阻塞完整原文回复，明确说明 HTML 已生成但文件预览未能交付。仅使用工具实际返回的文件入口，不伪造链接、不公开上传产物、不暴露本地或沙箱路径。')
    : '本次查询没有 HTML 产物，不调用 present_files。';

  return {
    ...inputManifest,
    htmlFilePath,
    artifactFiles,
    artifactCount: artifactFiles.length,
    clientContext,
    artifactDeliveryMode: !artifactFiles.length ? 'none' : desktopRequired ? 'desktop-sidebar' : 'portable-file',
    presentFilesArgs,
    presentFilesInstruction: artifactInstruction,
    artifactDeliveryInstruction: artifactInstruction,
    finalAnswerInstruction: `按 markdownChunkFiles 顺序并行读取、按索引无缝拼接，并逐字输出完整原始 Markdown。${artifactInstruction}`,
    responsePolicy: {
      ...(inputManifest.responsePolicy || {}),
      presentFilesRequired: desktopRequired,
      blockFinalAnswerUntilPresentFiles: desktopRequired,
      artifactDeliveryRequired: artifactFiles.length > 0,
      artifactTextPathIsNotDelivery: true
    }
  };
}

function normalizeQueryManifest(payload) {
  if (payload && payload.markdownFilePath && fs.existsSync(payload.markdownFilePath)) return payload;
  if (!payload || typeof payload.markdown !== 'string') return payload;
  const outputBase = payload.htmlFilePath
    ? path.dirname(payload.htmlFilePath)
    : path.resolve(process.env.CHENGXIN_WORKBUDDY_OUTPUT_DIR || path.join(process.cwd(), 'outputs'));
  fs.mkdirSync(outputBase, { recursive: true });
  const topic = safeTopic(
    (payload.responsePolicy && payload.responsePolicy.finalAnswerMustStartWith)
      || payload.htmlFileName
      || '同程旅行查询结果'
  ).replace(/\.html$/i, '');
  const markdownFilePath = uniquePath(outputBase, `${topic}.md`);
  fs.writeFileSync(markdownFilePath, payload.markdown, 'utf8');
  const chunks = splitUtf8(payload.markdown);
  const markdownChunkFiles = chunks.length === 1 ? [markdownFilePath] : chunks.map((chunk, index) => {
    const chunkPath = uniquePath(outputBase, `${topic}.part-${String(index + 1).padStart(3, '0')}.md`);
    fs.writeFileSync(chunkPath, chunk, 'utf8');
    return chunkPath;
  });
  const responseFilePath = uniquePath(outputBase, `${topic}.json`);
  fs.writeFileSync(responseFilePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
  return {
    type: 'workbuddy_file_manifest',
    version: '3.0-expert-wrapper',
    stdoutMode: 'file_manifest',
    responseFilePath,
    markdownFilePath,
    markdownFileName: path.basename(markdownFilePath),
    markdownChunkFiles,
    markdownChunkCount: markdownChunkFiles.length,
    markdownBytes: Buffer.byteLength(payload.markdown, 'utf8'),
    htmlFilePath: payload.htmlFilePath || '',
    htmlFileName: payload.htmlFileName || '',
    presentFilesInstruction: payload.presentFilesInstruction || '',
    responsePolicy: {
      ...(payload.responsePolicy || {}),
      finalAnswerField: 'markdownChunkFiles',
      fullResponseFinalAnswerField: 'markdown'
    },
    stats: payload.stats || {},
    ...(payload.resourceDisplay ? { resourceDisplay: payload.resourceDisplay } : {}),
    fallbackReason: payload.fallbackReason || ''
  };
}

function writeEvidenceFiles(markdownFilePath, context) {
  const directory = path.dirname(markdownFilePath);
  const stem = path.basename(markdownFilePath, path.extname(markdownFilePath));
  const fullPath = uniquePath(directory, `${stem}.expert-evidence.json`);
  fs.writeFileSync(fullPath, `${JSON.stringify(context, null, 2)}\n`, 'utf8');
  const chunks = splitEvidence(context);
  const chunkFiles = chunks.length === 1 ? [fullPath] : chunks.map((chunk, index) => {
    const chunkPath = uniquePath(directory, `${stem}.expert-evidence.part-${String(index + 1).padStart(3, '0')}.json`);
    fs.writeFileSync(chunkPath, `${JSON.stringify(chunk, null, 2)}\n`, 'utf8');
    return chunkPath;
  });
  return { fullPath, chunkFiles };
}

function augmentManifest(inputManifest, env = process.env, cwd = process.cwd()) {
  const manifest = withArtifactDelivery(normalizeQueryManifest(inputManifest), env, cwd);
  if (!manifest || !manifest.markdownFilePath || !fs.existsSync(manifest.markdownFilePath)) return manifest;
  const original = fs.readFileSync(manifest.markdownFilePath, 'utf8');
  const evidence = extractEvidence(original);
  const files = writeEvidenceFiles(manifest.markdownFilePath, evidence);
  return {
    ...manifest,
    expertEvidenceFilePath: files.fullPath,
    expertEvidenceChunkFiles: files.chunkFiles,
    expertEvidenceChunkCount: files.chunkFiles.length,
    expertEvidenceInstruction: '并行读取全部 expertEvidenceChunkFiles。专家解读的价格、时间、位置、开放信息和缺口判断必须以这些证据为准；用户预算不能当作实际花费；不得修改或替代原始 Markdown。'
  };
}

async function run(argv = process.argv.slice(2)) {
  const { query, queryArgs, intent, responseMode } = parseArgs(argv);
  if (!query) throw new Error('缺少 --query-script <查询脚本路径>');
  const task = applyTrainDateDefault(query, prepareQuery(query, queryArgs, intent));
  const responseFlow = classifyResponseFlow(query, task, responseMode);
  const started = Date.now();
  const env = queryEnvironment(process.env);
  const authMs = Date.now() - started;
  if (!env) {
    process.stdout.write('TC_CHENGXIN_REAUTH_REQUIRED\n');
    return 1;
  }
  env.CHENGXIN_EXPERT_INTENT = task.intent;
  const context = resolveClientContext(env);
  const queryStarted = Date.now();
  const result = childProcess.spawnSync(process.execPath, [path.resolve(query), ...queryArguments(task.args, context)], {
    cwd: process.cwd(),
    env,
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024
  });
  const queryProcessMs = Date.now() - queryStarted;
  const stdout = result.stdout || '';
  const stderr = result.stderr || '';
  const manifest = parseManifest(stdout);
  // The shared query emits connector-specific error guidance on stderr. In the expert,
  // only translate this failure signal; never rewrite successful Markdown or artifacts.
  if (!manifest && `${stdout}\n${stderr}`.split(/\r?\n/).some(line => line.trim() === 'TC_CHENGXIN_REAUTH_REQUIRED')) {
    process.stdout.write('TC_CHENGXIN_REAUTH_REQUIRED\n');
    process.stdout.write('同程旅行授权已失效。调用 tc-chengxin-auth；手机/小程序/云端须在普通最终回复展示登录链接并结束本轮，用户确认后单次检查授权；成功后通过专家包装器只重试一次原查询。\n');
    return 1;
  }
  if (stderr) process.stderr.write(stderr);
  if (result.status !== 0 || !manifest) {
    process.stdout.write(stdout);
    return result.status || 0;
  }
  if (manifest.type !== 'workbuddy_expert_snapshot') {
    throw new Error('查询脚本不支持专家前置取数，请更新完整专家包；禁止直接展示未审定产物');
  }
  const pipeline = require('./expert-pipeline');
  const snapshots = pipeline.loadSnapshots([manifest.snapshotFilePath]);
  if (responseFlow.flow === 'direct_render' && pipeline.catalogue(snapshots).length) {
    const renderStarted = Date.now();
    const previousExpert = process.env.CHENGXIN_WORKBUDDY_EXPERT;
    process.env.CHENGXIN_WORKBUDDY_EXPERT = '1';
    let payload;
    try {
      payload = await pipeline.renderDirect([manifest.snapshotFilePath], { compactChat: true });
    } finally {
      if (previousExpert === undefined) delete process.env.CHENGXIN_WORKBUDDY_EXPERT;
      else process.env.CHENGXIN_WORKBUDDY_EXPERT = previousExpert;
    }
    payload.timings = { authMs, queryProcessMs, renderMs: Date.now() - renderStarted, totalMs: Date.now() - started };
    const delivery = require('./expert-delivery');
    const saved = delivery.saveDelivery(payload);
    const receipt = delivery.deliveryReceipt(saved, { inlineFinalAnswer: true });
    process.stdout.write(`${START_MARKER}\n${JSON.stringify({ ...receipt,
      snapshotId: manifest.snapshotId, snapshotFilePath: manifest.snapshotFilePath,
      responseFlow: responseFlow.flow, responseFlowReason: responseFlow.reason,
      ...(task.queryDefaults ? { queryDefaults: task.queryDefaults } : {}),
      timings: payload.timings }, null, 2)}\n${END_MARKER}\n`);
    return 0;
  }
  const evidenceStarted = Date.now();
  const augmented = pipeline.prepareEvidence(manifest);
  augmented.timings = { authMs, queryProcessMs, evidenceMs: Date.now() - evidenceStarted, totalMs: Date.now() - started };
  const receipt = require('./decision-evidence').inputReceipt(augmented);
  process.stdout.write(`${START_MARKER}\n${JSON.stringify({ ...receipt,
    ...(task.queryDefaults ? { queryDefaults: task.queryDefaults } : {}),
    responseFlow: responseFlow.flow, responseFlowReason: responseFlow.reason }, null, 2)}\n${END_MARKER}\n`);
  return 0;
}

if (require.main === module) {
  run().then(code => {
    process.exitCode = code;
  }).catch((error) => {
    console.error(`专家证据提取失败：${error.message}`);
    process.exitCode = 1;
  });
}

module.exports = {
  augmentManifest,
  cliInvocation,
  extractEvidence,
  parseArgs,
  parseManifest,
  normalizeQueryManifest,
  queryEnvironment,
  queryArguments,
  run,
  splitUtf8,
  splitEvidence,
  stripMarkdown,
  withArtifactDelivery,
  writeEvidenceFiles
};
