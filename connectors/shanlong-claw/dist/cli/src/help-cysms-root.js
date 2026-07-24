"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.formatCysmsAccesstokenRootLine = formatCysmsAccesstokenRootLine;
const commands_1 = require("./commands");
const CYSMS_ROOT_FALLBACK_AUTH = '  sl cysms accesstoken               CY 开放 API，写 cyS.auth；成功后默认分页 getshops 更新 cyS.stores（--skip-stores 可关）；其它子命令见 sl cysms --help';
function formatCysmsAccesstokenRootLine() {
    const data = (0, commands_1.loadCommands)('cysms');
    const cmd = data?.commands.find((c) => c.action === 'accesstoken');
    if (!cmd) {
        return CYSMS_ROOT_FALLBACK_AUTH;
    }
    const desc = (cmd.description || cmd.name || '').trim();
    return `  sl cysms accesstoken               ${desc}`;
}
