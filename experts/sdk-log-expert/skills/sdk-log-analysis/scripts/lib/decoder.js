import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const DEFAULT_PUBLIC_PACKAGE = '@tencent/sdk-log-decoder';

function hasVendoredDecoder(vendorDir) {
  // Pure-TypeScript vendor: package.json + dist CLI entry.
  return fs.existsSync(path.join(vendorDir, 'package.json'))
    && fs.existsSync(path.join(vendorDir, 'dist', 'cjs', 'node', 'cli.js'));
}

export function resolveDecoderCommand({ skillDir, env = process.env } = {}) {
  if (!skillDir) throw new Error('resolveDecoderCommand requires skillDir');

  if (env.CLOG_DECODER_BIN) {
    return {
      mode: 'custom-bin',
      command: env.CLOG_DECODER_BIN,
      args: [],
      description: 'CLOG_DECODER_BIN override',
    };
  }

  const vendorDir = path.join(skillDir, 'vendor', 'clog-decoder');
  if (hasVendoredDecoder(vendorDir)) {
    return {
      mode: 'vendored',
      command: process.execPath,
      args: [path.join(vendorDir, 'dist', 'cjs', 'node', 'cli.js')],
      description: 'vendored TypeScript decoder',
    };
  }

  const args = ['--yes'];
  if (env.CLOG_DECODER_REGISTRY) args.push('--registry', env.CLOG_DECODER_REGISTRY);
  args.push(env.CLOG_DECODER_PACKAGE || DEFAULT_PUBLIC_PACKAGE);
  return {
    mode: 'npx',
    command: 'npx',
    args,
    description: 'npm decoder fallback',
  };
}

export function decodeFile(inputPath, outputPath, { skillDir, env = process.env, timeoutMs } = {}) {
  const resolved = resolveDecoderCommand({ skillDir, env });
  const result = spawnSync(resolved.command, [...resolved.args, inputPath, outputPath], {
    env,
    encoding: 'utf-8',
    timeout: timeoutMs,
  });
  if (result.error) {
    throw new Error(`clog decode failed (${resolved.mode}): ${result.error.message}`);
  }
  if (result.status !== 0) {
    const details = [result.stderr, result.stdout].filter(Boolean).join('\n').trim();
    throw new Error(`clog decode failed (${resolved.mode}, exit ${result.status}): ${details}`);
  }
  if (!fs.existsSync(outputPath) || fs.statSync(outputPath).size === 0) {
    throw new Error(`clog decode produced empty output: ${outputPath}`);
  }
  return { ...resolved, outputPath };
}
