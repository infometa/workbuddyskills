import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { sha256, stableJson } from './lib/kernel-utils.mjs';
import {
  createApprovalLedgerRequest,
  createHumanGateRequest,
  createOwnerResolutionRequest,
  validateHumanGateReceipt,
} from './quality/human-receipt-validator.mjs';

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const evaluatorRegistryPath = path.join(skillRoot, 'resources', 'gates', 'evaluator-registry.json');
const HASH = /^[a-f0-9]{64}$/u;
const BUNDLE_KEYS = ['approvalLedgerReceipt', 'asOf', 'binding', 'ownerResolutionReceipt', 'receipt'];
const BINDING_KEYS = [
  'artifactSetDigest', 'evidenceSnapshotDigest', 'gateId', 'gateInvocationDigest',
  'humanOwner', 'machineGateResultDigest', 'parameterProfile', 'projectStateDigest',
  'reviewMandate', 'reviewScopeDigest', 'sceneId', 'scenePackDigest',
];
const CONTEXT_KEYS = [
  'artifactSetDigest', 'evidenceSnapshotDigest', 'gateInvocationDigest',
  'machineGateResultDigest', 'projectStateDigest', 'reviewScopeDigest', 'scenePackDigest',
];

const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const exactKeys = (value, keys) => isObject(value) && Object.keys(value).sort().join(',') === [...keys].sort().join(',');

function loadActiveEvaluatorRegistry() {
  const bytes = fs.readFileSync(evaluatorRegistryPath);
  const registry = JSON.parse(bytes.toString('utf8'));
  const seedPath = path.resolve(path.dirname(evaluatorRegistryPath), String(registry?.seedRegistryPath ?? ''));
  const expectedSeedPath = path.join(skillRoot, 'resources', 'scene-quality-gate-registry.json');
  const seedBytes = seedPath === expectedSeedPath && fs.existsSync(seedPath) ? fs.readFileSync(seedPath) : Buffer.alloc(0);
  if (!validateEvaluatorRegistryBinding(registry, seedBytes)) throw new Error('quality_evaluator_registry_invalid');
  return registry;
}

export function validateEvaluatorRegistryBinding(registry, seedRegistryBytes) {
  return registry?.artifactType === 'active_quality_evaluator_registry'
    && registry?.seedRegistryPath === '../scene-quality-gate-registry.json'
    && registry?.activeEvaluatorCount === 32
    && registry?.pendingEvaluatorCount === 0
    && registry?.entryCount === 32
    && Array.isArray(registry.entries)
    && registry.entries.length === 32
    && new Set(registry.entries.map((item) => item.gateId)).size === 32
    && registry.entries.every((item) => item.lifecycle === 'active')
    && HASH.test(String(registry.seedRegistrySha256 ?? ''))
    && registry.seedRegistrySha256 === sha256(seedRegistryBytes);
}

function evaluatorIntegrity(entry) {
  if (entry?.lifecycle !== 'active' || !/^\.\.\/scripts\/quality\/evaluators\/[a-z0-9]+(?:-[a-z0-9]+)*\.mjs$/u.test(String(entry.evaluatorRef ?? '')) || !HASH.test(String(entry.evaluatorSha256 ?? ''))) return false;
  const target = path.resolve(path.join(skillRoot, 'resources'), ...entry.evaluatorRef.split('/'));
  const evaluatorRoot = `${path.join(skillRoot, 'scripts', 'quality', 'evaluators')}${path.sep}`;
  return target.startsWith(evaluatorRoot) && fs.existsSync(target) && sha256(fs.readFileSync(target)) === entry.evaluatorSha256;
}

export function planGates(scenePack) {
  if (!isObject(scenePack) || typeof scenePack.sceneId !== 'string' || !Array.isArray(scenePack.qualityGateRefs)) return [];
  const registry = loadActiveEvaluatorRegistry();
  return scenePack.qualityGateRefs.map((item) => {
    const human = item.registryId === 'human-review.receipt';
    const evaluator = human ? null : registry.entries.find((entry) => entry.gateId === item.registryId);
    const evaluatorReady = human ? false : evaluatorIntegrity(evaluator);
    const projection = {
      sceneId: scenePack.sceneId,
      registryId: item.registryId,
      parameterProfile: item.parameterProfile ?? null,
      humanOwner: item.humanOwner ?? null,
      reviewMandate: item.reviewMandate ?? null,
      evaluatorSha256: evaluatorReady ? evaluator.evaluatorSha256 : null,
    };
    return {
      ...projection,
      state: human ? 'trusted_human_receipt_required' : evaluatorReady ? 'active_evaluator_required' : 'evaluator_unavailable',
      passed: false,
      evaluatorRef: evaluatorReady ? evaluator.evaluatorRef : null,
      planDigest: sha256(stableJson(projection)),
    };
  });
}

// Package code can construct authority requests, but it never owns the private
// key and therefore cannot issue an acceptable human-review receipt.
export { createApprovalLedgerRequest, createOwnerResolutionRequest };
export function createHumanReviewRequest(binding, evidence, options = {}) {
  return createHumanGateRequest(binding, evidence, options);
}

export function validateHumanReviewReceipt(sceneGateBinding, bundle, sceneId, currentContext) {
  if (!exactKeys(bundle, BUNDLE_KEYS) || !exactKeys(bundle.binding, BINDING_KEYS) || !exactKeys(currentContext, CONTEXT_KEYS)) return { ok: false, issues: ['trusted_human_review_bundle_invalid'] };
  const binding = bundle.binding;
  const sceneBindingValid = sceneGateBinding?.registryId === 'human-review.receipt'
    && binding.gateId === 'human-review.receipt'
    && binding.sceneId === sceneId
    && binding.parameterProfile === sceneGateBinding.parameterProfile
    && binding.humanOwner === sceneGateBinding.humanOwner
    && binding.reviewMandate === sceneGateBinding.reviewMandate;
  const digestFieldsValid = BINDING_KEYS.filter((key) => key.endsWith('Digest')).every((key) => HASH.test(String(binding[key] ?? '')));
  const currentContextValid = CONTEXT_KEYS.every((key) => HASH.test(String(currentContext[key] ?? '')) && currentContext[key] === binding[key]);
  if (!sceneBindingValid || !digestFieldsValid || !currentContextValid) return { ok: false, issues: ['human_review_binding_invalid'] };
  return validateHumanGateReceipt(
    bundle.receipt,
    binding,
    { ownerResolutionReceipt: bundle.ownerResolutionReceipt, approvalLedgerReceipt: bundle.approvalLedgerReceipt },
    bundle.asOf,
  );
}
