"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isDomainFile = isDomainFile;
function isRecord(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function isParameter(value) {
    return isRecord(value) && typeof value.name === 'string';
}
function isEndpoint(value) {
    if (!isRecord(value) || typeof value.method !== 'string' || typeof value.path !== 'string') {
        return false;
    }
    const fmt = value.body_format;
    if (fmt !== undefined && fmt !== 'json' && fmt !== 'form') {
        return false;
    }
    return true;
}
function isEnvMapping(value) {
    return isRecord(value) && Object.values(value).every((item) => typeof item === 'string');
}
function isCommand(value) {
    return isRecord(value)
        && typeof value.command === 'string'
        && typeof value.domain === 'string'
        && typeof value.action === 'string'
        && isEndpoint(value.endpoint)
        && isEnvMapping(value.env_mapping)
        && (value.parameters === undefined || (Array.isArray(value.parameters) && value.parameters.every(isParameter)));
}
function isDomainFile(value) {
    return isRecord(value)
        && typeof value.domain === 'string'
        && typeof value.count === 'number'
        && Array.isArray(value.commands)
        && value.commands.every(isCommand);
}
