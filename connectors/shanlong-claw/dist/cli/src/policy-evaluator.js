"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getBusinessCommandId = getBusinessCommandId;
exports.isBusinessCommandAllowed = isBusinessCommandAllowed;
exports.isCoreCommandAllowed = isCoreCommandAllowed;
exports.filterDomainFile = filterDomainFile;
exports.denyPolicyCommand = denyPolicyCommand;
const SECURITY_ORDER = { S1: 1, S2: 2, S3: 3, S4: 4 };
function getBusinessCommandId(command) {
    return `${command.domain}.${command.action}`;
}
function matchesCoarseFilter(values, actual) {
    if (!values || values.length === 0) {
        return true;
    }
    if (!actual) {
        return false;
    }
    return values.includes(actual);
}
function isWithinMaxSecurityLevel(command, maxLevel) {
    const cmdLevel = (command.security_level || 'S1');
    const cmdOrder = SECURITY_ORDER[cmdLevel] || 1;
    const maxOrder = SECURITY_ORDER[maxLevel] || 1;
    return cmdOrder <= maxOrder;
}
function isBusinessCommandAllowed(ctx, command) {
    const { policy, packageScope } = ctx;
    const business = policy.business;
    if (!business.enabled) {
        return false;
    }
    if (packageScope === 'S1-only' && command.security_level !== 'S1') {
        return false;
    }
    const commandId = getBusinessCommandId(command);
    if (!business.allow.includes(commandId)) {
        return false;
    }
    if (!matchesCoarseFilter(business.products, command.product)) {
        return false;
    }
    if (!matchesCoarseFilter(business.domains, command.domain)) {
        return false;
    }
    if (!matchesCoarseFilter(business.categories, command.category)) {
        return false;
    }
    if (!matchesCoarseFilter(business.perspectives, command.perspective)) {
        return false;
    }
    const maxLevel = business.maxSecurityLevel || 'S1';
    if (!isWithinMaxSecurityLevel(command, maxLevel)) {
        return false;
    }
    if (business.deny?.includes(commandId)) {
        return false;
    }
    return true;
}
function isCoreCommandAllowed(policy, commandId) {
    return policy.core.allow.includes(commandId);
}
function filterDomainFile(ctx, data) {
    const commands = data.commands.filter((command) => isBusinessCommandAllowed(ctx, command));
    return {
        ...data,
        commands,
        count: commands.length,
    };
}
function denyPolicyCommand(_commandId) {
    console.error('Command is not enabled by the active CLI policy.');
    process.exit(1);
}
