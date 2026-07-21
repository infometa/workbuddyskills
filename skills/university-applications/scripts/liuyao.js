#!/usr/bin/env node
/**
 * 六爻预测脚本
 * 模拟三枚铜钱摇六次成卦
 * 输入：6组阴阳信息（每组3个0或1，1=阳面）
 */

const yaoNames = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻'];

// 八卦对应
const baGua = {
  '乾': '☰', '兑': '☱', '离': '☲', '震': '☳',
  '巽': '☴', '坎': '☵', '艮': '☶', '坤': '☷'
};

// 八卦属性
const baGuaInfo = {
  '乾': { element: '金', direction: '西北', trait: '刚健' },
  '兑': { element: '金', direction: '西', trait: '喜悦' },
  '离': { element: '火', direction: '南', trait: '明亮' },
  '震': { element: '木', direction: '东', trait: '震动' },
  '巽': { element: '木', direction: '东南', trait: '入' },
  '坎': { element: '水', direction: '北', trait: '险陷' },
  '艮': { element: '土', direction: '东北', trait: '止' },
  '坤': { element: '土', direction: '西南', trait: '柔顺' }
};

// 六亲
const liuQin = ['父母', '兄弟', '子孙', '妻财', '官鬼', '子孙', '妻财', '官鬼'];

// 地支藏干（简化）
const zangGan = {
  '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'],
  '卯': ['乙'], '辰': ['戊', '乙', '癸'], '巳': ['丙', '庚', '戊'],
  '午': ['丁', '己'], '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'],
  '酉': ['辛'], '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲']
};

/**
 * 抛铜钱模拟
 * 3个铜钱，正面=阳，背面=阴
 * 3正=老阳(变阴)，2正1背=少阳(阳)
 * 3背=老阴(变阳)，2背1正=少阴(阴)
 */
function tossCoin() {
  // 三枚铜钱各自独立：正面(1)=阳，背面(0)=阴
  const heads = [0, 1, 2].reduce((sum) => sum + (Math.random() < 0.5 ? 1 : 0), 0);
  if (heads === 3) return '阳动'; // 老阳（三正，变爻）
  if (heads === 2) return '阴';   // 少阴（二正一背，不变）
  if (heads === 1) return '阳';   // 少阳（一正二背，不变）
  return '阴动';                   // 老阴（三背，变爻）
}

/**
 * 模拟完整六次摇卦
 */
function simulateCoins() {
  const results = [];
  for (let i = 0; i < 6; i++) {
    results.push(tossCoin());
  }
  return results;
}

/**
 * 从输入解析卦象
 * 输入格式：六个0/1/2/3的数字
 * 0=少阳(阳不动)，1=少阴(阴不动)，2=老阳(动)，3=老阴(动)
 */
function parseCoins(input) {
  const results = [];
  for (const char of input) {
    const num = parseInt(char);
    if (num === 0 || num === 1) {
      // 不动爻
      results.push(num === 0 ? '阳' : '阴');
    } else if (num === 2) {
      // 老阳变阴
      results.push('阳动');
    } else if (num === 3) {
      // 老阴变阳
      results.push('阴动');
    }
  }
  return results;
}

/**
 * 根据地支找六亲
 */
function findLiuQin(zhi, riGan) {
  const riEl = getElement(riGan);
  const zhiEl = getElement(zhi);
  
  // 五行生克
  if (riEl === '木') {
    if (zhiEl === '木') return '比肩';
    if (zhiEl === '火') return '食神';
    if (zhiEl === '土') return '偏财';
    if (zhiEl === '金') return '官鬼';
    if (zhiEl === '水') return '印绶';
  } else if (riEl === '火') {
    if (zhiEl === '火') return '比肩';
    if (zhiEl === '土') return '食神';
    if (zhiEl === '金') return '偏财';
    if (zhiEl === '水') return '官鬼';
    if (zhiEl === '木') return '印绶';
  } else if (riEl === '土') {
    if (zhiEl === '土') return '比肩';
    if (zhiEl === '金') return '食神';
    if (zhiEl === '水') return '偏财';
    if (zhiEl === '木') return '官鬼';
    if (zhiEl === '火') return '印绶';
  } else if (riEl === '金') {
    if (zhiEl === '金') return '比肩';
    if (zhiEl === '水') return '食神';
    if (zhiEl === '木') return '偏财';
    if (zhiEl === '火') return '官鬼';
    if (zhiEl === '土') return '印绶';
  } else if (riEl === '水') {
    if (zhiEl === '水') return '比肩';
    if (zhiEl === '木') return '食神';
    if (zhiEl === '火') return '偏财';
    if (zhiEl === '土') return '官鬼';
    if (zhiEl === '金') return '印绶';
  }
  
  return '无';
}

/**
 * 获取五行
 */
function getElement(zhi) {
  const elements = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水'
  };
  return elements[zhi] || '土';
}

/**
 * 生成六爻卦象
 */
function generateLiuYao(coins, riGan, riZhi) {
  // 用时间或给定信息确定卦
  const date = new Date();
  const hour = date.getHours();
  
  // 简化：以下卦+上卦
  const gua64 = ['乾', '坤', '屯', '蒙', '需', '讼', '师', '比',
    '小畜', '履', '泰', '否', '同人', '大有', '谦', '豫',
    '随', '蛊', '临', '观', '噬嗑', '贲', '剥', '复',
    '无妄', '大畜', '颐', '大过', '坎', '离', '咸', '恒',
    '遁', '大壮', '晋', '明夷', '家人', '睽', '蹇', '解',
    '损', '益', '夬', '姤', '萃', '升', '困', '井',
    '革', '鼎', '震', '艮', '渐', '归妹', '丰', '旅',
    '巽', '兑', '涣', '节', '中孚', '小过', '既济', '未济'];
  
  // 动爻组合确定卦
  const dongCount = coins.filter(c => c.includes('动')).length;
  const guaIndex = (dongCount * 6 + coins.filter(c => c === '阳' || c === '阳动').length) % 64;
  const guaName = gua64[guaIndex];
  
  // 世应关系（简化）
  const shiYing = {
    '乾': { shi: '五爻', ying: '二爻' },
    '坤': { shi: '二爻', ying: '五爻' },
    '屯': { shi: '初爻', ying: '四爻' },
    '蒙': { shi: '三爻', ying: '上爻' },
    'default': { shi: '三爻', ying: '上爻' }
  };
  
  const sy = shiYing[guaName] || shiYing['default'];
  
  // 构建爻列表
  const yaoList = coins.map((c, i) => {
    const isYang = c === '阳' || c === '阳动';
    const isDong = c.includes('动');
    const zhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'][i];
    const gan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'][i];
    const liuqin = findLiuQin(zhi, riGan);
    
    return {
      name: yaoNames[i],
      yinYang: isYang ? '阳' : '阴',
      dong: isDong ? '动' : '',
      zhi,
      gan,
      liuqin
    };
  });
  
  return {
    guaName,
    yaoList,
    shiYing: sy,
    dongCount
  };
}

/**
 * 判断吉凶
 */
function judgeFortune(hexagram) {
  const { dongCount, yaoList } = hexagram;
  
  let result;
  if (dongCount === 0) {
    result = '静卦 - 事情稳定，需等待时机';
  } else if (dongCount === 1) {
    result = '独发 - 一件事主导，专注可成';
  } else if (dongCount === 2) {
    result = '双动 - 两件事关联，需协调';
  } else if (dongCount >= 3) {
    result = '多动 - 变数较多，谨慎行事';
  }
  
  // 检查动爻的六亲
  const dongLiuQin = yaoList.filter(y => y.dong === '动').map(y => y.liuqin);
  
  if (dongLiuQin.includes('官鬼')) {
    result += '\n⚠️ 动爻带官鬼 - 谨防小人、压力';
  }
  if (dongLiuQin.includes('妻财')) {
    result += '\n💰 动爻带妻财 - 财运显现或破耗';
  }
  if (dongLiuQin.includes('子孙')) {
    result += '\n🌟 动爻带子孙 - 好事发生，贵人运';
  }
  if (dongLiuQin.includes('父母')) {
    result += '\n📚 动爻带父母 - 文书、合同事宜';
  }
  
  return result;
}

/**
 * 生成报告
 */
function generateReport(hexagram, question = '占卜事宜') {
  const { guaName, yaoList, shiYing, dongCount } = hexagram;
  const guaInfo = baGuaInfo[guaName[0]] || baGuaInfo['乾'];
  
  const fortune = judgeFortune(hexagram);
  
  let report = `
🔮 【六爻预测】

📋 占卜信息
   事项：${question}
   动爻数：${dongCount}个

🎴 卦象
   卦名：${guaName}
   卦性：${guaInfo.trait}

📊 世应关系
   世爻：${shiYing.shi}
   应爻：${shiYing.ying}

📜 六爻排列（从下至上）
`;
  
  yaoList.reverse().forEach((y, i) => {
    const symbol = y.yinYang === '阳' ? '━━' : ' ━ ';
    const dongSymbol = y.dong === '动' ? ' ◯' : '  ';
    report += `   ${y.name} ${symbol}${dongSymbol} ${y.zhi}${y.gan} ${y.liuqin}\n`;
  });
  
  report += `
⚖️ 吉凶判断
${fortune}

💡 建议
${dongCount === 0 ? '静待时机，不宜妄动' : 
  dongCount === 1 ? '专注一事，把握独发之机' : 
  '多事并行，量力而行'}
`;
  
  return report;
}

// 主入口
const args = process.argv.slice(2);

if (args[0] === '--help' || args[0] === '-h') {
  console.log(`
六爻预测

用法:
  node liuyao.js                  # 模拟摇卦
  node liuyao.js 010203          # 指定6个爻(0=阳不动,1=阴不动,2=阳动,3=阴动)
  node liuyao.js 010203 婚姻     # 指定爻+问题

示例:
  node liuyao.js
  node liuyao.js 012013 事业
`);
} else if (args.length >= 1 && /^\d{6}$/.test(args[0])) {
  // 指定爻象
  const coins = parseCoins(args[0]);
  const question = args[1] || '占卜事宜';
  const riGan = '戊'; // 简化处理
  const riZhi = '子';
  const hexagram = generateLiuYao(coins, riGan, riZhi);
  console.log(generateReport(hexagram, question));
} else if (args.length >= 2 && /^\d{6}$/.test(args[0])) {
  // 爻象 + 问题
  const coins = parseCoins(args[0]);
  const question = args.slice(1).join(' ');
  const riGan = '戊';
  const riZhi = '子';
  const hexagram = generateLiuYao(coins, riGan, riZhi);
  console.log(generateReport(hexagram, question));
} else {
  // 模拟摇卦
  console.log('🎲 摇卦中...\n');
  const coins = simulateCoins();
  const question = args.join(' ') || '占卜事宜';
  const riGan = '戊';
  const riZhi = '子';
  const hexagram = generateLiuYao(coins, riGan, riZhi);
  console.log(`📍 摇得：[${coins.join(' ')}]\n`);
  console.log(generateReport(hexagram, question));
}
