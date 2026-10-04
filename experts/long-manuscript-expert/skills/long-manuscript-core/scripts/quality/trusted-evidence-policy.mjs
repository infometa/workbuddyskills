import crypto from 'node:crypto';
import { stableJson } from '../lib/kernel-utils.mjs';

// Verification-only package policy. The private key and signer never enter the
// distributable package; repo-only fixture builders or an external authority
// issue receipts. Ed25519 signatures are encoded as base64url in receiptDigest.
const POLICY_PUBLIC_KEY = crypto.createPublicKey(`-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAe8RPAroxdikQy4StpsncUQc0RSEsJnH9f81sSjFJiPQ=
-----END PUBLIC KEY-----`);
const POLICY_VERSION = 'manuscriptos.trusted-evidence.v1';

export const trustedEvidencePolicyDigest = crypto
  .createHash('sha256')
  .update(`${POLICY_VERSION}\0${POLICY_PUBLIC_KEY.export({ type: 'spki', format: 'der' }).toString('hex')}`, 'utf8')
  .digest('hex');

function signedBytes(namespace, payload) {
  return Buffer.from(`${POLICY_VERSION}\0${namespace}\0${stableJson(payload)}`, 'utf8');
}

export function verifyTrustedPolicyReceipt(namespace, payload, receiptDigest) {
  if (typeof namespace !== 'string' || !namespace || !/^[A-Za-z0-9_-]{80,96}$/u.test(String(receiptDigest ?? ''))) return false;
  try {
    return crypto.verify(null, signedBytes(namespace, payload), POLICY_PUBLIC_KEY, Buffer.from(String(receiptDigest), 'base64url'));
  } catch {
    return false;
  }
}

export function trustedPolicyRequest(namespace, payload) {
  return {
    schemaVersion: '1.0.0',
    namespace,
    policyDigest: trustedEvidencePolicyDigest,
    payload,
  };
}
