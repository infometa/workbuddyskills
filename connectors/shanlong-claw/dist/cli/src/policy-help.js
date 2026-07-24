"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.printPolicyHelpDisabled = printPolicyHelpDisabled;
exports.printPolicyRootHelp = printPolicyRootHelp;
exports.printPolicyCoreHelp = printPolicyCoreHelp;
exports.printPolicyDomains = printPolicyDomains;
exports.printPolicyDomainHelp = printPolicyDomainHelp;
exports.printPolicyCommandHelp = printPolicyCommandHelp;
exports.getPolicyAllowedDomains = getPolicyAllowedDomains;
const commands_1 = require("./commands");
const policy_evaluator_1 = require("./policy-evaluator");
const policy_core_1 = require("./policy-core");
const help_1 = require("./help");
const HELP_DISABLED_MESSAGE = 'Help is disabled by the active CLI policy.';
function printPolicyHelpDisabled() {
    console.error(HELP_DISABLED_MESSAGE);
    process.exit(1);
}
function getAllowedCoreEntries(context, family, commandId) {
    return policy_core_1.CORE_COMMANDS.filter((entry, index, list) => {
        if (family && entry.argv[0] !== family) {
            return false;
        }
        if (commandId && entry.id !== commandId) {
            return false;
        }
        if (!(0, policy_evaluator_1.isCoreCommandAllowed)(context.policy, entry.id)) {
            return false;
        }
        return list.findIndex((item) => item.id === entry.id) === index;
    });
}
function printCoreEntries(entries) {
    if (entries.length === 0) {
        console.log('  (无可用命令)');
        return;
    }
    for (const entry of entries) {
        console.log(`  sl ${entry.argv.join(' ').padEnd(28)} ${entry.summary}`);
    }
}
function printPolicyRootHelp(context) {
    if (!context.policy.help.enabled) {
        printPolicyHelpDisabled();
    }
    console.log('\nsl — 商龙餐饮 SaaS CLI (policy)\n');
    console.log('可用基础命令:\n');
    printCoreEntries(getAllowedCoreEntries(context));
    console.log('\n用法: sl <域> <命令> [参数]');
    console.log('      sl domains              列出允许的域');
}
function printPolicyCoreHelp(context, family, commandId) {
    if (!context.policy.help.enabled) {
        printPolicyHelpDisabled();
    }
    const entries = getAllowedCoreEntries(context, family, commandId);
    if (commandId && entries.length === 0) {
        printPolicyHelpDisabled();
    }
    console.log(`\n可用命令 (${family}):\n`);
    printCoreEntries(entries);
}
function printPolicyDomains(context) {
    if (!context.policy.help.enabled) {
        printPolicyHelpDisabled();
    }
    const rows = [];
    for (const domain of (0, commands_1.getAllDomains)()) {
        const data = (0, commands_1.loadCommands)(domain);
        if (!data) {
            continue;
        }
        const filtered = (0, policy_evaluator_1.filterDomainFile)(context.evaluator, data);
        if (filtered.commands.length > 0) {
            rows.push({ domain, count: filtered.count });
        }
    }
    console.log(`\n可用域 (${rows.length} 个):\n`);
    for (const row of rows) {
        console.log(`  ${row.domain.padEnd(20)}${row.count} 个命令`);
    }
    console.log('\n用法: sl <域> --help  查看域下允许的命令');
}
function printPolicyDomainHelp(context, domain, data) {
    if (!context.policy.help.enabled) {
        printPolicyHelpDisabled();
    }
    const filtered = (0, policy_evaluator_1.filterDomainFile)(context.evaluator, data);
    if (filtered.commands.length === 0) {
        printPolicyHelpDisabled();
    }
    (0, help_1.printDomainHelp)(domain, filtered);
}
function printPolicyCommandHelp(context, domain, command) {
    if (!context.policy.help.enabled) {
        printPolicyHelpDisabled();
    }
    if (!(0, policy_evaluator_1.isBusinessCommandAllowed)(context.evaluator, command)) {
        printPolicyHelpDisabled();
    }
    (0, help_1.printCommandHelp)(domain, command);
}
function getPolicyAllowedDomains(context) {
    return (0, commands_1.getAllDomains)().filter((domain) => {
        const data = (0, commands_1.loadCommands)(domain);
        return !!data && (0, policy_evaluator_1.filterDomainFile)(context.evaluator, data).commands.length > 0;
    });
}
