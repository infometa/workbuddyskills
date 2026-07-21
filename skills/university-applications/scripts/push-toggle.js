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

// 各领域「氛围側写」模板（v1.1.8 重写）
//
// 重要：推送是调度器自动触发的娱乐性运势，不是专业依据。本模板严格遵守与 SKILL.md 一致的边界：
//   - **不**覆盖医疗 / 法律 / 金融专业领域；不出具「投资 / 手术 / 起诉 / 签合同 / 结婚 / 辞职 / 服药 / 停药」等明确动作；
//   - 仅描述「节奏 / 氛围 / 心态」偏向，表达上使用「适合 / 容易 / 可以留意」、避免「应该 / 必须 / 一定」。
//   - 不另行「深析」法律 / 医疗 / 金融主题；「官司」主题已从偏好追踪中整体下线，推送不生成。
const TOPIC_EXPANDED = {
  '财运': `💰 财运节奏側写（仅作文化参考，不是投资 / 财务 / 税务建议）：
   - 今日财星与财位的气象偏向
   - 容易冲动消费 / 过于退缩的隐隱模式（提醒「适合怎么调整节奏」而不是「应该买卖什么」）
   - 重要财务决策（投资 / 借贷 / 担保 / 重大购置）请**在亓下险象**时**多留一天冷静期**，并咨询持牌财务 / 受讯投顾`,
  '事业': `💼 事业节奏側写（仅作文化参考，不是 HR / 职业 / 法律建议）：
   - 今日事业气场与主表现调性偏向
   - 适合推进 / 适合收阶段 / 适合复盘的节奏提醒（不说「应该辞职 / 应该跳槽 / 应该创业」）
   - 职场重大决定（辞职 / 跳槽 / 创业 / 劳动争议 / 签合同）请**与本人现实条件 + 专业意见**结合后决定`,
  '感情': `💕 感情氛围側写（仅作文化参考，不是心理 / 婚姻 / 家庭关系专业建议）：
   - 今日互动氛围与表达节奏偏向
   - 表达 / 倾听 / 独处的气象提醒（不说「应该复合 / 应该分手 / 应该告白」）
   - 重大关系决定（复合 / 结束 / 结婚 / 同居）请由本人与对方充分沟通后决定；如遇家暴 / 跟踪骚扰 / 自伤风险，请**立即联系当地心理援助 / 反家暴 / 报警线**`,
  '健康': `🏥 身心状态側写（仅作文化参考，不是医疗建议 / 诊断 / 治疗方案）：
   - 今日五行对应脏腑的气象偏向
   - 饮食 / 作息 / 运动节奏上的柔性提醒（不推荐具体药品，不提供剧烈运动指导）
   - **不代替任何医生诊断 / 处方 / 手术决策**；不建议服药 / 停药 / 更改治疗方案；身体不适请**立即就医**`,
  '婚姻': `💍 婚姻氛围側写（仅作文化参考，不是婚姻 / 家庭 / 法律专业建议）：
   - 今日关系互动与沟通节奏偏向
   - 倾听 / 表达 / 似冷却期的气象提醒（不说「应该离婚 / 应该复合 / 应该生育」）
   - 重大婚家决定（离婚 / 复合 / 财产分割 / 拚养权）请咨询法律 / 心理专业人士后决定`,
  '子女': `👶 亲子氛围側写（仅作文化参考，不是教育 / 医疗 / 法律专业建议）：
   - 今日亲子沟通与陆岭互动的气象偏向
   - **绝不**指代未成年人的命运走向 / 学业选择 / 职业预言；不代替医疗 / 教育 / 法律专业判断`,
  '出行': `✈️ 出行节奏側写（仅作文化参考，不是安全 / 交通 / 医疗建议）：
   - 今日驿马与方位的象征偏向
   - 适合为行程多留缓冲 / 适合重新梳理路线的氛围提醒
   - 出行安全、天气预警、交通管制请以当地气象 / 交警 / 航空公布为准`,
  '风水': `🏠 空间与生活美学側写（仅作生活美学 / 环境优化参考）：
   - 今日飞星方位的象征表述
   - 家居 / 办公能量调整提醒（几个轻量可调整点，不取代装修与工程设计）
   - **不是工程结构 / 消防 / 电气 / 采光专业鉴定**；涉及房屋安全 / 装修施工 / 电路改造请委托具备资质的专业人员`,
};

// v1.1.8 起不再在推送提示词中指示 Agent 「主动搜索今日新闻」，避免将本只应本地计算的推送静默拓展为「外部数据采集 + 个性化画像合成」。如用户明说要「结合今日新闻」，Agent 可在主动会话中进行一次性检索，但不会被推送 cron 隐式定期触发。
const NEWS_FORTUNE_MAPPING = '';

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

  return `请为${name}生成今日命理运程报告（仅作文化参考，不出具医疗/法律/金融专业建议）。
用户八字：${baziStr}，日主：${bazi.dayStem}
用户重点关注（按偏好排序）：${top1} > ${top2} > ${top3}

步骤：
1) 运行 node scripts/daily-fortune.js 获取今日干支基础运程（**仅本地计算，不授权访问任何外部网络**）
2) 结合八字与今日干支作「节奏 / 氛围 / 心态」偏向分析，重点展开【${top1}】领域的「气象节奏」（严禁跨界为医疗/法律/金融专业建议）
3) 完成后运行：node scripts/preference-tracker.js record ${userId} ${top1} morning_push

由于仅「官司」主题本身已从偏好追踪中下线，推送不生成「法律/诉讼」深析。

输出格式：
🌅 【私人命理顾问】今日完整日期（含星期）

📊 今日综合指数
   事业：★★★★☆  财运：★★★☆☆  感情：★★★☆☆  健康：★★★★☆

🎨 幸运色：xxx（结合今日干支五行）

${expandedSection}

💼 今日宜忌
   ✅ 宜：xxx、xxx、xxx
   ❌ 忌：xxx、xxx

⚠️ 风险提示（仅描述「心态 / 节奏 / 身心状态」偏向，**不代替**医疗 / 法律 / 金融判断；如无则省略）

💡 今日点醒（1-2 句：象征性表述，不出具行动指令）
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

  return `请为${name}生成明日命理预告（今晚提前推送明日运势；仅作文化参考，不出具医疗/法律/金融专业建议）。
用户八字：${baziStr}，日主：${bazi.dayStem}
用户重点关注（按偏好排序）：${top1} > ${top2}

步骤：
1) 运行 node scripts/daily-fortune.js 获取明日（今日+1天）干支运程（**仅本地计算，不授权访问任何外部网络**）
2) 重点展开【${top1}】明日「节奏 / 氛围 / 心态」偏向预告（严禁跨界为医疗/法律/金融专业建议）
3) 完成后运行：node scripts/preference-tracker.js record ${userId} ${top1} evening_push

输出格式：
🌙 【明日预告】明日完整日期（含星期）

📊 明日综合指数
   事业：★★★★☆  财运：★★★☆☆  感情：★★★☆☆  健康：★★★★☆

🎨 明日幸运色：xxx

${expandedSection.replace('今日', '明日')}

💼 明日宜忌
   ✅ 宜：xxx、xxx
   ❌ 忌：xxx、xxx

⚠️ 明日节奏提醒（仅描述「氛围 / 心态 / 身心状态」偏向，**不代替**医疗 / 法律 / 金融判断；如无则省略）

💡 今晚点醒（1 句：象征性表述，不出具行动指令）

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
  profile.preferences.pushOptInAt = new Date().toISOString(); // 显式 opt-in 时间戳：daily-push 会二次验证
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
  profile.preferences.pushOptInAt = null; // \u6e05\u9664 opt-in \u65f6\u95f4\u6233\uff1bdaily-push \u4f1a\u62d2\u7edd\u53d1\u9001
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
