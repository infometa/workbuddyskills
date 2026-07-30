#!/usr/bin/env node
/**
 * 每日运势推送开关
 * 开启时自动创建用户专属 cron job，关闭时删除
 *
 * 用法:
 *   node push-toggle.js on <userId>                开启推送（默认早8点+晚8点）
 *   node push-toggle.js off <userId>               关闭推送（删除 cron）
 *   node push-toggle.js status <userId>            查看状态
 *   node push-toggle.js on <userId> --morning 08:00 --evening 20:00
 */

const fs = require('fs');
const path = require('path');
const { getTopTopics } = require('./preference-tracker');

const PROFILES_DIR = path.join(__dirname, '../data/profiles');

// 各领域深度分析模板
const TOPIC_EXPANDED = {
  '财运': `💰 财运深析（重点关注）：
   - 今日财星状态与格局分析
   - 投资/支出/收款建议
   - 结合今日金融/市场新闻的财运影响与风险`,
  '事业': `💼 事业深析（重点关注）：
   - 今日官禄宫能量与事业星状态
   - 职场关键决策与行动建议
   - 结合今日政策/商业新闻的机遇与风险`,
  '感情': `💕 感情深析（重点关注）：
   - 今日桃花星与夫妻宫状态
   - 感情互动与表达建议
   - 今日社会/情感类新闻的命理启示`,
  '健康': `🏥 健康深析（重点关注）：
   - 今日五行对应脏腑的能量状态
   - 饮食、作息、运动建议
   - 结合今日天气/环境/公共卫生新闻`,
  '婚姻': `💍 婚姻深析（重点关注）：
   - 今日夫妻宫能量与刑冲状态
   - 婚姻经营与沟通建议
   - 今日家庭/社会新闻的婚姻启示`,
  '子女': `👶 子女深析（重点关注）：
   - 今日子女宫状态
   - 亲子关系与教育建议`,
  '官司': `⚖️ 官司/是非深析（重点关注）：
   - 今日官星与白虎星分析
   - 法律/合同/是非风险提示
   - 结合今日司法/社会冲突新闻`,
  '出行': `✈️ 出行深析（重点关注）：
   - 今日驿马星与方位吉凶
   - 出行时机、方向与交通建议
   - 结合今日天气/灾害/交通新闻`,
  '风水': `🏠 风水深析（重点关注）：
   - 今日飞星方位吉凶
   - 家居/办公能量调整建议`,
};

// 新闻到命理领域映射规则（嵌入 prompt，供 Agent 识别）
const NEWS_FORTUNE_MAPPING = `新闻与命理映射规则（识别今日新闻后按此对应）：
  - 市场波动/股债汇变动/降息加息 → 财运风险或机遇信号
  - 政策出台/经济刺激/行业利好 → 事业机遇信号
  - 监管收紧/行业整顿/合规要求 → 事业风险，行事低调
  - 自然灾害/台风暴雪/恶劣天气 → 出行风险 + 健康警示
  - 公共卫生/食品安全/空气质量 → 健康领域警示
  - 社会冲突/司法/法律法规变动 → 官司/是非风险
  - 科技突破/国际贸易/地缘政治 → 事业/财运双向影响分析`;

function loadProfile(userId) {
  const filePath = path.join(PROFILES_DIR, `${userId}.json`);
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function saveProfile(userId, profile) {
  const filePath = path.join(PROFILES_DIR, `${userId}.json`);
  profile.updatedAt = new Date().toISOString().split('T')[0];
  fs.writeFileSync(filePath, JSON.stringify(profile, null, 2), 'utf8');
}

/**
 * 创建用户专属 cron job
 * 返回 cron job id，失败返回 null
 */
function createCronJob(userId, name, cronExpr, message, channel) {
  const sessionKey = `agent:main:${channel}:direct:${userId}`;
  const args = [
    'cron', 'add',
    '--name', name,
    '--cron', cronExpr,
    '--tz', 'Asia/Shanghai',
    '--session', 'isolated',
    '--session-key', sessionKey,
    '--channel', channel,
    '--to', userId,
    '--announce',
    '--timeout-seconds', '120',
    '--message', message,
    '--json'
  ];

  try {
    // openclaw cron 由运行时管理，输出配置供运行时处理
    const cronConfig = { name, cronExpr, tz: 'Asia/Shanghai', session: 'isolated', sessionKey, channel, to: userId, announce: true, timeoutSeconds: 120, message };
    console.log(`__OPENCLAW_CRON_ADD__:${JSON.stringify(cronConfig)}`);
    return `cron:${name}:${userId}`;
  } catch (e) {
    console.error('创建 cron 失败:', e.message);
    return null;
  }
}

/**
 * 删除 cron job
 */
function removeCronJob(cronId) {
  try {
    console.log(`__OPENCLAW_CRON_RM__:${cronId}`);
    return true;
  } catch (e) {
    console.error(`删除 cron ${cronId} 失败:`, e.message);
    return false;
  }
}

/**
 * 构建早晨推送 prompt（今日运程）— 含偏好权重 + 新闻整合
 */
function buildMorningMessage(profile, topTopics) {
  const bazi = profile.bazi || {};
  const baziStr = `${bazi.year} ${bazi.month} ${bazi.day} ${bazi.hour}`;
  const name = profile.name || '用户';
  const userId = profile.userId;
  const top1 = topTopics[0] || '事业';
  const top2 = topTopics[1] || '财运';
  const top3 = topTopics[2] || '健康';
  const expandedSection = TOPIC_EXPANDED[top1] || '';

  return `请为${name}生成今日命理运程报告。
用户八字：${baziStr}，日主：${bazi.dayStem}
用户重点关注（按偏好排序）：${top1} > ${top2} > ${top3}

步骤：
1) 运行 node scripts/daily-fortune.js 获取今日干支基础运程
2) 搜索今日重要新闻（财经、政策、社会、国际各一条）
   ${NEWS_FORTUNE_MAPPING}
3) 结合八字与新闻做个性化分析，重点展开【${top1}】领域深度分析
4) 完成后运行：node scripts/preference-tracker.js record ${userId} ${top1} morning_push

输出格式：
🌅 【私人命理顾问】今日完整日期（含星期）

📊 今日综合指数
   事业：★★★★☆  财运：★★★☆☆  感情：★★★☆☆  健康：★★★★☆

🎨 幸运色：xxx（结合今日干支五行）

${expandedSection}

💼 今日宜忌
   ✅ 宜：xxx、xxx、xxx
   ❌ 忌：xxx、xxx

⚠️ 风险提示（结合命理+今日新闻背景，如无则省略）

📰 命理与时事（1-2句：将今日1条重要新闻与运势联系）

⏰ 今日三吉时：时辰（时间段）宜做xxx

💡 今日一句（命理格言或人生启示）`;
}

/**
 * 构建晚间推送 prompt（明日预告）— 含偏好权重 + 新闻整合
 */
function buildEveningMessage(profile, topTopics) {
  const bazi = profile.bazi || {};
  const baziStr = `${bazi.year} ${bazi.month} ${bazi.day} ${bazi.hour}`;
  const name = profile.name || '用户';
  const userId = profile.userId;
  const top1 = topTopics[0] || '事业';
  const top2 = topTopics[1] || '财运';
  const expandedSection = TOPIC_EXPANDED[top1] || '';

  return `请为${name}生成明日命理预告（今晚提前推送明日运势）。
用户八字：${baziStr}，日主：${bazi.dayStem}
用户重点关注（按偏好排序）：${top1} > ${top2}

步骤：
1) 运行 node scripts/daily-fortune.js 获取明日（今日+1天）干支运程
2) 搜索今日晚间重要新闻，预判对明日的影响
   ${NEWS_FORTUNE_MAPPING}
3) 重点展开【${top1}】明日深度预告
4) 完成后运行：node scripts/preference-tracker.js record ${userId} ${top1} evening_push

输出格式：
🌙 【明日预告】明日完整日期（含星期）

📊 明日综合指数
   事业：★★★★☆  财运：★★★☆☆  感情：★★★☆☆  健康：★★★★☆

🎨 明日幸运色：xxx

${expandedSection.replace('今日', '明日')}

💼 明日宜忌
   ✅ 宜：xxx、xxx
   ❌ 忌：xxx、xxx

⚠️ 明日风险预警（结合命理+今晚新闻动向，如无则省略）

📰 时事预判（今晚新闻对明日命理的影响，1句）

⏰ 明日三吉时

💡 今晚一句`;
}

// ─────────────────────────────────────────────

function enablePush(userId, options = {}) {
  const profile = loadProfile(userId);
  if (!profile) {
    console.log(`❌ 用户档案不存在: ${userId}，请先注册`);
    return false;
  }

  const morningTime = options.morning || '08:00';
  const eveningTime = options.evening || '20:00';
  const channel = options.channel || (profile.preferences?.channels?.[0]) || 'openclaw';

  const [mHour, mMin] = morningTime.split(':');
  const [eHour, eMin] = eveningTime.split(':');
  const morningCron = `${mMin} ${mHour} * * *`;
  const eveningCron = `${eMin} ${eHour} * * *`;

  console.log(`\n⏳ 正在为 ${profile.name}(${userId}) 创建推送计划...\n`);

  // 读取用户偏好权重
  const topTopics = getTopTopics(userId, 3);
  console.log(`  关注领域：${topTopics.join(' > ')}`);

  // 如果已有 cron，先删除旧的
  const existing = profile.push?.cronIds || {};
  if (existing.morning) { removeCronJob(existing.morning); }
  if (existing.evening) { removeCronJob(existing.evening); }

  // 创建早晨 cron
  const morningId = createCronJob(
    userId,
    `yunshi-morning-${userId}`,
    morningCron,
    buildMorningMessage(profile, topTopics),
    channel
  );

  // 创建晚间 cron
  const eveningId = createCronJob(
    userId,
    `yunshi-evening-${userId}`,
    eveningCron,
    buildEveningMessage(profile, topTopics),
    channel
  );

  // 保存到档案
  if (!profile.preferences) profile.preferences = {};
  profile.preferences.pushEnabled = true;
  profile.preferences.pushMorning = true;
  profile.preferences.pushEvening = true;
  profile.preferences.morningTime = morningTime;
  profile.preferences.eveningTime = eveningTime;
  profile.preferences.channels = [channel];
  profile.push = {
    cronIds: {
      morning: morningId,
      evening: eveningId
    },
    createdAt: new Date().toISOString()
  };

  saveProfile(userId, profile);

  console.log(`✅ 推送已开启！\n`);
  console.log(`  用户: ${profile.name} (${userId})`);
  console.log(`  渠道: ${channel}`);
  console.log(`  🌅 早晨运程: 每天 ${morningTime}  ${morningId ? `(id: ${morningId})` : '⚠️ 创建失败'}`);
  console.log(`  🌙 晚间预告: 每天 ${eveningTime}  ${eveningId ? `(id: ${eveningId})` : '⚠️ 创建失败'}`);
  console.log('');
  return true;
}

function disablePush(userId) {
  const profile = loadProfile(userId);
  if (!profile) {
    console.log(`❌ 用户档案不存在: ${userId}`);
    return false;
  }

  // 删除 cron job
  const cronIds = profile.push?.cronIds || {};
  let removed = 0;
  if (cronIds.morning) { if (removeCronJob(cronIds.morning)) removed++; }
  if (cronIds.evening) { if (removeCronJob(cronIds.evening)) removed++; }

  if (!profile.preferences) profile.preferences = {};
  profile.preferences.pushEnabled = false;
  profile.preferences.pushMorning = false;
  profile.preferences.pushEvening = false;
  profile.push = { cronIds: {}, disabledAt: new Date().toISOString() };

  saveProfile(userId, profile);

  console.log(`\n✅ 推送已关闭（删除了 ${removed} 个定时任务）\n`);
  return true;
}

function showStatus(userId) {
  const profile = loadProfile(userId);
  if (!profile) {
    console.log(`❌ 用户档案不存在: ${userId}`);
    return;
  }

  const pref = profile.preferences || {};
  const enabled = pref.pushEnabled ?? pref.pushMorning ?? false;
  const cronIds = profile.push?.cronIds || {};

  console.log(`
👤 用户: ${profile.name} (${userId})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧮 八字: ${profile.bazi?.year} ${profile.bazi?.month} ${profile.bazi?.day} ${profile.bazi?.hour}
📅 出生: ${profile.profile?.birthDate} ${profile.profile?.birthTime}
🔔 推送: ${enabled ? '✅ 已开启' : '❌ 已关闭'}
⏰ 早晨: ${pref.morningTime || '08:00'} ${cronIds.morning ? `(cron: ${cronIds.morning})` : ''}
🌙 晚间: ${pref.eveningTime || '20:00'} ${cronIds.evening ? `(cron: ${cronIds.evening})` : ''}
📡 渠道: ${(pref.channels || ['openclaw']).join(', ')}
📆 推送创建: ${profile.push?.createdAt?.split('T')[0] || '未设置'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`);
}

module.exports = { enablePush, disablePush, showStatus };

// ─────────────────────────────────────────────
// 命令行入口
// ─────────────────────────────────────────────

if (require.main !== module) return;

const args = process.argv.slice(2);
const command = args[0];
const userId = args[1];

if (!userId) {
  console.log(`
🔔 每日运势推送管理

用法:
  node push-toggle.js on <userId>                  开启推送（早8点+晚8点）
  node push-toggle.js off <userId>                 关闭推送
  node push-toggle.js status <userId>              查看状态
  node push-toggle.js on <userId> --morning 08:00 --evening 20:00
  node push-toggle.js on <userId> --channel feishu

说明:
  开启后自动创建两个定时任务：
  - 每天早晨推送当日运程（默认 08:00）
  - 每天晚间推送明日预告（默认 20:00）
`);
  process.exit(1);
}

const options = {};
const morningIdx = args.indexOf('--morning');
if (morningIdx !== -1 && args[morningIdx + 1]) options.morning = args[morningIdx + 1];
const eveningIdx = args.indexOf('--evening');
if (eveningIdx !== -1 && args[eveningIdx + 1]) options.evening = args[eveningIdx + 1];
const channelIdx = args.indexOf('--channel');
if (channelIdx !== -1 && args[channelIdx + 1]) options.channel = args[channelIdx + 1];

switch (command) {
  case 'on':  enablePush(userId, options); break;
  case 'off': disablePush(userId); break;
  case 'status': showStatus(userId); break;
  default:
    console.log(`❌ 未知命令: ${command}`);
    process.exit(1);
}
