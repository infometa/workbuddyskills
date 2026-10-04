#!/usr/bin/env node
'use strict';

const childProcess = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const START_MARKER = 'TC_CHENGXIN_COUPON_JSON_START';
const END_MARKER = 'TC_CHENGXIN_COUPON_JSON_END';
const CACHE_VERSION = 3;
const COMPATIBLE_CACHE_VERSIONS = new Set([1, 2, CACHE_VERSION]);
const CACHE_FILE_NAME = 'today-coupons-cache.json';

function text(value, fallback = '-') {
  const normalized = value === null || value === undefined ? '' : String(value).trim();
  return normalized || fallback;
}

function numberText(value) {
  if (value === null || value === undefined || value === '') return '';
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return String(value);
  return Number.isInteger(parsed) ? String(parsed) : String(parsed).replace(/0+$/, '').replace(/\.$/, '');
}

function cell(value) {
  return text(value).replace(/\|/g, '\\|').replace(/\r?\n/g, '；');
}

function validity(start, end) {
  if (start && end) return `${start} 至 ${end}`;
  if (end) return `${end} 前`;
  return '以券面展示为准';
}

function positiveNumberText(value) {
  const normalized = numberText(value);
  return normalized && Number(normalized) > 0 ? normalized : '';
}

function couponRule(coupon, factorCode) {
  const rules = Array.isArray(coupon && coupon.rules) ? coupon.rules : [];
  return rules.find((rule) => rule && Number(rule.factorCode) === factorCode) || null;
}

function discountRate(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0 || parsed > 100) return '';
  const rate = parsed > 10 ? parsed / 10 : parsed;
  return `${numberText(rate)}折`;
}

/**
 * factorCode=58 的 leftValue 是折扣值，rightValue 是“使用门槛,最高优惠金额”。
 * 折扣券的 amount 同样是最高优惠金额，不能作为固定面额展示。
 */
function discountBenefit(coupon) {
  const rule = couponRule(coupon, 58);
  const rate = discountRate(rule && rule.leftValue);
  const ruleValues = String((rule && rule.rightValue) || '')
    .split(',')
    .map((value) => positiveNumberText(value));
  const threshold = ruleValues[0] || '';
  const maxDiscount = ruleValues[1] || positiveNumberText(coupon.amount);
  const conditions = [];
  if (threshold) conditions.push(`满${threshold}元可用`);
  if (maxDiscount) conditions.push(`最高优惠${maxDiscount}元`);
  if (rate && conditions.length) return `${rate}（${conditions.join('，')}）`;
  if (rate) return rate;
  if (coupon.bonusIntro) return text(coupon.bonusIntro);
  if (conditions.length) return `折扣券（${conditions.join('，')}，具体规则以券面为准）`;
  return '折扣券（具体规则以券面为准）';
}

function claimBenefit(coupon) {
  if (!coupon) return '以领取结果为准';
  const preferentialType = String(coupon.preferentialType || '').trim();
  if (preferentialType === '1') return discountBenefit(coupon);
  const amount = positiveNumberText(coupon.amount);
  const threshold = positiveNumberText(coupon.thresholdAmount);
  const couponType = coupon.couponType === null || coupon.couponType === undefined
    ? '' : String(coupon.couponType).trim();
  if (couponType === '0' && amount) {
    return threshold ? `${amount}元代金券（满${threshold}元可用）` : `${amount}元代金券`;
  }
  if (couponType === '1') return discountBenefit(coupon);
  if (amount) return preferentialType ? `${amount}元红包` : `${amount}元`;
  return text(coupon.bonusIntro || coupon.bonusDetails, '以券面展示为准');
}

function claimStatus(item) {
  if (item.status === 'SUCCESS') return '领取成功';
  if (item.status === 'ALREADY_PROCESSED') return '本次请求已处理';
  if (item.status === 'ALREADY_USED') return '该批次已使用，不能再次领取';
  if (item.status === 'LIMIT_REACHED') return text(item.message, '已达到领取上限');
  if (item.status === 'NOT_AVAILABLE') return text(item.message, '活动暂不可领取');
  if (item.status === 'VERIFICATION_REQUIRED') return text(item.message, '需要完成实名信息');
  return text(item.message, '领取失败');
}

function workbuddyDirectory(env = process.env) {
  return String(env.WORKBUDDY_CONFIG_DIR || '').trim() || path.join(os.homedir(), '.workbuddy');
}

function couponCacheFile(env = process.env) {
  return path.join(
    workbuddyDirectory(env),
    'credentials',
    'tc-chengxin-travel-expert',
    CACHE_FILE_NAME
  );
}

function chinaDate(now = Date.now()) {
  const value = typeof now === 'function' ? now() : now;
  const timestamp = value instanceof Date ? value.getTime() : Number(value);
  const resolved = Number.isFinite(timestamp) ? timestamp : Date.now();
  return new Date(resolved + (8 * 60 * 60 * 1000)).toISOString().slice(0, 10);
}

function accountFingerprint(apiKey) {
  return crypto.createHash('sha256').update(String(apiKey || ''), 'utf8').digest('hex');
}

function successfulClaimItems(data) {
  if (!Array.isArray(data && data.results)) return [];
  return data.results.flatMap((item) => {
    if (!item || item.status !== 'SUCCESS') return [];
    const coupons = Array.isArray(item.coupons) && item.coupons.length
      ? item.coupons.filter(Boolean)
      : item.coupon ? [item.coupon] : [];
    return coupons.map((coupon) => {
      const expanded = { ...item, coupon };
      delete expanded.coupons;
      return expanded;
    });
  });
}

function activityKey(item) {
  if (!item) return '';
  const activityId = String(item.activityId || '').trim();
  const coupon = item.coupon || {};
  const couponId = String(coupon.couponCode || coupon.incomeId || coupon.discountId || '').trim();
  if (activityId && couponId) return `activity:${activityId}:coupon:${couponId}`;
  const identity = [coupon.incomeId, coupon.discountId, coupon.name, coupon.startTime, coupon.endTime]
    .map((value) => String(value || '').trim())
    .join('|');
  if (activityId && identity.replace(/\|/g, '')) return `activity:${activityId}:coupon:${identity}`;
  if (activityId) return `activity:${activityId}`;
  return identity.replace(/\|/g, '') ? `coupon:${identity}` : '';
}

function displayClaimState(item, repeatClaim) {
  if (item && item.claimState === 'NEW') return '**本次新领**';
  if (item && item.claimState === 'CLAIMED_TODAY') return '今日已领';
  return repeatClaim ? '今日已领' : '**本次新领**';
}

function isTravelItem(item) {
  const coupon = item && item.coupon ? item.coupon : {};
  const sourceType = String(item && item.sourceType || '').trim().toUpperCase();
  if (sourceType === 'TRAVEL') return true;
  return [item && item.activityId, coupon.batchNo, coupon.couponCode]
    .some((value) => /^AP_/i.test(String(value || '').trim()));
}

function businessType(item) {
  return isTravelItem(item) ? '出行' : '住宿';
}

function couponName(item) {
  const coupon = item && item.coupon ? item.coupon : {};
  return `**${text(coupon.name || `活动 ${item && item.activityId}`)}**`;
}

function businessSummary(items) {
  const hotelCount = items.filter((item) => !isTravelItem(item)).length;
  const travelCount = items.filter((item) => isTravelItem(item)).length;
  const parts = [];
  if (hotelCount > 0) parts.push(`住宿 ${hotelCount} 个`);
  if (travelCount > 0) parts.push(`出行 ${travelCount} 个`);
  return parts.join('、');
}

function combinedGuide(items) {
  const hasHotelCoupon = items.some((item) => !isTravelItem(item));
  const hasTravelCoupon = items.some((item) => isTravelItem(item));
  const lines = ['#### 💡 使用提示', ''];
  if (hasHotelCoupon) lines.push('- 🏨 **住宿券**：可用于符合券面规则的酒店或民宿订单。');
  if (hasTravelCoupon) lines.push('- ✈️ **出行券**：可用于符合券面规则的国内机票订单。');
  const queryGuide = hasHotelCoupon && hasTravelCoupon
    ? '告诉我住宿目的地和入住、离店日期，或机票出发地、目的地和出发日期即可。'
    : hasHotelCoupon
      ? '告诉我目的地和入住、离店日期即可。'
      : '告诉我出发地、目的地和出发日期即可。';
  lines.push(`- 🔎 **继续查询**：${queryGuide}`);
  lines.push('- 📱 **查看入口**：同程旅行 App「我的 → 优惠券/红包」。');
  lines.push('', '> ℹ️ 具体适用范围和最终价格以下单页为准。');
  return lines.join('\n');
}

function prepareFirstClaimData(data) {
  const successful = successfulClaimItems(data).map((item) => ({
    ...item,
    claimState: item.claimState === 'CLAIMED_TODAY' ? 'CLAIMED_TODAY' : 'NEW'
  }));
  if (successful.length === 0) {
    return {
      ...data,
      results: [],
      totalCount: 0,
      successCount: 0,
      newlyClaimedCount: 0,
      previouslyClaimedCount: 0
    };
  }
  const serverNewCount = successful.filter((item) => item.claimState === 'NEW').length;
  const serverPreviousCount = successful.length - serverNewCount;
  return {
    ...data,
    results: successful,
    totalCount: successful.length,
    successCount: successful.length,
    newlyClaimedCount: Number.isFinite(Number(data.newlyClaimedCount))
      ? Number(data.newlyClaimedCount) : serverNewCount,
    previouslyClaimedCount: Number.isFinite(Number(data.previouslyClaimedCount))
      ? Number(data.previouslyClaimedCount) : serverPreviousCount,
    repeatClaim: Boolean(data.repeatClaim || serverPreviousCount > 0)
  };
}

/**
 * 以 activityId + couponCode 为主键合并当天已领与本次增量结果。
 * 旧活动通常只返回 ALREADY_PROCESSED 且没有券详情，因此必须保留缓存中的完整券面。
 */
function mergeClaimData(cachedData, freshData) {
  const previousItems = successfulClaimItems(cachedData);
  const previousByKey = new Map();
  previousItems.forEach((item) => {
    const key = activityKey(item);
    if (key && !previousByKey.has(key)) previousByKey.set(key, item);
  });

  const newItems = [];
  const recoveredItems = [];
  const newKeys = new Set();
  // 先展开 coupons[]，避免当天新增的礼包活动只保留兼容字段 coupon 中的第一张券。
  const freshItems = successfulClaimItems(freshData);
  freshItems.forEach((item) => {
    const key = activityKey(item);
    if (key && previousByKey.has(key)) return;
    if (key && newKeys.has(key)) return;
    if (key) newKeys.add(key);
    if (item.claimState === 'CLAIMED_TODAY') {
      recoveredItems.push({ ...item, claimState: 'CLAIMED_TODAY' });
    } else {
      newItems.push({ ...item, claimState: 'NEW' });
    }
  });

  const retainedItems = previousItems.map((item) => ({ ...item, claimState: 'CLAIMED_TODAY' }));
  const combined = [...newItems, ...recoveredItems, ...retainedItems];
  if (combined.length === 0) {
    return {
      ...freshData,
      repeatClaim: true,
      newlyClaimedCount: 0,
      previouslyClaimedCount: 0
    };
  }
  return {
    ...freshData,
    success: true,
    results: combined,
    totalCount: combined.length,
    successCount: combined.length,
    newlyClaimedCount: newItems.length,
    previouslyClaimedCount: recoveredItems.length + retainedItems.length,
    repeatClaim: true,
    cached: false
  };
}

/**
 * 只复用当天、当前登录凭证的成功领券结果，避免同设备切换账号后串用。
 * 凭证本身不落盘，缓存只保存不可逆摘要和 Gateway 已返回的领券结果。
 */
function loadTodayClaimCache(apiKey, options = {}) {
  const env = options.env || process.env;
  const cacheFile = options.cacheFile || couponCacheFile(env);
  try {
    const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
    if (!cache
      || !COMPATIBLE_CACHE_VERSIONS.has(cache.version)
      || cache.date !== chinaDate(options.now)
      || cache.accountFingerprint !== accountFingerprint(apiKey)
      || successfulClaimItems(cache.data).length === 0) {
      return null;
    }
    return {
      ...cache.data,
      requestId: String(cache.requestId || cache.data.requestId || '').trim(),
      repeatClaim: true,
      cached: true,
      newlyClaimedCount: 0,
      previouslyClaimedCount: successfulClaimItems(cache.data).length,
      results: successfulClaimItems(cache.data).map((item) => ({
        ...item,
        claimState: 'CLAIMED_TODAY'
      }))
    };
  } catch (_) {
    // 缓存缺失或损坏时退化为正常请求 Gateway，不阻断领券。
    return null;
  }
}

/** 保存当天累计领取结果和稳定 requestId，供后续增量检查复用。 */
function saveTodayClaimCache(apiKey, data, options = {}) {
  if (successfulClaimItems(data).length === 0) return false;
  const env = options.env || process.env;
  const cacheFile = options.cacheFile || couponCacheFile(env);
  try {
    fs.mkdirSync(path.dirname(cacheFile), { recursive: true, mode: 0o700 });
    fs.writeFileSync(cacheFile, JSON.stringify({
      version: CACHE_VERSION,
      date: chinaDate(options.now),
      accountFingerprint: accountFingerprint(apiKey),
      requestId: String(options.requestId || data.requestId || '').trim(),
      data
    }), { encoding: 'utf8', mode: 0o600 });
    try { fs.chmodSync(cacheFile, 0o600); } catch (_) { /* Windows 不依赖 POSIX 权限 */ }
    return true;
  } catch (_) {
    // 本地缓存写入失败不影响本次已完成的领券结果。
    return false;
  }
}

function formatClaimMarkdown(data) {
  if (!data || data.success === false) {
    const trace = data && data.traceId ? `\n\n问题编号：${data.traceId}` : '';
    return `这次暂时没能领取优惠券/红包：${text(data && data.message, '服务暂时不可用')}${trace}`;
  }
  const items = Array.isArray(data.results) ? data.results : [];
  const handledCount = Number(data.successCount || 0);
  const successfulItems = successfulClaimItems(data);
  const newlyClaimedCount = Number.isFinite(Number(data.newlyClaimedCount))
    ? Number(data.newlyClaimedCount)
    : successfulItems.length;
  const todayCount = successfulItems.length;
  if (todayCount === 0) {
    const historyUnavailable = data.accountDayHistoryAvailable !== true;
    const lines = [
      '### 🎁 优惠券领取结果',
      '',
      'ℹ️ 这次没有新增领取成功的优惠券/红包。'
    ];
    if (historyUnavailable) {
      lines.push(
        '',
        '如果你今天已在其他设备领取过，当前暂未能取回当时的券面明细。'
      );
    }
    lines.push('', '- 📱 **查看入口**：同程旅行 App「我的 → 优惠券/红包」。');
    return lines.join('\n');
  }
  const typeSummary = businessSummary(successfulItems);
  const typeSuffix = typeSummary ? `：${typeSummary}` : '';
  // 部分成功时只向用户展示实际到账的券，失败明细仍由 traceId 留在网关日志中排查。
  const displayedItems = successfulItems;
  let title = '这次没有新增领取成功的优惠券/红包。';
  if (data.refreshFailed && todayCount > 0) {
    title = `已显示今天领取的 ${todayCount} 个优惠券/红包${typeSuffix}；本次新增活动检查暂未完成。`;
  } else if (data.repeatClaim && newlyClaimedCount > 0) {
    title = `本次新领 ${newlyClaimedCount} 个，今天累计已领取 ${todayCount} 个优惠券/红包${typeSuffix}。`;
  } else if (data.repeatClaim && todayCount > 0) {
    title = `今天已领取 ${todayCount} 个优惠券/红包${typeSuffix}，暂未发现新增可领活动。`;
  } else if (newlyClaimedCount > 0) title = `已帮你领取 ${newlyClaimedCount} 个优惠券/红包${typeSuffix}。`;
  else if (handledCount > 0) title = `你的领取请求已处理，共 ${handledCount} 个优惠券/红包：`;
  const summary = `✅ ${title}`;
  const lines = ['### 🎁 优惠券领取结果', '', summary, '', '| 状态 | 优惠券/红包 | 优惠内容 | 有效期 |', '| --- | --- | --- | --- |'];
  displayedItems.forEach((item) => {
    const coupon = item.coupon || {};
    const status = item.status === 'SUCCESS'
      ? displayClaimState(item, Boolean(data.repeatClaim))
      : claimStatus(item);
    lines.push(`| ${status} | ${cell(couponName(item))} | ${cell(claimBenefit(coupon))} | ${cell(validity(coupon.startTime, coupon.endTime))} |`);
  });
  lines.push('', combinedGuide(successfulItems));
  return lines.join('\n');
}

function isAuthError(error) {
  return Boolean(error && (error.code === 'CHENGXIN_AUTH_REQUIRED' || error.statusCode === 401));
}

function cachedFallback(cached, error) {
  const data = {
    ...cached,
    refreshFailed: true,
    refreshMessage: text(error && error.message, '新增活动检查暂不可用')
  };
  return {
    markdown: formatClaimMarkdown(data),
    traceId: cached.traceId || '',
    success: true,
    cached: true,
    refreshFailed: true,
    newlyClaimedCount: 0
  };
}

function tokenEnvironment(env = process.env, injectedApiKey = '') {
  if (injectedApiKey) return { ...env, CHENGXIN_API_KEY: String(injectedApiKey) };
  const { cliInvocation } = require('../../tc-chengxin-auth/scripts/ensure-auth');
  const invocation = cliInvocation(process.platform, env);
  const result = childProcess.spawnSync(invocation.command, [...invocation.prefixArgs, 'token'], {
    env, encoding: 'utf8', windowsHide: true, timeout: 15000
  });
  const apiKey = String(result.stdout || '').trim();
  if (result.status !== 0 || !apiKey) return null;
  return { ...env, CHENGXIN_API_KEY: apiKey };
}

async function execute(action, options = {}) {
  if (action !== 'claim') throw new Error('优惠券 Skill 只支持领取，不支持查询已有优惠券');
  const env = tokenEnvironment(options.env || process.env, options.apiKey);
  if (!env) return { reauthRequired: true };
  const cached = loadTodayClaimCache(env.CHENGXIN_API_KEY, {
    env,
    cacheFile: options.cacheFile,
    now: options.now
  });
  process.env.CHENGXIN_API_KEY = env.CHENGXIN_API_KEY;
  process.env.CHENGXIN_WORKBUDDY_EXPERT = '1';
  process.env.CHENGXIN_CALLER_CHANNEL = 'workbuddy';
  const apiClient = options.apiClient || require('./lib/api-client');
  const requestId = (cached && cached.requestId)
    || options.requestId
    || crypto.randomBytes(16).toString('hex');
  let envelope;
  try {
    envelope = await apiClient.call_api('/coupon/claim', { requestId });
  } catch (error) {
    if (isAuthError(error) || !cached) throw error;
    return cachedFallback(cached, error);
  }
  if (!envelope || envelope.code !== 0 || !envelope.data) {
    if (cached) return cachedFallback(cached, new Error(text(envelope && envelope.message, 'Gateway返回异常')));
    throw new Error(text(envelope && envelope.message, 'Gateway返回异常'));
  }
  const claimData = cached
    ? mergeClaimData(cached, envelope.data)
    : prepareFirstClaimData(envelope.data);
  const effectiveRequestId = String(envelope.data.requestId || requestId).trim() || requestId;
  claimData.requestId = effectiveRequestId;
  saveTodayClaimCache(env.CHENGXIN_API_KEY, claimData, {
    env,
    cacheFile: options.cacheFile,
    now: options.now,
    requestId: effectiveRequestId
  });
  const markdown = formatClaimMarkdown(claimData);
  return {
    markdown,
    traceId: claimData.traceId || '',
    success: claimData.success !== false,
    cached: Boolean(cached),
    newlyClaimedCount: claimData.newlyClaimedCount || 0
  };
}

function deliveryReceipt(result) {
  return {
    type: 'workbuddy_coupon_delivery',
    nextAction: 'reply',
    markdown: result.markdown,
    responsePolicy: {
      finalAnswerField: 'markdown',
      mode: 'verbatim',
      mustDisplayInChat: true,
      mustNotRewriteMarkdown: true,
      forbidRawResultReconstruction: true
    }
  };
}

async function run(argv = process.argv.slice(2)) {
  const action = argv[0];
  if (action !== 'claim') throw new Error('用法: coupon.js claim');
  try {
    const result = await execute(action);
    if (result.reauthRequired) {
      process.stdout.write('TC_CHENGXIN_REAUTH_REQUIRED\n');
      return 1;
    }
    process.stdout.write(`${START_MARKER}\n${JSON.stringify(deliveryReceipt(result))}\n${END_MARKER}\n`);
    return 0;
  } catch (error) {
    if (isAuthError(error)) {
      process.stdout.write('TC_CHENGXIN_REAUTH_REQUIRED\n');
      return 1;
    }
    throw error;
  }
}

if (require.main === module) {
  run().then((code) => { process.exitCode = code; }).catch((error) => {
    console.error(`优惠券/红包操作失败：${error.message}`);
    process.exitCode = 1;
  });
}

module.exports = {
  accountFingerprint,
  businessType,
  chinaDate,
  claimBenefit,
  combinedGuide,
  couponCacheFile,
  discountBenefit,
  discountRate,
  deliveryReceipt,
  execute,
  formatClaimMarkdown,
  businessSummary,
  loadTodayClaimCache,
  mergeClaimData,
  prepareFirstClaimData,
  run,
  saveTodayClaimCache,
  tokenEnvironment,
  validity
};
