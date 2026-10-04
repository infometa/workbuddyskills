import { sha256, stableJson } from '../lib/kernel-utils.mjs';
import { trustedEvidencePolicyDigest, trustedPolicyRequest, verifyTrustedPolicyReceipt } from './trusted-evidence-policy.mjs';

const HASH = /^[a-f0-9]{64}$/u;
const sha = (value) => sha256(stableJson(value));
const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const exactKeys = (value, keys) => isObject(value) && Object.keys(value).sort().join(',') === [...keys].sort().join(',');
const validHash = (value) => HASH.test(String(value ?? ''));
const OWNER_KEYS = ['schemaVersion', 'sceneId', 'humanOwnerRole', 'reviewerIdentityDigest', 'reviewScopeDigest', 'receiptDigest'];
const LEDGER_KEYS = ['schemaVersion', 'ledgerNamespace', 'ledgerFingerprintDigest', 'nonce', 'humanInvocationDigest', 'consumedAt', 'decision', 'receiptDigest'];
const HUMAN_KEYS = ['schemaVersion', 'gateId', 'parameterProfile', 'sceneId', 'humanOwnerRole', 'reviewerIdentityDigest', 'reviewMandate', 'gateInvocationDigest', 'machineGateResultDigest', 'scenePackDigest', 'projectStateDigest', 'artifactSetDigest', 'evidenceSnapshotDigest', 'reviewScopeDigest', 'decision', 'issuedAt', 'expiresAt', 'nonce', 'ownerResolutionReceiptDigest', 'approvalLedgerReceiptDigest', 'commentsDigest', 'receiptDigest'];

function humanInvocationDigest(binding) {
  return sha({
    gateId: 'human-review.receipt', parameterProfile: binding.parameterProfile, sceneId: binding.sceneId,
    humanOwner: binding.humanOwner, reviewMandate: binding.reviewMandate,
    gateInvocationDigest: binding.gateInvocationDigest, machineGateResultDigest: binding.machineGateResultDigest,
    scenePackDigest: binding.scenePackDigest, projectStateDigest: binding.projectStateDigest,
    artifactSetDigest: binding.artifactSetDigest, evidenceSnapshotDigest: binding.evidenceSnapshotDigest,
    reviewScopeDigest: binding.reviewScopeDigest, policyDigest: trustedEvidencePolicyDigest,
  });
}

// Package runtime creates unsigned requests only. The private key and signer
// live outside the distributable package.
export function createOwnerResolutionRequest({ sceneId, humanOwnerRole, reviewerIdentityDigest, reviewScopeDigest } = {}) {
  const payload = { schemaVersion: '1.0.0', sceneId, humanOwnerRole, reviewerIdentityDigest, reviewScopeDigest };
  return sceneId && humanOwnerRole && validHash(reviewerIdentityDigest) && validHash(reviewScopeDigest)
    ? trustedPolicyRequest('human.owner-resolution', payload) : null;
}

export function createApprovalLedgerRequest(binding, { ledgerNamespace, ledgerFingerprintDigest, nonce, consumedAt } = {}) {
  if (!binding || !/^[a-z0-9][a-z0-9._:-]{2,127}$/iu.test(String(ledgerNamespace ?? '')) || !/^[A-Za-z0-9_-]{16,128}$/u.test(String(nonce ?? '')) || !validHash(ledgerFingerprintDigest) || Number.isNaN(Date.parse(consumedAt))) return null;
  return trustedPolicyRequest('human.approval-ledger', { schemaVersion: '1.0.0', ledgerNamespace, ledgerFingerprintDigest, nonce, humanInvocationDigest: humanInvocationDigest(binding), consumedAt, decision: 'consumed' });
}

export function createHumanGateRequest(binding, evidence, options = {}) {
  const owner = evidence?.ownerResolutionReceipt; const ledger = evidence?.approvalLedgerReceipt;
  if (!binding || !owner || !ledger) return null;
  const payload = {
    schemaVersion: '1.0.0', gateId: 'human-review.receipt', parameterProfile: binding.parameterProfile,
    sceneId: binding.sceneId, humanOwnerRole: binding.humanOwner, reviewerIdentityDigest: owner.reviewerIdentityDigest,
    reviewMandate: binding.reviewMandate, gateInvocationDigest: binding.gateInvocationDigest,
    machineGateResultDigest: binding.machineGateResultDigest, scenePackDigest: binding.scenePackDigest,
    projectStateDigest: binding.projectStateDigest, artifactSetDigest: binding.artifactSetDigest,
    evidenceSnapshotDigest: binding.evidenceSnapshotDigest, reviewScopeDigest: binding.reviewScopeDigest,
    decision: 'approved', issuedAt: options.issuedAt, expiresAt: options.expiresAt, nonce: options.nonce,
    ownerResolutionReceiptDigest: owner.receiptDigest, approvalLedgerReceiptDigest: ledger.receiptDigest,
    commentsDigest: options.commentsDigest,
  };
  if ([payload.gateInvocationDigest, payload.machineGateResultDigest, payload.scenePackDigest, payload.projectStateDigest, payload.artifactSetDigest, payload.evidenceSnapshotDigest, payload.reviewScopeDigest, payload.reviewerIdentityDigest, payload.commentsDigest].some((value) => !validHash(value))) return null;
  return trustedPolicyRequest(`human.gate:${binding.parameterProfile}`, payload);
}

// Compatibility names deliberately return requests, never acceptable receipts.
export const createOwnerResolutionReceipt = createOwnerResolutionRequest;
export const createApprovalLedgerReceipt = (input) => trustedPolicyRequest('human.approval-ledger', input ?? {});
export const createHumanGateReceipt = createHumanGateRequest;

export function validateHumanGateReceipt(receipt, binding, evidence, asOf) {
  if (!exactKeys(receipt, HUMAN_KEYS) || receipt.schemaVersion !== '1.0.0' || receipt.gateId !== 'human-review.receipt' || receipt.decision !== 'approved' || !binding) return { ok: false, issues: ['human_receipt_shape_invalid'] };
  const owner = evidence?.ownerResolutionReceipt; const ledger = evidence?.approvalLedgerReceipt;
  if (!exactKeys(owner, OWNER_KEYS) || !exactKeys(ledger, LEDGER_KEYS)) return { ok: false, issues: ['trusted_human_authority_required'] };
  const ownerPayload = { schemaVersion: owner.schemaVersion, sceneId: owner.sceneId, humanOwnerRole: owner.humanOwnerRole, reviewerIdentityDigest: owner.reviewerIdentityDigest, reviewScopeDigest: owner.reviewScopeDigest };
  const ledgerPayload = { schemaVersion: ledger.schemaVersion, ledgerNamespace: ledger.ledgerNamespace, ledgerFingerprintDigest: ledger.ledgerFingerprintDigest, nonce: ledger.nonce, humanInvocationDigest: ledger.humanInvocationDigest, consumedAt: ledger.consumedAt, decision: ledger.decision };
  const humanPayload = { ...receipt }; delete humanPayload.receiptDigest;
  const ownerValid = verifyTrustedPolicyReceipt('human.owner-resolution', ownerPayload, owner.receiptDigest);
  const ledgerValid = ledger.decision === 'consumed' && ledger.humanInvocationDigest === humanInvocationDigest(binding) && verifyTrustedPolicyReceipt('human.approval-ledger', ledgerPayload, ledger.receiptDigest);
  const issued = Date.parse(receipt.issuedAt); const expires = Date.parse(receipt.expiresAt); const current = Date.parse(asOf);
  const bindingValid = receipt.parameterProfile === binding.parameterProfile && receipt.sceneId === binding.sceneId && receipt.humanOwnerRole === binding.humanOwner && receipt.reviewMandate === binding.reviewMandate && receipt.gateInvocationDigest === binding.gateInvocationDigest && receipt.machineGateResultDigest === binding.machineGateResultDigest && receipt.scenePackDigest === binding.scenePackDigest && receipt.projectStateDigest === binding.projectStateDigest && receipt.artifactSetDigest === binding.artifactSetDigest && receipt.evidenceSnapshotDigest === binding.evidenceSnapshotDigest && receipt.reviewScopeDigest === binding.reviewScopeDigest;
  const evidenceValid = ownerValid && ledgerValid && receipt.ownerResolutionReceiptDigest === owner.receiptDigest && receipt.approvalLedgerReceiptDigest === ledger.receiptDigest && receipt.reviewerIdentityDigest === owner.reviewerIdentityDigest && receipt.nonce === ledger.nonce;
  const timeValid = [issued, expires, current].every(Number.isFinite) && issued <= current && current < expires && expires - issued <= 15 * 60 * 1000 && Date.parse(ledger.consumedAt) === issued;
  const signatureValid = verifyTrustedPolicyReceipt(`human.gate:${binding.parameterProfile}`, humanPayload, receipt.receiptDigest);
  const ok = bindingValid && evidenceValid && timeValid && signatureValid;
  return { ok, issues: ok ? [] : ['human_review_receipt_invalid'] };
}
