"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CY_S_STORE_REGION_FIELD_ORDER = void 0;
exports.readCySStoresFromToken = readCySStoresFromToken;
exports.extractCySStoreRegionFromRow = extractCySStoreRegionFromRow;
exports.findCySStoreByShopId = findCySStoreByShopId;
exports.resolveCySStoreRowFromFlags = resolveCySStoreRowFromFlags;
exports.findCySStoreByCustomerName = findCySStoreByCustomerName;
exports.resolveCysmsOrgContext = resolveCysmsOrgContext;
exports.persistCySOrganizationBizCache = persistCySOrganizationBizCache;
exports.appendCysmsBizQueryParams = appendCysmsBizQueryParams;
const env_1 = require("./env");
const cysms_store_cache_1 = require("./cysms-store-cache");
const token_cache_1 = require("./token-cache");
const TOKEN_JSON_CY_S = 'cyS';
const CY_S_ORGANIZATION = 'organization';
function isPlainObject(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function loadCySRoot() {
    const v = (0, token_cache_1.loadTokenValue)(TOKEN_JSON_CY_S);
    return isPlainObject(v) ? { ...v } : {};
}
function readOrganizationSlice() {
    const root = loadCySRoot();
    const org = root[CY_S_ORGANIZATION];
    return isPlainObject(org) ? { ...org } : {};
}
function firstFromCsv(csv) {
    const first = csv.split(',')[0]?.trim();
    return first || '';
}
/** 供 CY 开放 API 相关接口复用：读取当前工作区 cache/cysms-stores.json。 */
function readCySStoresFromToken() {
    return (0, cysms_store_cache_1.readCysmsStoresCache)().map(cysms_store_cache_1.toLegacyCysmsStoreRow);
}
function normalizeComparableName(s) {
    return s.trim().toLowerCase();
}
/**
 * 在当前工作区 cache/cysms-stores.json 中按客户提供的门店名称查找。
 * 优先完全匹配 shop_name（含大小写不敏感），否则唯一一条包含匹配。
 */
/**
 * 与 sl-store-external-env-analysis 技能一致：门店档案上「区域类」字段的尝试顺序（首个非空作为 primary）。
 */
exports.CY_S_STORE_REGION_FIELD_ORDER = [
    'region_id',
    'regionId',
    'area_id',
    'areaId',
    'district_id',
    'districtId',
    'adcode',
    'area_code',
    'region_code',
];
function normalizeRegionScalar(value) {
    if (value === null || value === undefined) {
        return null;
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
        return String(value);
    }
    if (typeof value === 'string' && value.trim()) {
        return value.trim();
    }
    return null;
}
function readStoreField(row, key) {
    return normalizeRegionScalar(row[key]);
}
/**
 * 从单行门店档案提取区域编码与定位辅助信息（纯函数，不读盘）。
 */
function extractCySStoreRegionFromRow(row) {
    const nestedRaw = row.region;
    const nested = isPlainObject(nestedRaw) ? nestedRaw : null;
    const region_fields = {};
    const tryKey = (physicalKey) => {
        const top = readStoreField(row, physicalKey);
        if (top !== null) {
            region_fields[physicalKey] = top;
            return top;
        }
        if (nested) {
            const inner = readStoreField(nested, physicalKey);
            if (inner !== null) {
                region_fields[`region.${physicalKey}`] = inner;
                return inner;
            }
        }
        return null;
    };
    let primary = null;
    for (const k of exports.CY_S_STORE_REGION_FIELD_ORDER) {
        const v = tryKey(k);
        if (v !== null && !primary) {
            primary = {
                field: readStoreField(row, k) !== null ? k : `region.${k}`,
                value: v,
            };
        }
    }
    if (!primary && nested) {
        const idOnly = normalizeRegionScalar(nested.id);
        if (idOnly !== null) {
            region_fields['region.id'] = idOnly;
            primary = { field: 'region.id', value: idOnly };
        }
    }
    const locPick = (k) => {
        const v = readStoreField(row, k);
        return v ?? undefined;
    };
    const location_hint = {
        ...(locPick('province_name') ? { province_name: locPick('province_name') } : {}),
        ...(locPick('city_name') ? { city_name: locPick('city_name') } : {}),
        ...(locPick('county_name') ? { county_name: locPick('county_name') } : {}),
        ...(locPick('address') ? { address: locPick('address') } : {}),
        ...(locPick('province_id') ? { province_id: locPick('province_id') } : {}),
        ...(locPick('city_id') ? { city_id: locPick('city_id') } : {}),
        ...(locPick('county_id') ? { county_id: locPick('county_id') } : {}),
        ...(locPick('gc_x') ? { gc_x: locPick('gc_x') } : {}),
        ...(locPick('gc_y') ? { gc_y: locPick('gc_y') } : {}),
    };
    return { primary, region_fields, location_hint };
}
/** 在当前工作区 cache/cysms-stores.json 中按 shop_id / shopId 精确匹配一行 */
function findCySStoreByShopId(rawId) {
    const want = rawId.trim();
    if (!want) {
        return { ok: false, reason: 'not_found' };
    }
    const matches = [];
    for (const item of readCySStoresFromToken()) {
        if (!isPlainObject(item)) {
            continue;
        }
        const row = item;
        const id = row.shop_id ?? row.shopId;
        const sid = id != null && String(id).trim() ? String(id).trim() : '';
        if (sid === want) {
            matches.push(row);
        }
    }
    if (matches.length === 0) {
        return { ok: false, reason: 'not_found' };
    }
    if (matches.length > 1) {
        return {
            ok: false,
            reason: 'ambiguous',
            candidates: matches.map((r) => String(r.shop_name ?? want)).filter(Boolean),
        };
    }
    const row = matches[0];
    return { ok: true, row, shopId: want };
}
/**
 * 按 flag / 环境 / 当前工作区 selected cache 锁定一行门店档案（不发起网络请求）。
 * --store-name → 名称解析；否则 --store-id → cache/cysms-selected-stores.json → SL_CY7_STORE_* → 按 shop_id 匹配。
 */
function resolveCySStoreRowFromFlags(flags) {
    const storeNameInput = (flags['store-name'] || flags.storename || '').trim();
    if (storeNameInput) {
        return findCySStoreByCustomerName(storeNameInput);
    }
    let storeId = (flags['store-id'] || flags.storeid || '').trim();
    if (!storeId) {
        const selectedStore = (0, cysms_store_cache_1.readSelectedCysmsStores)()[0];
        storeId = String(selectedStore?.id ?? '').trim();
    }
    if (!storeId) {
        storeId = (0, env_1.getEnv)('SL_CY7_STORE_ID').trim();
    }
    if (!storeId) {
        storeId = firstFromCsv((0, env_1.getEnv)('SL_CY7_STORE_IDS').trim());
    }
    if (!storeId) {
        return { ok: false, reason: 'not_found' };
    }
    return findCySStoreByShopId(storeId);
}
function findCySStoreByCustomerName(rawName) {
    const name = rawName.trim();
    if (!name) {
        return { ok: false, reason: 'not_found' };
    }
    const stores = readCySStoresFromToken();
    const lower = normalizeComparableName(name);
    const exactMatches = [];
    const substringUnique = [];
    for (const item of stores) {
        if (!isPlainObject(item)) {
            continue;
        }
        const row = item;
        const shopName = row.shop_name ?? row.name;
        const n = typeof shopName === 'string' ? shopName.trim() : '';
        const code = String(row.shop_code ?? row.shopCode ?? row.code ?? '').trim();
        if (!n && !code) {
            continue;
        }
        if (n === name || normalizeComparableName(n) === lower || code === name || normalizeComparableName(code) === lower) {
            exactMatches.push(row);
        }
        else if (normalizeComparableName(n).includes(lower) || normalizeComparableName(code).includes(lower)) {
            substringUnique.push(row);
        }
    }
    const pickExact = () => {
        if (exactMatches.length === 0) {
            return { ok: false, reason: 'not_found' };
        }
        if (exactMatches.length > 1) {
            return {
                ok: false,
                reason: 'ambiguous',
                candidates: exactMatches.map((r) => String(r.shop_name ?? '')).filter(Boolean),
            };
        }
        const row = exactMatches[0];
        const id = row.shop_id ?? row.shopId;
        const shopId = id != null && String(id).trim() ? String(id).trim() : '';
        if (!shopId) {
            return { ok: false, reason: 'not_found' };
        }
        return { ok: true, row, shopId };
    };
    const exact = pickExact();
    if (exact.ok || exact.reason === 'ambiguous') {
        return exact;
    }
    if (substringUnique.length === 0) {
        return { ok: false, reason: 'not_found' };
    }
    if (substringUnique.length > 1) {
        return {
            ok: false,
            reason: 'ambiguous',
            candidates: substringUnique.map((r) => String(r.shop_name ?? '')).filter(Boolean),
        };
    }
    const row = substringUnique[0];
    const id = row.shop_id ?? row.shopId;
    const shopId = id != null && String(id).trim() ? String(id).trim() : '';
    if (!shopId) {
        return { ok: false, reason: 'not_found' };
    }
    return { ok: true, row, shopId };
}
/**
 * 解析 CY 开放 API 相关接口共用的「集团 centerId + 商龙云 groupNo + 门店 storeId + 品牌 brandId」。
 * - centerId：--center-id → cyS.organization.centerId → SL_CYSMS_CENTER_ID → SL_CY7_GROUP_ID
 * - groupNo：--group-no → cyS.organization.groupNo → SL_CYSMS_GROUP_NO → SL_UNIFIED_G_ID（可用 --omit-group-no 强制不传 groupNo）
 * - storeId：--store-id →（未传门店名/店 id 时）cache/cysms-selected-stores.json → SL_CY7_STORE_ID → SL_CY7_STORE_IDS 首项
 * - --store-name：在 cache/cysms-stores.json 中解析门店 id
 * - brandId：--brand-id →（未显式指定门店时）cyS.organization.brandId → SL_CY7_BRAND_ID →（显式指定门店后）再尝试 organization
 */
function resolveCysmsOrgContext(flags) {
    const org = readOrganizationSlice();
    const selectedStore = (0, cysms_store_cache_1.readSelectedCysmsStores)()[0];
    const centerFlag = (flags['center-id'] || flags.centerid || '').trim();
    const centerId = (centerFlag ||
        String(org.centerId ?? '').trim() ||
        (0, env_1.getEnv)('SL_CYSMS_CENTER_ID').trim() ||
        (0, env_1.getEnv)('SL_CY7_GROUP_ID').trim()).trim();
    const omitGroupNo = flags['omit-group-no'] === 'true' ||
        flags['omit-group-no'] === '1' ||
        flags.omitgroupno === 'true' ||
        flags.omitgroupno === '1';
    const groupFlag = (flags['group-no'] || flags.groupno || '').trim();
    const groupNo = omitGroupNo
        ? ''
        : (groupFlag ||
            String(org.groupNo ?? '').trim() ||
            (0, env_1.getEnv)('SL_CYSMS_GROUP_NO').trim() ||
            (0, env_1.getEnv)('SL_UNIFIED_G_ID').trim()).trim();
    const storeNameInput = (flags['store-name'] || flags.storename || '').trim();
    const explicitStoreId = (flags['store-id'] || flags.storeid || '').trim();
    const explicitStorePin = Boolean(explicitStoreId || storeNameInput);
    let storeId = explicitStoreId;
    if (!storeId && !storeNameInput) {
        storeId = String(selectedStore?.id ?? '').trim();
    }
    if (!storeId) {
        storeId = (0, env_1.getEnv)('SL_CY7_STORE_ID').trim();
    }
    if (!storeId) {
        storeId = firstFromCsv((0, env_1.getEnv)('SL_CY7_STORE_IDS').trim());
    }
    let brandId = (flags['brand-id'] || flags.brandid || '').trim();
    if (!brandId) {
        if (!explicitStorePin) {
            brandId = String(org.brandId ?? '').trim();
        }
        if (!brandId) {
            brandId = (0, env_1.getEnv)('SL_CY7_BRAND_ID').trim();
        }
        if (!brandId && explicitStorePin) {
            brandId = String(org.brandId ?? '').trim();
        }
    }
    let storeName;
    if (storeNameInput) {
        const found = findCySStoreByCustomerName(storeNameInput);
        if (found.ok === false && found.reason === 'ambiguous') {
            console.error(`✗ 门店名称「${storeNameInput}」匹配到多条，请改用更准确名称或 --store-id。候选: ${found.candidates.join(' | ')}`);
            process.exit(1);
        }
        if (found.ok === false) {
            console.error(`✗ 未在当前工作区 cache/cysms-stores.json 中找到门店「${storeNameInput}」。请先执行 sl cysms getshops 拉全量门店（勿加 --skip-sync），或改用 --store-id。`);
            process.exit(1);
        }
        storeId = found.shopId;
        const bid = found.row.brand_id ?? found.row.brandId;
        if (!brandId && bid != null && String(bid).trim()) {
            brandId = String(bid).trim();
        }
        const sn = found.row.shop_name;
        storeName = typeof sn === 'string' && sn.trim() ? sn.trim() : storeNameInput;
    }
    else if (storeId) {
        const fr = findCySStoreByShopId(storeId);
        if (fr.ok) {
            const sn = fr.row.shop_name;
            if (typeof sn === 'string' && sn.trim()) {
                storeName = sn.trim();
            }
        }
    }
    const base = { centerId, groupNo, storeId, brandId };
    return storeName ? { ...base, storeName } : base;
}
/** 将当前解析结果写入当前工作区 cache/cysms-selected-stores.json。 */
function persistCySOrganizationBizCache(ctx) {
    if (ctx.storeId) {
        const fr = findCySStoreByShopId(ctx.storeId);
        if (fr.ok) {
            (0, cysms_store_cache_1.writeSelectedCysmsStores)([fr.row]);
        }
    }
}
/** 为 datatransfer 类 POST 追加门店、品牌查询参数（有值才写入） */
function appendCysmsBizQueryParams(qs, ctx) {
    if (ctx.storeId) {
        qs.set('storeId', ctx.storeId);
        qs.set('shopId', ctx.storeId);
    }
    if (ctx.brandId) {
        qs.set('brandId', ctx.brandId);
    }
}
