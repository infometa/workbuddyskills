"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadTokenStore = loadTokenStore;
exports.loadTokenCache = loadTokenCache;
exports.saveTokenCache = saveTokenCache;
exports.clearTokenCache = clearTokenCache;
exports.saveTokenValue = saveTokenValue;
exports.loadTokenValue = loadTokenValue;
exports.cacheToken = cacheToken;
const fs_1 = __importDefault(require("fs"));
const constants_1 = require("./constants");
function isRecord(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function isTokenCacheEntry(value) {
    return isRecord(value)
        && typeof value.token === 'string'
        && typeof value.cached_at === 'string'
        && (typeof value.expires_at === 'number' || value.expires_at === null)
        && (value.userId === undefined || typeof value.userId === 'string')
        && (value.userName === undefined || typeof value.userName === 'string')
        && (value.accountId === undefined || typeof value.accountId === 'string');
}
function loadTokenStore() {
    try {
        if (fs_1.default.existsSync(constants_1.TOKEN_CACHE_FILE)) {
            const parsed = JSON.parse(fs_1.default.readFileSync(constants_1.TOKEN_CACHE_FILE, 'utf-8'));
            if (isRecord(parsed)) {
                return parsed;
            }
        }
    }
    catch {
        return {};
    }
    return {};
}
function isReadonly() {
    return process.env.SL_TOKEN_READONLY === '1';
}
function saveTokenStore(store) {
    if (isReadonly())
        return;
    fs_1.default.writeFileSync(constants_1.TOKEN_CACHE_FILE, JSON.stringify(store, null, 2), { encoding: 'utf-8', mode: 0o600 });
}
function loadTokenCache() {
    const store = loadTokenStore();
    const cache = {};
    for (const [key, value] of Object.entries(store)) {
        if (isTokenCacheEntry(value)) {
            cache[key] = value;
        }
    }
    return cache;
}
function saveTokenCache(cache) {
    const store = loadTokenStore();
    for (const [key, value] of Object.entries(cache)) {
        store[key] = value;
    }
    saveTokenStore(store);
}
function clearTokenCache() {
    if (fs_1.default.existsSync(constants_1.TOKEN_CACHE_FILE)) {
        fs_1.default.unlinkSync(constants_1.TOKEN_CACHE_FILE);
    }
}
function saveTokenValue(key, value) {
    const store = loadTokenStore();
    if (value === undefined) {
        delete store[key];
    }
    else {
        store[key] = value;
    }
    saveTokenStore(store);
}
function loadTokenValue(key) {
    return loadTokenStore()[key];
}
function cacheToken(product, token, ttlMs, extra = {}) {
    const cache = loadTokenCache();
    cache[product] = {
        token,
        cached_at: new Date().toISOString(),
        expires_at: ttlMs ? Date.now() + ttlMs : null,
        ...extra,
    };
    saveTokenCache(cache);
}
