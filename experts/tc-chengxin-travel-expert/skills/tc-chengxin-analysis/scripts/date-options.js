#!/usr/bin/env node
'use strict';

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith('--')) throw new Error(`无法识别参数: ${argv[i]}`);
    const key = argv[i].slice(2), value = argv[i + 1];
    if (!value || value.startsWith('--')) throw new Error(`参数 --${key} 缺少值`);
    args[key] = value; i += 1;
  }
  return args;
}

function validDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ''))) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}

function todayInChina(now = new Date()) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(now);
}

function addDays(value, days) {
  const date = new Date(`${value}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function dateOption(value) {
  const date = new Date(`${value}T00:00:00Z`), weekday = WEEKDAYS[date.getUTCDay()];
  return { date: value, weekday, label: `${Number(value.slice(5, 7))}月${Number(value.slice(8, 10))}日（${weekday}）` };
}

function normalizeWeekday(value) {
  const text = String(value || '').trim().replace(/^星期/, '周');
  const english = { Sunday:'周日', Monday:'周一', Tuesday:'周二', Wednesday:'周三', Thursday:'周四', Friday:'周五', Saturday:'周六' };
  return WEEKDAYS.includes(text) ? text : english[value] || null;
}

function build(args = {}, now = new Date()) {
  const baseDate = args['base-date'] || todayInChina(now);
  if (!validDate(baseDate)) throw new Error('base-date/start-date 必须为真实 YYYY-MM-DD 日期');
  if (args['default-tomorrow'] === 'true') {
    const tomorrow = dateOption(addDays(baseDate, 1));
    return {
      type: 'workbuddy_default_departure_date',
      timezone: 'Asia/Shanghai',
      baseDate,
      defaultDate: tomorrow.date,
      weekday: tomorrow.weekday,
      label: tomorrow.label,
      extra: `${tomorrow.date} 出发`,
      assumption: '用户未提供火车出发日期，按次日查询'
    };
  }
  const startDate = args['start-date'] || baseDate;
  if (!validDate(startDate)) throw new Error('base-date/start-date 必须为真实 YYYY-MM-DD 日期');
  const days = Number(args.days || 4);
  if (!Number.isInteger(days) || days < 1 || days > 14) throw new Error('days 必须是 1–14 的整数');
  const options = Array.from({ length: days }, (_, index) => dateOption(addDays(startDate, index)));
  const dateQuestion = {
    header: '出发日期',
    question: '您想哪天出发？',
    options: options.map(option => ({ label: option.label, description: `按 ${option.date} 查询` }))
  };
  const result = {
    type: 'workbuddy_date_options', timezone: 'Asia/Shanghai', baseDate, startDate,
    options,
    askUserQuestion: dateQuestion,
    questions: [dateQuestion],
    askUserQuestionPayload: { questions: [dateQuestion] }
  };
  if (args['check-date']) {
    if (!validDate(args['check-date'])) throw new Error('check-date 必须为真实 YYYY-MM-DD 日期');
    const actual = dateOption(args['check-date']), claimed = normalizeWeekday(args['claimed-weekday']);
    result.check = { ...actual, claimedWeekday: claimed || undefined,
      matches: claimed ? claimed === actual.weekday : undefined };
  }
  return result;
}

function main(argv = process.argv.slice(2)) {
  try {
    process.stdout.write(`${JSON.stringify(build(parseArgs(argv)), null, 2)}\n`);
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}

if (require.main === module) main();
module.exports = { addDays, build, dateOption, normalizeWeekday, parseArgs, todayInChina, validDate };
