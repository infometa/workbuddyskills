"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadCommands = loadCommands;
exports.isDomainFileForDomain = isDomainFileForDomain;
exports.mergeCommands = mergeCommands;
exports.loadCommandsMerged = loadCommandsMerged;
exports.getAllDomains = getAllDomains;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const constants_1 = require("./constants");
const types_1 = require("./types");
function loadCommands(domain) {
    const file = path_1.default.join(constants_1.COMMANDS_DIR, `${domain}.json`);
    if (!fs_1.default.existsSync(file)) {
        return null;
    }
    const parsed = JSON.parse(fs_1.default.readFileSync(file, 'utf-8'));
    return isDomainFileForDomain(parsed, domain) ? parsed : null;
}
function isDomainFileForDomain(value, domain) {
    return (0, types_1.isDomainFile)(value)
        && value.domain === domain
        && value.commands.every((command) => command.domain === domain);
}
function remoteCommandsUrl(domain) {
    const base = (process.env.SL_REMOTE_COMMANDS_URL || process.env.SL_COMMANDS_REMOTE_URL || '').trim();
    if (!base) {
        return '';
    }
    const cleanBase = base.replace(/\/+$/, '');
    if (cleanBase.includes('{domain}')) {
        return cleanBase.replace(/\{domain\}/g, encodeURIComponent(domain));
    }
    return `${cleanBase}/api/cli/commands/${encodeURIComponent(domain)}`;
}
function mergeCommandPreservingSecurity(local, remote) {
    const merged = { ...local };
    const displayFields = [
        'name',
        'description',
        'parameters',
        'output_filter',
        'response_filter',
        'output_transform',
        'source_file',
        'source_function',
    ];
    for (const field of displayFields) {
        if (remote[field] !== undefined) {
            Object.assign(merged, { [field]: remote[field] });
        }
    }
    return merged;
}
function mergeCommands(local, remote, domain) {
    local = isDomainFileForDomain(local, domain) ? local : null;
    remote = isDomainFileForDomain(remote, domain) ? remote : null;
    if (!local && !remote) {
        return null;
    }
    const merged = {
        domain: local?.domain || remote?.domain || domain,
        count: 0,
        commands: [],
    };
    const indexByAction = new Map();
    for (const source of [local, remote]) {
        for (const command of source?.commands || []) {
            const action = command.action;
            const existingIndex = indexByAction.get(action);
            if (existingIndex === undefined) {
                indexByAction.set(action, merged.commands.length);
                merged.commands.push(command);
            }
            else {
                const localCommand = local?.commands.find((item) => item.action === action);
                if (localCommand) {
                    merged.commands[existingIndex] = mergeCommandPreservingSecurity(localCommand, command);
                }
                else {
                    merged.commands[existingIndex] = command;
                }
            }
        }
    }
    merged.count = merged.commands.length;
    return merged;
}
async function loadCommandsMerged(domain) {
    const local = loadCommands(domain);
    const url = remoteCommandsUrl(domain);
    if (!url) {
        return local;
    }
    let timer = null;
    try {
        const controller = new AbortController();
        const timeoutMs = Number(process.env.SL_REMOTE_COMMANDS_TIMEOUT_MS || 1500);
        timer = setTimeout(() => controller.abort(), timeoutMs);
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) {
            return local;
        }
        const parsed = await response.json();
        const candidate = parsed && typeof parsed === 'object' && 'commands' in parsed
            ? parsed
            : null;
        const remote = isDomainFileForDomain(candidate, domain) ? candidate : null;
        return mergeCommands(local, remote, domain);
    }
    catch {
        return local;
    }
    finally {
        if (timer) {
            clearTimeout(timer);
        }
    }
}
function getAllDomains() {
    return fs_1.default.readdirSync(constants_1.COMMANDS_DIR)
        .filter((file) => file.endsWith('.json'))
        .map((file) => file.replace('.json', ''))
        .sort();
}
