"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.executeShowdocCommand = executeShowdocCommand;
const body_1 = require("./body");
const env_1 = require("./env");
const flags_1 = require("./flags");
const output_1 = require("./output");
const DEFAULT_SHOWDOC_BASE = 'https://doc.wuuxiang.com';
function isPlainObject(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function printShowdocUsage() {
    console.log(`用法:
  sl showdoc page --page-id <id> [--base-url <url>] [--format json]

说明:
  调用 ShowDoc 开放接口 GET .../server/index.php?s=/api/page/info&page_id=...
  用于在终端查看接口文档页元数据（page_title、page_content 等）。

  示例（与网页 #/46/444 中的 444 一致）:
  sl showdoc page --page-id 444

环境变量:
  SL_SHOWDOC_BASE_URL   默认 ${DEFAULT_SHOWDOC_BASE}`);
}
async function executeShowdocCommand(args) {
    if (args[0] !== 'showdoc') {
        return false;
    }
    if (args[1] === 'page') {
        const flags = (0, flags_1.parseFlags)(args.slice(2));
        const pageId = (flags['page-id'] || flags.pageid || '').trim();
        if (!pageId) {
            console.error('✗ 请使用 --page-id <数字>，例如与 ShowDoc 链接 #/46/444 中的 444');
            process.exit(1);
        }
        const base = (flags['base-url'] || (0, env_1.getEnv)('SL_SHOWDOC_BASE_URL', DEFAULT_SHOWDOC_BASE)).replace(/\/+$/, '');
        const url = `${base}/server/index.php?s=/api/page/info&page_id=${encodeURIComponent(pageId)}`;
        const controller = new AbortController();
        const timeoutMs = Number(process.env.SL_SHOWDOC_TIMEOUT_MS || 20000);
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        let response;
        try {
            response = await fetch(url, {
                method: 'GET',
                headers: { Accept: 'application/json' },
                signal: controller.signal,
            });
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            console.error(`✗ ShowDoc 请求失败: ${message}`);
            process.exit(1);
        }
        finally {
            clearTimeout(timer);
        }
        const text = await response.text();
        let parsed;
        try {
            parsed = JSON.parse(text);
        }
        catch {
            console.error('✗ 响应非 JSON');
            console.error(text.slice(0, 500));
            process.exit(1);
        }
        if (!isPlainObject(parsed)) {
            (0, output_1.formatOutput)(parsed, (0, body_1.getFormat)(flags));
            return true;
        }
        const err = parsed.error_code;
        if (err !== undefined && err !== 0 && err !== '0') {
            console.error(`✗ ShowDoc error_code=${String(err)}`);
        }
        (0, output_1.formatOutput)(parsed, (0, body_1.getFormat)(flags));
        if (!response.ok) {
            process.exit(1);
        }
        return true;
    }
    if (args[1] === '--help' || args[1] === '-h' || args[1] === undefined) {
        printShowdocUsage();
        return true;
    }
    console.error(`未知子命令: ${args[1]}`);
    printShowdocUsage();
    process.exit(1);
}
