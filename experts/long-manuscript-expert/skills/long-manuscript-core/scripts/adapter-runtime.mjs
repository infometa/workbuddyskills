import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { sha256, stableJson } from './lib/kernel-utils.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCHEMA_VERSION = '1.1.0';
const MAX_APPROVAL_TTL_SECONDS = 300;
const MAX_TARGET_TTL_SECONDS = 120;
const HASH_PATTERN = /^[a-f0-9]{64}$/u;
const FORBIDDEN_KEYS = new Set([
  'id', 'uid', 'userid', 'openid', 'unionid', 'externaluserid', 'chatid', 'docid',
  'sessionid', 'sessiontoken', 'token', 'accesstoken', 'refreshtoken', 'secret',
  'credential', 'cookie', 'apikey', 'cursor', 'webhookurl',
]);
const PUBLIC_DIGEST_KEYS = new Set(['artifactdigest', 'bindingdigest', 'contentdigest', 'receiptdigest']);
const SAFE_FALLBACK = 'local_workflow_without_connector';

const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const sha = (value) => sha256(stableJson(value));
const bindingKey = (portId, operation) => `${portId}\u001f${operation}`;
const validHash = (value) => HASH_PATTERN.test(String(value ?? ''));
const normalizeScene = (value) => String(value ?? '').trim();
const normalizeLabel = (value) => String(value ?? '').trim();

function exactKeys(value, requiredKeys) {
  if (!isObject(value)) return false;
  const actual = Object.keys(value).sort();
  const expected = [...requiredKeys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function parseTime(value) {
  const time = Date.parse(String(value ?? ''));
  return Number.isFinite(time) ? time : null;
}

function validateTimeWindow({ issuedAt, expiresAt, observedAt = null }, nowValue, maximumTtlSeconds) {
  const issued = parseTime(issuedAt);
  const expires = parseTime(expiresAt);
  const observed = observedAt === null ? issued : parseTime(observedAt);
  const now = parseTime(nowValue);
  if ([issued, expires, observed, now].some((value) => value === null)) return false;
  if (observed > issued || issued > now || now >= expires) return false;
  return expires - issued <= maximumTtlSeconds * 1000;
}

function normalizeKey(key) {
  return String(key ?? '').replace(/[^a-z0-9]/giu, '').toLowerCase();
}

function forbiddenKey(key) {
  const normalized = normalizeKey(key);
  if (FORBIDDEN_KEYS.has(normalized)) return true;
  return /^(?:user|open|union|externaluser|chat|doc|session|message|conversation|corp|tenant|target|record|task|calendar)id$/u.test(normalized);
}

function suspiciousPublicValue(key, value) {
  if (typeof value !== 'string') return false;
  const normalizedKey = normalizeKey(key);
  if (PUBLIC_DIGEST_KEYS.has(normalizedKey) && validHash(value)) return false;
  return /^(?:wo|wm|ww|usr|user|chat|doc|corp|session)[_-]?[a-z0-9]{5,}$/iu.test(value)
    || /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/iu.test(value)
    || /^[A-Za-z0-9+/=_-]{28,}$/u.test(value);
}

let authorityCache = null;
function loadAuthority() {
  if (authorityCache) return authorityCache;
  const registryPath = path.resolve(__dirname, '../resources/capability-port-adapter-registry.json');
  if (!fs.existsSync(registryPath)) return null;
  const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
  const mappings = new Map();
  for (const port of registry.entries ?? []) {
    for (const mapping of port.providerBindings ?? []) {
      const key = bindingKey(mapping.portId, mapping.operation);
      if (mappings.has(key)) throw new Error(`duplicate_authoritative_binding:${key}`);
      mappings.set(key, mapping);
    }
  }
  authorityCache = { registry, registryDigest: sha(registry), mappings };
  return authorityCache;
}

let sceneCache = null;
function loadSceneCache() {
  if (sceneCache) return sceneCache;
  sceneCache = new Map();
  const registryPath = path.resolve(__dirname, '../resources/scene-registry.json');
  if (!fs.existsSync(registryPath)) return sceneCache;
  const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
  for (const row of registry.entries ?? []) {
    const sceneId = normalizeScene(row.sceneId);
    const scenePath = path.resolve(__dirname, '../scenes', `${sceneId}.json`);
    if (!sceneId || !fs.existsSync(scenePath)) continue;
    const pack = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
    const bindings = new Map();
    for (const binding of pack.optionalPortBindings ?? []) {
      const key = bindingKey(binding.portId, binding.operation);
      const items = bindings.get(key) ?? [];
      items.push(binding);
      bindings.set(key, items);
    }
    sceneCache.set(sceneId, { pack, bindings });
  }
  return sceneCache;
}

function resolveSceneBinding(sceneId, mapping, legacyLabel = null, purpose = null) {
  const scenes = loadSceneCache();
  const canonicalSceneId = normalizeScene(sceneId);
  const scene = scenes.get(canonicalSceneId);
  if (!scene) return { ok: false, digest: null, binding: null };
  if (mapping.bindingScope === 'product_control_binding') {
    const binding = {
      bindingScope: mapping.bindingScope,
      sceneId: canonicalSceneId,
      portId: mapping.portId,
      operation: mapping.operation,
    };
    return { ok: true, digest: sha(binding), binding };
  }
  if (mapping.bindingScope !== 'scene_optional_binding') return { ok: false, digest: null, binding: null };
  const candidates = scene.bindings.get(bindingKey(mapping.portId, mapping.operation)) ?? [];
  const requestedLegacy = normalizeLabel(legacyLabel);
  const requestedPurpose = normalizeLabel(purpose);
  const binding = candidates.find((candidate) => {
    const candidateLegacy = normalizeLabel(candidate.legacyLabel);
    const candidatePurpose = normalizeLabel(candidate.purpose);
    return (requestedLegacy && requestedLegacy === candidateLegacy)
      || (!requestedLegacy && requestedPurpose && (requestedPurpose === candidateLegacy || requestedPurpose === candidatePurpose));
  });
  return binding ? { ok: true, digest: sha(binding), binding } : { ok: false, digest: null, binding: null };
}

function expectedReceiptNamespace(intent) {
  return intent.adapterId === 'wecom' ? 'wecom_collaboration' : 'fbs_connector_receipt';
}

function allowedPublicFields(intent) {
  const mapping = loadAuthority()?.mappings.get(bindingKey(intent?.portId, intent?.operation));
  return new Set(mapping?.publicResultFields ?? []);
}

export function sanitizePublicResult(value, intent = null) {
  const allowed = intent ? allowedPublicFields(intent) : null;
  const visit = (item) => {
    if (Array.isArray(item)) return item.map(visit);
    if (!isObject(item)) return item;
    const output = {};
    for (const [key, nested] of Object.entries(item)) {
      if (forbiddenKey(key) || (allowed && !allowed.has(key))) continue;
      if (typeof nested === 'string' && suspiciousPublicValue(key, nested)) {
        output[key] = '[redacted]';
      } else {
        output[key] = visit(nested);
      }
    }
    return output;
  };
  return visit(value);
}

export function hasForbiddenPublicFields(value, parentKey = '') {
  if (Array.isArray(value)) return value.some((item) => hasForbiddenPublicFields(item, parentKey));
  if (typeof value === 'string') return suspiciousPublicValue(parentKey, value);
  if (!isObject(value)) return false;
  return Object.entries(value).some(([key, item]) => forbiddenKey(key) || hasForbiddenPublicFields(item, key));
}

function sameBindingPolicyDigest(mapping, providerBindingDigest) {
  return sha({
    adapterId: mapping.adapterId,
    portId: mapping.portId,
    operation: mapping.operation,
    sameBindingRequired: Boolean(mapping.sameBindingRequired),
    providerBindingDigest,
  });
}

function bindingDigest(intent, targetResolutionReceipt) {
  return sha({
    intentDigest: intent.intentDigest,
    adapterId: intent.adapterId,
    portId: intent.portId,
    operation: intent.operation,
    providerBindingDigest: intent.providerBindingDigest,
    sceneBindingDigest: intent.sceneBindingDigest,
    sameBindingPolicyDigest: intent.sameBindingPolicyDigest,
    internalTargetDigest: targetResolutionReceipt?.internalTargetDigest ?? null,
    providerBindingFingerprintDigest: targetResolutionReceipt?.providerBindingFingerprintDigest ?? null,
    resolutionSnapshotDigest: targetResolutionReceipt?.resolutionSnapshotDigest ?? null,
    targetDescriptorDigest: intent.targetDescriptorDigest,
  });
}

export function computeBindingDigest(intent, targetResolutionReceipt) {
  return bindingDigest(intent, targetResolutionReceipt);
}

const INTENT_KEYS = [
  'schemaVersion', 'sceneId', 'portId', 'operation', 'adapterId', 'adapterOperation',
  'bindingScope', 'purpose', 'minimumDataScope', 'dataFields', 'targetDescriptorDigest',
  'payloadDigest', 'expectedReadbackDigest', 'idempotencyKeyDigest', 'providerRegistryDigest',
  'providerBindingDigest', 'sceneBindingDigest', 'sameBindingPolicyDigest', 'writeMode',
  'approvalRequired', 'readbackRequired', 'freshTargetResolutionRequired',
  'sameBindingRequired', 'fallback', 'executionAllowed', 'intentDigest',
];

export function validateAdapterIntent(intent) {
  if (!exactKeys(intent, INTENT_KEYS) || intent.schemaVersion !== SCHEMA_VERSION) return { ok: false, issue: 'intent_shape_invalid' };
  const { intentDigest, ...projection } = intent;
  if (!validHash(intentDigest) || sha(projection) !== intentDigest) return { ok: false, issue: 'intent_digest_invalid' };
  const authority = loadAuthority();
  const mapping = authority?.mappings.get(bindingKey(intent.portId, intent.operation));
  if (!authority || !mapping) return { ok: false, issue: 'intent_mapping_unknown' };
  if (intent.providerRegistryDigest !== authority.registryDigest || intent.providerBindingDigest !== sha(mapping)) return { ok: false, issue: 'intent_provider_binding_invalid' };
  const scalarMatches = intent.adapterId === mapping.adapterId
    && intent.adapterOperation === mapping.adapterOperation
    && intent.bindingScope === mapping.bindingScope
    && intent.writeMode === mapping.writeMode
    && intent.approvalRequired === Boolean(mapping.approvalRequired)
    && intent.readbackRequired === Boolean(mapping.readbackRequired)
    && intent.freshTargetResolutionRequired === Boolean(mapping.freshTargetResolutionRequired)
    && intent.sameBindingRequired === Boolean(mapping.sameBindingRequired)
    && intent.sameBindingPolicyDigest === sameBindingPolicyDigest(mapping, intent.providerBindingDigest)
    && intent.executionAllowed === false
    && intent.fallback === SAFE_FALLBACK;
  if (!scalarMatches) return { ok: false, issue: 'intent_authority_mismatch' };
  const sceneBinding = resolveSceneBinding(intent.sceneId, mapping, intent.purpose, intent.purpose);
  if (!sceneBinding.ok || sceneBinding.digest !== intent.sceneBindingDigest) return { ok: false, issue: 'intent_scene_binding_invalid' };
  if (!Array.isArray(intent.dataFields) || intent.dataFields.some((field) => typeof field !== 'string' || !field.trim())) return { ok: false, issue: 'intent_data_fields_invalid' };
  if (new Set(intent.dataFields).size !== intent.dataFields.length || [...intent.dataFields].sort().join('\u001f') !== intent.dataFields.join('\u001f')) return { ok: false, issue: 'intent_data_fields_not_canonical' };
  for (const digest of [intent.targetDescriptorDigest, intent.payloadDigest, intent.idempotencyKeyDigest, intent.providerRegistryDigest, intent.providerBindingDigest, intent.sceneBindingDigest, intent.sameBindingPolicyDigest]) {
    if (!validHash(digest)) return { ok: false, issue: 'intent_digest_field_invalid' };
  }
  if (intent.readbackRequired !== (intent.expectedReadbackDigest !== null)) return { ok: false, issue: 'intent_readback_binding_invalid' };
  if (intent.expectedReadbackDigest !== null && !validHash(intent.expectedReadbackDigest)) return { ok: false, issue: 'intent_readback_digest_invalid' };
  return { ok: true, issue: null, mapping };
}

export function createAdapterIntent(contract, request) {
  if (!isObject(contract) || !Array.isArray(contract.entries) || !isObject(request)) {
    return { ok: false, status: 'invalid_contract_or_request', issues: ['invalid_contract_or_request'], intent: null };
  }
  const authority = loadAuthority();
  const mapping = authority?.mappings.get(bindingKey(request.portId, request.operation));
  if (!mapping) return { ok: false, status: 'unknown_port_operation', issues: ['unknown_port_operation'], intent: null };
  const supplied = contract.entries.find((item) => item.portId === request.portId && item.operation === request.operation);
  if (!supplied || stableJson(supplied) !== stableJson(mapping)) {
    return { ok: false, status: 'invalid_contract_binding', issues: ['contract_binding_not_authoritative'], intent: null };
  }
  const sceneBinding = resolveSceneBinding(request.sceneId, mapping, request.legacyLabel, request.purpose);
  if (!sceneBinding.ok) return { ok: false, status: 'scene_binding_forbidden', issues: ['scene_binding_not_authorized'], intent: null };
  if (!Array.isArray(request.dataFields) || !Array.isArray(request.approvedFields)
      || request.dataFields.some((field) => typeof field !== 'string' || !field.trim())
      || request.approvedFields.some((field) => typeof field !== 'string' || !field.trim())
      || typeof request.minimumDataScope !== 'string' || !request.minimumDataScope.trim()
      || !isObject(request.targetDescriptor) || !isObject(request.payload)) {
    return { ok: false, status: 'invalid_request_shape', issues: ['invalid_request_shape'], intent: null };
  }
  if (mapping.readbackRequired && !isObject(request.expectedReadback)) {
    return { ok: false, status: 'expected_readback_required', issues: ['expected_readback_required'], intent: null };
  }
  const dataFields = [...new Set(request.dataFields)].sort();
  const approvedFields = new Set(request.approvedFields);
  const minimumScopeSatisfied = dataFields.every((field) => approvedFields.has(field));
  const targetDescriptorDigest = sha(request.targetDescriptor);
  const payloadDigest = sha(request.payload);
  const providerBindingDigest = sha(mapping);
  const idempotencyMaterial = String(request.idempotencyKey ?? sha({
    sceneId: request.sceneId,
    portId: mapping.portId,
    operation: mapping.operation,
    targetDescriptorDigest,
    payloadDigest,
  }));
  const projection = {
    schemaVersion: SCHEMA_VERSION,
    sceneId: normalizeScene(request.sceneId),
    portId: mapping.portId,
    operation: mapping.operation,
    adapterId: mapping.adapterId,
    adapterOperation: mapping.adapterOperation,
    bindingScope: mapping.bindingScope,
    purpose: normalizeLabel(request.legacyLabel ?? request.purpose),
    minimumDataScope: request.minimumDataScope,
    dataFields,
    targetDescriptorDigest,
    payloadDigest,
    expectedReadbackDigest: mapping.readbackRequired ? sha(request.expectedReadback) : null,
    idempotencyKeyDigest: sha({ idempotencyKey: idempotencyMaterial }),
    providerRegistryDigest: authority.registryDigest,
    providerBindingDigest,
    sceneBindingDigest: sceneBinding.digest,
    sameBindingPolicyDigest: sameBindingPolicyDigest(mapping, providerBindingDigest),
    writeMode: mapping.writeMode,
    approvalRequired: Boolean(mapping.approvalRequired),
    readbackRequired: Boolean(mapping.readbackRequired),
    freshTargetResolutionRequired: Boolean(mapping.freshTargetResolutionRequired),
    sameBindingRequired: Boolean(mapping.sameBindingRequired),
    fallback: SAFE_FALLBACK,
    executionAllowed: false,
  };
  const intent = { ...projection, intentDigest: sha(projection) };
  return minimumScopeSatisfied
    ? { ok: true, status: 'intent_ready', issues: [], intent }
    : { ok: false, status: 'scope_rejected', issues: ['minimum_data_scope_violation'], intent };
}

const APPROVAL_KEYS = [
  'schemaVersion', 'intentDigest', 'sceneId', 'portId', 'operation', 'adapterId',
  'humanOwner', 'decision', 'minimumDataScope', 'targetDescriptorDigest', 'requestDigest',
  'expectedReadbackDigest', 'idempotencyKeyDigest', 'providerBindingDigest',
  'sceneBindingDigest', 'approvalBindingDigest', 'issuedAt', 'expiresAt', 'nonce',
  'receiptDigest',
];

export function createApprovalReceipt(intent, humanOwner = 'current_user', options = {}) {
  if (!validateAdapterIntent(intent).ok || typeof humanOwner !== 'string' || !humanOwner.trim()) return null;
  if (typeof options.issuedAt !== 'string' || typeof options.nonce !== 'string') return null;
  const issuedAt = options.issuedAt;
  const issued = parseTime(issuedAt);
  const ttlSeconds = Number(options.ttlSeconds ?? MAX_APPROVAL_TTL_SECONDS);
  if (issued === null || !Number.isFinite(ttlSeconds) || ttlSeconds < 1 || ttlSeconds > MAX_APPROVAL_TTL_SECONDS) return null;
  const expiresAt = String(options.expiresAt ?? new Date(issued + ttlSeconds * 1000).toISOString());
  const nonce = options.nonce;
  if (!/^[a-z0-9_-]{16,128}$/iu.test(nonce)) return null;
  const payload = {
    schemaVersion: SCHEMA_VERSION,
    intentDigest: intent.intentDigest,
    sceneId: intent.sceneId,
    portId: intent.portId,
    operation: intent.operation,
    adapterId: intent.adapterId,
    humanOwner: humanOwner.trim(),
    decision: 'approved',
    minimumDataScope: intent.minimumDataScope,
    targetDescriptorDigest: intent.targetDescriptorDigest,
    requestDigest: sha({ payloadDigest: intent.payloadDigest, dataFields: intent.dataFields }),
    expectedReadbackDigest: intent.expectedReadbackDigest,
    idempotencyKeyDigest: intent.idempotencyKeyDigest,
    providerBindingDigest: intent.providerBindingDigest,
    sceneBindingDigest: intent.sceneBindingDigest,
    approvalBindingDigest: sha({
      intentDigest: intent.intentDigest,
      expectedReadbackDigest: intent.expectedReadbackDigest,
      idempotencyKeyDigest: intent.idempotencyKeyDigest,
      providerBindingDigest: intent.providerBindingDigest,
      sceneBindingDigest: intent.sceneBindingDigest,
    }),
    issuedAt,
    expiresAt,
    nonce,
  };
  return { ...payload, receiptDigest: sha(payload) };
}

export function validateApprovalReceipt(intent, receipt, options = {}) {
  if (!validateAdapterIntent(intent).ok || !exactKeys(receipt, APPROVAL_KEYS)) return false;
  if (receipt.schemaVersion !== SCHEMA_VERSION || receipt.decision !== 'approved' || !receipt.humanOwner?.trim()) return false;
  if (receipt.intentDigest !== intent.intentDigest || receipt.sceneId !== intent.sceneId || receipt.portId !== intent.portId
      || receipt.operation !== intent.operation || receipt.adapterId !== intent.adapterId
      || receipt.minimumDataScope !== intent.minimumDataScope || receipt.targetDescriptorDigest !== intent.targetDescriptorDigest
      || receipt.expectedReadbackDigest !== intent.expectedReadbackDigest || receipt.idempotencyKeyDigest !== intent.idempotencyKeyDigest
      || receipt.providerBindingDigest !== intent.providerBindingDigest || receipt.sceneBindingDigest !== intent.sceneBindingDigest) return false;
  if (receipt.requestDigest !== sha({ payloadDigest: intent.payloadDigest, dataFields: intent.dataFields })) return false;
  const expectedBinding = sha({
    intentDigest: intent.intentDigest,
    expectedReadbackDigest: intent.expectedReadbackDigest,
    idempotencyKeyDigest: intent.idempotencyKeyDigest,
    providerBindingDigest: intent.providerBindingDigest,
    sceneBindingDigest: intent.sceneBindingDigest,
  });
  if (receipt.approvalBindingDigest !== expectedBinding || !/^[a-z0-9_-]{16,128}$/iu.test(receipt.nonce)) return false;
  if (typeof options.now !== 'string' || !validateTimeWindow(receipt, options.now, options.maximumTtlSeconds ?? MAX_APPROVAL_TTL_SECONDS)) return false;
  const { receiptDigest, ...payload } = receipt;
  return validHash(receiptDigest) && sha(payload) === receiptDigest;
}

const TARGET_KEYS = [
  'schemaVersion', 'sceneId', 'portId', 'operation', 'adapterId', 'readableTarget',
  'targetDescriptorDigest', 'internalTargetDigest', 'providerBindingFingerprintDigest',
  'resolutionSnapshotDigest', 'intentDigest', 'bindingTargetDigest', 'observedAt',
  'issuedAt', 'expiresAt', 'receiptDigest',
];

export function createTargetResolutionReceipt(intent, readableTarget, internalTargetDigest, observedAt, options = {}) {
  if (!validateAdapterIntent(intent).ok || typeof readableTarget !== 'string' || !readableTarget.trim()
      || suspiciousPublicValue('targetLabel', readableTarget) || !validHash(internalTargetDigest)
      || !validHash(options.providerBindingFingerprintDigest) || !validHash(options.resolutionSnapshotDigest)) return null;
  if (typeof observedAt !== 'string') return null;
  const safeObservedAt = observedAt;
  const issuedAt = String(options.issuedAt ?? safeObservedAt);
  const issued = parseTime(issuedAt);
  const ttlSeconds = Number(options.ttlSeconds ?? MAX_TARGET_TTL_SECONDS);
  if (issued === null || !Number.isFinite(ttlSeconds) || ttlSeconds < 1 || ttlSeconds > MAX_TARGET_TTL_SECONDS) return null;
  const expiresAt = String(options.expiresAt ?? new Date(issued + ttlSeconds * 1000).toISOString());
  const payload = {
    schemaVersion: SCHEMA_VERSION,
    sceneId: intent.sceneId,
    portId: intent.portId,
    operation: intent.operation,
    adapterId: intent.adapterId,
    readableTarget: readableTarget.trim(),
    targetDescriptorDigest: intent.targetDescriptorDigest,
    internalTargetDigest: String(internalTargetDigest),
    providerBindingFingerprintDigest: String(options.providerBindingFingerprintDigest),
    resolutionSnapshotDigest: String(options.resolutionSnapshotDigest),
    intentDigest: intent.intentDigest,
    bindingTargetDigest: bindingDigest(intent, {
      internalTargetDigest,
      providerBindingFingerprintDigest: options.providerBindingFingerprintDigest,
      resolutionSnapshotDigest: options.resolutionSnapshotDigest,
    }),
    observedAt: safeObservedAt,
    issuedAt,
    expiresAt,
  };
  return { ...payload, receiptDigest: sha(payload) };
}

export function validateTargetResolutionReceipt(intent, receipt, options = {}) {
  if (!validateAdapterIntent(intent).ok || !exactKeys(receipt, TARGET_KEYS)) return false;
  if (receipt.schemaVersion !== SCHEMA_VERSION || !receipt.readableTarget?.trim() || suspiciousPublicValue('targetLabel', receipt.readableTarget)) return false;
  if (receipt.sceneId !== intent.sceneId || receipt.portId !== intent.portId || receipt.operation !== intent.operation
      || receipt.adapterId !== intent.adapterId || receipt.intentDigest !== intent.intentDigest
      || receipt.targetDescriptorDigest !== intent.targetDescriptorDigest) return false;
  if (![receipt.internalTargetDigest, receipt.providerBindingFingerprintDigest, receipt.resolutionSnapshotDigest].every(validHash)) return false;
  if (receipt.bindingTargetDigest !== bindingDigest(intent, receipt)) return false;
  if (typeof options.now !== 'string' || !validateTimeWindow(receipt, options.now, options.maximumTtlSeconds ?? MAX_TARGET_TTL_SECONDS)) return false;
  const { receiptDigest, ...payload } = receipt;
  return validHash(receiptDigest) && sha(payload) === receiptDigest;
}

const NONCE_CONSUMPTION_KEYS = [
  'schemaVersion', 'ledgerNamespace', 'ledgerFingerprintDigest', 'nonce',
  'intentDigest', 'idempotencyKeyDigest', 'approvalReceiptDigest', 'consumedAt',
  'decision', 'receiptDigest',
];

function nonceConsumptionRequest(intent, approvalReceipt, ledger, consumedAt) {
  return {
    schemaVersion: SCHEMA_VERSION,
    ledgerNamespace: ledger.namespace,
    ledgerFingerprintDigest: ledger.fingerprintDigest,
    nonce: approvalReceipt.nonce,
    intentDigest: intent.intentDigest,
    idempotencyKeyDigest: intent.idempotencyKeyDigest,
    approvalReceiptDigest: approvalReceipt.receiptDigest,
    consumedAt,
    decision: 'consumed',
  };
}

export function validateNonceConsumptionReceipt(receipt, intent, approvalReceipt, ledger, now) {
  if (!exactKeys(receipt, NONCE_CONSUMPTION_KEYS) || !validateAdapterIntent(intent).ok || !isObject(approvalReceipt) || !isObject(ledger)) return false;
  if (receipt.schemaVersion !== SCHEMA_VERSION || receipt.ledgerNamespace !== ledger.namespace
      || receipt.ledgerFingerprintDigest !== ledger.fingerprintDigest || receipt.nonce !== approvalReceipt.nonce
      || receipt.intentDigest !== intent.intentDigest || receipt.idempotencyKeyDigest !== intent.idempotencyKeyDigest
      || receipt.approvalReceiptDigest !== approvalReceipt.receiptDigest || receipt.decision !== 'consumed'
      || receipt.consumedAt !== now || !/^[a-z0-9][a-z0-9._:-]{2,127}$/iu.test(receipt.ledgerNamespace)
      || !validHash(receipt.ledgerFingerprintDigest) || parseTime(receipt.consumedAt) === null) return false;
  const { receiptDigest, ...payload } = receipt;
  return validHash(receiptDigest) && sha(payload) === receiptDigest;
}

async function consumeApprovalNonce(intent, execution, now) {
  const ledger = execution.approvalNonceLedger;
  if (!isObject(ledger) || typeof ledger.consume !== 'function' || !/^[a-z0-9][a-z0-9._:-]{2,127}$/iu.test(String(ledger.namespace ?? '')) || !validHash(ledger.fingerprintDigest)) {
    return { ok: false, status: 'approval_replay_guard_required', issue: 'durable_nonce_ledger_required', receipt: null };
  }
  const request = nonceConsumptionRequest(intent, execution.approvalReceipt, ledger, now);
  let outcome;
  try { outcome = await ledger.consume(request); }
  catch { return { ok: false, status: 'approval_replay_guard_required', issue: 'durable_nonce_ledger_unavailable', receipt: null }; }
  if (outcome?.ok === false && outcome?.status === 'already_consumed') return { ok: false, status: 'approval_replay_blocked', issue: 'approval_nonce_already_consumed', receipt: null };
  if (outcome?.ok !== true || !validateNonceConsumptionReceipt(outcome.receipt, intent, execution.approvalReceipt, ledger, now)) {
    return { ok: false, status: 'approval_replay_guard_required', issue: 'nonce_consumption_receipt_invalid', receipt: null };
  }
  return { ok: true, status: 'consumed', issue: null, receipt: outcome.receipt };
}

function outputFor(intent, {
  dispatchCount = 0,
  confirmedCount = 0,
  readCount = 0,
  writeCount = 0,
  localWorkflowContinues = true,
  publicResult = null,
  reconciliationRequired = false,
  externalReplayBlocked = false,
} = {}) {
  return {
    adapterId: intent?.adapterId ?? null,
    portId: intent?.portId ?? null,
    operation: intent?.operation ?? null,
    intentDigest: intent?.intentDigest ?? null,
    fallback: intent?.fallback ?? SAFE_FALLBACK,
    connectorRequired: false,
    donorSkillUsed: false,
    blindRetryAllowed: false,
    externalDispatchCount: dispatchCount,
    externalActionCount: confirmedCount,
    externalReadCount: readCount,
    externalWriteCount: writeCount,
    externalReplayBlocked,
    reconciliationRequired,
    localWorkflowContinues,
    publicResult,
  };
}

const RECONCILIATION_KEYS = [
  'schemaVersion', 'receiptNamespace', 'adapterId', 'portId', 'operation', 'sceneId',
  'intentDigest', 'idempotencyKeyDigest', 'providerBindingDigest', 'dispatchDigest',
  'nonceConsumptionReceiptDigest', 'reason', 'state', 'externalReplayBlocked', 'createdAt', 'receiptDigest',
];
const RECONCILIATION_REASONS = new Set([
  'provider_timeout_outcome_unknown',
  'provider_error_outcome_unknown',
  'invalid_provider_response_outcome_unknown',
  'provider_partial_success',
  'provider_failure_outcome_unknown',
  'provider_receipt_missing',
  'same_binding_receipt_required',
  'readback_mismatch_or_missing',
  'action_receipt_validation_failed',
  'public_projection_rejected_after_dispatch',
]);

function buildReconciliationReceipt(intent, reason, execution, createdAt) {
  const payload = {
    schemaVersion: SCHEMA_VERSION,
    receiptNamespace: expectedReceiptNamespace(intent),
    adapterId: intent.adapterId,
    portId: intent.portId,
    operation: intent.operation,
    sceneId: intent.sceneId,
    intentDigest: intent.intentDigest,
    idempotencyKeyDigest: intent.idempotencyKeyDigest,
    providerBindingDigest: intent.providerBindingDigest,
    nonceConsumptionReceiptDigest: execution.nonceConsumptionReceipt?.receiptDigest ?? null,
    dispatchDigest: sha({
      intentDigest: intent.intentDigest,
      approvalReceiptDigest: execution.approvalReceipt?.receiptDigest ?? null,
      targetResolutionReceiptDigest: execution.targetResolutionReceipt?.receiptDigest ?? null,
      idempotencyKeyDigest: intent.idempotencyKeyDigest,
    }),
    reason,
    state: 'required',
    externalReplayBlocked: true,
    createdAt,
  };
  return { ...payload, receiptDigest: sha(payload) };
}

export function validateReconciliationReceipt(receipt, intent, evidence = {}) {
  if (!validateAdapterIntent(intent).ok || !exactKeys(receipt, RECONCILIATION_KEYS)) return false;
  if (receipt.schemaVersion !== SCHEMA_VERSION || receipt.receiptNamespace !== expectedReceiptNamespace(intent)
      || receipt.adapterId !== intent.adapterId || receipt.portId !== intent.portId || receipt.operation !== intent.operation
      || receipt.sceneId !== intent.sceneId || receipt.intentDigest !== intent.intentDigest
      || receipt.idempotencyKeyDigest !== intent.idempotencyKeyDigest || receipt.providerBindingDigest !== intent.providerBindingDigest
      || receipt.state !== 'required' || receipt.externalReplayBlocked !== true || !parseTime(receipt.createdAt)
      || receipt.reason !== evidence.expectedReason || !RECONCILIATION_REASONS.has(receipt.reason)
      || receipt.createdAt !== evidence.dispatchCreatedAt) return false;
  const expectedDispatchDigest = sha({
    intentDigest: intent.intentDigest,
    approvalReceiptDigest: evidence.approvalReceipt?.receiptDigest ?? null,
    targetResolutionReceiptDigest: evidence.targetResolutionReceipt?.receiptDigest ?? null,
    idempotencyKeyDigest: intent.idempotencyKeyDigest,
  });
  if (receipt.dispatchDigest !== expectedDispatchDigest) return false;
  if (intent.approvalRequired) {
    if (!isObject(evidence.nonceConsumptionReceipt) || receipt.nonceConsumptionReceiptDigest !== evidence.nonceConsumptionReceipt.receiptDigest) return false;
    if (!validateNonceConsumptionReceipt(evidence.nonceConsumptionReceipt, intent, evidence.approvalReceipt, evidence.approvalNonceLedger, evidence.nonceConsumptionReceipt.consumedAt)) return false;
    if (!validateApprovalReceipt(intent, evidence.approvalReceipt, { now: evidence.dispatchCreatedAt })) return false;
  } else if (receipt.nonceConsumptionReceiptDigest !== null) return false;
  if (intent.freshTargetResolutionRequired && !validateTargetResolutionReceipt(intent, evidence.targetResolutionReceipt, { now: evidence.dispatchCreatedAt })) return false;
  const { receiptDigest, ...payload } = receipt;
  return validHash(receiptDigest) && sha(payload) === receiptDigest;
}

function unresolvedWrite(intent, status, issue, execution, now, publicResult = null) {
  const reconciliationReceipt = buildReconciliationReceipt(intent, issue, execution, now);
  return {
    ok: false,
    status,
    issues: [issue],
    output: outputFor(intent, {
      dispatchCount: 1,
      localWorkflowContinues: false,
      publicResult,
      reconciliationRequired: true,
      externalReplayBlocked: true,
    }),
    receipt: null,
    reconciliationReceipt,
  };
}

export async function executeAdapterIntent(intent, execution = {}) {
  const integrity = validateAdapterIntent(intent);
  if (!integrity.ok) return { ok: false, status: 'invalid_intent_integrity', issues: [integrity.issue], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  if (typeof execution.now !== 'string') return { ok: false, status: 'invalid_execution_clock', issues: ['trusted_execution_clock_required'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  const now = execution.now;
  if (parseTime(now) === null) return { ok: false, status: 'invalid_execution_clock', issues: ['trusted_execution_clock_required'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  if (execution.connectorAvailable !== true) return { ok: false, status: 'local_fallback', issues: ['connector_unavailable'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  if (!Number.isInteger(execution.timeoutMs) || execution.timeoutMs < 1000 || execution.timeoutMs > 30000) return { ok: false, status: 'invalid_timeout', issues: ['bounded_timeout_required'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  if (execution.discovery?.available !== true || (intent.adapterId === 'wecom' && (execution.discovery.authorizationStatus !== 'authorized' || execution.discovery.versionAtLeastMinimum !== true))) {
    return { ok: false, status: 'adapter_preflight_failed', issues: ['adapter_preflight_failed'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  }
  if (intent.approvalRequired && !validateApprovalReceipt(intent, execution.approvalReceipt, { now })) {
    return { ok: false, status: 'approval_required', issues: ['approval_receipt_invalid'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  }
  if (intent.freshTargetResolutionRequired && !validateTargetResolutionReceipt(intent, execution.targetResolutionReceipt, { now })) {
    return { ok: false, status: 'target_resolution_required', issues: ['fresh_target_resolution_required'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  }
  if (intent.freshTargetResolutionRequired && execution.discovery.bindingFingerprintDigest !== execution.targetResolutionReceipt.providerBindingFingerprintDigest) {
    return { ok: false, status: 'target_resolution_required', issues: ['discovery_binding_fingerprint_mismatch'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  }
  if (typeof execution.transport !== 'function') return { ok: false, status: 'local_fallback', issues: ['adapter_transport_unavailable'], output: outputFor(intent), receipt: null, reconciliationReceipt: null };
  if (intent.approvalRequired) {
    const consumption = await consumeApprovalNonce(intent, execution, now);
    if (!consumption.ok) return { ok: false, status: consumption.status, issues: [consumption.issue], output: outputFor(intent, { externalReplayBlocked: consumption.status === 'approval_replay_blocked' }), receipt: null, reconciliationReceipt: null };
    execution = { ...execution, nonceConsumptionReceipt: consumption.receipt };
  }

  const transportRequest = {
    adapterOperation: intent.adapterOperation,
    intentDigest: intent.intentDigest,
    providerBindingDigest: intent.providerBindingDigest,
    sceneBindingDigest: intent.sceneBindingDigest,
    idempotencyKeyDigest: intent.idempotencyKeyDigest,
    expectedReadbackDigest: intent.expectedReadbackDigest,
    approvalReceiptDigest: execution.approvalReceipt?.receiptDigest ?? null,
    targetResolutionReceiptDigest: execution.targetResolutionReceipt?.receiptDigest ?? null,
    timeoutMs: execution.timeoutMs,
  };
  let response;
  let timeoutHandle = null;
  try {
    response = await Promise.race([
      Promise.resolve(execution.transport(transportRequest)),
      new Promise((_, reject) => { timeoutHandle = setTimeout(() => reject(new Error('timeout')), execution.timeoutMs); }),
    ]);
  } catch (error) {
    if (intent.writeMode === 'external_write') return unresolvedWrite(intent, 'outcome_unknown', error.message === 'timeout' ? 'provider_timeout_outcome_unknown' : 'provider_error_outcome_unknown', execution, now);
    return { ok: false, status: error.message === 'timeout' ? 'timeout_fallback' : 'adapter_failed', issues: [error.message === 'timeout' ? 'adapter_timeout' : 'adapter_execution_failed'], output: outputFor(intent, { dispatchCount: 1 }), receipt: null, reconciliationReceipt: null };
  } finally {
    if (timeoutHandle !== null) clearTimeout(timeoutHandle);
  }
  if (!isObject(response)) {
    if (intent.writeMode === 'external_write') return unresolvedWrite(intent, 'outcome_unknown', 'invalid_provider_response_outcome_unknown', execution, now);
    return { ok: false, status: 'adapter_failed', issues: ['adapter_execution_failed'], output: outputFor(intent, { dispatchCount: 1 }), receipt: null, reconciliationReceipt: null };
  }
  const publicResult = sanitizePublicResult(response.publicResult ?? {}, intent);
  if (hasForbiddenPublicFields(publicResult)) {
    if (intent.writeMode === 'external_write') return unresolvedWrite(intent, 'projection_requires_reconciliation', 'public_projection_rejected_after_dispatch', execution, now);
    return { ok: false, status: 'public_result_rejected', issues: ['internal_identifier_exposure'], output: outputFor(intent, { dispatchCount: 1 }), receipt: null, reconciliationReceipt: null };
  }
  if (response.ok !== true) {
    if (intent.writeMode === 'external_write') {
      if (response.partial === true || response.status === 'partial_success') return unresolvedWrite(intent, 'partial_requires_reconciliation', 'provider_partial_success', execution, now, publicResult);
      if (response.outcome === 'rejected_before_action') return { ok: false, status: 'provider_rejected', issues: ['provider_rejected_before_action'], output: outputFor(intent, { dispatchCount: 1, publicResult }), receipt: null, reconciliationReceipt: null };
      return unresolvedWrite(intent, 'outcome_unknown', 'provider_failure_outcome_unknown', execution, now, publicResult);
    }
    return { ok: false, status: 'adapter_failed', issues: ['adapter_execution_failed'], output: outputFor(intent, { dispatchCount: 1, publicResult }), receipt: null, reconciliationReceipt: null };
  }
  if (intent.writeMode === 'external_write' && !validHash(response.providerReceiptDigest)) return unresolvedWrite(intent, 'outcome_unknown', 'provider_receipt_missing', execution, now, publicResult);
  if (intent.sameBindingRequired) {
    const target = execution.targetResolutionReceipt;
    if (response.providerBindingFingerprintDigest !== target?.providerBindingFingerprintDigest
        || response.bindingDigest !== bindingDigest(intent, target)) {
      return unresolvedWrite(intent, 'same_binding_mismatch', 'same_binding_receipt_required', execution, now, publicResult);
    }
  }
  if (intent.readbackRequired) {
    if (!isObject(response.readback) || sha(response.readback) !== intent.expectedReadbackDigest) return unresolvedWrite(intent, 'readback_requires_reconciliation', 'readback_mismatch_or_missing', execution, now, publicResult);
  }

  const receiptPayload = {
    schemaVersion: SCHEMA_VERSION,
    receiptNamespace: expectedReceiptNamespace(intent),
    adapterId: intent.adapterId,
    portId: intent.portId,
    operation: intent.operation,
    sceneId: intent.sceneId,
    intentDigest: intent.intentDigest,
    idempotencyKeyDigest: intent.idempotencyKeyDigest,
    providerRegistryDigest: intent.providerRegistryDigest,
    providerBindingDigest: intent.providerBindingDigest,
    sceneBindingDigest: intent.sceneBindingDigest,
    sameBindingPolicyDigest: intent.sameBindingPolicyDigest,
    requestDigest: sha(transportRequest),
    responseDigest: sha(response.publicResult ?? null),
    expectedReadbackDigest: intent.expectedReadbackDigest,
    readbackDigest: response.readback ? sha(response.readback) : null,
    providerReceiptDigest: response.providerReceiptDigest ?? null,
    providerBindingFingerprintDigest: response.providerBindingFingerprintDigest ?? execution.targetResolutionReceipt?.providerBindingFingerprintDigest ?? null,
    targetResolutionReceiptDigest: execution.targetResolutionReceipt?.receiptDigest ?? null,
    sameBindingDigest: bindingDigest(intent, execution.targetResolutionReceipt),
    approvalReceiptDigest: execution.approvalReceipt?.receiptDigest ?? null,
    nonceConsumptionReceiptDigest: execution.nonceConsumptionReceipt?.receiptDigest ?? null,
    externalDispatchCount: 1,
    externalActionCount: 1,
    externalReadCount: intent.writeMode === 'read_only' ? 1 : 0,
    externalWriteCount: intent.writeMode === 'external_write' ? 1 : 0,
    reconciliationState: 'not_required',
  };
  const receipt = { ...receiptPayload, receiptDigest: sha(receiptPayload) };
  if (!validateAdapterReceipt(receipt, intent, {
    approvalReceipt: execution.approvalReceipt,
    targetResolutionReceipt: execution.targetResolutionReceipt,
    readback: response.readback,
    providerReceiptDigest: response.providerReceiptDigest ?? null,
    providerBindingFingerprintDigest: response.providerBindingFingerprintDigest ?? execution.targetResolutionReceipt?.providerBindingFingerprintDigest ?? null,
    nonceConsumptionReceipt: execution.nonceConsumptionReceipt ?? null,
    approvalNonceLedger: execution.approvalNonceLedger ?? null,
    timeoutMs: execution.timeoutMs,
    providerPublicResult: response.publicResult ?? null,
  })) {
    if (intent.writeMode === 'external_write') return unresolvedWrite(intent, 'receipt_requires_reconciliation', 'action_receipt_validation_failed', execution, now, publicResult);
    return { ok: false, status: 'receipt_failed', issues: ['action_receipt_validation_failed'], output: outputFor(intent, { dispatchCount: 1, publicResult }), receipt: null, reconciliationReceipt: null };
  }
  return {
    ok: true,
    status: 'completed_with_receipt',
    issues: [],
    output: outputFor(intent, {
      dispatchCount: 1,
      confirmedCount: 1,
      readCount: intent.writeMode === 'read_only' ? 1 : 0,
      writeCount: intent.writeMode === 'external_write' ? 1 : 0,
      localWorkflowContinues: false,
      publicResult,
    }),
    receipt,
    reconciliationReceipt: null,
  };
}

const ACTION_RECEIPT_KEYS = [
  'schemaVersion', 'receiptNamespace', 'adapterId', 'portId', 'operation', 'sceneId',
  'intentDigest', 'idempotencyKeyDigest', 'providerRegistryDigest', 'providerBindingDigest',
  'sceneBindingDigest', 'sameBindingPolicyDigest', 'requestDigest', 'responseDigest',
  'expectedReadbackDigest', 'readbackDigest', 'providerReceiptDigest',
  'providerBindingFingerprintDigest', 'targetResolutionReceiptDigest', 'sameBindingDigest',
  'approvalReceiptDigest', 'nonceConsumptionReceiptDigest', 'externalDispatchCount', 'externalActionCount',
  'externalReadCount', 'externalWriteCount', 'reconciliationState', 'receiptDigest',
];

export function validateAdapterReceipt(receipt, intent, evidence = {}) {
  if (!validateAdapterIntent(intent).ok || !exactKeys(receipt, ACTION_RECEIPT_KEYS)) return false;
  if (receipt.schemaVersion !== SCHEMA_VERSION || receipt.receiptNamespace !== expectedReceiptNamespace(intent)
      || receipt.adapterId !== intent.adapterId || receipt.portId !== intent.portId || receipt.operation !== intent.operation
      || receipt.sceneId !== intent.sceneId || receipt.intentDigest !== intent.intentDigest
      || receipt.idempotencyKeyDigest !== intent.idempotencyKeyDigest || receipt.providerRegistryDigest !== intent.providerRegistryDigest
      || receipt.providerBindingDigest !== intent.providerBindingDigest || receipt.sceneBindingDigest !== intent.sceneBindingDigest
      || receipt.sameBindingPolicyDigest !== intent.sameBindingPolicyDigest || receipt.expectedReadbackDigest !== intent.expectedReadbackDigest
      || receipt.reconciliationState !== 'not_required' || receipt.externalDispatchCount !== 1 || receipt.externalActionCount !== 1
      || receipt.externalReadCount !== (intent.writeMode === 'read_only' ? 1 : 0)
      || receipt.externalWriteCount !== (intent.writeMode === 'external_write' ? 1 : 0)) return false;
  if (intent.approvalRequired) {
    if (!isObject(evidence.approvalReceipt) || receipt.approvalReceiptDigest !== evidence.approvalReceipt.receiptDigest) return false;
    if (!isObject(evidence.nonceConsumptionReceipt) || receipt.nonceConsumptionReceiptDigest !== evidence.nonceConsumptionReceipt.receiptDigest) return false;
    if (!validateNonceConsumptionReceipt(evidence.nonceConsumptionReceipt, intent, evidence.approvalReceipt, evidence.approvalNonceLedger, evidence.nonceConsumptionReceipt.consumedAt)) return false;
  } else if (receipt.approvalReceiptDigest !== null || receipt.nonceConsumptionReceiptDigest !== null) return false;
  if (intent.freshTargetResolutionRequired) {
    if (!isObject(evidence.targetResolutionReceipt) || receipt.targetResolutionReceiptDigest !== evidence.targetResolutionReceipt.receiptDigest
        || receipt.sameBindingDigest !== bindingDigest(intent, evidence.targetResolutionReceipt)) return false;
  } else if (receipt.targetResolutionReceiptDigest !== null) return false;
  if (intent.readbackRequired) {
    if (!isObject(evidence.readback) || receipt.readbackDigest !== sha(evidence.readback) || receipt.readbackDigest !== intent.expectedReadbackDigest) return false;
  } else if (receipt.readbackDigest !== null || receipt.expectedReadbackDigest !== null) return false;
  if (intent.writeMode === 'external_write') {
    if (!validHash(evidence.providerReceiptDigest) || receipt.providerReceiptDigest !== evidence.providerReceiptDigest) return false;
  } else if (receipt.providerReceiptDigest !== null) return false;
  if (intent.sameBindingRequired && receipt.providerBindingFingerprintDigest !== evidence.targetResolutionReceipt?.providerBindingFingerprintDigest) return false;
  const expectedTransportRequest = {
    adapterOperation: intent.adapterOperation,
    intentDigest: intent.intentDigest,
    providerBindingDigest: intent.providerBindingDigest,
    sceneBindingDigest: intent.sceneBindingDigest,
    idempotencyKeyDigest: intent.idempotencyKeyDigest,
    expectedReadbackDigest: intent.expectedReadbackDigest,
    approvalReceiptDigest: evidence.approvalReceipt?.receiptDigest ?? null,
    targetResolutionReceiptDigest: evidence.targetResolutionReceipt?.receiptDigest ?? null,
    timeoutMs: evidence.timeoutMs,
  };
  if (!Number.isInteger(evidence.timeoutMs) || receipt.requestDigest !== sha(expectedTransportRequest) || receipt.responseDigest !== sha(evidence.providerPublicResult ?? null)) return false;
  for (const digest of [receipt.requestDigest, receipt.responseDigest, receipt.idempotencyKeyDigest, receipt.providerRegistryDigest, receipt.providerBindingDigest, receipt.sceneBindingDigest, receipt.sameBindingPolicyDigest, receipt.sameBindingDigest]) {
    if (!validHash(digest)) return false;
  }
  for (const nullableDigest of [receipt.readbackDigest, receipt.providerReceiptDigest, receipt.providerBindingFingerprintDigest, receipt.targetResolutionReceiptDigest, receipt.approvalReceiptDigest, receipt.nonceConsumptionReceiptDigest]) {
    if (nullableDigest !== null && !validHash(nullableDigest)) return false;
  }
  const { receiptDigest, ...payload } = receipt;
  return validHash(receiptDigest) && sha(payload) === receiptDigest;
}
