"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CORE_COMMANDS = void 0;
exports.resolveCoreCommandId = resolveCoreCommandId;
exports.resolveCoreRoute = resolveCoreRoute;
exports.getCoreRegistration = getCoreRegistration;
function reg(id, argv, summary) {
    return { id, argv, summary };
}
const CYSMS_ACTIONS = [
    'accesstoken',
    'getshops',
    'store-region',
    'store-find',
    'cache-store-find',
    'store-use',
    'cache-store-use',
    'stores-refresh',
    'cache-stores-refresh',
    'business-situation',
    'business-situation-business-data',
    'business-situation-not-income',
    'business-situation-income',
    'business-situation-operate-data',
    'business-situation-other-data',
    'business-situation-shift-data',
    'business-situation-disc-rate',
    'business-situation-class-type-data',
    'business-situation-sale-type-data',
    'business-situation-meet-receivable-data',
    'service-area',
    'service-area-list',
    'service-area-point-list',
    'item-sellout-data',
    'book-order-detail',
    'serial-data',
    'serial-data-openclaw',
    'serial-data-items',
    'serial-data-item-income',
    'process-serial-data-item-income-json',
    'serial-data-item-qty-summary',
    'process-serial-data-item-qty-summary-json',
    'process-serial-data-abnormal-bill-summary-json',
    'serial-data-settle-details',
    'process-serial-data-settle-details-json',
    'serial-data-payway-income-summary',
    'process-serial-data-payway-income-summary-json',
    'serial-data-reversal-settlement-summary',
    'process-serial-data-reversal-settlement-summary-json',
    'serial-data-discount-details',
    'process-serial-data-discount-details-json',
    'serial-data-fulloff-details',
    'process-serial-data-fulloff-details-json',
    'serial-data-promote-details',
    'process-serial-data-promote-details-json',
    'serial-data-item-method-details',
    'process-serial-data-item-method-details-json',
    'process-serial-data-items-json',
    'o2o-ticket',
    'o2o-ticket-summary',
    'process-o2o-ticket-json',
    'process-o2o-ticket-summary-json',
];
exports.CORE_COMMANDS = [
    reg('token.refresh', ['token', 'refresh'], '刷新 Token'),
    reg('token.show', ['token', 'show'], '查看缓存的 Token'),
    reg('token.clear', ['token', 'clear'], '清除 Token 缓存'),
    reg('connector.auth', ['connector', 'auth'], 'WorkBuddy 连接器认证'),
    reg('connector.status', ['connector', 'status'], '连接器认证状态'),
    reg('connector.unauth', ['connector', 'unauth'], '清除连接器认证'),
    reg('connector.unauth', ['connector', 'logout'], '清除连接器认证'),
    reg('store.find', ['store', 'find'], '门店模糊查询'),
    reg('store.lookup', ['store', 'lookup'], '门店查询'),
    reg('crm-key', ['crm-key'], '获取 CRM RSA 公钥'),
    reg('showdoc.page', ['showdoc', 'page'], '拉取 ShowDoc 单页'),
    reg('starrocks.read-query', ['starrocks', 'read-query'], 'StarRocks 只读查询'),
    ...CYSMS_ACTIONS.map((action) => reg(`cysms.${action}`, ['cysms', action], `CY SMS: ${action}`)),
];
const byId = new Map();
for (const entry of exports.CORE_COMMANDS) {
    if (!byId.has(entry.id)) {
        byId.set(entry.id, entry);
    }
}
const sortedByArgvLength = [...exports.CORE_COMMANDS].sort((a, b) => b.argv.length - a.argv.length);
const coreFamilies = new Set(exports.CORE_COMMANDS.map((entry) => entry.argv[0]));
function resolveCoreCommandId(args) {
    for (const entry of sortedByArgvLength) {
        if (entry.argv.length > args.length) {
            continue;
        }
        const matches = entry.argv.every((part, index) => args[index] === part);
        if (matches) {
            return entry.id;
        }
    }
    return null;
}
function resolveCoreRoute(args) {
    const family = args[0];
    if (!coreFamilies.has(family)) {
        return { kind: 'not-core' };
    }
    const commandId = resolveCoreCommandId(args);
    const helpRequested = args.includes('--help') || args.includes('-h');
    if (args.length === 1 || helpRequested) {
        return commandId
            ? { kind: 'help', family, commandId }
            : { kind: 'help', family };
    }
    if (commandId) {
        return {
            kind: 'command',
            family,
            commandId,
        };
    }
    return { kind: 'unknown', family };
}
function getCoreRegistration(id) {
    return byId.get(id);
}
