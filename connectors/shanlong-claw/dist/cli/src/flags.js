"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseFlags = parseFlags;
const logger_1 = require("./logger");
function splitEqualsArg(raw, prefix) {
    const stripped = raw.slice(prefix.length);
    const eqIndex = stripped.indexOf('=');
    if (eqIndex > 0) {
        return { key: stripped.slice(0, eqIndex), value: stripped.slice(eqIndex + 1) };
    }
    return { key: stripped, value: null };
}
function parseFlags(args) {
    const flags = {};
    let index = 0;
    while (index < args.length) {
        const arg = args[index];
        if (arg === '--verbose' || arg === '-v') {
            (0, logger_1.setVerbose)(true);
            index += 1;
            continue;
        }
        if (arg.startsWith('--')) {
            const { key, value } = splitEqualsArg(arg, '--');
            if (value !== null) {
                flags[key] = value;
                index += 1;
            }
            else {
                const next = args[index + 1];
                const hasValue = next !== undefined && !next.startsWith('--');
                flags[key] = hasValue ? next : 'true';
                index += hasValue ? 2 : 1;
            }
            continue;
        }
        if (arg.startsWith('-')) {
            const { key, value } = splitEqualsArg(arg, '-');
            if (value !== null) {
                flags[key] = value;
                index += 1;
            }
            else {
                const next = args[index + 1];
                const hasValue = next !== undefined && !next.startsWith('-');
                flags[key] = hasValue ? next : 'true';
                index += hasValue ? 2 : 1;
            }
            continue;
        }
        index += 1;
    }
    return flags;
}
