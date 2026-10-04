#!/usr/bin/env node
'use strict';

const pkg = require('../package.json');

function parseFlags(args) {
  const flags = {};
  const rest = [];
  for (const a of args) {
    if (a === '--no-wait') flags.noWait = true;
    else if (a === '--json') flags.json = true;
    else rest.push(a);
  }
  return { flags, rest };
}

function printHelp() {
  process.stdout.write(
    [
      'tc-chengxin —— 同程程心 WorkBuddy 鉴权 CLI（仅鉴权 / 出 token）',
      '',
      '用法:',
      '  tc-chengxin auth login [--no-wait --json]   发起同程登录授权',
      '  tc-chengxin auth status [--json]            查看登录状态（必要时静默续期/轮询）',
      '  tc-chengxin auth logout                     退出登录并清除本地凭证',
      '  tc-chengxin auth invalidate [--json]        本地标记登录失效（供 401 自动重授权使用）',
      '  tc-chengxin token                           打印当前有效 access_token（必要时自动续期）',
      '  tc-chengxin --version                       版本号',
      ''
    ].join('\n') + '\n'
  );
}

async function main() {
  const argv = process.argv.slice(2);

  if (argv.includes('--version') || argv.includes('-v') || argv[0] === 'version') {
    process.stdout.write(pkg.version + '\n');
    return 0;
  }
  if (argv.length === 0 || argv.includes('--help') || argv.includes('-h') || argv[0] === 'help') {
    printHelp();
    return 0;
  }

  const { flags, rest } = parseFlags(argv);
  const cmd = rest[0];
  const sub = rest[1];

  if (cmd === 'auth' && sub === 'login') {
    return require('../src/commands/auth-login').authLogin(flags);
  }
  if (cmd === 'auth' && sub === 'status') {
    return require('../src/commands/auth-status').authStatus(flags);
  }
  if (cmd === 'auth' && sub === 'logout') {
    return require('../src/commands/auth-logout').authLogout();
  }
  if (cmd === 'auth' && sub === 'invalidate') {
    return require('../src/commands/auth-invalidate').authInvalidate(flags);
  }
  if (cmd === 'token') {
    return require('../src/commands/token').token();
  }

  process.stderr.write('未知命令: ' + argv.join(' ') + '\n\n');
  printHelp();
  return 1;
}

main()
  .then((code) => process.exit(code || 0))
  .catch((e) => {
    process.stderr.write('错误: ' + (e && e.message ? e.message : String(e)) + '\n');
    process.exit(1);
  });
