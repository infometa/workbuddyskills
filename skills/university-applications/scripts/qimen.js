#!/usr/bin/env node
/**
 * 奇门遁甲排盘脚本
 * 支持：时间起局、择日选时
 */

// 地支
const diZhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

// 九星
const nineStars = [
  { name: '天蓬', symbol: '⭐', element: '水', trait: '凶星', position: 1 },
  { name: '天任', symbol: '⭐', element: '土', trait: '凶星', position: 8 },
  { name: '天冲', symbol: '⭐', element: '木', trait: '吉星', position: 3 },
  { name: '天辅', symbol: '⭐', element: '木', trait: '吉星', position: 4 },
  { name: '天英', symbol: '⭐', element: '火', trait: '凶星', position: 9 },
  { name: '天芮', symbol: '⭐', element: '土', trait: '凶星', position: 2 },
  { name: '天柱', symbol: '⭐', element: '金', trait: '凶星', position: 7 },
  { name: '天心', symbol: '⭐', element: '金', trait: '吉星', position: 6 },
  { name: '天禽', symbol: '⭐', element: '土', trait: '大吉', position: 5 }
];

// 八门
const eightDoors = [
  { name: '休门', symbol: '🏠', element: '水', trait: '休息、平稳', position: 1 },
  { name: '生门', symbol: '🌱', element: '土', trait: '生长、财运', position: 8 },
  { name: '伤门', symbol: '💔', element: '木', trait: '受伤、变动', position: 3 },
  { name: '杜门', symbol: '🔒', element: '木', trait: '阻碍、保密', position: 4 },
  { name: '景门', symbol: '🔥', element: '火', trait: '文化、虚假', position: 9 },
  { name: '死门', symbol: '💀', element: '土', trait: '死亡、凶险', position: 2 },
  { name: '惊门', symbol: '😱', element: '金', trait: '惊恐、口舌', position: 7 },
  { name: '开门', symbol: '🚪', element: '金', trait: '开创、顺利', position: 6 }
];

// 三奇
const sanQi = ['乙', '丙', '丁'];

// 六仪
const liuYi = ['戊', '己', '庚', '辛', '壬', '癸'];

// 九宫（后天八卦方位）
const ninePalaces = [
  { num: 9, gua: '离', zhi: '午', direction: '南' },
  { num: 4, gua: '巽', zhi: '卯', direction: '东南' },
  { num: 2, gua: '坤', zhi: '未', direction: '西南' },
  { num: 3, gua: '震', zhi: '卯', direction: '东' },
  { num: 5, gua: '中', zhi: '戌', direction: '中' },
  { num: 1, gua: '坎', zhi: '子', direction: '北' },
  { num: 7, gua: '兑', zhi: '酉', direction: '西' },
  { num: 8, gua: '艮', zhi: '丑', direction: '东北' },
  { num: 6, gua: '乾', zhi: '戌', direction: '西北' }
];

/**
 * 判断阴遁还是阳遁
 * 冬至 → 夏至：阳遁
 * 夏至 → 冬至：阴遁
 */
function isYangDun(date = new Date()) {
  const month = date.getMonth() + 1;
  const day = date.getDate();
  
  // 节气粗略判断
  // 夏至在6月21日，冬至在12月22日
  const yearDay = date.getMonth() * 30 + day;
  const summerSolstice = 5 * 30 + 21; // 约6月21日
  const winterSolstice = 11 * 30 + 22; // 约12月22日
  
  if (yearDay < summerSolstice || yearDay > winterSolstice) {
    return true; // 阳遁（春夏）
  }
  return false; // 阴遁（秋冬）
}

/**
 * 计算值符星（以2024-01-01为基准，按时辰连续推算）
 */
function getZhiFu(date, isYang) {
  const baseDate = new Date('2024-01-01T00:00:00');
  const diffDays = Math.floor((date - baseDate) / (1000 * 60 * 60 * 24));
  const hour = date.getHours();
  const shichen = Math.floor((hour + 1) / 2) % 12; // 当前时辰序号
  const idx = ((diffDays * 12 + shichen) % 9 + 9) % 9;
  // 阳遁顺布，阴遁逆布
  return isYang ? nineStars[idx] : nineStars[(9 - idx) % 9];
}

/**
 * 计算值使门（以2024-01-01为基准，按时辰连续推算）
 */
function getZhiShi(date, isYang) {
  const baseDate = new Date('2024-01-01T00:00:00');
  const diffDays = Math.floor((date - baseDate) / (1000 * 60 * 60 * 24));
  const hour = date.getHours();
  const shichen = Math.floor((hour + 1) / 2) % 12;
  const idx = ((diffDays * 12 + shichen) % 8 + 8) % 8;
  return isYang ? eightDoors[idx] : eightDoors[(8 - idx) % 8];
}

/**
 * 排布九宫
 */
function arrangePalaces(isYang, zhiFu) {
  const palaces = [];
  
  // 阳遁顺布，阴遁逆布
  const order = isYang ? [1, 2, 3, 4, 5, 6, 7, 8, 9] : [9, 8, 7, 6, 5, 4, 3, 2, 1];
  
  // 九宫对应
  const palaceMap = {
    1: { gua: '坎', zhi: '子', direction: '北' },
    2: { gua: '坤', zhi: '未', direction: '西南' },
    3: { gua: '震', zhi: '卯', direction: '东' },
    4: { gua: '巽', zhi: '辰', direction: '东南' },
    5: { gua: '中', zhi: '戌', direction: '中' },
    6: { gua: '乾', zhi: '戌', direction: '西北' },
    7: { gua: '兑', zhi: '酉', direction: '西' },
    8: { gua: '艮', zhi: '丑', direction: '东北' },
    9: { gua: '离', zhi: '午', direction: '南' }
  };
  
  return order.map((num, index) => ({
    position: index + 1,
    num,
    ...palaceMap[num]
  }));
}

/**
 * 安九星到九宫
 */
function arrangeStars(palaces, isYang, zhiFu) {
  const starIndex = nineStars.findIndex(s => s.name === zhiFu.name);
  
  const result = palaces.map((palace, i) => {
    const offset = isYang ? i : (8 - i);
    const starIdx = (starIndex + offset) % 9;
    const star = nineStars[starIdx];
    
    // 天禽永远在中五宫
    if (palace.num === 5) {
      return { ...palace, star: nineStars[4] };
    }
    
    return { ...palace, star };
  });
  
  return result;
}

/**
 * 安八门到九宫
 */
function arrangeDoors(palaces, isYang, zhiShi) {
  const doorIndex = eightDoors.findIndex(d => d.name === zhiShi.name);
  
  const result = palaces.map((palace, i) => {
    const offset = isYang ? i : (8 - i);
    const doorIdx = (doorIndex + offset) % 8;
    const door = eightDoors[doorIdx];
    
    // 死门永远在坤二宫
    if (palace.num === 2) {
      return { ...palace, door: eightDoors[5] };
    }
    
    return { ...palace, door };
  });
  
  return result;
}

/**
 * 找三奇方位
 */
function findSanQi(palaces) {
  const results = [];
  
  palaces.forEach(p => {
    if (p.star && p.door) {
      const starName = p.star.name;
      // 乙奇在坎、离；丙奇在乾、兑；丁奇在震、巽
      if (starName === '天任' || starName === '天英') {
        results.push({ qi: '乙', palace: p });
      } else if (starName === '天心' || starName === '天柱') {
        results.push({ qi: '丙', palace: p });
      } else if (starName === '天冲' || starName === '天辅') {
        results.push({ qi: '丁', palace: p });
      }
    }
  });
  
  return results;
}

/**
 * 判断吉凶
 */
function judgeFortune(palace, sanQiCount) {
  const star = palace.star;
  const door = palace.door;
  
  if (!star || !door) return '未知';
  
  const starGood = ['天冲', '天辅', '天心', '天禽'].includes(star.name);
  const doorGood = ['生门', '休门', '开门', '景门'].includes(door.name);
  
  if (starGood && doorGood) return '大吉';
  if (starGood || doorGood) return '中吉';
  if (door.name === '死门' || door.name === '惊门') return '大凶';
  return '凶';
}

/**
 * 生成报告
 */
function generateReport(date, palaces, zhiFu, zhiShi, isYang, sanQiList) {
  const hour = date.getHours();
  const hourZhi = diZhi[Math.floor((hour + 1) / 2) % 12];
  const hourElement = { '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水' }[hourZhi];
  
  let report = `
🎴 【奇门遁甲盘】

📋 基本信息
   日期：${date.toLocaleDateString('zh-CN')}
   时辰：${hourZhi}时
   遁局：${isYang ? '阳遁' : '阴遁'}（${isYang ? '冬至→夏至' : '夏至→冬至'}）
   值符：${zhiFu.name}
   值使：${zhiShi.name}

📊 九宫排布
`;
  
  // 按洛书顺序展示
  const luoshu = [4, 9, 2, 3, 5, 1, 7, 8, 6]; // 巽4 离9 坤2 震3 中5 坎1 兑7 艮8 乾6
  
  report += '\n       【东南】【南】【西南】\n';
  report += '       ';
  
  for (let i = 0; i < 9; i++) {
    const row = Math.floor(i / 3);
    const col = i % 3;
    const palace = palaces.find(p => p.num === luoshu[i]);
    
    if (palace) {
      const starSymbol = palace.star ? palace.star.name.substring(1, 3) : '  ';
      const doorSymbol = palace.door ? palace.door.name.charAt(0) : ' ';
      report += `${starSymbol}${doorSymbol}  `;
    } else {
      report += '    ';
    }
    
    if (col === 2 && row === 0) report += '\n       【东】【中】【西】\n       ';
    if (col === 2 && row === 1) report += '\n       【东北】【北】【西北】\n       ';
  }
  
  // 详细宫位信息
  report += '\n\n📍 各宫位详情\n';
  report += '━━━━━━━━━━━━━━━━━━━━\n';
  
  palaces.forEach(p => {
    const guaInfo = ninePalaces.find(n => n.num === p.num) || {};
    const fortune = judgeFortune(p, 0);
    const fortuneSymbol = fortune.includes('吉') ? '✅' : fortune.includes('凶') ? '❌' : '⚠️';
    
    report += `\n【${p.num}宫】${p.direction || guaInfo.direction || ''} ${guaInfo.gua || ''} ${guaInfo.zhi || ''}\n`;
    if (p.star) report += `   九星：${p.star.name}（${p.star.element}，${p.star.trait}）\n`;
    if (p.door) report += `   八门：${p.door.name}（${p.door.trait}）\n`;
    report += `   吉凶：${fortuneSymbol} ${fortune}\n`;
  });
  
  // 三奇位置
  if (sanQiList.length > 0) {
    report += '\n✨ 三奇方位\n';
    sanQiList.forEach(sq => {
      report += `   ${sq.qi}奇在${sq.palace.direction}${sq.palace.num}宫\n`;
    });
  }
  
  // 最佳方位
  const goodPalaces = palaces.filter(p => judgeFortune(p, 0).includes('吉'));
  if (goodPalaces.length > 0) {
    report += '\n🌟 最佳方位\n';
    goodPalaces.forEach(p => {
      report += `   ${p.direction}（${p.num}宫）- ${p.star?.name || ''}${p.door?.name || ''}\n`;
    });
  }
  
  // 值符使跟随
  report += `\n⚡ 值符${zhiFu.name}运行，值使${zhiShi.name}值事\n`;
  
  report += `
💡 综合建议
   ${isYang ? '阳遁宜进，进攻性强' : '阴遁宜退，防守为主'}
   值符${zhiFu.name}为核心，${zhiShi.name}为动向
   ${goodPalaces.length > 0 ? `吉利方位：${goodPalaces.map(p => p.direction).join('、')}` : '宜静不宜动'}
`;
  
  return report;
}

// 主入口
const args = process.argv.slice(2);

if (args[0] === '--help' || args[0] === '-h') {
  console.log(`
奇门遁甲排盘

用法:
  node qimen.js                 # 当前时间起局
  node qimen.js 2026-03-24     # 指定日期（默认当前时辰）
  node qimen.js 2026-03-24 15  # 指定日期和时辰

示例:
  node qimen.js
  node qimen.js 2026-03-24
  node qimen.js 2026-03-24 15
`);
} else {
  let date;
  let hour;
  
  if (args.length === 0) {
    date = new Date();
  } else if (args.length === 1) {
    date = new Date(args[0]);
    if (isNaN(date.getTime())) {
      console.error('日期格式无效');
      process.exit(1);
    }
  } else if (args.length >= 2) {
    date = new Date(args[0]);
    if (isNaN(date.getTime())) {
      console.error('日期格式无效');
      process.exit(1);
    }
    hour = parseInt(args[1]);
    if (hour >= 0 && hour <= 23) {
      date.setHours(hour);
    }
  }
  
  const isYang = isYangDun(date);
  const zhiFu = getZhiFu(date, isYang);
  const zhiShi = getZhiShi(date, isYang);
  const palaces = arrangePalaces(isYang, zhiFu);
  const palacesWithStars = arrangeStars(palaces, isYang, zhiFu);
  const palacesWithAll = arrangeDoors(palacesWithStars, isYang, zhiShi);
  const sanQiList = findSanQi(palacesWithAll);
  
  console.log(generateReport(date, palacesWithAll, zhiFu, zhiShi, isYang, sanQiList));
}
