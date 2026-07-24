"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setVerbose = setVerbose;
exports.isVerbose = isVerbose;
exports.debugLog = debugLog;
let verbose = false;
function setVerbose(nextVerbose) {
    verbose = nextVerbose;
}
function isVerbose() {
    return verbose;
}
function debugLog(label, data) {
    if (!verbose) {
        return;
    }
    console.error(`\n┌─── ${label} ───`);
    if (typeof data === 'string') {
        console.error(data);
    }
    else {
        console.error(JSON.stringify(data, null, 2));
    }
    console.error(`└${'─'.repeat(label.length + 6)}`);
}
