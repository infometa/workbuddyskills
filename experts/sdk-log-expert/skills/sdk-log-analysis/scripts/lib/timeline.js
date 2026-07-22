import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

import { getTplPlugins } from './tpl-func.js';
import { extractLiteral, optimizeRegex, reg2keywords } from './reg-prefilter.js';
import { safeCodeBlock, safeEvidenceLine, safeMarkdownTableCell } from './safe-output.js';
import AhoCorasick from './aho-corasick.js';

const require = createRequire(import.meta.url);
const _artTemplate = require('../../vendor/art-template/lib/template-web.js');
const artTemplate = _artTemplate && _artTemplate.default ? _artTemplate.default : _artTemplate;

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_API_DIR = path.resolve(__dirname, '..', '..', 'data', 'api');
const LEVEL_MAP = { I: 'info', W: 'warn', E: 'error', F: 'error', D: 'normal' };
const TPL_TAG_PATTERN = /\[(\/)?(cost|strong|label|text|weak|primary|danger|warning|success)\]/g;
const SDK_BY_LOG_TYPE = {
  trtc: '实时音视频TRTC',
  im: '即时通信IM',
  tui: 'RTCRoomEngine',
  web: '实时音视频TRTC',
  kibana_native: '实时音视频TRTC',
  kibana_web: '实时音视频TRTC',
};
const TUI_HINT_RE = /Tuikit|TUIRoom|TUILive|TUICall|RTCRoom|RoomEngine|LiveKit|RoomKit|CallKit|Seat|麦位/i;
const WEB_LINE_RE = /^\[\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?\]\[[^\]]*\]\s*<(?:TRACE|DEBUG|INFO|WARN|ERROR|FATAL)>/i;

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function flattenApiList(raw, setKey, listKey, mapItem) {
  return (raw || []).flatMap(sdkSet => (sdkSet[setKey] || sdkSet[listKey] || []).map(item => mapItem(item, sdkSet)));
}

export function loadApiData(apiDir = DEFAULT_API_DIR) {
  const logRuleRaw = readJson(path.join(apiDir, 'log-rule.json'));
  const timelineRaw = readJson(path.join(apiDir, 'timeline.json'));
  const errorCodeRaw = readJson(path.join(apiDir, 'error-code.json'));

  const logRules = flattenApiList(logRuleRaw, 'LogRuleList', 'LogRuleList', (item, sdkSet) => ({
    id: item.Id,
    sdk: sdkSet.SdkName,
    ruleDesc: item.RuleDesc || '',
    level: item.RuleLevel || 'normal',
    rules: (item.RuleRegList || []).map(regRule => ({
      reg: regRule.Reg || '',
      desc: regRule.RegDesc || '',
      test: regRule.RegTestLog || '',
    })),
  }));

  const timelines = flattenApiList(timelineRaw, 'TimelineList', 'TimelineList', (item, sdkSet) => ({
    id: item.Id,
    name: item.Name,
    sdk: sdkSet.SdkName,
    ruleIds: item.LogRuleList || [],
  }));

  const errorCodes = flattenApiList(errorCodeRaw, 'ErrorCodeList', 'ErrorCodeList', (item, sdkSet) => ({
    sdk: sdkSet.SdkName,
    code: String(item.ErrorCode ?? ''),
    msg: String(item.ErrorMessage ?? ''),
    desc: [item.ErrorMessage, item.Description, item.Solution].filter(Boolean).join('；'),
  }));

  const sdkNames = [...new Set([
    ...logRuleRaw.map(item => item.SdkName).filter(Boolean),
    ...timelineRaw.map(item => item.SdkName).filter(Boolean),
    ...errorCodeRaw.map(item => item.SdkName).filter(Boolean),
  ])];

  return { logRules, timelines, errorCodes, sdkNames };
}

function removeTplTags(input) {
  return String(input || '').replace(TPL_TAG_PATTERN, '');
}

function renderTemplate(source, data, errorCodes, { keepTags = false } = {}) {
  if (!source) return '';
  try {
    const rendered = artTemplate.render(source, data, {
      bail: false,
      imports: getTplPlugins(errorCodes),
    }).replace(/&#\d+;/g, '');
    // keepTags=true 时保留 [danger]..[/danger] 等配色 tag 给前端渲染彩色文本；
    // CLI/markdown 路径默认剥离 tag。
    return (keepTags ? rendered : removeTplTags(rendered)).trim();
  } catch (error) {
    return `模版compile出错, ${error.message}`;
  }
}

// 端原生日志时间戳带 UTC 偏移，如 +8.0 / +5.5 / +05:50。
// 兼容约定（与浏览器端 SDK 日志解析实现一致）：
//   +5.5  => 5 小时 30 分钟（小数视为分钟的百分比 * 60）
//   +05:50 => 5 小时 50 分钟（冒号分隔视为分钟 * 100）
// 返回相对 UTC 的偏移分钟数；解析失败返回 null。
function parseNativeOffsetMinutes(offsetStr) {
  const isColonUTC = offsetStr.indexOf('.') === -1;
  const arr = offsetStr.split(/[.:]/);
  const hour = parseInt(arr[0], 10);
  const minute = parseFloat(`0.${arr[1] ?? '0'}`);
  if (Number.isNaN(hour) || Number.isNaN(minute)) return null;
  const offsetMinute = Math.floor(isColonUTC ? minute * 100 : minute * 60);
  return hour * 60 + (hour > 0 ? 1 : -1) * offsetMinute;
}

// 端原生时间戳无年份，使用当前年份作为参考，结合偏移构造 epoch ms。
function parseNativeEpochMs({ month, day, hh, mm, ss, ms, offset }) {
  const offsetMin = offset ? parseNativeOffsetMinutes(offset) : 480; // 默认 UTC+8
  if (offsetMin == null) return null;
  const msNum = ms ? Number(String(ms).padEnd(3, '0').slice(0, 3)) : 0;
  const base = Date.UTC(new Date().getFullYear(), Number(month) - 1, Number(day), Number(hh), Number(mm), Number(ss), msNum);
  if (Number.isNaN(base)) return null;
  return base - offsetMin * 60000;
}

function parseTime(text) {
  let m = text.match(/^TIM:\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})(?:\.\d+)?\s+([IWEFD])?/);
  if (m) return { type: 'im', level: LEVEL_MAP[m[3]] || 'normal', timeText: `${m[1]} ${m[2]}`, timestamp: Date.parse(`${m[1]}T${m[2]}`) || null };

  m = text.match(/^\[(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:\.\d+)?\]/);
  if (m) return { type: 'web', timeText: `${m[1]} ${m[2]}`, timestamp: Date.parse(`${m[1]}T${m[2]}`) || null };

  m = text.match(/^\[([IWEFD])\]\[(\d{2})-(\d{2})\/((\d{2}):(\d{2}):(\d{2}))(?:\.(\d+))?([+-]\d+(?:[.:]\d+)?)?\]/);
  if (m) {
    const timestamp = parseNativeEpochMs({ month: m[2], day: m[3], hh: m[5], mm: m[6], ss: m[7], ms: m[8], offset: m[9] });
    return { type: 'native', level: LEVEL_MAP[m[1]] || m[1], timeText: `${m[2]}-${m[3]} ${m[4]}`, timestamp: typeof timestamp === 'number' ? timestamp : null };
  }

  m = text.match(/(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:\.\d+)?/);
  if (m) return { type: 'unknown', timeText: `${m[1]} ${m[2]}`, timestamp: Date.parse(`${m[1]}T${m[2]}`) || null };

  m = text.match(/(\d{2})-(\d{2})[ /](\d{2}:\d{2}:\d{2})(?:\.\d+)?/);
  if (m) return { type: 'unknown', timeText: `${m[1]}-${m[2]} ${m[3]}`, timestamp: null };

  return { type: 'unknown', timeText: '', timestamp: null };
}

function parseLevel(text, fallback) {
  if (fallback) return fallback;
  const im = text.match(/^TIM:\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\s+([IWEFD])/);
  if (im) return LEVEL_MAP[im[1]] || 'normal';
  const web = text.match(/<(TRACE|DEBUG|INFO|WARN|ERROR|FATAL)>/i);
  if (web) return web[1].toLowerCase() === 'fatal' ? 'error' : web[1].toLowerCase();
  const native = text.match(/^\[([IWEFD])\]/);
  if (native) return LEVEL_MAP[native[1]] || native[1];
  return 'normal';
}

function parseUserId(text) {
  const web = text.match(/\[[↑↓][^\]|]*\|([^\]]+)\]/u);
  if (web) return web[1];
  const explicit = text.match(/(?:userID|userId|userid|user_id|str_userid)[:= ]+['\"]?([^,\]| }'\"]+)/i);
  return explicit ? explicit[1] : '';
}

export function parseLogLine(line, index = 0) {
  const raw = typeof line === 'string' ? line : JSON.stringify(line);
  const time = parseTime(raw);
  return {
    index,
    type: time.type,
    timeText: time.timeText,
    timestamp: time.timestamp,
    level: parseLevel(raw, time.level),
    userId: parseUserId(raw),
    text: raw.trim(),
  };
}

function toLineItems(lines) {
  return lines
    .map((line, index) => ({
      text: typeof line === 'string' ? line : JSON.stringify(line),
      line: index + 1,
      endLine: index + 1,
    }))
    .filter(item => item.text.trim());
}

export function detectLogType(lines, { fileNames = [] } = {}) {
  if (fileNames.some(name => String(name).toLowerCase().includes('imsdk_'))) {
    return { logType: 'im', reason: 'filename:imsdk_' };
  }

  let detected = 'unknown';
  const scanLines = lines.slice(0, 2000);
  for (const line of scanLines) {
    const text = typeof line === 'string' ? line : JSON.stringify(line);
    if (TUI_HINT_RE.test(text)) return { logType: 'tui', reason: 'tui-keyword' };
    if (WEB_LINE_RE.test(text)) return { logType: 'web', reason: 'web-bracket-level' };
    if (text.startsWith('TIM:')) detected = detected === 'unknown' ? 'im' : detected;
    else if (/^\[[IEW]\]\[\d.*/.test(text) && detected === 'unknown') detected = 'trtc';
  }
  return { logType: detected === 'unknown' ? 'trtc' : detected, reason: detected === 'unknown' ? 'default:trtc' : 'content' };
}

export function groupLogEntries(lines, logType) {
  const items = toLineItems(lines);
  if (!['im', 'trtc', 'tui', 'kibana_native'].includes(logType)) return items;

  const isStart = logType === 'im'
    ? item => item.text.startsWith('TIM:')
    : item => item.text.startsWith('[');

  const result = [];
  let current = null;
  for (const item of items) {
    if (isStart(item) || current == null) {
      if (current) result.push(current);
      current = { ...item };
    } else {
      current.text += `\n${item.text}`;
      current.endLine = item.endLine;
    }
  }
  if (current) result.push(current);
  return result;
}

function resolveSdk(apiData, { sdk, logType }) {
  if (sdk) return sdk;
  const mapped = SDK_BY_LOG_TYPE[logType];
  if (mapped && apiData.sdkNames.includes(mapped)) return mapped;
  if (logType === 'tui' && apiData.sdkNames.includes(SDK_BY_LOG_TYPE.trtc)) return SDK_BY_LOG_TYPE.trtc;
  if (apiData.sdkNames.length === 1) return apiData.sdkNames[0];
  return mapped || '';
}

function selectRules(apiData, { sdk, logType } = {}) {
  const resolvedSdk = resolveSdk(apiData, { sdk, logType });
  const timelineRuleIds = new Set(
    apiData.timelines
      .filter(item => !resolvedSdk || item.sdk === resolvedSdk)
      .flatMap(item => item.ruleIds || [])
  );
  const rulesInTimeline = apiData.logRules.filter(rule => {
    if (resolvedSdk && rule.sdk !== resolvedSdk) return false;
    return timelineRuleIds.has(rule.id);
  });
  const rules = rulesInTimeline.length > 0
    ? rulesInTimeline
    : apiData.logRules.filter(rule => !resolvedSdk || rule.sdk === resolvedSdk);
  return { rules, sdk: resolvedSdk };
}

// 检测正则是否含「顶层 alternation」(深度 0 的未转义 `|`，且不在字符集 [...] 内)。
// 顶层 alternation 意味着不同分支可走不同路径，reg2keywords / extractLiteral
// 推导出的字面 token 不再是「必现子串」，用它做预过滤会漏匹配 → 该 reg 的 gate 不可信。
function hasTopLevelAlternation(reg) {
  let depth = 0;
  let inClass = false;
  for (let i = 0; i < reg.length; i++) {
    const ch = reg[i];
    if (ch === '\\') { i++; continue; } // 跳过转义字符
    if (inClass) {
      if (ch === ']') inClass = false;
      continue;
    }
    if (ch === '[') { inClass = true; continue; }
    if (ch === '(') { depth++; continue; }
    if (ch === ')') { if (depth > 0) depth--; continue; }
    if (ch === '|' && depth === 0) return true;
  }
  return false;
}

// 为单个 reg 派生预过滤信息。
// - re:       优化后的编译正则（去掉无意义的 .* 前后缀，走 V8 快速路径）
// - literal:  最长必现字面量（用于 indexOf 跳过）；含顶层 alternation 时不可信，置 null
// - keywords: 派生关键字（长度 ≥ 2，小写）
// - reliable: 该 reg 的关键字是否可作为「必现」gate（无顶层 alternation 且至少有一个关键字）
function buildRegMeta(regRule) {
  const reg = regRule.reg;
  const altUnsafe = hasTopLevelAlternation(reg);
  const keywords = reg2keywords(reg).filter(kw => kw.length >= 2);
  const literal = altUnsafe ? null : extractLiteral(reg);
  return {
    regRule,
    re: new RegExp(optimizeRegex(reg), 'im'),
    literal,
    keywords,
    reliable: !altUnsafe && keywords.length > 0,
  };
}

function compileRules(rules) {
  return rules.map(rule => ({
    rule,
    rules: rule.rules.flatMap(regRule => {
      if (!regRule.reg) return [];
      try {
        return [buildRegMeta(regRule)];
      } catch {
        return [];
      }
    }),
  })).filter(item => item.rules.length > 0)
    // 一个规则可被 AC gate 当且仅当它的每个 reg 的关键字都「可信」(reliable)。
    // 只要有一个 reg 不可信（顶层 alternation / 无关键字），整条规则归为 always-test，
    // 即每行都测试 —— 偏向正确性，宁可慢也不漏匹配。
    .map(item => ({
      ...item,
      acGated: item.rules.every(reg => reg.reliable),
    }));
}

// 基于编译后的规则构建 Aho-Corasick 预过滤索引。
// 返回：
// - ac:               所有「可 AC gate」规则关键字构成的 AC 自动机（无关键字时为 null）
// - kwToRuleIndices:  关键字 → 命中的规则下标集合
// - alwaysTestIndices: 不可安全 gate、必须每行测试的规则下标
function buildPrefilter(compiledRules) {
  const kwToRuleIndices = new Map();
  const alwaysTestIndices = [];

  compiledRules.forEach((compiledRule, ruleIdx) => {
    if (!compiledRule.acGated) {
      alwaysTestIndices.push(ruleIdx);
      return;
    }
    for (const reg of compiledRule.rules) {
      for (const kw of reg.keywords) {
        let indices = kwToRuleIndices.get(kw);
        if (!indices) {
          indices = new Set();
          kwToRuleIndices.set(kw, indices);
        }
        indices.add(ruleIdx);
      }
    }
  });

  let ac = null;
  if (kwToRuleIndices.size > 0) {
    ac = new AhoCorasick();
    for (const kw of kwToRuleIndices.keys()) ac.addPattern(kw);
    ac.buildFailPointers();
  }

  return { ac, kwToRuleIndices, alwaysTestIndices };
}

function selectErrorCodes(apiData, sdk, logType) {
  const sdkSet = new Set(logType === 'tui'
    ? [SDK_BY_LOG_TYPE.tui, SDK_BY_LOG_TYPE.trtc, SDK_BY_LOG_TYPE.im]
    : [sdk]);
  const filtered = apiData.errorCodes.filter(item => sdkSet.has(item.sdk));
  return filtered.length > 0 ? filtered : apiData.errorCodes;
}

export function summarizeEvents(events) {
  const sorted = [...events].sort((a, b) => {
    if (a.timestamp && b.timestamp && a.timestamp !== b.timestamp) return a.timestamp - b.timestamp;
    return a.line - b.line;
  });
  const summary = { total: sorted.length, byRule: {}, byLevel: {} };
  for (const event of sorted) {
    summary.byRule[event.ruleId] = (summary.byRule[event.ruleId] || 0) + 1;
    summary.byLevel[event.level] = (summary.byLevel[event.level] || 0) + 1;
  }
  return { events: sorted, summary };
}

export function buildTimelineFromEntries(entries, options = {}) {
  const apiData = options.apiData || loadApiData(options.apiDir || DEFAULT_API_DIR);
  const logType = options.logType;
  const { rules, sdk } = selectRules(apiData, { ...options, logType });
  const errorCodes = selectErrorCodes(apiData, sdk, logType);
  const compiledRules = compileRules(rules);
  const { ac, kwToRuleIndices, alwaysTestIndices } = buildPrefilter(compiledRules);
  const events = [];

  for (const item of entries) {
    const lowerText = item.text.toLowerCase();

    // 计算候选规则下标：always-test 规则 ∪ AC 命中关键字对应的规则。
    // ac 为 null 表示没有任何可 gate 的规则，此时所有规则都在 alwaysTestIndices 里。
    let candidateRuleIndices = null;
    // options.__noPrefilter 仅用于等价性验证：强制所有规则为候选（等同朴素匹配）。
    if (ac && !options.__noPrefilter) {
      candidateRuleIndices = new Set(alwaysTestIndices);
      const matchedKws = ac.search(lowerText);
      for (const kw of matchedKws) {
        const indices = kwToRuleIndices.get(kw);
        if (indices) for (const idx of indices) candidateRuleIndices.add(idx);
      }
    }

    let matched = false;
    // 始终按原始下标顺序遍历，跳过非候选规则 —— 保持 first-match 的胜出规则不变。
    for (let ruleIdx = 0; ruleIdx < compiledRules.length; ruleIdx++) {
      if (candidateRuleIndices && !candidateRuleIndices.has(ruleIdx)) continue;
      const compiledRule = compiledRules[ruleIdx];
      for (const compiledReg of compiledRule.rules) {
        // literal indexOf 快速过滤：仅当 literal 非空时才可安全跳过。
        if (compiledReg.literal && lowerText.indexOf(compiledReg.literal) === -1) continue;
        const ret = compiledReg.re.exec(item.text);
        if (!ret) continue;
        const groups = ret.groups || {};
        const parsed = parseLogLine(item.text, item.line);
        const desc = renderTemplate(compiledReg.regRule.desc, { ...groups, __log: item.text }, errorCodes, { keepTags: options.keepTags });
        events.push({
          ...parsed,
          sdk: compiledRule.rule.sdk,
          line: item.line,
          endLine: item.endLine,
          ruleId: compiledRule.rule.id,
          ruleDesc: compiledRule.rule.ruleDesc,
          ruleLevel: compiledRule.rule.level,
          level: parsed.level === 'normal' ? compiledRule.rule.level : parsed.level,
          desc,
          log: item.text,
        });
        matched = true;
        break;
      }
      if (matched && !options.loopAllRule) break;
    }
  }
  return { sdk, logType, events };
}

export function buildTimeline(lines, options = {}) {
  const apiData = options.apiData || loadApiData(options.apiDir || DEFAULT_API_DIR);
  const detected = options.logType ? { logType: options.logType, reason: 'option' } : detectLogType(lines, { fileNames: options.fileNames || [] });
  const logType = detected.logType;
  const entries = groupLogEntries(lines, logType);
  const partial = buildTimelineFromEntries(entries, { ...options, apiData, logType });
  const { events, summary } = summarizeEvents(partial.events);
  return { sdk: partial.sdk, logType, detectReason: detected.reason, events, summary, timeline: null };
}

export function renderTimelineMarkdown(timeline) {
  const lines = ['# SDK 日志时间线', ''];
  if (timeline.sdk) lines.push(`- sdk: ${safeMarkdownTableCell(timeline.sdk, { maxChars: 120 })}`);
  if (timeline.logType) lines.push(`- logType: ${safeMarkdownTableCell(timeline.logType, { maxChars: 80 })}`);
  if (timeline.timeline) lines.push(`- timeline: ${safeMarkdownTableCell(timeline.timeline.name, { maxChars: 120 })}`);
  if (lines.at(-1) !== '') lines.push('');
  lines.push('## 摘要', '', '```json', JSON.stringify(timeline.summary, null, 2), '```', '', '## 关键事件', '');
  lines.push('| 时间 | 行号 | 级别 | 规则 | 说明 |');
  lines.push('|---|---:|---|---|---|');
  for (const e of timeline.events) {
    const desc = safeMarkdownTableCell(e.desc || '', { maxChars: 280 });
    const rule = safeMarkdownTableCell(e.ruleDesc || e.ruleId || '', { maxChars: 160 });
    const time = safeMarkdownTableCell(e.timeText || '', { maxChars: 80 });
    const level = safeMarkdownTableCell(e.level || '', { maxChars: 40 });
    lines.push(`| ${time} | L${e.line || e.index || ''} | ${level} | ${rule} | ${desc} |`);
  }

  if (timeline.events.length > 0) {
    const evidence = timeline.events
      .map(e => safeEvidenceLine(e.line || e.index || '', e.log || e.text || '', { maxChars: 500 }))
      .join('\n');
    lines.push('', '## 证据片段（已脱敏/截断）', '', safeCodeBlock(evidence, 'text'));
  }

  return `${lines.join('\n')}\n`;
}
