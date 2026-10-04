import { sha256, stableJson } from './lib/kernel-utils.mjs';

export function createPortIntent(scenePack, portId, operation, legacyLabel = null) {
  const binding = scenePack.optionalPortBindings.find((item) => item.portId === portId && item.operation === operation && (!legacyLabel || item.legacyLabel === legacyLabel));
  if (!binding) return { ok: false, status: 'not_declared', issues: ['port_intent_not_declared'], intent: null };
  const projection = { sceneId: scenePack.sceneId, legacyLabel: binding.legacyLabel, portId, operation, minimumDataScope: binding.minimumDataScope, writeMode: binding.writeMode };
  return { ok: true, status: 'intent_only', issues: [], intent: { ...projection, approvalRequired: binding.approvalRequired, readbackRequired: binding.readbackRequired, executionAllowed: false, adapterStatus: 'optional_adapter_registered_intent_only', fallback: 'local_workflow_without_connector', intentDigest: sha256(stableJson(projection)) } };
}
