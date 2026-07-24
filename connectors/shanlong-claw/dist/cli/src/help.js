"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.printHelp = printHelp;
exports.printDomains = printDomains;
exports.printDomainHelp = printDomainHelp;
exports.printCommandHelp = printCommandHelp;
const commands_1 = require("./commands");
const help_cysms_root_1 = require("./help-cysms-root");
const env_1 = require("./env");
function printHelp() {
    console.log(`
╔══════════════════════════════════════════╗
║  sl — 商龙餐饮 SaaS CLI                  ║
╚══════════════════════════════════════════╝

用法:
  sl <域> <命令> [参数]

示例:
  sl domains                     列出所有域
  sl --version                   查看 CLI 版本
  sl item --help                 查看菜品域所有命令
  sl item get-item-page-list     查询菜品列表
  sl coupon page-list            查询优惠券列表
  sl token refresh               刷新所有 Token
  sl token refresh-crm-gc-id     按当前 CRM Group 刷新 GC ID
  sl store find --type crm --name 门店  模糊查询 omShopCode

认证 & Token:
  Token 自动获取: API Key 换票 或 SLY 登录 → switchToken → 产品 Token (缓存在 token.json)
  sl token refresh [cy7|crm|scm|dc|all] 刷新 Token（优先 API Key，失败回退 SLY）
  sl token refresh-crm-gc-id [--group-id <集团号>]  按最终 SL_CRM_GROUP_ID 刷新并写入 SL_CRM_GC_ID
  sl token show                      查看缓存的 Token
  sl token clear                     清除 Token 缓存
  sl store find --type crm|cy7 --name <关键词>  从 token.json 门店清单模糊查 omShopCode
  sl crm-key                         获取 CRM RSA 公钥 (loginKey + init 双源)
${(0, help_cysms_root_1.formatCysmsAccesstokenRootLine)()}

WorkBuddy 连接器:
  sl connector auth                  读取 WorkBuddy 注入的 SL_API_KEY，写入 .env 并换票
  sl connector status                检查认证状态
  sl connector unauth                清除 token.json，并清空 .env 中的 SL_API_KEY
  认证后业务命令自动限制为 S1 安全级别

文档工具:
  sl showdoc page --page-id 444      拉取 ShowDoc 单页 JSON（对照网页文档）

调试:
  sl item big-class --verbose    打印完整请求/响应 headers 和 body
  sl item big-class --help       查看该命令的参数定义和用法

参数:
  --version, -v                  输出当前 CLI 版本
  --format json|table|csv        输出格式 (默认 json)
  --verbose                      打印完整请求/响应 headers 和 body
  --envPath <路径>                额外读取指定 .env 文件或目录中的 .env
  --params '{json}'              追加合并业务参数对象
  --body '{json}'                作为最终浅覆盖层合并到请求 body
  --header '{json}'              追加或覆盖请求 headers
  --keyword <关键词>              搜索关键词 (按接口支持的参数传)
  --page <页码>                  页码
  --size <数量>                  每页数量
  --help                         帮助信息 (域级或命令级)

环境文件体系:
  .env         当前生效配置（所有变量集中在此文件）
  .env.test    测试环境模板 (手工拷贝为 .env 使用)
  .env.prod    正式环境模板 (手工拷贝为 .env 使用)
  加载顺序: .env → --envPath (可选追加)

  环境切换: 将 .env.test 或 .env.prod 复制为 .env
    SL_ENV                         当前环境标识 (test | prod)

  商龙云认证:
    SL_SLY_BASEURL                 商龙云地址
    SL_AI_HOST                     AI 助手中间层 (switchToken 服务)
    SL_API_KEY                     API Key 换票认证

  代理网关 (在 .env.test/.env.prod 中配置):
    SL_GATEWAY_HOST                代理网关地址（设置后默认所有产品走网关）
    SL_CY7_VIA_GATEWAY             CY7 网关开关 (true/false，不设跟随全局)
    SL_CRM_VIA_GATEWAY             CRM 网关开关 (true/false，不设跟随全局)
    SL_SCM_VIA_GATEWAY             SCM 网关开关 (true/false，不设跟随全局)

  直连地址 (仅 VIA_GATEWAY=false 时需要):
    SL_CY7_API_BASE_URL            CY7 餐饮 API 地址
    SL_CRM_API_BASE_URL            CRM8 API 地址
    SL_SCM_API_BASE_URL            供应链 API 地址
    SL_ANALYSIS_API_BASE_URL       供应链报表分析引擎根地址（sl scm_analysis，POST /analysis/query）
    SL_ANALYSIS_AUTHORIZATION_OVERRIDE  可选，仅 scm_analysis：覆盖 Authorization / Fx-Token，与浏览器 Network 一致

  业务参数 (在 .env 主控中配置):
    SL_CY7_GROUP_ID / BRAND_ID / STORE_ID    CY7 集团/品牌/门店号
    SL_CRM_GC_ID / STORE_ID                  CRM group_code/门店号
    SL_UNIFIED_G_ID                          统一 G 号
    SL_PERSPECTIVE                           Agent 视角 (group|store)
    SL_LOCK_BIZ_PARAMS=true                  锁定 .env 中的业务参数，避免 token refresh 覆盖
    SL_LOCK_BIZ_PARAM_KEYS=SL_CRM_GC_ID,...  可选，仅锁定指定业务参数；不填则锁定全部 SL_* 业务参数
`);
}
function printDomains() {
    const domains = (0, commands_1.getAllDomains)();
    console.log(`\n可用域 (${domains.length} 个):\n`);
    domains.forEach((domain) => {
        const data = (0, commands_1.loadCommands)(domain);
        console.log(`  ${domain.padEnd(20)}${data ? `${data.count} 个命令` : ''}`);
    });
    console.log('\n用法: sl <域> --help  查看域下所有命令');
}
function printDomainHelp(domain, data) {
    console.log(`\n域: ${domain} (${data.count} 个命令)\n`);
    const maxLen = Math.min(Math.max(...data.commands.map((cmd) => cmd.action.length)), 35);
    const productLabels = {
        cy7: '[CY7]',
        crm: '[CRM]',
        scm: '[SCM]',
        sly: '[SLY]',
        dc: '[DC]',
        fx: '[FX]',
    };
    data.commands.forEach((cmd) => {
        const product = productLabels[cmd.product || 'cy7'] || `[${cmd.product}]`;
        const perspective = { group: '[集团]', store: '[门店]', both: '' }[cmd.perspective || ''] || '';
        const security = cmd.security_level ? ` ${cmd.security_level}` : '';
        console.log(`  sl ${domain} ${cmd.action.padEnd(maxLen + 2)}${product}${perspective}${security} ${(cmd.name || '').slice(0, 30)}`);
    });
    console.log(`\n用法: sl ${domain} <命令> [--参数 值]`);
    console.log(`详情: sl ${domain} <命令> --help`);
}
function printCommandHelp(domain, cmd) {
    console.log('');
    console.log(`╔══ ${cmd.command} ══`);
    console.log(`║ 名称: ${cmd.name || cmd.action}`);
    console.log(`║ 描述: ${cmd.description || '-'}`);
    console.log(`║ 产品: ${(cmd.product || 'cy7').toUpperCase()}`);
    console.log(`║ 视角: ${({ group: '集团', store: '门店', both: '通用' }[cmd.perspective || ''] || cmd.perspective)}`);
    console.log(`║ 分类: ${cmd.category || '-'}`);
    console.log(`║ 安全: ${cmd.security_level || '-'}`);
    console.log('║');
    console.log(`║ 接口: ${cmd.endpoint.method} ${cmd.endpoint.path}`);
    console.log(`║ 来源: ${cmd.source_file || '-'} → ${cmd.source_function || '-'}`);
    console.log('╚══');
    const envParams = Object.entries(cmd.env_mapping || {}).filter(([key]) => !key.startsWith('_'));
    if (envParams.length > 0) {
        console.log('\n自动填充参数 (从环境变量):');
        const maxName = Math.max(...envParams.map(([key]) => key.length));
        envParams.forEach(([param, envKey]) => {
            const value = (0, env_1.getEnv)(envKey);
            console.log(`  ${param.padEnd(maxName + 2)}← ${envKey}${value ? ` = ${JSON.stringify(value)}` : ' (未设置)'}`);
        });
    }
    if (cmd.product === 'dc' && (cmd.parameters || []).some((parameter) => parameter.name.startsWith('SL_'))) {
        const hasBizParams = [
            'SL_CY7_GROUP_ID',
            'SL_CY7_STORE_ID',
            'SL_CY7_BRAND_ID',
            'SL_CRM_GC_ID',
            'SL_CRM_STORE_ID',
            'SL_SCM_GROUP_ID',
            'SL_SCM_STORE_ID',
            'SL_UNIFIED_G_ID',
        ].some((key) => !!(0, env_1.getEnv)(key));
        console.log('\n自动填充参数 (从 token.json.biz_params):');
        console.log(`  biz_params  ← token.json.biz_params${hasBizParams ? ' (已设置)' : ' (未设置)'}`);
    }
    if ((cmd.parameters || []).length > 0) {
        console.log('\n业务参数 (通过 --key value 传入):');
        const maxName = Math.max(...(cmd.parameters || []).map((parameter) => parameter.name.length));
        (cmd.parameters || []).forEach((parameter) => {
            const required = parameter.required ? ' [必填]' : '';
            const defaultValue = parameter.default !== undefined ? ` (默认: ${JSON.stringify(parameter.default)})` : '';
            const type = parameter.type ? ` <${parameter.type}>` : '';
            console.log(`  --${parameter.name.padEnd(maxName + 2)}${type}${required}${defaultValue}`);
            if (parameter.description) {
                console.log(`    ${' '.repeat(maxName + 2)}${parameter.description}`);
            }
        });
    }
    else {
        console.log('\n业务参数: (未定义，可通过 --key value 传入任意参数)');
    }
    console.log('\n通用参数:');
    console.log('  --format, -f     输出格式: json | table | csv (默认: json)');
    console.log('  --verbose, -v    打印完整请求/响应 headers 和 body');
    console.log('  --envPath        额外读取指定 .env 文件或目录中的 .env');
    console.log('  --params         追加合并 JSON 参数对象');
    console.log('  --body           作为最终浅覆盖层合并到 JSON body');
    if (cmd.endpoint.body_format === 'form') {
        console.log('  --body-file      读取文件内容为 application/x-www-form-urlencoded 原样发送（与 curl --data-raw 一致）');
    }
    console.log('  --header         追加或覆盖 JSON headers');
    console.log('  --help, -h       显示此帮助信息');
    console.log('\n示例:');
    console.log(`  sl ${domain} ${cmd.action}`);
    console.log(`  sl ${domain} ${cmd.action} --format table`);
    console.log(`  sl ${domain} ${cmd.action} --verbose`);
    console.log(`  sl ${domain} ${cmd.action} --params '${'{"pageNo":1}'}'`);
    console.log(`  sl ${domain} ${cmd.action} --body '${'{"shopId":"1000057789"}'}'`);
    console.log(`  sl ${domain} ${cmd.action} --header '${'{"X-Debug":"1"}'}'`);
    const exampleParameter = (cmd.parameters || []).find((parameter) => parameter.example !== undefined) || (cmd.parameters || [])[0];
    if (exampleParameter) {
        const exampleValue = exampleParameter.example !== undefined
            ? exampleParameter.example
            : exampleParameter.default !== undefined
                ? exampleParameter.default
                : '...';
        console.log(`  sl ${domain} ${cmd.action} --${exampleParameter.name} ${JSON.stringify(exampleValue)}`);
    }
    console.log('');
}
