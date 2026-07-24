"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CY7_OMSHOP_STORE_MAP_FILE = void 0;
exports.readCy7OmshopStoreMap = readCy7OmshopStoreMap;
exports.normalizeCy7StoreKeyword = normalizeCy7StoreKeyword;
exports.findCy7OmshopStoresByKeyword = findCy7OmshopStoresByKeyword;
exports.matchCy7OmshopStore = matchCy7OmshopStore;
exports.resolveCy7OmshopStoreCode = resolveCy7OmshopStoreCode;
exports.parseSqlQuotedOmShopCodes = parseSqlQuotedOmShopCodes;
exports.formatOmShopCodesForSql = formatOmShopCodesForSql;
exports.resolveCy7OmshopStoreCodes = resolveCy7OmshopStoreCodes;
exports.resolveCy7OmshopStoreCodeForSql = resolveCy7OmshopStoreCodeForSql;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
exports.CY7_OMSHOP_STORE_MAP_FILE = path_1.default.join('cache', 'cy7-omshop-store-map.json');
function isPlainObject(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function readString(value) {
    if (typeof value === 'string') {
        return value.trim();
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
        return String(value);
    }
    return '';
}
function readCy7OmshopStoreMap() {
    const file = path_1.default.resolve(process.cwd(), exports.CY7_OMSHOP_STORE_MAP_FILE);
    let parsed;
    try {
        parsed = JSON.parse(fs_1.default.readFileSync(file, 'utf-8'));
    }
    catch {
        return { omShopCodes: '', stores: [] };
    }
    if (!isPlainObject(parsed)) {
        return { omShopCodes: '', stores: [] };
    }
    const stores = Array.isArray(parsed.stores)
        ? parsed.stores
            .filter(isPlainObject)
            .map((row) => ({
            omShopCode: readString(row.omShopCode),
            orgName: readString(row.orgName),
        }))
            .filter((row) => row.omShopCode && row.orgName)
        : [];
    const omShopCodes = readString(parsed.omShopCodes) || stores.map((store) => `'${store.omShopCode}'`).join(',');
    return { omShopCodes, stores };
}
function normalizeCy7StoreKeyword(value) {
    return value.trim().toLowerCase();
}
function findCy7OmshopStoresByKeyword(input) {
    const raw = input.trim();
    const { stores } = readCy7OmshopStoreMap();
    if (!raw || raw.toLowerCase() === 'null') {
        return stores;
    }
    const normalized = normalizeCy7StoreKeyword(raw);
    return stores.filter((store) => normalizeCy7StoreKeyword(store.omShopCode).includes(normalized) ||
        normalizeCy7StoreKeyword(store.orgName).includes(normalized));
}
function matchCy7OmshopStore(input) {
    const raw = input.trim();
    if (!raw) {
        return { ok: false, reason: 'not_found' };
    }
    const { stores } = readCy7OmshopStoreMap();
    if (stores.length === 0) {
        return { ok: false, reason: 'not_found' };
    }
    const normalized = normalizeCy7StoreKeyword(raw);
    const exactMatches = stores.filter((store) => store.omShopCode === raw ||
        normalizeCy7StoreKeyword(store.omShopCode) === normalized ||
        store.orgName === raw ||
        normalizeCy7StoreKeyword(store.orgName) === normalized);
    const matches = exactMatches.length > 0 ? exactMatches : findCy7OmshopStoresByKeyword(raw);
    if (matches.length === 0) {
        return { ok: false, reason: 'not_found' };
    }
    if (matches.length > 1) {
        return { ok: false, reason: 'ambiguous', candidates: matches };
    }
    return { ok: true, store: matches[0], omShopCode: matches[0].omShopCode };
}
function resolveSingleCy7OmshopStoreCode(input) {
    const raw = input.trim();
    if (!raw) {
        return raw;
    }
    const { stores } = readCy7OmshopStoreMap();
    if (stores.length === 0) {
        return raw;
    }
    const match = matchCy7OmshopStore(raw);
    if (!match.ok) {
        if (match.reason === 'ambiguous') {
            throw new Error(`门店「${raw}」匹配到多条门店，请改用更准确名称或门店编码。候选: ${(match.candidates || []).map((store) => store.orgName).join(' | ')}`);
        }
        throw new Error(`未在 ${exports.CY7_OMSHOP_STORE_MAP_FILE} 中找到门店「${raw}」，请改用更准确名称或门店编码。`);
    }
    return match.omShopCode;
}
/** 解析单个门店编码或名称，返回 omShopCode（不含 SQL 引号）。 */
function resolveCy7OmshopStoreCode(input) {
    const raw = input.trim();
    if (!raw) {
        return raw;
    }
    if (raw.includes(',')) {
        throw new Error(`门店参数「${raw}」包含多个值，请改用逗号分隔的多门店入参，或使用 resolveCy7OmshopStoreCodeForSql。`);
    }
    if (raw.includes("'")) {
        const quoted = parseSqlQuotedOmShopCodes(raw);
        if (quoted?.length === 1) {
            return quoted[0];
        }
        throw new Error(`门店参数「${raw}」格式无效，请传入单个门店编码/名称，或使用 SQL IN 格式如 '198728','198729'。`);
    }
    return resolveSingleCy7OmshopStoreCode(raw);
}
/** 从 SQL IN 片段（'code1','code2'）或逗号分隔文本中提取 omShopCode 列表。 */
function parseSqlQuotedOmShopCodes(input) {
    const trimmed = input.trim();
    if (!trimmed.includes("'")) {
        return null;
    }
    const matches = trimmed.match(/'([^']*)'/g);
    if (!matches || matches.length === 0) {
        return null;
    }
    return matches.map((item) => item.slice(1, -1));
}
/** 将 omShopCode 列表格式化为 DataCube SQL IN 子句可用的 'code1','code2' 字符串。 */
function formatOmShopCodesForSql(codes) {
    const unique = [...new Set(codes.map((code) => code.trim()).filter(Boolean))];
    if (unique.length === 0) {
        return '';
    }
    return unique.map((code) => `'${code.replace(/'/g, "''")}'`).join(',');
}
/** 解析单个或多个门店（编码/名称/逗号分隔/SQL IN 格式），返回 omShopCode 数组。 */
function resolveCy7OmshopStoreCodes(input) {
    const raw = input.trim();
    if (!raw) {
        return [];
    }
    const preQuoted = parseSqlQuotedOmShopCodes(raw);
    if (preQuoted) {
        return preQuoted;
    }
    const parts = raw.split(',').map((part) => part.trim()).filter(Boolean);
    return parts.map((part) => resolveSingleCy7OmshopStoreCode(part));
}
/** 解析门店参数并格式化为 DataCube SQL IN 子句：'code1','code2'。 */
function resolveCy7OmshopStoreCodeForSql(input) {
    return formatOmShopCodesForSql(resolveCy7OmshopStoreCodes(input));
}
