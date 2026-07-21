#!/usr/bin/env node
/**
 * check_wrapper_compat.js
 *
 * Checks whether recent evolver changes affect interfaces used by feishu-evolver-wrapper.
 * Run manually or via cursor rule to detect breaking changes early.
 *
 * Usage:
 *   node scripts/check_wrapper_compat.js           # check all interfaces
 *   node scripts/check_wrapper_compat.js --diff     # check only files in git diff
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');

const INTERFACE_CONTRACT = [
  {
    file: 'src/ops/self_repair.js',
    requiredExports: ['repair'],
    description: 'wrapper calls selfRepair.repair()',
  },
  {
    file: 'src/ops/commentary.js',
    requiredExports: ['getComment'],
    description: 'wrapper calls getComment(type, dur, ok, persona)',
  },
  {
    file: 'src/ops/cleanup.js',
    requiredExports: ['run'],
    description: 'wrapper calls cleanup.run()',
  },
  {
    file: 'src/ops/skills_monitor.js',
    requiredExports: ['run'],
    description: 'wrapper calls skills_monitor.run()',
  },
  {
    file: 'src/ops/health_check.js',
    requiredExports: ['runHealthCheck'],
    description: 'wrapper calls runHealthCheck()',
  },
  {
    file: 'src/gep/bridge.js',
    requiredExports: ['renderSessionsSpawnCall'],
    description: 'wrapper parses sessions_spawn() output from bridge',
  },
];

function getChangedFiles() {
  try {
    const out = execSync('git diff --name-only HEAD~1', { cwd: ROOT, encoding: 'utf8' }).trim();
    return out ? out.split('\n') : [];
  } catch (e) {
    return [];
  }
}

function checkInterface(spec) {
  const fullPath = path.join(ROOT, spec.file);
  if (!fs.existsSync(fullPath)) {
    return { file: spec.file, status: 'MISSING', detail: 'file does not exist' };
  }

  try {
    const mod = require(fullPath);
    const missing = spec.requiredExports.filter(name => typeof mod[name] !== 'function');
    if (missing.length > 0) {
      return {
        file: spec.file,
        status: 'BROKEN',
        detail: `missing exports: ${missing.join(', ')} -- ${spec.description}`,
      };
    }
    return { file: spec.file, status: 'OK' };
  } catch (e) {
    return { file: spec.file, status: 'ERROR', detail: `require failed: ${e.message}` };
  }
}

function main() {
  const diffMode = process.argv.includes('--diff');
  let contracts = INTERFACE_CONTRACT;

  if (diffMode) {
    const changed = getChangedFiles();
    contracts = contracts.filter(c => changed.includes(c.file));
    if (contracts.length === 0) {
      process.stdout.write('No wrapper-affecting files changed.\n');
      process.exit(0);
    }
  }

  const results = contracts.map(checkInterface);
  const broken = results.filter(r => r.status !== 'OK');

  for (const r of results) {
    const icon = r.status === 'OK' ? '[OK]' : '[!!]';
    process.stdout.write(`${icon} ${r.file}${r.detail ? ' -- ' + r.detail : ''}\n`);
  }

  if (broken.length > 0) {
    process.stdout.write(`\n${broken.length} interface(s) broken. feishu-evolver-wrapper-private needs update.\n`);
    process.stdout.write('Wrapper repo: /home/kprimo97/evomap/feishu-evolver-wrapper-private\n');
    process.exit(1);
  } else {
    process.stdout.write(`\nAll ${results.length} interface(s) compatible.\n`);
  }
}

main();
