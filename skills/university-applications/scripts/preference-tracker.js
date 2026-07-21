#!/usr/bin/env node
/**
 * 用户偏好学习系统
 * 基于用户互动记录，动态调整关注领域权重
 *
 * 用法（供 Agent 调用）:
 *   node preference-tracker.js record <userId> <topic> [context]
 *   node preference-tracker.js weights <userId>
 *   node preference-tracker.js top <userId> [n]
 */

const fs = require('fs');
const path = require('path');

const PROFILES_DIR = path.join(__dirname, '../data/profiles');

// 支持的关注领域
// 注意：v1.1.8 起移除「官司」主题。法律相关问题不在本 skill 声明的覆盖范围内
// （SKILL.md 已声明不覆盖法律/医疗/金融等专业领域），
// 持久化追踪「官司」会构成超出声明范围的敏感画像，因此从可记录主题中下线。
// 历史档案中已存在的「官司」记录会在 _computeWeights/_normalizeWeights 中被自动忽略。
const TOPICS = ['财运', '事业', '感情', '健康', '婚姻', '子女', '出行', '风水'];

// 互动来源权重倍率
const CONTEXT_MULTIPLIERS = {
  explicit_query: 2.0,   // 用户主动提问
  topic_drill:    1.5,   // 用户追问同一话题
  morning_push:   0.8,   // 晨间推送被消费
  evening_push:   0.8,   // 晚间推送被消费
};

const DECAY_LAMBDA     = 0.05;  // 衰减系数，约14天半衰期
const MAX_LOG_SIZE     = 500;   // 最大记录条数
const MIN_WEIGHT       = 0.5;   // 进入 focusAreas 的最低权重
const DEFAULT_FOCUS    = ['事业', '财运', '健康'];

// ─────────────────────────────────────────────
// 文件 I/O
// ─────────────────────────────────────────────

function loadProfile(userId) {
  const fp = path.join(PROFILES_DIR, `${userId}.json`);
  if (!fs.existsSync(fp)) return null;
  return JSON.parse(fs.readFileSync(fp, 'utf8'));
}

function saveProfile(userId, profile) {
  const fp = path.join(PROFILES_DIR, `${userId}.json`);
  profile.updatedAt = new Date().toISOString().split('T')[0];
  fs.writeFileSync(fp, JSON.stringify(profile, null, 2), 'utf8');
}

// ─────────────────────────────────────────────
// 核心算法：指数衰减加权
// ─────────────────────────────────────────────

function _computeWeights(log) {
  const now = Date.now();
  const totals = {};
  TOPICS.forEach(t => { totals[t] = 0; });

  for (const entry of (log || [])) {
    if (!TOPICS.includes(entry.topic)) continue;
    if (!entry.ts || typeof entry.ts !== 'number') continue;
    const daysDelta = (now - entry.ts) / 86400000;
    const multiplier = CONTEXT_MULTIPLIERS[entry.context] || 1.0;
    totals[entry.topic] += multiplier * Math.exp(-DECAY_LAMBDA * daysDelta);
  }
  return totals;
}

function _normalizeWeights(raw) {
  const max = Math.max(...Object.values(raw), 0.001);
  const result = {};
  for (const [t, w] of Object.entries(raw)) {
    result[t] = parseFloat((w / max).toFixed(3));
  }
  return result;
}

function _sortedTopics(weights) {
  return Object.entries(weights)
    .sort((a, b) => b[1] - a[1])
    .map(([topic, weight]) => ({ topic, weight }));
}

// ─────────────────────────────────────────────
// 公开 API
// ─────────────────────────────────────────────

/**
 * 记录一次互动
 *
 * 隐私披露（v1.1.9 加强）：
 * - 本函数仅在用户在 profile.preferences 中显式 opt-in 后才会写入。
 *   必须同时满足：
 *     - profile.preferences.allowPreferenceLearning === true
 *     - profile.preferences.preferenceLearningOptInAt 为 ISO 时间戳
 *   如果任一条件不满足，本函数返回 false 且**不**写入任何 interactionLog。
 * - 调用方可以运行 CLI: `node preference-tracker.js opt-in <userId>` 来开启；
 *   并以 `node preference-tracker.js opt-out <userId>` 随时关闭且清空日志。
 * - 写入位置：data/profiles/<userId>.json 的 interactionLog 字段（**仅本地**，不上传）。
 * - 留存策略：滚动保留最近 MAX_LOG_SIZE 条，超出后**永久丢弃最旧记录**；
 *   也可以随时通过 `node scripts/profile.js delete <userId>` 整体清空，
 *   或手工编辑 JSON 中的 interactionLog 字段。
 * - 主题白名单：见 TOPICS。`官司` 等敏感法律主题已下线，不再被记录。
 * - 推送来源（context=morning_push/evening_push）的写入由 daily-push.js 串联，
 *   仅在用户已显式 opt-in 推送（preferences.pushOptInAt 存在）后才会发生。
 */
function recordInteraction(userId, topic, context = 'explicit_query') {
  const profile = loadProfile(userId);
  if (!profile) return false;
  if (!TOPICS.includes(topic)) return false;

  // 默认关闭：如果用户未显式 opt-in，本函数不进行任何写入
  // （这是实现层隔离，不是允许会话余颂静默采集。）
  const allowed = !!(profile.preferences
    && profile.preferences.allowPreferenceLearning === true
    && profile.preferences.preferenceLearningOptInAt);
  if (!allowed) return false;

  if (!profile.interactionLog) profile.interactionLog = [];

  profile.interactionLog.push({ ts: Date.now(), topic, context });

  // 超出上限时删除最旧的记录
  if (profile.interactionLog.length > MAX_LOG_SIZE) {
    profile.interactionLog = profile.interactionLog.slice(-MAX_LOG_SIZE);
  }

  // 重新计算并更新 focusAreas
  const raw = _computeWeights(profile.interactionLog);
  const normalized = _normalizeWeights(raw);
  const top = _sortedTopics(normalized)
    .filter(({ weight }) => weight >= MIN_WEIGHT)
    .slice(0, 3)
    .map(({ topic }) => topic);

  if (!profile.preferences) profile.preferences = {};
  profile.preferences.focusAreas = top.length > 0 ? top : DEFAULT_FOCUS;

  saveProfile(userId, profile);
  return true;
}

/**
 * 显式 opt-in 偏好学习
 */
function optInPreferenceLearning(userId) {
  const profile = loadProfile(userId);
  if (!profile) return false;
  if (!profile.preferences) profile.preferences = {};
  profile.preferences.allowPreferenceLearning = true;
  profile.preferences.preferenceLearningOptInAt = new Date().toISOString();
  saveProfile(userId, profile);
  return true;
}

/**
 * opt-out：关闭偏好学习并清空已有历史
 */
function optOutPreferenceLearning(userId) {
  const profile = loadProfile(userId);
  if (!profile) return false;
  if (!profile.preferences) profile.preferences = {};
  profile.preferences.allowPreferenceLearning = false;
  profile.preferences.preferenceLearningOptInAt = null;
  profile.interactionLog = [];
  profile.preferences.focusAreas = DEFAULT_FOCUS;
  saveProfile(userId, profile);
  return true;
}

/**
 * 获取所有领域权重（归一化，降序）
 */
function getWeights(userId) {
  const profile = loadProfile(userId);
  if (!profile) return [];
  const raw = _computeWeights(profile.interactionLog || []);
  const normalized = _normalizeWeights(raw);
  return _sortedTopics(normalized);
}

/**
 * 获取 top-n 关注领域（有互动记录用计算结果，否则用 profile 默认值）
 */
function getTopTopics(userId, n = 3) {
  const profile = loadProfile(userId);
  if (!profile) return DEFAULT_FOCUS.slice(0, n);

  const log = profile.interactionLog || [];
  if (log.length === 0) {
    return (profile.preferences?.focusAreas || DEFAULT_FOCUS).slice(0, n);
  }

  const raw = _computeWeights(log);
  const normalized = _normalizeWeights(raw);
  return _sortedTopics(normalized)
    .slice(0, n)
    .map(({ topic }) => topic);
}

module.exports = { recordInteraction, getWeights, getTopTopics, optInPreferenceLearning, optOutPreferenceLearning, TOPICS };

// ─────────────────────────────────────────────
// 命令行入口（供 Agent 调用）
// ─────────────────────────────────────────────

if (require.main === module) {
  const [cmd, userId, ...rest] = process.argv.slice(2);

  if (!cmd || !userId) {
    console.log(`
🧠 用户偏好追踪器

用法:
  node preference-tracker.js opt-in  <userId>          # 启用偏好学习（需本人同意）
  node preference-tracker.js opt-out <userId>          # 关闭偏好学习并清空互动日志
  node preference-tracker.js record  <userId> <topic> [context]
  node preference-tracker.js weights <userId>
  node preference-tracker.js top     <userId> [n]

说明:
  - record 仅在 profile.preferences.allowPreferenceLearning === true 且记录了 opt-in 时间戳后才会写入。
  - opt-out 后，interactionLog 会被一次性清空，focusAreas 回退到默认值。

topic 可选: ${TOPICS.join(' | ')}
context 可选: explicit_query | topic_drill | morning_push | evening_push

示例:
  node preference-tracker.js opt-in 123456
  node preference-tracker.js record 123456 财运 explicit_query
  node preference-tracker.js opt-out 123456
`);
    process.exit(1);
  }

  switch (cmd) {
    case 'opt-in': {
      const ok = optInPreferenceLearning(userId);
      if (ok) {
        console.log(JSON.stringify({ success: true, userId, allowPreferenceLearning: true, action: 'opt-in' }));
      } else {
        console.error(`❌ 用户不存在或未初始化: ${userId}`);
        process.exit(1);
      }
      break;
    }
    case 'opt-out': {
      const ok = optOutPreferenceLearning(userId);
      if (ok) {
        console.log(JSON.stringify({ success: true, userId, allowPreferenceLearning: false, action: 'opt-out', interactionLogCleared: true }));
      } else {
        console.error(`❌ 用户不存在: ${userId}`);
        process.exit(1);
      }
      break;
    }
    case 'record': {
      const [topic, context = 'explicit_query'] = rest;
      if (!topic) { console.error('缺少 topic 参数'); process.exit(1); }
      const ok = recordInteraction(userId, topic, context);
      if (!ok) {
        // 给出明确提示，避免调用方静默以为写入成功
        console.log(JSON.stringify({ success: false, userId, topic, context, reason: 'profile-missing-or-not-opted-in' }));
      } else {
        console.log(JSON.stringify({ success: true, userId, topic, context }));
      }
      break;
    }
    case 'weights': {
      const weights = getWeights(userId);
      console.log(JSON.stringify({ userId, weights }));
      break;
    }
    case 'top': {
      const n = parseInt(rest[0] || '3');
      const topics = getTopTopics(userId, n);
      console.log(JSON.stringify({ userId, topTopics: topics }));
      break;
    }
    default:
      console.error(`未知命令: ${cmd}`);
      process.exit(1);
  }
}
