import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { evaluateCapability, runCapability } from './capability-runtime.mjs';
import { capabilityResult, sealCapabilityResult, sha256, stableJson } from './lib/kernel-utils.mjs';
import { validateHumanReviewReceipt } from './gate-planner.mjs';

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sceneRoot = path.join(skillRoot, 'scenes');
const legacyPath = path.join(skillRoot, 'resources', 'legacy-scene-migrations.json');
const registryPath = path.join(skillRoot, 'resources', 'scene-registry.json');
const exactContext = (context) => context && typeof context === 'object' && !Array.isArray(context) && Object.keys(context).sort().join(',') === 'connectorAvailable,externalWriteAuthorized' && typeof context.connectorAvailable === 'boolean' && typeof context.externalWriteAuthorized === 'boolean';

export function loadScenePack(sceneId) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(String(sceneId ?? ''))) return null;
  const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
  const entry = registry.entries.find((item) => item.sceneId === sceneId);
  if (!entry || entry.packRef !== `../scenes/${sceneId}.json`) return null;
  const target = path.resolve(path.join(skillRoot, 'resources'), ...entry.packRef.split('/'));
  if (!target.startsWith(`${sceneRoot}${path.sep}`) || !fs.existsSync(target)) return null;
  const bytes = fs.readFileSync(target);
  if (sha256(bytes) !== entry.packSha256) return null;
  return JSON.parse(bytes.toString('utf8'));
}

const normalizeSignal = (value) => String(value ?? '').normalize('NFKC').toLocaleLowerCase('en-US').replace(/\s+/gu, ' ').trim();
export function routeDomainScene({ explicitSceneId = null, text = '' } = {}, context = { connectorAvailable: false, externalWriteAuthorized: false }) {
  if (!exactContext(context)) return { ok: false, status: 'invalid_invocation', issues: ['context_shape_invalid'], candidates: [] };
  const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
  if (explicitSceneId !== null) {
    const explicit = registry.entries.find((item) => item.sceneId === explicitSceneId);
    return explicit ? { ok: true, status: 'routed', sceneId: explicit.sceneId, routeSource: 'explicit', candidates: [{ sceneId: explicit.sceneId, score: 1 }], connectorInfluencedRoute: false } : { ok: false, status: 'rejected', issues: ['unknown_explicit_scene'], candidates: [], connectorInfluencedRoute: false };
  }
  const normalized = normalizeSignal(text);
  const scored = registry.entries.filter((item) => item.kind === 'vertical_scene').map((entry) => {
    const pack = loadScenePack(entry.sceneId);
    const score = Math.max(0, ...pack.triggers.map((trigger) => normalized.includes(normalizeSignal(trigger.signal)) ? trigger.weight : 0));
    return { sceneId: entry.sceneId, score };
  }).filter((item) => item.score > 0).sort((left, right) => right.score - left.score || Buffer.from(left.sceneId).compare(Buffer.from(right.sceneId)));
  if (scored.length === 0 || scored[0].score < 0.8) return { ok: true, status: 'routed', sceneId: 'general', routeSource: 'fallback', candidates: scored, connectorInfluencedRoute: false };
  if (scored.length > 1 && scored[0].score === scored[1].score) return { ok: false, status: 'needs_clarification', issues: ['domain_scene_tie'], candidates: scored.filter((item) => item.score === scored[0].score), connectorInfluencedRoute: false };
  return { ok: true, status: 'routed', sceneId: scored[0].sceneId, routeSource: 'trigger', candidates: scored, connectorInfluencedRoute: false };
}

function missingInputIds(pack, inputs) {
  return pack.requiredInputs.filter((item) => item.required).map((item) => item.id).filter((id) => {
    const value = inputs?.[id];
    return value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0);
  });
}

export function evaluateSceneRequest(sceneId, input = {}, context = { connectorAvailable: false, externalWriteAuthorized: false }) {
  const pack = loadScenePack(sceneId);
  if (!pack) return sealCapabilityResult('scene-pack-runtime', input, context, capabilityResult('scene-pack-runtime', input, { ok: false, status: 'unknown_scene', issues: ['unknown_scene'], output: {} }));
  if (!exactContext(context)) return sealCapabilityResult('scene-pack-runtime', input, { connectorAvailable: false, externalWriteAuthorized: false }, capabilityResult('scene-pack-runtime', input, { ok: false, status: 'invalid_invocation', issues: ['context_shape_invalid'], output: { sceneId: pack.sceneId } }));
  const missing = missingInputIds(pack, input.inputs ?? {});
  const conflicts = Array.isArray(input.conflicts) ? input.conflicts : [];
  const externalAction = input.externalAction ?? null;
  const adversarialSignals = Array.isArray(input.adversarialSignals) ? input.adversarialSignals.map((item) => String(item).normalize('NFKC').trim()).filter(Boolean) : [];
  const adversarialPattern = /(?:ignore|bypass|override|skip).{0,40}(?:scene|scope|contract|gate|review)|(?:publish|release).{0,40}(?:unverified|without review)|fabricat(?:e|ed|ion)|force.{0,20}general|伪造|绕过|忽略.{0,20}(?:场景|范围|合同|门禁|审核)|未经核验.{0,20}(?:发布|交付)/iu;
  const rejectedAdversarialSignals = adversarialSignals.filter((signal) => adversarialPattern.test(signal));
  const unauthorized = Boolean(externalAction) && context.externalWriteAuthorized !== true;
  const binding = externalAction ? pack.optionalPortBindings.find((item) => item.portId === externalAction.portId && item.operation === externalAction.operation && (!externalAction.legacyLabel || item.legacyLabel === externalAction.legacyLabel)) : null;
  const portIntentProjection = binding ? { sceneId: pack.sceneId, legacyLabel: binding.legacyLabel, portId: binding.portId, operation: binding.operation, minimumDataScope: binding.minimumDataScope, writeMode: binding.writeMode } : null;
  const portIntent = externalAction && binding ? { ...portIntentProjection, approvalRequired: binding.approvalRequired, readbackRequired: binding.readbackRequired, executionAllowed: false, adapterStatus: 'optional_adapter_registered_intent_only', fallback: binding.fallback, intentDigest: sha256(stableJson(portIntentProjection)) } : null;
  const undeclaredAction = Boolean(externalAction) && !binding;
  const authorizedIntentOnly = Boolean(externalAction) && !unauthorized && Boolean(binding);
  const unknownOperationMode = input.operationMode && !pack.operationModes.includes(input.operationMode);
  const riskOrder = ['low', 'medium', 'high', 'restricted'];
  const riskHint = riskOrder.includes(input.contentRiskClassHint) ? input.contentRiskClassHint : pack.contentRiskClass;
  const effectiveRisk = riskOrder.indexOf(riskHint) > riskOrder.indexOf(pack.contentRiskClass) ? riskHint : pack.contentRiskClass;
  const generalRiskConflict = pack.sceneId === 'general' && riskOrder.indexOf(effectiveRisk) > riskOrder.indexOf('medium');
  const status = missing.length ? 'needs_input' : conflicts.length || generalRiskConflict ? 'needs_clarification' : unknownOperationMode ? 'rejected' : unauthorized || undeclaredAction ? 'rejected' : authorizedIntentOnly ? 'port_intent_only' : 'draft_ready';
  const issues = [
    ...missing.map((id) => `${id}:required`),
    ...conflicts.map((item) => `${item.field ?? 'unknown'}:conflicting`),
    ...(unauthorized ? ['external_action_not_authorized'] : [])
    , ...(undeclaredAction ? ['port_intent_not_declared'] : [])
    , ...(authorizedIntentOnly ? ['external_adapter_execution_not_requested'] : [])
    , ...(unknownOperationMode ? ['operation_mode_not_supported_by_scene'] : [])
    , ...(generalRiskConflict ? ['risk_class_requires_explicit_vertical_scene'] : [])
  ];
  return sealCapabilityResult('scene-pack-runtime', input, context, capabilityResult('scene-pack-runtime', input, {
    ok: status === 'draft_ready', status,
    output: {
      sceneId: pack.sceneId,
      operationMode: input.operationMode ?? pack.operationModes[0],
      routePreserved: true,
      connectorInfluencedRoute: false,
      localOfflineAvailable: true,
      connectorUnavailableFallbackUsed: context.connectorAvailable === false && pack.optionalPortBindings.length > 0,
      missingInputIds: missing,
      conflictFields: conflicts.map((item) => item.field ?? 'unknown'),
      unauthorizedExternalAction: unauthorized,
      portIntent,
      adversarialSignalsRejected: rejectedAdversarialSignals,
      contentRiskClass: effectiveRisk,
      qualityGateRegistryIds: [...new Set(pack.qualityGateRefs.map((item) => item.registryId))].sort(),
      artifactArchetypeIds: [...new Set(pack.artifactRefs.map((item) => item.archetypeId))].sort(),
      optionalPortOperations: [...new Set(pack.optionalPortBindings.map((item) => `${item.portId}.${item.operation}`))].sort(),
      allowGeneralSubstitution: generalRiskConflict ? false : pack.fallback.allowGeneralSubstitution,
      externalActionCount: 0,
      qualityEvaluationState: 'not_run_for_this_request',
      deliveryBlockedPendingGateEvaluation: true,
      packSemanticDigest: sha256(stableJson(pack)),
      packPhysicalSha256: JSON.parse(fs.readFileSync(registryPath, 'utf8')).entries.find((item) => item.sceneId === pack.sceneId).packSha256
    }, issues
  }));
}

export function evaluateSceneResult(result, input = {}, context = { connectorAvailable: false, externalWriteAuthorized: false }) {
  return evaluateCapability('scene-pack-runtime', result, input, context);
}

export function composeScenes(sceneIds, context = { connectorAvailable: false, externalWriteAuthorized: false }) {
  const packs = sceneIds.map(loadScenePack);
  if (packs.some((item) => item === null)) return sealCapabilityResult('scene-composer', { scenes: sceneIds }, context, capabilityResult('scene-composer', { scenes: sceneIds }, { ok: false, status: 'rejected', output: { composedDomainScenes: [], contentRiskClass: 'low', qualityGateRefs: [], artifactRefs: [] }, issues: ['unknown_scene'] }));
  const scenes = packs.map((pack) => ({ sceneId: pack.sceneId, contentRiskClass: pack.contentRiskClass, qualityGateRefs: pack.qualityGateRefs.map((item) => item.registryId), artifactRefs: pack.artifactRefs.map((item) => item.archetypeId) }));
  return runCapability('scene-composer', { scenes }, context);
}

export function resolveLegacyRoute(legacyId, signals = {}, domainScene = 'general', evidence = {}) {
  if (['material_activation', 'continuation_or_revision', 'finished_draft_closure'].includes(legacyId)) {
    const input = { legacyId, signals, domainScene, evidence };
    const routed = runCapability('scene-router', input, { connectorAvailable: false, externalWriteAuthorized: false });
    const pack = loadScenePack(domainScene);
    if (!pack) return { ok: false, status: 'unknown_scene', output: { domainScene } };
    const legalBinding = pack.qualityGateRefs.find((item) => item.registryId === 'human-review.receipt' && item.humanOwner === 'legal_reviewer');
    const legalBlocked = legacyId === 'finished_draft_closure' && pack.contentRiskClass === 'restricted' && (!legalBinding || !validateHumanReviewReceipt(legalBinding, evidence.legalReviewBundle, pack.sceneId, evidence.legalReviewContext).ok);
    const status = legalBlocked ? 'human_review_required' : routed.status;
    return {
      ok: routed.ok && !legalBlocked,
      status,
      issues: legalBlocked ? ['legal_review_receipt_required'] : routed.issues,
      output: {
        operationMode: routed.output.operationMode,
        domainScene,
        routeSource: routed.output.routeSource,
        ambiguity: routed.output.ambiguity,
        connectorInfluencedRoute: false,
        contentRiskClass: pack.contentRiskClass,
        qualityGateRegistryIds: [...new Set(pack.qualityGateRefs.map((item) => item.registryId))].sort(),
        artifactArchetypeIds: [...new Set(pack.artifactRefs.map((item) => item.archetypeId))].sort(),
        allowGeneralSubstitution: pack.fallback.allowGeneralSubstitution
      }
    };
  }
  const registry = JSON.parse(fs.readFileSync(legacyPath, 'utf8'));
  const migration = registry.legacySceneMigrations.find((item) => item.legacyId === legacyId);
  if (!migration) return { ok: false, status: 'unknown_legacy_route', legacyId, domainScenes: [] };
  const candidates = [...migration.domainScenes];
  const selected = evidence?.selectedDomainScene ?? (domainScene !== 'general' ? domainScene : null);
  if (candidates.length > 1 && !candidates.includes(selected)) {
    return { ok: false, status: 'needs_clarification', issues: ['legacy_scene_choice_required'], legacyId, domainScenes: candidates, selectedDomainScene: null, capabilityIds: migration.capabilityIds ?? [], mustNotMapTo: migration.mustNotMapTo ?? [] };
  }
  const resolved = candidates.length === 1 ? candidates[0] : selected;
  return { ok: true, status: 'resolved', legacyId, domainScenes: [resolved], selectedDomainScene: resolved, candidateDomainScenes: candidates, capabilityIds: migration.capabilityIds ?? [], mustNotMapTo: migration.mustNotMapTo ?? [] };
}
