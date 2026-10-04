'use strict';

const path = require('path');
const { inferExplicitResponseMode, normalizeResponseMode } = require('./response-mode');
const { addDays, todayInChina } = require('./date-options');

const DIRECT_QUERY_SCRIPTS = new Set([
  'bus-query.js',
  'flight-query.js',
  'hotel-query.js',
  'scenery-query.js',
  'traffic-query.js',
  'train-query.js'
]);

// Simple lookup means that the user only asks for the current result list. Once
// the request contains a preference, comparison, constraint or planning goal,
// the returned data still needs an expert decision instead of a mechanical
// first-page rendering. "附近/周边" is deliberately not a preference here: it
// is part of the search object for hotel and scenery queries.
const EXPERT_ANALYSIS_SIGNALS = [
  /行程|攻略|路线.{0,6}(?:安排|规划)|每天.{0,6}(?:安排|怎么玩)|多日|一日游|两日游|三日游|自由行/,
  /综合解读|综合推荐|分析推荐|专家解读|帮我分析|详细分析|给出建议/,
  /对比|比较|哪个好|哪一个好|选哪个|怎么选|帮我选|帮我挑|挑一个|推荐哪个|取舍|兼顾|优先/,
  /便宜|低价|最省钱|最快|最省时|最短|最早|最晚|性价比|划算|舒适|方便|值得/,
  /预算|\d+(?:\.\d+)?\s*元.{0,6}(?:内|以内|以下)|不超过|至少|至多|以上|以下/,
  /偏好|必须|不要|不想|不住|排除|避开|只要|适合/,
  /亲子|带娃|儿童|老人|老年|商务|情侣|无障碍|宠物/,
  /上午|下午|早上|晚上|凌晨|直达|中转|卧铺|一等座|二等座|商务座|经济舱|公务舱|头等舱/,
  /星级|评分|早餐|停车|泳池|健身|房型|床型|退改|行李|接驳|换乘/
];

function decisionText(value) {
  return String(value || '').replace(
    /(?:不需要|不用|不要)(?:做|制定|规划)?(?:行程规划|行程安排|行程|攻略|分析|比较|对比)(?=\s*(?:[，,。；;]|$))/g,
    ''
  );
}

function isItineraryRequest(value) {
  const positive = decisionText(value);
  return /行程规划|规划.{0,8}行程|安排行程|行程安排|自由行安排|每日安排|每天怎么玩|每日路线|多日行程|\bitinerary\b/i.test(positive);
}

function optionText(args) {
  const values = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = String(args[index] || '');
    const equals = arg.indexOf('=');
    const key = equals < 0 ? arg : arg.slice(0, equals);
    if (!['--query', '--extra'].includes(key)) continue;
    const value = equals < 0 ? args[index + 1] : arg.slice(equals + 1);
    if (value !== undefined) values.push(String(value));
    if (equals < 0) index += 1;
  }
  return values.join(' ').trim();
}

function hasOption(args, name) {
  return args.some(arg => String(arg || '').split('=')[0] === name);
}

function trainDateState(value) {
  const text = String(value || '');
  if (/日期未定|时间未定|还没定日期|随便看看|哪天都行|任意日期/.test(text)) return 'open';
  if (/\d{4}[-年/.]\d{1,2}[-月/.]\d{1,2}(?:日|号)?|\d{1,2}月\d{1,2}(?:日|号)?|(?:^|\D)\d{1,2}[/-]\d{1,2}(?:\D|$)|今天|明天|后天|大后天|本周|下周|周末|月底|月初|周[一二三四五六日天]|星期[一二三四五六日天]/.test(text)) return 'provided';
  return 'missing';
}

// Enforce the product default in code instead of relying on every model to run
// a separate date helper. It applies only to an A-to-B route, never to a lone
// train number, and never overrides an explicit/open-ended date statement.
function applyTrainDateDefault(queryScript, task, now = new Date()) {
  if (path.basename(queryScript || '') !== 'train-query.js') return task;
  const args = [...(task && task.args || [])];
  const hasCityPair = hasOption(args, '--departure') && hasOption(args, '--destination');
  const hasStationPair = hasOption(args, '--departure-station') && hasOption(args, '--arrival-station');
  if (!hasCityPair && !hasStationPair) return task;
  const state = trainDateState(optionText(args));
  if (state !== 'missing') return task;
  const baseDate = todayInChina(now);
  const defaultDate = addDays(baseDate, 1);
  const extraIndex = args.indexOf('--extra');
  if (extraIndex >= 0) args[extraIndex + 1] = `${defaultDate} 出发；${args[extraIndex + 1]}`;
  else args.push('--extra', `${defaultDate} 出发`);
  return { ...task, args, queryDefaults: {
    departureDate: defaultDate,
    reason: 'train_route_missing_date_defaults_to_next_day',
    timezone: 'Asia/Shanghai'
  } };
}

function classifyResponseFlow(queryScript, task, requestedMode = 'auto') {
  const script = path.basename(queryScript || '');
  const rawRequestText = optionText(task && task.args || []);
  const requestText = decisionText(rawRequestText);
  const responseMode = normalizeResponseMode(requestedMode);
  if (!DIRECT_QUERY_SCRIPTS.has(script)) {
    return { flow: 'expert_analysis', reason: 'unsupported_direct_query' };
  }
  if (!task || task.intent === 'itinerary' || isItineraryRequest(requestText)) {
    return { flow: 'expert_analysis', reason: 'itinerary' };
  }
  if (responseMode === 'expert') {
    return { flow: 'expert_analysis', reason: 'user_selected_expert' };
  }
  if (responseMode === 'direct') {
    return { flow: 'direct_render', reason: 'user_selected_direct' };
  }
  const explicitMode = inferExplicitResponseMode(rawRequestText);
  if (explicitMode === 'expert') {
    return { flow: 'expert_analysis', reason: 'explicit_expert_request' };
  }
  if (explicitMode === 'direct') {
    return { flow: 'direct_render', reason: 'explicit_direct_request' };
  }
  if (task.args.some(arg => String(arg).split('=')[0] === '--low-price')) {
    return { flow: 'expert_analysis', reason: 'preference_or_constraint' };
  }
  const signal = EXPERT_ANALYSIS_SIGNALS.find(pattern => pattern.test(requestText));
  if (signal) return { flow: 'expert_analysis', reason: 'preference_or_constraint' };
  return { flow: 'direct_render', reason: 'simple_lookup' };
}

// Travel shares one endpoint with package-tour search. Keep the user intent explicit.
function prepareQuery(query, args, requestedIntent) {
  if (requestedIntent && !['itinerary', 'selection'].includes(requestedIntent)) throw new Error('--intent 只能是 itinerary 或 selection');
  const travel = path.basename(query) === 'travel-query.js';
  let extra = '';
  let searchQuery = '';
  const kept = [];
  const seen = new Set();
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const equals = arg.indexOf('=');
    const key = equals < 0 ? arg : arg.slice(0, equals);
    const paired = arg.startsWith('--') && equals < 0 && args[i + 1] !== undefined && !args[i + 1].startsWith('--');
    if (key === '--extra' || key === '--query') {
      if (seen.has(key)) throw new Error(`${key} 重复，请合并本轮已确认条件后只传一次`);
      seen.add(key);
      if (equals < 0 && !paired) throw new Error(`${key} 缺少值`);
      const value = equals < 0 ? args[++i] : arg.slice(equals + 1);
      if (key === '--extra') extra = value;
      else {
        if (!value.trim()) throw new Error('--query 不能为空');
        searchQuery = value;
        kept.push('--query', value);
      }
    } else {
      kept.push(arg);
      if (paired) kept.push(args[++i]);
    }
  }
  const requestText = `${searchQuery} ${extra}`;
  const intent = requestedIntent || (travel && isItineraryRequest(requestText) ? 'itinerary' : '');
  if (travel && !intent) throw new Error('旅行查询必须明确 --intent itinerary（规划每天行程）或 --intent selection（只比选跟团/度假产品），不能按接口返回类型替用户改变需求');
  if (travel && intent === 'selection' && isItineraryRequest(requestText)) throw new Error('行程规划需求不能以 selection 查询；请使用 --intent itinerary');
  const prefix = '行程规划，按天安排交通、住宿与景点。';
  if (travel && intent === 'itinerary' && !extra.startsWith(prefix)) extra = `${prefix}${extra}`;
  // The shared CLI limits extra to 500 characters. Never silently discard user constraints.
  if (extra.length > 500) throw new Error('extra 超过 500 字，请保留行程意图和已确认条件后精简重试');
  if (searchQuery.length > 2000) throw new Error('query 超过 2000 字，请保留查询对象和已确认条件后精简重试');
  return { intent: intent || 'selection', args: extra ? [...kept, '--extra', extra] : kept };
}

module.exports = { applyTrainDateDefault, classifyResponseFlow, hasOption, isItineraryRequest, optionText, prepareQuery, trainDateState };
