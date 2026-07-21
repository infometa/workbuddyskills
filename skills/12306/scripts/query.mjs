#!/usr/bin/env node
// Query 12306 train tickets: schedule, remaining tickets, prices
import { parseArgs } from 'node:util';
import { writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadStations, resolveStation } from './stations.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));

const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
  Referer: 'https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc',
};

// 12306 API returns pipe-delimited fields; index mapping:
// ref: https://blog.csdn.net/a460550542/article/details/86302597
const F = {
  trainNo: 2, trainCode: 3, fromCode: 6, toCode: 7,
  departTime: 8, arriveTime: 9, duration: 10, canBuy: 11, date: 13,
  gr: 21, rw: 23, rz: 24, tz: 25, wz: 26, yw: 28, yz: 29,
  ze: 30, zy: 31, swz: 32, dw: 33,
};

// --- Argument parsing ---

const { values, positionals } = parseArgs({
  options: {
    date:         { type: 'string',  short: 'd' },
    type:         { type: 'string',  short: 't', default: '' },
    depart:       { type: 'string' },          // e.g. 08:00-12:00
    arrive:       { type: 'string' },          // e.g. -18:00
    'max-duration': { type: 'string' },        // e.g. 2h, 90m, 1h30m
    available:    { type: 'boolean', default: false },  // only bookable
    seat:         { type: 'string' },          // e.g. ze,zy (has tickets for these seat types)
    format:       { type: 'string',  short: 'f', default: 'html' }, // html or md
    output:       { type: 'string',  short: 'o' },     // output file path
    json:         { type: 'boolean', default: false },
  },
  allowPositionals: true,
});

const [fromName, toName] = positionals;
if (!fromName || !toName) {
  console.error(`Usage: query.mjs <from> <to> [options]

Options:
  -d, --date <YYYY-MM-DD>     Travel date (default: today)
  -t, --type <G|D|Z|T|K>      Filter train types (combinable, e.g. GD)
  --depart <HH:MM-HH:MM>      Depart time range (e.g. 08:00-12:00, 18:00-)
  --arrive <HH:MM-HH:MM>      Arrive time range (e.g. -18:00, 14:00-20:00)
  --max-duration <duration>    Max travel time (e.g. 2h, 90m, 1h30m)
  --available                  Only show bookable trains
  --seat <types>               Only show trains with tickets for given seats
                               (comma-separated: swz,zy,ze,rw,dw,yw,yz,wz)
  -f, --format <html|md>       Output format (default: html)
  -o, --output <path>          Output file path (html mode only)
  --json                       Output raw JSON`);
  process.exit(1);
}

const date = values.date || new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Shanghai' });
const trainTypeFilter = (values.type || '').toUpperCase();

// --- Time & duration helpers ---

function parseTime(s) {
  const [h, m] = s.split(':').map(Number);
  return h * 60 + m;
}

function parseTimeRange(s) {
  if (!s) return null;
  const [lo, hi] = s.split('-');
  return { lo: lo ? parseTime(lo) : 0, hi: hi ? parseTime(hi) : 24 * 60 };
}

function parseDurationLimit(s) {
  if (!s) return null;
  const match = s.match(/^(?:(\d+)h)?(?:(\d+)m)?$/i);
  if (!match) return null;
  return (parseInt(match[1] || 0) * 60) + parseInt(match[2] || 0);
}

function formatDuration(raw) {
  // raw from 12306: "01:30" or "00:45"
  const [h, m] = raw.split(':').map(Number);
  if (isNaN(h) || isNaN(m)) return raw;
  return h > 0 ? `${h}h${m.toString().padStart(2, '0')}m` : `${m}m`;
}

function durationMinutes(raw) {
  const [h, m] = raw.split(':').map(Number);
  return h * 60 + m;
}

// --- API ---

async function getCookie() {
  const res = await fetch('https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc', {
    headers: HEADERS,
    redirect: 'manual',
  });
  const cookies = res.headers.getSetCookie?.() || [];
  return cookies.map(c => c.split(';')[0]).join('; ');
}

async function queryTickets(from, to, travelDate) {
  const cookie = await getCookie();
  const params = new URLSearchParams({
    'leftTicketDTO.train_date': travelDate,
    'leftTicketDTO.from_station': from.station_code,
    'leftTicketDTO.to_station': to.station_code,
    purpose_codes: 'ADULT',
  });

  const res = await fetch(`https://kyfw.12306.cn/otn/leftTicket/query?${params}`, {
    headers: { ...HEADERS, Cookie: cookie },
  });

  const json = await res.json();
  if (!json.data?.result) {
    console.error('No data returned:', JSON.stringify(json).slice(0, 500));
    process.exit(1);
  }
  return json.data;
}

// --- Parsing ---

function parseTicket(raw, stationMap) {
  const f = raw.split('|');
  const v = (key) => f[F[key]] || '--';

  return {
    trainNo: v('trainNo'), trainCode: v('trainCode'),
    fromStation: stationMap[v('fromCode')]?.station_name || v('fromCode'),
    toStation: stationMap[v('toCode')]?.station_name || v('toCode'),
    departTime: v('departTime'), arriveTime: v('arriveTime'),
    duration: v('duration'), canBuy: v('canBuy'), date: v('date'),
    swz: v('swz'), tz: v('tz'), zy: v('zy'), ze: v('ze'),
    gr: v('gr'), rw: v('rw'), dw: v('dw'),
    yw: v('yw'), rz: v('rz'), yz: v('yz'), wz: v('wz'),
  };
}

function hasSeat(val) {
  return val && val !== '--' && val !== '' && val !== '无';
}

// --- Filtering ---

function applyFilters(tickets) {
  let result = tickets;

  if (trainTypeFilter) {
    const chars = [...trainTypeFilter];
    result = result.filter(t => chars.some(ch => t.trainCode.startsWith(ch)));
  }

  const departRange = parseTimeRange(values.depart);
  if (departRange) {
    result = result.filter(t => {
      const m = parseTime(t.departTime);
      return m >= departRange.lo && m <= departRange.hi;
    });
  }

  const arriveRange = parseTimeRange(values.arrive);
  if (arriveRange) {
    result = result.filter(t => {
      const m = parseTime(t.arriveTime);
      return m >= arriveRange.lo && m <= arriveRange.hi;
    });
  }

  const maxDur = parseDurationLimit(values['max-duration']);
  if (maxDur) {
    result = result.filter(t => durationMinutes(t.duration) <= maxDur);
  }

  if (values.available) {
    result = result.filter(t => t.canBuy === 'Y');
  }

  if (values.seat) {
    const seatTypes = values.seat.split(',').map(s => s.trim().toLowerCase());
    result = result.filter(t => seatTypes.every(s => hasSeat(t[s])));
  }

  return result;
}

// --- HTML output ---

function seatCell(val) {
  if (!val || val === '--' || val === '') return '<td class="na">\u2014</td>';
  if (val === '无') return '<td class="sold-out">\u65E0</td>';
  if (val === '有') return '<td class="available">\u6709</td>';
  return `<td class="count">${val}</td>`;
}

function buildHTML(tickets, from, to, travelDate, filterDesc) {
  const e = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const fn = e(from.station_name), tn = e(to.station_name);

  const rows = tickets.map(t => {
    const swz = t.swz !== '--' ? t.swz : t.tz !== '--' ? t.tz : '--';
    const rw = t.rw !== '--' ? t.rw : t.dw !== '--' ? t.dw : '--';
    const typeClass = t.trainCode[0]?.toLowerCase() || '';
    const buyClass = t.canBuy === 'Y' ? 'yes' : 'no';
    return `      <tr>
        <td class="train-code type-${typeClass}">${e(t.trainCode)}</td>
        <td class="time"><span class="depart">${e(t.departTime)}</span><span class="arrow">\u2192</span><span class="arrive">${e(t.arriveTime)}</span></td>
        <td class="duration">${formatDuration(t.duration)}</td>
        ${seatCell(swz)}${seatCell(t.zy)}${seatCell(t.ze)}${seatCell(rw)}${seatCell(t.yw)}${seatCell(t.yz)}${seatCell(t.wz)}
        <td class="buy-${buyClass}">${t.canBuy === 'Y' ? '\u53EF\u8D2D' : '\u552E\u7F44'}</td>
      </tr>`;
  }).join('\n');

  const filterTag = filterDesc
    ? `<div class="filters">${e(filterDesc)}</div>`
    : '';

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${fn} \u2192 ${tn} \u5217\u8F66\u65F6\u523B\u8868</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif; background: #f5f5f7; color: #1d1d1f; }
  .container { max-width: 1100px; margin: 0 auto; padding: 40px 20px; }
  header { text-align: center; margin-bottom: 32px; }
  h1 { font-size: 28px; font-weight: 600; letter-spacing: -0.5px; }
  h1 .arrow { margin: 0 12px; color: #86868b; font-weight: 300; }
  .meta { margin-top: 8px; color: #86868b; font-size: 15px; }
  .meta span + span::before { content: "\\00b7"; margin: 0 8px; }
  .filters { margin-top: 6px; color: #0071e3; font-size: 13px; }
  .table-wrap { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  .empty { padding: 60px 20px; text-align: center; color: #86868b; font-size: 15px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  thead { background: #fafafa; }
  th { padding: 12px 10px; font-weight: 500; color: #86868b; font-size: 12px; letter-spacing: 0.5px; border-bottom: 1px solid #f0f0f0; white-space: nowrap; }
  td { padding: 11px 10px; border-bottom: 1px solid #f5f5f5; text-align: center; white-space: nowrap; }
  tr:last-child td { border-bottom: none; }
  tr:hover { background: #fafbff; }
  .train-code { font-weight: 600; text-align: left; padding-left: 16px; }
  .type-g { color: #0071e3; }
  .type-d { color: #34c759; }
  .type-z { color: #af52de; }
  .type-t { color: #ff9500; }
  .type-k { color: #86868b; }
  .time { font-variant-numeric: tabular-nums; }
  .depart { font-weight: 600; }
  .arrow { margin: 0 4px; color: #c0c0c0; }
  .arrive { color: #6e6e73; }
  .duration { color: #86868b; font-variant-numeric: tabular-nums; }
  .na { color: #d2d2d7; }
  .available { color: #34c759; font-weight: 500; }
  .sold-out { color: #ff3b30; }
  .count { font-weight: 600; font-variant-numeric: tabular-nums; }
  .buy-yes { color: #34c759; font-weight: 500; }
  .buy-no { color: #ff3b30; font-weight: 500; }
  footer { text-align: center; margin-top: 24px; color: #c0c0c0; font-size: 12px; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>${fn}<span class="arrow">\u2192</span>${tn}</h1>
    <div class="meta"><span>${e(travelDate)}</span><span>${tickets.length} \u8D9F\u5217\u8F66</span></div>
    ${filterTag}
  </header>
  <div class="table-wrap">${tickets.length === 0
    ? '\n    <div class="empty">\u6CA1\u6709\u627E\u5230\u7B26\u5408\u6761\u4EF6\u7684\u5217\u8F66</div>'
    : `
    <table>
      <thead><tr>
        <th style="text-align:left;padding-left:16px">\u8F66\u6B21</th><th>\u65F6\u95F4</th><th>\u8017\u65F6</th>
        <th>\u5546\u52A1/\u7279\u7B49</th><th>\u4E00\u7B49\u5EA7</th><th>\u4E8C\u7B49\u5EA7</th><th>\u8F6F\u5367/\u52A8\u5367</th><th>\u786C\u5367</th><th>\u786C\u5EA7</th><th>\u65E0\u5EA7</th><th>\u72B6\u6001</th>
      </tr></thead>
      <tbody>
${rows}
      </tbody>
    </table>`}
  </div>
  <footer>\u6570\u636E\u6765\u6E90 12306 \u00b7 ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}</footer>
</div>
</body>
</html>`;
}

// --- Markdown output ---

function buildMarkdown(tickets, from, to, travelDate, filterDesc) {
  const lines = [];
  lines.push(`## ${from.station_name} \u2192 ${to.station_name} | ${travelDate} | ${tickets.length} \u8D9F\u5217\u8F66`);
  if (filterDesc) lines.push(`> ${filterDesc}`);
  lines.push('');

  if (tickets.length === 0) {
    lines.push('\u6CA1\u6709\u627E\u5230\u7B26\u5408\u6761\u4EF6\u7684\u5217\u8F66');
    return lines.join('\n');
  }

  lines.push('| \u8F66\u6B21 | \u51FA\u53D1\u2192\u5230\u8FBE | \u8017\u65F6 | \u5546\u52A1/\u7279\u7B49 | \u4E00\u7B49\u5EA7 | \u4E8C\u7B49\u5EA7 | \u8F6F\u5367/\u52A8\u5367 | \u786C\u5367 | \u786C\u5EA7 | \u65E0\u5EA7 | \u72B6\u6001 |');
  lines.push('|------|-----------|------|-----------|--------|--------|-----------|------|------|------|------|');

  for (const t of tickets) {
    const swz = t.swz !== '--' ? t.swz : t.tz !== '--' ? t.tz : '--';
    const rw = t.rw !== '--' ? t.rw : t.dw !== '--' ? t.dw : '--';
    const buy = t.canBuy === 'Y' ? '\u2705' : '\u274C';
    lines.push(`| ${t.trainCode} | ${t.departTime}\u2192${t.arriveTime} | ${formatDuration(t.duration)} | ${swz} | ${t.zy} | ${t.ze} | ${rw} | ${t.yw} | ${t.yz} | ${t.wz} | ${buy} |`);
  }
  return lines.join('\n');
}

function buildFilterDesc() {
  const parts = [];
  if (trainTypeFilter) parts.push(`${trainTypeFilter} \u5B57\u5934`);
  if (values.depart) parts.push(`\u51FA\u53D1 ${values.depart}`);
  if (values.arrive) parts.push(`\u5230\u8FBE ${values.arrive}`);
  if (values['max-duration']) parts.push(`\u8017\u65F6 \u2264 ${values['max-duration']}`);
  if (values.available) parts.push('\u4EC5\u53EF\u8D2D');
  if (values.seat) parts.push(`\u6709\u7968: ${values.seat}`);
  return parts.length ? parts.join(' | ') : '';
}

// --- Main ---

const stationData = await loadStations();
const fromStation = resolveStation(stationData, fromName);
const toStation = resolveStation(stationData, toName);
if (!fromStation) { console.error(`Station not found: ${fromName}`); process.exit(1); }
if (!toStation) { console.error(`Station not found: ${toName}`); process.exit(1); }

console.error(`Querying: ${fromStation.station_name}(${fromStation.station_code}) \u2192 ${toStation.station_name}(${toStation.station_code}) on ${date}`);

const data = await queryTickets(fromStation, toStation, date);
const tickets = data.result.map(r => parseTicket(r, stationData.STATIONS));
const filtered = applyFilters(tickets);

const fmt = values.format?.toLowerCase() || 'html';
const filterDesc = buildFilterDesc();

if (values.json) {
  console.log(JSON.stringify(filtered, null, 2));
} else if (fmt === 'md') {
  console.error(`${filtered.length}/${tickets.length} trains matched.`);
  console.log(buildMarkdown(filtered, fromStation, toStation, date, filterDesc));
} else {
  const html = buildHTML(filtered, fromStation, toStation, date, filterDesc);
  const outPath = values.output || join(__dirname, '..', 'data',
    `${fromStation.station_name}-${toStation.station_name}-${date}.html`);
  writeFileSync(outPath, html);
  console.error(`${filtered.length}/${tickets.length} trains matched. Saved to ${outPath}`);
  console.log(outPath);
}
