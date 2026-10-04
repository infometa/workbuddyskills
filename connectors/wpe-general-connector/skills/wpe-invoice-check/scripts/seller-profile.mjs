#!/usr/bin/env node
/**
 * 销方企业画像 —— 从「票面要素 + 统一社会信用代码规则」推断销方主体画像。
 *
 * ⚠️ 定位：这是**票面/代码侧画像**，不是工商登记查询。
 *    注册资本、成立日期、股东、经营状态、参保人数等要素**票面上没有**，
 *    脚本不会编造；需要时须走外部工商检索（WebSearch 等）并明确标注来源。
 *
 * 用法：
 *   node seller-profile.mjs --name "重庆市江津区岭寓物业服务有限公司" --taxno 91500116MAABP9NU8J \
 *        [--goods "*生产生活服务*车辆停放服务"] [--tax-class-code 3040502020200000000] \
 *        [--tax-rate 9] [--total 9.00] [--net 8.26] [--tax 0.74] [--date 20260916] \
 *        [--invoice-type 32] [--json]
 *
 *   # 位置参数简写
 *   node seller-profile.mjs <销方名称> <销方税号> [税收分类编码] [税率] [价税合计元] [开票日期yyyymmdd]
 *
 *   # 从查验结果取数（连接器 call_internal_api 返回的票面 Data 即可）
 *   node seller-profile.mjs --check-json /tmp/check.json [--json]
 *
 * 税率写法兼容：9 / 9% / 0.09 都按 9% 处理。
 *
 * 数据源（改动即生效，无需改脚本）：
 *   references/region-codes.md        行政区划（最长前缀：6位区县 → 4位地市 → 2位省级）
 *   references/tax-class-industry.md  税收分类编码前缀 → 行业归类
 *   references/industry-keywords.md   名称行业词 → 国民经济行业门类 + 组织形式后缀
 *
 * 退出码：0 正常输出；1 参数不足（至少需要名称或税号之一）
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REF = join(dirname(fileURLToPath(import.meta.url)), '..', 'references');

/** 通用 markdown 表格解析：取 `## section` 小节（section 为 null 时取文首第一段）的所有表格行。 */
function loadTable(file, section = null) {
  let md;
  try {
    md = readFileSync(join(REF, file), 'utf8');
  } catch {
    return [];
  }
  let block = md;
  if (section) {
    const start = md.indexOf(`## ${section}`);
    if (start < 0) return [];
    const rest = md.slice(start + section.length + 3);
    const end = rest.indexOf('\n## ');
    block = end < 0 ? rest : rest.slice(0, end);
  } else {
    const end = block.indexOf('\n## ');
    block = end < 0 ? block : block.slice(0, end);
  }
  return block
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.startsWith('|'))
    .map((l) =>
      l
        .split('|')
        .slice(1, -1)
        .map((c) => c.replace(/\*\*/g, '').trim()),
    )
    .filter((cells) => cells.length >= 2 && !/^-+$/.test(cells[0]) && !/^(代码|关键词|前缀|后缀)$/.test(cells[0]));
}

const REGIONS = loadTable('region-codes.md');
const TAXCLASS = loadTable('tax-class-industry.md');
const INDUSTRY = loadTable('industry-keywords.md');
const ORGFORM = loadTable('industry-keywords.md', '组织形式后缀（名称结构解析用）');

// ---------------- 统一社会信用代码（GB 32100-2015） ----------------
const CC_CHARS = '0123456789ABCDEFGHJKLMNPQRTUWXY'; // 31 个字符（去掉 I O S V Z）
const CC_WEIGHTS = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28];

/** 校验 18 位统一社会信用代码的校验位；非 18 位返回 null。 */
function checkCreditCode(code) {
  if (!/^[0-9A-Z]{18}$/.test(code)) return null;
  let sum = 0;
  for (let i = 0; i < 17; i++) {
    const v = CC_CHARS.indexOf(code[i]);
    if (v < 0) return null;
    sum += v * CC_WEIGHTS[i];
  }
  const expect = CC_CHARS[(31 - (sum % 31)) % 31];
  return { expected: expect, actual: code[17], ok: expect === code[17] };
}

/** 第 1 位：登记管理部门；第 2 位：机构类别（随登记管理部门不同而不同）。 */
const DEPT = {
  1: '机构编制管理部门',
  2: '外交部门',
  3: '司法行政部门',
  4: '文化部门（历史码）',
  5: '民政部门',
  6: '旅游部门（历史码）',
  7: '宗教事务管理部门',
  8: '工商行政管理（历史码）',
  9: '工商 / 市场监督管理部门',
  A: '中央军委改革和编制办公室',
  N: '农业部门',
  Y: '其他管理部门',
};
const ORG_TYPE = {
  9: { 1: '企业', 2: '个体工商户', 3: '农民专业合作社', 9: '其他（工商登记）' },
  1: { 1: '机关', 2: '事业单位', 3: '编办直接管理机构编制的群众团体', 9: '其他（机构编制）' },
  5: { 1: '社会团体', 2: '民办非企业单位', 3: '基金会', 9: '其他（民政登记）' },
  3: {
    1: '基层法律服务所',
    2: '律师执业机构',
    3: '公证机构',
    4: '司法鉴定机构',
    5: '仲裁委员会',
  },
};

// ---------------- 行政区划 ----------------
const REGION_SKIP = new Set(['市辖区', '县', '省直辖县级行政区划', '自治区直辖县级行政区划']);

function regionName(code) {
  const hit = REGIONS.find((r) => r[0] === String(code));
  if (!hit || REGION_SKIP.has(hit[1])) return null;
  return { name: hit[1], level: hit[2] };
}

function resolveRegion(code6) {
  const c = String(code6 || '').replace(/\D/g, '');
  if (c.length < 2) return null;
  const county = c.length >= 6 ? regionName(c.slice(0, 6)) : null;
  const city = c.length >= 4 ? regionName(c.slice(0, 4)) : null;
  const prov = regionName(c.slice(0, 2));
  const provinceName = prov?.name || `未知（前2位 ${c.slice(0, 2)}）`;
  // 直辖市（京/津/沪/渝）：地市级「市辖区」被排除，直接以省级名兜底，避免出现「未收录（前4位 5001）」
  const isMunicipality = ['11', '12', '31', '50'].includes(c.slice(0, 2));
  const cityName = city?.name || (isMunicipality ? provinceName : c.length >= 4 ? `未收录（前4位 ${c.slice(0, 4)}）` : '—');
  return {
    province: provinceName,
    city: cityName,
    county: county?.name || (c.length >= 6 ? `未收录（前6位 ${c.slice(0, 6)}）` : '—'),
    countyUnknown: !county,
  };
}

// ---------------- 名称结构解析 ----------------
/** 名称头部的行政区划兜底正则：省/自治区 → 市/自治州/盟/地区 → 区/县/旗/市。 */
const REGION_RE =
  /^((?:[\u4e00-\u9fa5]{2,7})(?:省|自治区))?((?:[\u4e00-\u9fa5]{2,8})(?:市|自治州|盟|地区))?((?:[\u4e00-\u9fa5]{2,8})(?:区|县|旗|市))?/;

/** 省级简称：重庆市→重庆、广西壮族自治区→广西、河北省→河北（企业名常省略「省/市」）。 */
function aliasOf(n) {
  let s = n;
  for (let i = 0; i < 3; i++) {
    const t = s.replace(/(特别行政区|自治区|壮族|回族|维吾尔|省|市)$/, '');
    if (t === s || t.length < 2) break;
    s = t;
  }
  return s;
}

/** 从名称头部剥离行政区划（表匹配优先；表里没有的区县走正则兜底）。 */
function stripRegion(name) {
  const names = REGIONS.filter((r) => !REGION_SKIP.has(r[1]) && r[2] !== '市' && r[1].length >= 2)
    .flatMap((r) => (r[2] === '省' ? [r[1], aliasOf(r[1])] : [r[1]]))
    .filter((n) => n && n.length >= 2)
    .sort((a, b) => b.length - a.length);
  const picked = [];
  let rest = name;
  for (let i = 0; i < 2; i++) {
    const hit = names.find((n) => rest.startsWith(n) && rest.length > n.length);
    if (!hit) break;
    picked.push(hit);
    rest = rest.slice(hit.length);
  }
  if (picked.length) return { regionPrefix: picked.join(''), rest };

  const m = name.match(REGION_RE);
  const parts = (m ? [m[1], m[2], m[3]] : []).filter(Boolean);
  if (parts.length) {
    const prefix = parts.join('');
    if (prefix.length >= 2 && name.length > prefix.length) {
      return { regionPrefix: prefix, rest: name.slice(prefix.length) };
    }
  }
  return { regionPrefix: '', rest: name };
}

function stripOrgForm(s) {
  const forms = ORGFORM.map((r) => r[0]).sort((a, b) => b.length - a.length);
  for (const f of forms) {
    if (s.endsWith(f)) return { form: f, core: s.slice(0, s.length - f.length) };
  }
  return { form: '', core: s };
}

function matchIndustry(text) {
  for (const [keys, sector, detail, typical] of INDUSTRY) {
    // 关键词列用「、」分隔同义词（不能用 |，那是 markdown 列分隔符）
    for (const k of keys.split('、')) {
      if (k && text.includes(k)) {
        return { keyword: k, sector, detail, typical };
      }
    }
  }
  return null;
}

// ---------------- 税收分类编码 → 行业 ----------------
function lookupTaxClass(code) {
  const c = String(code || '').replace(/\D/g, '');
  if (!c) return null;
  const chain = [];
  for (const len of [5, 3, 1]) {
    if (c.length < len) continue;
    const hit = TAXCLASS.find((r) => r[0] === c.slice(0, len));
    if (hit) {
      chain.unshift({ prefix: hit[0], name: hit[1], parent: hit[2] });
      if (len === 1) break;
    }
  }
  if (!chain.length) return { chain: [], matched: null, text: `未收录（${c}）` };
  const matched = chain[chain.length - 1];
  return {
    matched,
    chain,
    text: chain.map((c2) => c2.name).join(' > '),
  };
}

// ---------------- 纳税人身份 / 开票特征 ----------------
function parseRate(s) {
  if (s === null || s === undefined || s === '') return null;
  let n = Number(String(s).replace('%', '').trim());
  if (!Number.isFinite(n)) return null;
  if (n > 0 && n < 1) n = n * 100;
  return Math.round(n * 100) / 100;
}

function inferTaxpayer(rate) {
  if (rate === null) return { level: '未知', text: '未提供税率，无法推断纳税人身份' };
  if (rate === 13 || rate === 9 || rate === 6) {
    return {
      level: '一般纳税人（推断·高置信）',
      text: `适用 ${rate}% 属一般计税税率，销方大概率为**增值税一般纳税人**`,
    };
  }
  if (rate === 1) return { level: '小规模纳税人（推断）', text: '1% 为小规模纳税人 3% 征收率减按 1% 征收（阶段性优惠）' };
  if (rate === 3) return { level: '小规模或简易计税（不可区分）', text: '3% 征收率：小规模纳税人常用，也可能是一般纳税人的简易计税项目' };
  if (rate === 5) return { level: '小规模或简易计税（不可区分）', text: '5% 征收率：不动产/劳务派遣等差额或简易项目，常见于小规模或一般纳税人简易计税' };
  if (rate === 0) return { level: '免税 / 零税率', text: '0%：免税项目或零税率（出口等），需结合商品判断' };
  return { level: '需人工确认', text: `票面税率 ${rate}% 不在常规档位（13/9/6/5/3/1/0），请核对` };
}

function amountBand(yuan) {
  if (!Number.isFinite(yuan)) return '—';
  if (yuan < 100) return `零星小额（<100 元）—— 常见于停车、零售、餐饮等高频场景`;
  if (yuan < 1000) return '小额（100–1000 元）';
  if (yuan < 10000) return '中小额（1000–1 万元）';
  if (yuan < 100000) return '中额（1 万–10 万元）';
  if (yuan < 1000000) return '大额（10 万–100 万元）';
  return '超大额（≥100 万元）';
}

function dateInfo(yyyymmdd) {
  const s = String(yyyymmdd || '');
  if (!/^\d{8}$/.test(s)) return null;
  const y = +s.slice(0, 4);
  const m = +s.slice(4, 6);
  const d = +s.slice(6, 8);
  const dt = new Date(y, m - 1, d);
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dt.getDay()];
  const tags = [];
  if (dt.getDay() === 0 || dt.getDay() === 6) tags.push('周末');
  const lastDay = new Date(y, m, 0).getDate();
  if (d >= lastDay - 2) tags.push('月末');
  if ([3, 6, 9, 12].includes(m) && d >= lastDay - 4) tags.push('季末');
  return { text: `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}（${week}）`, tags };
}

// ---------------- 参数 ----------------
const argv = process.argv.slice(2);
const jsonOut = argv.includes('--json');

function flag(name) {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 ? argv[i + 1] : undefined;
}

let input = {
  name: flag('name'),
  taxno: flag('taxno'),
  taxClassCode: flag('tax-class-code'),
  rate: flag('tax-rate'),
  total: flag('total'),
  net: flag('net'),
  tax: flag('tax'),
  date: flag('date'),
  invoiceType: flag('invoice-type'),
  goods: flag('goods'),
};

const checkJsonPath = flag('check-json');
if (checkJsonPath) {
  let obj;
  try {
    obj = JSON.parse(readFileSync(checkJsonPath, 'utf8'));
  } catch (e) {
    console.error(`读取 --check-json 失败：${e.message}`);
    process.exit(1);
  }
  const data = obj?.Response?.Data ?? obj?.Data ?? obj?.final?.data ?? obj?.data ?? obj;
  const items = data?.InvoiceItems || data?.Items || [];
  const it0 = items[0] || {};
  input = {
    name: input.name || data?.SellerName,
    taxno: input.taxno || data?.SellerTaxpayerId,
    taxClassCode: input.taxClassCode || it0?.TaxClassCode || data?.TaxClassCode,
    rate: input.rate ?? it0?.GoodsTaxRate ?? it0?.TaxRate ?? data?.TaxRate,
    total: input.total ?? data?.TotalAmount,
    net: input.net ?? data?.NetAmount,
    tax: input.tax ?? data?.TaxAmount,
    date: input.date || data?.InvoiceDate,
    invoiceType: input.invoiceType || data?.InvoiceType,
    goods: input.goods || it0?.GoodsName || it0?.Name,
  };
}

// 位置参数兼容：<名称> <税号> [税编] [税率] [价税合计元] [日期]
const positional = argv.filter((a) => !a.startsWith('--') && a !== (checkJsonPath || '@@'));
const pos = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i].startsWith('--')) {
    if (['--name', '--taxno', '--tax-class-code', '--tax-rate', '--total', '--net', '--tax', '--date', '--invoice-type', '--goods', '--check-json'].includes(argv[i])) i++;
    continue;
  }
  pos.push(argv[i]);
}
if (!input.name && !input.taxno) {
  input.name = input.name || pos[0];
  input.taxno = input.taxno || pos[1];
  input.taxClassCode = input.taxClassCode || pos[2];
  input.rate = input.rate ?? pos[3];
  input.total = input.total ?? pos[4];
  input.date = input.date || pos[5];
}

if (!input.name && !input.taxno) {
  console.error('用法: node seller-profile.mjs --name <销方名称> --taxno <销方税号> [--tax-class-code <19位编码>] [--tax-rate 9] [--total 9.00] [--date 20260916] [--json]');
  console.error('   或: node seller-profile.mjs --check-json <invoice-check 的 --json 输出文件>');
  process.exit(1);
}

// ---------------- 组装画像 ----------------
const name = (input.name || '').trim();
const taxno = (input.taxno || '').replace(/\s/g, '').toUpperCase();
const rate = parseRate(input.rate);
const total = input.total !== undefined && input.total !== '' ? Number(String(input.total).replace(/[¥,]/g, '')) : NaN;
const net = input.net !== undefined && input.net !== '' ? Number(String(input.net).replace(/[¥,]/g, '')) : NaN;
const tax = input.tax !== undefined && input.tax !== '' ? Number(String(input.tax).replace(/[¥,]/g, '')) : NaN;

const cc = checkCreditCode(taxno);
const codeKind =
  taxno.length === 18
    ? '18 位统一社会信用代码'
    : taxno.length === 15
      ? '15 位旧版纳税人识别号'
      : taxno.length === 20
        ? '20 位个人/外籍纳税人识别号（身份证+顺序码）'
        : `长度 ${taxno.length} 位（非常规，需核对）`;

// 代码侧登记画像
let codeRegion = null;
let dept = null;
let orgType = null;
let codeNo = null;
if (taxno.length >= 8 && /^\d{6}/.test(taxno)) {
  const off = taxno.length === 18 ? 2 : 0;
  const regionCode = taxno.slice(off, off + 6);
  codeRegion = resolveRegion(regionCode);
  codeRegion = { ...codeRegion, code: regionCode };
}
if (taxno.length === 18) {
  dept = { code: taxno[0], name: DEPT[taxno[0]] || '未收录' };
  const table = ORG_TYPE[taxno[0]];
  orgType = { code: taxno[1], name: table?.[taxno[1]] || '未收录' };
  codeNo = taxno.slice(8, 17); // 主体标识码（组织机构代码）
}

// 名称侧画像
const { regionPrefix, rest } = stripRegion(name);
const { form, core } = stripOrgForm(rest);
// 行业词：先扫名称，名称未命中时回退到票面商品名
let industry = matchIndustry(core || name);
let industrySrc = '名称';
if (!industry && input.goods) {
  industry = matchIndustry(input.goods);
  industrySrc = '票面商品';
}
/** 字号 = 去掉行业词再去掉通用尾巴（服务/管理/经营…）。 */
const BRAND_TAIL = /(服务|管理|经营|技术|发展|实业|集团|中心|工作室|经营部|营业部)+$/;
const brand =
  (core || '')
    .replace(industry?.keyword || '\u0000', '')
    .replace(/(有限责任公司|有限公司|股份)/g, '')
    .replace(BRAND_TAIL, '')
    .trim()
    .slice(0, 24) || '未识别';

// 税编侧行业
const tc = lookupTaxClass(input.taxClassCode);

// 提示
const notes = [];
if (taxno.length === 18) {
  if (cc && !cc.ok) notes.push(`⚠️ 统一社会信用代码校验位不通过：按 GB 32100-2015 应为 ${cc.expected}，实为 ${cc.actual} → **税号很可能录入有误，或该主体尚未换发统一社会信用代码**`);
  else if (cc?.ok) notes.push('✅ 统一社会信用代码校验位通过（GB 32100-2015）');
}
if (![15, 18, 20].includes(taxno.length)) notes.push(`⚠️ 税号长度 ${taxno.length} 位，不在常规长度（15/18/20）内，请核对`);
if (regionPrefix && codeRegion && !codeRegion.countyUnknown) {
  const same = regionPrefix.includes(codeRegion.county) || codeRegion.county.includes(regionPrefix.replace(/^.*?(省|自治区)/, ''));
  if (same) notes.push(`✅ 名称行政区划「${regionPrefix}」与代码登记机关区划「${codeRegion.county}」一致`);
  else notes.push(`ℹ️ 名称行政区划「${regionPrefix}」与代码登记机关区划「${codeRegion.county}」不一致 —— 常见于异地经营、集团统一登记或名称未冠区划，非必然异常`);
}
if (industry?.typical && rate !== null) {
  const typicals = industry.typical.match(/\d+(?=%)/g) || [];
  if (typicals.length && !typicals.map(Number).includes(rate)) {
    notes.push(`ℹ️ 名称行业词「${industry.keyword}」的典型税率为 ${industry.typical}，本票为 ${rate}% —— 可能因兼营、混合销售或归类差异，需人工确认`);
  }
}
const goodsShort = (input.goods || '').match(/\*(.+?)\*/)?.[1];
if (goodsShort && tc && !tc.text.includes(goodsShort)) {
  notes.push(
    `ℹ️ 票面简称「*${goodsShort}*」与税收分类编码归类「${tc.text}」是两套口径 —— 简称是开票时的商品简称，编码归类是法定归类；不一致时以**编码归类**为准，本画像两者并列展示供对照`,
  );
}
if (/分公司|分支机构/.test(form)) {
  notes.push('ℹ️ 销方为**分支机构**，发票主体与法人主体可能不同，涉诉/授信场景需另行核对总公司');
}
if (taxno.length === 18 && taxno[1] === '2') {
  notes.push('ℹ️ 销方登记为**个体工商户**（非企业法人），交易对手风险评估口径与企业不同');
}
if (taxno.length === 18 && ['1', '5', 'Y'].includes(taxno[0])) {
  notes.push(`ℹ️ 销方为**非工商登记主体**（${dept?.name} / ${orgType?.name}），通常不以营利为目的`);
}

/** 登记地：省/市/区县去重后拼接，未收录的层级直接跳过，避免输出「未收录（前6位 xxx）」之类的噪声。 */
const regionLabel = codeRegion
  ? [...new Set([codeRegion.province, codeRegion.city, codeRegion.county].filter((x) => x && !/未收录|未知|^—$/.test(x)))].join('') +
    '登记'
  : '登记地未知';

const profile = {
  source: '票面要素 + 统一社会信用代码规则推断（非工商登记查询）',
  identity: {
    name: name || '—',
    taxno: taxno || '—',
    codeKind,
    creditCodeCheck: cc ? { ok: cc.ok, expected: cc.expected, actual: cc.actual } : null,
    orgCode: codeNo,
  },
  nameStructure: {
    region: regionPrefix || '未识别出区划前缀',
    brand: brand || '—',
    industryWord: industry?.keyword || '未命中',
    orgForm: form || '未识别',
  },
  registration: {
    dept: dept ? `${dept.code} → ${dept.name}` : '—（非 18 位统一代码，无法解析）',
    orgType: orgType ? `${orgType.code} → ${orgType.name}` : '—',
    region: codeRegion ? `${codeRegion.code} → ${codeRegion.province} / ${codeRegion.city} / ${codeRegion.county}` : '—',
  },
  industry: {
    fromTaxClassCode: tc ? `${input.taxClassCode} → ${tc.text}` : '未提供税收分类编码',
    fromName: industry
      ? `${industry.keyword}（来自${industrySrc}） → ${industry.sector}（${industry.detail}）`
      : '名称与票面商品均未命中行业词',
    goods: input.goods || '—',
  },
  taxpayer: inferTaxpayer(rate),
  invoiceBehavior: {
    date: dateInfo(input.date)?.text || input.date || '—',
    dateTags: dateInfo(input.date)?.tags || [],
    totalYuan: Number.isFinite(total) ? total : null,
    netYuan: Number.isFinite(net) ? net : null,
    taxYuan: Number.isFinite(tax) ? tax : null,
    band: amountBand(total),
    invoiceType: input.invoiceType || '—',
  },
  notes,
  summary: [
    name || '—',
    `（${taxno || '—'}）`,
    regionLabel,
    orgType?.name || '主体性质待核',
    industry?.sector || '行业待核',
    inferTaxpayer(rate).level,
    Number.isFinite(total) ? `本票价税合计 ¥${total.toFixed(2)}` : null,
  ]
    .filter(Boolean)
    .join(' · '),
  boundary: [
    '注册资本、法定代表人、成立日期、登记机关、经营状态、股东/出资、参保人数、纳税信用等级 —— **票面均不含**，本画像不提供',
    '如需上述要素，须走外部工商检索（企业信用信息公示系统/第三方平台），并在结论中标注「来源：外部检索，非票面数据」',
    '本画像中的纳税人身份、行业门类均为**规则推断**，不作为法律或税务判定依据',
  ],
};

if (jsonOut) {
  console.log(JSON.stringify(profile, null, 2));
  process.exit(0);
}

/** 按显示宽度（中文 2 列）对齐标签。 */
const dispWidth = (s) => [...s].reduce((n, ch) => n + (/[^\x00-\xff]/.test(ch) ? 2 : 1), 0);
const L = (k, v) => console.log(`  ${k}${' '.repeat(Math.max(1, 14 - dispWidth(k)))}：${v}`);
const yuan = (y) => (Number.isFinite(y) ? `¥${y.toFixed(2)}` : '—');

console.log('════════ 销方企业画像 ════════');
console.log(`摘要：${profile.summary}`);
console.log(`（依据：${profile.source}）\n`);

console.log('[1] 主体标识');
L('企业名称', profile.identity.name);
L('纳税人识别号', `${profile.identity.taxno}　（${profile.identity.codeKind}）`);
if (profile.identity.creditCodeCheck) {
  const c = profile.identity.creditCodeCheck;
  L('代码校验', c.ok ? `通过 ✅（校验位 ${c.actual}）` : `不通过 ⚠️（应为 ${c.expected}，实为 ${c.actual}）`);
}
if (profile.identity.orgCode) L('主体标识码', `${profile.identity.orgCode}（组织机构代码段）`);

console.log('\n[2] 名称结构');
L('行政区划', profile.nameStructure.region);
L('字号', profile.nameStructure.brand);
L('行业词', profile.nameStructure.industryWord);
L('组织形式', profile.nameStructure.orgForm);

console.log('\n[3] 登记画像（来自纳税人识别号）');
L('登记管理部门', profile.registration.dept);
L('机构类别', profile.registration.orgType);
L('登记机关区划', profile.registration.region);

console.log('\n[4] 行业画像');
L('税收分类编码', profile.industry.fromTaxClassCode);
L('名称行业词', profile.industry.fromName);
L('票面商品', profile.industry.goods);

console.log('\n[5] 纳税人身份（推断）');
L('结论', profile.taxpayer.level);
L('依据', profile.taxpayer.text);
if (profile.invoiceBehavior.invoiceType !== '—') {
  L('票种', `${profile.invoiceBehavior.invoiceType}（小规模也可自开普票，不能据此判定纳税人身份）`);
}

console.log('\n[6] 开票特征');
L('开票日期', [profile.invoiceBehavior.date, ...profile.invoiceBehavior.dateTags].filter(Boolean).join(' · '));
L('价税合计', `${yuan(profile.invoiceBehavior.totalYuan)}　（${profile.invoiceBehavior.band}）`);
L('不含税金额', yuan(profile.invoiceBehavior.netYuan));
L('税额', yuan(profile.invoiceBehavior.taxYuan));

console.log('\n[7] 提示');
for (const n of profile.notes) console.log(`  ${n}`);
if (!profile.notes.length) console.log('  （无）');

console.log('\n[8] 数据边界（务必随结论一并转达）');
for (const b of profile.boundary) console.log(`  · ${b}`);
