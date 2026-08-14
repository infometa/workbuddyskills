#!/usr/bin/env node
/**
 * container-scripts/pm2-register.js
 *
 * 容器端：用 PM2 启动应用 + 自检 cwd（防 I 类路径漂移最后一道运行时防线）
 *
 * 协议：
 *   node pm2-register.js --input '<json>'
 *
 *   input: {
 *     projectId: string;        // 用于 cwd 白名单校验
 *     pm2Name: string;          // PM2 进程名（建议 pd-${projectId}）
 *     appPath: string;          // 必须 === /data/services/apps/${projectId}
 *     script: string;           // 入口脚本，例 'server.js'
 *     port: number;             // 通过 PORT 环境变量传给 server
 *     pm2Cmd?: string;          // 默认 'pm2'（测试时可注入 stub）
 *     pm2CmdArgs?: string[];    // 默认 []（注入 stub 时可前缀 args，例 [stubPath]）
 *   }
 *
 * 流程：
 *   1. 校验 appPath === /data/services/apps/${projectId}
 *   2. pm2 start ${appPath}/${script} --name pm2Name --cwd appPath（PORT env）
 *   3. pm2 save
 *   4. pm2 jlist → 找 pm2Name → 校验 pm_cwd === appPath + status === 'online'
 *   5. 任一不通过 → status:'failed'（强阻塞 R1）
 *
 * 退出码：success=0, failed=1
 */
'use strict';

const fs = require('node:fs');
const { spawnSync } = require('node:child_process');

function emitSuccess(data) {
  process.stdout.write(JSON.stringify({ status: 'success', data }) + '\n');
  process.exit(0);
}
function emitFailure(code, message, hint, details) {
  const err = { code, message };
  if (hint) err.hint = hint;
  if (details) err.details = details;
  process.stdout.write(JSON.stringify({ status: 'failed', error: err }) + '\n');
  process.exit(1);
}
function logProgress(msg) {
  process.stderr.write('[pm2-register] ' + msg + '\n');
}

function parseInput(argv) {
  const i = argv.indexOf('--input');
  if (i < 0) return null;
  const v = argv[i + 1];
  if (v === undefined) return null;
  try {
    return JSON.parse(v);
  } catch (e) {
    emitFailure('BAD_INPUT', '--input is not valid JSON: ' + e.message);
  }
}

const PROJECT_ID_RE = /^[a-zA-Z0-9_-]+$/;
function isValidProjectId(s) {
  return (
    typeof s === 'string' &&
    s.length > 0 &&
    s.length <= 100 &&
    PROJECT_ID_RE.test(s)
  );
}

/**
 * 调 pm2（execFile argv 直传，绕过 shell 引号）
 *
 * @returns { stdout, stderr, code }
 */
function pm2(input, args) {
  const cmd = input.pm2Cmd || 'pm2';
  const prefix = Array.isArray(input.pm2CmdArgs) ? input.pm2CmdArgs : [];
  const allArgs = [...prefix, ...args];
  const r = spawnSync(cmd, allArgs, {
    encoding: 'utf-8',
    timeout: 60_000,
    windowsHide: true,
  });
  return {
    stdout: String(r.stdout || ''),
    stderr: String(r.stderr || ''),
    code: r.status === null ? -1 : r.status,
  };
}

function main(argv) {
  const input = parseInput(argv);
  if (!input || typeof input !== 'object') {
    emitFailure('BAD_INPUT', 'Provide --input <json>');
  }

  // 1. 输入校验
  if (!isValidProjectId(input.projectId)) {
    emitFailure(
      'BAD_INPUT',
      'projectId fails format check (a-z0-9_- 1-100)',
    );
  }
  if (typeof input.pm2Name !== 'string' || input.pm2Name.length === 0) {
    emitFailure('BAD_INPUT', 'pm2Name must be non-empty string');
  }
  if (typeof input.appPath !== 'string' || input.appPath.length === 0) {
    emitFailure('BAD_INPUT', 'appPath must be non-empty string');
  }
  if (typeof input.script !== 'string' || input.script.length === 0) {
    emitFailure('BAD_INPUT', 'script must be non-empty string');
  }
  if (
    typeof input.port !== 'number' ||
    !Number.isInteger(input.port) ||
    input.port < 1 ||
    input.port > 65535
  ) {
    emitFailure('BAD_INPUT', 'port must be integer 1-65535');
  }

  // 2. appPath 白名单 (路径单一事实源)
  const expectedAppPath = '/data/services/apps/' + input.projectId;
  if (input.appPath !== expectedAppPath) {
    emitFailure(
      'BAD_APP_PATH',
      'appPath=' +
        input.appPath +
        ' but expected=' +
        expectedAppPath +
        ' (path single source of truth)',
      'appPath 必须严格等于 /data/services/apps/{projectId}',
    );
  }

  // 3. pm2 start
  const scriptPath = input.appPath + '/' + input.script;
  const hasInterpreter = typeof input.interpreter === 'string' && input.interpreter.length > 0;
  logProgress(
    'starting pm2: ' + input.pm2Name +
    ' (cwd=' + input.appPath +
    (hasInterpreter ? ', interpreter=' + input.interpreter : '') + ')',
  );
  const startArgs = [
    'start',
    scriptPath,
    '--name',
    input.pm2Name,
    '--cwd',
    input.appPath,
    '--update-env',
  ];
  // 非 Node.js 项目通过 --interpreter 指定解释器（如 python3）
  if (hasInterpreter) {
    startArgs.push('--interpreter', input.interpreter);
  }
  // 通过 --env-PORT 风格不通用，最稳是 PM2 ecosystem 或 process.env 注入
  // 这里用 PM2 的 ENV_VAR 语法：pm2 start ... -- --env，但实际 PM2 的标准是 ecosystem.config 或者 ENV_PORT 命令前缀
  // 选择最简单的：通过 spawnSync env 把 PORT 传进 pm2，pm2 会把当前进程 env 继承给子进程（PM2 默认行为）
  // 注意：要确保后续 pm2 进程能看到 PORT
  const startEnv = { ...process.env, PORT: String(input.port) };

  const cmd = input.pm2Cmd || 'pm2';
  const prefix = Array.isArray(input.pm2CmdArgs) ? input.pm2CmdArgs : [];
  const startResult = spawnSync(cmd, [...prefix, ...startArgs], {
    encoding: 'utf-8',
    timeout: 60_000,
    windowsHide: true,
    env: startEnv,
  });
  if (startResult.status !== 0) {
    emitFailure(
      'PM2_START_FAILED',
      'pm2 start exited ' +
        startResult.status +
        ': ' +
        String(startResult.stderr || '').slice(0, 300),
    );
  }

  // 4. pm2 save
  const saveResult = pm2(input, ['save']);
  if (saveResult.code !== 0) {
    emitFailure(
      'PM2_SAVE_FAILED',
      'pm2 save exited ' +
        saveResult.code +
        ': ' +
        saveResult.stderr.slice(0, 300),
    );
  }

  // 5. pm2 jlist 自检（路径单一事实源第四道防线）
  logProgress('self-check: pm2 jlist');
  const listResult = pm2(input, ['jlist']);
  if (listResult.code !== 0) {
    emitFailure(
      'PM2_JLIST_FAILED',
      'pm2 jlist exited ' +
        listResult.code +
        ': ' +
        listResult.stderr.slice(0, 300),
    );
  }
  let procs;
  try {
    procs = JSON.parse(listResult.stdout);
  } catch (e) {
    emitFailure(
      'PM2_BAD_JSON',
      'pm2 jlist returned non-JSON: ' + e.message,
      undefined,
      { stdoutHead: listResult.stdout.slice(0, 300) },
    );
  }
  if (!Array.isArray(procs)) {
    emitFailure(
      'PM2_BAD_JSON',
      'pm2 jlist returned non-array',
    );
  }

  const proc = procs.find((p) => p && p.name === input.pm2Name);
  if (!proc) {
    emitFailure(
      'NOT_FOUND',
      'PM2 process not found after start: ' + input.pm2Name,
      'pm2 start 可能没成功。检查 pm2 logs.',
    );
  }
  const actualCwd = (proc.pm2_env && proc.pm2_env.pm_cwd) || '';
  const actualStatus = (proc.pm2_env && proc.pm2_env.status) || '';

  if (actualCwd !== input.appPath) {
    emitFailure(
      'CWD_MISMATCH',
      'PM2 pm_cwd=' +
        actualCwd +
        ' but expected=' +
        input.appPath +
        ' (path drift detected)',
      '严重路径漂移：pm2 进程的 cwd 不是 /data/services/apps/{projectId}。可能 pm2 沿用了旧 dump 状态，pm2 delete + 重启',
      { actualCwd, expectedCwd: input.appPath },
    );
  }
  if (actualStatus !== 'online') {
    emitFailure(
      'BAD_STATUS',
      'PM2 status=' + actualStatus + ' (expected online)',
      'pm2 logs ' + input.pm2Name + ' 看启动失败原因',
      { actualStatus },
    );
  }

  emitSuccess({
    pm2Name: input.pm2Name,
    pm2Cwd: actualCwd,
    pid: proc.pid,
    status: actualStatus,
    port: input.port,
  });
}

main(process.argv.slice(2));
