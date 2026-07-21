#!/usr/bin/env node
/**
 * 用户档案管理脚本 - 支持家庭成员
 * 保存/读取用户命理数据及家庭成员
 */

const fs = require('fs');
const path = require('path');

const PROFILES_DIR = path.join(__dirname, '../data/profiles');

// 隐私控制：默认脚本输出脱敏，仅在调用者明确传入 --full 时才全量输出。
// 这可以避免在共享终端/CI日志/cron邮件 中意外外露谁的八字、出生信息、家庭成员。
const SHOW_FULL = process.argv.includes('--full');
const SHOW_FULL_HINT = '\n   ⚠ 默认脱敏。如需访问完整信息（仅推荐在个人设备），请追加 --full 并确保未被日志采集。';

function maskName(s) {
  if (!s) return '';
  if (s.length <= 1) return s + '*';
  return s[0] + '*'.repeat(Math.max(1, s.length - 1));
}
function maskBazi(b) {
  if (!b) return '?? ?? ?? ??';
  // 只输出五行属性不外露干支原始值
  const ZHI_ELEM = { '子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水' };
  const cells = ['year','month','day','hour'].map(k => {
    const v = (b[k] || '');
    if (v.length < 2) return '—';
    return ZHI_ELEM[v[1]] || '—';
  });
  return `已配置（五行序列：${cells.join('-')}）`;
}
function maskBirthDate(d) {
  if (!d) return '';
  // 仅保留年，隐藏月日
  const m = String(d).match(/^(\d{4})/);
  return m ? `${m[1]}-**-**` : '****';
}
function renderBazi(b) {
  if (SHOW_FULL) return `${b?.year || '?'} ${b?.month || ''} ${b?.day || ''} ${b?.hour || ''}`;
  return maskBazi(b);
}

// 确保目录存在
if (!fs.existsSync(PROFILES_DIR)) {
  fs.mkdirSync(PROFILES_DIR, { recursive: true });
}

/**
 * 获取用户档案路径
 */
function getProfilePath(userId) {
  return path.join(PROFILES_DIR, `${userId}.json`);
}

/**
 * 读取用户档案
 */
function loadProfile(userId) {
  const filePath = getProfilePath(userId);
  if (!fs.existsSync(filePath)) {
    return null;
  }
  const data = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(data);
}

/**
 * 保存用户档案
 */
function saveProfile(userId, data) {
  const filePath = getProfilePath(userId);
  const profile = {
    ...data,
    userId,
    updatedAt: new Date().toISOString().split('T')[0]
  };
  fs.writeFileSync(filePath, JSON.stringify(profile, null, 2), 'utf8');
  return profile;
}

/**
 * 更新档案字段
 */
function updateProfile(userId, field, value) {
  const profile = loadProfile(userId) || {};
  
  // 处理嵌套字段如 "family.spouse.name"
  const fields = field.split('.');
  let current = profile;
  
  for (let i = 0; i < fields.length - 1; i++) {
    if (!current[fields[i]]) {
      current[fields[i]] = {};
    }
    current = current[fields[i]];
  }
  
  current[fields[fields.length - 1]] = value;
  
  saveProfile(userId, profile);
  console.log(`✅ 已更新: ${field} = ${value}`);
}

/**
 * 添加家庭成员
 */
function addFamilyMember(userId, type, name, data = {}) {
  const profile = loadProfile(userId);
  if (!profile) {
    console.log(`❌ 用户档案不存在: ${userId}`);
    return;
  }
  
  if (!profile.family) {
    profile.family = {};
  }
  
  const memberData = {
    name,
    profile: {
      birthDate: data.birthDate || '待录入',
      birthTime: data.birthTime || '待录入',
      birthPlace: data.birthPlace || '',
      gender: data.gender || '',
      lunarBirth: data.lunarBirth || ''
    },
    bazi: {
      year: data.year || '',
      month: data.month || '',
      day: data.day || '',
      hour: data.hour || '',
      dayStem: data.dayStem || '',
      zodiac: data.zodiac || '',
      sect: data.sect || '晚子时',
      source: 'pending'
    },
    relationship: type,
    addedAt: new Date().toISOString().split('T')[0]
  };
  
  if (type === 'children') {
    if (!profile.family.children) {
      profile.family.children = [];
    }
    profile.family.children.push(memberData);
    console.log(`✅ 已添加子女: ${name}`);
  } else {
    profile.family[type] = memberData;
    console.log(`✅ 已添加${type}: ${name}`);
  }
  
  saveProfile(userId, profile);
}

/**
 * 添加子女
 */
function addChild(userId, name, birthDate, gender) {
  const profile = loadProfile(userId);
  if (!profile) {
    console.log(`❌ 用户档案不存在: ${userId}`);
    return;
  }
  
  const child = {
    name,
    profile: {
      birthDate: birthDate || '待录入',
      birthTime: '待录入',
      birthPlace: '',
      gender: gender || '',
      lunarBirth: ''
    },
    bazi: {
      year: '',
      month: '',
      day: '',
      hour: '',
      source: 'pending'
    },
    relationship: '子女',
    addedAt: new Date().toISOString().split('T')[0]
  };
  
  if (!profile.family) profile.family = {};
  if (!profile.family.children) profile.family.children = [];
  
  profile.family.children.push(child);
  saveProfile(userId, profile);
  console.log(`✅ 已添加子女: ${name} (${gender || '待定'})`);
}

/**
 * 列出家庭成员
 */
function listFamilyMembers(userId) {
  const profile = loadProfile(userId);
  if (!profile) {
    console.log(`❌ 用户档案不存在: ${userId}`);
    return;
  }
  
  console.log(`\n👪 家庭成员列表 (${profile.name})\n`);
  
  const { family } = profile;
  
  if (family?.spouse?.name && family.spouse.name !== '配偶') {
    console.log(`  👫 配偶: ${SHOW_FULL ? family.spouse.name : maskName(family.spouse.name)}`);
    console.log(`     八字: ${renderBazi(family.spouse.bazi)}`);
  }
  
  if (family?.father?.name && family.father.name !== '父亲') {
    console.log(`  👨 父亲: ${SHOW_FULL ? family.father.name : maskName(family.father.name)}`);
    console.log(`     八字: ${renderBazi(family.father.bazi)}`);
  }
  
  if (family?.mother?.name && family.mother.name !== '母亲') {
    console.log(`  👩 母亲: ${SHOW_FULL ? family.mother.name : maskName(family.mother.name)}`);
    console.log(`     八字: ${renderBazi(family.mother.bazi)}`);
  }
  
  if (family?.children?.length > 0) {
    console.log(`  👶 子女 (${family.children.length}):`);
    family.children.forEach((child, i) => {
      console.log(`     ${i + 1}. ${SHOW_FULL ? child.name : maskName(child.name)} (${child.profile?.gender || '待定'})`);
      console.log(`        出生: ${SHOW_FULL ? (child.profile?.birthDate || '待录入') : maskBirthDate(child.profile?.birthDate)}`);
      console.log(`        八字: ${renderBazi(child.bazi)}`);
    });
  }
  
  if (!family?.spouse && !family?.father && !family?.mother && (!family?.children || family.children.length === 0)) {
    console.log(`  (暂无家庭成员记录)`);
  }
  
  console.log('');
}

/**
 * 显示完整档案
 */
function showProfile(userId) {
  const profile = loadProfile(userId);
  if (!profile) {
    console.log(`❌ 用户档案不存在: ${userId}`);
    return;
  }
  
  console.log('\n📋 用户档案' + (SHOW_FULL ? '' : '（默认脱敏）') + '\n');
  console.log(`ID: ${SHOW_FULL ? profile.userId : maskName(profile.userId)}`);
  console.log(`姓名: ${SHOW_FULL ? profile.name : maskName(profile.name)}`);
  console.log(`出生: ${SHOW_FULL ? `${profile.profile?.birthDate || ''} ${profile.profile?.birthTime || ''}` : maskBirthDate(profile.profile?.birthDate)}`);
  console.log(`地点: ${SHOW_FULL ? (profile.profile?.birthPlace || '') : (profile.profile?.birthPlace ? '已填写（已脱敏）' : '')}`);
  console.log(`性别: ${profile.profile?.gender || ''}`);
  
  console.log('\n🧮 八字');
  console.log(`  ${renderBazi(profile.bazi)}`);
  if (SHOW_FULL) {
    console.log(`  日主: ${profile.bazi?.dayStem}`);
    console.log(`  生肖: ${profile.bazi?.zodiac}`);
  } else {
    console.log(`  日主与生肖已隐藏（--full 可查看）`);
  }
  
  if (profile.ziwei) {
    console.log('\n✨ 紫微');
    console.log(`  命宫: ${SHOW_FULL ? profile.ziwei.mingGong : '已配置（脱敏）'}`);
    if (SHOW_FULL) console.log(`  命主: ${profile.ziwei.mingZhu}`);
  }
  
  if (!SHOW_FULL) console.error(SHOW_FULL_HINT);
  listFamilyMembers(userId);
}

/**
 * 列出所有用户
 */
function listProfiles() {
  const files = fs.readdirSync(PROFILES_DIR).filter(f => f.endsWith('.json'));
  console.log('\n📋 用户列表' + (SHOW_FULL ? '' : '（默认脱敏）') + '\n');
  
  files.forEach(f => {
    const userId = f.replace('.json', '');
    const data = loadProfile(userId);
    if (SHOW_FULL) {
      console.log(`  ${userId} | ${data?.name || '未知'} | ${data?.profile?.birthDate || '未知'}`);
    } else {
      console.log(`  ${maskName(userId)} | ${maskName(data?.name || '未知')} | ${maskBirthDate(data?.profile?.birthDate)}`);
    }
  });
  
  console.log(`\n共 ${files.length} 个用户\n`);
  if (!SHOW_FULL) console.error(SHOW_FULL_HINT);
}

/**
 * 删除档案
 *
 * v1.1.8 起：
 *  - 默认**软删除**：将 <userId>.json 重命名为 <userId>.json.deleted-<timestamp>，
 *    保留在 data/profiles/ 同目录内，用户 30 天内可手动恢复。
 *  - 要求**二次确认**：必须传入 --yes 或交互式输入 'DELETE' 文本；否则拒绝。
 *  - 可选 `--purge` 强制**硬删除**（fs.unlink），仅在用户明确同意丢弃可恢复性时使用。
 *  - 在删除前试图调用 push-toggle.js disablePush，防止遗留的 cron 依然调度运行，造成 stale-push 问题。
 *
 * 警告：本指令处理的是出生信息 / 个人八字 / 家庭成员资料等**高敏感个人信息**，
 * 请勿在批量脚本 / CI 中无人值守地调用。
 */
function _readlineConfirm(promptText) {
  // 同步读取一行 stdin，避引 readline 异步依赖。
  try {
    process.stdout.write(promptText);
    const fdRead = process.stdin.fd;
    const buf = Buffer.alloc(1);
    let line = '';
    while (true) {
      try {
        const n = fs.readSync(fdRead, buf, 0, 1);
        if (n === 0) break;
        const ch = buf.toString('utf8', 0, 1);
        if (ch === '\n') break;
        if (ch === '\r') continue;
        line += ch;
        if (line.length > 64) break;
      } catch (e) {
        // EAGAIN 或 stdin 不可读（非 tty），退出
        return null;
      }
    }
    return line.trim();
  } catch (_) {
    return null;
  }
}

function deleteProfile(userId, opts = {}) {
  const filePath = getProfilePath(userId);
  if (!fs.existsSync(filePath)) {
    console.log(`❌ 档案不存在: ${userId}`);
    return;
  }

  const yesFlag = !!opts.yes;
  const purgeFlag = !!opts.purge;

  // 警告体
  console.error(`⚠️  即将${purgeFlag ? '硬删除（不可恢复）' : '软删除（可 30 天内手动恢复）'}该用户档案：${userId}`);
  console.error('⚠️  该文件包含出生信息、八字、可选家庭成员资料与互动日志。');
  if (purgeFlag) {
    console.error('⚠️  已设置 --purge：文件将被彻底从磁盘上移除，不可恢复。');
  } else {
    console.error('⚠️  软删除后文件仍位于 data/profiles/ 下，带 .deleted-<时间戳> 后缀；如需恢复，只需重命名去掉后缀即可。');
  }

  // 二次确认：--yes 或 交互式输入 'DELETE'
  if (!yesFlag) {
    const tty = process.stdin.isTTY;
    if (!tty) {
      console.error('❌ 非交互式环境下拒绝删除：请重新运行并加上 --yes 明确表示同意（可同时加 --purge 表示硬删除）。');
      return;
    }
    const ans = _readlineConfirm(`请输入 'DELETE' 以确认删除 ${userId}，或输入其他任意字符取消： `);
    if (ans !== 'DELETE') {
      console.log('✖ 已取消删除。');
      return;
    }
  }

  // 先关闭推送，避免遗留 cron
  try {
    const { disablePush } = require('./push-toggle');
    if (typeof disablePush === 'function') {
      try { disablePush(userId); } catch (e) { /* 静默 */ }
    }
  } catch (e) {
    // push-toggle 不可用，不阫塞主流程
  }

  if (purgeFlag) {
    fs.unlinkSync(filePath);
    console.log(`✅ 已硬删除: ${userId}`);
    return;
  }

  // 软删除 = 重命名
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const tomb = `${filePath}.deleted-${ts}`;
  fs.renameSync(filePath, tomb);
  console.log(`✅ 已软删除为：${path.basename(tomb)}`);
  console.log('   如需恢复，请去掉 .deleted-<时间戳> 后缀；如需彻底丢弃，请手动删除该备份文件。');
}

// 主入口
const args = process.argv.slice(2);
const command = args[0];

switch (command) {
  case 'show':
  case 'load':
    if (args[1]) {
      showProfile(args[1]);
    } else {
      console.log('用法: node profile.js show <userId>');
    }
    break;
    
  case 'list':
    listProfiles();
    break;
    
  case 'save':
    if (args.length < 4) {
      console.log('用法: node profile.js save <userId> <field> <value>');
      console.log('示例: node profile.js save 123 name 张三');
      console.log('      node profile.js save 123 bazi.day 戊子');
    } else {
      updateProfile(args[1], args[2], args[3]);
    }
    break;
    
  case 'add':
    // node profile.js add <userId> <type> <name> [birthDate] [gender]
    if (args.length < 4) {
      console.log('用法:');
      console.log('  node profile.js add <userId> spouse <name> [出生日期] [性别]');
      console.log('  node profile.js add <userId> father <name> [出生日期]');
      console.log('  node profile.js add <userId> mother <name> [出生日期]');
      console.log('  node profile.js add <userId> child <name> <出生日期> <性别>');
      console.log('');
      console.log('示例:');
      console.log('  node profile.js add 123 spouse 李四 1990-05-15 女');
      console.log('  node profile.js add 123 child 子女姓名 2020-01-01 男');
    } else {
      const userId = args[1];
      const type = args[2];
      const name = args[3];
      
      if (type === 'child') {
        const birthDate = args[4];
        const gender = args[5];
        addChild(userId, name, birthDate, gender);
      } else {
        addFamilyMember(userId, type, name, {
          birthDate: args[4],
          gender: type === 'spouse' ? (args[5] || '女') : (args[4] ? '男' : '')
        });
      }
    }
    break;
    
  case 'family':
    if (args[1]) {
      listFamilyMembers(args[1]);
    } else {
      console.log('用法: node profile.js family <userId>');
    }
    break;
    
  case 'delete':
    if (args[1]) {
      // --yes / -y 跳过交互式二次确认（批量环境下主动表示同意）
      // --purge 表示硬删除（不可恢复）；不加则默认软删除
      const opts = {
        yes: args.includes('--yes') || args.includes('-y'),
        purge: args.includes('--purge')
      };
      deleteProfile(args[1], opts);
    } else {
      console.log('用法: node profile.js delete <userId> [--yes] [--purge]');
      console.log('  --yes / -y    跳过交互式确认（批量场景主动同意）');
      console.log('  --purge       硬删除不可恢复；默认为软删除（可手动恢复）');
    }
    break;
    
  default:
    console.log(`
🗂️ 用户档案管理 (支持家庭成员)

用法:
  node profile.js show <userId>              显示完整档案
  node profile.js list                        列出所有用户
  node profile.js save <userId> <field> <value>  保存字段
  node profile.js add <userId> <type> <name> [参数]  添加家庭成员
  node profile.js family <userId>            显示家庭成员
  node profile.js delete <userId>            删除档案

家庭成员类型:
  spouse   - 配偶
  father   - 父亲
  mother   - 母亲
  child    - 子女

示例:
  # 查看档案
  node profile.js show 123456

  # 添加配偶
  node profile.js add 123456 spouse 配偶姓名 1990-05-15 女

  # 添加子女
  node profile.js add 123456 child 子女姓名 2020-01-01 男

  # 添加父亲
  node profile.js add 123456 father 父亲姓名 1950-03-15

  # 查看家庭成员
  node profile.js family 123456

  # 保存八字
  node profile.js save 123456 family.spouse.bazi.year 庚午
`);
}

module.exports = { loadProfile, saveProfile, updateProfile, addFamilyMember, addChild, listFamilyMembers, showProfile };
