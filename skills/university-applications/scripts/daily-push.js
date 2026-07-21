#!/usr/bin/env node
/**
 * 每日运势自动推送脚本
 * 读取所有已开启推送的用户，生成定制化运程并通过 OpenClaw 发送
 *
 * 用法:
 *   node daily-push.js                  # 推送今日运势给所有已开启的用户
 *   node daily-push.js --dry-run       # 模拟推送（不实际发送）
 *   node daily-push.js --test <userId> # **仅作为 dry-run 调试工具**：
 *                                       自动以 dry-run 模式运行（不交付、不落盘、不输出运势正文）；
 *                                       未 opt-in 的用户也允许仅做运算验证。
 *                                       v1.2.0 起**已移除**任何借助 flag 走正式发送给未 opt-in 用户的旁路；
 *                                       要正式接收推送，用户必须运行 push-toggle.js on <userId> 显式 opt-in。
 *   node daily-push.js --list          # 列出所有已开启推送的用户（仅聚合统计）
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

  // 注意：这里特意改成「氛围/主题」类描述，不再给出"投资/手术/签约/搬家/诉讼"
  // 等具体行动指令；推送属于自动触发的娱乐性内容，不应越界为
  // 法律/医疗/财务的具体行为建议。
  const YI_JI = {
    '木': {
      yi: ['沟通对话的氛围', '学习与吸收新事物', '主动联系老朋友', '为想做的事列计划'],
      ji: ['情绪冲动下的取舍', '对结果过早下定论', '勉强自己的应酬']
    },
    '火': {
      yi: ['表达想法', '尝试一点小创新', '让自己被看见', '梳理近期热度过高的情绪'],
      ji: ['口角与争辩', '硬碰硬的对抗', '对比与较劲']
    },
    '土': {
      yi: ['整理空间与习惯', '稳住节奏与计划', '回应身边人的需要', '把已经在做的事做厚一层'],
      ji: ['同时摊太多事', '为别人的进度焦虑', '强行加速']
    },
    '金': {
      yi: ['梳理边界与原则', '复盘与归档', '精简事项', '把"差不多"做到位'],
      ji: ['过度严苛地评判他人', '对自己反复挑剔', '冷处理本该回应的关系']
    },
    '水': {
      yi: ['留出独处与休整', '换个角度看老问题', '阅读、写作与表达', '柔和地推进进度'],
      ji: ['过度内耗', '把别人的情绪都接到自己身上', '在不确定时强求答案']
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

  // 注意：以下提示属于自我节奏类的轻量提醒，不是医疗/财务/法律的具体行动指令。
  // 请勿据此做投资决策、终止治疗或撤销合同。

  // 驿马星 → 节奏类提醒
  const yimaZhi = ['申', '亥', '寅', '巳'];
  if (yimaZhi.includes(zhi)) {
    warnings.push({ level: '🟡', type: '节奏', msg: '今日变动气息偏强，给行程多留一点缓冲' });
  }

  // 五黄煞 → 自我照护类提醒
  const wuhuang = ['子', '卯', '午', '酉'];
  if (wuhuang.includes(zhi)) {
    warnings.push({ level: '🟡', type: '自我照护', msg: '近期容易能量低落，注意休息与饮食的规律' });
  }

  // 八字日主与当日关系 → 心态/精力类提醒
  const dayStem = bazi?.dayStem || '甲';
  const dayStemWuxing = { '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水' }[dayStem] || '木';
  const dayWuxing = ZHI_ELEMENT[zhi] || '土';
  const ke = { '木': '土', '火': '金', '土': '水', '金': '木', '水': '火' };

  if (ke[dayStemWuxing] === dayWuxing) {
    warnings.push({ level: '🟡', type: '心绪', msg: '今日容易冲动消费或情绪化决定，重要选择宜冷静一日再做' });
  }

  if (warnings.length === 0) {
    warnings.push({ level: '🟢', type: '综合', msg: '今日总体平稳，按既定节奏行事即可' });
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

⚠️ 本日运势仅为娱乐性文化参考；不是医疗、法律、心理、财务、婚姻、就业的专业建议；不应作为投资、合同、医疗、人身安全等决策的依据。如有相应需要，请联系合规专业人士。

━━━━━━━━━━━━━━━━━━━━━━
📊 今日趋势侧写（参考用）
   工作主题 ${formatStars(scores.career)}
   财务节奏 ${formatStars(scores.wealth)}
   关系氛围 ${formatStars(scores.love)}
   身心状态 ${formatStars(scores.health)}
━━━━━━━━━━━━━━━━━━━━━━

🎨 配色 / 方位 / 数字（生活美学层面）
   颜色：${elementInfo.color}
   方位：${elementInfo.direction}
   数字：${luckyNumbers.join('、')}
   元素：${elementInfo.emoji} ${elementInfo.element}

💮 今日整体气象
   ${fortuneLevel.level} — ${fortuneLevel.desc}

💼 今日适合 / 不太适合的「氛围」
   ✅ 适合：${yiJi.yi.join('、')}
   ⚠️ 不太适合：${yiJi.ji.join('、')}

⚠️ 自我节奏提醒（非医疗 / 财务 / 法律建议）
${warnings.map(w => `   ${w.level}【${w.type}】${w.msg}`).join('\n')}

⏰ 适合行事的时段
${luckyHours.slice(0, 3).map(h => `   • ${h.zhi}时（${h.range}点）- ${h.tip}`).join('\n')}
${luckyHours.length > 3 ? `   • ...等 ${luckyHours.length} 个时段` : ''}

📅 季节 / 时令侧写
${yearMonthTips.map(t => `   【${t.period}】${t.msg}`).join('\n')}

💡 今日一言
   「${quote}」

🧮 八字用神：${yongshen.primary}（主）${yongshen.secondary.join('、')}（辅）
   今日干支：${dayGanZhi}（${elementInfo.element}气${elementInfo.direction.includes('东方') ? '旺' : '得令'}）

———
⚠️ 仅供文化参考，不构成医疗/法律/心理/财务/婚姻等专业建议。重大决策请咨询专业人士；如有情绪困扰请联系当地心理援助热线。
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
  // 双重 opt-in 安全门：
  //  - pushEnabled 为 true
  //  - pushOptInAt 存在（证明是用户主动调用 push-toggle.js on 后写入的时间戳，
  //    仅字段为 true 不足以发送）
  //  - bazi 完整
  // 如果 profile 文件所有者手工修改了 pushEnabled:true 但未补 opt-in 时间戳，
  // 则必须走 push-toggle.js 重新 opt-in，避免静默默认启用推送。
  return profiles.filter(p => {
    const prefs = p.preferences || {};
    const enabled = prefs.pushEnabled === true;
    const optedIn = !!prefs.pushOptInAt; // 时间戳存在
    const hasBazi = p.bazi && p.bazi.day && p.bazi.dayStem;
    return enabled && optedIn && hasBazi;
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

async function sendMessage(userId, message, opts = {}) {
  const { dryRun = false } = opts;
  // 重要：为避免在多用户环境下将某个用户的运势串台到其他人，
  // 这里不会将运势正文写到 stdout，而是：
  //  1. 在 stdout 输出仅含脱敏状态行（供调度者/运维查看）。
  //  2. 实际发送模式下将完整运势写入每个用户独立的本地交付文件，
  //     由 OpenClaw 运行时按 userId 读取并点对点发送。
  //  3. **dry-run 是真正的不落盘运行**：不会生成任何 outbox / outbox-dryrun 文件，
  //     也不会将运势正文输出到 stdout，仅进行计算验证。这保证了
  //     调试/CI/共享终端中不会意外留存个人运势与八字数据。
  if (!userId) {
    console.error('   ⚠ sendMessage: userId 为空，拒绝发送以避免泄露');
    return false;
  }

  if (dryRun) {
    // dry-run 严格不落盘、不交付、不输出运势正文；
    // 仅验证调用者传入的 userId / message 是否合法。
    if (typeof message !== 'string' || !message.length) {
      console.error('   ⚠ dry-run: message 为空，计算可能出错');
      return false;
    }
    return true;
  }

  try {
    const outboxDir = path.join(__dirname, '../data/outbox');
    if (!fs.existsSync(outboxDir)) {
      fs.mkdirSync(outboxDir, { recursive: true, mode: 0o700 });
    }
    // 仅仅允许 userId 中的安全字符，避免路径穿越
    const safeId = String(userId).replace(/[^a-zA-Z0-9_\-]/g, '_');
    const dateStr = new Date().toISOString().split('T')[0];
    const outFile = path.join(outboxDir, `${safeId}_${dateStr}.txt`);
    const payload = {
      userId: safeId,
      generatedAt: new Date().toISOString(),
      mode: 'live',
      content: message
    };
    // 写入文件时限制为仅当前用户可读（0600）
    fs.writeFileSync(outFile, JSON.stringify(payload, null, 2), { encoding: 'utf8', mode: 0o600 });

    // 在 stdout 仅输出状态行，不输出个人运势正文 / 不输出原始 userId
    return true;
  } catch (e) {
    console.error(`   ❌ sendMessage 写入失败: ${e.message}`);
    return false;
  }
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
    if (!testProfile) {
      console.log(`   ❌ 测试用户不存在: ${testUserId}`);
      return;
    }

    // v1.2.0：--test 现在**强制 dry-run**，不再保留 --i-am-the-user 旁路。
    // 任何 --test 调用都不会向未 opt-in 用户产生真实 outbox / 真实交付，
    // 因为这会让脚本可被多操作员或自动化滥用，给从未同意的用户写入个人运势。
    if (!dryRun) {
      console.error('   ❌ 拒绝：--test 在 v1.2.0 起已**强制以 dry-run 运行**，');
      console.error('       不再支持 --i-am-the-user 等旁路走正式发送。');
      console.error('       要正式接收每日推送，请让用户本人运行：');
      console.error(`         node scripts/push-toggle.js on ${testUserId}`);
      console.error('       要做调试验算，请改用：');
      console.error(`         node scripts/daily-push.js --dry-run --test ${testUserId}`);
      return;
    }

    const optedIn = !!(testProfile.preferences && testProfile.preferences.pushEnabled && testProfile.preferences.pushOptInAt);
    if (!optedIn) {
      console.log(`   ⚠️  测试用户 ${testUserId} 未 opt-in 推送；dry-run 模式仅验算不交付、不落盘。`);
    }

    targets = [testProfile];
    console.log(`   📋 测试模式: 仅验算 ${testUserId}（dry-run 强制）\n`);
  }

  console.log(`   📋 共 ${targets.length} 个用户开启推送\n`);
  console.log('   ' + '─'.repeat(50));

  let successCount = 0;
  let failCount = 0;

  for (const profile of targets) {
    const { userId, name } = profile;
    // 不在 stdout 上拼接 userId/姓名；避免在共享环境下被外人看到
    process.stdout.write(`   🔄 推送中... `);

    try {
      const fortune = generatePersonalizedFortune(profile, date);

      if (dryRun) {
        // dry-run 下：仅验证运算能否生成运势文本，不交付、不落盘、不输出正文
        await sendMessage(userId, fortune, { dryRun: true });
        console.log('✅ (dry-run 仅验算，未写入任何文件)');
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
        // 仅记录脱敏后的标识，避免日志文件被外部读取后泄露姓名/userId
        userIdHash: require('crypto').createHash('sha256').update(String(userId)).digest('hex').slice(0, 8),
        status: dryRun ? 'dry-run' : (sent ? 'success' : 'failed')
      });
    } catch (e) {
      console.log(`❌ ${e.message}`);
      failCount++;
      logEntry.results.push({
        userIdHash: require('crypto').createHash('sha256').update(String(profile.userId || '')).digest('hex').slice(0, 8),
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
  // 出于隐私小化原则，本命令只输出聚合计数，
  // 不提供任何逐条查看八字/姓名/userId/推送作息的通道，
  // 所有完整信息请仅通过 `node scripts/profile.js show <userId> --full` 在本人设备上查看。
  const profiles = loadAllProfiles();
  const targets = getUsersWithPushEnabled(profiles);

  console.log('\n📋 已开启每日运势推送的用户（仅聚合统计）:\n');
  console.error('   ⚠ 本命令不输出任何个人信息。需查看单个用户详情请在本人设备上使用：node scripts/profile.js show <userId> --full\n');

  if (targets.length === 0) {
    console.log('   （暂无用户开启推送）\n');
    return;
  }

  const channelsStat = {};
  for (const p of targets) {
    const ch = (p.preferences?.channels || ['openclaw'])[0] || 'openclaw';
    channelsStat[ch] = (channelsStat[ch] || 0) + 1;
  }
  const lastPushStat = targets.reduce((acc, p) => {
    acc[p.lastPushDate ? 'pushed' : 'never'] = (acc[p.lastPushDate ? 'pushed' : 'never'] || 0) + 1;
    return acc;
  }, {});
  console.log(`   总计：${targets.length} 人开启推送`);
  console.log(`   渠道分布：${Object.entries(channelsStat).map(([k,v])=>`${k}=${v}`).join(', ')}`);
  console.log(`   推送状态：已推送过=${lastPushStat.pushed||0}, 从未推送=${lastPushStat.never||0}`);
  console.log('');
}

// ============================================================
// 命令行入口
// ============================================================

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--list') || args.includes('-l')) {
    // 不再提供 --full 通道，避免批量暴露个人信息
    if (args.includes('--full')) {
      console.error('   ❌ 出于隐私考虑，--list --full 已在 v1.1.7 移除。如需查看单个用户详情，请在本人设备运行：');
      console.error('   node scripts/profile.js show <userId> --full');
      process.exit(1);
    }
    listPushUsers();
    return;
  }

  // --test 必须先于 --dry-run 处理，以便 --dry-run --test <userId> 走单用户路径。
  // v1.2.0：--test 已**强制 dry-run**，不再读取 --i-am-the-user 旁路。
  const testIdx = args.indexOf('--test');
  if (testIdx !== -1 && args[testIdx + 1]) {
    if (args.includes('--i-am-the-user')) {
      console.error('⚠ 注意：--i-am-the-user 旁路在 v1.2.0 起已**移除**。');
      console.error('  --test 现在统一以 dry-run 模式运行，不会向未 opt-in 用户做真实交付。');
    }
    await runPush({ dryRun: true, testUserId: args[testIdx + 1] });
    return;
  }

  if (args.includes('--dry-run') || args.includes('-d')) {
    await runPush({ dryRun: true });
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
  node daily-push.js --dry-run        模拟推送（只计算不交付、不落盘）
  node daily-push.js --test <userId>  **调试专用**；v1.2.0 起强制 dry-run，不会做真实交付。
                                      要正式接收推送，请让该用户本人运行 push-toggle.js on <userId>。
  node daily-push.js --list           仅输出聚合统计（不提供 --full 通道）
隐私说明:
  - sendMessage 不会将个人运势输出到 stdout，仅在非 dry-run 下写入个人 outbox 由 OpenClaw 运行时点对点派发。
  - --dry-run 仅做运算验证，不会产生任何 outbox 文件、也不会将运势正文输出到终端。
  - --test 默认不会绕过 opt-in 检查，以防止给未同意用户发送个人运势。
  - --list 只出现聚合计数（人数/渠道分布/推送状态），不提供 --full 通道。
  - 需查看某个用户详情，请在本人设备上运行：node scripts/profile.js show <userId> --full。

配置:
  - 用户的 preferences.pushEnabled 需为 true 且必须包含显式 opt-in 时间戳（preferences.pushOptInAt）
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
