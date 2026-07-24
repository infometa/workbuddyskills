"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LOGIN_ENDPOINTS = exports.TOKEN_ENV_MAP = exports.GATEWAY_ROUTE_PREFIX = exports.TOKEN_CACHE_FILE = exports.COMMANDS_DIR = exports.GENERATED_DIR = void 0;
exports.resolveCliPolicyFile = resolveCliPolicyFile;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
/** ts-node 自 cli/src 起两层到仓根；tsc 产物在 dist/cli/src 需三层。 */
function resolveGeneratedCliDir() {
    const twoUp = path_1.default.resolve(__dirname, '../../generated/cli');
    const threeUp = path_1.default.resolve(__dirname, '../../../generated/cli');
    const tryDir = (d) => fs_1.default.existsSync(path_1.default.join(d, 'commands'));
    if (tryDir(threeUp))
        return threeUp;
    if (tryDir(twoUp))
        return twoUp;
    return twoUp;
}
exports.GENERATED_DIR = resolveGeneratedCliDir();
exports.COMMANDS_DIR = path_1.default.join(exports.GENERATED_DIR, 'commands');
exports.TOKEN_CACHE_FILE = path_1.default.join(process.env.SL_CLI_HOME || path_1.default.join(process.env.HOME || process.env.USERPROFILE || '.', '.slclaw'), 'token.json');
function resolveCliPolicyFile() {
    const configured = (process.env.SL_CLI_POLICY_FILE || '').trim();
    if (configured) {
        return path_1.default.resolve(process.cwd(), configured);
    }
    return path_1.default.resolve(process.cwd(), 'sl-cli-policy.json');
}
exports.GATEWAY_ROUTE_PREFIX = {
    cy7: 'ai2cyweb/fast',
    crm: 'ai2crmweb',
    scm: 'ai2fxweb',
    sly: 'ai2slyweb/newProxy',
    dc: 'ai2dcweb/lb',
    fx: 'ai2fxweb/bill',
    report: 'ai2rptweb',
};
exports.TOKEN_ENV_MAP = {
    cy7: 'SL_CY7_SESSION_TOKEN',
    crm: 'SL_CRM_SESSION_TOKEN',
    scm: 'SL_SCM_SESSION_TOKEN',
};
exports.LOGIN_ENDPOINTS = {
    crm: {
        login: '/crm7auth/login/kotler/login.do',
        envUsername: 'SL_CRM_USERNAME',
        envPassword: 'SL_CRM_PASSWORD',
        envBaseUrl: 'SL_CRM_API_BASE_URL',
        tokenField: 'sessionId',
    },
    cy7: {
        login: '/api/itembase/emp/emplogin',
        envUsername: 'SL_CY7_USERNAME',
        envPassword: 'SL_CY7_PASSWORD',
        envBaseUrl: 'SL_CY7_API_BASE_URL',
        tokenField: 'sessionId',
    },
    scm: {
        login: '/auth/v1/login/username',
        envUsername: 'SL_SCM_USERNAME',
        envPassword: 'SL_SCM_PASSWORD',
        envBaseUrl: 'SL_SCM_API_BASE_URL',
        tokenField: 'token',
    },
};
