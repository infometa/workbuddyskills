"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getRequestTimeoutMs = getRequestTimeoutMs;
exports.fetchWithTimeout = fetchWithTimeout;
const env_1 = require("../env");
function getRequestTimeoutMs(envKey = 'SL_REQUEST_TIMEOUT_MS', fallbackMs = 30000) {
    const raw = (0, env_1.getEnv)(envKey);
    if (!raw) {
        return fallbackMs;
    }
    const value = Number(raw);
    return Number.isFinite(value) && value > 0 ? value : fallbackMs;
}
function isAbortError(error) {
    return error instanceof Error && error.name === 'AbortError';
}
async function fetchWithTimeout(url, init, label, timeoutMs = getRequestTimeoutMs()) {
    const controller = new AbortController();
    let timer = null;
    const timeoutError = new Error(`${label} 请求超时（${timeoutMs}ms）: ${url}`);
    const timeoutPromise = new Promise((_, reject) => {
        timer = setTimeout(() => {
            controller.abort();
            reject(timeoutError);
        }, timeoutMs);
    });
    const fetchPromise = fetch(url, {
        ...init,
        signal: controller.signal,
    }).catch((error) => {
        if (isAbortError(error)) {
            throw timeoutError;
        }
        throw error;
    });
    try {
        return await Promise.race([fetchPromise, timeoutPromise]);
    }
    finally {
        if (timer) {
            clearTimeout(timer);
        }
    }
}
