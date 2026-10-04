#!/usr/bin/env node
/**
 * 按票种换算 Amount（元 → 分），并提示该票种要求的取值口径。
 *
 * 用法：
 *   node calc-amount.mjs <票种代码> <金额·元>
 *   node calc-amount.mjs 32 9.00      # 数电普票：价税合计 9.00 元 → 900
 *   node calc-amount.mjs 01 8.26      # 增值税专票：不含税 8.26 元 → 826
 *   node calc-amount.mjs 03 120000    # 机动车：车价合计 → 12000000
 *
 * 口径数据源：references/invoice-types.md 主表第 5 列（唯一数据源，改表即生效）。
 *
 * 退出码：0 正常；1 参数错或票种不在枚举中
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const [type, yuanRaw] = process.argv.slice(2);
if (!type || yuanRaw === undefined) {
  console.error('用法: node calc-amount.mjs <票种代码> <金额·元>   例: node calc-amount.mjs 32 9.00');
  process.exit(1);
}
const yuan = Number(yuanRaw);
if (!Number.isFinite(yuan) || yuan < 0) {
  console.error(`金额必须是非负数（单位元），当前为 ${yuanRaw}`);
  process.exit(1);
}

/** 读取票种主表：代码 / 中文名称 / 发票代码必填 / 校验码必填 / Amount 口径 */
function loadTypes() {
  const p = join(dirname(fileURLToPath(import.meta.url)), '..', 'references', 'invoice-types.md');
  const md = readFileSync(p, 'utf8');
  const start = md.indexOf('## 主表');
  if (start < 0) return new Map();
  const rest = md.slice(start);
  const end = rest.indexOf('\n## ', 10);
  const block = end < 0 ? rest : rest.slice(0, end);
  const map = new Map();
  for (const line of block.split('\n')) {
    const l = line.trim();
    if (!l.startsWith('|')) continue;
    const cells = l
      .split('|')
      .slice(1, -1)
      .map((c) => c.replace(/\*\*/g, '').trim());
    if (cells.length < 5 || /^-+$/.test(cells[0]) || cells[0] === '代码') continue;
    map.set(cells[0], { name: cells[1], needCode: cells[2], needCheck: cells[3], amountRule: cells[4] });
  }
  return map;
}

const types = loadTypes();
const meta = types.get(String(type).padStart(2, '0')) || types.get(String(type));
if (!meta) {
  console.error(`票种 ${type} 不在枚举表中；请读 references/invoice-types.md 查看全部票种。`);
  process.exit(1);
}

const cents = Math.round(yuan * 100);
const rule = meta.amountRule || '-';

console.log(`票种        : ${String(type).padStart(2, '0')} ${meta.name}`);
console.log(`Amount 口径 : ${rule}`);
console.log(`金额(元)    : ${yuan}`);
console.log(`Amount(分)  : ${cents}`);

if (/不含税/.test(rule)) {
  console.log('\n⚠️ 该票种要求【不含税金额】——请取票面「金额」栏，不要用「价税合计」。');
} else if (/车价/.test(rule)) {
  console.log('\n⚠️ 该票种要求【车价合计】——请取票面「车价合计」栏。');
} else if (/价税合计/.test(rule)) {
  console.log('\n✅ 该票种取票面「价税合计」栏，无需换算税率。');
}
if (/可空/.test(rule)) {
  console.log('   该票种金额可为空：拿不到不含税金额时传 0。');
}
if (/^否/.test(meta.needCheck || '')) {
  console.log(`   校验码：可省略（传 ""）。`);
} else {
  console.log(`   校验码：${meta.needCheck}`);
}
