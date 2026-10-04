import fs from 'node:fs';
import { capabilityIds, evaluateCapability, runCapability } from './capability-runtime.mjs';

const DEFAULT_CONTEXT = Object.freeze({ connectorAvailable: false, externalWriteAuthorized: false });

function readJsonFile(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function readStdinJson() {
  if (process.stdin.isTTY) return null;
  const text = fs.readFileSync(0, 'utf8').trim();
  return text ? JSON.parse(text) : null;
}

function parse(argv) {
  const options = {
    command: argv[0] ?? 'list',
    capabilityId: argv[1] ?? null,
    inputPath: null,
    resultPath: null,
    contextPath: null,
  };
  for (let index = 2; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === '--input') options.inputPath = argv[++index];
    else if (flag === '--result') options.resultPath = argv[++index];
    else if (flag === '--context') options.contextPath = argv[++index];
    else throw new Error(`unknown_argument:${flag}`);
    if (!argv[index]) throw new Error(`missing_value:${flag}`);
  }
  return options;
}

function runCommand(options, stdinValue) {
  const input = options.inputPath ? readJsonFile(options.inputPath) : (stdinValue ?? {});
  const context = options.contextPath ? readJsonFile(options.contextPath) : DEFAULT_CONTEXT;
  const result = runCapability(options.capabilityId, input, context);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (!result.ok && ![
    'needs_clarification', 'needs_input', 'verification_required', 'verification_planned',
    'offline_degraded', 'degraded', 'descriptor_ready', 'activation_pending',
    'human_review_pending', 'human_review_required', 'quality_gate_required',
    'planning_incomplete', 'plan_incomplete', 'plan_ready', 'repurposing_planned',
    'assessment_completed', 'revision_required', 'revise', 'max_round_reached',
  ].includes(result.status)) process.exitCode = 1;
}

function evaluateCommand(options, stdinValue) {
  let result;
  let input;
  let context;
  if (options.resultPath || options.inputPath || options.contextPath) {
    if (!options.resultPath || !options.inputPath || !options.contextPath) throw new Error('evaluate_requires_result_input_and_context');
    result = readJsonFile(options.resultPath);
    input = readJsonFile(options.inputPath);
    context = readJsonFile(options.contextPath);
  } else {
    if (!stdinValue || typeof stdinValue !== 'object' || Array.isArray(stdinValue)) throw new Error('evaluate_envelope_required');
    const keys = Object.keys(stdinValue).sort().join(',');
    if (keys !== 'context,input,result') throw new Error('evaluate_envelope_requires_exact_result_input_context');
    ({ result, input, context } = stdinValue);
  }
  const evaluation = evaluateCapability(options.capabilityId, result, input, context);
  process.stdout.write(`${JSON.stringify(evaluation, null, 2)}\n`);
  if (!evaluation.ok) process.exitCode = 1;
}

function main() {
  const options = parse(process.argv.slice(2));
  if (options.command === 'list') {
    process.stdout.write(`${JSON.stringify({ schemaVersion: '1.1.0', runtime: 'ManuscriptOS', capabilityIds, connectorRequired: false, donorSkillRequired: false }, null, 2)}\n`);
    return;
  }
  if (!options.capabilityId) throw new Error('capability_id_required');
  const stdinValue = options.inputPath || options.resultPath || options.contextPath ? null : readStdinJson();
  if (options.command === 'run') return runCommand(options, stdinValue);
  if (options.command === 'evaluate') return evaluateCommand(options, stdinValue);
  throw new Error(`unknown_command:${options.command}`);
}

try {
  main();
} catch (error) {
  process.stderr.write(`${JSON.stringify({ schemaVersion: '1.1.0', ok: false, error: error.message })}\n`);
  process.exitCode = 1;
}
