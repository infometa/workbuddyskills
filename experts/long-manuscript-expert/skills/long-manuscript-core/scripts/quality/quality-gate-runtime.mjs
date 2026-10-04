import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { sha256, stableJson, unique } from '../lib/kernel-utils.mjs';
import { inspectBinaryArtifact } from './binary-artifact-inspector.mjs';
import { trustedEvidencePolicyDigest, verifyTrustedPolicyReceipt } from './trusted-evidence-policy.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REGISTRY_PATH = path.resolve(__dirname, '../../resources/gates/evaluator-registry.json');
const SCENE_REGISTRY_PATH = path.resolve(__dirname, '../../resources/scene-registry.json');
const SCHEMA_VERSION = '1.0.0';
const HASH = /^[a-f0-9]{64}$/u;
const STATUSES = new Set(['passed', 'failed', 'needs_input', 'needs_human_review', 'evaluator_unavailable', 'error']);
const EVIDENCE_KEYS = [
  'schemaVersion', 'sceneId', 'projectStateDigest', 'artifactSetDigest', 'asOf', 'artifacts',
  'requiredInputs', 'providedInputs', 'sources', 'claims', 'classifications', 'sensitiveItems',
  'coverage', 'entities', 'examples', 'externalActions', 'metrics', 'anonymization', 'consents',
  'fieldScope', 'projections', 'references', 'relationships', 'rights', 'risks', 'hazards',
  'schemaChecks', 'scopeLock', 'events', 'temporalPolicy', 'versions', 'voice', 'workflow',
  'deliveryManifest', 'semanticReviews',
];
const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const exactKeys = (value, keys) => isObject(value) && Object.keys(value).sort().join(',') === [...keys].sort().join(',');
const sha = (value) => sha256(stableJson(value));
const validHash = (value) => HASH.test(String(value ?? ''));
const safePath = (value) => typeof value === 'string' && value.length > 0 && !value.includes('\\') && !value.startsWith('/') && !/^[A-Za-z]:/u.test(value) && value.split('/').every((segment) => segment && segment !== '.' && segment !== '..');

let registryCache = null;
function loadRegistry() {
  if (!registryCache) {
    registryCache = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
    const seedPath = path.resolve(path.dirname(REGISTRY_PATH), String(registryCache.seedRegistryPath ?? ''));
    const expectedSeedPath = path.resolve(__dirname, '../../resources/scene-quality-gate-registry.json');
    const seedValid = seedPath === expectedSeedPath && fs.existsSync(seedPath) && registryCache.seedRegistrySha256 === sha256(fs.readFileSync(seedPath));
    const registryValid = registryCache.artifactType === 'active_quality_evaluator_registry' && registryCache.activeEvaluatorCount === 32 && registryCache.pendingEvaluatorCount === 0 && registryCache.entryCount === 32 && Array.isArray(registryCache.entries) && registryCache.entries.length === 32 && new Set(registryCache.entries.map((item) => item.gateId)).size === 32 && registryCache.entries.every((item) => item.lifecycle === 'active');
    if (!seedValid || !registryValid) throw new Error('quality_evaluator_registry_integrity_failed');
  }
  return registryCache;
}

function evidenceShapeIssues(evidence) {
  const issues = [];
  const dateTimeValid = (value) => /^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])[Tt](?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/u.test(value) && !Number.isNaN(Date.parse(value));
  const typeMatches = (value, type) => {
    if (type === 'null') return value === null;
    if (type === 'array') return Array.isArray(value);
    if (type === 'object') return isObject(value);
    if (type === 'integer') return typeof value === 'number' && Number.isInteger(value);
    if (type === 'number') return typeof value === 'number' && Number.isFinite(value);
    return typeof value === type;
  };
  const validate = (value, schema, location) => {
    const found = [];
    if (schema === true) return found;
    if (schema === false || !isObject(schema)) return [`gate_evidence_schema_invalid:${location}`];
    if (Array.isArray(schema.anyOf)) {
      if (!schema.anyOf.some((branch) => validate(value, branch, location).length === 0)) found.push(`gate_evidence_schema_any_of:${location}`);
    }
    if (Object.hasOwn(schema, 'const') && stableJson(value) !== stableJson(schema.const)) found.push(`gate_evidence_schema_const:${location}`);
    if (Array.isArray(schema.enum) && !schema.enum.some((candidate) => stableJson(value) === stableJson(candidate))) found.push(`gate_evidence_schema_enum:${location}`);
    if (Object.hasOwn(schema, 'type')) {
      const types = Array.isArray(schema.type) ? schema.type : [schema.type];
      if (!types.every((type) => typeof type === 'string') || !types.some((type) => typeMatches(value, type))) {
        found.push(`gate_evidence_schema_type:${location}`);
        return found;
      }
    }
    if (typeof value === 'string') {
      if (Number.isInteger(schema.minLength) && value.length < schema.minLength) found.push(`gate_evidence_schema_min_length:${location}`);
      if (typeof schema.pattern === 'string' && !new RegExp(schema.pattern, 'u').test(value)) found.push(`gate_evidence_schema_pattern:${location}`);
      if (schema.format === 'date-time' && !dateTimeValid(value)) found.push(`gate_evidence_schema_date_time:${location}`);
    }
    if (typeof value === 'number' && Number.isFinite(value) && typeof schema.minimum === 'number' && value < schema.minimum) found.push(`gate_evidence_schema_minimum:${location}`);
    if (Array.isArray(value)) {
      if (isObject(schema.items) || typeof schema.items === 'boolean') value.forEach((item, index) => found.push(...validate(item, schema.items, `${location}[${index}]`)));
      if (schema.uniqueItems === true) {
        const seen = new Set();
        value.forEach((item, index) => {
          const digest = stableJson(item);
          if (seen.has(digest)) found.push(`gate_evidence_schema_unique:${location}[${index}]`);
          seen.add(digest);
        });
      }
    }
    if (isObject(value)) {
      const properties = isObject(schema.properties) ? schema.properties : {};
      if (Array.isArray(schema.required)) for (const key of schema.required) if (!Object.hasOwn(value, key)) found.push(`gate_evidence_schema_required:${location}.${key}`);
      for (const [key, item] of Object.entries(value)) {
        if (Object.hasOwn(properties, key)) found.push(...validate(item, properties[key], `${location}.${key}`));
        else if (schema.additionalProperties === false) found.push(`gate_evidence_schema_additional:${location}.${key}`);
        else if (isObject(schema.additionalProperties) || typeof schema.additionalProperties === 'boolean') found.push(...validate(item, schema.additionalProperties, `${location}.${key}`));
      }
    }
    return found;
  };
  try {
    const schemaPath = path.resolve(__dirname, '../../schemas/gate-evidence.schema.json');
    const schema = evidenceShapeIssues.schema ??= JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
    issues.push(...validate(evidence, schema, '$'));
  } catch {
    return ['gate_evidence_schema_unavailable'];
  }
  if (isObject(evidence) && Array.isArray(evidence.artifacts)) evidence.artifacts.forEach((artifact, index) => {
    if (!isObject(artifact) || typeof artifact.bytesBase64 !== 'string') return;
    const decoded = Buffer.from(artifact.bytesBase64, 'base64');
    const canonical = decoded.toString('base64').replace(/=+$/u, '');
    if (artifact.bytesBase64.replace(/\s+/gu, '').replace(/=+$/u, '') !== canonical) issues.push(`gate_evidence_base64_invalid:artifacts[${index}]`);
  });
  return issues;
}

function sealedRecordValid(record, keys, namespace) {
  if (!exactKeys(record, [...keys, 'receiptDigest'])) return false;
  const payload = { ...record };
  delete payload.receiptDigest;
  return verifyTrustedPolicyReceipt(namespace, payload, record.receiptDigest);
}

const sourceReceiptValid = (source) => sealedRecordValid(source, ['sourceId', 'locator', 'contentDigest', 'observedAt', 'validUntil', 'sourceClass', 'authorityEvidenceDigest', 'licenseDigest'], 'source.receipt')
  && safePath(source.locator) && validHash(source.contentDigest) && validHash(source.authorityEvidenceDigest) && validHash(source.licenseDigest)
  && !Number.isNaN(Date.parse(source.observedAt)) && !Number.isNaN(Date.parse(source.validUntil)) && ['official', 'primary', 'secondary', 'user_supplied'].includes(source.sourceClass);
const rightsReceiptValid = (item) => sealedRecordValid(item, ['artifactDigest', 'rightsholderDigest', 'grantType', 'allowedUse', 'territory', 'issuedAt', 'expiresAt', 'revocationState', 'evidenceArtifactDigest', 'reviewerReceiptDigest'], 'rights.receipt')
  && [item.artifactDigest, item.rightsholderDigest, item.evidenceArtifactDigest, item.reviewerReceiptDigest].every(validHash)
  && ['owned', 'licensed', 'cleared', 'public_domain'].includes(item.grantType) && item.revocationState === 'active'
  && !Number.isNaN(Date.parse(item.issuedAt)) && !Number.isNaN(Date.parse(item.expiresAt));
const consentReceiptValid = (item) => sealedRecordValid(item, ['subjectDigest', 'purpose', 'scopeDigest', 'artifactSetDigest', 'issuedAt', 'expiresAt', 'revoked'], 'consent.receipt')
  && validHash(item.subjectDigest) && validHash(item.scopeDigest) && validHash(item.artifactSetDigest) && item.revoked === false
  && !Number.isNaN(Date.parse(item.issuedAt)) && !Number.isNaN(Date.parse(item.expiresAt));
const semanticReviewValid = (review, gateId, parameterProfile, subjectDigest) => sealedRecordValid(review, ['gateId', 'reviewerRole', 'subjectDigest', 'decision', 'resultDigest'], `semantic-review:${gateId}:${parameterProfile}`)
  && review.gateId === gateId && review.subjectDigest === subjectDigest && review.decision === 'passed'
  && review.reviewerRole === `profile:${parameterProfile}`
  && review.resultDigest === sha({ gateId, parameterProfile, subjectDigest, decision: 'passed', policyDigest: trustedEvidencePolicyDigest });

function missingOr(statusCondition, issue) {
  return statusCondition ? [] : [issue];
}

const profileCoverageId = new Map([
  ['seed.answer-completeness', 'answers'], ['seed.api-completeness', 'api'],
  ['seed.department-source-coverage', 'departments'], ['seed.objective-assessment-alignment', 'objectives'],
  ['seed.option-completeness', 'options'], ['seed.requirement-coverage', 'requirements'],
]);

const subjectiveProfiles = new Set([
  'seed.consensus-disagreement-separation', 'seed.fact-inference-separation', 'seed.fact-opinion-separation',
  'seed.marketing-fact-separation', 'seed.memory-fact-separation', 'seed.source-balance',
  'seed.literature-balance', 'seed.evidence-strength', 'seed.recommendation-strength',
  'seed.reputation-risk', 'seed.legal-advice-boundary', 'seed.voice-consistency', 'seed.voice-fidelity',
  'seed.originality-boundary', 'seed.local-term-fidelity', 'seed.tradeoff-visibility',
]);

function profilePolicyIssues(gateId, parameterProfile, evidence) {
  if (parameterProfile === 'core.default') return [];
  const issues = [];
  const profile = String(parameterProfile ?? '');
  if (!profile.startsWith('seed.')) return ['profile_policy_missing'];

  if (gateId === 'artifact.structure') {
    const required = profile === 'seed.instructor-learner-separation' ? ['instructor', 'learner'] : ['title', 'section'];
    if (!evidence.artifacts.some((item) => required.every((id) => (item.actualStructureIds ?? []).includes(id)))) issues.push(`${profile}:profile_structure_missing`);
  } else if (gateId === 'claim.fact-inference-separation') {
    const classes = new Set(evidence.classifications.map((item) => item.classification));
    const required = profile.includes('consensus-disagreement') ? ['consensus', 'disagreement']
      : profile.includes('fact-opinion') ? ['fact', 'opinion']
        : profile.includes('marketing-fact') ? ['fact', 'marketing']
          : profile.includes('memory-fact') ? ['fact', 'memory'] : ['fact', 'inference'];
    if (!required.every((value) => classes.has(value))) issues.push(`${profile}:classification_profile_incomplete`);
  } else if (gateId === 'claim.support' && profile === 'seed.claim-proof') {
    if (!evidence.claims.every((claim) => (claim.sourceIds ?? []).length >= 1 && (claim.sourceIds ?? []).every((id) => evidence.references.some((ref) => ref.sourceId === id)))) issues.push('seed.claim-proof:locator_proof_missing');
  } else if (gateId === 'confidentiality.preserved') {
    const expectedClass = profile.includes('sacred') ? 'restricted' : profile.includes('source-protection') ? 'protected_source' : 'confidential';
    if (!evidence.sensitiveItems.some((item) => item.classification === expectedClass)) issues.push(`${profile}:classified_subject_missing`);
  } else if (gateId === 'coverage.completeness') {
    const expected = profileCoverageId.get(profile);
    if (!expected || !evidence.coverage.some((row) => row.coverageId === expected)) issues.push(`${profile}:profile_denominator_missing`);
  } else if (gateId === 'entity.identity-consistency') {
    if (profile === 'seed.duplicate-event-control' && new Set(evidence.events.map((item) => item.recordId)).size !== evidence.events.length) issues.push('seed.duplicate-event-control:duplicate_event');
    if (profile === 'seed.media-identity' && !evidence.artifacts.some((item) => item.itemId || item.recordId)) issues.push('seed.media-identity:media_identity_binding_missing');
    if (profile === 'seed.identity-accuracy' && evidence.entities.some((item) => !item.name || !(item.aliases ?? []).length)) issues.push('seed.identity-accuracy:identity_evidence_incomplete');
  } else if (gateId === 'numeric-unit.consistency' && !evidence.metrics.every((item) => item.unit && item.period && item.denominator && item.scale)) issues.push('seed.metric-definition-consistency:metric_dimension_missing');
  else if (gateId === 'privacy.anonymization' && !evidence.anonymization.some((item) => item.private === true)) issues.push('seed.anonymization:private_subject_missing');
  else if (gateId === 'privacy.consent') {
    const expectedPurpose = profile === 'seed.bearer-consent' ? 'bearer_consent' : 'informed_consent';
    if (!evidence.consents.some((item) => item.purpose === expectedPurpose)) issues.push(`${profile}:consent_purpose_mismatch`);
  } else if (gateId === 'privacy.minimization' && !(evidence.fieldScope.emittedFields ?? []).length) issues.push('seed.living-person-privacy:emitted_field_projection_missing');
  else if (gateId === 'projection.parity' && evidence.projections.length < 2) issues.push('seed.cross-case-comparability:multiple_projection_required');
  else if (gateId === 'reference.fidelity') {
    const expectedType = profile.split('.').at(-1);
    if (!evidence.references.some((item) => item.type === expectedType || item.reviewScope === expectedType)) issues.push(`${profile}:reference_kind_missing`);
  } else if (gateId === 'relationship.consistency' && !evidence.relationships.every((item) => item.type)) issues.push('seed.relationship-consistency:relationship_type_missing');
  else if (gateId === 'rights.clearance') {
    const use = profile.split('.').at(-1);
    if (!evidence.rights.some((item) => item.allowedUse === use || item.reviewScope === use)) issues.push(`${profile}:rights_use_scope_missing`);
  } else if (gateId === 'risk.disclosure') {
    if (!evidence.risks.some((item) => item.reviewScope === profile || item.type === profile)) issues.push(`${profile}:risk_profile_missing`);
  } else if (gateId === 'safety.hazard-review' && !evidence.hazards.some((item) => item.riskClass === 'high')) issues.push('seed.safety-warning:high_risk_hazard_missing');
  else if (gateId === 'source.freshness' && !evidence.sources.every((item) => item.observedAt && item.validUntil)) issues.push('seed.freshness:source_window_missing');
  else if (gateId === 'source.quality') {
    const classes = new Set(evidence.sources.map((item) => item.sourceClass));
    if (profile === 'seed.multi-source-corroboration' && evidence.sources.length < 2) issues.push(`${profile}:independent_sources_missing`);
    else if (profile === 'seed.literature-balance' && (evidence.sources.length < 2 || classes.size < 2)) issues.push(`${profile}:balanced_literature_missing`);
    else if (profile === 'seed.source-balance' && classes.size < 2) issues.push(`${profile}:source_class_balance_missing`);
    else if (profile === 'seed.official-record-priority' && !classes.has('official')) issues.push(`${profile}:official_record_missing`);
    else if (profile === 'seed.authoritative-source' && ![...classes].some((value) => ['official', 'primary'].includes(value))) issues.push(`${profile}:authoritative_source_missing`);
    else if (profile === 'seed.evidence-strength' && evidence.sources.some((item) => !['official', 'primary'].includes(item.sourceClass))) issues.push(`${profile}:weak_source_present`);
    else if (profile === 'seed.source-quality' && evidence.sources.length < 1) issues.push(`${profile}:quality_source_missing`);
  } else if (gateId === 'source.traceability') {
    if (!evidence.references.some((item) => item.reviewScope === profile || item.type === profile)) issues.push(`${profile}:traceability_projection_missing`);
  } else if (gateId === 'temporal.validity') {
    if (profile === 'seed.effective-date' && !evidence.versions.some((item) => item.role === 'effective')) issues.push(`${profile}:effective_version_missing`);
    if (profile === 'seed.late-entry-policy' && !validHash(evidence.temporalPolicy.lateEntryPolicyDigest)) issues.push(`${profile}:late_entry_policy_missing`);
  } else if (gateId === 'timeline.consistency') {
    if (!evidence.events.some((item) => item.type === profile || item.reviewScope === profile)) issues.push(`${profile}:timeline_profile_evidence_missing`);
  } else if (gateId === 'version.alignment') {
    if (profile === 'seed.deadline-and-version' && !evidence.versions.some((item) => item.role === 'deadline')) issues.push(`${profile}:deadline_version_missing`);
  } else if (gateId === 'workflow.completeness') {
    const marker = profile.split('.').at(-1);
    if (!(evidence.workflow.steps ?? []).some((item) => item.reviewScope === marker || item.type === marker)) issues.push(`${profile}:workflow_profile_step_missing`);
  }

  if (subjectiveProfiles.has(profile)) {
    const review = evidence.semanticReviews.find((item) => item.gateId === gateId && item.reviewerRole === `profile:${profile}`);
    if (!semanticReviewValid(review, gateId, profile, evidence.projectStateDigest)) issues.push(`${profile}:trusted_profile_review_required`);
  }
  return issues;
}

function evaluateEvidence(gateId, parameterProfile, evidence) {
  const missing = [];
  const failures = [];
  const metrics = {};
  const artifacts = evidence.artifacts;
  const artifactByPath = new Map(artifacts.map((item) => [item.path, item]));
  const sourceById = new Map(evidence.sources.map((item) => [item.sourceId, item]));
  const entityIds = new Set(evidence.entities.map((item) => item.entityId));

  if (gateId === 'artifact.openability') {
    if (artifacts.length === 0) missing.push('artifact_required');
    for (const artifact of artifacts) {
      if (!safePath(artifact.path) || !validHash(artifact.sha256) || typeof artifact.bytesBase64 !== 'string') { failures.push(`artifact_invalid:${artifact.path ?? 'unknown'}`); continue; }
      const bytes = Buffer.from(artifact.bytesBase64, 'base64');
      if (bytes.length !== artifact.byteLength || sha256(bytes) !== artifact.sha256) failures.push(`artifact_integrity_mismatch:${artifact.path}`);
      else if (['docx', 'pdf'].includes(artifact.format)) {
        const inspection = inspectBinaryArtifact(artifact.format, bytes, { byteLength: artifact.byteLength, sha256: artifact.sha256 });
        if (!inspection.ok) failures.push(...inspection.issues.map((issue) => `${artifact.path}:${issue}`));
      } else if (!['markdown', 'html', 'json'].includes(artifact.format) || bytes.length === 0) failures.push(`artifact_not_openable:${artifact.path}`);
    }
    metrics.artifactCount = artifacts.length;
  } else if (gateId === 'artifact.structure') {
    if (artifacts.length === 0) missing.push('artifact_required');
    for (const artifact of artifacts) for (const required of artifact.requiredStructureIds ?? []) if (!(artifact.actualStructureIds ?? []).includes(required)) failures.push(`${artifact.path}:structure_missing:${required}`);
  } else if (gateId === 'claim.fact-inference-separation') {
    if (evidence.claims.length === 0) missing.push('claim_required');
    const classified = new Set(evidence.classifications.map((item) => item.claimId));
    for (const claim of evidence.claims) if (!classified.has(claim.claimId)) failures.push(`${claim.claimId}:classification_missing`);
  } else if (gateId === 'claim.support') {
    if (evidence.claims.length === 0 || evidence.sources.length === 0) missing.push('claim_and_source_required');
    for (const claim of evidence.claims) if (!Array.isArray(claim.sourceIds) || claim.sourceIds.length === 0 || claim.sourceIds.some((sourceId) => !sourceReceiptValid(sourceById.get(sourceId)))) failures.push(`${claim.claimId}:unsupported`);
  } else if (gateId === 'confidentiality.preserved') {
    for (const item of evidence.sensitiveItems) {
      const payload = { itemId: item.itemId, classification: item.classification, exposed: item.exposed };
      if (item.classification !== 'public' && (item.exposed === true || !verifyTrustedPolicyReceipt('confidentiality.handling', payload, item.handlingReceiptDigest))) failures.push(`${item.itemId}:confidentiality_not_preserved`);
    }
  } else if (gateId === 'coverage.completeness') {
    if (evidence.coverage.length === 0) missing.push('coverage_denominator_required');
    for (const row of evidence.coverage) for (const required of row.requiredIds ?? []) if (!(row.coveredIds ?? []).includes(required)) failures.push(`${row.coverageId}:uncovered:${required}`);
  } else if (gateId === 'delivery-manifest.integrity') {
    if (!Array.isArray(evidence.deliveryManifest.artifacts) || evidence.deliveryManifest.artifacts.length === 0) missing.push('delivery_manifest_required');
    const expected = artifacts.map((item) => ({ path: item.path, sha256: item.sha256, byteLength: item.byteLength, format: item.format })).sort((a, b) => a.path.localeCompare(b.path, 'en'));
    const actual = [...(evidence.deliveryManifest.artifacts ?? [])].sort((a, b) => a.path.localeCompare(b.path, 'en'));
    if (stableJson(expected) !== stableJson(actual)) failures.push('delivery_manifest_artifact_set_mismatch');
  } else if (gateId === 'encoding.valid') {
    if (artifacts.length === 0) missing.push('artifact_required');
    for (const artifact of artifacts.filter((item) => ['markdown', 'html', 'json'].includes(item.format))) {
      const bytes = Buffer.from(artifact.bytesBase64, 'base64');
      const text = bytes.toString('utf8');
      if (text.includes('\uFFFD') || text.includes('\u0000') || sha256(bytes) !== artifact.sha256) failures.push(`${artifact.path}:encoding_invalid`);
    }
  } else if (gateId === 'entity.identity-consistency') {
    if (evidence.entities.length === 0) missing.push('entity_registry_required');
    if (entityIds.size !== evidence.entities.length) failures.push('duplicate_entity_id');
    const aliases = new Map();
    for (const entity of evidence.entities) for (const alias of [entity.name, ...(entity.aliases ?? [])]) { const key = String(alias).toLocaleLowerCase('en-US'); if (aliases.has(key) && aliases.get(key) !== entity.entityId) failures.push(`alias_conflict:${alias}`); else aliases.set(key, entity.entityId); }
  } else if (gateId === 'example.executable') {
    if (evidence.examples.length === 0) missing.push('execution_receipt_required');
    for (const example of evidence.examples) if (!sealedRecordValid(example, ['exampleId', 'codeDigest', 'expectedOutputDigest', 'observedOutputDigest', 'exitCode', 'networkUsed'], 'example.execution') || example.exitCode !== 0 || example.networkUsed !== false || example.expectedOutputDigest !== example.observedOutputDigest) failures.push(`${example.exampleId}:example_not_executable`);
  } else if (gateId === 'external-action.authorized') {
    for (const action of evidence.externalActions) {
      const trusted = sealedRecordValid(action, ['actionId', 'status', 'authorizationReceiptDigest', 'actionReceiptDigest', 'reconciliationRequired'], 'external-action.receipt');
      if (!trusted || action.status !== 'completed_with_receipt' || !validHash(action.authorizationReceiptDigest) || !validHash(action.actionReceiptDigest) || action.reconciliationRequired === true) failures.push(`${action.actionId}:external_action_not_authorized`);
    }
    metrics.noExternalAction = evidence.externalActions.length === 0;
  } else if (gateId === 'input.required') {
    if (evidence.requiredInputs.length === 0) missing.push('required_input_contract_missing');
    const provided = new Map(evidence.providedInputs.map((item) => [item.inputId, item]));
    for (const inputId of evidence.requiredInputs) { const item = provided.get(inputId); if (!item || item.present !== true || !item.typeValid || !item.sensitivity) failures.push(`${inputId}:required_input_missing_or_invalid`); }
  } else if (gateId === 'numeric-unit.consistency') {
    if (evidence.metrics.length === 0) missing.push('metric_registry_required');
    const definitions = new Map();
    for (const metric of evidence.metrics) { const signature = `${metric.unit}|${metric.period}|${metric.denominator}|${metric.scale}`; if (definitions.has(metric.metricId) && definitions.get(metric.metricId) !== signature) failures.push(`${metric.metricId}:metric_definition_conflict`); else definitions.set(metric.metricId, signature); }
  } else if (gateId === 'privacy.anonymization') {
    for (const item of evidence.anonymization) {
      const payload = { subjectId: item.subjectId, private: item.private, pseudonymized: item.pseudonymized, mappingExposed: item.mappingExposed };
      if (item.private === true && (!item.pseudonymized || item.mappingExposed === true || !verifyTrustedPolicyReceipt('privacy.anonymization', payload, item.mappingReceiptDigest))) failures.push(`${item.subjectId}:anonymization_failed`);
    }
  } else if (gateId === 'privacy.consent') {
    if (evidence.consents.length === 0) missing.push('consent_receipt_required');
    for (const consent of evidence.consents) if (!consentReceiptValid(consent) || consent.artifactSetDigest !== evidence.artifactSetDigest || Date.parse(consent.issuedAt) > Date.parse(evidence.asOf) || Date.parse(consent.expiresAt) <= Date.parse(evidence.asOf)) failures.push('consent_receipt_invalid');
  } else if (gateId === 'privacy.minimization') {
    const requested = new Set(evidence.fieldScope.requestedFields ?? []); const approved = new Set(evidence.fieldScope.approvedFields ?? []);
    for (const field of evidence.fieldScope.emittedFields ?? []) if (!requested.has(field) || !approved.has(field)) failures.push(`field_not_minimized:${field}`);
    for (const field of requested) if (!approved.has(field)) failures.push(`field_not_approved:${field}`);
  } else if (gateId === 'projection.parity') {
    if (evidence.projections.length === 0) missing.push('projection_required');
    for (const projection of evidence.projections) if (projection.canonicalDigest !== projection.projectedDigest || !validHash(projection.ruleDigest)) failures.push(`${projection.projectionId}:projection_drift`);
  } else if (gateId === 'reference.fidelity') {
    if (evidence.references.length === 0) missing.push('reference_required');
    for (const reference of evidence.references) if (!sourceReceiptValid(sourceById.get(reference.sourceId)) || reference.normalizedSourceDigest !== reference.normalizedReferenceDigest) failures.push(`${reference.referenceId}:reference_drift`);
  } else if (gateId === 'relationship.consistency') {
    if (evidence.relationships.length === 0) missing.push('relationship_graph_required');
    const seen = new Map();
    for (const relation of evidence.relationships) { const key = `${relation.from}|${relation.to}`; if (!entityIds.has(relation.from) || !entityIds.has(relation.to) || relation.from === relation.to) failures.push(`${relation.relationshipId}:relationship_invalid`); if (seen.has(key) && seen.get(key) !== relation.type) failures.push(`${relation.relationshipId}:relationship_conflict`); seen.set(key, relation.type); }
  } else if (gateId === 'rights.clearance') {
    if (evidence.rights.length === 0) missing.push('rights_receipt_required');
    for (const right of evidence.rights) if (!rightsReceiptValid(right) || Date.parse(right.issuedAt) > Date.parse(evidence.asOf) || Date.parse(right.expiresAt) <= Date.parse(evidence.asOf)) failures.push('rights_receipt_invalid');
  } else if (gateId === 'risk.disclosure') {
    if (evidence.risks.length === 0) missing.push('risk_ledger_required');
    for (const risk of evidence.risks) {
      const payload = { riskId: risk.riskId, severity: risk.severity, disclosed: risk.disclosed, tradeoffVisible: risk.tradeoffVisible };
      if (risk.severity === 'critical' && (!risk.disclosed || !risk.tradeoffVisible || !verifyTrustedPolicyReceipt('risk.disclosure', payload, risk.disclosureDigest))) failures.push(`${risk.riskId}:critical_risk_not_disclosed`);
    }
    const review = evidence.semanticReviews.find((item) => item.gateId === gateId && item.reviewerRole === `profile:${parameterProfile}`);
    if (!semanticReviewValid(review, gateId, parameterProfile, evidence.projectStateDigest)) failures.push('risk_semantic_review_required');
  } else if (gateId === 'safety.hazard-review') {
    if (evidence.hazards.length === 0) missing.push('hazard_inventory_required');
    for (const hazard of evidence.hazards) {
      const payload = { hazardId: hazard.hazardId, riskClass: hazard.riskClass, warningBeforeStep: hazard.warningBeforeStep, controls: hazard.controls, owner: hazard.owner };
      if (!hazard.warningBeforeStep || !hazard.controls?.length || !hazard.owner || (hazard.riskClass === 'high' && !verifyTrustedPolicyReceipt('safety.human-review', payload, hazard.humanReceiptDigest))) failures.push(`${hazard.hazardId}:hazard_review_incomplete`);
    }
  } else if (gateId === 'schema.valid') {
    if (evidence.schemaChecks.length === 0) missing.push('schema_validation_required');
    for (const check of evidence.schemaChecks) if (!sealedRecordValid(check, ['objectId', 'passed', 'schemaDigest', 'instanceDigest', 'additionalPropertiesDetected'], 'schema.validation') || !check.passed || !validHash(check.schemaDigest) || !validHash(check.instanceDigest) || check.additionalPropertiesDetected) failures.push(`${check.objectId}:schema_invalid`);
  } else if (gateId === 'scope.lock') {
    const scopePayload = { allowedScopes: evidence.scopeLock.allowedScopes, forbiddenScopes: evidence.scopeLock.forbiddenScopes, originalDigests: evidence.scopeLock.originalDigests };
    if (!Array.isArray(evidence.scopeLock.allowedScopes) || evidence.scopeLock.allowedScopes.length === 0 || !verifyTrustedPolicyReceipt('scope.approval', scopePayload, evidence.scopeLock.approvalReceiptDigest)) missing.push('scope_lock_required');
    for (const change of evidence.scopeLock.changes ?? []) if (!(evidence.scopeLock.allowedScopes ?? []).some((scope) => change.scope === scope || change.scope.startsWith(`${scope}/`)) || (evidence.scopeLock.forbiddenScopes ?? []).some((scope) => change.scope === scope || change.scope.startsWith(`${scope}/`)) || evidence.scopeLock.originalDigests?.[change.scope] !== change.beforeDigest || !validHash(change.beforeDigest)) failures.push(`${change.scope}:scope_violation`);
  } else if (gateId === 'source.freshness') {
    if (evidence.sources.length === 0) missing.push('source_receipt_required');
    for (const source of evidence.sources) if (!sourceReceiptValid(source) || Date.parse(source.observedAt) > Date.parse(evidence.asOf) || Date.parse(source.validUntil) <= Date.parse(evidence.asOf)) failures.push(`${source.sourceId}:source_stale`);
  } else if (gateId === 'source.quality') {
    if (evidence.sources.length === 0) missing.push('source_receipt_required');
    for (const source of evidence.sources) if (!sourceReceiptValid(source) || !['official', 'primary'].includes(source.sourceClass)) failures.push(`${source.sourceId}:source_quality_insufficient`);
  } else if (gateId === 'source.traceability') {
    if (evidence.sources.length === 0 || evidence.claims.length === 0) missing.push('source_and_claim_graph_required');
    for (const claim of evidence.claims) if (!claim.sourceIds?.length || claim.sourceIds.some((sourceId) => !sourceReceiptValid(sourceById.get(sourceId)))) failures.push(`${claim.claimId}:traceability_broken`);
  } else if (gateId === 'temporal.validity') {
    if (!evidence.temporalPolicy.coverageStart || !evidence.temporalPolicy.coverageEnd) missing.push('temporal_policy_required');
    const start = Date.parse(evidence.temporalPolicy.coverageStart); const end = Date.parse(evidence.temporalPolicy.coverageEnd);
    if (!Number.isFinite(start) || !Number.isFinite(end) || start > end || evidence.events.some((event) => Date.parse(event.date) < start || Date.parse(event.date) > end) || (evidence.temporalPolicy.lateEntryCount > 0 && !validHash(evidence.temporalPolicy.lateEntryPolicyDigest))) failures.push('temporal_validity_failed');
  } else if (gateId === 'timeline.consistency') {
    if (evidence.events.length === 0) missing.push('timeline_required');
    const times = evidence.events.map((event) => Date.parse(event.date));
    if (times.some((time) => !Number.isFinite(time)) || times.some((time, index) => index > 0 && time < times[index - 1]) || evidence.events.some((event) => event.conflict === true)) failures.push('timeline_inconsistent');
  } else if (gateId === 'version.alignment') {
    if (evidence.versions.length === 0) missing.push('version_registry_required');
    const target = evidence.versions.find((item) => item.role === 'target')?.version;
    if (!target || evidence.versions.some((item) => item.role !== 'target' && item.version !== target && !item.compatibilityDeclared)) failures.push('version_alignment_failed');
  } else if (gateId === 'voice.fidelity') {
    if (!validHash(evidence.voice.profileDigest) || !validHash(evidence.voice.factAnchorBefore) || !validHash(evidence.voice.factAnchorAfter)) missing.push('voice_profile_required');
    if (evidence.voice.factAnchorBefore !== evidence.voice.factAnchorAfter || (evidence.voice.requiredPhrases ?? []).some((phrase) => !evidence.voice.text.includes(phrase)) || (evidence.voice.forbiddenPhrases ?? []).some((phrase) => evidence.voice.text.includes(phrase))) failures.push('voice_fidelity_failed');
    const review = evidence.semanticReviews.find((item) => item.gateId === gateId && item.reviewerRole === `profile:${parameterProfile}`);
    if (!semanticReviewValid(review, gateId, parameterProfile, evidence.projectStateDigest)) failures.push('voice_semantic_review_required');
  } else if (gateId === 'workflow.completeness') {
    if (!Array.isArray(evidence.workflow.requiredStepIds) || evidence.workflow.requiredStepIds.length === 0) missing.push('workflow_contract_required');
    const actual = new Map((evidence.workflow.steps ?? []).map((step) => [step.stepId, step]));
    for (const stepId of evidence.workflow.requiredStepIds ?? []) { const step = actual.get(stepId); if (!step || !step.owner || !step.outputRef || !step.exceptionPath) failures.push(`${stepId}:workflow_step_incomplete`); }
    if (evidence.workflow.orphanStepIds?.length || evidence.workflow.cycleDetected) failures.push('workflow_graph_invalid');
  } else if (gateId === 'privacy.anonymization') {
    // handled above; branch retained for completeness
  } else failures.push('evaluator_not_implemented');

  failures.push(...profilePolicyIssues(gateId, parameterProfile, evidence));
  metrics.parameterProfile = parameterProfile;
  metrics.profilePolicyDigest = sha({ gateId, parameterProfile, trustedEvidencePolicyDigest });
  metrics.missingEvidenceCount = missing.length;
  metrics.failureCount = failures.length;
  return { missing: unique(missing), failures: unique(failures), metrics };
}

const INVOCATION_KEYS = ['schemaVersion', 'gateId', 'parameterProfile', 'sceneId', 'operationMode', 'targetTransition', 'contentRiskClass', 'evidence', 'evidenceSnapshotDigest', 'artifactSetDigest', 'projectStateDigest', 'scenePackDigest', 'registryDigest', 'profileDigest', 'evaluatorDigest', 'asOf', 'invocationDigest'];
export function createGateInvocation({ gateId, parameterProfile = null, sceneId, operationMode = 'review_quality', targetTransition = 'delivery_ready', contentRiskClass = 'medium', evidence } = {}) {
  const registry = loadRegistry();
  const entry = registry.entries.find((item) => item.gateId === gateId);
  const sceneEntry = JSON.parse(fs.readFileSync(SCENE_REGISTRY_PATH, 'utf8')).entries.find((item) => item.sceneId === sceneId);
  if (!entry || entry.lifecycle !== 'active') return { ok: false, status: 'evaluator_unavailable', issues: ['active_evaluator_missing'], invocation: null };
  if (!sceneEntry) return { ok: false, status: 'needs_input', issues: ['scene_pack_not_registered'], invocation: null };
  const profileRegistered = entry.parameterProfiles.length === 0
    ? parameterProfile === 'core.default'
    : typeof parameterProfile === 'string' && entry.parameterProfiles.includes(parameterProfile);
  if (!profileRegistered) return { ok: false, status: 'needs_input', issues: ['parameter_profile_not_registered'], invocation: null };
  const evidenceIssues = evidenceShapeIssues(evidence);
  if (evidenceIssues.length) return { ok: false, status: 'needs_input', issues: evidenceIssues, invocation: null };
  if (evidence.sceneId !== sceneId || evidence.asOf === undefined) return { ok: false, status: 'needs_input', issues: ['gate_evidence_scene_mismatch'], invocation: null };
  const projection = {
    schemaVersion: SCHEMA_VERSION,
    gateId,
    parameterProfile,
    sceneId,
    operationMode,
    targetTransition,
    contentRiskClass,
    evidence,
    evidenceSnapshotDigest: sha(evidence),
    artifactSetDigest: evidence.artifactSetDigest,
    projectStateDigest: evidence.projectStateDigest,
    scenePackDigest: sceneEntry.packSha256,
    registryDigest: sha(registry),
    profileDigest: sha({ gateId, parameterProfile }),
    evaluatorDigest: entry.evaluatorSha256,
    asOf: evidence.asOf,
  };
  return { ok: true, status: 'invocation_ready', issues: [], invocation: { ...projection, invocationDigest: sha(projection) } };
}

function invocationValid(invocation, expectedGateId) {
  if (!exactKeys(invocation, INVOCATION_KEYS) || invocation.schemaVersion !== SCHEMA_VERSION || invocation.gateId !== expectedGateId) return false;
  const { invocationDigest, ...projection } = invocation;
  if (sha(projection) !== invocationDigest || evidenceShapeIssues(invocation.evidence).length || sha(invocation.evidence) !== invocation.evidenceSnapshotDigest) return false;
  const registry = loadRegistry(); const entry = registry.entries.find((item) => item.gateId === invocation.gateId);
  const sceneEntry = JSON.parse(fs.readFileSync(SCENE_REGISTRY_PATH, 'utf8')).entries.find((item) => item.sceneId === invocation.sceneId);
  return entry?.lifecycle === 'active' && sceneEntry?.packSha256 === invocation.scenePackDigest && invocation.registryDigest === sha(registry) && invocation.evaluatorDigest === entry.evaluatorSha256 && invocation.profileDigest === sha({ gateId: invocation.gateId, parameterProfile: invocation.parameterProfile }) && invocation.artifactSetDigest === invocation.evidence.artifactSetDigest && invocation.projectStateDigest === invocation.evidence.projectStateDigest && invocation.asOf === invocation.evidence.asOf;
}

export function runGateForId(gateId, invocation, context = { connectorAvailable: false, externalWriteAuthorized: false }) {
  const contextValid = exactKeys(context, ['connectorAvailable', 'externalWriteAuthorized']) && context.connectorAvailable === false && context.externalWriteAuthorized === false;
  let evaluation = { missing: [], failures: ['gate_invocation_invalid'], metrics: {} };
  if (invocationValid(invocation, gateId) && contextValid) {
    try { evaluation = evaluateEvidence(gateId, invocation.parameterProfile, invocation.evidence); }
    catch { evaluation = { missing: [], failures: ['gate_evaluator_internal_error'], metrics: {} }; }
  }
  const status = !invocationValid(invocation, gateId) || !contextValid ? 'error' : evaluation.missing.length ? 'needs_input' : evaluation.failures.length ? (evaluation.failures.some((issue) => issue.endsWith('semantic_review_required')) ? 'needs_human_review' : 'failed') : 'passed';
  const findings = [...evaluation.missing.map((code) => ({ code, severity: 'critical', subjectRef: invocation?.sceneId ?? 'unknown', evidenceRefs: [], expectedDigest: null, observedDigest: null })), ...evaluation.failures.map((code) => ({ code, severity: 'critical', subjectRef: invocation?.sceneId ?? 'unknown', evidenceRefs: [], expectedDigest: null, observedDigest: null }))];
  const payload = { gateId, parameterProfile: invocation?.parameterProfile ?? null, sceneId: invocation?.sceneId ?? 'unknown', status, ok: status === 'passed', deliveryEffect: status === 'passed' ? 'allow' : status === 'needs_human_review' ? 'human_block' : 'block', findings, metrics: evaluation.metrics, context };
  const resultDigest = sha(payload);
  const receiptPayload = { schemaVersion: SCHEMA_VERSION, gateId, parameterProfile: payload.parameterProfile, sceneId: payload.sceneId, invocationDigest: invocation?.invocationDigest ?? null, evaluatorDigest: invocation?.evaluatorDigest ?? null, registryDigest: invocation?.registryDigest ?? null, profileDigest: invocation?.profileDigest ?? null, scenePackDigest: invocation?.scenePackDigest ?? null, evidenceSnapshotDigest: invocation?.evidenceSnapshotDigest ?? null, artifactSetDigest: invocation?.artifactSetDigest ?? null, resultDigest, decision: status === 'passed' ? 'passed' : 'blocked', externalActionCount: 0 };
  return { ...payload, resultDigest, receipt: { ...receiptPayload, receiptDigest: sha(receiptPayload) } };
}

const RESULT_KEYS = ['gateId', 'parameterProfile', 'sceneId', 'status', 'ok', 'deliveryEffect', 'findings', 'metrics', 'context', 'resultDigest', 'receipt'];
export function evaluateGateResult(result, invocation) {
  const issues = [];
  if (!exactKeys(result, RESULT_KEYS) || !invocationValid(invocation, result?.gateId) || !STATUSES.has(result?.status)) issues.push('gate_result_shape_invalid');
  const payload = { gateId: result?.gateId, parameterProfile: result?.parameterProfile, sceneId: result?.sceneId, status: result?.status, ok: result?.ok, deliveryEffect: result?.deliveryEffect, findings: result?.findings, metrics: result?.metrics, context: result?.context };
  if (result?.resultDigest !== sha(payload)) issues.push('gate_result_digest_mismatch');
  const receiptPayload = { schemaVersion: SCHEMA_VERSION, gateId: result?.gateId, parameterProfile: result?.parameterProfile, sceneId: result?.sceneId, invocationDigest: invocation?.invocationDigest ?? null, evaluatorDigest: invocation?.evaluatorDigest ?? null, registryDigest: invocation?.registryDigest ?? null, profileDigest: invocation?.profileDigest ?? null, scenePackDigest: invocation?.scenePackDigest ?? null, evidenceSnapshotDigest: invocation?.evidenceSnapshotDigest ?? null, artifactSetDigest: invocation?.artifactSetDigest ?? null, resultDigest: result?.resultDigest, decision: result?.status === 'passed' ? 'passed' : 'blocked', externalActionCount: 0 };
  if (!exactKeys(result?.receipt, [...Object.keys(receiptPayload), 'receiptDigest']) || result.receipt.receiptDigest !== sha(receiptPayload)) issues.push('gate_receipt_invalid');
  for (const [key, value] of Object.entries(receiptPayload)) if (result?.receipt?.[key] !== value) issues.push(`gate_receipt_binding_mismatch:${key}`);
  if (invocationValid(invocation, result?.gateId) && exactKeys(result?.context, ['connectorAvailable', 'externalWriteAuthorized'])) {
    const expected = runGateForId(result.gateId, invocation, result.context);
    if (stableJson(expected) !== stableJson(result)) issues.push('gate_evaluator_output_mismatch');
  }
  return { ok: issues.length === 0, issues: unique(issues) };
}

export const machineGateIds = Object.freeze(loadRegistry().entries.map((item) => item.gateId));
