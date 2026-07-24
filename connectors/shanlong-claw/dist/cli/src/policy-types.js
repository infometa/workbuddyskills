"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BOOTSTRAP_POLICY = void 0;
exports.parseCliPolicy = parseCliPolicy;
exports.BOOTSTRAP_POLICY = {
    name: 'bootstrap',
    version: 1,
    help: { enabled: true },
    business: {
        enabled: false,
        allow: [],
    },
    core: {
        allow: [
            'connector.auth',
            'connector.status',
            'connector.unauth',
            'token.refresh',
            'crm-key',
        ],
    },
};
const SECURITY_LEVELS = new Set(['S1', 'S2', 'S3', 'S4']);
function assertRecord(value, path) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
        throw new Error(`${path} must be an object`);
    }
    return value;
}
function assertString(value, path) {
    if (typeof value !== 'string' || !value) {
        throw new Error(`${path} must be a non-empty string`);
    }
    return value;
}
function assertBoolean(value, path) {
    if (typeof value !== 'boolean') {
        throw new Error(`${path} must be a boolean`);
    }
    return value;
}
function assertStringArray(value, path) {
    if (!Array.isArray(value) || value.some((item) => typeof item !== 'string')) {
        throw new Error(`${path} must be a string array`);
    }
    return value;
}
function assertOnlyKeys(obj, allowed, path) {
    for (const key of Object.keys(obj)) {
        if (!allowed.includes(key)) {
            throw new Error(`${path}.${key} is not allowed`);
        }
    }
}
function parseHelp(value) {
    const obj = assertRecord(value, 'help');
    assertOnlyKeys(obj, ['enabled'], 'help');
    return { enabled: assertBoolean(obj.enabled, 'help.enabled') };
}
function parseBusiness(value) {
    const obj = assertRecord(value, 'business');
    assertOnlyKeys(obj, [
        'enabled',
        'maxSecurityLevel',
        'products',
        'domains',
        'categories',
        'perspectives',
        'allow',
        'deny',
    ], 'business');
    const enabled = assertBoolean(obj.enabled, 'business.enabled');
    let maxSecurityLevel;
    if (obj.maxSecurityLevel !== undefined) {
        const level = assertString(obj.maxSecurityLevel, 'business.maxSecurityLevel');
        if (!SECURITY_LEVELS.has(level)) {
            throw new Error('business.maxSecurityLevel must be S1, S2, S3, or S4');
        }
        maxSecurityLevel = level;
    }
    const products = obj.products === undefined ? undefined : assertStringArray(obj.products, 'business.products');
    const domains = obj.domains === undefined ? undefined : assertStringArray(obj.domains, 'business.domains');
    const categories = obj.categories === undefined ? undefined : assertStringArray(obj.categories, 'business.categories');
    const perspectives = obj.perspectives === undefined ? undefined : assertStringArray(obj.perspectives, 'business.perspectives');
    const allow = obj.allow === undefined ? [] : assertStringArray(obj.allow, 'business.allow');
    const deny = obj.deny === undefined ? undefined : assertStringArray(obj.deny, 'business.deny');
    return {
        enabled,
        maxSecurityLevel,
        products,
        domains,
        categories,
        perspectives,
        allow,
        deny,
    };
}
function parseCore(value) {
    const obj = assertRecord(value, 'core');
    assertOnlyKeys(obj, ['allow'], 'core');
    return { allow: assertStringArray(obj.allow, 'core.allow') };
}
function parseCliPolicy(value) {
    const obj = assertRecord(value, 'policy');
    assertOnlyKeys(obj, ['name', 'version', 'help', 'business', 'core'], 'policy');
    const name = assertString(obj.name, 'name');
    const version = obj.version;
    if (version !== 1) {
        throw new Error('version must be 1');
    }
    return {
        name,
        version: 1,
        help: parseHelp(obj.help),
        business: parseBusiness(obj.business),
        core: parseCore(obj.core),
    };
}
