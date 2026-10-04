import { sha256, stableJson } from './lib/kernel-utils.mjs';

export function planArtifacts(scenePack) {
  return scenePack.artifactRefs.map((item) => ({ artifactId: item.artifactId, archetypeId: item.archetypeId, state: 'planned_descriptor', contentGenerated: false, deliveryReady: false, planDigest: sha256(stableJson({ sceneId: scenePack.sceneId, artifactId: item.artifactId, archetypeId: item.archetypeId })) }));
}

export function validateArtifactPlan(scenePack, plans) {
  const expected = planArtifacts(scenePack);
  const ok = stableJson(expected) === stableJson(plans) && plans.every((item) => item.contentGenerated === false && item.deliveryReady === false);
  return { ok, issues: ok ? [] : ['artifact_plan_mismatch'] };
}
