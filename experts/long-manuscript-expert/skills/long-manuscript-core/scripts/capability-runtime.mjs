import { asArray, capabilityResult, capabilityRuntimePolicyDigest, escapeHtml, measuredWords, normalizeCapabilityContext, riskMax, sealCapabilityResult, sha256, stableJson, unique } from './lib/kernel-utils.mjs';

export const operationModes = [
  'material_activation', 'project_planning', 'chapter_generation', 'continuation', 'bounded_revision',
  'review_quality', 'finished_draft_closure', 'template_fill_conversion', 'export_delivery', 'asset_repurposing'
];

function sceneRouter(input) {
  const explicit = input?.explicit ?? {};
  const signals = input?.signals ?? {};
  let operationMode = explicit.operationMode ?? null;
  let routeSource = operationMode ? 'explicit' : 'fallback';
  const ambiguity = [];
  if (!operationMode && input?.legacyId === 'material_activation') { operationMode = 'material_activation'; routeSource = 'legacy_adapter'; }
  if (!operationMode && input?.legacyId === 'finished_draft_closure') { operationMode = 'finished_draft_closure'; routeSource = 'legacy_adapter'; }
  if (!operationMode && input?.legacyId === 'continuation_or_revision') {
    routeSource = 'legacy_adapter';
    const continueSignal = Boolean(signals.continue);
    const editSignal = Boolean(signals.editScope || signals.change);
    if (continueSignal !== editSignal) operationMode = continueSignal ? 'continuation' : 'bounded_revision';
    else { operationMode = 'needs_clarification'; ambiguity.push('continuation_vs_bounded_revision'); }
  }
  if (!operationMode) operationMode = 'material_activation';
  const domainScene = explicit.domainScene ?? input?.domainScene ?? 'general';
  const validOperation = operationModes.includes(operationMode) || operationMode === 'needs_clarification';
  return capabilityResult('scene-router', input, {
    status: operationMode === 'needs_clarification' ? 'needs_clarification' : validOperation ? 'completed' : 'rejected',
    ok: validOperation && operationMode !== 'needs_clarification',
    output: { operationMode, domainScene, routeSource, ambiguity, connectorInfluencedRoute: false, fallbackReason: domainScene === 'general' && routeSource === 'legacy_adapter' ? 'legacy_no_domain_signal' : null },
    issues: validOperation ? ambiguity : ['unknown_operation_mode']
  });
}

function sceneComposer(input) {
  const scenes = asArray(input?.scenes);
  const ids = scenes.map((item) => item.sceneId);
  const issues = [];
  if (scenes.length < 2) issues.push('composition_requires_two_scenes');
  if (ids.includes('general')) issues.push('general_cannot_be_composed');
  if (new Set(ids).size !== ids.length) issues.push('duplicate_scene');
  return capabilityResult('scene-composer', input, {
    ok: issues.length === 0,
    status: issues.length ? 'rejected' : 'completed',
    output: {
      composedDomainScenes: issues.length === 0 ? unique(ids.filter((id) => id !== 'general')) : [],
      contentRiskClass: riskMax(scenes.map((item) => item.contentRiskClass)),
      qualityGateRefs: issues.length === 0 ? unique(scenes.flatMap((item) => asArray(item.qualityGateRefs))) : [],
      artifactRefs: issues.length === 0 ? unique(scenes.flatMap((item) => asArray(item.artifactRefs))) : []
    },
    issues
  });
}

function materialActivation(input) {
  const materials = asArray(input?.materials);
  const normalized = materials.map((item, index) => ({ id: item.id ?? `material-${index + 1}`, kind: item.kind ?? 'text', hasSummary: Boolean(item.summary || item.text), sourceKnown: Boolean(item.source), rightsKnown: Boolean(item.rightsStatus) }));
  const gaps = [];
  if (materials.length === 0) gaps.push('no_material');
  for (const item of normalized) {
    if (!item.hasSummary) gaps.push(`${item.id}:summary_missing`);
    if (!item.sourceKnown) gaps.push(`${item.id}:source_missing`);
  }
  const draftingReady = normalized.length > 0 && gaps.length === 0;
  return capabilityResult('material-activation', input, {
    ok: draftingReady,
    status: materials.length === 0 ? 'needs_input' : draftingReady ? 'activated' : 'activation_pending',
    output: { inventory: normalized, materialCount: normalized.length, inventoryReady: normalized.length > 0, draftingReady, firstValueReady: normalized.length > 0, proposedOperationMode: 'project_planning', gaps, blockingFact: gaps[0] ?? null },
    issues: materials.length === 0 ? ['one_material_or_goal_required'] : gaps
  });
}

function multimodalNormalizer(input) {
  const supported = new Set(['text', 'markdown', 'document', 'table', 'pdf', 'image', 'audio', 'transcript']);
  const items = asArray(input?.items).map((item, index) => ({ id: item.id ?? `item-${index + 1}`, kind: String(item.kind ?? 'unknown').toLowerCase(), name: item.name ?? null, extractionState: supported.has(String(item.kind ?? '').toLowerCase()) ? 'descriptor_ready' : 'unsupported', uncertainty: item.uncertainty ?? null }));
  const unsupported = items.filter((item) => item.extractionState === 'unsupported').map((item) => item.id);
  const descriptorReady = items.some((item) => item.extractionState === 'descriptor_ready');
  return capabilityResult('multimodal-normalizer', input, {
    ok: descriptorReady,
    status: items.length === 0 ? 'needs_input' : unsupported.length === items.length ? 'degraded' : 'descriptor_ready',
    output: { manifest: items, unsupportedIds: unsupported, contentExtractionPerformed: false },
    issues: items.length === 0 ? ['item_required'] : [],
    warnings: unsupported.map((id) => `${id}:unsupported_format`)
  });
}

function researchVerification(input) {
  const claims = asArray(input?.claims);
  const sourceReceipts = new Map(asArray(input?.sourceReceipts).filter((receipt) => {
    const payload = { sourceRef: receipt?.sourceRef, observedAt: receipt?.observedAt, contentDigest: receipt?.contentDigest, qualityDecision: receipt?.qualityDecision };
    return typeof receipt?.sourceRef === 'string' && !Number.isNaN(Date.parse(receipt?.observedAt)) && /^[a-f0-9]{64}$/u.test(String(receipt?.contentDigest ?? '')) && ['accepted', 'rejected', 'needs_review'].includes(receipt?.qualityDecision) && receipt?.receiptDigest === sha256(stableJson(payload));
  }).map((receipt) => [receipt.sourceRef, receipt]));
  const assessed = claims.map((claim, index) => {
    const id = claim.id ?? `claim-${index + 1}`;
    const sourceRefs = asArray(claim.sourceRefs);
    const stale = claim.freshness === 'stale';
    const conflicting = Boolean(claim.conflictingSources);
    const receiptsBound = sourceRefs.length > 0 && sourceRefs.every((sourceRef) => sourceReceipts.get(sourceRef)?.qualityDecision === 'accepted');
    return { id, sourceRefs, freshness: claim.freshness ?? 'unknown', receiptsBound, status: receiptsBound && !stale && !conflicting ? 'evidence_bound_pending_quality_gate' : conflicting ? 'conflicting' : 'unverified' };
  });
  const unverified = assessed.filter((item) => item.status !== 'evidence_bound_pending_quality_gate').map((item) => item.id);
  return capabilityResult('research-verification', input, {
    ok: false,
    status: claims.length === 0 ? 'needs_input' : input?.offlineMode ? 'offline_degraded' : 'verification_planned',
    output: { claims: assessed, unverifiedClaimIds: unverified, verificationPlan: assessed.map((item) => ({ claimId: item.id, action: item.receiptsBound ? 'run_c5_source_quality_gate' : input?.offlineMode ? 'mark_unverified_and_request_source' : 'bind_current_source_receipt' })), networkUsed: false, sourceReceiptCount: sourceReceipts.size, qualityGateActive: false },
    issues: claims.length === 0 ? ['claim_required'] : ['source_quality_gate_pending', ...unverified.map((id) => `${id}:unverified`)]
  });
}

function sourceClaimGraph(input) {
  const sources = asArray(input?.sources);
  const claims = asArray(input?.claims);
  const sourceComplete = (item) => typeof item.id === 'string' && item.id.length > 0 && typeof item.locator === 'string' && item.locator.length > 0 && typeof item.title === 'string' && item.title.length > 0 && !Number.isNaN(Date.parse(item.observedAt)) && ['primary', 'secondary', 'official', 'user_supplied'].includes(item.quality) && /^[a-f0-9]{64}$/u.test(String(item.contentDigest ?? ''));
  const sourceIds = new Set(sources.filter(sourceComplete).map((item) => item.id));
  const incompleteSources = sources.filter((item) => !sourceComplete(item)).map((item) => item?.id ?? 'unknown');
  const dangling = [];
  const edges = [];
  for (const claim of claims) {
    for (const sourceId of asArray(claim.sourceIds)) {
      if (sourceIds.has(sourceId)) edges.push({ claimId: claim.id, sourceId, relation: 'supported_by' });
      else dangling.push(`${claim.id}->${sourceId}`);
    }
  }
  const unsupported = claims.filter((claim) => asArray(claim.sourceIds).length === 0).map((claim) => claim.id);
  const claimGraph = { schemaVersion: '1.1.0', claims: claims.map((item) => ({ id: item.id, text: String(item.text ?? ''), status: asArray(item.sourceIds).length > 0 && asArray(item.sourceIds).every((sourceId) => sourceIds.has(sourceId)) ? 'supported' : 'unverified', chapterRefs: asArray(item.chapterRefs) })), edges };
  return capabilityResult('source-ledger-claim-graph', input, {
    ok: claims.length > 0 && sources.length > 0 && incompleteSources.length === 0 && dangling.length === 0 && unsupported.length === 0,
    status: claims.length === 0 ? 'needs_input' : incompleteSources.length === 0 && dangling.length === 0 && unsupported.length === 0 && sources.length > 0 ? 'completed' : 'verification_required',
    output: claimGraph,
    issues: [...(sources.length === 0 ? ['source_required'] : []), ...(claims.length === 0 ? ['claim_required'] : []), ...incompleteSources.map((id) => `${id}:source_evidence_incomplete`), ...unsupported.map((id) => `${id}:unsupported`), ...dangling.map((id) => `${id}:dangling`)]
  });
}

function entityTimeline(input) {
  const entities = asArray(input?.entities);
  const events = asArray(input?.events);
  const aliasOwner = new Map();
  const conflicts = [];
  for (const entity of entities) {
    for (const alias of unique([entity.name, ...asArray(entity.aliases)].filter(Boolean))) {
      const key = alias.toLocaleLowerCase('en-US');
      if (aliasOwner.has(key) && aliasOwner.get(key) !== entity.id) conflicts.push(`alias:${alias}`);
      else aliasOwner.set(key, entity.id);
    }
  }
  const validEntityIds = new Set(entities.map((item) => item.id));
  const normalizedEvents = events.map((event) => ({ ...event, validDate: !Number.isNaN(Date.parse(event.date)), unknownEntityIds: asArray(event.entityIds).filter((id) => !validEntityIds.has(id)) }));
  for (const event of normalizedEvents) {
    if (!event.validDate) conflicts.push(`event:${event.id}:invalid_date`);
    for (const id of event.unknownEntityIds) conflicts.push(`event:${event.id}:unknown_entity:${id}`);
  }
  const entityById = new Map(entities.map((entity) => [entity.id, entity]));
  const chapterRefs = asArray(input?.chapterEntityRefs);
  for (const reference of chapterRefs) {
    const entity = entityById.get(reference.entityId);
    const allowedNames = new Set(entity ? [entity.name, ...asArray(entity.aliases)].filter(Boolean).map((name) => String(name).toLocaleLowerCase('en-US')) : []);
    if (!entity) conflicts.push(`chapter:${reference.chapterId}:unknown_entity:${reference.entityId}`);
    else if (!allowedNames.has(String(reference.displayName ?? '').toLocaleLowerCase('en-US'))) conflicts.push(`chapter:${reference.chapterId}:cross_chapter_drift:${reference.entityId}`);
  }
  const aliasMap = Object.fromEntries([...aliasOwner.entries()].sort(([left], [right]) => left.localeCompare(right, 'en')));
  return capabilityResult('entity-timeline-continuity', input, { ok: conflicts.length === 0, status: conflicts.length ? 'continuity_conflict' : 'completed', output: { entityCount: entities.length, events: normalizedEvents, aliasMap, crossChapterReferenceCount: chapterRefs.length, conflicts }, issues: conflicts });
}

function scopeLockDiff(input) {
  const isCanonicalScope = (value) => typeof value === 'string' && value.length > 0 && value.length <= 512 && !value.includes('\\') && !value.includes('%') && !value.startsWith('/') && !value.endsWith('/') && value.split('/').every((segment) => segment && segment !== '.' && segment !== '..');
  const digestPattern = /^[a-f0-9]{64}$/u;
  const allowed = asArray(input?.lock?.allowedScopes);
  const forbidden = asArray(input?.lock?.forbiddenScopes);
  const changes = asArray(input?.changes);
  const invalidAllowedScopes = [...allowed, ...forbidden].filter((scope) => !isCanonicalScope(scope));
  const isWithin = (candidate, scope) => candidate === scope || candidate.startsWith(`${scope}/`);
  const approvalPayload = { allowedScopes: unique(allowed), forbiddenScopes: unique(forbidden), originalDigests: input?.lock?.originalDigests ?? {} };
  const expectedScopeDigest = sha256(stableJson(approvalPayload));
  const expectedApprovalReceiptDigest = sha256(stableJson({ type: 'scope_approval', scopeDigest: expectedScopeDigest, decision: 'approved' }));
  const approvalReceipt = input?.lock?.approvalReceipt;
  const approvalExplicit = input?.lock?.approvalState === 'explicit' && approvalReceipt?.decision === 'approved' && approvalReceipt?.scopeDigest === expectedScopeDigest && approvalReceipt?.receiptDigest === expectedApprovalReceiptDigest;
  const authorized = changes.filter((item) => invalidAllowedScopes.length === 0 && approvalExplicit && isCanonicalScope(item.scope) && digestPattern.test(String(item.beforeDigest ?? '')) && input?.lock?.originalDigests?.[item.scope] === item.beforeDigest && allowed.some((scope) => isWithin(item.scope, scope)) && !forbidden.some((scope) => isWithin(item.scope, scope)));
  const unauthorized = changes.filter((item) => !authorized.includes(item));
  const issues = [
    ...invalidAllowedScopes.map((scope) => `${scope}:invalid_allowed_scope`),
    ...(!approvalExplicit ? ['scope_approval_required'] : []),
    ...unauthorized.map((item) => !isCanonicalScope(item.scope) ? `${item.scope}:invalid_scope` : !digestPattern.test(String(item.beforeDigest ?? '')) ? `${item.scope}:rollback_digest_required` : input?.lock?.originalDigests?.[item.scope] !== item.beforeDigest ? `${item.scope}:original_digest_mismatch` : forbidden.some((scope) => isWithin(item.scope, scope)) ? `${item.scope}:forbidden_scope` : `${item.scope}:outside_scope`)
  ];
  return capabilityResult('scope-lock-diff', input, {
    ok: changes.length > 0 && issues.length === 0,
    status: changes.length === 0 ? 'needs_input' : issues.length ? 'rejected' : 'completed',
    output: { approvalReceiptValid: approvalExplicit, authorizedChanges: authorized, unauthorizedChanges: unauthorized, rollbackPlan: authorized.map((item) => ({ scope: item.scope, restoreFromDigest: item.beforeDigest })) },
    issues: changes.length === 0 ? ['change_required'] : issues
  });
}

function voiceProfile(input) {
  const text = String(input?.text ?? '');
  const profile = input?.profile ?? {};
  const forbiddenHits = asArray(profile.forbiddenPhrases).filter((phrase) => phrase && text.includes(phrase));
  const requiredMissing = asArray(profile.requiredPhrases).filter((phrase) => phrase && !text.includes(phrase));
  const issues = [...forbiddenHits.map((item) => `forbidden:${item}`), ...requiredMissing.map((item) => `missing:${item}`)];
  const facts = asArray(input?.facts);
  return capabilityResult('voice-profile-humanizer', input, { ok: issues.length === 0, status: issues.length ? 'revision_required' : 'assessment_completed', output: { forbiddenHits, requiredMissing, factPreservationRequired: true, factAnchorDigest: sha256(stableJson(facts)), detectorEvasionObjective: false, transformationPerformed: false }, issues });
}

function chapterPlanning(input) {
  const chapters = asArray(input?.chapters).map((chapter) => {
    const measuredWordCount = measuredWords(chapter.text);
    const targetWordCount = Number(chapter.targetWordCount ?? 0);
    const planComplete = Boolean(chapter.id && chapter.title && chapter.promise && asArray(chapter.materialRefs).length && targetWordCount > 0);
    const status = !planComplete ? 'blocked' : measuredWordCount >= targetWordCount ? 'complete' : chapter.text ? 'drafting' : 'planned';
    return { id: chapter.id, title: chapter.title ?? '', promise: chapter.promise ?? '', materialRefs: asArray(chapter.materialRefs), claimRefs: asArray(chapter.claimRefs), targetWordCount, status };
  });
  const incomplete = chapters.filter((item) => item.status === 'blocked').map((item) => item.id);
  const allExpanded = chapters.length > 0 && chapters.every((item) => item.status === 'complete');
  return capabilityResult('chapter-planning-expansion', input, { ok: incomplete.length === 0 && chapters.length > 0, status: chapters.length === 0 ? 'needs_input' : incomplete.length ? 'plan_incomplete' : allExpanded ? 'expanded' : 'plan_ready', output: { schemaVersion: '1.1.0', chapters }, issues: chapters.length === 0 ? ['chapter_required'] : incomplete.map((id) => `${id}:incomplete_plan`) });
}

function reviewLoop(input) {
  const issues = asArray(input?.issues).filter((item) => !item.resolved);
  const round = Number(input?.round ?? 1);
  const maxRounds = Number(input?.maxRounds ?? 3);
  const critical = issues.filter((item) => item.severity === 'critical');
  const reviewerFailed = input?.reviewerExecution?.status === 'failed';
  const requiredGateIdsRaw = asArray(input?.requiredGateIds);
  const requiredGateIds = unique(requiredGateIdsRaw);
  const requiredGateReceipts = asArray(input?.requiredGateReceipts);
  const receiptGateIds = requiredGateReceipts.map((item) => item?.gateId);
  const receiptsUnique = new Set(receiptGateIds).size === receiptGateIds.length;
  const requiredGateIdsUnique = new Set(requiredGateIdsRaw).size === requiredGateIdsRaw.length;
  const gateEvidenceValid = requiredGateIds.length > 0 && requiredGateIdsUnique && receiptsUnique && stableJson(unique(receiptGateIds)) === stableJson(requiredGateIds) && requiredGateReceipts.every((item) => {
    if (!item?.gateId || item.status !== 'passed' || !/^[a-f0-9]{64}$/u.test(String(item.resultDigest ?? ''))) return false;
    return item.receiptDigest === sha256(stableJson({ gateId: item.gateId, status: item.status, resultDigest: item.resultDigest }));
  });
  const boundsValid = Number.isInteger(round) && Number.isInteger(maxRounds) && round >= 1 && maxRounds >= 1 && maxRounds <= 10 && round <= maxRounds;
  let state = !boundsValid ? 'rejected' : reviewerFailed ? 'human_review_pending' : issues.length === 0 && gateEvidenceValid ? 'passed' : issues.length === 0 ? 'verification_required' : critical.length > 0 && round >= maxRounds ? 'human_review_required' : round >= maxRounds ? 'max_round_reached' : 'revise';
  const reviewIssues = [...critical.map((item) => `${item.id}:critical`), ...(!boundsValid ? ['review_round_bounds_invalid'] : []), ...(reviewerFailed ? ['reviewer_execution_failed'] : []), ...(issues.length === 0 && !reviewerFailed && !gateEvidenceValid ? ['quality_gate_receipt_required'] : [])];
  return capabilityResult('review-revise-quality-loop', input, { ok: state === 'passed', status: state, output: { state, round, maxRounds, reviewerExecutionState: input?.reviewerExecution?.status ?? 'not_reported', openIssueIds: issues.map((item) => item.id), criticalIssueIds: critical.map((item) => item.id), requiredGateIds, requiredGateReceiptCount: requiredGateReceipts.length, gateEvidenceValid, nextRound: state === 'revise' ? round + 1 : null }, issues: reviewIssues });
}

function rightsPrivacy(input) {
  const items = asArray(input?.items);
  const issues = items.length === 0 ? ['rights_item_required'] : [];
  const allowedRights = new Set(['cleared', 'owned', 'licensed', 'public_domain']);
  const receiptValid = (receipt, type, itemId, decision) => {
    if (!receipt || receipt.type !== type || receipt.itemId !== itemId || receipt.decision !== decision || !/^[a-f0-9]{64}$/u.test(String(receipt.evidenceDigest ?? ''))) return false;
    return receipt.receiptDigest === sha256(stableJson({ type, itemId, decision, evidenceDigest: receipt.evidenceDigest }));
  };
  const assessments = [];
  for (const item of items) {
    const itemIssues = [];
    if (item.livingPerson && (item.consentStatus !== 'present' || !receiptValid(item.consentReceipt, 'living_person_consent', item.id, 'present'))) itemIssues.push('living_person_consent_missing');
    if (item.rightsStatus === 'denied') itemIssues.push('rights_denied');
    else if (!allowedRights.has(item.rightsStatus)) itemIssues.push('rights_unknown');
    if (['private', 'restricted'].includes(item.privacyClass) && !receiptValid(item.privacyHandlingReceipt, 'privacy_handling', item.id, 'approved')) itemIssues.push('privacy_handling_required');
    if (item.restrictedKnowledge && !receiptValid(item.humanReviewReceipt, 'human_review', item.id, 'approved')) itemIssues.push('human_review_required');
    issues.push(...itemIssues.map((issue) => `${item.id}:${issue}`));
    assessments.push({ itemId: item.id, decision: itemIssues.length === 0 ? 'allow' : itemIssues.includes('rights_denied') ? 'block' : 'needs_review', reasons: itemIssues, evidenceLevel: itemIssues.length === 0 ? 'validated_local_receipt' : 'insufficient_evidence' });
  }
  let denied = issues.some((issue) => issue.endsWith(':rights_denied'));
  const requestedFields = asArray(input?.requestedFields);
  const approvedFields = new Set(asArray(input?.approvedFields));
  const minimumDataScope = requestedFields.length > 0 ? requestedFields.every((field) => approvedFields.has(field)) : null;
  if (minimumDataScope === false) { issues.push('minimum_data_scope_violation'); denied = true; }
  return capabilityResult('rights-privacy-consent', input, { ok: issues.length === 0, status: items.length === 0 ? 'needs_input' : denied ? 'release_blocked' : issues.length ? 'human_review_pending' : 'completed', output: { itemCount: items.length, assessments, releaseAllowed: issues.length === 0 && items.length > 0 && minimumDataScope !== false, minimumDataScope, minimumDataScopeEvaluated: requestedFields.length > 0 }, issues });
}

function multiFormatRendering(input) {
  const title = String(input?.title ?? 'Untitled');
  const sections = asArray(input?.sections);
  const markdown = [`# ${title}`, ...sections.flatMap((section) => ['', `## ${section.heading ?? 'Section'}`, String(section.body ?? '')])].join('\n');
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title></head><body><h1>${escapeHtml(title)}</h1>${sections.map((section) => `<section><h2>${escapeHtml(section.heading ?? 'Section')}</h2><p>${escapeHtml(section.body ?? '')}</p></section>`).join('')}</body></html>`;
  const requested = unique(asArray(input?.formats).length ? input.formats : ['markdown']);
  const artifacts = [];
  const unavailable = [];
  for (const format of requested) {
    if (format === 'markdown') artifacts.push({ format, mimeType: 'text/markdown; charset=utf-8', content: markdown, byteLength: Buffer.byteLength(markdown, 'utf8'), sha256: sha256(Buffer.from(markdown, 'utf8')), artifactState: 'in_memory', structuralChecks: { titleHeading: markdown.startsWith(`# ${title}`), sectionHeadingCount: sections.length } });
    else if (format === 'html') artifacts.push({ format, mimeType: 'text/html; charset=utf-8', content: html, byteLength: Buffer.byteLength(html, 'utf8'), sha256: sha256(Buffer.from(html, 'utf8')), artifactState: 'in_memory', structuralChecks: { htmlDocument: html.startsWith('<!doctype html>'), titleHeading: html.includes(`<h1>${escapeHtml(title)}</h1>`), sectionHeadingCount: sections.length } });
    else unavailable.push({ format, fallback: 'markdown', reason: 'binary_renderer_not_available_in_core_runtime' });
  }
  const qualityEvidenceValid = /^[a-f0-9]{64}$/u.test(String(input?.qualityReceiptDigest ?? ''));
  const rightsEvidenceValid = /^[a-f0-9]{64}$/u.test(String(input?.rightsReceiptDigest ?? ''));
  const deliveryReady = ['reviewed', 'delivery_ready', 'delivered'].includes(input?.qualityState) && sections.length > 0 && qualityEvidenceValid && rightsEvidenceValid;
  return capabilityResult('multi-format-rendering', input, { ok: artifacts.length > 0 && deliveryReady, status: deliveryReady ? (unavailable.length ? 'degraded' : 'completed') : 'quality_gate_required', output: { artifacts, unavailable, deliveryReady, qualityEvidenceValid, rightsEvidenceValid, fileWritePerformed: false, externalDeliveryPerformed: false }, issues: deliveryReady ? [] : sections.length === 0 ? ['content_required'] : ['quality_and_rights_receipts_required'], warnings: unavailable.map((item) => `${item.format}:degraded_to_markdown`) });
}

function mediaPlanning(input) {
  const items = asArray(input?.items).map((item, index) => ({ id: item.id ?? `media-${index + 1}`, kind: item.kind ?? 'image', purpose: item.purpose ?? null, caption: item.caption ?? null, source: item.source ?? null, rightsStatus: item.rightsStatus ?? 'unknown', placement: item.placement ?? null }));
  const gaps = items.length === 0 ? ['no_media'] : [];
  for (const item of items) {
    if (!item.caption) gaps.push(`${item.id}:caption_missing`);
    if (!item.source) gaps.push(`${item.id}:source_missing`);
    if (item.rightsStatus !== 'cleared') gaps.push(`${item.id}:rights_not_cleared`);
  }
  return capabilityResult('media-illustration-planning', input, { ok: gaps.length === 0 && items.length > 0, status: items.length ? (gaps.length ? 'planning_incomplete' : 'completed') : 'needs_input', output: { mediaManifest: items, gaps, mediaGenerated: false }, issues: gaps });
}

function continuationRecovery(input) {
  if (input?.capsule) {
    const required = ['documentType', 'audience', 'goal', 'completedSections', 'currentAnchor', 'constraints', 'nextObjective'];
    const missing = required.filter((field) => ['completedSections', 'constraints'].includes(field) ? !Array.isArray(input.capsule[field]) : typeof input.capsule[field] !== 'string' || !input.capsule[field].trim());
    const capsule = { documentType: input.capsule.documentType ?? '', audience: input.capsule.audience ?? '', goal: input.capsule.goal ?? '', completedSections: asArray(input.capsule.completedSections), currentAnchor: input.capsule.currentAnchor ?? '', constraints: asArray(input.capsule.constraints), openEvidenceGaps: asArray(input.capsule.openEvidenceGaps), nextObjective: input.capsule.nextObjective ?? '', savedBySystem: false };
    return capabilityResult('continuation-recovery', input, { ok: missing.length === 0, status: missing.length ? 'state_conflict' : 'completed', output: { capsule, capsuleDigest: sha256(stableJson(capsule)), missingFields: missing }, issues: missing.map((field) => `${field}:missing`) });
  }
  const project = input?.project ?? {};
  const capsule = { documentType: project.documentType ?? null, audience: project.audience ?? null, goal: project.goal ?? null, completedSections: asArray(project.completedSections), currentAnchor: project.currentAnchor ?? null, constraints: asArray(project.constraints), openEvidenceGaps: asArray(project.openEvidenceGaps), nextObjective: project.nextObjective ?? null, savedBySystem: false };
  const missing = ['documentType', 'audience', 'goal', 'currentAnchor', 'nextObjective'].filter((field) => !capsule[field]);
  return capabilityResult('continuation-recovery', input, { ok: missing.length === 0, status: missing.length ? 'needs_input' : 'completed', output: { capsule, capsuleDigest: sha256(stableJson(capsule)), missingFields: missing }, issues: missing.map((field) => `${field}:missing`) });
}

function assetRepurposing(input) {
  const allowed = ['reviewed', 'delivery_ready', 'delivered'].includes(input?.qualityState) && /^[a-f0-9]{64}$/u.test(String(input?.qualityReceiptDigest ?? ''));
  const channels = unique(asArray(input?.targetChannels));
  const provenanceReady = Boolean(input?.sourceArtifactId && input?.factGraphRef);
  const briefs = allowed && provenanceReady ? channels.map((channel) => ({ channel, sourceArtifactId: input.sourceArtifactId, factGraphRef: input.factGraphRef, adaptationRules: ['preserve_verified_facts', 'adapt_length_and_structure', 'do_not_invent_claims'] })) : [];
  return capabilityResult('asset-repurposing', input, { ok: allowed && provenanceReady && channels.length > 0, status: !allowed ? 'quality_gate_required' : !provenanceReady ? 'needs_input' : channels.length ? 'repurposing_planned' : 'needs_input', output: { briefs, qualityGateSatisfied: allowed, provenanceReady, contentGenerated: false }, issues: !allowed ? ['quality_gate_required'] : !provenanceReady ? ['source_artifact_and_fact_graph_required'] : channels.length ? [] : ['target_channel_required'] });
}

const handlers = {
  'scene-router': sceneRouter,
  'scene-composer': sceneComposer,
  'material-activation': materialActivation,
  'multimodal-normalizer': multimodalNormalizer,
  'research-verification': researchVerification,
  'source-ledger-claim-graph': sourceClaimGraph,
  'entity-timeline-continuity': entityTimeline,
  'scope-lock-diff': scopeLockDiff,
  'voice-profile-humanizer': voiceProfile,
  'chapter-planning-expansion': chapterPlanning,
  'review-revise-quality-loop': reviewLoop,
  'rights-privacy-consent': rightsPrivacy,
  'multi-format-rendering': multiFormatRendering,
  'media-illustration-planning': mediaPlanning,
  'continuation-recovery': continuationRecovery,
  'asset-repurposing': assetRepurposing
};

export const capabilityIds = Object.freeze(Object.keys(handlers));
const isPlainObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value) && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
const contextShapeValid = (context) => isPlainObject(context) && Object.keys(context).sort().join(',') === 'connectorAvailable,externalWriteAuthorized' && typeof context.connectorAvailable === 'boolean' && typeof context.externalWriteAuthorized === 'boolean';
const exactKeys = (value, keys) => isPlainObject(value) && Object.keys(value).sort().join(',') === [...keys].sort().join(',');
const receiptShapeValid = (receipt) => exactKeys(receipt, ['schemaVersion', 'capabilityId', 'inputDigest', 'contextDigest', 'invocationDigest', 'policyDigest', 'resultDigest', 'externalActionCount', 'connectorRequired', 'donorSkillUsed']);
const resultShapeValid = (result) => exactKeys(result, ['capabilityId', 'status', 'ok', 'output', 'issues', 'warnings', 'context', 'receipt']) && typeof result.capabilityId === 'string' && result.capabilityId.length > 0 && typeof result.status === 'string' && result.status.length > 0 && typeof result.ok === 'boolean' && isPlainObject(result.output) && Array.isArray(result.issues) && result.issues.every((item) => typeof item === 'string') && new Set(result.issues).size === result.issues.length && Array.isArray(result.warnings) && result.warnings.every((item) => typeof item === 'string') && new Set(result.warnings).size === result.warnings.length && contextShapeValid(result.context) && receiptShapeValid(result.receipt);

function validateNestedInput(capabilityId, input) {
  const issues = [];
  const object = (value, path, required = false) => {
    if (value === undefined && !required) return true;
    if (!isPlainObject(value)) { issues.push(`nested_input_invalid:${path}`); return false; }
    return true;
  };
  const objectArray = (value, path, itemCheck = null) => {
    if (value === undefined) return;
    if (!Array.isArray(value)) { issues.push(`nested_input_invalid:${path}`); return; }
    value.forEach((item, index) => {
      if (!isPlainObject(item)) issues.push(`nested_input_invalid:${path}[${index}]`);
      else if (itemCheck) itemCheck(item, `${path}[${index}]`);
    });
  };
  const stringArray = (value, path) => {
    if (value === undefined) return;
    if (!Array.isArray(value)) { issues.push(`nested_input_invalid:${path}`); return; }
    value.forEach((item, index) => { if (typeof item !== 'string') issues.push(`nested_input_invalid:${path}[${index}]`); });
  };

  if (capabilityId === 'scene-router') { object(input.explicit, 'explicit'); object(input.signals, 'signals'); }
  if (capabilityId === 'scene-composer') objectArray(input.scenes, 'scenes', (item, pathValue) => { stringArray(item.qualityGateRefs, `${pathValue}.qualityGateRefs`); stringArray(item.artifactRefs, `${pathValue}.artifactRefs`); });
  if (capabilityId === 'material-activation') objectArray(input.materials, 'materials');
  if (capabilityId === 'multimodal-normalizer') objectArray(input.items, 'items');
  if (capabilityId === 'research-verification') {
    objectArray(input.claims, 'claims', (item, pathValue) => stringArray(item.sourceRefs, `${pathValue}.sourceRefs`));
    objectArray(input.sourceReceipts, 'sourceReceipts');
  }
  if (capabilityId === 'source-ledger-claim-graph') {
    objectArray(input.sources, 'sources');
    objectArray(input.claims, 'claims', (item, pathValue) => { stringArray(item.sourceIds, `${pathValue}.sourceIds`); stringArray(item.chapterRefs, `${pathValue}.chapterRefs`); });
  }
  if (capabilityId === 'entity-timeline-continuity') {
    objectArray(input.entities, 'entities', (item, pathValue) => stringArray(item.aliases, `${pathValue}.aliases`));
    objectArray(input.events, 'events', (item, pathValue) => stringArray(item.entityIds, `${pathValue}.entityIds`));
    objectArray(input.chapterEntityRefs, 'chapterEntityRefs');
  }
  if (capabilityId === 'scope-lock-diff') {
    if (object(input.lock, 'lock')) {
      stringArray(input.lock?.allowedScopes, 'lock.allowedScopes');
      stringArray(input.lock?.forbiddenScopes, 'lock.forbiddenScopes');
      object(input.lock?.originalDigests, 'lock.originalDigests');
      object(input.lock?.approvalReceipt, 'lock.approvalReceipt');
    }
    objectArray(input.changes, 'changes');
  }
  if (capabilityId === 'voice-profile-humanizer') {
    if (object(input.profile, 'profile')) {
      stringArray(input.profile?.forbiddenPhrases, 'profile.forbiddenPhrases');
      stringArray(input.profile?.requiredPhrases, 'profile.requiredPhrases');
    }
    if (input.facts !== undefined && !Array.isArray(input.facts)) issues.push('nested_input_invalid:facts');
  }
  if (capabilityId === 'chapter-planning-expansion') objectArray(input.chapters, 'chapters', (item, pathValue) => { stringArray(item.materialRefs, `${pathValue}.materialRefs`); stringArray(item.claimRefs, `${pathValue}.claimRefs`); object(item.expansionApprovalReceipt, `${pathValue}.expansionApprovalReceipt`); });
  if (capabilityId === 'review-revise-quality-loop') {
    objectArray(input.issues, 'issues');
    stringArray(input.requiredGateIds, 'requiredGateIds');
    objectArray(input.requiredGateReceipts, 'requiredGateReceipts');
    object(input.reviewerExecution, 'reviewerExecution');
  }
  if (capabilityId === 'rights-privacy-consent') {
    objectArray(input.items, 'items', (item, pathValue) => {
      object(item.consentReceipt, `${pathValue}.consentReceipt`);
      object(item.privacyHandlingReceipt, `${pathValue}.privacyHandlingReceipt`);
      object(item.humanReviewReceipt, `${pathValue}.humanReviewReceipt`);
    });
    stringArray(input.requestedFields, 'requestedFields');
    stringArray(input.approvedFields, 'approvedFields');
  }
  if (capabilityId === 'multi-format-rendering') { objectArray(input.sections, 'sections'); stringArray(input.formats, 'formats'); }
  if (capabilityId === 'media-illustration-planning') objectArray(input.items, 'items');
  if (capabilityId === 'continuation-recovery') {
    if (object(input.capsule, 'capsule')) {
      stringArray(input.capsule?.completedSections, 'capsule.completedSections');
      stringArray(input.capsule?.constraints, 'capsule.constraints');
      stringArray(input.capsule?.openEvidenceGaps, 'capsule.openEvidenceGaps');
    }
    if (object(input.project, 'project')) {
      stringArray(input.project?.completedSections, 'project.completedSections');
      stringArray(input.project?.constraints, 'project.constraints');
      stringArray(input.project?.openEvidenceGaps, 'project.openEvidenceGaps');
    }
  }
  if (capabilityId === 'asset-repurposing') stringArray(input.targetChannels, 'targetChannels');
  return unique(issues);
}

export function runCapability(capabilityId, input = {}, context = { connectorAvailable: false, externalWriteAuthorized: false }) {
  const invocationIssues = [...(!isPlainObject(input) ? ['input_object_required'] : []), ...(!contextShapeValid(context) ? ['context_shape_invalid'] : []), ...(isPlainObject(input) ? validateNestedInput(capabilityId, input) : [])];
  let result;
  if (invocationIssues.length > 0) result = capabilityResult(capabilityId, input, { ok: false, status: 'invalid_invocation', issues: invocationIssues });
  else if (!Object.hasOwn(handlers, capabilityId)) result = capabilityResult(capabilityId, input, { ok: false, status: 'unknown_capability', issues: ['unknown_capability'] });
  else {
    try { result = handlers[capabilityId](input, context); }
    catch { result = capabilityResult(capabilityId, input, { ok: false, status: 'runtime_internal_error', issues: ['runtime_internal_error'] }); }
  }
  return sealCapabilityResult(capabilityId, input, context, result);
}

export function evaluateCapability(capabilityId, result, input = {}, context = { connectorAvailable: false, externalWriteAuthorized: false }) {
  const issues = [];
  const normalizedContext = normalizeCapabilityContext(context);
  if (!isPlainObject(input)) issues.push('input_shape_invalid');
  if (!contextShapeValid(context)) issues.push('context_shape_invalid');
  if (result?.capabilityId !== capabilityId) issues.push('capability_id_mismatch');
  if (result?.receipt?.capabilityId !== capabilityId) issues.push('receipt_capability_id_mismatch');
  if (result?.receipt?.schemaVersion !== '1.1.0') issues.push('receipt_schema_version_mismatch');
  if (result?.receipt?.connectorRequired !== false) issues.push('connector_dependency_detected');
  if (result?.receipt?.donorSkillUsed !== false) issues.push('donor_skill_dependency_detected');
  if (result?.receipt?.externalActionCount !== 0) issues.push('unexpected_external_action');
  if (!resultShapeValid(result)) issues.push('result_schema_invalid');
  if (stableJson(result?.context) !== stableJson(normalizedContext)) issues.push('context_mismatch');
  if (result?.receipt?.inputDigest !== sha256(stableJson(input ?? {}))) issues.push('input_digest_mismatch');
  if (result?.receipt?.contextDigest !== sha256(stableJson(normalizedContext))) issues.push('context_digest_mismatch');
  const invocationPayload = { capabilityId, input: input ?? {}, context: normalizedContext };
  if (result?.receipt?.invocationDigest !== sha256(stableJson(invocationPayload))) issues.push('invocation_digest_mismatch');
  if (result?.receipt?.policyDigest !== capabilityRuntimePolicyDigest) issues.push('policy_digest_mismatch');
  const payload = { capabilityId: result?.capabilityId, status: result?.status, ok: result?.ok, output: result?.output, issues: result?.issues, warnings: result?.warnings, context: result?.context };
  if (result?.receipt?.resultDigest !== sha256(stableJson(payload))) issues.push('result_digest_mismatch');
  return { ok: issues.length === 0, issues };
}
