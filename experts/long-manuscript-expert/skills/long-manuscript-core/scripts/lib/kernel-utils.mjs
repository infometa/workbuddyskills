import crypto from 'node:crypto';

export function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === 'object') {
    const output = {};
    for (const key of Object.keys(value).sort()) output[key] = canonicalize(value[key]);
    return output;
  }
  return value;
}

export function stableJson(value) {
  return JSON.stringify(canonicalize(value));
}

export function sha256(value) {
  return crypto.createHash('sha256').update(Buffer.isBuffer(value) ? value : Buffer.from(String(value), 'utf8')).digest('hex');
}

export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export function unique(values) {
  return [...new Set(values)].sort((a, b) => String(a).localeCompare(String(b), 'en'));
}

export function riskMax(values) {
  const order = ['low', 'medium', 'high', 'restricted'];
  return asArray(values).reduce((current, value) => order.indexOf(value) > order.indexOf(current) ? value : current, 'low');
}

export function escapeHtml(value) {
  return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}

export function measuredWords(value) {
  const text = String(value ?? '').trim();
  if (!text) return 0;
  const latin = text.match(/[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*/gu) ?? [];
  const han = text.match(/[\p{Script=Han}]/gu) ?? [];
  return latin.length + han.length;
}

export function capabilityResult(capabilityId, input, { status = 'completed', ok = true, output = {}, issues = [], warnings = [] } = {}) {
  const normalizedIssues = unique(asArray(issues).map(String));
  const normalizedWarnings = unique(asArray(warnings).map(String));
  const payload = {
    capabilityId,
    status,
    ok: Boolean(ok),
    output,
    issues: normalizedIssues,
    warnings: normalizedWarnings
  };
  return payload;
}

export function normalizeCapabilityContext(context = {}) {
  return {
    connectorAvailable: Boolean(context?.connectorAvailable),
    externalWriteAuthorized: Boolean(context?.externalWriteAuthorized)
  };
}

export const capabilityRuntimePolicyDigest = sha256(stableJson({
  schemaVersion: '1.0.0',
  runtimeSelfContained: true,
  connectorRequired: false,
  donorSkillRequired: false,
  externalActionCount: 0
}));

export function sealCapabilityResult(capabilityId, input, context, result) {
  const normalizedContext = normalizeCapabilityContext(context);
  const payload = {
    capabilityId: result?.capabilityId,
    status: result?.status,
    ok: result?.ok,
    output: result?.output,
    issues: unique(asArray(result?.issues).map(String)),
    warnings: unique(asArray(result?.warnings).map(String)),
    context: normalizedContext
  };
  return {
    ...payload,
    receipt: {
      schemaVersion: '1.1.0',
      capabilityId,
      inputDigest: sha256(stableJson(input ?? {})),
      contextDigest: sha256(stableJson(normalizedContext)),
      invocationDigest: sha256(stableJson({ capabilityId, input: input ?? {}, context: normalizedContext })),
      policyDigest: capabilityRuntimePolicyDigest,
      resultDigest: sha256(stableJson(payload)),
      externalActionCount: 0,
      connectorRequired: false,
      donorSkillUsed: false
    }
  };
}
