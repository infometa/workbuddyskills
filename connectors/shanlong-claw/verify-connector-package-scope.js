#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const { evaluateConnectorReadOnlyCommand } = require('./connector-readonly-policy');

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function walkFiles(root, current = root, out = []) {
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    const full = path.join(current, entry.name);
    if (entry.isSymbolicLink()) {
      throw new Error(`symbolic link is forbidden: ${path.relative(root, full)}`);
    }
    if (entry.isDirectory()) walkFiles(root, full, out);
    else if (entry.isFile()) out.push(full);
  }
  return out;
}

function findUnreachableRuntimeFiles(srcDir) {
  const allJs = walkFiles(srcDir).filter((file) => file.endsWith('.js'));
  const seen = new Set();
  const pending = [path.join(srcDir, 'index.js')];
  while (pending.length > 0) {
    const file = path.resolve(pending.pop());
    if (seen.has(file) || !fs.existsSync(file)) continue;
    seen.add(file);
    const source = fs.readFileSync(file, 'utf8');
    for (const match of source.matchAll(/require\(\s*['"](\.[^'"]+)['"]\s*\)/g)) {
      let dependency = path.resolve(path.dirname(file), match[1]);
      if (!path.extname(dependency)) dependency += '.js';
      if (dependency.startsWith(`${path.resolve(srcDir)}${path.sep}`) && fs.existsSync(dependency)) {
        pending.push(dependency);
      }
    }
  }
  return allJs.filter((file) => !seen.has(path.resolve(file)));
}

function verifyConnectorDist(distDir, label = distDir) {
  const manifestPath = path.join(distDir, 'generated', 'cli', 'manifest.json');
  const commandsDir = path.join(distDir, 'generated', 'cli', 'commands');
  const capabilitiesPath = path.join(distDir, 'cli', 'src', 'build-capabilities.js');
  const outputRuntimePath = path.join(distDir, 'cli', 'src', 'output.js');
  const updateVerifierPath = path.join(distDir, 'cli', 'src', 'verify-connector-package-scope.js');
  const readOnlyPolicyPath = path.join(distDir, 'cli', 'src', 'connector-readonly-policy.js');
  const entryPath = path.join(distDir, 'cli', 'src', 'index.js');
  const distPackagePath = path.join(distDir, 'package.json');

  for (const required of [
    manifestPath,
    commandsDir,
    capabilitiesPath,
    outputRuntimePath,
    updateVerifierPath,
    readOnlyPolicyPath,
    entryPath,
    distPackagePath,
  ]) {
    if (!fs.existsSync(required)) {
      throw new Error(`${label}: missing required S1 package artifact: ${path.relative(distDir, required)}`);
    }
  }

  const manifest = readJson(manifestPath);
  if (manifest.mode !== 'S1-only') {
    throw new Error(`${label}: manifest.mode must be S1-only, got ${JSON.stringify(manifest.mode)}`);
  }

  const distPackage = readJson(distPackagePath);
  if (distPackage.name !== 'slclaw-cli-s1') {
    throw new Error(`${label}: dist package must be slclaw-cli-s1, got ${JSON.stringify(distPackage.name)}`);
  }
  if (distPackage.dependencies && Object.keys(distPackage.dependencies).length > 0) {
    throw new Error(`${label}: runtime dependencies must be bundled, not declared in dist/package.json`);
  }

  const allowedTopLevel = new Set(['cli', 'generated', 'package.json']);
  const unexpectedTopLevel = fs.readdirSync(distDir)
    .filter((entry) => !allowedTopLevel.has(entry));
  if (unexpectedTopLevel.length > 0) {
    throw new Error(`${label}: unexpected top-level artifacts: ${unexpectedTopLevel.join(', ')}`);
  }

  const allFiles = walkFiles(distDir);
  const forbiddenArtifacts = allFiles.filter((file) => {
    const relative = path.relative(distDir, file);
    const base = path.basename(file);
    return base === '.DS_Store'
      || base === '.env'
      || base.startsWith('.env.')
      || /\.(?:key|pem|p12|pfx|jks|keystore|map|ts)$/i.test(base)
      || relative === path.join('cli', 'src', 'view.js');
  });
  if (forbiddenArtifacts.length > 0) {
    throw new Error(
      `${label}: forbidden or unnecessary artifacts: ${forbiddenArtifacts.map((file) => path.relative(distDir, file)).join(', ')}`,
    );
  }

  const unreachableRuntime = findUnreachableRuntimeFiles(path.join(distDir, 'cli', 'src'));
  if (unreachableRuntime.length > 0) {
    throw new Error(
      `${label}: unreachable runtime files: ${unreachableRuntime.map((file) => path.relative(distDir, file)).join(', ')}`,
    );
  }

  delete require.cache[require.resolve(capabilitiesPath)];
  const capabilities = require(capabilitiesPath);
  if (capabilities.PACKAGE_SCOPE !== 'S1-only') {
    throw new Error(
      `${label}: PACKAGE_SCOPE must be S1-only, got ${JSON.stringify(capabilities.PACKAGE_SCOPE)}`,
    );
  }

  const outputRuntime = fs.readFileSync(outputRuntimePath, 'utf8');
  if (/\brequire\s*\(\s*['"]quicktype-core['"]\s*\)/.test(outputRuntime)) {
    throw new Error(`${label}: quicktype-core is not bundled into output.js`);
  }

  const commandFiles = fs.readdirSync(commandsDir).filter((file) => file.endsWith('.json'));
  if (commandFiles.length === 0) {
    throw new Error(`${label}: no command catalogs found`);
  }

  let totalCommands = 0;
  const violations = [];
  const forbiddenCommandFields = [
    'credential_type',
    'description_short',
    'output_columns',
    'relations',
    'source_file',
    'sql',
    'tags',
  ];
  for (const file of commandFiles) {
    const data = readJson(path.join(commandsDir, file));
    const commands = Array.isArray(data.commands) ? data.commands : [];
    if (data.count !== commands.length) {
      throw new Error(`${label}: ${file} count=${data.count} but contains ${commands.length} commands`);
    }
    totalCommands += commands.length;
    for (const command of commands) {
      const leakedFields = forbiddenCommandFields.filter((field) => command[field] !== undefined);
      if (leakedFields.length > 0) {
        violations.push(`${file}/${command.action || '<unknown>'}:unnecessary-fields:${leakedFields.join('+')}`);
        continue;
      }
      const result = evaluateConnectorReadOnlyCommand(command);
      if (!result.allowed) {
        violations.push(`${file}/${command.action || '<unknown>'}:${result.reason}`);
      }
    }
  }

  if (violations.length > 0) {
    const sample = violations.slice(0, 10).join(', ');
    throw new Error(`${label}: found ${violations.length} non-read-only commands (${sample})`);
  }
  if (totalCommands === 0) {
    throw new Error(`${label}: S1 command catalog is empty`);
  }
  if (manifest.total_domains !== commandFiles.length || manifest.total_commands !== totalCommands) {
    throw new Error(
      `${label}: manifest counts do not match catalogs `
      + `(manifest=${manifest.total_domains}/${manifest.total_commands}, actual=${commandFiles.length}/${totalCommands})`,
    );
  }

  return { domains: commandFiles.length, commands: totalCommands };
}

if (require.main === module) {
  const distDir = process.argv[2];
  if (!distDir) {
    console.error('usage: node scripts/verify-connector-package-scope.js <dist-dir>');
    process.exit(2);
  }
  try {
    const stats = verifyConnectorDist(path.resolve(distDir));
    console.log(`connector package scope: PASS (${stats.domains} domains / ${stats.commands} S1 commands)`);
  } catch (error) {
    console.error(`connector package scope: FAIL: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

module.exports = { verifyConnectorDist };
