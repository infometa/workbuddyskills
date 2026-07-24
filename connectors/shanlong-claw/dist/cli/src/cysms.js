"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.refreshCySAuthAfterSlCredentialSync = refreshCySAuthAfterSlCredentialSync;
exports.executeCysmsCommand = executeCysmsCommand;
const body_1 = require("./body");
const commands_1 = require("./commands");
const cysms_context_1 = require("./cysms-context");
const cysms_store_cache_1 = require("./cysms-store-cache");
const fs_1 = require("fs");
const env_1 = require("./env");
const flags_1 = require("./flags");
const logger_1 = require("./logger");
const output_1 = require("./output");
const parse_cysms_json_1 = require("./parse-cysms-json");
const request_1 = require("./request");
const token_cache_1 = require("./token-cache");
const DEFAULT_CYSMS_APP_ID = 'ef724f5da71f4959ba1d50d39eeced74';
const DEFAULT_CYSMS_ACCESS_ID = 'f9aa95fd67f247898a36c87baa8cd48b';
const DEFAULT_CYSMS_BASE = 'https://cysms.wuuxiang.com';
const ACCESSTOKEN_PATH = '/api/auth/accesstoken';
const GETSHOPS_PATH = '/api/datatransfer/getshops';
/** ShowDoc 营业情况汇总 https://doc.wuuxiang.com/showdoc/web/#/46/14375 */
const GET_BUSINESS_SITUATION_PATH = '/api/datatransfer/getBusinessSituation';
/** ShowDoc 消费区域、客位列表 https://doc.wuuxiang.com/showdoc/web/#/46/6642 */
const GET_SERVICE_AREA_PATH = '/api/datatransfer/getServiceArea';
/** ShowDoc 菜品估清明细：POST /api/datatransfer/getitemselloutdata */
const GET_ITEM_SELLOUT_DATA_PATH = '/api/datatransfer/getitemselloutdata';
/** ShowDoc 预订信息明细 https://doc.wuuxiang.com/showdoc/web/#/46/17236 */
const GET_BOOK_ORDER_DETAIL_PATH = '/api/datatransfer/getBookOrderDetailData';
/** ShowDoc 账单明细查询 getserialdata https://doc.wuuxiang.com/showdoc/web/#/46/460；结算明细 settleDetail、品项打折方案优惠明细 discountDetail 等字段见 #/46/444 */
const GET_SERIAL_DATA_PATH = '/api/datatransfer/getserialdata';
/** ShowDoc 团购券接口 getO2oTicket https://doc.wuuxiang.com/showdoc/web/#/46/24327 */
const GET_O2O_TICKET_PATH = '/api/datatransfer/getO2oTicket';
/** token.json 根下仅保留 auth；门店列表与已确认门店写入当前工作区 cache/ */
const TOKEN_JSON_CY_S = 'cyS';
const CY_S_AUTH = 'auth';
const LEGACY_APP_ID = 'cyS_appid';
const LEGACY_ACCESS_ID = 'cyS_accessid';
const EXPIRY_SKEW_MS = 60000;
/** SL 同步后自动 getshops 分页上限（pageSize 最大 50） */
const MAX_GETSHOPS_SYNC_PAGES = 200;
/** 旧版平铺在 cyS 根上的鉴权字段，用于一次性迁移到 cyS.auth */
const AUTH_FLAT_KEYS = new Set([
    'appid',
    'accessid',
    'msg',
    'code',
    'access_token',
    'refresh_token',
    'expires_in',
    'cached_at',
    'expires_at',
]);
function isPlainObject(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function resolveCysmsCommandDefinition(action) {
    if (!action) {
        return undefined;
    }
    return (0, commands_1.loadCommands)('cysms')?.commands.find((item) => item.action === action);
}
function resolveCysmsBuiltinAction(action) {
    return resolveCysmsCommandDefinition(action)?.source_function || action || '';
}
function loadCySRoot() {
    const v = (0, token_cache_1.loadTokenValue)(TOKEN_JSON_CY_S);
    return isPlainObject(v) ? { ...v } : {};
}
function readCysmsStringFromTokenJson(key) {
    const v = (0, token_cache_1.loadTokenValue)(key);
    return typeof v === 'string' && v.trim() ? v.trim() : '';
}
/** 从 cyS.auth 读取；若无 auth 则从旧版 cyS 根上平铺字段迁移读取 */
function extractCySAuthSlice(cyS) {
    const nested = cyS[CY_S_AUTH];
    if (isPlainObject(nested)) {
        return { ...nested };
    }
    const fromFlat = {};
    for (const k of AUTH_FLAT_KEYS) {
        if (cyS[k] !== undefined) {
            fromFlat[k] = cyS[k];
        }
    }
    return fromFlat;
}
function readAppIdFromStore() {
    const auth = extractCySAuthSlice(loadCySRoot());
    const fromAuth = auth.appid;
    if (typeof fromAuth === 'string' && fromAuth.trim()) {
        return fromAuth.trim();
    }
    return readCysmsStringFromTokenJson(LEGACY_APP_ID);
}
function readAccessIdFromStore() {
    const auth = extractCySAuthSlice(loadCySRoot());
    const fromAuth = auth.accessid;
    if (typeof fromAuth === 'string' && fromAuth.trim()) {
        return fromAuth.trim();
    }
    return readCysmsStringFromTokenJson(LEGACY_ACCESS_ID);
}
function getExpiresDeadlineMs(auth) {
    if (typeof auth.expires_at === 'number' && Number.isFinite(auth.expires_at)) {
        return auth.expires_at;
    }
    const cachedAt = auth.cached_at;
    const expiresIn = auth.expires_in;
    if (typeof cachedAt === 'string' && expiresIn != null) {
        const t = Date.parse(cachedAt);
        const sec = Number(expiresIn);
        if (Number.isFinite(t) && Number.isFinite(sec) && sec > 0) {
            return t + sec * 1000 - EXPIRY_SKEW_MS;
        }
    }
    return null;
}
function getCachedCySPayloadIfValid(force) {
    if (force) {
        return null;
    }
    const auth = extractCySAuthSlice(loadCySRoot());
    const tok = auth.access_token;
    if (typeof tok !== 'string' || !tok.trim()) {
        return null;
    }
    const deadline = getExpiresDeadlineMs(auth);
    if (deadline === null || Date.now() >= deadline) {
        return null;
    }
    return {
        msg: auth.msg ?? 'success',
        code: auth.code ?? '0',
        access_token: tok,
        refresh_token: typeof auth.refresh_token === 'string' ? auth.refresh_token : '',
        expires_in: typeof auth.expires_in === 'number' ? auth.expires_in : Number(auth.expires_in) || 0,
        _from_cache: true,
    };
}
function pickApiFieldsForCyS(result) {
    if (!isPlainObject(result)) {
        return {};
    }
    const r = result;
    const out = {};
    for (const k of ['msg', 'code', 'access_token', 'refresh_token', 'expires_in']) {
        if (r[k] !== undefined) {
            out[k] = r[k];
        }
    }
    return out;
}
function persistCySMerged(apiSlice, appid, accessid) {
    const prevRoot = loadCySRoot();
    const prevAuth = extractCySAuthSlice(prevRoot);
    const expIn = Number(apiSlice.expires_in ?? prevAuth.expires_in) || 0;
    const newAuth = {
        ...prevAuth,
        appid,
        accessid,
        ...apiSlice,
        cached_at: new Date().toISOString(),
    };
    newAuth.expires_at = expIn > 0 ? Date.now() + expIn * 1000 - EXPIRY_SKEW_MS : null;
    const nextRoot = {
        [CY_S_AUTH]: newAuth,
    };
    (0, token_cache_1.saveTokenValue)(TOKEN_JSON_CY_S, nextRoot);
    if ((0, token_cache_1.loadTokenValue)(LEGACY_APP_ID) !== undefined) {
        (0, token_cache_1.saveTokenValue)(LEGACY_APP_ID, undefined);
    }
    if ((0, token_cache_1.loadTokenValue)(LEGACY_ACCESS_ID) !== undefined) {
        (0, token_cache_1.saveTokenValue)(LEGACY_ACCESS_ID, undefined);
    }
}
function isAccesstokenSuccess(result) {
    if (!isPlainObject(result)) {
        return false;
    }
    const code = result.code;
    const okCode = code === '0' || code === 0 || code === '200' || code === 200;
    const tok = readCysmsTokenString(result);
    return !!tok && okCode;
}
function printCysmsUsage() {
    console.log(`用法:
  sl cysms accesstoken [--appid <id>] [--accessid <id>] [--format json]
                       [--force] [--base-url <url>] [--skip-stores]
  sl cysms stores-refresh [--center-id <id>] [--group-no <id>] [--omit-group-no]
                          [--store-id <id>] [--store-name <名称>] [--brand-id <id>]
                          [--base-url <url>]
  sl cysms getshops [--center-id <id>] [--page-no <n>] [--page-size <n>] [--group-no <id>] [--omit-group-no]
                    [--store-id <id>] [--store-name <名称>] [--brand-id <id>]
                    [--format json] [--force] [--skip-sync] [--base-url <url>]
  sl cysms store-region [--store-name <名称>] [--store-id <id>] [--format json] [--only-primary]
  sl cysms store-find [--store <模糊名称/编号>] [--format json]
  sl cysms store-use  [--store <模糊名称/编号>] [--format json]
  sl cysms business-situation [--begin-date <yyyy-MM-dd HH:mm:ss>] [--end-date <...>] [--settle-date <yyyy-MM-dd>] [--date-type 1|2]
                              [--sale-type <n>] [--item-type <n>] [--item-class-type <n>] [--discounted true|false] [--is-disc-include-not-income true|false]
                              [--center-id ...] [--group-no ...] [--omit-group-no] [--store-id ...] [--store-name ...] [--format json] [--force] [--base-url <url>]
  sl cysms service-area [--page-no <n>] [--page-size <n>] [--all-pages]
                        [--center-id ...] [--group-no ...] [--omit-group-no] [--store-id ...] [--store-name ...] [--format json] [--force] [--base-url <url>]
  sl cysms service-area-list [--page-no <n>] [--page-size <n>] [--all-pages]
                             [--center-id ...] [--group-no ...] [--omit-group-no] [--store-id ...] [--store-name ...] [--format json] [--force] [--base-url <url>]
  sl cysms service-area-point-list [--page-no <n>] [--page-size <n>] [--all-pages]
                                   [--center-id ...] [--group-no ...] [--omit-group-no] [--store-id ...] [--store-name ...] [--format json] [--force] [--base-url <url>]
  sl cysms item-sellout-data [--time-begin <yyyy-MM-dd HH:mm:ss>] [--time-end <yyyy-MM-dd HH:mm:ss>] [--page-no <n>] [--page-size <n>] [--all-pages]
                             [--center-id ...] [--group-no ...] [--omit-group-no] [--store-id ...] [--store-name ...] [--format json] [--force] [--base-url <url>]
  sl cysms book-order-detail [--begin <yyyy-MM-dd HH:mm:ss> --end <yyyy-MM-dd HH:mm:ss>]
                             [--telephone <手机号>] [--order-time-type <n>]
                             [--center-id ...] [--group-no ...] [--omit-group-no] [--store-id ...] [--store-name ...] [--format json|profile-batch] [--force] [--base-url <url>]
  sl cysms o2o-ticket [--begin <yyyy-MM-dd HH:mm:ss> --end <yyyy-MM-dd HH:mm:ss>] [--seller <1-9>] [--page-no <n>] [--page-size <n>] [--all-pages] [--single-page true|1]
                      [--print-request true|1] [--center-id ...] [--group-no ...] [--omit-group-no] [--store-id ...] [--store-name ...] [--format json] [--force] [--base-url <url>]
  sl cysms o2o-ticket-summary  （时间、分页、门店与 **o2o-ticket** 相同；先拉全量 ticketDataList 再过滤汇总；**--only-redeemed true** 仅保留已核销；**--ticket-types 1,2**；**--ticket-counts 0,1**；stdout schema **cy7.cysms.o2o_ticket_summary.v1**；stdin 见 **process-o2o-ticket-summary-json**）
  sl cysms process-o2o-ticket-json  （stdin JSON；stdout 与 o2o-ticket 一致：ticketDataListRaw + ticketDataList，仍走 output_filter）
  sl cysms process-o2o-ticket-summary-json  （stdin JSON + 过滤 flags 同 o2o-ticket-summary；无网络）
  sl cysms serial-data [--begin-date|--begin <...> --end-date|--end <...>] [--settle-date <yyyy-MM-dd> --date-type 1|2]
                       [--page-no <n>] [--page-size <n>] [--all-pages] [--print-request true|1]
                       [--is-data-filtering 0|1] [--order-type <csv>] [--need-pkg-detail 0|1] [--is-query-unsettled 0|1]
                       [--center-id ...] [--group-no ...] [--omit-group-no] [--store-id ...] [--store-name ...]
                       [--format json|checkout-anomaly-summary|abnormal-bill-summary] [--force] [--base-url <url>]
  sl cysms serial-data-openclaw  （参数同 serial-data；未指定时间窗时默认本机自然当日 00:00~23:59 且 dateType=5 最后上传口径；可查昨日等须显式 --begin-date/--end-date 或 --settle-date）
  sl cysms serial-data-items     （参数同 serial-data；未指定时间窗时默认当日全日 + dateType=5 最后上传口径，与 serial-data-openclaw 一致；有 begin/end 时建议显式 --date-type 5；stdout：**仅** itemListRaw + itemList（品项明细行，经 output_filter）；**不再**含 item_qty_summary；菜品销量汇总请用 **serial-data-item-qty-summary**；默认 --page-no 1 时若 pageInfo 表明尚有账单则自动顺序拉齐并合并，后续页与首屏 **同一 pageSize**；仅首屏请加 --single-page true）
  sl cysms serial-data-item-income  （参数、分页与 serial-data-items 完全相同；stdout：**仅** itemIncomeListRaw + itemIncomeList，为 bill.item[] 展平行并补账单 bs_id/sc_id；含 ShowDoc #/46/444 品项金额字段 orig_subtotal、disc_money、income_money 等（经 output_filter）；stdin 整形见 **process-serial-data-item-income-json**）
  sl cysms serial-data-item-qty-summary  （参数、分页与 serial-data-items 完全相同；stdout：**仅** item_qty_summary（按 item_id 合计 last_qty）+ item_qty_summary_by_name（按菜品显示名合计 last_qty，同名不同 id 合并）+ bill_count、item_row_count、pageInfo；**不**输出 item 明细行；可加 --omit-item-qty-summary / --omit-item-qty-summary-by-name）
  sl cysms serial-data-settle-details  （参数同 serial-data；时间默认与 serial-data-items 一致；stdout：settleListRaw + settleList；结算明细 settleDetail 见 ShowDoc #/46/444，父接口 #/46/460；分页与 --single-page 语义同 serial-data-items）
  sl cysms serial-data-discount-details  （参数同 serial-data；时间默认与 serial-data-items 一致；stdout：discountListRaw + discountList；ShowDoc #/46/460 品项打折方案优惠明细 discountDetail 展平；分页与 --single-page 语义同 serial-data-items）
  sl cysms serial-data-fulloff-details  （参数同 serial-data；时间默认与 serial-data-items 一致；stdout：fulloffListRaw + fulloffList；ShowDoc #/46/460 满减定额优惠明细 fulloffDetail 展平；分页与 --single-page 语义同 serial-data-items）
  sl cysms serial-data-promote-details  （参数同 serial-data；时间默认与 serial-data-items 一致；stdout：promoteListRaw + promoteList；ShowDoc #/46/460 促销方案优惠明细 promoteDetail 展平；分页与 --single-page 语义同 serial-data-items）
  sl cysms serial-data-item-method-details  （参数同 serial-data；时间默认与 serial-data-items 一致；stdout：itemMethodListRaw + itemMethodList；ShowDoc #/46/460 菜品做法明细 itemMethodData 展平（自 bill.item[]）；分页与 --single-page 语义同 serial-data-items）
  sl cysms serial-data-payway-income-summary  （参数、分页与 serial-data-settle-details 相同；stdout：按结算方式与销售类型汇总 settleDetail 的 pay_money 实收、income_money 纯收；默认仅 settle_state=1 或缺省且 delflg 非 1/2；**--include-all-settle-states true** 含返位/预结；stdin 见 **process-serial-data-payway-income-summary-json**）
  sl cysms serial-data-reversal-settlement-summary  （参数、分页与 serial-data-payway-income-summary 相同；仅 **settle_state=-1 返位结算** 账单：输出订单量、按 waiter/salesman 分桶张数、settleDetail 按结算方式/销售类型金额汇总；结算行计入等同 payway 的 include-all-settle-states；stdin 见 **process-serial-data-reversal-settlement-summary-json**）
  sl cysms process-serial-data-items-json  （stdin JSON；stdout 与 serial-data-items 一致：**仅** itemListRaw + itemList，仍走 output_filter）
  sl cysms process-serial-data-item-income-json  （stdin JSON；stdout 与 serial-data-item-income 一致：**仅** itemIncomeListRaw + itemIncomeList；整包 getserialdata 时展平行补 bs_id/sc_id；仍走 output_filter）
  sl cysms process-serial-data-item-qty-summary-json  （stdin JSON；stdout 与 serial-data-item-qty-summary 一致：仅汇总数组 + 计数；支持 --omit-item-qty-summary / --omit-item-qty-summary-by-name）
  sl cysms process-serial-data-settle-details-json  （stdin JSON；stdout 同上含 settleListRaw + settleList）
  sl cysms process-serial-data-discount-details-json  （stdin JSON；stdout 同上含 discountListRaw + discountList）
  sl cysms process-serial-data-fulloff-details-json  （stdin JSON；stdout 同上含 fulloffListRaw + fulloffList）
  sl cysms process-serial-data-promote-details-json  （stdin JSON；stdout 同上含 promoteListRaw + promoteList）
  sl cysms process-serial-data-item-method-details-json  （stdin JSON；stdout 同上含 itemMethodListRaw + itemMethodList）
  sl cysms process-serial-data-payway-income-summary-json  （stdin：getserialdata 整包、或 settleList/settleListRaw、或结算行数组；stdout 与 serial-data-payway-income-summary 相同；**--include-all-settle-states true**；可选 **--shop-id**）
  sl cysms process-serial-data-reversal-settlement-summary-json  （stdin：getserialdata 整包或 **data.billList** 账单主信息数组；须含 settle_state 以识别返位；stdout 与 serial-data-reversal-settlement-summary 相同 schema；可选 **--shop-id**）
  sl cysms process-serial-data-abnormal-bill-summary-json  （stdin JSON：getserialdata 整包或含 data.billList；stdout 与 serial-data --format abnormal-bill-summary 相同 schema；可选 --shop-id 写入 query_echo.shop_id_override）

说明:
  accesstoken — 请求 POST ${ACCESSTOKEN_PATH}?appid=...&accessid=...&response_type=token（与开放文档 URL 一致；服务端拒绝 GET）
    appid / accessid 默认从 .env 的 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID 读取（再回退 token.json → cyS.auth，便于兼容旧数据）；换票结果写入 token.json → cyS.auth。
    成功后（或命中未过期缓存时）默认再分页拉取 **getshops**，把门店列表写入当前工作目录 cache/cysms-stores.json（需 .env 中 centerId，如 SL_CY7_GROUP_ID）；加 **--skip-stores** 可关闭。

  store-region — 仅从当前工作目录 cache/cysms-stores.json 解析门店行并输出区域编码（与外部环境分析技能字段顺序一致）；不写接口、不换票。
    门店锁定与 resolveCysmsOrgContext 一致：无 --store-name/--store-id 时优先 cache/cysms-selected-stores.json，再 SL_CY7_STORE_ID；有名称时在缓存中匹配。成功后把本次解析结果写回 cache/cysms-selected-stores.json。
    --only-primary 时仅向 stdout 打印首选区域编码一行（便于 shell 捕获）；其余说明走 stderr。

  business-situation — POST ${GET_BUSINESS_SITUATION_PATH}?centerId=...&shopId=...（ShowDoc #/46/14375 营业情况汇总；Header 同 getshops）
    须提供 centerId（机构）与 shopId（门店），默认来自 resolveCysmsOrgContext（与 getshops 一致：--center-id、--store-id/--store-name、SL_CY7_*、cyS.organization）。
    时间范围（二选一或按文档由服务端优先 settleDate）：
      - --begin-date 与 --end-date 成对；格式 yyyy-MM-dd HH:mm:ss（含空格时请整体加引号）；如需按结算时间等口径查询，可同时传 --date-type。
      - --settle-date yyyy-MM-dd 时须同时 --date-type：1=自然日 2=营业日。
    可选：--sale-type（1堂食/2外带/3外卖/4自提）、--item-type、--item-class-type、--discounted、--is-disc-include-not-income。

  service-area — POST ${GET_SERVICE_AREA_PATH}?centerId=...&shopId=...&pageNo=...&pageSize=...（ShowDoc #/46/6642 消费区域与客位列表；Header 同 getshops）
    客位字段见文档：isReserve、defCapacity、minCapacity、maxCapacity 等；pageSize 最大 50。
    --all-pages 时顺序拉取全部页并将 areaList 合并为一条响应（pageInfo 标注 merged）。
  service-area-list — 同 service-area；stdout 只返回 data.areaList（经 output_filter 裁剪图片字段）和计数/pageInfo，避免返回整包大 JSON。
  service-area-point-list — 同 service-area；先展平 data.areaList[].pointList[]，stdout 只返回 data.pointList（经 output_filter 裁剪图片字段）和计数/pageInfo，避免返回整包消费区域大 JSON。

  item-sellout-data — POST ${GET_ITEM_SELLOUT_DATA_PATH}?centerId=...&shopId=...&timeBegin=...&timeEnd=...&pageNo=...&pageSize=...（菜品估清明细；Header 同 getshops）
    timeBegin/timeEnd 必须成对；若均未填，默认本机自然当日 00:00:00 ~ 23:59:59。pageSize 文档最大 50。
    --all-pages 时顺序拉取全部页并合并 itemSelloutDataList；stdout 只返回 itemSelloutDataList、sellout_row_count 和 pageInfo（经 output_filter 裁剪）。

  book-order-detail — POST ${GET_BOOK_ORDER_DETAIL_PATH}?centerId=...&shopId=...&begin=...&end=...（ShowDoc #/46/17236 预订信息明细；Header 同 getshops）
    --begin / --end 可省略：省略时默认 **本机自然当日** 00:00:00 ~ 23:59:59；若只填其一则须补全或二者皆省略。
    可选 --telephone、--order-time-type（文档样例 query 含 orderTimeType）。
    --format profile-batch 时：从返回 data.data 中筛「取消时间为空」的预订单，输出供第二步会员画像批查的标准 JSON（order_no + contact_phone + book_type 等）。是否调用 CRM 用户画像由技能约定：默认仅当 bookType 非「普通用餐」时才将电话纳入 member 批查（见 .cursor/skills/cy-预定情况/SKILL.md）。

  o2o-ticket — POST ${GET_O2O_TICKET_PATH}?centerId=...&shopId=...&begin=...&end=...&pageNo=...&pageSize=...（ShowDoc #/46/24327 团购券 getO2oTicket；Header 同 getshops）
    时间与 book-order-detail 相同（--begin/--end 成对或默认本机自然当日）；pageSize 默认 500、最大 500；可选 **--seller**（文档平台枚举 1～9：美团点评/支付宝口碑/抖音券等）。
    默认 **--page-no 1** 且未 **--single-page** 时：若 pageInfo 表明尚有数据则自动顺序拉齐 ticketDataList（上限 200 页，**全程同一 pageSize**）；**--all-pages** 自第 1 页顺序拉齐；**--single-page true** 仅首请求；显式 **--page-no** 大于 1 时只拉该页。
    stdout（--format json）data：**ticketDataListRaw**、**ticketDataList**（经 output_filter）、**ticket_row_count**、**pageInfo**；若网关误用 billList 键名，实现侧会回退读取。
    --print-request：首请求前 stderr 打印 URL、QueryString、脱敏 Header。

  o2o-ticket-summary — 与 **o2o-ticket** 共用拉数逻辑；在合并后的 ticket 行上按 flag 过滤后输出 **cy7.cysms.o2o_ticket_summary.v1**（按平台 deFromName、按 ticketType 金额汇总、ticketCount 状态分布等）。**--only-redeemed true** 时仅统计 ticketState 含「已核销」或为数值 1 的行（实返以 ticketDataListRaw 为准）。stdin 离线汇总见 **process-o2o-ticket-summary-json**。

  serial-data — POST ${GET_SERIAL_DATA_PATH}?centerId=...&shopId=...&pageNo=...&pageSize=...（ShowDoc #/46/460 账单明细查询 getserialdata；Header 同 getshops）
    时间（二选一，与文档一致）：① --settle-date + --date-type（1 自然日 2 营业日）；② --begin-date/--end-date 或别名 --begin/--end（须成对），此时默认附带 dateType=3（结算时间），可用 --date-type 覆盖为 4 开台 / 5 最后上传。
    若 settle 与 begin/end 均未填：默认 **本机自然当日** 00:00:00 ~ 23:59:59，且 dateType=3。
    pageSize 默认 500（文档最大 500）；--all-pages 顺序合并全部页的 data.billList。
    --print-request true|1：在发**首屏** getserialdata 前向 stderr 打印整体入参（完整 URL、QueryString、Header；access_token 脱敏）；与全部 serial-data* 变体共用。
    --format checkout-anomaly-summary：按 waiter_code / waiter_name 汇总返位结算（settle_state=-1）、废单（state=3）、空账（state=2）笔数，供结账异常分析技能使用。
    --format abnormal-bill-summary：按 waiter_code / waiter_name 汇总空帐删除（state=2）、废单（state=3）、挂单（state=4）笔数及涉及服务员列表（ShowDoc #/46/444 state）；不含返位结算；stdin 整形见 **process-serial-data-abnormal-bill-summary-json**。

  serial-data-openclaw — 同路径同 Header；为 OpenClaw 技能包拆分的别名命令。未指定 settle 与 begin/end 时，默认 **本机自然当日** 全日时间窗且 **dateType=5**（最后上传口径）；查其它自然日须显式传参。stdout 对 data.billList 每项剔除 **item / settleDetail / discountDetail / promoteDetail / fulloffDetail / ticketDetail** 等明细数组，保留顶层主账单字段（如 bs_id、bs_code、waiter_*、金额汇总等）；若网关改为嵌套 billDetail 且仍须裁剪，可再配合注册表 output_filter。
    显式传入 --begin-date/--end-date（或 --settle-date）时行为与 serial-data 一致；若业务文档另有「beginDate/endDate 取字面 5」的特例环境，可显式 --begin-date 5 --end-date 5（部分网关会校验失败）。

  serial-data-items — 同 serial-data 调 getserialdata。未指定 settle 与 begin/end 时默认 **本机自然当日** 全日窗且 **dateType=5**（最后上传口径；与 **serial-data-openclaw** 一致）；显式 begin/end 且未传 **--date-type** 时亦为 **dateType=5**。其它日期须显式传参；若需结算时间口径可显式 **--date-type 3**。--format json 时 **不**输出 billList；将各账单 **item** 展平后 stdout 的 **data** 含：**itemListRaw**（网关完整品项行）、**itemList**（经 **output_filter** 裁剪）；**不含** item_qty_summary / item_qty_summary_by_name（汇总见 **serial-data-item-qty-summary**）。另附 bill_count、item_row_count、pageInfo。不支持 --format checkout-anomaly-summary / abnormal-bill-summary。
    默认在 **--page-no 1**（或未传 page-no）且未加 **--single-page true** 时：若 pageInfo.pageTotal>1 或 totalSize 大于本页 billList 条数，则自动拉取第 2…N 页并合并（与 **--all-pages** 相同上限 200 页）；**各页 pageSize 须与网关分页一致**，故自动拉取时全程使用与首请求相同的 **--page-size**（默认 500）。若希望单次响应更小，请显式 **--page-size 100**（全程 100），勿在自动模式下混用不同 pageSize（会错位漏单）。**--single-page true** 时始终只发一页请求（恢复旧行为）。

  serial-data-item-income — 与 **serial-data-items** 共用 getserialdata、query、默认时间窗、dateType、分页与自动多页合并语义；将 **bill.item[]** 以 **flattenBillItemsWithBillContextFromSerialBills** 展平（行上缺省时自账单补 **bs_id / bs_code / sc_id**）。stdout 的 **data** 含 **itemIncomeListRaw**（完整品项行含金额字段）、**itemIncomeList**（经 **output_filter** 裁剪 ShowDoc #/46/444 所列 Decimal 及关键维度）；另附 bill_count、**item_income_row_count**、pageInfo。若仅需数量/名称不含金额，仍用 **serial-data-items**。从 **serial-data-items** 已裁剪的 JSON 管道再整形**不会**补回未请求字段，金额分析请用本命令或上游 **serial-data --format json** 整包。

  serial-data-item-qty-summary — 与 **serial-data-items** 共用 getserialdata 与**完全相同**的 query、默认时间窗、dateType、分页与自动多页合并语义；区别为 stdout **仅**输出 **item_qty_summary**（按 **item_id** 合计 **last_qty**）、**item_qty_summary_by_name**（按 **item_name / temp_item_name** 显示名合计 **last_qty**）、bill_count、item_row_count、pageInfo；**不**输出 itemList / itemListRaw。**--omit-item-qty-summary** / **--omit-item-qty-summary-by-name** 可分别去掉两类汇总。

  process-serial-data-items-json — 无网络；从 **stdin** 读入 JSON（getserialdata 整包、或含 data.itemList / itemListRaw、或品项行数组），写出与 serial-data-items **相同 data 形状**（itemListRaw / itemList 等，仍走 output_filter）；**不含**汇总数组。

  process-serial-data-item-income-json — 无网络；stdin 为 getserialdata 整包、或含 data.itemIncomeList / itemIncomeListRaw、或 **完整** data.itemList / itemListRaw、或品项行数组；写出与 serial-data-item-income **相同 data 形状**（仍走 output_filter）；整包账单时展平方式与有网络命令一致（补 bs_id/sc_id）。

  process-serial-data-item-qty-summary-json — 无网络；stdin 形态同 process-serial-data-items-json；写出与 serial-data-item-qty-summary **相同 data 形状**（仅汇总 + 计数，仍走该命令注册表上的 output_filter）；支持 **--omit-item-qty-summary**、**--omit-item-qty-summary-by-name**。

  serial-data-settle-details — 同 getserialdata（**settleDetail** 字段见 ShowDoc #/46/444；父接口 #/46/460）。时间与分页默认与 **serial-data-items** 一致（未指定窗时当日全日 + dateType=5；begin/end 未成对 dateType 时亦为 5）；将各账单 **settleDetail** 展平为 **settleListRaw**、**settleList**（经 **output_filter**），附 bill_count、settle_row_count、pageInfo；不支持 --format checkout-anomaly-summary / abnormal-bill-summary；**--single-page** 与自动多页合并语义同 serial-data-items。

  serial-data-discount-details — 同 getserialdata（ShowDoc #/46/460 内 **品项打折方案优惠明细 discountDetail**）。时间、分页与 **serial-data-settle-details** 一致；将各账单 **discountDetail** 展平为 **discountListRaw**、**discountList**（经 **output_filter**），附 bill_count、discount_row_count、pageInfo。

  process-serial-data-settle-details-json — 无网络；stdin 为 getserialdata 整包、或含 data.settleList / settleListRaw、或结算明细行数组时，写出与 serial-data-settle-details **相同 data 形状**（仍走 output_filter）。

  process-serial-data-discount-details-json — 无网络；stdin 为 getserialdata 整包、或含 data.discountList / discountListRaw、或优惠明细行数组时，写出与 serial-data-discount-details **相同 data 形状**（仍走 output_filter）。

  serial-data-fulloff-details — 同 getserialdata（ShowDoc #/46/460 内 **满减定额优惠明细 fulloffDetail**）。时间、分页与 **serial-data-discount-details** 一致；将各账单 **fulloffDetail** 展平为 **fulloffListRaw**、**fulloffList**（经 **output_filter**），附 bill_count、fulloff_row_count、pageInfo。

  process-serial-data-fulloff-details-json — 无网络；stdin 为 getserialdata 整包、或含 data.fulloffList / fulloffListRaw、或满减定额优惠明细行数组时，写出与 serial-data-fulloff-details **相同 data 形状**（仍走 output_filter）。

  serial-data-promote-details — 同 getserialdata（ShowDoc #/46/460 内 **促销方案优惠明细 promoteDetail**）。时间、分页与 **serial-data-fulloff-details** 一致；将各账单 **promoteDetail** 展平为 **promoteListRaw**、**promoteList**（经 **output_filter**），附 bill_count、promote_row_count、pageInfo。

  process-serial-data-promote-details-json — 无网络；stdin 为 getserialdata 整包、或含 data.promoteList / promoteListRaw、或促销方案优惠明细行数组时，写出与 serial-data-promote-details **相同 data 形状**（仍走 output_filter）。

  serial-data-item-method-details — 同 getserialdata（ShowDoc #/46/460 内 **菜品做法明细 itemMethodData**，挂在 **bill.item[]** 各行下）。时间、分页与 **serial-data-promote-details** 一致；展平为 **itemMethodListRaw**、**itemMethodList**（经 **output_filter**），行上补 **bs_id/bs_code** 与 **item_id/item_name**（品项名）；附 bill_count、item_method_row_count、pageInfo。

  serial-data-payway-income-summary — 同 getserialdata；对 **settleDetail**（ShowDoc #/46/444）按 **payway_id/name** 与账单 **sale_type_id**（1 堂食 / 2 外带 / 3 外卖线下 / 4 自提）汇总 **pay_money 实收**、**income_money 纯收**、**not_income_money**；并输出 **bill_level_by_sale_type**（主档 **last_total**、**income_total** 等键名随网关）供交叉核对。时间、分页、自动多页合并与 **serial-data-settle-details** 一致。默认不计入 **delflg** 为 1/2 的结算行，且仅 **settle_state=1** 或缺省；加 **--include-all-settle-states true** 时计入返位/预结等全部状态。

  serial-data-reversal-settlement-summary — 同 getserialdata 与 **serial-data-payway-income-summary** 的 query/分页/自动多页合并；先筛 **账单主信息 settle_state=-1**（返位结算，ShowDoc #/46/444），再输出 **reversal_bill_count**、**by_waiter**（waiter_code/name 分桶账单张数，salesman_* 为桶内首次非空回填）、以及 **settleDetail** 的金额汇总字段（与 payway-income 同名的 **grand_totals**、**by_payway**、**by_sale_type**、**by_payway_and_sale_type**、**bill_level_by_sale_type** 等），结算行计入固定为「含全部 settle_state、排除 delflg 1/2」（等同 payway 的 **--include-all-settle-states true** 且仅限返位账单）。stdin 整形见 **process-serial-data-reversal-settlement-summary-json**（须整包或 billList，**不支持**仅 stdin 结算行：无法识别主档 settle_state）。

  process-serial-data-item-method-details-json — 无网络；stdin 为 getserialdata 整包、或含 data.itemMethodList / itemMethodListRaw、或做法明细行数组时，写出与 serial-data-item-method-details **相同 data 形状**（仍走 output_filter）。

  process-serial-data-payway-income-summary-json — 无网络；stdin 优先级：**data.settleListRaw** → **data.settleList**（仅结算行时 **bill_level_by_sale_type** 为空数组）→ getserialdata 整包含 **billList** → 结算行对象数组。写出与 **serial-data-payway-income-summary** 相同 **data**（schema cy7.cysms.serial_data_payway_income_summary.v1）。

  process-serial-data-reversal-settlement-summary-json — 无网络；stdin 为 getserialdata 整包、**data.billList** 或账单主信息行数组（须可读 **settle_state**，支持 **billDetail** 嵌套）；stdout 与 **serial-data-reversal-settlement-summary** 相同（schema **cy7.cysms.serial_data_reversal_settlement_summary.v1**）；可选 **--shop-id**。

  process-serial-data-abnormal-bill-summary-json — 无网络；stdin 为 getserialdata 整包或含 **data.billList**（账单主信息行，字段见 ShowDoc #/46/444）；stdout 与 **serial-data --format abnormal-bill-summary** 相同（schema cy.cysms.abnormal_bill_waiter_summary.v1）；可选 **--shop-id** 仅用于回显。

  getshops — POST ${GETSHOPS_PATH}?centerId=...&pageNo=...&pageSize=...（ShowDoc 门店档案信息页，需 Header: access_token、accessid、granttype=client）
    appid / accessid 默认优先 .env 的 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID（再回退 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}）
    access_token 默认同上 auth 缓存；本地 expires_at 过期或 getshops 返回疑似令牌错误时自动 accesstoken 并写回 token.json，再重试一次
    centerId / storeId / brandId：--center-id → cyS.organization.centerId → SL_CYSMS_CENTER_ID → SL_CY7_GROUP_ID；
      --store-id →（未传门店名时）cache/cysms-selected-stores.json → SL_CY7_STORE_ID → SL_CY7_STORE_IDS 首项；
      --brand-id →（未显式指定门店时）cyS.organization.brandId → SL_CY7_BRAND_ID。
      若提供 --store-name，在 cache/cysms-stores.json 按 name/code 匹配 id，并把命中门店写入 cache/cysms-selected-stores.json 供后续同类接口复用。
    groupNo（商龙云集团号）默认：--group-no → SL_CYSMS_GROUP_NO → token.json biz_params.SL_UNIFIED_G_ID → cyS.organization.groupNo。
      若遇「根据 groupNo 查询不到餐饮集团号」而 centerId 正确，可加 --omit-group-no 使请求 **不带** groupNo 查询参数再试。
    请求 URL 会在有值时附带 storeId、shopId、brandId 查询参数（与 centerId 同为「控制变量」，后续 datatransfer 类子命令将沿用同一解析模块）。
    业务成功时默认把门店列表写入当前工作目录 cache/cysms-stores.json（加 --skip-sync 可关闭）

  成功后将返回体合并写入 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}（access_token、refresh_token、expires_in、cached_at、expires_at）。
  门店列表写入当前工作目录 cache/cysms-stores.json；用户确认的默认门店写入 cache/cysms-selected-stores.json；**accesstoken 成功或命中有效缓存后默认会拉 getshops 更新 stores**（除非 --skip-stores）。
  未过期时默认复用 ${CY_S_AUTH}.access_token；加 --force 强制刷新。

环境变量（可被同名 flag 覆盖）:
  SL_CYSMS_BASE_URL     默认 ${DEFAULT_CYSMS_BASE}
  SL_CYSMS_APP_ID       对应 appid（鉴权请求优先从此读取，再回退 cyS.auth）
  SL_CYSMS_ACCESS_ID    对应 accessid（同上）
  SL_CYSMS_CENTER_ID    可选，覆盖默认 centerId
  SL_CYSMS_GROUP_NO     可选，覆盖默认商龙云集团号 groupNo
  SL_CYSMS_SKIP_AUTO_ACCESSTOKEN   true 时关闭：SL 换票后不自动 accesstoken / getshops（仍可用 sl cysms accesstoken / getshops）
  SL_CYSMS_AUTO_ACCESSTOKEN_FORCE  已废弃：SL 凭据同步后自动 accesstoken 恒为强制拉新（等同 sl cysms accesstoken --force true）
  SL_CY7_GROUP_ID       与 centerId 同源（.env / token.json biz_params）
  SL_CY7_STORE_ID       门店 ID；可与 SL_CY7_STORE_IDS 首项、--store-name 解析结果写入 cache/cysms-selected-stores.json
  SL_CY7_BRAND_ID       品牌 ID

  默认凭证：.env 的 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID → token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}（兼容旧版平铺在 cyS 根上，或旧键 ${LEGACY_APP_ID} / ${LEGACY_ACCESS_ID}）`);
}
function readCysmsTokenString(result) {
    if (!result || typeof result !== 'object' || Array.isArray(result)) {
        return null;
    }
    const r = result;
    for (const key of ['access_token', 'accessToken', 'token']) {
        const v = r[key];
        if (typeof v === 'string' && v.trim()) {
            return v;
        }
    }
    const data = r.data;
    if (data && typeof data === 'object' && !Array.isArray(data)) {
        const d = data;
        for (const key of ['access_token', 'accessToken', 'token']) {
            const v = d[key];
            if (typeof v === 'string' && v.trim()) {
                return v;
            }
        }
    }
    return null;
}
function isHttpSuccess(status) {
    return typeof status === 'number' && status >= 200 && status < 300;
}
function readHttpStatus(result) {
    if (!result || typeof result !== 'object') {
        return undefined;
    }
    const r = result;
    if (typeof r._httpStatus === 'number') {
        return r._httpStatus;
    }
    if (typeof r.statusCode === 'number') {
        return r.statusCode;
    }
    return undefined;
}
/** getshops 等接口返回「令牌类」错误时，强制 accesstoken 后重试一次 */
function isGetshopsBizSuccess(result) {
    if (!isPlainObject(result)) {
        return false;
    }
    const r = result;
    if (r.success === false) {
        return false;
    }
    const code = r.code;
    if (code === '0' || code === 0 || code === 200 || code === '200') {
        return true;
    }
    const msg = String(r.msg ?? '').toLowerCase();
    if (msg === 'success' || msg === 'ok') {
        return true;
    }
    if (Array.isArray(r.shopList)) {
        return true;
    }
    const data = r.data;
    if (data !== undefined && data !== null) {
        if (Array.isArray(data)) {
            return true;
        }
        if (isPlainObject(data) && Object.keys(data).length > 0) {
            return true;
        }
    }
    return false;
}
/** 从 getshops 类分页接口解析门店数组（兼容多种 data 形态） */
function extractStoresArrayFromCysmsListResult(result) {
    if (!isPlainObject(result)) {
        return null;
    }
    const data = result.data;
    if (Array.isArray(data)) {
        return data;
    }
    if (isPlainObject(data)) {
        const d = data;
        for (const key of ['list', 'records', 'rows', 'content', 'shops', 'shopList', 'shop_list', 'dataList']) {
            const v = d[key];
            if (Array.isArray(v)) {
                return v;
            }
        }
        const page = d.page;
        if (isPlainObject(page)) {
            const p = page;
            for (const key of ['list', 'records', 'rows', 'content', 'shops', 'shopList', 'dataList']) {
                const v = p[key];
                if (Array.isArray(v)) {
                    return v;
                }
            }
        }
    }
    const top = result;
    for (const key of ['shopList', 'shop_list', 'list', 'records', 'rows', 'shops', 'content', 'dataList']) {
        const v = top[key];
        if (Array.isArray(v)) {
            return v;
        }
    }
    return null;
}
/** 机构摘要：优先接口 data.organization / data.group；否则写入请求上下文 */
function buildOrganizationSnapshot(result, ctx) {
    const syncedAt = new Date().toISOString();
    if (isPlainObject(result)) {
        const data = result.data;
        if (isPlainObject(data)) {
            const d = data;
            const org = d.organization;
            if (isPlainObject(org)) {
                return { ...org, synced_at: syncedAt, centerId: ctx.centerId, groupNo: ctx.groupNo || null };
            }
            const group = d.group;
            if (isPlainObject(group)) {
                return { ...group, synced_at: syncedAt, centerId: ctx.centerId, groupNo: ctx.groupNo || null };
            }
            const pick = {
                synced_at: syncedAt,
                centerId: ctx.centerId,
                groupNo: ctx.groupNo || null,
            };
            for (const k of ['companyName', 'orgName', 'centerName', 'groupName', 'name', 'total', 'totalCount', 'totalElements']) {
                if (d[k] !== undefined) {
                    pick[k] = d[k];
                }
            }
            if (Object.keys(pick).length > 3) {
                return pick;
            }
        }
    }
    return {
        centerId: ctx.centerId,
        groupNo: ctx.groupNo || null,
        synced_at: syncedAt,
    };
}
/** 合并写入当前工作区 cache/cysms-stores.json，不覆盖 cyS.auth */
function persistCySStoresAndOrganizationPartial(stores, organization) {
    if (stores !== null) {
        const simpleStores = (0, cysms_store_cache_1.writeCysmsStoresCache)(stores, {
            centerId: String(organization.centerId || ''),
            groupNo: typeof organization.groupNo === 'string' ? organization.groupNo : null,
        });
        console.error(`✓ 已同步当前工作区 cache/cysms-stores.json（${simpleStores.length} 条）`);
        return;
    }
    void organization;
    console.error(`✓ 已保留当前工作区门店缓存（未识别到门店数组，cache/cysms-stores.json 未改写）`);
}
function storeRowDedupeKey(row) {
    if (!row || typeof row !== 'object' || Array.isArray(row)) {
        return '';
    }
    const r = row;
    const id = r.shop_id ?? r.shopId ?? r.id;
    if (typeof id === 'string' || typeof id === 'number') {
        return String(id).trim();
    }
    return '';
}
/**
 * SL 换票并 accesstoken 成功后：分页拉取 getshops 并合并写入当前工作区 cache/cysms-stores.json（与 `sl cysms getshops` 不写 skip-sync 时一致，且拉全部分页）。
 */
async function syncCySStoresFromGetshopsPaged(baseUrl, appid, accessid, initialToken, ctx) {
    if (!ctx.centerId) {
        console.error(`⚠ CY 开放 API：缺少 centerId，跳过 getshops 门店同步（请配置 SL_CY7_GROUP_ID / SL_CYSMS_CENTER_ID）`);
        return;
    }
    const cacheStatus = (0, cysms_store_cache_1.getCysmsStoresCacheStatus)({ centerId: ctx.centerId, groupNo: ctx.groupNo || null });
    if (cacheStatus.orgMatches) {
        console.error(`✓ CY 开放 API：当前机构门店缓存可复用（${cacheStatus.storeCount} 条），跳过 getshops 同步`);
        return;
    }
    if (cacheStatus.hasStores) {
        console.error('⚠ CY 开放 API：检测到机构号变化，已清空门店列表缓存与当前门店缓存，准备重新同步 getshops');
        (0, cysms_store_cache_1.clearCysmsStoreCache)();
    }
    const pageSize = '50';
    const pageSizeNum = Number(pageSize);
    console.error('→ CY 开放 API：正在分页拉取门店 getshops（仅 centerId / groupNo，不带单店筛选）…');
    const runOnePass = async (sendGroupNo) => {
        const acc = [];
        const seenLocal = new Set();
        let lastOk = null;
        let tok = initialToken;
        for (let pageNo = 1; pageNo <= MAX_GETSHOPS_SYNC_PAGES; pageNo += 1) {
            const qs = new URLSearchParams({
                centerId: ctx.centerId,
                pageNo: String(pageNo),
                pageSize,
            });
            if (sendGroupNo && ctx.groupNo) {
                qs.set('groupNo', ctx.groupNo);
            }
            /** 全量门店列表：勿附加 storeId/brandId，否则部分环境返回空列表 */
            const endpoint = {
                path: `${GETSHOPS_PATH}?${qs.toString()}`,
                method: 'POST',
            };
            const buildHeaders = (accessToken) => ({
                access_token: accessToken,
                accessid,
                granttype: 'client',
            });
            let result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(tok));
            if (isLikelyCysmsTokenRejected(result)) {
                console.error('⚠ CY 开放 API：getshops 疑似令牌失效，已强制 accesstoken 后重试当前页…');
                const fresh = await fetchAndPersistCysmsAccessToken(true, appid, accessid, baseUrl);
                if (!fresh) {
                    console.error('✗ CY 开放 API：getshops 换票失败，停止分页同步');
                    return { merged: acc, last: lastOk };
                }
                tok = fresh;
                result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(tok));
            }
            if (!isGetshopsBizSuccess(result)) {
                if (pageNo === 1) {
                    const hint = sendGroupNo && ctx.groupNo
                        ? '（可核对 SL_UNIFIED_G_ID / SL_CYSMS_GROUP_NO 是否与 centerId 匹配）'
                        : '';
                    console.error(`⚠ CY 开放 API：getshops 第 1 页业务未成功${hint}，本段分页结束`);
                }
                break;
            }
            lastOk = result;
            const stores = extractStoresArrayFromCysmsListResult(result) ?? [];
            if (stores.length === 0) {
                break;
            }
            for (const row of stores) {
                const k = storeRowDedupeKey(row);
                if (k) {
                    if (!seenLocal.has(k)) {
                        seenLocal.add(k);
                        acc.push(row);
                    }
                }
                else {
                    acc.push(row);
                }
            }
            if (stores.length < pageSizeNum) {
                break;
            }
        }
        return { merged: acc, last: lastOk };
    };
    let { merged, last: lastSuccessResult } = await runOnePass(Boolean(ctx.groupNo));
    if (merged.length === 0 && ctx.groupNo) {
        console.error('⚠ CY 开放 API：附带 groupNo 未拉到门店，改为不带 groupNo 再拉取…');
        ({ merged, last: lastSuccessResult } = await runOnePass(false));
    }
    if (!lastSuccessResult) {
        return;
    }
    const org = {
        ...buildOrganizationSnapshot(lastSuccessResult, { centerId: ctx.centerId, groupNo: ctx.groupNo }),
        ...(ctx.storeId ? { storeId: ctx.storeId } : {}),
        ...(ctx.brandId ? { brandId: ctx.brandId } : {}),
    };
    persistCySStoresAndOrganizationPartial(merged.length > 0 ? merged : null, org);
    if (ctx.storeId) {
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
    }
}
function isLikelyCysmsTokenRejected(result) {
    const status = readHttpStatus(result);
    if (status === 401 || status === 403) {
        return true;
    }
    if (!result || typeof result !== 'object' || Array.isArray(result)) {
        return false;
    }
    const r = result;
    const msg = String(r.msg ?? r.message ?? '');
    return /令牌|token|授权|失效|过期|无效|未授权|鉴权|登录|无权|signature|签名校验/i.test(msg);
}
function readCySAppIdForCommand(flags) {
    return flags.appid || (0, env_1.getEnv)('SL_CYSMS_APP_ID') || readAppIdFromStore() || DEFAULT_CYSMS_APP_ID;
}
function readCySAccessIdForCommand(flags) {
    return flags.accessid || (0, env_1.getEnv)('SL_CYSMS_ACCESS_ID') || readAccessIdFromStore() || DEFAULT_CYSMS_ACCESS_ID;
}
function readValidCySAccessTokenOrNull(force) {
    if (force) {
        return null;
    }
    const auth = extractCySAuthSlice(loadCySRoot());
    const tok = typeof auth.access_token === 'string' ? auth.access_token.trim() : '';
    if (!tok) {
        return null;
    }
    const deadline = getExpiresDeadlineMs(auth);
    if (deadline === null) {
        return tok;
    }
    if (Date.now() < deadline) {
        return tok;
    }
    return null;
}
/**
 * 请求开放 accesstoken 并写入 cyS.auth（与 sl cysms accesstoken 一致）。
 * @returns 可用 access_token，失败时返回 null（不 exit，供 SLY 换票后自动换票等场景）
 */
async function fetchAndPersistCysmsAccessToken(force, appid, accessid, baseUrl) {
    const cached = readValidCySAccessTokenOrNull(force);
    if (cached) {
        return cached;
    }
    const qs = new URLSearchParams({
        appid,
        accessid,
        response_type: 'token',
    }).toString();
    const endpoint = {
        path: `${ACCESSTOKEN_PATH}?${qs}`,
        method: 'POST',
    };
    const result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms');
    if (isAccesstokenSuccess(result)) {
        const slice = pickApiFieldsForCyS(result);
        persistCySMerged(slice, appid, accessid);
    }
    const t = readCysmsTokenString(result);
    return t && t.trim() ? t.trim() : null;
}
async function obtainCysmsAccessToken(force, appid, accessid, baseUrl) {
    const t = await fetchAndPersistCysmsAccessToken(force, appid, accessid, baseUrl);
    if (!t) {
        console.error('✗ 换取 access_token 失败，请检查 appid / accessid 或先执行 sl cysms accesstoken');
        process.exit(1);
    }
    return t;
}
async function obtainCy7SessionTokenFromSly() {
    const tokenModule = require('./token');
    const auth = await tokenModule.refreshRequestAuth('cy7');
    const token = auth?.sessionToken || auth?.headers?.['Access-Token-Shop'] || '';
    if (!token) {
        console.error('✗ CY7 Token 获取失败，请检查 SLY 账号密码配置');
        process.exit(1);
    }
    return token;
}
function isEnvExplicitTrue(key) {
    return ['true', '1', 'yes'].includes((0, env_1.getEnv)(key).trim().toLowerCase());
}
/**
 * 在 SLY 登录、switchToken 写入业务凭据之后调用：
 * 当已在环境（含 .env）同时配置 `SL_CYSMS_APP_ID` 与 `SL_CYSMS_ACCESS_ID` 时：强制 accesstoken 并写 token.json → cyS.auth，再分页 getshops 写入当前工作区 cache/cysms-stores.json。
 * **本路径不从 token.json 回退读取 appid/accessid**；任一项未配置则直接跳过鉴权与后续 getshops（手动换票仍可用 `sl cysms accesstoken`，其凭据链含 token.json 回退）。
 *
 * 跳过：设置 SL_CYSMS_SKIP_AUTO_ACCESSTOKEN=true
 * 换票策略：SL 凭据写入后此处**始终**忽略 cyS 本地未过期缓存并重新请求 accesstoken（等同 `sl cysms accesstoken --force true`）。
 * 成功后再分页拉取 **getshops** 写入当前工作区 cache/cysms-stores.json（需 centerId；缺省时跳过门店同步）。
 */
async function refreshCySAuthAfterSlCredentialSync() {
    if (isEnvExplicitTrue('SL_CYSMS_SKIP_AUTO_ACCESSTOKEN')) {
        return;
    }
    const appid = (0, env_1.getEnv)('SL_CYSMS_APP_ID').trim() || readAppIdFromStore() || DEFAULT_CYSMS_APP_ID;
    const accessid = (0, env_1.getEnv)('SL_CYSMS_ACCESS_ID').trim() || readAccessIdFromStore() || DEFAULT_CYSMS_ACCESS_ID;
    if (!appid || !accessid) {
        (0, logger_1.debugLog)('cyS 自动鉴权已跳过', 'SL_CYSMS_APP_ID 与 SL_CYSMS_ACCESS_ID 需同时在环境（如 .env）中配置；未配置则不请求 accesstoken / getshops');
        return;
    }
    const baseUrl = (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE).replace(/\/+$/, '');
    /** SL 同步后优先复用未过期 cyS 本地缓存，缺失或过期时再拉新 CY 开放票。 */
    const force = false;
    try {
        const tok = await fetchAndPersistCysmsAccessToken(force, appid, accessid, baseUrl);
        if (!tok) {
            console.error('⚠ CY 开放 API：SL 凭据刷新后自动 accesstoken 失败（已忽略，可检查 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID 或手动执行 sl cysms accesstoken）');
            return;
        }
        (0, cysms_context_1.persistCySOrganizationBizCache)((0, cysms_context_1.resolveCysmsOrgContext)({}));
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)({});
        await syncCySStoresFromGetshopsPaged(baseUrl, appid, accessid, tok, ctx);
        console.error('✓ CY 开放 API：已根据 .env 同步 cyS.auth，并已刷新当前工作区门店缓存');
    }
    catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        console.error(`⚠ CY 开放 API：自动 accesstoken 异常（已忽略）: ${msg}`);
    }
}
function extractAreaListFromServiceAreaData(data) {
    if (!isPlainObject(data)) {
        return [];
    }
    const list = data.areaList;
    return Array.isArray(list) ? list : [];
}
function readServiceAreaPageInfo(data) {
    if (!isPlainObject(data)) {
        return { pageNo: 1, pageTotal: 1, pageSize: 50, totalSize: 0 };
    }
    const pi = data.pageInfo;
    if (!isPlainObject(pi)) {
        return { pageNo: 1, pageTotal: 1, pageSize: 50, totalSize: 0 };
    }
    return {
        pageNo: Number(pi.pageNo) || 1,
        pageTotal: Number(pi.pageTotal) || 1,
        pageSize: Number(pi.pageSize) || 50,
        totalSize: Number(pi.totalSize) || 0,
    };
}
function extractItemSelloutListFromData(data) {
    if (!isPlainObject(data)) {
        return [];
    }
    const list = data.itemSelloutDataList;
    return Array.isArray(list) ? list : [];
}
function readItemSelloutPageInfo(data) {
    if (!isPlainObject(data)) {
        return { pageNo: 1, pageTotal: 1, pageSize: 50, totalSize: 0 };
    }
    const pi = data.pageInfo;
    if (!isPlainObject(pi)) {
        return { pageNo: 1, pageTotal: 1, pageSize: 50, totalSize: 0 };
    }
    return {
        pageNo: Number(pi.pageNo) || 1,
        pageTotal: Number(pi.pageTotal) || 1,
        pageSize: Number(pi.pageSize) || 50,
        totalSize: Number(pi.totalSize) || 0,
    };
}
function extractBookOrderDetailRows(result) {
    if (!isPlainObject(result)) {
        return [];
    }
    const topData = result.data;
    if (!isPlainObject(topData)) {
        return [];
    }
    const inner = topData.data;
    if (!Array.isArray(inner)) {
        return [];
    }
    const out = [];
    for (const row of inner) {
        if (isPlainObject(row)) {
            out.push(row);
        }
    }
    return out;
}
function cancelTimeIsEmpty(row) {
    const c = row.cancelTime;
    if (c === null || c === undefined) {
        return true;
    }
    if (typeof c === 'string' && !c.trim()) {
        return true;
    }
    if (typeof c === 'number' && (c === 0 || !Number.isFinite(c))) {
        return true;
    }
    return false;
}
function pad2(n) {
    return n < 10 ? `0${n}` : String(n);
}
/** 本机时区自然日：当日 00:00:00 ~ 23:59:59（与 book-order-detail 默认时间窗一致） */
function defaultBookOrderDetailLocalCalendarDay() {
    const now = new Date();
    const y = now.getFullYear();
    const m = pad2(now.getMonth() + 1);
    const d = pad2(now.getDate());
    const dateLabel = `${y}-${m}-${d}`;
    return {
        begin: `${dateLabel} 00:00:00`,
        end: `${dateLabel} 23:59:59`,
        dateLabel,
    };
}
function buildReserveProfileBatchPayload(params) {
    const active = params.rows.filter(cancelTimeIsEmpty);
    const seen = new Set();
    const items = [];
    for (const row of active) {
        const orderNo = row.orderNo != null ? String(row.orderNo).trim() : '';
        const tel = row.tel != null ? String(row.tel).trim() : '';
        if (!orderNo && !tel) {
            continue;
        }
        const key = `${orderNo}\t${tel}`;
        if (seen.has(key)) {
            continue;
        }
        seen.add(key);
        items.push({
            order_no: orderNo || null,
            contact_phone: tel || null,
            book_man: row.bookMan != null ? String(row.bookMan) : null,
            shift: row.shift != null ? String(row.shift) : null,
            book_time: row.bookTime != null ? String(row.bookTime) : null,
            book_type: row.bookType != null ? String(row.bookType) : null,
            book_source: row.bookSource != null ? String(row.bookSource) : null,
            people: row.people ?? null,
            book_point: row.bookPoint != null ? String(row.bookPoint) : null,
            book_state: row.bookState != null ? String(row.bookState) : null,
            remark: row.remark != null ? String(row.remark) : null,
            bs_code: row.bsCode != null ? String(row.bsCode) : null,
            book_point_bsid: row.bookPointBsid ?? null,
        });
    }
    return {
        schema: 'cy.reserve_profile_lookup.v1',
        generated_at: new Date().toISOString(),
        shop_id: params.shopId,
        time_window: { begin: params.begin, end: params.end },
        active_reservation_count: items.length,
        items,
    };
}
function extractBillListFromSerialDataResult(result) {
    if (!isPlainObject(result)) {
        return [];
    }
    const data = result.data;
    if (!isPlainObject(data)) {
        return [];
    }
    const list = data.billList;
    if (!Array.isArray(list)) {
        return [];
    }
    const out = [];
    for (const row of list) {
        if (isPlainObject(row)) {
            out.push(row);
        }
    }
    return out;
}
/**
 * getserialdata 常见实返：账单主信息（bs_id、bs_code、waiter_*、金额汇总等）在 billList 行顶层，
 * 菜品/结算方式等落在若干明细数组。与 ShowDoc 中「嵌套 billDetail」形态可能并存；OpenClaw 变体 stdout 需瘦身时剔除下列重块。
 */
const CY_GETSERIALDATA_BILL_DETAIL_ARRAY_KEYS = [
    'item',
    'settleDetail',
    'discountDetail',
    'promoteDetail',
    'fulloffDetail',
    'ticketDetail',
];
function stripCysmsSerialBillListDetailArrays(result) {
    if (!isPlainObject(result)) {
        return result;
    }
    const data = result.data;
    if (!isPlainObject(data) || !Array.isArray(data.billList)) {
        return result;
    }
    const stripRow = (row) => {
        if (!isPlainObject(row)) {
            return row;
        }
        const next = { ...row };
        for (const k of CY_GETSERIALDATA_BILL_DETAIL_ARRAY_KEYS) {
            delete next[k];
        }
        return next;
    };
    return {
        ...result,
        data: {
            ...data,
            billList: data.billList.map(stripRow),
        },
    };
}
function applyOpenclawSerialStdoutShaping(isOpenclawVariant, outFmt, result) {
    if (!isOpenclawVariant || isSerialDataBillSummaryFormat(outFmt)) {
        return result;
    }
    return stripCysmsSerialBillListDetailArrays(result);
}
/** 将各 bill 下的 ShowDoc「品项消费明细 item」数组展平为一维列表（字段以网关实返为准）。 */
function flattenBillItemsFromSerialBills(bills) {
    const rows = [];
    for (const bill of bills) {
        const items = bill.item;
        if (!Array.isArray(items)) {
            continue;
        }
        for (const it of items) {
            if (isPlainObject(it)) {
                rows.push({ ...it });
            }
        }
    }
    return rows;
}
/** 品项行展平并自账单主信息补全 bs_id / bs_code / sc_id（行上缺省时），供菜品收入等需账单级关联的分析。 */
function flattenBillItemsWithBillContextFromSerialBills(bills) {
    const rows = [];
    for (const bill of bills) {
        const items = bill.item;
        if (!Array.isArray(items)) {
            continue;
        }
        const billBsId = bill.bs_id;
        const billBsCode = bill.bs_code;
        const billScId = bill.sc_id;
        for (const it of items) {
            if (!isPlainObject(it)) {
                continue;
            }
            const row = { ...it };
            if (row.bs_id == null && billBsId != null) {
                row.bs_id = billBsId;
            }
            if (row.bs_code == null && billBsCode != null) {
                row.bs_code = billBsCode;
            }
            if (row.sc_id == null && billScId != null) {
                row.sc_id = billScId;
            }
            rows.push(row);
        }
    }
    return rows;
}
/** ShowDoc「菜品做法明细 itemMethodData」：挂在 bill.item[] 各行下；展平并补 bs_id/bs_code、item_id、item_name（品项名优先 item_name，否则 temp_item_name）。 */
function flattenItemMethodDataFromSerialBills(bills) {
    const rows = [];
    for (const bill of bills) {
        const billBsId = bill.bs_id;
        const billBsCode = bill.bs_code;
        const items = bill.item;
        if (!Array.isArray(items)) {
            continue;
        }
        for (const it of items) {
            if (!isPlainObject(it)) {
                continue;
            }
            const methods = it.itemMethodData;
            if (!Array.isArray(methods)) {
                continue;
            }
            const itemId = it.item_id;
            const fromItem = it.item_name != null ? String(it.item_name).trim() : '';
            const fromTemp = it.temp_item_name != null ? String(it.temp_item_name).trim() : '';
            const itemNameDisp = fromItem || fromTemp;
            for (const m of methods) {
                if (!isPlainObject(m)) {
                    continue;
                }
                const row = { ...m };
                if (row.bs_id == null && billBsId != null) {
                    row.bs_id = billBsId;
                }
                if (row.bs_code == null && billBsCode != null) {
                    row.bs_code = billBsCode;
                }
                if (row.item_id == null && itemId != null) {
                    row.item_id = itemId;
                }
                if (row.item_name == null && itemNameDisp) {
                    row.item_name = itemNameDisp;
                }
                rows.push(row);
            }
        }
    }
    return rows;
}
/** ShowDoc「结算明细 settleDetail」数组展平；若行上缺 bs_id/bs_code 则从账单主信息补全便于对账。 */
function flattenSettleDetailsFromSerialBills(bills) {
    const rows = [];
    for (const bill of bills) {
        const details = bill.settleDetail;
        if (!Array.isArray(details)) {
            continue;
        }
        const billBsId = bill.bs_id;
        const billBsCode = bill.bs_code;
        for (const d of details) {
            if (!isPlainObject(d)) {
                continue;
            }
            const row = { ...d };
            if (row.bs_id == null && billBsId != null) {
                row.bs_id = billBsId;
            }
            if (row.bs_code == null && billBsCode != null) {
                row.bs_code = billBsCode;
            }
            rows.push(row);
        }
    }
    return rows;
}
/** 与 ShowDoc 可能并存的 billDetail 嵌套：合并后再读 sale_type_id、last_total 等主档字段。 */
function mergeBillDetailIntoBill(bill) {
    const bd = bill.billDetail;
    if (!isPlainObject(bd)) {
        return bill;
    }
    const { billDetail: _omit, ...billRest } = bill;
    return { ...bd, ...billRest };
}
const SALE_TYPE_ID_LABELS = {
    1: '堂食',
    2: '外带',
    3: '外卖（线下）',
    4: '自提',
};
function saleTypeLabelFromId(id) {
    if (id === null) {
        return '（未知）';
    }
    return SALE_TYPE_ID_LABELS[id] ?? `其它(${id})`;
}
function readBillSaleTypeId(bill) {
    const merged = mergeBillDetailIntoBill(bill);
    return toFiniteNumberOrNull(merged.sale_type_id ?? merged.saleTypeId);
}
function readBillIncomeTotalField(bill) {
    const merged = mergeBillDetailIntoBill(bill);
    const raw = merged.income_total ??
        merged.income_tota ??
        merged.incomeTotal ??
        merged.pure_income ??
        merged.income_money;
    return toMoneyNumberForSummary(raw);
}
function readBillLastTotalField(bill) {
    const merged = mergeBillDetailIntoBill(bill);
    return toMoneyNumberForSummary(merged.last_total ?? merged.lastTotal);
}
function toMoneyNumberForSummary(v) {
    if (v === null || v === undefined) {
        return 0;
    }
    if (typeof v === 'number' && Number.isFinite(v)) {
        return v;
    }
    const s = String(v).trim().replace(/,/g, '');
    if (!s) {
        return 0;
    }
    const n = Number(s);
    return Number.isFinite(n) ? n : 0;
}
/** settleDetail 展平并挂上账单销售类型，供结算方式收入汇总。 */
function flattenSettleDetailsWithSaleTypeFromSerialBills(bills) {
    const rows = [];
    for (const billRaw of bills) {
        const bill = mergeBillDetailIntoBill(billRaw);
        const details = bill.settleDetail;
        if (!Array.isArray(details)) {
            continue;
        }
        const billBsId = bill.bs_id;
        const billBsCode = bill.bs_code;
        const stId = readBillSaleTypeId(bill);
        const stNameRaw = bill.sale_type_name ?? bill.saleTypeName;
        const stName = typeof stNameRaw === 'string' && stNameRaw.trim() ? stNameRaw.trim() : null;
        for (const d of details) {
            if (!isPlainObject(d)) {
                continue;
            }
            const row = { ...d };
            if (row.bs_id == null && billBsId != null) {
                row.bs_id = billBsId;
            }
            if (row.bs_code == null && billBsCode != null) {
                row.bs_code = billBsCode;
            }
            if (row.sale_type_id == null && stId !== null) {
                row.sale_type_id = stId;
            }
            if (row.sale_type_name == null && stName) {
                row.sale_type_name = stName;
            }
            rows.push(row);
        }
    }
    return rows;
}
function emptyPaywayIncomeAgg() {
    return {
        pay_money_total: 0,
        income_money_total: 0,
        not_income_money_total: 0,
        settle_line_count: 0,
    };
}
function addSettleRowToAgg(agg, row) {
    agg.pay_money_total += toMoneyNumberForSummary(row.pay_money);
    agg.income_money_total += toMoneyNumberForSummary(row.income_money);
    agg.not_income_money_total += toMoneyNumberForSummary(row.not_income_money);
    agg.settle_line_count += 1;
}
function shouldIncludeSettleRowForIncomeSummary(row, includeAllSettleStates) {
    const df = toFiniteNumberOrNull(row.delflg);
    if (df === 1 || df === 2) {
        return false;
    }
    if (includeAllSettleStates) {
        return true;
    }
    const ss = toFiniteNumberOrNull(row.settle_state);
    if (ss === null) {
        return true;
    }
    return ss === 1;
}
const PAYWAY_INCOME_SUMMARY_SCHEMA = 'cy7.cysms.serial_data_payway_income_summary.v1';
function paywayKeyFromSettleRow(row) {
    const id = row.payway_id ?? row.paywayId;
    const name = row.payway_name != null ? String(row.payway_name).trim() : '';
    const sid = id !== undefined && id !== null ? String(id) : '';
    return `${sid}\t${name}`;
}
function paywayMetaFromKey(key) {
    const tab = key.indexOf('\t');
    const idStr = tab >= 0 ? key.slice(0, tab) : key;
    const name = tab >= 0 ? key.slice(tab + 1) : '';
    if (!idStr) {
        return { payway_id: null, payway_name: name || '（无结算方式名）' };
    }
    const n = Number(idStr);
    return { payway_id: Number.isFinite(n) && String(n) === idStr ? n : idStr, payway_name: name || '（无结算方式名）' };
}
function buildPaywayIncomeSummaryData(params) {
    const rowsInput = params.settleRowsOverride != null
        ? params.settleRowsOverride
        : flattenSettleDetailsWithSaleTypeFromSerialBills(params.bills);
    const rows = rowsInput.filter((r) => shouldIncludeSettleRowForIncomeSummary(r, params.includeAllSettleStates));
    const byPaywayMap = new Map();
    const bySaleMap = new Map();
    const crossMap = new Map();
    const grand = emptyPaywayIncomeAgg();
    for (const row of rows) {
        addSettleRowToAgg(grand, row);
        const pk = paywayKeyFromSettleRow(row);
        let a = byPaywayMap.get(pk);
        if (!a) {
            a = emptyPaywayIncomeAgg();
            byPaywayMap.set(pk, a);
        }
        addSettleRowToAgg(a, row);
        const st = toFiniteNumberOrNull(row.sale_type_id);
        const sk = st === null ? '__null__' : String(st);
        let s = bySaleMap.get(sk);
        if (!s) {
            s = emptyPaywayIncomeAgg();
            bySaleMap.set(sk, s);
        }
        addSettleRowToAgg(s, row);
        const ck = `${pk}\x1e${sk}`;
        let c = crossMap.get(ck);
        if (!c) {
            c = emptyPaywayIncomeAgg();
            crossMap.set(ck, c);
        }
        addSettleRowToAgg(c, row);
    }
    const paywayFirstCodes = new Map();
    for (const row of rows) {
        const pk = paywayKeyFromSettleRow(row);
        if (!paywayFirstCodes.has(pk) && row.payway_code != null) {
            paywayFirstCodes.set(pk, row.payway_code);
        }
    }
    const by_payway = Array.from(byPaywayMap.entries())
        .map(([key, agg]) => {
        const meta = paywayMetaFromKey(key);
        return {
            payway_id: meta.payway_id,
            payway_code: paywayFirstCodes.get(key) ?? null,
            payway_name: meta.payway_name,
            ...agg,
        };
    });
    by_payway.sort((a, b) => b.pay_money_total - a.pay_money_total ||
        String(a.payway_name).localeCompare(String(b.payway_name), 'zh-Hans-CN'));
    const by_sale_type = Array.from(bySaleMap.entries())
        .map(([sk, agg]) => {
        const id = sk === '__null__' ? null : Number(sk);
        const sid = id !== null && Number.isFinite(id) ? id : null;
        return {
            sale_type_id: sid,
            sale_type_label: saleTypeLabelFromId(sid),
            ...agg,
        };
    })
        .sort((a, b) => {
        const na = a.sale_type_id ?? 999;
        const nb = b.sale_type_id ?? 999;
        return na - nb;
    });
    const by_payway_and_sale_type = Array.from(crossMap.entries())
        .map(([key, agg]) => {
        const sep = key.indexOf('\x1e');
        const pk = sep >= 0 ? key.slice(0, sep) : key;
        const sk = sep >= 0 ? key.slice(sep + 1) : '__null__';
        const payMeta = paywayMetaFromKey(pk);
        const id = sk === '__null__' ? null : Number(sk);
        const sid = id !== null && Number.isFinite(id) ? id : null;
        return {
            payway_id: payMeta.payway_id,
            payway_code: paywayFirstCodes.get(pk) ?? null,
            payway_name: payMeta.payway_name,
            sale_type_id: sid,
            sale_type_label: saleTypeLabelFromId(sid),
            ...agg,
        };
    })
        .sort((a, b) => b.pay_money_total - a.pay_money_total ||
        String(a.payway_name).localeCompare(String(b.payway_name), 'zh-Hans-CN') ||
        (a.sale_type_id ?? 999) - (b.sale_type_id ?? 999));
    const billSaleBillMap = new Map();
    if (params.settleRowsOverride == null) {
        for (const billRaw of params.bills) {
            const merged = mergeBillDetailIntoBill(billRaw);
            const st = readBillSaleTypeId(merged);
            const sk = st === null ? '__null__' : String(st);
            let b = billSaleBillMap.get(sk);
            if (!b) {
                b = { bill_count: 0, last_total_sum: 0, income_total_sum: 0 };
                billSaleBillMap.set(sk, b);
            }
            b.bill_count += 1;
            b.last_total_sum += readBillLastTotalField(merged);
            b.income_total_sum += readBillIncomeTotalField(merged);
        }
    }
    const bill_level_by_sale_type = Array.from(billSaleBillMap.entries())
        .map(([sk, b]) => {
        const id = sk === '__null__' ? null : Number(sk);
        const sid = id !== null && Number.isFinite(id) ? id : null;
        return {
            sale_type_id: sid,
            sale_type_label: saleTypeLabelFromId(sid),
            ...b,
        };
    })
        .sort((a, b) => (a.sale_type_id ?? 999) - (b.sale_type_id ?? 999));
    return {
        schema: PAYWAY_INCOME_SUMMARY_SCHEMA,
        generated_at: new Date().toISOString(),
        shop_id: params.shopId,
        query_echo: params.queryEcho,
        metrics_legend: {
            pay_money_total: 'settleDetail.pay_money 合计（实收，ShowDoc #/46/444：纯收+非收入）；默认仅统计 settle_state=1 或缺省、且 delflg 非 1/2 的结算行',
            income_money_total: 'settleDetail.income_money 合计（纯收）',
            not_income_money_total: 'settleDetail.not_income_money 合计（非收入）',
            bill_last_total_sum: '账单主信息 last_total 按 sale_type_id 合计（实收口径对照；字段可能在 billDetail 嵌套内）',
            bill_income_total_sum: '账单主信息 income_total / income_tota 等按 sale_type_id 合计（纯收口径对照，键名随网关实返）',
            sale_type_id_enum: '1堂食 2外带 3外卖（线下）4自提（ShowDoc #/46/444）',
        },
        settle_row_count_included: rows.length,
        settle_row_count_raw: rowsInput.length,
        grand_totals: { ...grand },
        by_payway,
        by_sale_type,
        by_payway_and_sale_type,
        bill_level_by_sale_type,
    };
}
function shapeSerialDataPaywayIncomeSummaryStdout(bills, shopId, queryEcho, includeAllSettleStates, settleRowsOverride) {
    const data = buildPaywayIncomeSummaryData({
        bills,
        shopId,
        queryEcho,
        includeAllSettleStates,
        settleRowsOverride,
    });
    return {
        code: '0',
        msg: 'success',
        data: {
            ...data,
            bill_count: bills.length,
        },
    };
}
/** ShowDoc「品项打折方案优惠明细 discountDetail」数组展平；若行上缺 bs_id/bs_code 则从账单主信息补全。 */
function flattenDiscountDetailsFromSerialBills(bills) {
    const rows = [];
    for (const bill of bills) {
        const details = bill.discountDetail;
        if (!Array.isArray(details)) {
            continue;
        }
        const billBsId = bill.bs_id;
        const billBsCode = bill.bs_code;
        for (const d of details) {
            if (!isPlainObject(d)) {
                continue;
            }
            const row = { ...d };
            if (row.bs_id == null && billBsId != null) {
                row.bs_id = billBsId;
            }
            if (row.bs_code == null && billBsCode != null) {
                row.bs_code = billBsCode;
            }
            rows.push(row);
        }
    }
    return rows;
}
/** ShowDoc「满减定额优惠明细 fulloffDetail」数组展平；若行上缺 bs_id/bs_code 则从账单主信息补全。 */
function flattenFulloffDetailsFromSerialBills(bills) {
    const rows = [];
    for (const bill of bills) {
        const details = bill.fulloffDetail;
        if (!Array.isArray(details)) {
            continue;
        }
        const billBsId = bill.bs_id;
        const billBsCode = bill.bs_code;
        for (const d of details) {
            if (!isPlainObject(d)) {
                continue;
            }
            const row = { ...d };
            if (row.bs_id == null && billBsId != null) {
                row.bs_id = billBsId;
            }
            if (row.bs_code == null && billBsCode != null) {
                row.bs_code = billBsCode;
            }
            rows.push(row);
        }
    }
    return rows;
}
/** ShowDoc「促销方案优惠明细 promoteDetail」数组展平；若行上缺 bs_id/bs_code 则从账单主信息补全。 */
function flattenPromoteDetailsFromSerialBills(bills) {
    const rows = [];
    for (const bill of bills) {
        const details = bill.promoteDetail;
        if (!Array.isArray(details)) {
            continue;
        }
        const billBsId = bill.bs_id;
        const billBsCode = bill.bs_code;
        for (const d of details) {
            if (!isPlainObject(d)) {
                continue;
            }
            const row = { ...d };
            if (row.bs_id == null && billBsId != null) {
                row.bs_id = billBsId;
            }
            if (row.bs_code == null && billBsCode != null) {
                row.bs_code = billBsCode;
            }
            rows.push(row);
        }
    }
    return rows;
}
function cloneItemRows(rows) {
    return rows.map((r) => ({ ...r }));
}
/** 按 ShowDoc 品项行 item_id 分组合计 last_qty，供 serial-data-item-qty-summary 与 stdin 整形共用。 */
function buildItemQtySummaryFromItemRows(rows) {
    const map = new Map();
    for (const row of rows) {
        const rawId = row.item_id;
        const hasId = rawId !== undefined && rawId !== null && String(rawId).trim() !== '';
        const key = hasId ? String(rawId) : '__missing_item_id__';
        const qty = Number(row.last_qty);
        const delta = Number.isFinite(qty) ? qty : 0;
        const fromItem = row.item_name != null ? String(row.item_name).trim() : '';
        const fromTemp = row.temp_item_name != null ? String(row.temp_item_name).trim() : '';
        const displayName = fromItem || fromTemp;
        const prev = map.get(key);
        if (!prev) {
            map.set(key, {
                id: hasId ? rawId : null,
                name: displayName,
                amount: delta,
            });
        }
        else {
            prev.amount += delta;
            if (!prev.name && displayName) {
                prev.name = displayName;
            }
        }
    }
    const list = Array.from(map.values());
    list.sort((a, b) => {
        const sa = a.id !== undefined && a.id !== null ? String(a.id) : '';
        const sb = b.id !== undefined && b.id !== null ? String(b.id) : '';
        const na = Number(sa);
        const nb = Number(sb);
        if (Number.isFinite(na) && Number.isFinite(nb) && String(na) === sa && String(nb) === sb) {
            return na - nb;
        }
        return sa.localeCompare(sb, 'zh-Hans-CN');
    });
    return list;
}
/** 按品项显示名称分组合计 last_qty（item_name 优先，否则 temp_item_name）；同名不同 item_id 会合并，供「菜品销量」按名称汇总。 */
function buildItemQtySummaryByNameFromItemRows(rows) {
    const map = new Map();
    for (const row of rows) {
        const fromItem = row.item_name != null ? String(row.item_name).trim() : '';
        const fromTemp = row.temp_item_name != null ? String(row.temp_item_name).trim() : '';
        const displayName = fromItem || fromTemp || '（无名称）';
        const key = displayName;
        const qty = Number(row.last_qty);
        const delta = Number.isFinite(qty) ? qty : 0;
        const prev = map.get(key);
        if (!prev) {
            map.set(key, { id: null, name: displayName, amount: delta });
        }
        else {
            prev.amount += delta;
        }
    }
    const list = Array.from(map.values());
    list.sort((a, b) => b.amount - a.amount || a.name.localeCompare(b.name, 'zh-Hans-CN'));
    return list;
}
/** 单页：保留 code/msg，data 为 item 展平明细（无汇总数组；汇总见 serial-data-item-qty-summary）。 */
function shapeSerialDataItemsStdoutFromResult(result) {
    if (!isPlainObject(result)) {
        return result;
    }
    const bills = extractBillListFromSerialDataResult(result);
    const itemList = flattenBillItemsFromSerialBills(bills);
    const itemListRaw = cloneItemRows(itemList);
    const itemListOut = cloneItemRows(itemList);
    const data = isPlainObject(result.data) ? result.data : {};
    const pageInfo = data.pageInfo;
    return {
        ...result,
        data: {
            itemListRaw,
            itemList: itemListOut,
            pageInfo: pageInfo ?? null,
            bill_count: bills.length,
            item_row_count: itemList.length,
        },
    };
}
/** --all-pages：在合并后的 billList 上展平品项行。 */
function shapeSerialDataItemsStdoutFromMergedEnvelope(envelope, mergedBills, sourcePageTotal) {
    const itemList = flattenBillItemsFromSerialBills(mergedBills);
    const itemListRaw = cloneItemRows(itemList);
    const itemListOut = cloneItemRows(itemList);
    return {
        ...envelope,
        data: {
            itemListRaw,
            itemList: itemListOut,
            pageInfo: {
                merged: true,
                bill_count: mergedBills.length,
                item_row_count: itemList.length,
                source_page_total: sourcePageTotal,
            },
        },
    };
}
/** 品项行菜品收入金额字段：ShowDoc #/46/444 品项 item 层 Decimal 口径。 */
function shapeSerialDataItemIncomeStdoutFromResult(result) {
    if (!isPlainObject(result)) {
        return result;
    }
    const bills = extractBillListFromSerialDataResult(result);
    const rows = flattenBillItemsWithBillContextFromSerialBills(bills);
    const itemIncomeListRaw = cloneItemRows(rows);
    const itemIncomeList = cloneItemRows(rows);
    const data = isPlainObject(result.data) ? result.data : {};
    const pageInfo = data.pageInfo;
    return {
        ...result,
        data: {
            itemIncomeListRaw,
            itemIncomeList,
            pageInfo: pageInfo ?? null,
            bill_count: bills.length,
            item_income_row_count: rows.length,
        },
    };
}
function shapeSerialDataItemIncomeStdoutFromMergedEnvelope(envelope, mergedBills, sourcePageTotal) {
    const rows = flattenBillItemsWithBillContextFromSerialBills(mergedBills);
    const itemIncomeListRaw = cloneItemRows(rows);
    const itemIncomeList = cloneItemRows(rows);
    return {
        ...envelope,
        data: {
            itemIncomeListRaw,
            itemIncomeList,
            pageInfo: {
                merged: true,
                bill_count: mergedBills.length,
                item_income_row_count: rows.length,
                source_page_total: sourcePageTotal,
            },
        },
    };
}
/** 单页：仅输出按 item_id / 按菜品显示名汇总的数量与计数（不输出 item 明细行）。 */
function shapeSerialDataItemQtySummaryStdoutFromResult(result, opts) {
    if (!isPlainObject(result)) {
        return result;
    }
    const bills = extractBillListFromSerialDataResult(result);
    const itemList = flattenBillItemsFromSerialBills(bills);
    const data = isPlainObject(result.data) ? result.data : {};
    const pageInfo = data.pageInfo;
    const item_qty_summary = opts?.omitItemQtySummary ? undefined : buildItemQtySummaryFromItemRows(itemList);
    const item_qty_summary_by_name = opts?.omitItemQtySummaryByName
        ? undefined
        : buildItemQtySummaryByNameFromItemRows(itemList);
    return {
        ...result,
        data: {
            ...(item_qty_summary !== undefined ? { item_qty_summary } : {}),
            ...(item_qty_summary_by_name !== undefined ? { item_qty_summary_by_name } : {}),
            pageInfo: pageInfo ?? null,
            bill_count: bills.length,
            item_row_count: itemList.length,
        },
    };
}
function shapeSerialDataItemQtySummaryStdoutFromMergedEnvelope(envelope, mergedBills, sourcePageTotal, opts) {
    const itemList = flattenBillItemsFromSerialBills(mergedBills);
    const item_qty_summary = opts?.omitItemQtySummary ? undefined : buildItemQtySummaryFromItemRows(itemList);
    const item_qty_summary_by_name = opts?.omitItemQtySummaryByName
        ? undefined
        : buildItemQtySummaryByNameFromItemRows(itemList);
    return {
        ...envelope,
        data: {
            ...(item_qty_summary !== undefined ? { item_qty_summary } : {}),
            ...(item_qty_summary_by_name !== undefined ? { item_qty_summary_by_name } : {}),
            pageInfo: {
                merged: true,
                bill_count: mergedBills.length,
                item_row_count: itemList.length,
                source_page_total: sourcePageTotal,
            },
        },
    };
}
/** 从 stdin 解析后的 JSON 提取品项行（process-serial-data-items-json / process-serial-data-item-qty-summary-json 共用）。 */
function collectItemInputRowsFromParsedCysmsJson(parsed) {
    const rows = [];
    if (Array.isArray(parsed)) {
        for (const row of parsed) {
            if (isPlainObject(row)) {
                rows.push(row);
            }
        }
        return rows;
    }
    if (isPlainObject(parsed)) {
        const p = parsed;
        const data = p.data;
        if (isPlainObject(data) && Array.isArray(data.itemIncomeListRaw)) {
            for (const row of data.itemIncomeListRaw) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
            return rows;
        }
        if (isPlainObject(data) && Array.isArray(data.itemIncomeList)) {
            for (const row of data.itemIncomeList) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
            return rows;
        }
        if (isPlainObject(data) && Array.isArray(data.itemListRaw)) {
            for (const row of data.itemListRaw) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
            return rows;
        }
        if (isPlainObject(data) && Array.isArray(data.itemList)) {
            for (const row of data.itemList) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
            return rows;
        }
        const bills = extractBillListFromSerialDataResult(parsed);
        return flattenBillItemsFromSerialBills(bills);
    }
    return rows;
}
/** process-serial-data-item-income-json：整包账单时用品项行 + 账单级 bs_id/sc_id 补全（与有网络变体一致）。 */
function collectItemIncomeInputRowsFromParsedCysmsJson(parsed) {
    const rows = [];
    if (Array.isArray(parsed)) {
        for (const row of parsed) {
            if (isPlainObject(row)) {
                rows.push(row);
            }
        }
        return rows;
    }
    if (isPlainObject(parsed)) {
        const p = parsed;
        const data = p.data;
        if (isPlainObject(data) && Array.isArray(data.itemIncomeListRaw)) {
            for (const row of data.itemIncomeListRaw) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
            return rows;
        }
        if (isPlainObject(data) && Array.isArray(data.itemIncomeList)) {
            for (const row of data.itemIncomeList) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
            return rows;
        }
        if (isPlainObject(data) && Array.isArray(data.itemListRaw)) {
            for (const row of data.itemListRaw) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
            return rows;
        }
        if (isPlainObject(data) && Array.isArray(data.itemList)) {
            for (const row of data.itemList) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
            return rows;
        }
        const bills = extractBillListFromSerialDataResult(parsed);
        return flattenBillItemsWithBillContextFromSerialBills(bills);
    }
    return rows;
}
/** 结算明细展平 stdout：settleListRaw + settleList（output_filter），不含 billList。 */
function shapeSerialDataSettleDetailsStdoutFromResult(result) {
    if (!isPlainObject(result)) {
        return result;
    }
    const bills = extractBillListFromSerialDataResult(result);
    const settleList = flattenSettleDetailsFromSerialBills(bills);
    const settleListRaw = cloneItemRows(settleList);
    const settleListOut = cloneItemRows(settleList);
    const data = isPlainObject(result.data) ? result.data : {};
    const pageInfo = data.pageInfo;
    return {
        ...result,
        data: {
            settleListRaw,
            settleList: settleListOut,
            pageInfo: pageInfo ?? null,
            bill_count: bills.length,
            settle_row_count: settleList.length,
        },
    };
}
function shapeSerialDataSettleDetailsStdoutFromMergedEnvelope(envelope, mergedBills, sourcePageTotal) {
    const settleList = flattenSettleDetailsFromSerialBills(mergedBills);
    const settleListRaw = cloneItemRows(settleList);
    const settleListOut = cloneItemRows(settleList);
    return {
        ...envelope,
        data: {
            settleListRaw,
            settleList: settleListOut,
            pageInfo: {
                merged: true,
                bill_count: mergedBills.length,
                settle_row_count: settleList.length,
                source_page_total: sourcePageTotal,
            },
        },
    };
}
/** 品项打折方案优惠明细展平 stdout：discountListRaw + discountList（output_filter），不含 billList。 */
function shapeSerialDataDiscountDetailsStdoutFromResult(result) {
    if (!isPlainObject(result)) {
        return result;
    }
    const bills = extractBillListFromSerialDataResult(result);
    const discountList = flattenDiscountDetailsFromSerialBills(bills);
    const discountListRaw = cloneItemRows(discountList);
    const discountListOut = cloneItemRows(discountList);
    const data = isPlainObject(result.data) ? result.data : {};
    const pageInfo = data.pageInfo;
    return {
        ...result,
        data: {
            discountListRaw,
            discountList: discountListOut,
            pageInfo: pageInfo ?? null,
            bill_count: bills.length,
            discount_row_count: discountList.length,
        },
    };
}
function shapeSerialDataDiscountDetailsStdoutFromMergedEnvelope(envelope, mergedBills, sourcePageTotal) {
    const discountList = flattenDiscountDetailsFromSerialBills(mergedBills);
    const discountListRaw = cloneItemRows(discountList);
    const discountListOut = cloneItemRows(discountList);
    return {
        ...envelope,
        data: {
            discountListRaw,
            discountList: discountListOut,
            pageInfo: {
                merged: true,
                bill_count: mergedBills.length,
                discount_row_count: discountList.length,
                source_page_total: sourcePageTotal,
            },
        },
    };
}
/** 满减定额优惠明细展平 stdout：fulloffListRaw + fulloffList（output_filter），不含 billList。 */
function shapeSerialDataFulloffDetailsStdoutFromResult(result) {
    if (!isPlainObject(result)) {
        return result;
    }
    const bills = extractBillListFromSerialDataResult(result);
    const fulloffList = flattenFulloffDetailsFromSerialBills(bills);
    const fulloffListRaw = cloneItemRows(fulloffList);
    const fulloffListOut = cloneItemRows(fulloffList);
    const data = isPlainObject(result.data) ? result.data : {};
    const pageInfo = data.pageInfo;
    return {
        ...result,
        data: {
            fulloffListRaw,
            fulloffList: fulloffListOut,
            pageInfo: pageInfo ?? null,
            bill_count: bills.length,
            fulloff_row_count: fulloffList.length,
        },
    };
}
function shapeSerialDataFulloffDetailsStdoutFromMergedEnvelope(envelope, mergedBills, sourcePageTotal) {
    const fulloffList = flattenFulloffDetailsFromSerialBills(mergedBills);
    const fulloffListRaw = cloneItemRows(fulloffList);
    const fulloffListOut = cloneItemRows(fulloffList);
    return {
        ...envelope,
        data: {
            fulloffListRaw,
            fulloffList: fulloffListOut,
            pageInfo: {
                merged: true,
                bill_count: mergedBills.length,
                fulloff_row_count: fulloffList.length,
                source_page_total: sourcePageTotal,
            },
        },
    };
}
/** 促销方案优惠明细展平 stdout：promoteListRaw + promoteList（output_filter），不含 billList。 */
function shapeSerialDataPromoteDetailsStdoutFromResult(result) {
    if (!isPlainObject(result)) {
        return result;
    }
    const bills = extractBillListFromSerialDataResult(result);
    const promoteList = flattenPromoteDetailsFromSerialBills(bills);
    const promoteListRaw = cloneItemRows(promoteList);
    const promoteListOut = cloneItemRows(promoteList);
    const data = isPlainObject(result.data) ? result.data : {};
    const pageInfo = data.pageInfo;
    return {
        ...result,
        data: {
            promoteListRaw,
            promoteList: promoteListOut,
            pageInfo: pageInfo ?? null,
            bill_count: bills.length,
            promote_row_count: promoteList.length,
        },
    };
}
function shapeSerialDataPromoteDetailsStdoutFromMergedEnvelope(envelope, mergedBills, sourcePageTotal) {
    const promoteList = flattenPromoteDetailsFromSerialBills(mergedBills);
    const promoteListRaw = cloneItemRows(promoteList);
    const promoteListOut = cloneItemRows(promoteList);
    return {
        ...envelope,
        data: {
            promoteListRaw,
            promoteList: promoteListOut,
            pageInfo: {
                merged: true,
                bill_count: mergedBills.length,
                promote_row_count: promoteList.length,
                source_page_total: sourcePageTotal,
            },
        },
    };
}
/** 菜品做法明细展平 stdout：itemMethodListRaw + itemMethodList（output_filter），不含 billList。 */
function shapeSerialDataItemMethodDetailsStdoutFromResult(result) {
    if (!isPlainObject(result)) {
        return result;
    }
    const bills = extractBillListFromSerialDataResult(result);
    const itemMethodList = flattenItemMethodDataFromSerialBills(bills);
    const itemMethodListRaw = cloneItemRows(itemMethodList);
    const itemMethodListOut = cloneItemRows(itemMethodList);
    const data = isPlainObject(result.data) ? result.data : {};
    const pageInfo = data.pageInfo;
    return {
        ...result,
        data: {
            itemMethodListRaw,
            itemMethodList: itemMethodListOut,
            pageInfo: pageInfo ?? null,
            bill_count: bills.length,
            item_method_row_count: itemMethodList.length,
        },
    };
}
function shapeSerialDataItemMethodDetailsStdoutFromMergedEnvelope(envelope, mergedBills, sourcePageTotal) {
    const itemMethodList = flattenItemMethodDataFromSerialBills(mergedBills);
    const itemMethodListRaw = cloneItemRows(itemMethodList);
    const itemMethodListOut = cloneItemRows(itemMethodList);
    return {
        ...envelope,
        data: {
            itemMethodListRaw,
            itemMethodList: itemMethodListOut,
            pageInfo: {
                merged: true,
                bill_count: mergedBills.length,
                item_method_row_count: itemMethodList.length,
                source_page_total: sourcePageTotal,
            },
        },
    };
}
function readSerialDataPageInfo(data) {
    if (!isPlainObject(data)) {
        return { pageNo: 1, pageTotal: 1, pageSize: 500, totalSize: 0 };
    }
    const pi = data.pageInfo;
    if (!isPlainObject(pi)) {
        return { pageNo: 1, pageTotal: 1, pageSize: 500, totalSize: 0 };
    }
    return {
        pageNo: Number(pi.pageNo) || 1,
        pageTotal: Number(pi.pageTotal) || 1,
        pageSize: Number(pi.pageSize) || 500,
        totalSize: Number(pi.totalSize) || 0,
    };
}
function looksLikeO2oTicketRow(row) {
    if (!isPlainObject(row)) {
        return false;
    }
    const r = row;
    return (r.ticketCode !== undefined ||
        r.ticketId !== undefined ||
        r.verifyId !== undefined ||
        (r.deFromName !== undefined && (r.payMoney !== undefined || r.ticketName !== undefined || r.ticketType !== undefined)));
}
function rowsFromCandidateArray(arr) {
    if (!Array.isArray(arr) || arr.length === 0) {
        return [];
    }
    const out = [];
    for (const row of arr) {
        if (isPlainObject(row)) {
            out.push(row);
        }
    }
    return out;
}
/** getO2oTicket：文档为 ticketDataList；实返可能用 billList、list 等，或 ticketDataList 为空但其它键有行 */
function extractTicketDataListFromO2oData(data) {
    if (Array.isArray(data)) {
        const rows = rowsFromCandidateArray(data);
        return rows.length && looksLikeO2oTicketRow(rows[0]) ? rows : [];
    }
    if (!isPlainObject(data)) {
        return [];
    }
    const tryFromRecord = (d) => {
        const preferKeys = [
            'ticketDataList',
            'billList',
            'ticketList',
            'ticketVoList',
            'list',
            'rows',
            'records',
            'dataList',
            'content',
        ];
        for (const k of preferKeys) {
            const rows = rowsFromCandidateArray(d[k]);
            if (rows.length && looksLikeO2oTicketRow(rows[0])) {
                return rows;
            }
        }
        for (const v of Object.values(d)) {
            const rows = rowsFromCandidateArray(v);
            if (rows.length && looksLikeO2oTicketRow(rows[0])) {
                return rows;
            }
        }
        return [];
    };
    const d = data;
    let rows = tryFromRecord(d);
    if (rows.length) {
        return rows;
    }
    const inner = d.data;
    if (isPlainObject(inner)) {
        rows = tryFromRecord(inner);
        if (rows.length) {
            return rows;
        }
    }
    return [];
}
function extractTicketDataListFromO2oApiResult(result) {
    if (!isPlainObject(result)) {
        return [];
    }
    const r = result;
    const fromData = extractTicketDataListFromO2oData(r.data);
    if (fromData.length) {
        return fromData;
    }
    return extractTicketDataListFromO2oData(r);
}
function cloneTicketRows(rows) {
    return rows.map((r) => ({ ...r }));
}
function shapeO2oTicketStdoutPayload(params) {
    const ticketDataListRaw = cloneTicketRows(params.rows);
    const ticketDataList = cloneTicketRows(params.rows);
    return {
        code: params.code ?? '0',
        msg: params.msg ?? 'success',
        data: {
            ticketDataListRaw,
            ticketDataList,
            ticket_row_count: params.rows.length,
            pageInfo: params.pageInfo ?? null,
        },
    };
}
function collectO2oTicketInputRowsFromParsedCysmsJson(parsed) {
    if (Array.isArray(parsed)) {
        const out = [];
        for (const row of parsed) {
            if (isPlainObject(row)) {
                out.push(row);
            }
        }
        return out;
    }
    if (!isPlainObject(parsed)) {
        return [];
    }
    const root = parsed;
    const data = root.data;
    if (isPlainObject(data)) {
        const d = data;
        const fromRaw = d.ticketDataListRaw;
        if (Array.isArray(fromRaw)) {
            const out = [];
            for (const row of fromRaw) {
                if (isPlainObject(row)) {
                    out.push(row);
                }
            }
            if (out.length) {
                return out;
            }
        }
        const fromList = d.ticketDataList;
        if (Array.isArray(fromList)) {
            const out = [];
            for (const row of fromList) {
                if (isPlainObject(row)) {
                    out.push(row);
                }
            }
            if (out.length) {
                return out;
            }
        }
        const nested = extractTicketDataListFromO2oData(data);
        if (nested.length) {
            return nested;
        }
    }
    return extractTicketDataListFromO2oApiResult(parsed);
}
function parseMoneyLikeForO2o(v) {
    if (v == null) {
        return 0;
    }
    if (typeof v === 'number' && Number.isFinite(v)) {
        return v;
    }
    const s = String(v).trim().replace(/,/g, '');
    if (!s) {
        return 0;
    }
    const n = Number(s);
    return Number.isFinite(n) ? n : 0;
}
/** ShowDoc #/46/24327：已核销券；网关可能返回中文描述或数值，见子 skill 说明 */
function rowMatchesRedeemedTicketState(row) {
    const ts = row.ticketState;
    const s = String(ts ?? '').trim();
    if (s.includes('已核销')) {
        return true;
    }
    if (s === '1' || ts === 1) {
        return true;
    }
    return false;
}
function applyO2oTicketSummaryFilters(rows, opts) {
    return rows.filter((row) => {
        if (opts.onlyRedeemed && !rowMatchesRedeemedTicketState(row)) {
            return false;
        }
        if (opts.ticketTypes && opts.ticketTypes.length > 0) {
            const t = Number(row.ticketType);
            if (!Number.isFinite(t) || !opts.ticketTypes.includes(t)) {
                return false;
            }
        }
        if (opts.ticketCounts && opts.ticketCounts.length > 0) {
            const c = String(row.ticketCount ?? '').trim();
            if (!opts.ticketCounts.includes(c)) {
                return false;
            }
        }
        return true;
    });
}
function parseCsvIntsO2o(raw) {
    const s = raw.trim();
    if (!s) {
        return null;
    }
    const parts = s
        .split(/[,，\s]+/)
        .map((x) => x.trim())
        .filter(Boolean);
    const nums = parts.map((p) => Number(p)).filter((n) => Number.isFinite(n));
    return nums.length ? nums : null;
}
function parseCsvStringsO2o(raw) {
    const s = raw.trim();
    if (!s) {
        return null;
    }
    const parts = s
        .split(/[,，\s]+/)
        .map((x) => x.trim())
        .filter(Boolean);
    return parts.length ? parts : null;
}
function readO2oTicketSummaryFilterFlags(flags) {
    const onlyRedeemed = flags['only-redeemed'] === 'true' ||
        flags['only-redeemed'] === '1' ||
        flags.onlyredeemed === 'true' ||
        flags.onlyRedeemed === 'true';
    const ticketTypes = parseCsvIntsO2o(String(flags['ticket-types'] || flags.tickettypes || '').trim());
    const ticketCounts = parseCsvStringsO2o(String(flags['ticket-counts'] || flags.ticketcounts || '').trim());
    return { onlyRedeemed, ticketTypes, ticketCounts };
}
function buildO2oTicketSummaryData(params) {
    const emptyMoney = () => ({
        row_count: 0,
        pay_money_sum: 0,
        income_money_sum: 0,
        ticket_income_money_sum: 0,
        disc_money_sum: 0,
        business_last_sum: 0,
    });
    const byPlatform = new Map();
    const byTicketType = new Map();
    const ticketCountBreakdown = {};
    const grand = emptyMoney();
    const ticketTypeLabel = (t) => {
        const n = Number(t);
        const labels = {
            1: '代金券',
            2: '团购(套餐券)',
            3: '单品券',
            4: '类别券(按品项)',
            5: '类别券(按小类)',
        };
        if (Number.isFinite(n) && labels[n]) {
            return `${n}:${labels[n]}`;
        }
        return String(t ?? '');
    };
    for (const row of params.analyzed_rows) {
        grand.row_count += 1;
        grand.pay_money_sum += parseMoneyLikeForO2o(row.payMoney);
        grand.income_money_sum += parseMoneyLikeForO2o(row.incomeMoney);
        grand.ticket_income_money_sum += parseMoneyLikeForO2o(row.ticketIncomeMoney);
        grand.disc_money_sum += parseMoneyLikeForO2o(row.discMoney);
        grand.business_last_sum += parseMoneyLikeForO2o(row.businessLast);
        const platKey = String(row.deFromName ?? row.bizType ?? '').trim() || '(空)';
        let pb = byPlatform.get(platKey);
        if (!pb) {
            pb = { ...emptyMoney(), deFromName: row.deFromName ?? null, bizType: row.bizType ?? null };
            byPlatform.set(platKey, pb);
        }
        pb.row_count = pb.row_count + 1;
        pb.pay_money_sum = pb.pay_money_sum + parseMoneyLikeForO2o(row.payMoney);
        pb.income_money_sum = pb.income_money_sum + parseMoneyLikeForO2o(row.incomeMoney);
        pb.ticket_income_money_sum =
            pb.ticket_income_money_sum + parseMoneyLikeForO2o(row.ticketIncomeMoney);
        pb.disc_money_sum = pb.disc_money_sum + parseMoneyLikeForO2o(row.discMoney);
        pb.business_last_sum = pb.business_last_sum + parseMoneyLikeForO2o(row.businessLast);
        const tk = ticketTypeLabel(row.ticketType);
        let tb = byTicketType.get(tk);
        if (!tb) {
            tb = { ...emptyMoney(), ticket_type_key: row.ticketType ?? null, ticket_type_label: tk };
            byTicketType.set(tk, tb);
        }
        tb.row_count = tb.row_count + 1;
        tb.pay_money_sum = tb.pay_money_sum + parseMoneyLikeForO2o(row.payMoney);
        tb.income_money_sum = tb.income_money_sum + parseMoneyLikeForO2o(row.incomeMoney);
        tb.ticket_income_money_sum =
            tb.ticket_income_money_sum + parseMoneyLikeForO2o(row.ticketIncomeMoney);
        tb.disc_money_sum = tb.disc_money_sum + parseMoneyLikeForO2o(row.discMoney);
        tb.business_last_sum = tb.business_last_sum + parseMoneyLikeForO2o(row.businessLast);
        const tc = String(row.ticketCount ?? '').trim() || '(空)';
        ticketCountBreakdown[tc] = (ticketCountBreakdown[tc] ?? 0) + 1;
    }
    return {
        schema: 'cy7.cysms.o2o_ticket_summary.v1',
        generated_at: new Date().toISOString(),
        shop_id: params.shopId,
        time_window: { begin: params.begin, end: params.end },
        seller_query: params.seller || null,
        rows_input_total: params.rows_input_total,
        rows_after_filter: params.rows_after_filter,
        filters: params.filters,
        grand_totals: grand,
        by_platform: [...byPlatform.values()],
        by_ticket_type: [...byTicketType.values()],
        ticket_count_state_breakdown: ticketCountBreakdown,
    };
}
function toFiniteNumberOrNull(v) {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
}
/** serial-data 上基于 billList 的汇总类 stdout，不走行级 output_filter，与 Openclaw 裁剪逻辑并列 */
function isSerialDataBillSummaryFormat(fmt) {
    return fmt === 'checkout-anomaly-summary' || fmt === 'abnormal-bill-summary';
}
function buildCheckoutAnomalyWaiterSummary(params) {
    const map = new Map();
    const waiterKey = (row) => {
        const c = row.waiter_code != null ? String(row.waiter_code).trim() : '';
        const n = row.waiter_name != null ? String(row.waiter_name).trim() : '';
        return `${c}\t${n}`;
    };
    for (const row of params.bills) {
        const key = waiterKey(row);
        const code = row.waiter_code != null ? String(row.waiter_code).trim() : '';
        const name = row.waiter_name != null ? String(row.waiter_name).trim() : '';
        let agg = map.get(key);
        if (!agg) {
            agg = { waiter_code: code, waiter_name: name, reversal_settlement: 0, void_bill: 0, empty_account: 0 };
            map.set(key, agg);
        }
        const st = toFiniteNumberOrNull(row.state);
        const ss = toFiniteNumberOrNull(row.settle_state);
        if (ss === -1) {
            agg.reversal_settlement += 1;
        }
        if (st === 3) {
            agg.void_bill += 1;
        }
        if (st === 2) {
            agg.empty_account += 1;
        }
    }
    const by_waiter = Array.from(map.values()).map((r) => ({
        ...r,
        focus_signal_total: r.reversal_settlement + r.void_bill + r.empty_account,
    }));
    by_waiter.sort((a, b) => b.focus_signal_total - a.focus_signal_total ||
        b.void_bill - a.void_bill ||
        b.empty_account - a.empty_account);
    return {
        schema: 'cy.checkout_anomaly_waiter_summary.v1',
        generated_at: new Date().toISOString(),
        shop_id: params.shopId,
        query_echo: params.queryEcho,
        bill_list_rows: params.bills.length,
        metrics_legend: {
            reversal_settlement: '账单主信息 settle_state = -1（返位结算，ShowDoc #/46/460）',
            void_bill: '账单主信息 state = 3（废单）',
            empty_account: '账单主信息 state = 2（空帐删除，已关账）',
        },
        by_waiter,
    };
}
/** 废单 / 空账删除 / 挂单：按 ShowDoc #/46/444 账单主信息 state 与 waiter_* 汇总（不含返位结算）。 */
function buildAbnormalBillWaiterSummary(params) {
    const map = new Map();
    const waiterKey = (row) => {
        const c = row.waiter_code != null ? String(row.waiter_code).trim() : '';
        const n = row.waiter_name != null ? String(row.waiter_name).trim() : '';
        return `${c}\t${n}`;
    };
    let emptyTot = 0;
    let voidTot = 0;
    let pendingTot = 0;
    for (const row of params.bills) {
        const st = toFiniteNumberOrNull(row.state);
        if (st !== 2 && st !== 3 && st !== 4) {
            continue;
        }
        const key = waiterKey(row);
        const code = row.waiter_code != null ? String(row.waiter_code).trim() : '';
        const name = row.waiter_name != null ? String(row.waiter_name).trim() : '';
        let agg = map.get(key);
        if (!agg) {
            agg = { waiter_code: code, waiter_name: name, empty_account_deleted: 0, voided: 0, pending_order: 0 };
            map.set(key, agg);
        }
        if (st === 2) {
            agg.empty_account_deleted += 1;
            emptyTot += 1;
        }
        else if (st === 3) {
            agg.voided += 1;
            voidTot += 1;
        }
        else {
            agg.pending_order += 1;
            pendingTot += 1;
        }
    }
    const by_waiter = Array.from(map.values()).map((r) => ({
        ...r,
        abnormal_bill_total: r.empty_account_deleted + r.voided + r.pending_order,
    }));
    by_waiter.sort((a, b) => b.abnormal_bill_total - a.abnormal_bill_total ||
        b.voided - a.voided ||
        b.empty_account_deleted - a.empty_account_deleted ||
        b.pending_order - a.pending_order);
    const waiters_involved = by_waiter.map((r) => ({
        waiter_code: r.waiter_code,
        waiter_name: r.waiter_name,
    }));
    const abnormal_bills = emptyTot + voidTot + pendingTot;
    return {
        schema: 'cy.cysms.abnormal_bill_waiter_summary.v1',
        generated_at: new Date().toISOString(),
        shop_id: params.shopId,
        query_echo: params.queryEcho,
        bill_list_rows: params.bills.length,
        totals: {
            empty_account_deleted: emptyTot,
            voided: voidTot,
            pending_order: pendingTot,
            abnormal_bills: abnormal_bills,
        },
        metrics_legend: {
            empty_account_deleted: '账单主信息 state = 2（空帐删除，已关账，ShowDoc #/46/444）',
            voided: '账单主信息 state = 3（废单）',
            pending_order: '账单主信息 state = 4（挂单）',
        },
        note: '笔数为账单条数统计，不等于定性；同一服务员可同时出现多类状态笔数。',
        by_waiter,
        waiters_involved,
    };
}
const REVERSAL_SETTLEMENT_SUMMARY_SCHEMA = 'cy7.cysms.serial_data_reversal_settlement_summary.v1';
function filterBillsReversalSettlement(bills) {
    return bills.filter((b) => {
        const m = mergeBillDetailIntoBill(b);
        return toFiniteNumberOrNull(m.settle_state) === -1;
    });
}
function waiterBucketKeyFromMergedBill(m) {
    const c = m.waiter_code != null ? String(m.waiter_code).trim() : '';
    const n = m.waiter_name != null ? String(m.waiter_name).trim() : '';
    return `${c}\t${n}`;
}
/** 返位结算（bill settle_state=-1）：订单量、服务员分桶、结算方式/销售类型 rollup（settleDetail，等同 payway-income 且 include_all_settle_states）。 */
function buildReversalSettlementSummaryCore(bills, shopId, queryEcho) {
    const reversalBills = filterBillsReversalSettlement(bills);
    const wmap = new Map();
    for (const bill of reversalBills) {
        const m = mergeBillDetailIntoBill(bill);
        const key = waiterBucketKeyFromMergedBill(m);
        const waiter_code = m.waiter_code != null ? String(m.waiter_code).trim() : '';
        const waiter_name = m.waiter_name != null ? String(m.waiter_name).trim() : '';
        const salesman_code = m.salesman_code != null ? String(m.salesman_code).trim() : '';
        const salesman_name = m.salesman_name != null ? String(m.salesman_name).trim() : '';
        let agg = wmap.get(key);
        if (!agg) {
            agg = { waiter_code, waiter_name, salesman_code, salesman_name, bill_count: 0 };
            wmap.set(key, agg);
        }
        agg.bill_count += 1;
        if (!agg.salesman_code && salesman_code) {
            agg.salesman_code = salesman_code;
        }
        if (!agg.salesman_name && salesman_name) {
            agg.salesman_name = salesman_name;
        }
    }
    const by_waiter = Array.from(wmap.values()).sort((a, b) => b.bill_count - a.bill_count ||
        a.waiter_code.localeCompare(b.waiter_code, 'zh-Hans-CN') ||
        a.waiter_name.localeCompare(b.waiter_name, 'zh-Hans-CN'));
    const payInner = buildPaywayIncomeSummaryData({
        bills: reversalBills,
        shopId,
        queryEcho: { ...queryEcho, reversal_settlement_subset: true },
        includeAllSettleStates: true,
    });
    const { schema: _pwSchema, shop_id: _sid, query_echo: _qe, generated_at: _g, metrics_legend: payLegend, ...payRollups } = payInner;
    return {
        schema: REVERSAL_SETTLEMENT_SUMMARY_SCHEMA,
        generated_at: new Date().toISOString(),
        shop_id: shopId,
        query_echo: queryEcho,
        bill_list_rows: bills.length,
        reversal_bill_count: reversalBills.length,
        metrics_legend: {
            reversal_bill_count: '账单主信息 settle_state = -1（返位结算，ShowDoc #/46/444）',
            bill_list_rows: '本窗口 billList 总条数（含非返位结算）',
            by_waiter: '返位结算账单张数按 waiter_code / waiter_name 分桶；salesman_* 为桶内首次非空回填（同一桶多营销员时不拆分）',
            payway_block: '以下 settle 汇总字段与 serial-data-payway-income-summary 同名同算法，且 **仅限返位结算账单**；结算行计入等同 include_all_settle_states=true 且排除 delflg 1/2',
            payway_metrics_legend: payLegend,
        },
        by_waiter,
        ...payRollups,
    };
}
function shapeSerialDataReversalSettlementSummaryStdout(bills, shopId, queryEcho) {
    const data = buildReversalSettlementSummaryCore(bills, shopId, queryEcho);
    return {
        code: '0',
        msg: 'success',
        data: {
            ...data,
            bill_count: bills.length,
        },
    };
}
const O2O_TICKET_MAX_PAGES = 200;
async function runCysmsO2oTicketFetchAndMerge(params) {
    const maskTok = (t) => !t || t.length <= 8 ? '***' : `${t.slice(0, 4)}…${t.slice(-4)}`;
    let token = params.token;
    const { baseUrl, ctx, begin, end, seller } = params;
    const buildHeaders = (accessToken) => ({
        access_token: accessToken,
        accessid: params.accessid,
        granttype: 'client',
    });
    let o2oReqLogged = false;
    const buildQs = (pageNo) => {
        const qs = new URLSearchParams({
            centerId: ctx.centerId,
            shopId: ctx.storeId,
            begin,
            end,
            pageNo: String(pageNo),
            pageSize: params.pageSizeRaw,
        });
        const s = seller.trim();
        if (s) {
            qs.set('seller', s);
        }
        if (ctx.groupNo) {
            qs.set('groupNo', ctx.groupNo);
        }
        (0, cysms_context_1.appendCysmsBizQueryParams)(qs, ctx);
        return qs;
    };
    const fetchPage = async (pageNo) => {
        const qs = buildQs(pageNo);
        if (params.printRequest && !o2oReqLogged) {
            o2oReqLogged = true;
            console.error('✓ getO2oTicket 整体入参（--print-request；POST Body 为空对象 {}）：');
            console.error(`  URL: ${baseUrl}${GET_O2O_TICKET_PATH}`);
            console.error(`  QueryString: ${qs.toString()}`);
            console.error(`  Headers: ${JSON.stringify({
                access_token: maskTok(token),
                accessid: params.accessid,
                granttype: 'client',
            })}`);
        }
        const endpoint = {
            path: `${GET_O2O_TICKET_PATH}?${qs.toString()}`,
            method: 'POST',
        };
        let r = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
        if (!params.tokenOverride && isLikelyCysmsTokenRejected(r)) {
            console.error('⚠ getO2oTicket 返回疑似令牌失效，已强制 accesstoken 并写回 token.json，重试一次…');
            token = await obtainCysmsAccessToken(true, params.appid, params.accessid, baseUrl);
            r = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
        }
        return r;
    };
    if (params.singlePage || params.startPage > 1) {
        const result = await fetchPage(params.startPage);
        const st = readHttpStatus(result);
        const rows = extractTicketDataListFromO2oApiResult(result);
        const data = isPlainObject(result) && isPlainObject(result.data)
            ? result.data
            : {};
        const shaped = shapeO2oTicketStdoutPayload({
            code: result?.code,
            msg: result?.msg,
            rows,
            pageInfo: data.pageInfo ?? null,
        });
        return { shaped, mergedRows: rows, httpStatus: st };
    }
    if (params.allPages) {
        const merged = [];
        let pageTotalLimit = 1;
        let lastResult = null;
        for (let p = 1; p <= pageTotalLimit && p <= O2O_TICKET_MAX_PAGES; p += 1) {
            const result = await fetchPage(p);
            lastResult = result;
            const st = readHttpStatus(result);
            if (st !== undefined && !isHttpSuccess(st)) {
                const rows = extractTicketDataListFromO2oApiResult(result);
                const shaped = shapeO2oTicketStdoutPayload({
                    code: result?.code,
                    msg: result?.msg,
                    rows,
                    pageInfo: null,
                });
                return { shaped, mergedRows: rows, httpStatus: st };
            }
            const data = isPlainObject(result) && isPlainObject(result.data)
                ? result.data
                : {};
            const chunk = extractTicketDataListFromO2oData(data);
            merged.push(...chunk);
            const pi = readSerialDataPageInfo(data);
            pageTotalLimit = Math.max(pageTotalLimit, pi.pageTotal);
            if (chunk.length === 0 && p > 1) {
                break;
            }
        }
        const pageInfoMerged = {
            merged: true,
            all_pages: true,
            pageNo: 1,
            pageSize: merged.length,
            totalSize: merged.length,
            pageTotal: 1,
            sourcePageTotal: pageTotalLimit,
            pagesFetched: Math.min(pageTotalLimit, O2O_TICKET_MAX_PAGES),
        };
        console.error(`✓ o2o-ticket --all-pages：已合并 ${merged.length} 条 ticketDataList（各页 pageSize=${params.pageSizeRaw}）`);
        const envelope = isPlainObject(lastResult) && lastResult !== null
            ? { ...lastResult }
            : { code: '0', msg: 'success', data: {} };
        const shaped = shapeO2oTicketStdoutPayload({
            code: envelope.code,
            msg: envelope.msg,
            rows: merged,
            pageInfo: pageInfoMerged,
        });
        return { shaped, mergedRows: merged, httpStatus: readHttpStatus(lastResult) };
    }
    const result = await fetchPage(1);
    const st = readHttpStatus(result);
    const httpOk = st === undefined || isHttpSuccess(st);
    const dataFirst = isPlainObject(result) && isPlainObject(result.data)
        ? result.data
        : {};
    const rowsFirst = extractTicketDataListFromO2oApiResult(result);
    const piFirst = readSerialDataPageInfo(dataFirst);
    const needMore = httpOk &&
        (piFirst.pageTotal > 1 || (piFirst.totalSize > 0 && rowsFirst.length < piFirst.totalSize));
    if (!needMore) {
        const shaped = shapeO2oTicketStdoutPayload({
            code: result?.code,
            msg: result?.msg,
            rows: rowsFirst,
            pageInfo: dataFirst.pageInfo ?? null,
        });
        return { shaped, mergedRows: rowsFirst, httpStatus: st };
    }
    const merged = [...rowsFirst];
    let pageTotalLimit = piFirst.pageTotal;
    let lastResult = result;
    for (let p = 2; p <= pageTotalLimit && p <= O2O_TICKET_MAX_PAGES; p += 1) {
        const next = await fetchPage(p);
        lastResult = next;
        const stN = readHttpStatus(next);
        if (stN !== undefined && !isHttpSuccess(stN)) {
            const rows = extractTicketDataListFromO2oApiResult(next);
            const shaped = shapeO2oTicketStdoutPayload({
                code: next?.code,
                msg: next?.msg,
                rows,
                pageInfo: null,
            });
            return { shaped, mergedRows: rows, httpStatus: stN };
        }
        const dataN = isPlainObject(next) && isPlainObject(next.data)
            ? next.data
            : {};
        const chunk = extractTicketDataListFromO2oData(dataN);
        merged.push(...chunk);
        const pi = readSerialDataPageInfo(dataN);
        pageTotalLimit = Math.max(pageTotalLimit, pi.pageTotal);
        if (chunk.length === 0 && p > 1) {
            break;
        }
    }
    const pageInfoMerged = {
        merged: true,
        auto_pages: true,
        pageNo: 1,
        pageSize: merged.length,
        totalSize: merged.length,
        pageTotal: 1,
        sourcePageTotal: pageTotalLimit,
        pagesFetched: Math.min(pageTotalLimit, O2O_TICKET_MAX_PAGES),
    };
    console.error(`✓ o2o-ticket：已按 pageInfo 自动合并 ${merged.length} 条 ticketDataList（各页 pageSize=${params.pageSizeRaw}）`);
    const envelope = isPlainObject(lastResult) && lastResult !== null
        ? { ...lastResult }
        : { code: '0', msg: 'success', data: {} };
    const shaped = shapeO2oTicketStdoutPayload({
        code: envelope.code,
        msg: envelope.msg,
        rows: merged,
        pageInfo: pageInfoMerged,
    });
    return { shaped, mergedRows: merged, httpStatus: readHttpStatus(lastResult) };
}
async function executeCysmsCommand(args) {
    if (args[0] !== 'cysms') {
        return false;
    }
    if (args[1] === 'accesstoken') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const force = flags.force === 'true' || flags.force === '1';
        const skipStores = flags['skip-stores'] === 'true' || flags['skip-stores'] === '1';
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        if (!appid || !accessid) {
            console.error(`✗ 缺少 appid 或 accessid：请在 .env 配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，或使用 --appid / --accessid（再兼容 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}、旧键 ${LEGACY_APP_ID} / ${LEGACY_ACCESS_ID}）`);
            process.exit(1);
        }
        const syncStoresIfNeeded = async () => {
            if (skipStores) {
                return;
            }
            const tok = readValidCySAccessTokenOrNull(false);
            if (!tok) {
                console.error('⚠ CY 开放 API：无可用 access_token，跳过 getshops 门店缓存');
                return;
            }
            const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
            if (!ctx.centerId) {
                console.error('⚠ CY 开放 API：缺少 centerId（如 SL_CY7_GROUP_ID），跳过 getshops 门店缓存');
                return;
            }
            (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
            await syncCySStoresFromGetshopsPaged(baseUrl, appid, accessid, tok, ctx);
        };
        const cached = getCachedCySPayloadIfValid(force);
        if (cached) {
            console.error(`✓ 使用 token.json 内 ${TOKEN_JSON_CY_S}.${CY_S_AUTH} 缓存（access_token 未过期）`);
            (0, output_1.formatOutput)(cached, (0, body_1.getFormat)(flags));
            await syncStoresIfNeeded();
            return true;
        }
        const qs = new URLSearchParams({
            appid,
            accessid,
            response_type: 'token',
        }).toString();
        const endpoint = {
            path: `${ACCESSTOKEN_PATH}?${qs}`,
            method: 'POST',
        };
        const result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms');
        const status = readHttpStatus(result);
        if (status !== undefined && !isHttpSuccess(status)) {
            console.error(`✗ HTTP 状态异常: ${String(status)}`);
        }
        (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags));
        if (status !== undefined && !isHttpSuccess(status)) {
            process.exit(1);
        }
        if (isAccesstokenSuccess(result)) {
            const slice = pickApiFieldsForCyS(result);
            persistCySMerged(slice, appid, accessid);
            console.error(`✓ 已合并写入 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}`);
            await syncStoresIfNeeded();
        }
        return true;
    }
    if (args[1] === 'store-find' || args[1] === 'cache-store-find') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const query = (flags.store ||
            flags['store-name'] ||
            flags.storename ||
            flags['store-id'] ||
            flags.storeid ||
            flags.q ||
            flags.query ||
            '').trim();
        if (!query) {
            console.error('✗ 缺少门店查询参数：请传 --store / --store-name / --store-id，可用逗号分隔多个关键词');
            process.exit(1);
        }
        const stores = (0, cysms_store_cache_1.findCysmsStoresByQuery)(query);
        (0, output_1.formatOutput)({
            code: '0',
            msg: 'success',
            data: {
                schema: 'cy7.cysms.store_cache_find.v1',
                query,
                stores,
                count: stores.length,
            },
        }, (0, body_1.getFormat)(flags));
        return true;
    }
    if (args[1] === 'store-use' || args[1] === 'cache-store-use') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const query = (flags.store ||
            flags['store-name'] ||
            flags.storename ||
            flags['store-id'] ||
            flags.storeid ||
            flags.q ||
            flags.query ||
            '').trim();
        if (!query) {
            console.error('✗ 缺少要确认的门店：请传 --store / --store-name / --store-id，可用逗号分隔多个关键词');
            process.exit(1);
        }
        const stores = (0, cysms_store_cache_1.findCysmsStoresByQuery)(query);
        if (stores.length === 0) {
            console.error('✗ 当前工作区 cache/cysms-stores.json 未匹配到门店，请先执行 sl cysms getshops 或换更准确的关键词');
            process.exit(1);
        }
        const selected = (0, cysms_store_cache_1.writeSelectedCysmsStores)(stores);
        (0, output_1.formatOutput)({
            code: '0',
            msg: 'success',
            data: {
                schema: 'cy7.cysms.store_cache_use.v1',
                query,
                stores: selected,
                count: selected.length,
            },
        }, (0, body_1.getFormat)(flags));
        console.error(`✓ 已写入当前工作区 cache/cysms-selected-stores.json（${selected.length} 条）`);
        return true;
    }
    if (args[1] === 'store-region') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.storeId) {
            console.error(`✗ 未锁定门店：请提供 --store-name / --store-id，或先执行 sl cysms store-use 写入当前工作区 cache/cysms-selected-stores.json，或配置 SL_CY7_STORE_ID，并确保 sl cysms getshops 已写入 cache/cysms-stores.json`);
            process.exit(1);
        }
        const found = (0, cysms_context_1.findCySStoreByShopId)(ctx.storeId);
        if (found.ok === false && found.reason === 'ambiguous') {
            console.error(`✗ 匹配到多条门店，请改用 --store-id。候选: ${found.candidates.join(' | ')}`);
            process.exit(1);
        }
        if (found.ok === false) {
            console.error(`✗ 未在当前工作区 cache/cysms-stores.json 中找到 shop_id=${ctx.storeId}。请执行 sl cysms getshops 同步门店列表，或检查 --store-id / 缓存门店是否与列表一致`);
            process.exit(1);
        }
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
        const storeNameFlag = (flags['store-name'] || flags.storename || '').trim();
        const storeIdFlag = (flags['store-id'] || flags.storeid || '').trim();
        if ((storeNameFlag || storeIdFlag) && ctx.storeId) {
            console.error(`✓ 门店上下文 storeId=${ctx.storeId}（cache/cysms-selected-stores.json 已刷新）`);
        }
        const regionPayload = (0, cysms_context_1.extractCySStoreRegionFromRow)(found.row);
        const shopName = typeof found.row.shop_name === 'string' ? found.row.shop_name.trim() : '';
        const onlyPrimary = flags['only-primary'] === 'true' || flags['only-primary'] === '1';
        if (onlyPrimary) {
            if (!regionPayload.primary) {
                console.error('✗ 门店档案中未找到区域类字段（region_id / adcode / region.id 等）');
                process.exit(1);
            }
            console.error(`✓ ${shopName || found.shopId} → ${regionPayload.primary.field}=${regionPayload.primary.value}`);
            console.log(regionPayload.primary.value);
            return true;
        }
        const out = {
            success: true,
            shop_id: found.shopId,
            shop_name: shopName || null,
            region: regionPayload,
            region_code: regionPayload.primary?.value ?? null,
            region_code_field: regionPayload.primary?.field ?? null,
        };
        console.error(`✓ 已解析门店「${shopName || found.shopId}」区域编码（token.json 缓存）`);
        (0, output_1.formatOutput)(out, (0, body_1.getFormat)(flags));
        return true;
    }
    const cysmsAction = args[1];
    const cysmsCommandDefinition = resolveCysmsCommandDefinition(cysmsAction);
    if (resolveCysmsBuiltinAction(cysmsAction) === 'business-situation') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const force = flags.force === 'true' || flags.force === '1';
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        const useOpenApiCredential = !!(appid && accessid);
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.centerId) {
            console.error(`✗ 缺少 centerId：请在 .env / token.json biz_params 配置 SL_CY7_GROUP_ID（或 --center-id / SL_CYSMS_CENTER_ID）`);
            process.exit(1);
        }
        if (!ctx.storeId) {
            console.error(`✗ 缺少 shopId：请配置 --store-id / --store-name / SL_CY7_STORE_ID，或先执行 sl cysms store-use 写入当前工作区 cache/cysms-selected-stores.json，并确保已 getshops 写入 cache/cysms-stores.json`);
            process.exit(1);
        }
        const qs = new URLSearchParams({ centerId: ctx.centerId, shopId: ctx.storeId });
        (0, cysms_context_1.appendCysmsBizQueryParams)(qs, ctx);
        const beginDate = (flags['begin-date'] || flags.begindate || '').trim();
        const endDate = (flags['end-date'] || flags.enddate || '').trim();
        if (beginDate || endDate) {
            if (!beginDate || !endDate) {
                console.error('✗ --begin-date 与 --end-date 须成对填写（文档：填了 beginDate 则 endDate 必填）');
                process.exit(1);
            }
            qs.set('beginDate', beginDate);
            qs.set('endDate', endDate);
        }
        const settleDate = (flags['settle-date'] || flags.settledate || '').trim();
        const dateType = (flags['date-type'] || flags.datetype || '').trim();
        if (settleDate) {
            qs.set('settleDate', settleDate);
            if (!dateType) {
                console.error('✗ 填写 --settle-date 时须同时指定 --date-type（1=按自然日 2=按营业日）');
                process.exit(1);
            }
        }
        if (dateType) {
            qs.set('dateType', dateType);
        }
        const pageNo = (flags['page-no'] || flags.pageno || '').trim();
        if (pageNo) {
            qs.set('pageNo', pageNo);
        }
        const pageSize = (flags['page-size'] || flags.pagesize || '').trim();
        if (pageSize) {
            qs.set('pageSize', pageSize);
        }
        const saleType = (flags['sale-type'] || flags.saletype || '').trim();
        if (saleType) {
            qs.set('saleType', saleType);
        }
        const itemType = (flags['item-type'] || flags.itemtype || '').trim();
        if (itemType) {
            qs.set('itemType', itemType);
        }
        const itemClassType = (flags['item-class-type'] || flags.itemclasstype || '').trim();
        if (itemClassType) {
            qs.set('itemClassType', itemClassType);
        }
        const discountedRaw = (flags.discounted || '').trim().toLowerCase();
        if (discountedRaw === 'true' || discountedRaw === '1') {
            qs.set('discounted', 'true');
        }
        else if (discountedRaw === 'false' || discountedRaw === '0') {
            qs.set('discounted', 'false');
        }
        const discIncRaw = (flags['is-disc-include-not-income'] || flags.isdiscincludenotincome || '').trim().toLowerCase();
        if (discIncRaw === 'true' || discIncRaw === '1') {
            qs.set('isDiscIncludeNotIncome', 'true');
        }
        else if (discIncRaw === 'false' || discIncRaw === '0') {
            qs.set('isDiscIncludeNotIncome', 'false');
        }
        const tokenOverride = (flags['access-token'] || '').trim();
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
        const storeNameFlag = (flags['store-name'] || flags.storename || '').trim();
        if (storeNameFlag && ctx.storeId) {
            console.error(`✓ 门店上下文 storeId=${ctx.storeId}（cache/cysms-selected-stores.json 已刷新）`);
        }
        const endpoint = {
            path: `${GET_BUSINESS_SITUATION_PATH}?${qs.toString()}`,
            method: 'POST',
        };
        const buildHeaders = (accessToken) => ({
            access_token: accessToken,
            accessid,
            granttype: 'client',
        });
        let result;
        if (useOpenApiCredential || tokenOverride) {
            let token = tokenOverride || (await obtainCysmsAccessToken(force, appid, accessid, baseUrl));
            if (!tokenOverride && readValidCySAccessTokenOrNull(force)) {
                console.error(`✓ 使用 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}.access_token`);
            }
            else if (!tokenOverride) {
                console.error('✓ 已自动换取 access_token 并写入 token.json');
            }
            result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
            if (!tokenOverride && isLikelyCysmsTokenRejected(result)) {
                console.error('⚠ business-situation 返回疑似令牌失效，已强制 accesstoken 并写回 token.json，重试一次…');
                token = await obtainCysmsAccessToken(true, appid, accessid, baseUrl);
                result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
            }
        }
        else {
            console.error('→ 未配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，改用 SLY 账号密码刷新 CY7 Token 并请求 CY7 业务接口...');
            const cy7Token = await obtainCy7SessionTokenFromSly();
            const cy7Resolved = (0, env_1.resolveBaseUrl)('cy7', 'SL_CY7_API_BASE_URL');
            const cy7BaseUrl = cy7Resolved.url.replace(/\/+$/, '');
            if (!cy7BaseUrl) {
                console.error('✗ 缺少 CY7 业务接口地址：请配置 SL_CY7_API_BASE_URL 或 SL_GATEWAY_HOST');
                process.exit(1);
            }
            result = await (0, request_1.makeRequest)(cy7BaseUrl, endpoint, cy7Token, {}, 'cy7');
        }
        const status = readHttpStatus(result);
        if (status !== undefined && !isHttpSuccess(status)) {
            console.error(`✗ HTTP 状态异常: ${String(status)}`);
        }
        (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags), cysmsCommandDefinition);
        if (status !== undefined && !isHttpSuccess(status)) {
            process.exit(1);
        }
        return true;
    }
    if (resolveCysmsBuiltinAction(cysmsAction) === 'service-area') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const force = flags.force === 'true' || flags.force === '1';
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        if (!appid || !accessid) {
            console.error(`✗ 缺少 appid 或 accessid（请在 .env 配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，或 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}）`);
            process.exit(1);
        }
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.centerId) {
            console.error(`✗ 缺少 centerId：请在 .env / token.json biz_params 配置 SL_CY7_GROUP_ID（或 --center-id / SL_CYSMS_CENTER_ID）`);
            process.exit(1);
        }
        if (!ctx.storeId) {
            console.error(`✗ 缺少 shopId：请配置 --store-id / --store-name / SL_CY7_STORE_ID，或先执行 sl cysms store-use 写入当前工作区 cache/cysms-selected-stores.json，并确保已 getshops 写入 cache/cysms-stores.json`);
            process.exit(1);
        }
        let pageSize = String(flags['page-size'] || flags.pagesize || '50').trim() || '50';
        const pageSizeNum = Number(pageSize);
        if (Number.isFinite(pageSizeNum) && pageSizeNum > 50) {
            console.error('⚠ pageSize 文档约定最大 50，已改为 50');
            pageSize = '50';
        }
        const allPages = flags['all-pages'] === 'true' || flags['all-pages'] === '1';
        const startPage = allPages
            ? 1
            : Math.max(1, Math.floor(Number(String(flags['page-no'] || flags.pageno || '1').trim()) || 1));
        const tokenOverride = (flags['access-token'] || '').trim();
        let token = tokenOverride || (await obtainCysmsAccessToken(force, appid, accessid, baseUrl));
        if (!tokenOverride && readValidCySAccessTokenOrNull(force)) {
            console.error(`✓ 使用 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}.access_token`);
        }
        else if (!tokenOverride) {
            console.error('✓ 已自动换取 access_token 并写入 token.json');
        }
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
        const storeNameFlag = (flags['store-name'] || flags.storename || '').trim();
        if (storeNameFlag && ctx.storeId) {
            console.error(`✓ 门店上下文 storeId=${ctx.storeId}（cache/cysms-selected-stores.json 已刷新）`);
        }
        const buildHeaders = (accessToken) => ({
            access_token: accessToken,
            accessid,
            granttype: 'client',
        });
        const fetchServiceAreaPage = async (pageNo) => {
            const qs = new URLSearchParams({ centerId: ctx.centerId, pageNo: String(pageNo), pageSize });
            if (ctx.groupNo) {
                qs.set('groupNo', ctx.groupNo);
            }
            (0, cysms_context_1.appendCysmsBizQueryParams)(qs, ctx);
            const endpoint = {
                path: `${GET_SERVICE_AREA_PATH}?${qs.toString()}`,
                method: 'POST',
            };
            let r = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
            if (!tokenOverride && isLikelyCysmsTokenRejected(r)) {
                console.error('⚠ service-area 返回疑似令牌失效，已强制 accesstoken 并写回 token.json，重试一次…');
                token = await obtainCysmsAccessToken(true, appid, accessid, baseUrl);
                r = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
            }
            return r;
        };
        if (!allPages) {
            const result = await fetchServiceAreaPage(startPage);
            const status = readHttpStatus(result);
            if (status !== undefined && !isHttpSuccess(status)) {
                console.error(`✗ HTTP 状态异常: ${String(status)}`);
            }
            (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags), cysmsCommandDefinition);
            if (status !== undefined && !isHttpSuccess(status)) {
                process.exit(1);
            }
            return true;
        }
        const mergedAreas = [];
        let pageTotalLimit = 1;
        let lastResult = null;
        const maxPages = 200;
        for (let p = 1; p <= pageTotalLimit && p <= maxPages; p += 1) {
            const result = await fetchServiceAreaPage(p);
            lastResult = result;
            const status = readHttpStatus(result);
            if (status !== undefined && !isHttpSuccess(status)) {
                console.error(`✗ HTTP 状态异常: ${String(status)}`);
                (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags));
                process.exit(1);
            }
            if (!isPlainObject(result)) {
                break;
            }
            const data = result.data;
            mergedAreas.push(...extractAreaListFromServiceAreaData(data));
            const pi = readServiceAreaPageInfo(data);
            pageTotalLimit = Math.max(pageTotalLimit, pi.pageTotal);
            if (extractAreaListFromServiceAreaData(data).length === 0 && p > 1) {
                break;
            }
        }
        const envelope = isPlainObject(lastResult) && lastResult !== null
            ? { ...lastResult }
            : { code: '0', msg: 'success', data: {} };
        const prevData = isPlainObject(envelope.data) ? envelope.data : {};
        envelope.data = {
            ...prevData,
            areaList: mergedAreas,
            pageInfo: {
                merged: true,
                pageNo: 1,
                pageSize: mergedAreas.length,
                totalSize: mergedAreas.length,
                pageTotal: 1,
                sourcePageTotal: pageTotalLimit,
                pagesFetched: Math.min(pageTotalLimit, maxPages),
            },
        };
        console.error(`✓ service-area --all-pages：已合并 ${mergedAreas.length} 条消费区域（含各区域 pointList）`);
        (0, output_1.formatOutput)(envelope, (0, body_1.getFormat)(flags), cysmsCommandDefinition);
        return true;
    }
    if (resolveCysmsBuiltinAction(cysmsAction) === 'item-sellout-data') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const force = flags.force === 'true' || flags.force === '1';
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        if (!appid || !accessid) {
            console.error(`✗ 缺少 appid 或 accessid（请在 .env 配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，或 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}）`);
            process.exit(1);
        }
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.centerId) {
            console.error(`✗ 缺少 centerId：请在 .env / token.json biz_params 配置 SL_CY7_GROUP_ID（或 --center-id / SL_CYSMS_CENTER_ID）`);
            process.exit(1);
        }
        if (!ctx.storeId) {
            console.error(`✗ 缺少 shopId：请配置 --store-id / --store-name / SL_CY7_STORE_ID，或先执行 sl cysms store-use 写入当前工作区 cache/cysms-selected-stores.json，并确保已 getshops 写入 cache/cysms-stores.json`);
            process.exit(1);
        }
        const timeBeginIn = (flags['time-begin'] ||
            flags.timebegin ||
            flags['begin-date'] ||
            flags.begindate ||
            flags.begin ||
            '').trim();
        const timeEndIn = (flags['time-end'] ||
            flags.timeend ||
            flags['end-date'] ||
            flags.enddate ||
            flags.end ||
            '').trim();
        if ((timeBeginIn && !timeEndIn) || (!timeBeginIn && timeEndIn)) {
            console.error('✗ item-sellout-data：--time-begin 与 --time-end 须成对填写，或二者皆省略以使用默认本机自然当日');
            process.exit(1);
        }
        let timeBegin = timeBeginIn;
        let timeEnd = timeEndIn;
        if (!timeBegin && !timeEnd) {
            const def = defaultBookOrderDetailLocalCalendarDay();
            timeBegin = def.begin;
            timeEnd = def.end;
            console.error(`✓ item-sellout-data：未指定时间，使用本机自然当日 ${def.dateLabel}（${timeBegin} ~ ${timeEnd}）`);
        }
        let pageSize = String(flags['page-size'] || flags.pagesize || '50').trim() || '50';
        const pageSizeNum = Number(pageSize);
        if (Number.isFinite(pageSizeNum) && pageSizeNum > 50) {
            console.error('⚠ pageSize 文档约定最大 50，已改为 50');
            pageSize = '50';
        }
        const allPages = flags['all-pages'] === 'true' || flags['all-pages'] === '1';
        const startPage = allPages
            ? 1
            : Math.max(1, Math.floor(Number(String(flags['page-no'] || flags.pageno || '1').trim()) || 1));
        const tokenOverride = (flags['access-token'] || '').trim();
        let token = tokenOverride || (await obtainCysmsAccessToken(force, appid, accessid, baseUrl));
        if (!tokenOverride && readValidCySAccessTokenOrNull(force)) {
            console.error(`✓ 使用 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}.access_token`);
        }
        else if (!tokenOverride) {
            console.error('✓ 已自动换取 access_token 并写入 token.json');
        }
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
        const storeNameFlag = (flags['store-name'] || flags.storename || '').trim();
        if (storeNameFlag && ctx.storeId) {
            console.error(`✓ 门店上下文 storeId=${ctx.storeId}（cache/cysms-selected-stores.json 已刷新）`);
        }
        const buildHeaders = (accessToken) => ({
            access_token: accessToken,
            accessid,
            granttype: 'client',
        });
        const fetchItemSelloutPage = async (pageNo) => {
            const qs = new URLSearchParams({
                centerId: ctx.centerId,
                pageNo: String(pageNo),
                pageSize,
                timeBegin,
                timeEnd,
            });
            if (ctx.groupNo) {
                qs.set('groupNo', ctx.groupNo);
            }
            (0, cysms_context_1.appendCysmsBizQueryParams)(qs, ctx);
            const endpoint = {
                path: `${GET_ITEM_SELLOUT_DATA_PATH}?${qs.toString()}`,
                method: 'POST',
            };
            let r = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
            if (!tokenOverride && isLikelyCysmsTokenRejected(r)) {
                console.error('⚠ item-sellout-data 返回疑似令牌失效，已强制 accesstoken 并写回 token.json，重试一次…');
                token = await obtainCysmsAccessToken(true, appid, accessid, baseUrl);
                r = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
            }
            return r;
        };
        if (!allPages) {
            const result = await fetchItemSelloutPage(startPage);
            const status = readHttpStatus(result);
            if (status !== undefined && !isHttpSuccess(status)) {
                console.error(`✗ HTTP 状态异常: ${String(status)}`);
            }
            (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags), cysmsCommandDefinition);
            if (status !== undefined && !isHttpSuccess(status)) {
                process.exit(1);
            }
            return true;
        }
        const mergedRows = [];
        let pageTotalLimit = 1;
        let lastResult = null;
        const maxPages = 200;
        for (let p = 1; p <= pageTotalLimit && p <= maxPages; p += 1) {
            const result = await fetchItemSelloutPage(p);
            lastResult = result;
            const status = readHttpStatus(result);
            if (status !== undefined && !isHttpSuccess(status)) {
                console.error(`✗ HTTP 状态异常: ${String(status)}`);
                (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags));
                process.exit(1);
            }
            if (!isPlainObject(result)) {
                break;
            }
            const data = result.data;
            const chunk = extractItemSelloutListFromData(data);
            mergedRows.push(...chunk);
            const pi = readItemSelloutPageInfo(data);
            pageTotalLimit = Math.max(pageTotalLimit, pi.pageTotal);
            if (chunk.length === 0 && p > 1) {
                break;
            }
        }
        const envelope = isPlainObject(lastResult) && lastResult !== null
            ? { ...lastResult }
            : { code: '0', msg: 'success', data: {} };
        const prevData = isPlainObject(envelope.data) ? envelope.data : {};
        envelope.data = {
            ...prevData,
            itemSelloutDataList: mergedRows,
            pageInfo: {
                merged: true,
                pageNo: 1,
                pageSize: mergedRows.length,
                totalSize: mergedRows.length,
                pageTotal: 1,
                sourcePageTotal: pageTotalLimit,
                pagesFetched: Math.min(pageTotalLimit, maxPages),
            },
        };
        console.error(`✓ item-sellout-data --all-pages：已合并 ${mergedRows.length} 条菜品估清明细`);
        (0, output_1.formatOutput)(envelope, (0, body_1.getFormat)(flags), cysmsCommandDefinition);
        return true;
    }
    if (args[1] === 'book-order-detail') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const force = flags.force === 'true' || flags.force === '1';
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        if (!appid || !accessid) {
            console.error(`✗ 缺少 appid 或 accessid（请在 .env 配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，或 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}）`);
            process.exit(1);
        }
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.centerId) {
            console.error(`✗ 缺少 centerId：请在 .env / token.json biz_params 配置 SL_CY7_GROUP_ID（或 --center-id / SL_CYSMS_CENTER_ID）`);
            process.exit(1);
        }
        if (!ctx.storeId) {
            console.error(`✗ 缺少 shopId：请配置 --store-id / --store-name / SL_CY7_STORE_ID，或先执行 sl cysms store-use 写入当前工作区 cache/cysms-selected-stores.json，并确保已 getshops 写入 cache/cysms-stores.json`);
            process.exit(1);
        }
        const beginIn = (flags.begin || '').trim();
        const endIn = (flags.end || '').trim();
        if ((beginIn && !endIn) || (!beginIn && endIn)) {
            console.error('✗ book-order-detail：--begin 与 --end 须成对填写，或二者皆省略以使用默认「本机自然当日 00:00:00 ~ 23:59:59」');
            process.exit(1);
        }
        let begin = beginIn;
        let end = endIn;
        if (!begin && !end) {
            const def = defaultBookOrderDetailLocalCalendarDay();
            begin = def.begin;
            end = def.end;
            console.error(`✓ book-order-detail：未指定 --begin/--end，使用本机自然当日 ${def.dateLabel}（${def.begin} ~ ${def.end}）`);
        }
        const qs = new URLSearchParams({ centerId: ctx.centerId, begin, end });
        if (ctx.groupNo) {
            qs.set('groupNo', ctx.groupNo);
        }
        (0, cysms_context_1.appendCysmsBizQueryParams)(qs, ctx);
        const telephone = (flags.telephone || flags.phone || '').trim();
        if (telephone) {
            qs.set('telephone', telephone);
        }
        const orderTimeType = (flags['order-time-type'] || flags.ordertimetype || '').trim();
        if (orderTimeType) {
            qs.set('orderTimeType', orderTimeType);
        }
        const tokenOverride = (flags['access-token'] || '').trim();
        let token = tokenOverride || (await obtainCysmsAccessToken(force, appid, accessid, baseUrl));
        if (!tokenOverride && readValidCySAccessTokenOrNull(force)) {
            console.error(`✓ 使用 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}.access_token`);
        }
        else if (!tokenOverride) {
            console.error('✓ 已自动换取 access_token 并写入 token.json');
        }
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
        const storeNameFlag = (flags['store-name'] || flags.storename || '').trim();
        if (storeNameFlag && ctx.storeId) {
            console.error(`✓ 门店上下文 storeId=${ctx.storeId}（cache/cysms-selected-stores.json 已刷新）`);
        }
        const endpoint = {
            path: `${GET_BOOK_ORDER_DETAIL_PATH}?${qs.toString()}`,
            method: 'POST',
        };
        const buildHeaders = (accessToken) => ({
            access_token: accessToken,
            accessid,
            granttype: 'client',
        });
        let result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
        if (!tokenOverride && isLikelyCysmsTokenRejected(result)) {
            console.error('⚠ book-order-detail 返回疑似令牌失效，已强制 accesstoken 并写回 token.json，重试一次…');
            token = await obtainCysmsAccessToken(true, appid, accessid, baseUrl);
            result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
        }
        const status = readHttpStatus(result);
        if (status !== undefined && !isHttpSuccess(status)) {
            console.error(`✗ HTTP 状态异常: ${String(status)}`);
        }
        const outFmt = (0, body_1.getFormat)(flags);
        if (outFmt === 'profile-batch') {
            const rows = extractBookOrderDetailRows(result);
            (0, output_1.formatOutput)(buildReserveProfileBatchPayload({ shopId: ctx.storeId, begin, end, rows }), 'json');
        }
        else {
            (0, output_1.formatOutput)(result, outFmt);
        }
        if (status !== undefined && !isHttpSuccess(status)) {
            process.exit(1);
        }
        return true;
    }
    if (args[1] === 'o2o-ticket' || args[1] === 'o2o-ticket-summary') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const force = flags.force === 'true' || flags.force === '1';
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        if (!appid || !accessid) {
            console.error(`✗ 缺少 appid 或 accessid（请在 .env 配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，或 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}）`);
            process.exit(1);
        }
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.centerId) {
            console.error(`✗ 缺少 centerId：请在 .env / token.json biz_params 配置 SL_CY7_GROUP_ID（或 --center-id / SL_CYSMS_CENTER_ID）`);
            process.exit(1);
        }
        if (!ctx.storeId) {
            console.error(`✗ 缺少 shopId：请配置 --store-id / --store-name / SL_CY7_STORE_ID，或先执行 sl cysms store-use 写入当前工作区 cache/cysms-selected-stores.json，并确保已 getshops 写入 cache/cysms-stores.json`);
            process.exit(1);
        }
        const beginIn = (flags.begin || '').trim();
        const endIn = (flags.end || '').trim();
        if ((beginIn && !endIn) || (!beginIn && endIn)) {
            console.error('✗ o2o-ticket / o2o-ticket-summary：--begin 与 --end 须成对填写，或二者皆省略以使用默认「本机自然当日 00:00:00 ~ 23:59:59」');
            process.exit(1);
        }
        let begin = beginIn;
        let end = endIn;
        if (!begin && !end) {
            const def = defaultBookOrderDetailLocalCalendarDay();
            begin = def.begin;
            end = def.end;
            console.error(`✓ ${args[1]}：未指定 --begin/--end，使用本机自然当日 ${def.dateLabel}（${begin} ~ ${end}）`);
        }
        let pageSizeRaw = String(flags['page-size'] || flags.pagesize || '500').trim() || '500';
        const pageSizeNum = Number(pageSizeRaw);
        if (Number.isFinite(pageSizeNum) && pageSizeNum > 500) {
            console.error('⚠ getO2oTicket：pageSize 文档最大 500，已改为 500');
            pageSizeRaw = '500';
        }
        const allPages = flags['all-pages'] === 'true' || flags['all-pages'] === '1';
        const singlePage = flags['single-page'] === 'true' || flags['single-page'] === '1' || flags.singlepage === 'true';
        const printRequest = flags['print-request'] === 'true' ||
            flags['print-request'] === '1' ||
            flags.printrequest === 'true' ||
            flags.printrequest === '1';
        const startPage = Math.max(1, Math.floor(Number(String(flags['page-no'] || flags.pageno || '1').trim()) || 1));
        const seller = String(flags.seller || '').trim();
        const tokenOverride = (flags['access-token'] || '').trim();
        let token = tokenOverride || (await obtainCysmsAccessToken(force, appid, accessid, baseUrl));
        if (!tokenOverride && readValidCySAccessTokenOrNull(force)) {
            console.error(`✓ 使用 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}.access_token`);
        }
        else if (!tokenOverride) {
            console.error('✓ 已自动换取 access_token 并写入 token.json');
        }
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
        const storeNameFlag = (flags['store-name'] || flags.storename || '').trim();
        if (storeNameFlag && ctx.storeId) {
            console.error(`✓ 门店上下文 storeId=${ctx.storeId}（cache/cysms-selected-stores.json 已刷新）`);
        }
        const runFetch = async () => runCysmsO2oTicketFetchAndMerge({
            baseUrl,
            ctx,
            begin,
            end,
            seller,
            pageSizeRaw,
            allPages,
            singlePage,
            startPage,
            printRequest,
            token,
            tokenOverride,
            appid,
            accessid,
        });
        if (args[1] === 'o2o-ticket') {
            const fmt = (0, body_1.getFormat)(flags);
            const { shaped, httpStatus } = await runFetch();
            (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('o2o-ticket'));
            if (httpStatus !== undefined && !isHttpSuccess(httpStatus)) {
                process.exit(1);
            }
            return true;
        }
        const { mergedRows, httpStatus } = await runFetch();
        if (httpStatus !== undefined && !isHttpSuccess(httpStatus)) {
            console.error(`✗ HTTP 状态异常: ${String(httpStatus)}`);
            process.exit(1);
        }
        const flt = readO2oTicketSummaryFilterFlags(flags);
        const analyzed = applyO2oTicketSummaryFilters(mergedRows, {
            onlyRedeemed: flt.onlyRedeemed,
            ticketTypes: flt.ticketTypes,
            ticketCounts: flt.ticketCounts,
        });
        const shopEcho = (flags['shop-id'] || flags.shopid || ctx.storeId || '').trim();
        const summary = buildO2oTicketSummaryData({
            shopId: shopEcho,
            begin,
            end,
            seller,
            rows_input_total: mergedRows.length,
            rows_after_filter: analyzed.length,
            filters: {
                only_redeemed: flt.onlyRedeemed,
                ticket_types: flt.ticketTypes,
                ticket_counts: flt.ticketCounts,
            },
            analyzed_rows: analyzed,
        });
        (0, output_1.formatOutput)({ code: '0', msg: 'success', data: summary }, 'json');
        return true;
    }
    if (args[1] === 'process-o2o-ticket-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        const rows = collectO2oTicketInputRowsFromParsedCysmsJson(parsed);
        const shaped = shapeO2oTicketStdoutPayload({
            code: '0',
            msg: 'success',
            rows,
            pageInfo: { source: 'stdin', merged: false },
        });
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('o2o-ticket'));
        return true;
    }
    if (args[1] === 'process-o2o-ticket-summary-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        const mergedRows = collectO2oTicketInputRowsFromParsedCysmsJson(parsed);
        const flt = readO2oTicketSummaryFilterFlags(flags);
        const analyzed = applyO2oTicketSummaryFilters(mergedRows, {
            onlyRedeemed: flt.onlyRedeemed,
            ticketTypes: flt.ticketTypes,
            ticketCounts: flt.ticketCounts,
        });
        const begin = (flags.begin || '').trim() || null;
        const end = (flags.end || '').trim() || null;
        const seller = String(flags.seller || '').trim();
        const shopEcho = (flags['shop-id'] || flags.shopid || '').trim();
        const summary = buildO2oTicketSummaryData({
            shopId: shopEcho || '(stdin)',
            begin: begin ?? '',
            end: end ?? '',
            seller,
            rows_input_total: mergedRows.length,
            rows_after_filter: analyzed.length,
            filters: {
                only_redeemed: flt.onlyRedeemed,
                ticket_types: flt.ticketTypes,
                ticket_counts: flt.ticketCounts,
            },
            analyzed_rows: analyzed,
        });
        (0, output_1.formatOutput)({ code: '0', msg: 'success', data: summary }, 'json');
        return true;
    }
    if (args[1] === 'process-serial-data-items-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        const rows = collectItemInputRowsFromParsedCysmsJson(parsed);
        const itemListRaw = cloneItemRows(rows);
        const itemList = cloneItemRows(rows);
        const shaped = {
            code: '0',
            msg: 'success',
            data: {
                itemListRaw,
                itemList,
                bill_count: null,
                item_row_count: rows.length,
                pageInfo: { source: 'stdin', merged: false },
            },
        };
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-items'));
        return true;
    }
    if (args[1] === 'process-serial-data-item-income-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        const rows = collectItemIncomeInputRowsFromParsedCysmsJson(parsed);
        const itemIncomeListRaw = cloneItemRows(rows);
        const itemIncomeList = cloneItemRows(rows);
        const shaped = {
            code: '0',
            msg: 'success',
            data: {
                itemIncomeListRaw,
                itemIncomeList,
                bill_count: null,
                item_income_row_count: rows.length,
                pageInfo: { source: 'stdin', merged: false },
            },
        };
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-item-income'));
        return true;
    }
    if (args[1] === 'process-serial-data-item-qty-summary-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const omitItemQtySummary = flags['omit-item-qty-summary'] === 'true' || flags['omit-item-qty-summary'] === '1';
        const omitItemQtySummaryByName = flags['omit-item-qty-summary-by-name'] === 'true' || flags['omit-item-qty-summary-by-name'] === '1';
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        const rows = collectItemInputRowsFromParsedCysmsJson(parsed);
        const item_qty_summary = omitItemQtySummary ? undefined : buildItemQtySummaryFromItemRows(rows);
        const item_qty_summary_by_name = omitItemQtySummaryByName
            ? undefined
            : buildItemQtySummaryByNameFromItemRows(rows);
        const shaped = {
            code: '0',
            msg: 'success',
            data: {
                ...(item_qty_summary !== undefined ? { item_qty_summary } : {}),
                ...(item_qty_summary_by_name !== undefined ? { item_qty_summary_by_name } : {}),
                bill_count: null,
                item_row_count: rows.length,
                pageInfo: { source: 'stdin', merged: false },
            },
        };
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-item-qty-summary'));
        return true;
    }
    if (args[1] === 'process-serial-data-settle-details-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        let rows = [];
        if (Array.isArray(parsed)) {
            for (const row of parsed) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
        }
        else if (isPlainObject(parsed)) {
            const p = parsed;
            const data = p.data;
            if (isPlainObject(data) && Array.isArray(data.settleListRaw)) {
                for (const row of data.settleListRaw) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else if (isPlainObject(data) && Array.isArray(data.settleList)) {
                for (const row of data.settleList) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else {
                const bills = extractBillListFromSerialDataResult(parsed);
                rows = flattenSettleDetailsFromSerialBills(bills);
            }
        }
        const settleListRaw = cloneItemRows(rows);
        const settleList = cloneItemRows(rows);
        const shaped = {
            code: '0',
            msg: 'success',
            data: {
                settleListRaw,
                settleList,
                bill_count: null,
                settle_row_count: rows.length,
                pageInfo: { source: 'stdin', merged: false },
            },
        };
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-settle-details'));
        return true;
    }
    if (args[1] === 'process-serial-data-discount-details-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        let rows = [];
        if (Array.isArray(parsed)) {
            for (const row of parsed) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
        }
        else if (isPlainObject(parsed)) {
            const p = parsed;
            const data = p.data;
            if (isPlainObject(data) && Array.isArray(data.discountListRaw)) {
                for (const row of data.discountListRaw) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else if (isPlainObject(data) && Array.isArray(data.discountList)) {
                for (const row of data.discountList) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else {
                const bills = extractBillListFromSerialDataResult(parsed);
                rows = flattenDiscountDetailsFromSerialBills(bills);
            }
        }
        const discountListRaw = cloneItemRows(rows);
        const discountList = cloneItemRows(rows);
        const shaped = {
            code: '0',
            msg: 'success',
            data: {
                discountListRaw,
                discountList,
                bill_count: null,
                discount_row_count: rows.length,
                pageInfo: { source: 'stdin', merged: false },
            },
        };
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-discount-details'));
        return true;
    }
    if (args[1] === 'process-serial-data-fulloff-details-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        let rows = [];
        if (Array.isArray(parsed)) {
            for (const row of parsed) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
        }
        else if (isPlainObject(parsed)) {
            const p = parsed;
            const data = p.data;
            if (isPlainObject(data) && Array.isArray(data.fulloffListRaw)) {
                for (const row of data.fulloffListRaw) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else if (isPlainObject(data) && Array.isArray(data.fulloffList)) {
                for (const row of data.fulloffList) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else {
                const bills = extractBillListFromSerialDataResult(parsed);
                rows = flattenFulloffDetailsFromSerialBills(bills);
            }
        }
        const fulloffListRaw = cloneItemRows(rows);
        const fulloffList = cloneItemRows(rows);
        const shaped = {
            code: '0',
            msg: 'success',
            data: {
                fulloffListRaw,
                fulloffList,
                bill_count: null,
                fulloff_row_count: rows.length,
                pageInfo: { source: 'stdin', merged: false },
            },
        };
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-fulloff-details'));
        return true;
    }
    if (args[1] === 'process-serial-data-promote-details-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        let rows = [];
        if (Array.isArray(parsed)) {
            for (const row of parsed) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
        }
        else if (isPlainObject(parsed)) {
            const p = parsed;
            const data = p.data;
            if (isPlainObject(data) && Array.isArray(data.promoteListRaw)) {
                for (const row of data.promoteListRaw) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else if (isPlainObject(data) && Array.isArray(data.promoteList)) {
                for (const row of data.promoteList) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else {
                const bills = extractBillListFromSerialDataResult(parsed);
                rows = flattenPromoteDetailsFromSerialBills(bills);
            }
        }
        const promoteListRaw = cloneItemRows(rows);
        const promoteList = cloneItemRows(rows);
        const shaped = {
            code: '0',
            msg: 'success',
            data: {
                promoteListRaw,
                promoteList,
                bill_count: null,
                promote_row_count: rows.length,
                pageInfo: { source: 'stdin', merged: false },
            },
        };
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-promote-details'));
        return true;
    }
    if (args[1] === 'process-serial-data-item-method-details-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        let rows = [];
        if (Array.isArray(parsed)) {
            for (const row of parsed) {
                if (isPlainObject(row)) {
                    rows.push(row);
                }
            }
        }
        else if (isPlainObject(parsed)) {
            const p = parsed;
            const data = p.data;
            if (isPlainObject(data) && Array.isArray(data.itemMethodListRaw)) {
                for (const row of data.itemMethodListRaw) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else if (isPlainObject(data) && Array.isArray(data.itemMethodList)) {
                for (const row of data.itemMethodList) {
                    if (isPlainObject(row)) {
                        rows.push(row);
                    }
                }
            }
            else {
                const bills = extractBillListFromSerialDataResult(parsed);
                rows = flattenItemMethodDataFromSerialBills(bills);
            }
        }
        const itemMethodListRaw = cloneItemRows(rows);
        const itemMethodList = cloneItemRows(rows);
        const shaped = {
            code: '0',
            msg: 'success',
            data: {
                itemMethodListRaw,
                itemMethodList,
                bill_count: null,
                item_method_row_count: rows.length,
                pageInfo: { source: 'stdin', merged: false },
            },
        };
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-item-method-details'));
        return true;
    }
    if (args[1] === 'process-serial-data-payway-income-summary-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const includeAllSettleStates = flags['include-all-settle-states'] === 'true' ||
            flags['include-all-settle-states'] === '1' ||
            flags.includeallsettlestates === 'true';
        const shopOverride = String(flags['shop-id'] || flags['store-id'] || '').trim();
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        let bills = [];
        let settleRowsOverride = null;
        if (Array.isArray(parsed)) {
            settleRowsOverride = [];
            for (const row of parsed) {
                if (isPlainObject(row)) {
                    settleRowsOverride.push(row);
                }
            }
        }
        else if (isPlainObject(parsed)) {
            const p = parsed;
            const data = p.data;
            const rawList = isPlainObject(data) && Array.isArray(data.settleListRaw) ? data.settleListRaw : null;
            const slimList = isPlainObject(data) && Array.isArray(data.settleList) ? data.settleList : null;
            if (rawList && rawList.length > 0) {
                settleRowsOverride = [];
                for (const row of rawList) {
                    if (isPlainObject(row)) {
                        settleRowsOverride.push(row);
                    }
                }
            }
            else if (slimList && slimList.length > 0) {
                settleRowsOverride = [];
                for (const row of slimList) {
                    if (isPlainObject(row)) {
                        settleRowsOverride.push(row);
                    }
                }
            }
            else {
                bills = extractBillListFromSerialDataResult(parsed);
            }
        }
        const usedRows = settleRowsOverride != null && settleRowsOverride.length > 0;
        const queryEcho = {
            source: 'stdin',
            stdin_settle_rows_only: usedRows,
            include_all_settle_states: includeAllSettleStates,
        };
        if (shopOverride) {
            queryEcho.shop_id_override = shopOverride;
        }
        let shopId = shopOverride;
        if (!shopId && isPlainObject(parsed)) {
            const data = parsed.data;
            if (isPlainObject(data)) {
                const sid = data.shopId ?? data.shop_id;
                if (sid != null && String(sid).trim()) {
                    shopId = String(sid).trim();
                }
            }
        }
        if (!shopId) {
            shopId = 'unknown';
        }
        const shaped = shapeSerialDataPaywayIncomeSummaryStdout(bills, shopId, queryEcho, includeAllSettleStates, usedRows ? settleRowsOverride : null);
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-payway-income-summary'));
        return true;
    }
    if (args[1] === 'process-serial-data-abnormal-bill-summary-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const shopOverride = String(flags['shop-id'] || flags['store-id'] || '').trim();
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        let bills;
        if (Array.isArray(parsed)) {
            bills = [];
            for (const row of parsed) {
                if (isPlainObject(row)) {
                    bills.push(row);
                }
            }
        }
        else {
            bills = extractBillListFromSerialDataResult(parsed);
        }
        const queryEcho = { source: 'stdin' };
        if (shopOverride) {
            queryEcho.shop_id_override = shopOverride;
        }
        let shopId = shopOverride;
        if (!shopId && isPlainObject(parsed)) {
            const data = parsed.data;
            if (isPlainObject(data)) {
                const sid = data.shopId ?? data.shop_id;
                if (sid != null && String(sid).trim()) {
                    shopId = String(sid).trim();
                }
            }
        }
        if (!shopId) {
            shopId = 'unknown';
        }
        (0, output_1.formatOutput)(buildAbnormalBillWaiterSummary({
            shopId,
            bills,
            queryEcho,
        }), 'json', undefined);
        return true;
    }
    if (args[1] === 'process-serial-data-reversal-settlement-summary-json') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const fmt = (0, body_1.getFormat)(flags);
        const shopOverride = String(flags['shop-id'] || flags['store-id'] || '').trim();
        const stdinText = (0, fs_1.readFileSync)(0, 'utf8');
        let parsed;
        try {
            parsed = (0, parse_cysms_json_1.parseCysmsJson)(stdinText.trim() || 'null');
        }
        catch {
            console.error('✗ stdin 不是合法 JSON');
            process.exit(1);
        }
        let bills;
        if (Array.isArray(parsed)) {
            bills = [];
            for (const row of parsed) {
                if (isPlainObject(row)) {
                    bills.push(row);
                }
            }
        }
        else {
            bills = extractBillListFromSerialDataResult(parsed);
        }
        const queryEcho = { source: 'stdin' };
        if (shopOverride) {
            queryEcho.shop_id_override = shopOverride;
        }
        let shopId = shopOverride;
        if (!shopId && isPlainObject(parsed)) {
            const data = parsed.data;
            if (isPlainObject(data)) {
                const sid = data.shopId ?? data.shop_id;
                if (sid != null && String(sid).trim()) {
                    shopId = String(sid).trim();
                }
            }
        }
        if (!shopId) {
            shopId = 'unknown';
        }
        const shaped = shapeSerialDataReversalSettlementSummaryStdout(bills, shopId, queryEcho);
        (0, output_1.formatOutput)(shaped, fmt, resolveCysmsCommandDefinition('serial-data-reversal-settlement-summary'));
        return true;
    }
    if (args[1] === 'serial-data' ||
        args[1] === 'serial-data-openclaw' ||
        args[1] === 'serial-data-items' ||
        args[1] === 'serial-data-item-income' ||
        args[1] === 'serial-data-item-qty-summary' ||
        args[1] === 'serial-data-settle-details' ||
        args[1] === 'serial-data-discount-details' ||
        args[1] === 'serial-data-fulloff-details' ||
        args[1] === 'serial-data-promote-details' ||
        args[1] === 'serial-data-item-method-details' ||
        args[1] === 'serial-data-payway-income-summary' ||
        args[1] === 'serial-data-reversal-settlement-summary') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const isOpenclawVariant = args[1] === 'serial-data-openclaw';
        const isItemsVariant = args[1] === 'serial-data-items';
        const isItemIncomeVariant = args[1] === 'serial-data-item-income';
        const isItemQtySummaryVariant = args[1] === 'serial-data-item-qty-summary';
        const isSettleDetailsVariant = args[1] === 'serial-data-settle-details';
        const isDiscountDetailsVariant = args[1] === 'serial-data-discount-details';
        const isFulloffDetailsVariant = args[1] === 'serial-data-fulloff-details';
        const isPromoteDetailsVariant = args[1] === 'serial-data-promote-details';
        const isItemMethodDetailsVariant = args[1] === 'serial-data-item-method-details';
        const isPaywayIncomeSummaryVariant = args[1] === 'serial-data-payway-income-summary';
        const isReversalSettlementSummaryVariant = args[1] === 'serial-data-reversal-settlement-summary';
        const isSerialFlattenVariant = isItemsVariant ||
            isItemIncomeVariant ||
            isItemQtySummaryVariant ||
            isSettleDetailsVariant ||
            isDiscountDetailsVariant ||
            isFulloffDetailsVariant ||
            isPromoteDetailsVariant ||
            isItemMethodDetailsVariant ||
            isPaywayIncomeSummaryVariant ||
            isReversalSettlementSummaryVariant;
        const serialCmdDef = resolveCysmsCommandDefinition(isOpenclawVariant
            ? 'serial-data-openclaw'
            : isItemsVariant
                ? 'serial-data-items'
                : isItemIncomeVariant
                    ? 'serial-data-item-income'
                    : isItemQtySummaryVariant
                        ? 'serial-data-item-qty-summary'
                        : isSettleDetailsVariant
                            ? 'serial-data-settle-details'
                            : isDiscountDetailsVariant
                                ? 'serial-data-discount-details'
                                : isFulloffDetailsVariant
                                    ? 'serial-data-fulloff-details'
                                    : isPromoteDetailsVariant
                                        ? 'serial-data-promote-details'
                                        : isItemMethodDetailsVariant
                                            ? 'serial-data-item-method-details'
                                            : isPaywayIncomeSummaryVariant
                                                ? 'serial-data-payway-income-summary'
                                                : isReversalSettlementSummaryVariant
                                                    ? 'serial-data-reversal-settlement-summary'
                                                    : 'serial-data');
        const force = flags.force === 'true' || flags.force === '1';
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        if (!appid || !accessid) {
            console.error(`✗ 缺少 appid 或 accessid（请在 .env 配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，或 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}）`);
            process.exit(1);
        }
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.centerId) {
            console.error(`✗ 缺少 centerId：请在 .env / token.json biz_params 配置 SL_CY7_GROUP_ID（或 --center-id / SL_CYSMS_CENTER_ID）`);
            process.exit(1);
        }
        if (!ctx.storeId) {
            console.error(`✗ 缺少 shopId：请配置 --store-id / --store-name / SL_CY7_STORE_ID，或先执行 sl cysms store-use 写入当前工作区 cache/cysms-selected-stores.json，并确保已 getshops 写入 cache/cysms-stores.json`);
            process.exit(1);
        }
        const settleDate = (flags['settle-date'] || flags.settledate || '').trim();
        const beginDate = (flags['begin-date'] || flags.begindate || flags.begin || '').trim();
        const endDate = (flags['end-date'] || flags.enddate || flags.end || '').trim();
        let dateType = (flags['date-type'] || flags.datetype || '').trim();
        if (settleDate && (beginDate || endDate)) {
            console.error('✗ serial-data：--settle-date 与 --begin-date/--end-date（或 --begin/--end）请勿同时填写');
            process.exit(1);
        }
        if ((beginDate && !endDate) || (!beginDate && endDate)) {
            console.error('✗ serial-data：--begin-date/--end-date 与 --begin/--end 须成对填写，或改用 --settle-date + --date-type');
            process.exit(1);
        }
        if (settleDate && !dateType) {
            console.error('✗ serial-data：填写 --settle-date 时须同时指定 --date-type（1=自然日 2=营业日）');
            process.exit(1);
        }
        let beginEff = beginDate;
        let endEff = endDate;
        if (!settleDate && !beginEff && !endEff) {
            if (isOpenclawVariant || isSerialFlattenVariant) {
                const def = defaultBookOrderDetailLocalCalendarDay();
                beginEff = def.begin;
                endEff = def.end;
                dateType = '5';
                if (isOpenclawVariant) {
                    console.error(`✓ serial-data-openclaw：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径）`);
                }
                else if (isSettleDetailsVariant) {
                    console.error(`✓ serial-data-settle-details：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-items 一致）`);
                }
                else if (isDiscountDetailsVariant) {
                    console.error(`✓ serial-data-discount-details：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-items 一致）`);
                }
                else if (isFulloffDetailsVariant) {
                    console.error(`✓ serial-data-fulloff-details：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-items 一致）`);
                }
                else if (isPromoteDetailsVariant) {
                    console.error(`✓ serial-data-promote-details：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-items 一致）`);
                }
                else if (isItemMethodDetailsVariant) {
                    console.error(`✓ serial-data-item-method-details：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-items 一致）`);
                }
                else if (isPaywayIncomeSummaryVariant) {
                    console.error(`✓ serial-data-payway-income-summary：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-settle-details 一致）`);
                }
                else if (isReversalSettlementSummaryVariant) {
                    console.error(`✓ serial-data-reversal-settlement-summary：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-payway-income-summary 一致）`);
                }
                else if (isItemIncomeVariant) {
                    console.error(`✓ serial-data-item-income：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-items 一致）`);
                }
                else if (isItemQtySummaryVariant) {
                    console.error(`✓ serial-data-item-qty-summary：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-items 一致）`);
                }
                else {
                    console.error(`✓ serial-data-items：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}）且 dateType=5（最后上传口径；与 serial-data-openclaw 一致）`);
                }
            }
            else {
                const def = defaultBookOrderDetailLocalCalendarDay();
                beginEff = def.begin;
                endEff = def.end;
                if (!dateType) {
                    dateType = '3';
                }
                console.error(`✓ serial-data：未指定时间窗，使用本机自然当日 ${def.dateLabel}（${beginEff} ~ ${endEff}），dateType=3（结算时间）`);
            }
        }
        if (beginEff && endEff && !dateType) {
            dateType = isSerialFlattenVariant ? '5' : '3';
        }
        let pageSizeRaw = String(flags['page-size'] || flags.pagesize || '500').trim() || '500';
        const pageSizeNum = Number(pageSizeRaw);
        if (Number.isFinite(pageSizeNum) && pageSizeNum > 500) {
            console.error('⚠ serial-data：pageSize 文档最大 500，已改为 500');
            pageSizeRaw = '500';
        }
        const allPages = flags['all-pages'] === 'true' || flags['all-pages'] === '1';
        const maxSerialDataPages = 200;
        const itemsSinglePage = flags['single-page'] === 'true' || flags['single-page'] === '1' || flags.singlepage === 'true';
        const printRequest = flags['print-request'] === 'true' ||
            flags['print-request'] === '1' ||
            flags.printrequest === 'true' ||
            flags.printrequest === '1';
        const tokenOverride = (flags['access-token'] || '').trim();
        let token = tokenOverride || (await obtainCysmsAccessToken(force, appid, accessid, baseUrl));
        if (!tokenOverride && readValidCySAccessTokenOrNull(force)) {
            console.error(`✓ 使用 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}.access_token`);
        }
        else if (!tokenOverride) {
            console.error('✓ 已自动换取 access_token 并写入 token.json');
        }
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
        const storeNameFlag = (flags['store-name'] || flags.storename || '').trim();
        if (storeNameFlag && ctx.storeId) {
            console.error(`✓ 门店上下文 storeId=${ctx.storeId}（cache/cysms-selected-stores.json 已刷新）`);
        }
        const buildHeaders = (accessToken) => ({
            access_token: accessToken,
            accessid,
            granttype: 'client',
        });
        const buildQsForPage = (pageNo) => {
            const qs = new URLSearchParams({
                centerId: ctx.centerId,
                pageNo: String(pageNo),
                pageSize: pageSizeRaw,
            });
            if (ctx.groupNo) {
                qs.set('groupNo', ctx.groupNo);
            }
            (0, cysms_context_1.appendCysmsBizQueryParams)(qs, ctx);
            if (settleDate) {
                qs.set('settleDate', settleDate);
                qs.set('dateType', dateType);
            }
            else {
                qs.set('beginDate', beginEff);
                qs.set('endDate', endEff);
                qs.set('dateType', dateType);
            }
            const needPkg = (flags['need-pkg-detail'] || flags.needpkgdetail || '').trim();
            if (needPkg === '0' || needPkg === '1') {
                qs.set('needPkgDetail', needPkg);
            }
            const orderType = (flags['order-type'] || flags.ordertype || '').trim();
            if (orderType) {
                qs.set('orderType', orderType);
            }
            const isData = (flags['is-data-filtering'] || flags.isdatafiltering || '').trim();
            if (isData === '0' || isData === '1') {
                qs.set('isDataFiltering', isData);
            }
            const isUnsettled = (flags['is-query-unsettled'] || flags.isqueryunsettled || '').trim();
            if (isUnsettled === '0' || isUnsettled === '1') {
                qs.set('isQueryUnsettled', isUnsettled);
            }
            return qs;
        };
        const maskAccessTokenForLog = (t) => {
            const s = String(t || '').trim();
            if (!s) {
                return '（空）';
            }
            if (s.length <= 12) {
                return '***';
            }
            return `${s.slice(0, 4)}…${s.slice(-4)}`;
        };
        let serialRequestLogged = false;
        const queryEcho = {
            centerId: ctx.centerId,
            shopId: ctx.storeId,
            settleDate: settleDate || null,
            beginDate: beginEff || null,
            endDate: endEff || null,
            dateType: dateType || null,
            pageSize: pageSizeRaw,
            all_pages: allPages,
        };
        const fetchSerialPage = async (pageNo) => {
            const qs = buildQsForPage(pageNo);
            if (printRequest && !serialRequestLogged) {
                serialRequestLogged = true;
                console.error('✓ getserialdata 整体入参（--print-request；POST Body 为空对象 {}）：');
                console.error(`  URL: ${baseUrl}${GET_SERIAL_DATA_PATH}`);
                console.error(`  QueryString: ${qs.toString()}`);
                console.error(`  Headers: ${JSON.stringify({
                    access_token: maskAccessTokenForLog(token),
                    accessid,
                    granttype: 'client',
                })}`);
            }
            const endpoint = {
                path: `${GET_SERIAL_DATA_PATH}?${qs.toString()}`,
                method: 'POST',
            };
            let r = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
            if (!tokenOverride && isLikelyCysmsTokenRejected(r)) {
                console.error('⚠ serial-data 返回疑似令牌失效，已强制 accesstoken 并写回 token.json，重试一次…');
                token = await obtainCysmsAccessToken(true, appid, accessid, baseUrl);
                r = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
            }
            return r;
        };
        const outFmt = (0, body_1.getFormat)(flags);
        if (isSerialFlattenVariant && isSerialDataBillSummaryFormat(outFmt)) {
            console.error('✗ serial-data-items / serial-data-item-income / serial-data-item-qty-summary / serial-data-settle-details / serial-data-discount-details / serial-data-fulloff-details / serial-data-promote-details / serial-data-item-method-details / serial-data-payway-income-summary / serial-data-reversal-settlement-summary：不支持 --format checkout-anomaly-summary 或 --format abnormal-bill-summary，请使用 sl cysms serial-data');
            process.exit(1);
        }
        /** 汇总格式与原始 billList 结构不同；OpenClaw 变体 stdout 另做明细数组剔除，勿套行级 output_filter */
        const serialFormatCmd = isSerialDataBillSummaryFormat(outFmt) ? undefined : serialCmdDef;
        const serialItemQtyShapeOpts = isItemQtySummaryVariant
            ? {
                omitItemQtySummary: flags['omit-item-qty-summary'] === 'true' || flags['omit-item-qty-summary'] === '1',
                omitItemQtySummaryByName: flags['omit-item-qty-summary-by-name'] === 'true' ||
                    flags['omit-item-qty-summary-by-name'] === '1',
            }
            : undefined;
        const includeAllSettleStatesForPayway = flags['include-all-settle-states'] === 'true' ||
            flags['include-all-settle-states'] === '1' ||
            flags.includeallsettlestates === 'true';
        if (!allPages) {
            const startPage = Math.max(1, Math.floor(Number(String(flags['page-no'] || flags.pageno || '1').trim()) || 1));
            const result = await fetchSerialPage(startPage);
            const status = readHttpStatus(result);
            if (status !== undefined && !isHttpSuccess(status)) {
                console.error(`✗ HTTP 状态异常: ${String(status)}`);
            }
            const httpOk = status === undefined || isHttpSuccess(status);
            if (isSerialFlattenVariant &&
                startPage === 1 &&
                !itemsSinglePage &&
                !isSerialDataBillSummaryFormat(outFmt) &&
                httpOk &&
                isPlainObject(result)) {
                const billsFirst = extractBillListFromSerialDataResult(result);
                const dataFirst = isPlainObject(result.data) ? result.data : {};
                const piFirst = readSerialDataPageInfo(dataFirst);
                const needMorePages = piFirst.pageTotal > 1 || (piFirst.totalSize > 0 && billsFirst.length < piFirst.totalSize);
                if (needMorePages) {
                    const mergedBills = [...billsFirst];
                    let pageTotalLimit = piFirst.pageTotal;
                    let lastResult = result;
                    for (let p = 2; p <= pageTotalLimit && p <= maxSerialDataPages; p += 1) {
                        const nextResult = await fetchSerialPage(p);
                        lastResult = nextResult;
                        const st = readHttpStatus(nextResult);
                        if (st !== undefined && !isHttpSuccess(st)) {
                            console.error(`✗ HTTP 状态异常: ${String(st)}`);
                            const shapedErr = isItemsVariant
                                ? shapeSerialDataItemsStdoutFromResult(nextResult)
                                : isItemIncomeVariant
                                    ? shapeSerialDataItemIncomeStdoutFromResult(nextResult)
                                    : isItemQtySummaryVariant
                                        ? shapeSerialDataItemQtySummaryStdoutFromResult(nextResult, serialItemQtyShapeOpts)
                                        : isSettleDetailsVariant
                                            ? shapeSerialDataSettleDetailsStdoutFromResult(nextResult)
                                            : isDiscountDetailsVariant
                                                ? shapeSerialDataDiscountDetailsStdoutFromResult(nextResult)
                                                : isFulloffDetailsVariant
                                                    ? shapeSerialDataFulloffDetailsStdoutFromResult(nextResult)
                                                    : isPromoteDetailsVariant
                                                        ? shapeSerialDataPromoteDetailsStdoutFromResult(nextResult)
                                                        : isItemMethodDetailsVariant
                                                            ? shapeSerialDataItemMethodDetailsStdoutFromResult(nextResult)
                                                            : isPaywayIncomeSummaryVariant
                                                                ? shapeSerialDataPaywayIncomeSummaryStdout(extractBillListFromSerialDataResult(nextResult), ctx.storeId, {
                                                                    ...queryEcho,
                                                                    include_all_settle_states: includeAllSettleStatesForPayway,
                                                                }, includeAllSettleStatesForPayway, null)
                                                                : isReversalSettlementSummaryVariant
                                                                    ? shapeSerialDataReversalSettlementSummaryStdout(extractBillListFromSerialDataResult(nextResult), ctx.storeId, { ...queryEcho, pageNo: p })
                                                                    : applyOpenclawSerialStdoutShaping(isOpenclawVariant, outFmt, nextResult);
                            (0, output_1.formatOutput)(shapedErr, outFmt, serialFormatCmd);
                            process.exit(1);
                        }
                        if (!isPlainObject(nextResult)) {
                            break;
                        }
                        const data = nextResult.data;
                        const chunk = extractBillListFromSerialDataResult(nextResult);
                        mergedBills.push(...chunk);
                        const pi = readSerialDataPageInfo(data);
                        pageTotalLimit = Math.max(pageTotalLimit, pi.pageTotal);
                        if (chunk.length === 0 && p > 1) {
                            break;
                        }
                    }
                    const envelope = isPlainObject(lastResult) && lastResult !== null
                        ? { ...lastResult }
                        : { code: '0', msg: 'success', data: {} };
                    const prevData = isPlainObject(envelope.data) ? envelope.data : {};
                    envelope.data = {
                        ...prevData,
                        billList: mergedBills,
                        pageInfo: {
                            merged: true,
                            auto_items_pages: true,
                            pageNo: 1,
                            pageSize: mergedBills.length,
                            totalSize: mergedBills.length,
                            pageTotal: 1,
                            sourcePageTotal: pageTotalLimit,
                            pagesFetched: Math.min(pageTotalLimit, maxSerialDataPages),
                        },
                    };
                    if (isItemsVariant) {
                        const itemMergedCount = flattenBillItemsFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-items：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList → ${itemMergedCount} 条品项（item）行（各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataItemsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isItemIncomeVariant) {
                        const itemIncomeMergedCount = flattenBillItemsWithBillContextFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-item-income：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList → ${itemIncomeMergedCount} 条品项收入（item）行（各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataItemIncomeStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isItemQtySummaryVariant) {
                        const itemMergedCount = flattenBillItemsFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-item-qty-summary：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList → ${itemMergedCount} 条品项（item）行用于汇总（各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataItemQtySummaryStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit, serialItemQtyShapeOpts);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isSettleDetailsVariant) {
                        const settleMergedCount = flattenSettleDetailsFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-settle-details：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList → ${settleMergedCount} 条结算明细（settleDetail）行（各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataSettleDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isDiscountDetailsVariant) {
                        const discountMergedCount = flattenDiscountDetailsFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-discount-details：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList → ${discountMergedCount} 条品项打折方案优惠明细（discountDetail）行（各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataDiscountDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isFulloffDetailsVariant) {
                        const fulloffMergedCount = flattenFulloffDetailsFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-fulloff-details：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList → ${fulloffMergedCount} 条满减定额优惠明细（fulloffDetail）行（各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataFulloffDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isPromoteDetailsVariant) {
                        const promoteMergedCount = flattenPromoteDetailsFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-promote-details：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList → ${promoteMergedCount} 条促销方案优惠明细（promoteDetail）行（各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataPromoteDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isItemMethodDetailsVariant) {
                        const itemMethodMergedCount = flattenItemMethodDataFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-item-method-details：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList → ${itemMethodMergedCount} 条菜品做法明细（itemMethodData）行（各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataItemMethodDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isPaywayIncomeSummaryVariant) {
                        const paywayRows = flattenSettleDetailsWithSaleTypeFromSerialBills(mergedBills).length;
                        console.error(`✓ serial-data-payway-income-summary：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList（${paywayRows} 条结算行用于汇总；各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataPaywayIncomeSummaryStdout(mergedBills, ctx.storeId, { ...queryEcho, include_all_settle_states: includeAllSettleStatesForPayway }, includeAllSettleStatesForPayway, null);
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    else if (isReversalSettlementSummaryVariant) {
                        const revBills = filterBillsReversalSettlement(mergedBills);
                        const revRows = flattenSettleDetailsWithSaleTypeFromSerialBills(revBills).length;
                        console.error(`✓ serial-data-reversal-settlement-summary：已按 pageInfo 自动合并 ${mergedBills.length} 条 billList（返位 ${revBills.length} 张，${revRows} 条结算行参与汇总；各页 pageSize=${pageSizeRaw}，与首屏一致）`);
                        const shaped = shapeSerialDataReversalSettlementSummaryStdout(mergedBills, ctx.storeId, {
                            ...queryEcho,
                            pageNo: startPage,
                        });
                        (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
                    }
                    return true;
                }
            }
            if (isSerialDataBillSummaryFormat(outFmt)) {
                const bills = extractBillListFromSerialDataResult(result);
                (0, output_1.formatOutput)(outFmt === 'checkout-anomaly-summary'
                    ? buildCheckoutAnomalyWaiterSummary({
                        shopId: ctx.storeId,
                        bills,
                        queryEcho: { ...queryEcho, pageNo: startPage },
                    })
                    : buildAbnormalBillWaiterSummary({
                        shopId: ctx.storeId,
                        bills,
                        queryEcho: { ...queryEcho, pageNo: startPage },
                    }), 'json', undefined);
            }
            else {
                const shaped = isItemsVariant
                    ? shapeSerialDataItemsStdoutFromResult(result)
                    : isItemIncomeVariant
                        ? shapeSerialDataItemIncomeStdoutFromResult(result)
                        : isItemQtySummaryVariant
                            ? shapeSerialDataItemQtySummaryStdoutFromResult(result, serialItemQtyShapeOpts)
                            : isSettleDetailsVariant
                                ? shapeSerialDataSettleDetailsStdoutFromResult(result)
                                : isDiscountDetailsVariant
                                    ? shapeSerialDataDiscountDetailsStdoutFromResult(result)
                                    : isFulloffDetailsVariant
                                        ? shapeSerialDataFulloffDetailsStdoutFromResult(result)
                                        : isPromoteDetailsVariant
                                            ? shapeSerialDataPromoteDetailsStdoutFromResult(result)
                                            : isItemMethodDetailsVariant
                                                ? shapeSerialDataItemMethodDetailsStdoutFromResult(result)
                                                : isPaywayIncomeSummaryVariant
                                                    ? shapeSerialDataPaywayIncomeSummaryStdout(extractBillListFromSerialDataResult(result), ctx.storeId, {
                                                        ...queryEcho,
                                                        pageNo: startPage,
                                                        include_all_settle_states: includeAllSettleStatesForPayway,
                                                    }, includeAllSettleStatesForPayway, null)
                                                    : isReversalSettlementSummaryVariant
                                                        ? shapeSerialDataReversalSettlementSummaryStdout(extractBillListFromSerialDataResult(result), ctx.storeId, { ...queryEcho, pageNo: startPage })
                                                        : applyOpenclawSerialStdoutShaping(isOpenclawVariant, outFmt, result);
                (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
            }
            if (status !== undefined && !isHttpSuccess(status)) {
                process.exit(1);
            }
            return true;
        }
        const mergedBills = [];
        let pageTotalLimit = 1;
        let lastResult = null;
        for (let p = 1; p <= pageTotalLimit && p <= maxSerialDataPages; p += 1) {
            const result = await fetchSerialPage(p);
            lastResult = result;
            const status = readHttpStatus(result);
            if (status !== undefined && !isHttpSuccess(status)) {
                console.error(`✗ HTTP 状态异常: ${String(status)}`);
                const shapedErr = isItemsVariant
                    ? shapeSerialDataItemsStdoutFromResult(result)
                    : isItemIncomeVariant
                        ? shapeSerialDataItemIncomeStdoutFromResult(result)
                        : isItemQtySummaryVariant
                            ? shapeSerialDataItemQtySummaryStdoutFromResult(result, serialItemQtyShapeOpts)
                            : isSettleDetailsVariant
                                ? shapeSerialDataSettleDetailsStdoutFromResult(result)
                                : isDiscountDetailsVariant
                                    ? shapeSerialDataDiscountDetailsStdoutFromResult(result)
                                    : isFulloffDetailsVariant
                                        ? shapeSerialDataFulloffDetailsStdoutFromResult(result)
                                        : isPromoteDetailsVariant
                                            ? shapeSerialDataPromoteDetailsStdoutFromResult(result)
                                            : isItemMethodDetailsVariant
                                                ? shapeSerialDataItemMethodDetailsStdoutFromResult(result)
                                                : isPaywayIncomeSummaryVariant
                                                    ? shapeSerialDataPaywayIncomeSummaryStdout(extractBillListFromSerialDataResult(result), ctx.storeId, {
                                                        ...queryEcho,
                                                        pageNo: p,
                                                        include_all_settle_states: includeAllSettleStatesForPayway,
                                                    }, includeAllSettleStatesForPayway, null)
                                                    : isReversalSettlementSummaryVariant
                                                        ? shapeSerialDataReversalSettlementSummaryStdout(extractBillListFromSerialDataResult(result), ctx.storeId, { ...queryEcho, pageNo: p })
                                                        : applyOpenclawSerialStdoutShaping(isOpenclawVariant, outFmt, result);
                (0, output_1.formatOutput)(shapedErr, isSerialDataBillSummaryFormat(outFmt) ? 'json' : outFmt, serialFormatCmd);
                process.exit(1);
            }
            if (!isPlainObject(result)) {
                break;
            }
            const data = result.data;
            const chunk = extractBillListFromSerialDataResult(result);
            mergedBills.push(...chunk);
            const pi = readSerialDataPageInfo(data);
            pageTotalLimit = Math.max(pageTotalLimit, pi.pageTotal);
            if (chunk.length === 0 && p > 1) {
                break;
            }
        }
        const envelope = isPlainObject(lastResult) && lastResult !== null
            ? { ...lastResult }
            : { code: '0', msg: 'success', data: {} };
        const prevData = isPlainObject(envelope.data) ? envelope.data : {};
        envelope.data = {
            ...prevData,
            billList: mergedBills,
            pageInfo: {
                merged: true,
                pageNo: 1,
                pageSize: mergedBills.length,
                totalSize: mergedBills.length,
                pageTotal: 1,
                sourcePageTotal: pageTotalLimit,
                pagesFetched: Math.min(pageTotalLimit, maxSerialDataPages),
            },
        };
        if (isItemsVariant) {
            const itemMergedCount = flattenBillItemsFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-items --all-pages：已合并 ${mergedBills.length} 条 billList → ${itemMergedCount} 条品项（item）行`);
        }
        else if (isItemIncomeVariant) {
            const itemIncomeMergedCount = flattenBillItemsWithBillContextFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-item-income --all-pages：已合并 ${mergedBills.length} 条 billList → ${itemIncomeMergedCount} 条品项收入（item）行`);
        }
        else if (isItemQtySummaryVariant) {
            const itemMergedCount = flattenBillItemsFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-item-qty-summary --all-pages：已合并 ${mergedBills.length} 条 billList → ${itemMergedCount} 条品项（item）行用于汇总`);
        }
        else if (isSettleDetailsVariant) {
            const settleMergedCount = flattenSettleDetailsFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-settle-details --all-pages：已合并 ${mergedBills.length} 条 billList → ${settleMergedCount} 条结算明细（settleDetail）行`);
        }
        else if (isDiscountDetailsVariant) {
            const discountMergedCount = flattenDiscountDetailsFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-discount-details --all-pages：已合并 ${mergedBills.length} 条 billList → ${discountMergedCount} 条品项打折方案优惠明细（discountDetail）行`);
        }
        else if (isFulloffDetailsVariant) {
            const fulloffMergedCount = flattenFulloffDetailsFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-fulloff-details --all-pages：已合并 ${mergedBills.length} 条 billList → ${fulloffMergedCount} 条满减定额优惠明细（fulloffDetail）行`);
        }
        else if (isPromoteDetailsVariant) {
            const promoteMergedCount = flattenPromoteDetailsFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-promote-details --all-pages：已合并 ${mergedBills.length} 条 billList → ${promoteMergedCount} 条促销方案优惠明细（promoteDetail）行`);
        }
        else if (isItemMethodDetailsVariant) {
            const itemMethodMergedCount = flattenItemMethodDataFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-item-method-details --all-pages：已合并 ${mergedBills.length} 条 billList → ${itemMethodMergedCount} 条菜品做法明细（itemMethodData）行`);
        }
        else if (isPaywayIncomeSummaryVariant) {
            const paywayRows = flattenSettleDetailsWithSaleTypeFromSerialBills(mergedBills).length;
            console.error(`✓ serial-data-payway-income-summary --all-pages：已合并 ${mergedBills.length} 条 billList（${paywayRows} 条结算行用于汇总）`);
        }
        else if (isReversalSettlementSummaryVariant) {
            const revBills = filterBillsReversalSettlement(mergedBills);
            const revRows = flattenSettleDetailsWithSaleTypeFromSerialBills(revBills).length;
            console.error(`✓ serial-data-reversal-settlement-summary --all-pages：已合并 ${mergedBills.length} 条 billList（返位 ${revBills.length} 张，${revRows} 条结算行参与汇总）`);
        }
        else {
            console.error(`✓ serial-data --all-pages：已合并 ${mergedBills.length} 条 billList`);
        }
        if (isSerialDataBillSummaryFormat(outFmt)) {
            (0, output_1.formatOutput)(outFmt === 'checkout-anomaly-summary'
                ? buildCheckoutAnomalyWaiterSummary({
                    shopId: ctx.storeId,
                    bills: mergedBills,
                    queryEcho,
                })
                : buildAbnormalBillWaiterSummary({
                    shopId: ctx.storeId,
                    bills: mergedBills,
                    queryEcho,
                }), 'json', undefined);
        }
        else {
            const shaped = isItemsVariant
                ? shapeSerialDataItemsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit)
                : isItemIncomeVariant
                    ? shapeSerialDataItemIncomeStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit)
                    : isItemQtySummaryVariant
                        ? shapeSerialDataItemQtySummaryStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit, serialItemQtyShapeOpts)
                        : isSettleDetailsVariant
                            ? shapeSerialDataSettleDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit)
                            : isDiscountDetailsVariant
                                ? shapeSerialDataDiscountDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit)
                                : isFulloffDetailsVariant
                                    ? shapeSerialDataFulloffDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit)
                                    : isPromoteDetailsVariant
                                        ? shapeSerialDataPromoteDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit)
                                        : isItemMethodDetailsVariant
                                            ? shapeSerialDataItemMethodDetailsStdoutFromMergedEnvelope(envelope, mergedBills, pageTotalLimit)
                                            : isPaywayIncomeSummaryVariant
                                                ? shapeSerialDataPaywayIncomeSummaryStdout(mergedBills, ctx.storeId, { ...queryEcho, include_all_settle_states: includeAllSettleStatesForPayway }, includeAllSettleStatesForPayway, null)
                                                : isReversalSettlementSummaryVariant
                                                    ? shapeSerialDataReversalSettlementSummaryStdout(mergedBills, ctx.storeId, queryEcho)
                                                    : applyOpenclawSerialStdoutShaping(isOpenclawVariant, outFmt, envelope);
            (0, output_1.formatOutput)(shaped, outFmt, serialFormatCmd);
        }
        return true;
    }
    if (args[1] === 'stores-refresh' || args[1] === 'cache-stores-refresh') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        if (!appid || !accessid) {
            console.error(`✗ 缺少 appid 或 accessid（请在 .env 配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，或 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}）`);
            process.exit(1);
        }
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.centerId) {
            console.error(`✗ 缺少 centerId：请在 .env / token.json biz_params 配置 SL_CY7_GROUP_ID（或 --center-id / SL_CYSMS_CENTER_ID）`);
            process.exit(1);
        }
        (0, cysms_store_cache_1.clearCysmsStoreCache)();
        console.error('✓ 已清空当前工作区 cache/cysms-stores.json 与 cache/cysms-selected-stores.json');
        const token = await obtainCysmsAccessToken(true, appid, accessid, baseUrl);
        await syncCySStoresFromGetshopsPaged(baseUrl, appid, accessid, token, ctx);
        (0, output_1.formatOutput)({
            code: '0',
            msg: 'success',
            data: {
                refreshed: true,
                centerId: ctx.centerId,
                groupNo: ctx.groupNo || null,
                cacheFile: 'cache/cysms-stores.json',
                selectedCacheFile: 'cache/cysms-selected-stores.json',
            },
        }, (0, body_1.getFormat)(flags));
        return true;
    }
    if (args[1] === 'getshops') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const force = flags.force === 'true' || flags.force === '1';
        const baseUrl = (flags['base-url'] || (0, env_1.getEnv)('SL_CYSMS_BASE_URL', DEFAULT_CYSMS_BASE)).replace(/\/+$/, '');
        const appid = readCySAppIdForCommand(flags);
        const accessid = readCySAccessIdForCommand(flags);
        if (!appid || !accessid) {
            console.error(`✗ 缺少 appid 或 accessid（请在 .env 配置 SL_CYSMS_APP_ID / SL_CYSMS_ACCESS_ID，或 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}）`);
            process.exit(1);
        }
        const ctx = (0, cysms_context_1.resolveCysmsOrgContext)(flags);
        if (!ctx.centerId) {
            console.error(`✗ 缺少 centerId：请在 .env / token.json biz_params 配置 SL_CY7_GROUP_ID（或 --center-id / SL_CYSMS_CENTER_ID）`);
            process.exit(1);
        }
        const pageNo = String(flags['page-no'] || flags.pageno || '1').trim() || '1';
        let pageSize = String(flags['page-size'] || flags.pagesize || '50').trim() || '50';
        const pageSizeNum = Number(pageSize);
        if (Number.isFinite(pageSizeNum) && pageSizeNum > 50) {
            console.error('⚠ pageSize 文档约定最大 50，已改为 50');
            pageSize = '50';
        }
        const qs = new URLSearchParams({ centerId: ctx.centerId, pageNo, pageSize });
        if (ctx.groupNo) {
            qs.set('groupNo', ctx.groupNo);
        }
        (0, cysms_context_1.appendCysmsBizQueryParams)(qs, ctx);
        const tokenOverride = (flags['access-token'] || '').trim();
        let token = tokenOverride || (await obtainCysmsAccessToken(force, appid, accessid, baseUrl));
        if (!tokenOverride && readValidCySAccessTokenOrNull(force)) {
            console.error(`✓ 使用 token.json → ${TOKEN_JSON_CY_S}.${CY_S_AUTH}.access_token`);
        }
        else if (!tokenOverride) {
            console.error('✓ 已自动换取 access_token 并写入 token.json');
        }
        (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
        const storeNameFlag = (flags['store-name'] || flags.storename || '').trim();
        if (storeNameFlag && ctx.storeId) {
            console.error(`✓ 已将门店名称「${storeNameFlag}」解析为 storeId=${ctx.storeId}，并写入当前工作区 cache/cysms-selected-stores.json`);
        }
        const endpoint = {
            path: `${GETSHOPS_PATH}?${qs.toString()}`,
            method: 'POST',
        };
        const buildHeaders = (accessToken) => ({
            access_token: accessToken,
            accessid,
            granttype: 'client',
        });
        let result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
        if (!tokenOverride && isLikelyCysmsTokenRejected(result)) {
            console.error('⚠ getshops 返回疑似令牌失效，已强制 accesstoken 并写回 token.json，重试一次…');
            token = await obtainCysmsAccessToken(true, appid, accessid, baseUrl);
            result = await (0, request_1.makeRequest)(baseUrl, endpoint, null, {}, 'cysms', buildHeaders(token));
        }
        const status = readHttpStatus(result);
        if (status !== undefined && !isHttpSuccess(status)) {
            console.error(`✗ HTTP 状态异常: ${String(status)}`);
        }
        (0, output_1.formatOutput)(result, (0, body_1.getFormat)(flags));
        if (status !== undefined && !isHttpSuccess(status)) {
            process.exit(1);
        }
        const skipSync = flags['skip-sync'] === 'true' || flags['skip-sync'] === '1';
        if (!skipSync && isGetshopsBizSuccess(result)) {
            const stores = extractStoresArrayFromCysmsListResult(result);
            const org = {
                ...buildOrganizationSnapshot(result, { centerId: ctx.centerId, groupNo: ctx.groupNo }),
                ...(ctx.storeId ? { storeId: ctx.storeId } : {}),
                ...(ctx.brandId ? { brandId: ctx.brandId } : {}),
            };
            persistCySStoresAndOrganizationPartial(stores, org);
            if (ctx.storeId) {
                (0, cysms_context_1.persistCySOrganizationBizCache)(ctx);
            }
        }
        return true;
    }
    if (args[1] === '--help' || args[1] === '-h' || args[1] === undefined) {
        printCysmsUsage();
        return true;
    }
    console.error(`未知子命令: ${args[1]}`);
    printCysmsUsage();
    process.exit(1);
}
