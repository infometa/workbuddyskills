"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.cysmsStoresCacheFile = cysmsStoresCacheFile;
exports.cysmsSelectedStoresCacheFile = cysmsSelectedStoresCacheFile;
exports.normalizeCysmsStore = normalizeCysmsStore;
exports.toLegacyCysmsStoreRow = toLegacyCysmsStoreRow;
exports.getCysmsStoresCacheStatus = getCysmsStoresCacheStatus;
exports.writeCysmsStoresCache = writeCysmsStoresCache;
exports.readCysmsStoresCache = readCysmsStoresCache;
exports.writeSelectedCysmsStores = writeSelectedCysmsStores;
exports.readSelectedCysmsStores = readSelectedCysmsStores;
exports.clearCysmsStoreCache = clearCysmsStoreCache;
exports.findCysmsStoresByQuery = findCysmsStoresByQuery;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const CACHE_DIR_NAME = 'cache';
const STORES_FILE_NAME = 'cysms-stores.json';
const SELECTED_STORES_FILE_NAME = 'cysms-selected-stores.json';
function cacheDir() {
    return path_1.default.join(process.cwd(), CACHE_DIR_NAME);
}
function cysmsStoresCacheFile() {
    return path_1.default.join(cacheDir(), STORES_FILE_NAME);
}
function cysmsSelectedStoresCacheFile() {
    return path_1.default.join(cacheDir(), SELECTED_STORES_FILE_NAME);
}
function ensureCacheDir() {
    fs_1.default.mkdirSync(cacheDir(), { recursive: true });
}
function isRecord(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function readString(row, keys) {
    for (const k of keys) {
        const v = row[k];
        if (typeof v === 'string' && v.trim()) {
            return v.trim();
        }
        if (typeof v === 'number' && Number.isFinite(v)) {
            return String(v);
        }
    }
    return '';
}
function readNestedRegionString(row, keys) {
    const direct = readString(row, keys);
    if (direct) {
        return direct;
    }
    const nested = row.region;
    if (isRecord(nested)) {
        return readString(nested, [...keys, 'id']);
    }
    return '';
}
function readLocationString(row, camelKey, snakeKey) {
    return readString(row, [camelKey, snakeKey]);
}
function normalizeCysmsStore(row) {
    if (!isRecord(row)) {
        return null;
    }
    const id = readString(row, ['id', 'shop_id', 'shopId', 'storeId']);
    const name = readString(row, ['name', 'shop_name', 'shopName', 'storeName']);
    if (!id || !name) {
        return null;
    }
    return {
        id,
        name,
        code: readString(row, ['code', 'shop_code', 'shopCode', 'shop_no', 'shopNo']),
        regionCode: readNestedRegionString(row, [
            'regionCode',
            'region_code',
            'region_id',
            'regionId',
            'area_id',
            'areaId',
            'district_id',
            'districtId',
            'adcode',
            'area_code',
        ]),
        regionName: readNestedRegionString(row, ['regionName', 'region_name']),
        provinceId: readLocationString(row, 'provinceId', 'province_id'),
        provinceName: readLocationString(row, 'provinceName', 'province_name'),
        cityId: readLocationString(row, 'cityId', 'city_id'),
        cityName: readLocationString(row, 'cityName', 'city_name'),
        countyId: readLocationString(row, 'countyId', 'county_id'),
        countyName: readLocationString(row, 'countyName', 'county_name'),
        address: readString(row, ['address', 'addr', 'detailAddress', 'shop_address', 'shopAddress']),
        gcX: readLocationString(row, 'gcX', 'gc_x'),
        gcY: readLocationString(row, 'gcY', 'gc_y'),
    };
}
function toLegacyCysmsStoreRow(store) {
    return {
        id: store.id,
        shop_id: store.id,
        shopId: store.id,
        name: store.name,
        shop_name: store.name,
        shopName: store.name,
        code: store.code,
        shop_code: store.code,
        shopCode: store.code,
        regionCode: store.regionCode,
        region_code: store.regionCode,
        region_id: store.regionCode,
        regionName: store.regionName,
        region_name: store.regionName,
        provinceId: store.provinceId,
        province_id: store.provinceId,
        provinceName: store.provinceName,
        province_name: store.provinceName,
        cityId: store.cityId,
        city_id: store.cityId,
        cityName: store.cityName,
        city_name: store.cityName,
        countyId: store.countyId,
        county_id: store.countyId,
        countyName: store.countyName,
        county_name: store.countyName,
        address: store.address,
        gcX: store.gcX,
        gc_x: store.gcX,
        gcY: store.gcY,
        gc_y: store.gcY,
    };
}
function normalizeStores(rows) {
    const out = [];
    const seen = new Set();
    for (const row of rows) {
        const s = normalizeCysmsStore(row);
        if (!s || seen.has(s.id)) {
            continue;
        }
        seen.add(s.id);
        out.push(s);
    }
    return out;
}
function mergeStores(existing, incoming) {
    const out = [...existing];
    const indexById = new Map();
    out.forEach((store, index) => indexById.set(store.id, index));
    for (const store of incoming) {
        const existingIndex = indexById.get(store.id);
        if (existingIndex === undefined) {
            indexById.set(store.id, out.length);
            out.push(store);
        }
        else {
            out[existingIndex] = store;
        }
    }
    return out;
}
function normalizeScopeValue(value) {
    if (typeof value === 'string') {
        return value.trim();
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
        return String(value);
    }
    return '';
}
function readCysmsStoresCacheFile() {
    try {
        const parsed = JSON.parse(fs_1.default.readFileSync(cysmsStoresCacheFile(), 'utf-8'));
        if (isRecord(parsed) && Array.isArray(parsed.stores)) {
            return {
                synced_at: readString(parsed, ['synced_at']) || new Date(0).toISOString(),
                source: 'cysms.getshops',
                centerId: normalizeScopeValue(parsed.centerId),
                groupNo: normalizeScopeValue(parsed.groupNo) || null,
                stores: normalizeStores(parsed.stores),
            };
        }
    }
    catch {
        return null;
    }
    return null;
}
function getCysmsStoresCacheStatus(scope) {
    const cached = readCysmsStoresCacheFile();
    const cachedCenterId = normalizeScopeValue(cached?.centerId);
    const cachedGroupNo = normalizeScopeValue(cached?.groupNo);
    const expectedCenterId = normalizeScopeValue(scope.centerId);
    const expectedGroupNo = normalizeScopeValue(scope.groupNo);
    const storeCount = cached?.stores.length || 0;
    return {
        hasStores: storeCount > 0,
        orgMatches: storeCount > 0 && cachedCenterId === expectedCenterId && cachedGroupNo === expectedGroupNo,
        cachedCenterId,
        cachedGroupNo,
        storeCount,
    };
}
function writeCysmsStoresCache(rows, scope) {
    const status = scope ? getCysmsStoresCacheStatus(scope) : null;
    if (status?.hasStores && !status.orgMatches) {
        clearCysmsStoreCache();
    }
    const stores = mergeStores(readCysmsStoresCache(), normalizeStores(rows));
    ensureCacheDir();
    const payload = {
        synced_at: new Date().toISOString(),
        source: 'cysms.getshops',
        ...(scope?.centerId ? { centerId: normalizeScopeValue(scope.centerId) } : {}),
        ...(scope ? { groupNo: normalizeScopeValue(scope.groupNo) || null } : {}),
        stores,
    };
    fs_1.default.writeFileSync(cysmsStoresCacheFile(), JSON.stringify(payload, null, 2), 'utf-8');
    return stores;
}
function readCysmsStoresCache() {
    return readCysmsStoresCacheFile()?.stores || [];
}
function writeSelectedCysmsStores(rows) {
    const stores = normalizeStores(rows);
    ensureCacheDir();
    const payload = {
        updated_at: new Date().toISOString(),
        stores,
    };
    fs_1.default.writeFileSync(cysmsSelectedStoresCacheFile(), JSON.stringify(payload, null, 2), 'utf-8');
    return stores;
}
function readSelectedCysmsStores() {
    try {
        const parsed = JSON.parse(fs_1.default.readFileSync(cysmsSelectedStoresCacheFile(), 'utf-8'));
        if (isRecord(parsed) && Array.isArray(parsed.stores)) {
            return normalizeStores(parsed.stores);
        }
    }
    catch {
        return [];
    }
    return [];
}
function clearCysmsStoreCache() {
    for (const file of [cysmsStoresCacheFile(), cysmsSelectedStoresCacheFile()]) {
        try {
            if (fs_1.default.existsSync(file)) {
                fs_1.default.unlinkSync(file);
            }
        }
        catch {
            // Cache cleanup is best-effort; auth refresh must not fail because of a stale local file.
        }
    }
}
function splitQuery(input) {
    return input
        .split(/[,\n，、]+/g)
        .map((s) => s.trim())
        .filter(Boolean);
}
function includesQuery(store, q) {
    const needle = q.toLowerCase();
    return [
        store.id,
        store.name,
        store.code,
        store.regionCode,
        store.regionName,
        store.provinceId,
        store.provinceName,
        store.cityId,
        store.cityName,
        store.countyId,
        store.countyName,
        store.address,
    ]
        .filter(Boolean)
        .some((v) => v.toLowerCase().includes(needle));
}
function findCysmsStoresByQuery(input) {
    const stores = readCysmsStoresCache();
    const queries = splitQuery(input);
    if (queries.length === 0) {
        return [];
    }
    const out = [];
    const seen = new Set();
    for (const q of queries) {
        for (const store of stores) {
            if (!seen.has(store.id) && includesQuery(store, q)) {
                seen.add(store.id);
                out.push(store);
            }
        }
    }
    return out;
}
