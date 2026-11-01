#!/usr/bin/env node
// Run one CLI command. Filter progress only; never interpret or suppress stdout.
import { spawn } from 'node:child_process';
import { mkdirSync, openSync, writeSync, closeSync, writeFileSync, renameSync } from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
if (args[0] !== '--out-dir' || !args[1] || args[2] !== '--' || !args[3]) {
  process.stderr.write('Usage: node run-cli.mjs --out-dir <new-directory> -- <executable> [args...]\n');
  process.exit(2);
}
const dir = path.resolve(args[1]);
mkdirSync(path.dirname(dir), { recursive: true });
// Refuse reuse: stale output must never be treated as a new command result.
mkdirSync(dir, { mode: 0o700 });
const resultFile = path.join(dir, 'stdout.partial');
const result = openSync(resultFile, 'wx', 0o600);
const diagnostic = openSync(path.join(dir, 'stderr.log'), 'wx', 0o600);
const progressFile = openSync(path.join(dir, 'progress.ndjson'), 'wx', 0o600);
const seen = new Map();
let pending = '';
let lastDiagnostic = '';
function emitProgress(line) {
  let event;
  try { event = JSON.parse(line); } catch { return; }
  if (event?.event !== 'task_progress') {
    // Preserve non-progress JSON events; do not hide a new interaction type.
    process.stderr.write(line + '\n');
    return;
  }
  const p = event.data?.taskProgress;
  if (!p || typeof p.id !== 'string' || !Array.isArray(p.tasks)) {
    process.stderr.write(line + '\n');
    return;
  }
  const key = JSON.stringify([event.data.sessionId, event.data.messageId, p.id]);
  const tasks = p.tasks.map(t => ({
    id: t.id, kind: t.kind, title: t.title, status: t.status, detail: t.detail,
    featureId: t.featureId, steps: t.steps, stepProgress: t.stepProgress,
  }));
  // Ignore revision, changed, formatting, timestamps and tool-call counters.
  const signature = JSON.stringify({tasks, warnings:p.warnings, complete:p.complete});
  if (seen.get(key) === signature) return;
  seen.set(key, signature);
  // First observation must be displayed even if upstream says changed=false.
  const emitted = JSON.stringify({
    schemaVersion:event.schemaVersion, event:event.event,
    data:{...event.data, taskProgress:{...p, changed:true}},
  }) + '\n';
  writeSync(progressFile, emitted);
  process.stderr.write(emitted);
}
const child = spawn(args[3], args.slice(4), { shell:false, stdio:['inherit','pipe','pipe'] });
child.stdout.on('data', bytes => { writeSync(result, bytes); process.stdout.write(bytes); });
child.stderr.setEncoding('utf8');
child.stderr.on('data', chunk => {
  writeSync(diagnostic, chunk);
  lastDiagnostic = (lastDiagnostic + chunk).slice(-8192);
  pending += chunk;
  let end;
  while ((end = pending.indexOf('\n')) >= 0) {
    emitProgress(pending.slice(0, end).replace(/\r$/, ''));
    pending = pending.slice(end + 1);
  }
  // Bound malformed/non-line log buffering; raw diagnostics remain on disk.
  if (pending.length > 2_000_000) { process.stderr.write(pending); pending = ''; }
});
let launchError;
child.on('error', error => { launchError = error.message; process.stderr.write(error.message + '\n'); });
const signals = ['SIGINT','SIGTERM'];
const handlers = signals.map(signal => { const handler=()=>child.kill(signal); process.on(signal,handler); return handler; });
child.on('close', (code, signal) => {
  if (pending) emitProgress(pending);
  closeSync(result); closeSync(diagnostic); closeSync(progressFile);
  renameSync(resultFile, path.join(dir, 'stdout.json'));
  writeFileSync(path.join(dir, 'exit.json'), JSON.stringify({code,signal,error:launchError??null})+'\n', {flag:'wx',mode:0o600});
  if (code !== 0 && lastDiagnostic) process.stderr.write(lastDiagnostic);
  signals.forEach((signal,i)=>process.off(signal,handlers[i]));
  // Preserve command failure. The wrapper never retries or starts another task.
  process.exitCode = code ?? (signal === 'SIGINT' ? 130 : signal === 'SIGTERM' ? 143 : 1);
});
