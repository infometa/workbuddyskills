#!/usr/bin/env node
/**
 * 每日运势自动推送脚本
 * 读取所有已开启推送的用户，生成定制化运程并通过 OpenClaw 发送
 *
 * 用法:
 *   node daily-push.js                  # 推送今日运势给所有已开启的用户
 *   node daily-push.js --dry-run       # 模拟推送（不实际发送）
 *   node daily-push.js --test <userId> # 测试推送指定用户
 *   node daily-push.js --list          # 列出所有已开启推送的用户
 */

const fs = require('fs');
const path = require('path');

const PROFILES_DIR = path.join(__dirname, '../data/profiles');
const LOG_FILE = path.join(__dirname, '../data/push-log.json');

// ============================================================
// 八字/紫微 核心分析（内嵌，避免外部依赖）
// ============================================================

const GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
const SHENGXIAO = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪'];

const ZHI_ELEMENT = {
  '子': '水', '丑': '土', '寅': '木', '卯': '木',
  '辰': '土', '巳': '火', '午': '火', '未': '土',
  '申': '金', '酉': '金', '戌': '土', '亥': '水'
};

const ELEMENT_COLOR = {
  '木': { color: '绿色、青色', direction: '东方', emoji: '🌿' },
  '火': { color: '红色、紫色', direction: '南方', emoji: '🔥' },
  '土': { color: '黄色、棕色', direction: '中央', emoji: '🌍' },
  '金': { color: '白色、银色', direction: '西方', emoji: '⚪' },
  '水': { color: '黑色、蓝色', direction: '北方', emoji: '🌊' }
};

const LUCKY_NUMBERS = {
  '木': [3, 8], '火': [2, 7], '土': [5, 10], '金': [4, 9], '水': [1, 6]
};

const DAY_MAP = ['日', '一', '二', '三', '四', '五', '六'];
const MONTH_MAP = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊'];

const HOUR_INFO = {
  '子': { range: '23-01', tip: '整理思考', stars: '☽ 阴性星' },
  '丑': { range: '01-03', tip: '睡眠休息', stars: '☆ 平常' },
  '寅': { range: '03-05', tip: '计划准备', stars: '🌟 小吉' },
  '卯': { range: '05-07', tip: '晨间运动', stars: '🌟 小吉' },
  '辰': { range: '07-09', tip: '贵人运佳', stars: '★★ 吉祥' },
  '巳': { range: '09-11', tip: '事业高峰', stars: '★★ 大吉' },
  '午': { range: '11-13', tip: '财运旺盛', stars: '★★ 大吉' },
  '未': { range: '13-15', tip: '平稳行事', stars: '★☆ 一般' },
  '申': { range: '15-17', tip: '财运佳', stars: '★★ 吉祥' },
  '酉': { range: '17-19', tip: '收整理', stars: '★☆ 一般' },
  '戌': { range: '19-21', tip: '社交应酬', stars: '★★ 吉祥' },
  '亥': { range: '21-23', tip: '学习思考', stars: '☆ 平常' }
};

// ============================================================
// 命理核心算法
// ============================================================

function getDayGanZhi(date = new Date()) {
  const baseDate = new Date('2024-01-01T12:00:00');
  const diffDays = Math.round((date - baseDate) / (1000 * 60 * 60 * 24));
  const ganIndex = ((diffDays % 10) + 10) % 10;
  const zhiIndex = ((diffDays % 12) + 12) % 12;
  return GAN[ganIndex] + ZHI[zhiIndex];
}

function getYearGanZhi(year) {
  const baseYear = 1984; // 甲子年
  const offset = year - baseYear;
  return GAN[((offset % 10) + 10) % 10] + ZHI[((offset % 12) + 12) % 12];
}

function getLunarMonth(month) {
  return MONTH_MAP[month - 1] + '月';
}

function getElementInfo(ganZhi) {
  const zhi = ganZhi[1];
  const element = ZHI_ELEMENT[zhi] || '土';
  return { element, ...ELEMENT_COLOR[element] };
}

function getLuckyNumbers(element) {
  const nums = LUCKY_NUMBERS[element] || [5, 10];
  const allNums = [];
  for (let i = 0; i < 5; i++) allNums.push(nums[i % nums.length]);
  return allNums.slice(0, 5);
}

// ============================================================
// 八字用神计算
// ============================================================

function calculateBaziYongshen(bazi) {
  if (!bazi || !bazi.dayStem) return { primary: '木', secondary: ['火', '水'], details: [] };

  const dayStem = bazi.dayStem;
  const monthZhi = bazi.month ? bazi.month[1] : '寅';

  const dayWuxing = { '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水' }[dayStem] || '木';
  const monthWuxing = ZHI_ELEMENT[monthZhi] || '木';

  const sheng = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' };
  const ke = { '木': '土', '火': '金', '土': '水', '金': '木', '水': '火' };

  const results = [];

  // 调候用神
  const tiaohouTable = {
    '甲': { '寅': '丙', '卯': '丙', '辰': '癸', '巳': '壬', '午': '壬', '未': '癸', '申': '丁', '酉': '丁', '戌': '辛', '亥': '丙', '子': '庚', '丑': '辛' },
    '乙': { '寅': '丙', '卯': '丙', '辰': '癸', '巳': '壬', '午': '癸', '未': '丙', '申': '丁', '酉': '丁', '戌': '辛', '亥': '丙', '子': '庚', '丑': '辛' }
  };
  const t = tiaohouTable[dayStem]?.[monthZhi];
  if (t) results.push({ type: '调候', value: t, desc: '寒木喜火暖局' });

  // 扶抑用神
  results.push({ type: '扶抑', value: sheng[dayWuxing], desc: `日主${dayWuxing}，喜生助` });
  results.push({ type: '忌', value: ke[dayWuxing], desc: `日主${dayWuxing}，宜避` });

  const primary = results[0]?.value || dayWuxing;
  const secondary = [...new Set(results.filter(r => r.type === '扶抑').map(r => r.value))];

  return { primary, secondary: secondary.slice(0, 2), details: results };
}

// ============================================================
// 运势评分（结合八字五行 + 当日干支）
// ============================================================

function generatePersonalizedScores(bazi, dayGanZhi) {
  const dayElement = ZHI_ELEMENT[dayGanZhi[1]] || '土';
  const dayWuxing = dayElement;

  // 八字日主五行
  const dayStem = bazi?.dayStem || '甲';
  const dayStemWuxing = { '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水' }[dayStem] || '木';

  // 日主与当日五行的关系
  const sheng = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' };
  const ke = { '木': '土', '火': '金', '土': '水', '金': '木', '水': '火' };
  const bi = { '木': '金', '火': '水', '土': '木', '金': '火', '水': '土' };

  // 生助日主 = 吉
  const dayHelpsDay = dayWuxing === dayStemWuxing || sheng[dayStemWuxing] === dayWuxing;
  // 克耗日主 = 压力
  const dayStressesDay = ke[dayStemWuxing] === dayWuxing || bi[dayStemWuxing] === dayWuxing;

  // 事业：与用神同气 + 当日吉
  let career = 3 + Math.random() * 1.5;
  let wealth = 3 + Math.random() * 1.5;
  let love = 3 + Math.random() * 1.5;
  let health = 3 + Math.random() * 1.5;

  if (dayHelpsDay) {
    career += 0.5;
    wealth += 0.5;
    health += 0.3;
  }
  if (dayStressesDay) {
    career -= 0.3;
    wealth -= 0.3;
  }

  // 基于用神微调
  const yongshen = calculateBaziYongshen(bazi);
  if (yongshen.primary === dayElement) { career += 0.5; wealth += 0.3; }

  // 加入日期随机性（确保每天有变化）
  const date = new Date();
  const dayFactor = (date.getDate() % 3) * 0.3 - 0.3;
  career += dayFactor;
  wealth += dayFactor * 0.8;
  love += dayFactor * 0.6;
  health += dayFactor * 0.4;

  const scores = {
    career: Math.min(5, Math.max(1, career)).toFixed(1),
    wealth: Math.min(5, Math.max(1, wealth)).toFixed(1),
    love: Math.min(5, Math.max(1, love)).toFixed(1),
    health: Math.min(5, Math.max(1, health)).toFixed(1)
  };

  return scores;
}

function formatStars(score) {
  const num = parseFloat(score);
  const full = Math.floor(num);
  const half = num - full >= 0.5 ? 1 : 0;
  return '★'.repeat(full) + '☆'.repeat(5 - full - half);
}

// ============================================================
// 宜忌生成（基于八字用神 + 当日干支）
// ============================================================

function generateYiJi(bazi, dayGanZhi) {
  const dayElement = ZHI_ELEMENT[dayGanZhi[1]] || '土';
  const yongshen = calculateBaziYongshen(bazi);
  const primaryElement = yongshen.primary;

  const YI_JI = {
    '木': {
      yi: ['出行', '学习', '交友', '谈判', '签约', '求职'],
      ji: ['冒险', '投资', '手术', '安葬', '破土']
    },
    '火': {
      yi: ['表白', '签约', '创新', '表演', '开业', '上任'],
      ji: ['安葬', '搬家', '诉讼', '动土', '破土']
    },
    '土': {
      yi: ['种植', '装修', '求职', '上任', '签约', '装修'],
      ji: ['动土', '开业', '破土', '安葬', '投资']
    },
    '金': {
      yi: ['上任', '洽谈', '收款', '装修', '签约', '投资'],
      ji: ['安葬', '破土', '开业', '动土', '搬家']
    },
    '水': {
      yi: ['出行', '考试', '推广', '流动', '求职', '开业'],
      ji: ['搬家', '动土', '投资', '安葬', '破土']
    }
  };

  // 优先用神，其次当日五行
  const element = primaryElement || dayElement;
  const info = YI_JI[element] || YI_JI['土'];

  return {
    yi: info.yi.slice(0, 4),
    ji: info.ji.slice(0, 4)
  };
}

// ============================================================
// 吉凶判断
// ============================================================

function getDayFortuneLevel(dayGanZhi) {
  const zhi = dayGanZhi[1];

  // 天恩 吉日
  const tianEnZhi = ['丑', '寅', '卯', '辰', '午', '未', '亥'];
  // 天贵 吉时
  const tianGuiZhi = ['辰', '巳', '午', '未', '申'];
  // 驿马 变动
  const yimaZhi = ['申', '亥', '寅', '巳'];

  let level = '平常';
  let desc = '今日诸事平稳';

  if (tianEnZhi.includes(zhi)) {
    level = '吉祥';
    desc = '天恩降临，贵人相助';
  }
  if (yimaZhi.includes(zhi)) {
    if (level === '吉祥') {
      level = '小吉';
      desc = '有变动，宜把握机遇';
    } else {
      level = '平常';
      desc = '驿马星动，出行奔波';
    }
  }

  // 检查是否破日（相破）
  const poPairs = [['子','丑'], ['寅','亥'], ['卯','戌'], ['辰','酉'], ['巳','申'], ['午','未']];
  for (const [a, b] of poPairs) {
    if (zhi === a || zhi === b) {
      level = '平常';
      desc = '今日有小损耗，宜守成';
      break;
    }
  }

  return { level, desc };
}

// ============================================================
// 风险预警
// ============================================================

function generateWarnings(bazi, dayGanZhi) {
  const warnings = [];
  const zhi = dayGanZhi[1];

  // 驿马星
  const yimaZhi = ['申', '亥', '寅', '巳'];
  if (yimaZhi.includes(zhi)) {
    warnings.push({ level: '🟡', type: '出行', msg: '今日驿马星动，出行注意安全，提前出门' });
  }

  // 五黄煞（简易判断：基于地支）
  const wuhuang = ['子', '卯', '午', '酉'];
  if (wuhuang.includes(zhi)) {
    warnings.push({ level: '🟡', type: '健康', msg: '注意脾胃保养，饮食清淡' });
  }

  // 八字日主与当日关系
  const dayStem = bazi?.dayStem || '甲';
  const dayStemWuxing = { '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水' }[dayStem] || '木';
  const dayWuxing = ZHI_ELEMENT[zhi] || '土';
  const ke = { '木': '土', '火': '金', '土': '水', '金': '木', '水': '火' };

  if (ke[dayStemWuxing] === dayWuxing) {
    warnings.push({ level: '🔴', type: '破财', msg: '今日财星受克，谨慎投资，避免大额花费' });
  }

  if (warnings.length === 0) {
    warnings.push({ level: '🟢', type: '综合', msg: '今日总体顺遂，无明显风险' });
  }

  return warnings;
}

// ============================================================
// 吉时计算
// ============================================================

function getLuckyHours(dayGanZhi) {
  const zhi = dayGanZhi[1];
  const dayElement = ZHI_ELEMENT[zhi] || '土';

  // 找与当日同气的时辰（旺相）
  const sameElementZhi = Object.entries(ZHI_ELEMENT)
    .filter(([_, el]) => el === dayElement)
    .map(([z]) => z);

  // 找生助当日五行的时辰
  const sheng = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' };
  const helpfulZhi = Object.entries(ZHI_ELEMENT)
    .filter(([_, el]) => el === sheng[dayElement])
    .map(([z]) => z);

  const allLucky = [...sameElementZhi, ...helpfulZhi];
  const unique = [...new Set(allLucky)].slice(0, 4);

  return unique.map(z => ({
    zhi: z,
    ...(HOUR_INFO[z] || { range: '--', tip: '平常', stars: '☆' })
  }));
}

// ============================================================
// 流年/流月提示（简化版，基于八字和大运）
// ============================================================

function getYearMonthTips(bazi) {
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;

  const yearGanZhi = getYearGanZhi(currentYear);
  const yearElement = ZHI_ELEMENT[yearGanZhi[1]] || '土';

  const tips = [];

  // 流年提示
  const yearTips = {
    '木': '今年木气旺盛，利事业拓展，春季尤佳',
    '火': '今年火气当令，利创新突破，夏季事业运佳',
    '土': '今年土气稳重，利积累沉淀，秋季财运回升',
    '金': '今年金气肃杀，利变革调整，秋季利财运',
    '水': '今年水气流动，利流通传播，冬季人脉广'
  };
  tips.push({ period: '流年', msg: yearTips[yearElement] || '今年运势平稳' });

  // 流月提示（简化）
  const monthTips = [
    '正月开门红，二月稳中求进，三月事业上升',
    '四月注意小人，五月财运上佳，六月桃花旺盛',
    '七月健康注意，八月事业转折，九月贵人相助',
    '十月财运爆发，十一月感情升温，十二月总结规划'
  ];
  const monthIdx = Math.floor((currentMonth - 1) / 2);
  tips.push({ period: '本月', msg: monthTips[monthIdx] || '本月运势良好' });

  return tips;
}

// ============================================================
// 每日一言
// ============================================================

function getDailyQuote(dayGanZhi) {
  const quotes = [
    { element: '木', text: '木秀于林，风必摧之；堆出于岸，流必湍之。' },
    { element: '木', text: '顺势而为，不与天争；待时而动，方成大事。' },
    { element: '火', text: '火焰熊熊，照亮前路；热情如火，无坚不摧。' },
    { element: '火', text: '烈火炼真金，逆境显本色。' },
    { element: '土', text: '厚德载物，稳如泰山；静以修身，俭以养德。' },
    { element: '土', text: '土能生金，稳中求进；深根固本，方可长久。' },
    { element: '金', text: '金以刚为体，人以正为尊；锋芒内敛，大业可成。' },
    { element: '金', text: '金戈铁马，气吞万里如虎。' },
    { element: '水', text: '上善若水，水善利万物而不争。' },
    { element: '水', text: '水能载舟，亦能覆舟；顺势而行，方得始终。' },
    { element: '通用', text: '命里有时终须有，命里无时莫强求。' },
    { element: '通用', text: '三分天注定，七分靠打拼。' }
  ];

  const dayElement = ZHI_ELEMENT[dayGanZhi[1]] || '土';
  const dayQuotes = quotes.filter(q => q.element === dayElement);
  const fallback = quotes.filter(q => q.element === '通用');

  const pool = dayQuotes.length > 0 ? dayQuotes : fallback;
  const idx = new Date().getDate() % pool.length;
  return pool[idx]?.text || '积善之家，必有余庆。';
}

// ============================================================
// 生成完整个性化运程报告
// ============================================================

function generatePersonalizedFortune(profile, date = new Date()) {
  const { bazi } = profile;
  const dayGanZhi = getDayGanZhi(date);
  const elementInfo = getElementInfo(dayGanZhi);
  const luckyNumbers = getLuckyNumbers(elementInfo.element);
  const scores = generatePersonalizedScores(bazi, dayGanZhi);
  const fortuneLevel = getDayFortuneLevel(dayGanZhi);
  const yiJi = generateYiJi(bazi, dayGanZhi);
  const warnings = generateWarnings(bazi, dayGanZhi);
  const luckyHours = getLuckyHours(dayGanZhi);
  const yearMonthTips = getYearMonthTips(bazi);
  const quote = getDailyQuote(dayGanZhi);
  const yongshen = calculateBaziYongshen(bazi);

  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const weekDay = DAY_MAP[date.getDay()];
  const lunarMonth = getLunarMonth(month);

  // 用户基本信息
  const userName = profile.name || '你';
  const gender = profile.profile?.gender === '男' ? '先生' : '女士';
  const zodiac = bazi?.zodiac || '';

  // 构建报告
  const fortuneEmoji = fortuneLevel.level === '大吉' ? '🌟' :
                       fortuneLevel.level === '吉祥' ? '✨' :
                       fortuneLevel.level === '小吉' ? '🌤️' : '🌙';

  let report = `${fortuneEmoji} 【${userName}${gender}】${year}年${month}月${day}日（周${weekDay}）

━━━━━━━━━━━━━━━━━━━━━━
📊 今日综合指数
   事业 ${formatStars(scores.career)} ${scores.career}分
   财运 ${formatStars(scores.wealth)} ${scores.wealth}分
   感情 ${formatStars(scores.love)} ${scores.love}分
   健康 ${formatStars(scores.health)} ${scores.health}分
━━━━━━━━━━━━━━━━━━━━━━

🎨 幸运属性
   颜色：${elementInfo.color}
   方位：${elementInfo.direction}
   数字：${luckyNumbers.join('、')}
   幸运物：${elementInfo.emoji} ${elementInfo.element}元素相关

💮 今日吉凶
   ${fortuneLevel.level} — ${fortuneLevel.desc}

💼 今日宜忌
   ✅ 宜：${yiJi.yi.join('、')}
   ❌ 忌：${yiJi.ji.join('、')}

⚠️ 风险提示
${warnings.map(w => `   ${w.level}【${w.type}】${w.msg}`).join('\n')}

⏰ 吉时
${luckyHours.slice(0, 3).map(h => `   • ${h.zhi}时（${h.range}点）- ${h.tip}`).join('\n')}
${luckyHours.length > 3 ? `   • ...等 ${luckyHours.length} 个吉时` : ''}

📅 流年流月
${yearMonthTips.map(t => `   【${t.period}】${t.msg}`).join('\n')}

💡 今日一言
   「${quote}」

🧮 八字用神：${yongshen.primary}（主）${yongshen.secondary.join('、')}（辅）
   今日干支：${dayGanZhi}（${elementInfo.element}气${elementInfo.direction.includes('东方') ? '旺' : '得令'}）
`;

  return report;
}

// ============================================================
// 用户档案管理
// ============================================================

function loadAllProfiles() {
  if (!fs.existsSync(PROFILES_DIR)) return [];
  const files = fs.readdirSync(PROFILES_DIR).filter(f => f.endsWith('.json'));
  const profiles = [];
  for (const file of files) {
    try {
      const userId = file.replace('.json', '');
      const data = JSON.parse(fs.readFileSync(path.join(PROFILES_DIR, file), 'utf8'));
      profiles.push({ userId, ...data });
    } catch (e) {
      console.warn(`⚠️ 加载档案失败: ${file}`, e.message);
    }
  }
  return profiles;
}

function getUsersWithPushEnabled(profiles) {
  return profiles.filter(p => {
    // 新字段：preferences.pushEnabled（优先）或 legacy 字段
    const enabled = p.preferences?.pushEnabled ?? p.preferences?.pushMorning ?? false;
    const hasBazi = p.bazi && p.bazi.day && p.bazi.dayStem;
    return enabled && hasBazi;
  });
}

function updateLastPushDate(userId) {
  const filePath = path.join(PROFILES_DIR, `${userId}.json`);
  if (!fs.existsSync(filePath)) return;
  try {
    const profile = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    profile.lastPushDate = new Date().toISOString().split('T')[0];
    profile.updatedAt = new Date().toISOString().split('T')[0];
    fs.writeFileSync(filePath, JSON.stringify(profile, null, 2), 'utf8');
  } catch (e) {
    console.warn(`⚠️ 更新推送日期失败: ${userId}`, e.message);
  }
}

// ============================================================
// OpenClaw 消息发送（通过 IPC / openclaw 工具接口）
// ============================================================

async function sendMessage(userId, message) {
  // 在 openclaw cron 环境中，stdout 内容由运行时自动发送给用户
  console.log(message);
  return true;
}

// ============================================================
// 日志记录
// ============================================================

function loadLog() {
  if (!fs.existsSync(LOG_FILE)) return { runs: [] };
  try {
    return JSON.parse(fs.readFileSync(LOG_FILE, 'utf8'));
  } catch (e) {
    return { runs: [] };
  }
}

function appendLog(entry) {
  const log = loadLog();
  log.runs.push(entry);
  // 只保留最近100条
  if (log.runs.length > 100) log.runs = log.runs.slice(-100);
  fs.writeFileSync(LOG_FILE, JSON.stringify(log, null, 2), 'utf8');
}

// ============================================================
// 主推送流程
// ============================================================

async function runPush({ dryRun = false, testUserId = null } = {}) {
  const date = new Date();
  const dateStr = date.toISOString().split('T')[0];
  const logEntry = {
    date: dateStr,
    timestamp: new Date().toISOString(),
    dryRun,
    results: []
  };

  console.log(`\n🚀 每日运势推送开始 - ${dateStr}\n`);
  console.log(`   模式: ${dryRun ? '🔸 模拟推送（不实际发送）' : '📨 正式推送'}\n`);

  const allProfiles = loadAllProfiles();
  let targets = getUsersWithPushEnabled(allProfiles);

  if (testUserId) {
    const testProfile = allProfiles.find(p => p.userId === testUserId);
    if (testProfile) {
      targets = [testProfile];
      console.log(`   📋 测试模式: 仅推送给 ${testUserId}\n`);
    } else {
      console.log(`   ❌ 测试用户不存在: ${testUserId}`);
      return;
    }
  }

  console.log(`   📋 共 ${targets.length} 个用户开启推送\n`);
  console.log('   ' + '─'.repeat(50));

  let successCount = 0;
  let failCount = 0;

  for (const profile of targets) {
    const { userId, name } = profile;
    process.stdout.write(`   🔄 ${name || userId} (${userId})... `);

    try {
      const fortune = generatePersonalizedFortune(profile, date);

      if (dryRun) {
        console.log('\n' + fortune.split('\n').map(l => '   ' + l).join('\n'));
        console.log('   ' + '─'.repeat(50));
        successCount++;
      } else {
        const sent = await sendMessage(userId, fortune);
        if (sent) {
          updateLastPushDate(userId);
          console.log('✅');
          successCount++;
        } else {
          console.log('⚠️ (发送失败，已记录)');
          failCount++;
        }
      }

      logEntry.results.push({
        userId,
        name,
        status: dryRun ? 'dry-run' : (sent ? 'success' : 'failed')
      });
    } catch (e) {
      console.log(`❌ ${e.message}`);
      failCount++;
      logEntry.results.push({
        userId,
        name,
        status: 'error',
        error: e.message
      });
    }
  }

  console.log('   ' + '─'.repeat(50));
  console.log(`\n   ✅ 推送完成: ${successCount} 成功${failCount > 0 ? `, ${failCount} 失败` : ''}\n`);

  appendLog(logEntry);
  return { successCount, failCount };
}

// ============================================================
// 列出开启推送的用户
// ============================================================

function listPushUsers() {
  const profiles = loadAllProfiles();
  const targets = getUsersWithPushEnabled(profiles);

  console.log('\n📋 已开启每日运势推送的用户:\n');
  if (targets.length === 0) {
    console.log('   （暂无用户开启推送）\n');
    return;
  }

  for (const p of targets) {
    const lastPush = p.lastPushDate || '从未推送';
    const channels = (p.preferences?.channels || ['openclaw']).join(', ');
    console.log(`   👤 ${p.name} (${p.userId})`);
    console.log(`      八字: ${p.bazi?.year} ${p.bazi?.month} ${p.bazi?.day} ${p.bazi?.hour}`);
    console.log(`      推送时间: ${p.preferences?.morningTime || '07:00'} | 渠道: ${channels}`);
    console.log(`      最后推送: ${lastPush}`);
    console.log('');
  }
}

// ============================================================
// 命令行入口
// ============================================================

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--list') || args.includes('-l')) {
    listPushUsers();
    return;
  }

  if (args.includes('--dry-run') || args.includes('-d')) {
    await runPush({ dryRun: true });
    return;
  }

  const testIdx = args.indexOf('--test');
  if (testIdx !== -1 && args[testIdx + 1]) {
    await runPush({ testUserId: args[testIdx + 1] });
    return;
  }

  if (args.length === 0) {
    await runPush({ dryRun: false });
    return;
  }

  // 帮助
  console.log(`
🌅 每日运势自动推送脚本

用法:
  node daily-push.js                  推送给所有已开启的用户
  node daily-push.js --dry-run        模拟推送（显示内容，不发送）
  node daily-push.js --test <userId>  测试推送指定用户
  node daily-push.js --list           列出已开启推送的用户

配置:
  - 用户的 preferences.pushEnabled 需为 true
  - 用户的 preferences.morningTime 决定推送时间（默认07:00）
  - 渠道由 preferences.channels 指定（openclaw/telegram/feishu，由 OpenClaw 运行时统一投递）
  - 用户需有完整的八字信息（bazi.dayStem 不为空）

OpenClaw Cron 配置:
  openclaw cron add "0 7 * * *" "cd <skill-dir> && node scripts/daily-push.js"
`);
}

main().catch(e => {
  console.error('❌ 推送脚本出错:', e);
  process.exit(1);
});
