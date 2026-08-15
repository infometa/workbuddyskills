import { constants as fsConstants, readFileSync } from 'node:fs'
import { execFile } from 'node:child_process'
import { createHash, randomBytes, randomUUID } from 'node:crypto'
import { link, lstat, mkdir, open, readFile, readdir, rename, unlink, writeFile } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { promisify } from 'node:util'
import { fileURLToPath } from 'node:url'

import {
  BUNDLE_VERIFY_REQUEST_SCHEMA,
  isCognitiveAssetBundleRef,
  verifyCognitiveAssetBundle,
} from './cognitive-assets.mjs'
import { bindCollectionStatusesToCurrentRunEvents } from './collection-event-binding.mjs'
import {
  BoardContractError,
  CURRENT_WORKSPACE_RELEASE,
  PACKAGE_VERSION as EXPERT_PACKAGE_VERSION,
  assertWorkspacePathNoLinks,
  inspectWorkspace,
  inspectWorkspaceAccess,
  requireWritableWorkspace,
  verifyCurrentEventLedgerBytes,
} from './workspace-access.mjs'
import {
  LEGACY_RESUME_DIGEST_SCHEMA,
  PREDECESSOR_RESUME_DIGEST_SCHEMA,
  inspectLegacyResume,
  inspectPredecessorResume,
  readPredecessorResumeDigestReceipt,
  recordLegacyResumeDigestUnlocked,
  recordPredecessorResumeDigestUnlocked,
  resumeDigestFromReceipt,
} from './legacy-resume.mjs'

export const PACKAGE_ID = 'fbsir-eight-seat-board'
export const PACKAGE_VERSION = EXPERT_PACKAGE_VERSION
export const PRODUCT_VERSION = PACKAGE_VERSION
export const WORKSPACE_RELEASE = CURRENT_WORKSPACE_RELEASE
export const WORKSPACE_PRODUCT_VERSION = WORKSPACE_RELEASE.productVersion
export const WORKSPACE_SCHEMA = WORKSPACE_RELEASE.workspaceSchema
export const EVENT_SCHEMA = WORKSPACE_RELEASE.eventSchema
export { BoardContractError, inspectWorkspace, requireWritableWorkspace }
export const SEAT_PROPOSAL_SCHEMA = 'fbsir.review-seat-proposal/v1'
export const PLAN_SCHEMA = 'fbsir.review-plan/v2'
export const PREDECESSOR_RUN_REF_SCHEMA = 'fbsir.predecessor-run-ref/v2'
export const LEGACY_PREDECESSOR_RUN_REF_SCHEMA = 'fbsir.predecessor-run-ref/v1'
export const PLAN_CONFIRMATION_RECORD_SCHEMA = 'fbsir.review-plan-confirmation-record/v1'
export const PLAN_CONFIRMATION_RECORD_EVIDENCE_BOUNDARY = 'durable_package_local_action_ownership_only_not_user_host_or_cross_workspace_proof'
export const TASK_SCHEMA = 'fbsir.member-task/v1'
export const RESULT_SCHEMA = 'fbsir.member-result/v1'
export const PROCESS_SUPPORT_RESULT_SCHEMA = 'fbsir.process-support-result/v1'
export const PROCESS_SUPPORT_HANDOFF_SCHEMA = 'fbsir.process-support-handoff/v1'
export const PROCESS_SUPPORT_HANDOFF_EVIDENCE_BOUNDARY = 'validated_result_target_and_payload_hash_only_not_sendmessage_execution_host_receipt_or_lead_consumption_proof'
export const DELIVERY_OBSERVATION_SCHEMA = 'fbsir.member-delivery-observation/v1'
export const FAILURE_SCHEMA = 'fbsir.member-failure/v1'
export const COLLECTION_SCHEMA = 'fbsir.review-collection/v1'
export const DELIVERY_SCHEMA = 'fbsir.review-delivery/v1'
export const ENTRY_INTENT_SCHEMA = 'fbsir.entry-intent/v1'
export const HOST_ACTION_SCHEMA = 'fbsir.host-action-envelope/v1'
export const HOST_ACTION_EVIDENCE_BOUNDARY = 'package_proposed_action_only_not_host_execution_or_product_credit'
export const MATERIAL_SUFFICIENCY_SCHEMA = 'fbsir.material-sufficiency/v1'
export const MATERIAL_SUFFICIENCY_EVIDENCE_BOUNDARY = 'material_shape_and_internal_consistency_only_not_material_existence_authenticity_completeness_or_conclusion_truth'
export const MATERIAL_CARD_DRAFT_SCHEMA = 'fbsir.material-card-draft/v1'
export const MATERIAL_CARD_BUILD_EVIDENCE_BOUNDARY = 'package_local_csprng_reference_mint_and_material_shape_only_not_material_existence_authenticity_completeness_or_conclusion_truth'
export const DECISION_RECORD_SCHEMA = 'fbsir.decision-record/v1'
export const DECISION_RECORD_EVIDENCE_BOUNDARY = 'pending_decision_record_shape_and_digest_only_not_user_confirmation_identity_presentation_truth_persistence_host_execution_or_product_credit'
export const CASE_RESUME_CARD_SCHEMA = 'fbsir.case-resume-card/v1'
export const CASE_RESUME_CARD_EVIDENCE_BOUNDARY = 'read_only_expected_receipt_binding_and_content_free_operational_projection_only_not_body_truth_semantic_completion_host_execution_user_confirmation_or_product_credit'
export const HOST_RECEIPT_RECORD_SCHEMA = 'fbsir.host-receipt-record/v1'
export const HOST_RECEIPT_RECORD_EVIDENCE_BOUNDARY = 'workspace_bound_digest_only_host_receipt_observation_not_host_signature_receipt_authenticity_event_truth_or_product_credit'
export const CLAIM_EVIDENCE_SCHEMA = 'fbsir.claim-evidence/v1'
export const CLAIM_EVIDENCE_EVIDENCE_BOUNDARY = 'workspace_bound_declared_claim_marker_statement_digest_and_registered_source_binding_only_not_unmarked_claim_completeness_material_authenticity_or_claim_truth'
export const WORKSPACE_MATERIAL_RECORD_SCHEMA = 'fbsir.workspace-material-card/v1'
export const PUBLIC_SOURCE_RECORD_SCHEMA = 'fbsir.public-source-observation/v1'
export const PUBLIC_SOURCE_EVIDENCE_BOUNDARY = 'workspace_bound_digest_only_public_source_observation_not_source_authenticity_freshness_claim_truth_or_product_credit'

const RUN_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/
const ACTION_INSTANCE_ID_PATTERN = /^act_[a-z0-9][a-z0-9_-]{0,119}$/
const MATERIAL_REF_PATTERN = /^mat_[0-9a-f]{32}$/
const MATERIAL_GAP_ID_PATTERN = /^gap_[0-9a-f]{32}$/
const MATERIAL_VERSION_PATTERN = /^(?:user_declared_v[1-9][0-9]{0,5}|ref_[0-9a-f]{32})$/
const EVENT_ID_PATTERN = /^evt_[0-9a-f]{32}$/
const HOST_RECEIPT_REF_PATTERN = /^rcpt_[0-9a-f]{32}$/
const HEX_64 = /^[0-9a-f]{64}$/
const WRITER_ID = 'board-convener'
const execFileAsync = promisify(execFile)
let currentProcessIdentityPromise
const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..')
const runtimeManifest = JSON.parse(readFileSync(path.join(packageRoot, '.codebuddy-plugin', 'plugin.json'), 'utf8'))
const PROFESSIONAL_SEAT_IDS = new Set(runtimeManifest.members
  .filter((member) => member.role === 'member' && (!member.seatClass || member.seatClass === 'professional_review'))
  .map((member) => member.id))
const SUPPORT_SEAT_IDS = new Set(runtimeManifest.members
  .filter((member) => member.role === 'member' && member.seatClass === 'process_support')
  .map((member) => member.id))
const EVIDENCE_LEVELS = new Set(['package_local_observation', 'user_confirmation', 'host_runtime_receipt'])
const EVENT_CATALOG = Object.freeze({
  'meeting.opened': ['package_local_observation'],
  'agenda.registered': ['package_local_observation'],
  'plan.frozen': ['user_confirmation'],
  'team.create_requested': ['package_local_observation'],
  'team.created': ['host_runtime_receipt'],
  'team.create_failed': ['package_local_observation', 'host_runtime_receipt'],
  'seat.selected': ['package_local_observation'],
  'seat.dispatch_requested': ['package_local_observation'],
  'seat.dispatched': ['host_runtime_receipt'],
  'seat.dispatch_failed': ['package_local_observation', 'host_runtime_receipt'],
  'seat.result_received': ['host_runtime_receipt'],
  'seat.result_recovered': ['package_local_observation'],
  'seat.result_failed': ['package_local_observation'],
  'round.independent_sealed': ['package_local_observation'],
  'challenge.dispatched': ['host_runtime_receipt'],
  'challenge.result_received': ['host_runtime_receipt'],
  'collection.ready': ['package_local_observation'],
  'memo.compiled': ['package_local_observation'],
  'artifact.presented': ['package_local_observation', 'host_runtime_receipt'],
  'user.confirmed': ['user_confirmation'],
  'run.failed': ['package_local_observation', 'host_runtime_receipt'],
  'run.stopped': ['user_confirmation'],
  'checkpoint.created': ['package_local_observation'],
})
const METADATA_KEYS = new Set([
  'agendaItemId', 'artifactType', 'failureClass', 'receiptStatus', 'reviewMode', 'roundId',
  'seatId', 'state', 'valueStage', 'workspaceMode', 'attempt', 'revision', 'count', 'reasonCode',
])
const SENSITIVE_KEY = /(content|prompt|question|answer|raw|token|secret|password|email|phone|name|address|ip|document|attachment|material)/i
const EVENT_KEYS = new Set([
  'schema', 'eventId', 'eventType', 'sequence', 'occurredAt', 'recordedAt', 'runIdHash',
  'actorId', 'evidence', 'metadata', 'payloadHash', 'release', 'privacy', 'intentDigest',
  'previousEventHash', 'eventHash',
])
const TASK_KEYS = new Set([
  'schema', 'runId', 'agendaItemId', 'seatId', 'taskClass', 'reviewMode', 'revision',
  'decisionQuestion', 'factSlices', 'evidenceRefs', 'firstRoundIsolation', 'returnTo',
  'resultTarget', 'deliveryObservationTarget',
])
const PLAN_KEY_LIST = Object.freeze([
  'schema', 'runId', 'revision', 'reviewMode', 'agendaItems', 'specialistSeatIds',
  'supportSeatIds', 'decisionCardHash', 'userConfirmed', 'confirmationReceiptId',
  'confirmationAction', 'predecessorRunRef', 'singleNextAction',
])
const EVENT_INPUT_KEYS = new Set(['workspaceRoot', 'runId', 'actorId', 'eventType', 'evidence', 'metadata', 'payloadHash'])
const HOST_RECEIPT_INPUT_KEYS = new Set([
  'workspaceRoot', 'runId', 'actorId', 'eventType', 'metadata', 'payloadHash', 'hostReceiptDigest',
])
const HOST_RECEIPT_RECORD_KEYS = new Set([
  'schema', 'receiptRef', 'workspaceIdHash', 'runIdHash', 'eventType', 'metadata', 'payloadHash',
  'hostReceiptDigest', 'verificationState', 'recordedBy', 'recordedAt', 'release', 'evidenceBoundary',
])
const CLAIM_EVIDENCE_DRAFT_KEYS = new Set(['schema', 'claims', 'contentStoredInEventLedger'])
const CLAIM_DRAFT_KEYS = new Set(['ordinal', 'evidenceRefs'])
const CLAIM_CLASSIFICATIONS = new Set(['fact', 'estimate', 'assumption', 'judgement', 'unknown'])
const WORKSPACE_MATERIAL_INPUT_KEYS = new Set(['workspaceRoot', 'runId', 'actorId', 'draft'])
const WORKSPACE_MATERIAL_RECORD_KEYS = new Set([
  'schema', 'workspaceIdHash', 'runIdHash', 'draftDigest', 'materialCard', 'recordedBy',
  'recordedAt', 'release', 'evidenceBoundary',
])
const CLAIM_RECORD_INPUT_KEYS = new Set(['workspaceRoot', 'runId', 'actorId', 'artifactPath', 'draft'])
const CLAIM_VERIFY_INPUT_KEYS = new Set(['workspaceRoot', 'runId', 'artifactPath'])
const PUBLIC_SOURCE_INPUT_KEYS = new Set(['workspaceRoot', 'runId', 'actorId', 'sourceDigest'])
const PUBLIC_SOURCE_RECORD_KEYS = new Set([
  'schema', 'sourceRef', 'workspaceIdHash', 'runIdHash', 'sourceDigest', 'recordedBy',
  'recordedAt', 'release', 'evidenceBoundary',
])
const CLAIM_INDEX_KEYS = new Set([
  'schema', 'workspaceIdHash', 'runIdHash', 'artifactSha256', 'claims', 'summary',
  'contentStoredInEventLedger', 'release', 'evidenceBoundary',
])
const CLAIM_INDEX_CLAIM_KEYS = new Set([
  'ordinal', 'claimId', 'statementDigest', 'critical', 'requestedClassification', 'classification',
  'evidenceRefs', 'evidenceStatus', 'downgradeReason',
])
const PLAN_KEYS = new Set(PLAN_KEY_LIST)
const PLAN_CONFIRMATION_ACTION_KEY_LIST = Object.freeze(['actionId', 'actionInstanceId', 'actionEnvelopeDigest'])
const PLAN_CONFIRMATION_ACTION_KEYS = new Set(PLAN_CONFIRMATION_ACTION_KEY_LIST)
const LEGACY_PREDECESSOR_RUN_REF_KEY_LIST = Object.freeze([
  'schema', 'receiptRef', 'receiptPayloadHash', 'sourceRunIdHash', 'legacyResumeDigest',
])
const LEGACY_PREDECESSOR_RUN_REF_KEYS = new Set(LEGACY_PREDECESSOR_RUN_REF_KEY_LIST)
const PREDECESSOR_RUN_REF_KEY_LIST = Object.freeze([
  'schema', 'receiptRef', 'receiptPayloadHash', 'sourceRunIdHash',
  'resumeDigestSchema', 'resumeDigest',
])
const PREDECESSOR_RUN_REF_KEYS = new Set(PREDECESSOR_RUN_REF_KEY_LIST)
const PLAN_CONFIRMATION_RECORD_KEY_LIST = Object.freeze([
  'schema', 'actionId', 'actionInstanceId', 'actionEnvelopeDigest', 'runId', 'revision',
  'confirmationReceiptId', 'planPayloadHash', 'workspaceIdHash', 'evidenceBoundary',
])
const PLAN_CONFIRMATION_RECORD_KEYS = new Set(PLAN_CONFIRMATION_RECORD_KEY_LIST)
const SEAT_PROPOSAL_KEYS = new Set(['schema', 'reviewMode', 'specialistSeatIds', 'supportSeatIds'])
const ENTRY_INTENT_KEYS = new Set([
  'schema', 'route', 'confidenceBand', 'signals', 'firstValueType',
  'teamCreationAllowed', 'workspaceWriteAllowed', 'evidenceBoundary',
])
const ENTRY_INTENT_SIGNAL_KEYS = new Set([
  'hasDecisionQuestion', 'hasUserMaterial', 'hasResumeReference',
  'isCapabilityQuestion', 'isOutOfScope',
])
const ENTRY_INTENT_ROUTES = new Set([
  'capability_discovery', 'decision_intake', 'material_review_intake',
  'continue_or_resume', 'graceful_redirect',
])
const ENTRY_INTENT_CONFIDENCE_BANDS = new Set(['low', 'medium', 'high'])
const ENTRY_FIRST_VALUE_BY_ROUTE = Object.freeze({
  capability_discovery: 'capability_card',
  decision_intake: 'decision_start_card',
  material_review_intake: 'decision_start_card_with_material_sufficiency',
  continue_or_resume: 'case_resume_card',
  graceful_redirect: 'graceful_redirect_card',
})
const HOST_ACTION_KEYS = Object.freeze([
  'schema', 'actionId', 'actionInstanceId', 'product', 'arguments', 'sideEffectClass',
  'approvalState', 'idempotent', 'stopCondition', 'doneState', 'successorAction',
  'routeSignature', 'evidenceBoundary',
])
const HOST_ACTION_KEY_SET = new Set(HOST_ACTION_KEYS)
const HOST_ACTION_PRODUCT_KEYS = Object.freeze(['packageId', 'productVersion'])
const HOST_ACTION_PRODUCT_KEY_SET = new Set(HOST_ACTION_PRODUCT_KEYS)
const REVIEW_MODES = new Set(['quick_review', 'standard_review', 'deep_review'])
const RESUME_SOURCES = new Set(['current_checkpoint', 'predecessor_read_only', 'legacy_read_only'])
const MATERIAL_KEY_LIST = Object.freeze([
  'schema', 'state', 'received', 'missing', 'pendingVerification',
  'conclusionPolicy', 'nextAction', 'contentStoredInEventLedger',
])
const MATERIAL_KEYS = new Set(MATERIAL_KEY_LIST)
const MATERIAL_RECEIVED_KEY_LIST = Object.freeze(['materialRef', 'version', 'status'])
const MATERIAL_RECEIVED_KEYS = new Set(MATERIAL_RECEIVED_KEY_LIST)
const MATERIAL_GAP_KEY_LIST = Object.freeze(['gapId', 'impact', 'blockingFor'])
const MATERIAL_GAP_KEYS = new Set(MATERIAL_GAP_KEY_LIST)
const MATERIAL_CARD_DRAFT_KEY_LIST = Object.freeze(['schema', 'received', 'missing', 'contentStoredInEventLedger'])
const MATERIAL_CARD_DRAFT_KEYS = new Set(MATERIAL_CARD_DRAFT_KEY_LIST)
const MATERIAL_CARD_RECEIVED_SLOT_KEY_LIST = Object.freeze(['versionKind', 'versionOrdinal', 'status'])
const MATERIAL_CARD_RECEIVED_SLOT_KEYS = new Set(MATERIAL_CARD_RECEIVED_SLOT_KEY_LIST)
const MATERIAL_CARD_MISSING_SLOT_KEY_LIST = Object.freeze(['impact', 'blockingFor'])
const MATERIAL_CARD_MISSING_SLOT_KEYS = new Set(MATERIAL_CARD_MISSING_SLOT_KEY_LIST)
const MATERIAL_CARD_VERSION_KINDS = new Set(['user_declared', 'package_minted'])
const MATERIAL_CARD_INPUT_STATUSES = new Set(['received_unverified', 'received_conflicted'])
const MATERIAL_STATES = new Set([
  'sufficient_for_framing', 'sufficient_for_conditional_review', 'insufficient_for_conclusion',
])
const MATERIAL_RECEIVED_STATUSES = new Set([
  'received_unverified', 'received_verified', 'received_conflicted',
])
const MATERIAL_GAP_IMPACTS = new Set([
  'may_change_framing',
  'may_change_option',
  'may_change_option_or_reversibility',
  'may_change_risk_or_legality',
  'may_change_timing_or_accountability',
])
const MATERIAL_GAP_BLOCKERS = new Set([
  'conditional_conclusion', 'definitive_conclusion', 'irreversible_recommendation',
])
const MATERIAL_CONCLUSION_POLICIES = new Set(['framing_only', 'conditional_only', 'no_conclusion'])
const MATERIAL_NEXT_ACTIONS = new Set(['add_facts', 'confirm_review'])
const DECISION_RECORD_KEY_LIST = Object.freeze([
  'schema', 'decisionRecordId', 'workspaceScopeHash', 'runId', 'revision', 'decisionOwner',
  'status', 'sourceArtifact', 'decision', 'decisionDigest', 'confirmation', 'recordedBy',
  'recordedAt', 'release', 'privacy', 'evidenceBoundary',
])
const DECISION_RECORD_KEYS = new Set(DECISION_RECORD_KEY_LIST)
const DECISION_SOURCE_ARTIFACT_KEY_LIST = Object.freeze(['artifactType', 'artifactDigest', 'presentationEventHash'])
const DECISION_SOURCE_ARTIFACT_KEYS = new Set(DECISION_SOURCE_ARTIFACT_KEY_LIST)
const DECISION_BODY_KEY_LIST = Object.freeze([
  'decisionCode', 'statement', 'declinedOptions', 'leadingIndicators', 'triggers',
  'actionItems', 'reviewAt',
])
const DECISION_BODY_KEYS = new Set(DECISION_BODY_KEY_LIST)
const DECISION_INDICATOR_KEY_LIST = Object.freeze(['indicatorId', 'metric', 'target', 'reviewTriggerId'])
const DECISION_INDICATOR_KEYS = new Set(DECISION_INDICATOR_KEY_LIST)
const DECISION_TRIGGER_KEY_LIST = Object.freeze(['triggerId', 'condition', 'response'])
const DECISION_TRIGGER_KEYS = new Set(DECISION_TRIGGER_KEY_LIST)
const DECISION_ACTION_ITEM_KEY_LIST = Object.freeze(['actionItemId', 'ownerRef', 'dueAt', 'status'])
const DECISION_ACTION_ITEM_KEYS = new Set(DECISION_ACTION_ITEM_KEY_LIST)
const DECISION_RELEASE_KEY_LIST = Object.freeze(['packageId', 'productVersion'])
const DECISION_RELEASE_KEYS = new Set(DECISION_RELEASE_KEY_LIST)
const DECISION_PRIVACY_KEY_LIST = Object.freeze(['class', 'contentStored', 'telemetryExport', 'schemaVersion'])
const DECISION_PRIVACY_KEYS = new Set(DECISION_PRIVACY_KEY_LIST)
const DECISION_ARTIFACT_TYPES = new Set(['quick_review_card', 'review_memo', 'deep_review_preparation_card'])
const DECISION_CODES = new Set(['approved', 'approved_with_conditions', 'rejected', 'deferred', 'revision_requested', 'no_decision'])
const DECISION_ACTION_STATUSES = new Set(['open', 'in_progress', 'blocked', 'done', 'cancelled'])
const DECISION_RECORD_ID_PATTERN = /^decision_[0-9a-f]{32}$/
const DECISION_INDICATOR_ID_PATTERN = /^indicator_[a-z0-9][a-z0-9_.:-]{0,117}$/
const DECISION_TRIGGER_ID_PATTERN = /^trigger_[a-z0-9][a-z0-9_.:-]{0,119}$/
const DECISION_ACTION_ITEM_ID_PATTERN = /^action_[a-z0-9][a-z0-9_.:-]{0,120}$/
const DECISION_OWNER_REF_PATTERN = /^owner_[a-z0-9][a-z0-9_.:-]{0,121}$/
const CANONICAL_UTC_TIMESTAMP_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/
const CASE_RESUME_CARD_KEY_LIST = Object.freeze([
  'schema', 'presentationState', 'accessMode', 'evidenceState', 'source',
  'observedMilestoneIds', 'evidenceBindingIds', 'openGateIds', 'materialGate',
  'nextAction', 'responsibility', 'recoveryBoundary', 'contentIncluded', 'writesPerformed',
  'evidenceBoundary',
])
const CASE_RESUME_CARD_KEYS = new Set(CASE_RESUME_CARD_KEY_LIST)
const CASE_RESUME_SOURCE_KEYS = new Set(['receiptType', 'runIdHash', 'receiptDigest'])
const CASE_RESUME_MATERIAL_GATE_KEYS = new Set(['state', 'missingCount', 'pendingVerificationCount'])
const CASE_RESUME_NEXT_ACTION_KEYS = new Set(['actionId', 'approvalState', 'resumeSource', 'targetRunRequired'])
const CASE_RESUME_RESPONSIBILITY_KEYS = new Set(['ownerStatus', 'dueAt', 'reviewAt'])
const CASE_RESUME_PRESENTATION_STATES = new Set([
  'current_resume_card', 'predecessor_read_only_resume_card',
  'legacy_read_only_resume_card', 'resume_evidence_insufficient_card',
])
const CASE_RESUME_EVIDENCE_STATES = new Set([
  'verified_current_checkpoint', 'verified_predecessor_resume_digest',
  'verified_legacy_resume_digest', 'missing', 'unsupported', 'receipt_mismatch', 'source_changed',
])
const CASE_RESUME_MILESTONE_ORDER = Object.freeze([
  'meeting_opened_event_observed', 'agenda_registered_event_observed', 'plan_frozen_event_observed',
  'team_creation_terminal_event_observed', 'seat_selection_event_observed',
  'seat_dispatch_terminal_event_observed', 'seat_result_terminal_event_observed',
  'round_sealed_event_observed', 'collection_ready_event_observed',
  'memo_compiled_event_observed', 'artifact_presented_event_observed',
  'user_confirmation_event_observed', 'run_terminal_event_observed', 'checkpoint_event_observed',
])
const CASE_RESUME_EVIDENCE_BINDING_ORDER = Object.freeze([
  'current_checkpoint_bound',
  'predecessor_workspace_bound', 'predecessor_plan_bound', 'predecessor_event_chain_bound',
  'predecessor_checkpoint_bound', 'predecessor_collection_bound', 'predecessor_delivery_bound',
  'predecessor_deliverable_inventory_bound',
  'legacy_workspace_bound', 'legacy_plan_bound', 'legacy_event_chain_bound',
  'legacy_checkpoint_bound', 'legacy_collection_bound', 'legacy_delivery_bound',
  'legacy_deliverable_inventory_bound',
])
const CASE_RESUME_MILESTONE_IDS = new Set(CASE_RESUME_MILESTONE_ORDER)
const CASE_RESUME_EVIDENCE_BINDING_IDS = new Set(CASE_RESUME_EVIDENCE_BINDING_ORDER)
const CASE_RESUME_OPEN_GATE_ORDER = Object.freeze([
  'source_receipt_required', 'source_unsupported_or_changed',
  'resume_action_not_presented', 'explicit_resume_confirmation_required', 'new_run_binding_required',
  'run_terminal_no_same_run_resume', 'material_status_not_bound', 'human_review_required',
  'predecessor_content_truth_unverified', 'legacy_content_truth_unverified',
])
const CASE_RESUME_OPEN_GATE_IDS = new Set(CASE_RESUME_OPEN_GATE_ORDER)
const CASE_RESUME_MATERIAL_STATES = new Set([
  'not_bound_by_checkpoint', 'not_available_from_predecessor_digest',
  'not_available_from_legacy_digest', 'no_verified_evidence',
])
const CHECKPOINT_KEYS = new Set([
  'schema', 'runIdHash', 'state', 'eventCount', 'chainHead', 'createdAt', 'release',
])
const CHECKPOINT_INPUT_KEY_LIST = Object.freeze(['workspaceRoot', 'runId', 'actorId', 'state'])
const CHECKPOINT_INPUT_KEYS = new Set(CHECKPOINT_INPUT_KEY_LIST)
const MAX_CHECKPOINT_BYTES = 16 * 1024
const METADATA_ENUM_VALUES = Object.freeze({
  artifactType: new Set([
    'decision_start_card', 'material_sufficiency_card', 'quick_review_card', 'review_memo',
    'deep_review_preparation_card', 'action_review_card', 'case_resume_card',
  ]),
  failureClass: new Set([
    'team_create_failed', 'seat_dispatch_failed', 'seat_result_failed', 'run_failed',
    'validation_failed', 'precondition_failed',
  ]),
  receiptStatus: new Set(['not_required', 'requested', 'received', 'verified', 'rejected', 'unavailable']),
  reviewMode: REVIEW_MODES,
  state: new Set([
    'initialized', 'opened', 'registered', 'frozen', 'requested', 'created', 'selected',
    'dispatched', 'received', 'sealed', 'ready', 'compiled', 'presented', 'confirmed',
    'failed', 'stopped', 'checkpointed', 'ready_to_present',
  ]),
  valueStage: new Set([
    'capability_card', 'decision_start_card', 'material_sufficiency', 'conditional_review',
    'decision_artifact', 'action_follow_up',
  ]),
  workspaceMode: new Set(['fresh', 'resumed', 'legacy_read_only']),
  reasonCode: new Set([
    'member_no_response', 'send_message_failed', 'result_invalid',
    'member_terminal_without_result', 'retry_exhausted', 'user_requested_stop',
    'precondition_failed', 'validation_failed',
  ]),
})
const METADATA_NUMBER_KEYS = new Set(['attempt', 'revision', 'count'])

export const HOST_ACTION_CATALOG = Object.freeze({
  confirm_review: Object.freeze({
    argumentKeys: Object.freeze(['reviewMode', 'decisionCardHash']),
    sideEffectClass: 'state_write',
    approvalState: 'required',
    stopCondition: 'plan_v2_frozen_with_exact_action_digest',
    doneState: 'review_plan_confirmed',
    successorAction: 'request_team_create',
    routeSignature: 'fbsir-eight-seat-board:confirm_review:v1',
  }),
  add_facts: Object.freeze({
    argumentKeys: Object.freeze(['decisionCardHash', 'factUpdateDigest']),
    sideEffectClass: 'conversation_update',
    approvalState: 'user_submission',
    stopCondition: 'decision_card_recomputed_with_exact_fact_update_digest',
    doneState: 'facts_applied_to_decision_card',
    successorAction: 'present_updated_decision_card',
    routeSignature: 'fbsir-eight-seat-board:add_facts:v1',
  }),
  change_mode: Object.freeze({
    argumentKeys: Object.freeze(['decisionCardHash', 'fromReviewMode', 'toReviewMode']),
    sideEffectClass: 'plan_update',
    approvalState: 'required',
    stopCondition: 'seat_proposal_recomputed_for_exact_mode_change',
    doneState: 'review_mode_changed',
    successorAction: 'present_updated_decision_card',
    routeSignature: 'fbsir-eight-seat-board:change_mode:v1',
  }),
  resume_case: Object.freeze({
    argumentKeys: Object.freeze(['resumeSource', 'sourceRunIdHash', 'resumeReceiptDigest', 'targetRunId']),
    sideEffectClass: 'state_write',
    approvalState: 'required',
    stopCondition: 'current_run_receipt_revalidated_or_read_only_successor_plan_bound',
    doneState: 'case_resume_authorized',
    successorAction: 'resume_current_node_or_initialize_read_only_successor',
    routeSignature: 'fbsir-eight-seat-board:resume_case:v1',
  }),
  confirm_decision_record: Object.freeze({
    argumentKeys: Object.freeze(['runId', 'decisionDigest']),
    sideEffectClass: 'state_write',
    approvalState: 'required',
    stopCondition: 'decision_record_written_with_exact_decision_digest',
    doneState: 'decision_record_confirmed',
    successorAction: 'present_action_review_card',
    routeSignature: 'fbsir-eight-seat-board:confirm_decision_record:v1',
  }),
})
const AGENDA_ITEM_KEYS = new Set(['agendaItemId', 'decisionQuestion'])
const RESULT_KEYS = new Set([
  'schema', 'runId', 'agendaItemId', 'seatId', 'taskClass', 'revision', 'stance',
  'confidence', 'conclusionReady', 'receiptId', 'evidenceRefs', 'sections',
])
const PROCESS_SUPPORT_HANDOFF_KEYS = new Set([
  'schema', 'runId', 'agendaItemId', 'seatId', 'revision', 'resultTarget', 'resultPayloadHash',
])
const DELIVERY_OBSERVATION_KEYS = new Set([
  'schema', 'runId', 'agendaItemId', 'seatId', 'revision', 'resultPayloadHash',
  'channel', 'recipient', 'status', 'attempt', 'observedAt', 'hostReceiptId',
])
const FAILURE_KEYS = new Set([
  'schema', 'runId', 'agendaItemId', 'seatId', 'revision', 'status', 'attempts', 'reasonCode',
  'recordedBy', 'recordedAt', 'detailHash',
])
const HASH_BOUND_EVENT_TYPES = new Set([
  'plan.frozen',
  'seat.dispatch_requested', 'seat.dispatched', 'seat.dispatch_failed',
  'seat.result_received', 'seat.result_recovered', 'seat.result_failed',
  'collection.ready', 'memo.compiled', 'artifact.presented', 'user.confirmed',
])
const PROFESSIONAL_RESULT_SECTIONS = new Set(['judgement', 'conditions', 'failureConditions', 'humanGate', 'evidenceAssessment', 'dissent'])
const SUPPORT_RESULT_SECTIONS = new Set(['deliveryStatus', 'sourceLedger', 'artifactChecklist', 'capabilityStatus'])
const SUPPORT_DELIVERY_STATUS_KEYS = new Set(['state', 'receiptObserved'])
const SUPPORT_SOURCE_LEDGER_KEYS = new Set(['entries', 'pendingVerification', 'mutationAllowed'])
const SUPPORT_ARTIFACT_CHECKLIST_KEYS = new Set(['requiredCount', 'readyCount', 'pendingCount', 'humanAcceptanceRequired'])
const SUPPORT_CAPABILITY_STATUS_KEYS = new Set(['state', 'materialStateEffect', 'externalFactProven', 'manualVerificationRequired'])
const SUPPORT_DELIVERY_STATES = new Set(['completed', 'partial', 'blocked'])
const SUPPORT_CAPABILITY_STATES = new Set(['available', 'unavailable', 'not_authorized', 'accepted_without_result'])

function invariant(condition, code, message = code, details = {}) {
  if (!condition) throw new BoardContractError(code, message, details)
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function assertTransportData(value, code, seen = new Set()) {
  if (value === null || ['string', 'boolean'].includes(typeof value)) return
  if (typeof value === 'number') {
    invariant(Number.isFinite(value), code)
    return
  }
  invariant(typeof value === 'object' && !seen.has(value), code, 'Input must be an acyclic plain-data value')
  seen.add(value)
  const prototype = Object.getPrototypeOf(value)
  invariant(
    Array.isArray(value) ? prototype === Array.prototype : prototype === Object.prototype || prototype === null,
    code,
    'Input must use only plain objects and arrays',
  )
  for (const key of Reflect.ownKeys(value)) {
    invariant(typeof key === 'string', code, 'Symbol keys are forbidden')
    const descriptor = Object.getOwnPropertyDescriptor(value, key)
    invariant(descriptor && Object.hasOwn(descriptor, 'value'), code, 'Accessors are forbidden')
    if (key !== 'length') invariant(descriptor.enumerable === true, code, 'Hidden data fields are forbidden')
    if (key !== 'length') assertTransportData(descriptor.value, code, seen)
  }
  seen.delete(value)
}

function snapshotTransportData(value, code) {
  try {
    assertTransportData(value, code)
    return structuredClone(value)
  } catch (error) {
    if (error instanceof BoardContractError) throw error
    throw new BoardContractError(code, 'Input must be cloneable plain data')
  }
}

function requiredAssetBundleRef(evidenceRefs, code) {
  const bundleRefs = evidenceRefs.filter((value) => isCognitiveAssetBundleRef(value))
  invariant(bundleRefs.length === 1, code, 'Exactly one cognitive asset bundle reference is required', { count: bundleRefs.length })
  return bundleRefs[0]
}

function canonical(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value)
  if (typeof value === 'number') {
    invariant(Number.isFinite(value), 'NON_FINITE_NUMBER')
    return JSON.stringify(value)
  }
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`
  invariant(isObject(value), 'CANONICAL_VALUE_INVALID')
  const entries = Object.keys(value).sort().map((key) => {
    invariant(value[key] !== undefined, 'UNDEFINED_VALUE_FORBIDDEN', 'Undefined values are not canonical', { key })
    return `${JSON.stringify(key)}:${canonical(value[key])}`
  })
  return `{${entries.join(',')}}`
}

function assertExactKeys(value, allowedKeys, code) {
  invariant(isObject(value), code)
  const unexpected = Object.keys(value).filter((key) => !allowedKeys.has(key))
  invariant(unexpected.length === 0, code, 'Envelope or receipt contains undeclared fields', { unexpectedCount: unexpected.length })
}

function assertRequiredKeys(value, requiredKeys, code) {
  invariant(isObject(value), code)
  const missing = requiredKeys.filter((key) => !Object.hasOwn(value, key))
  invariant(missing.length === 0, code, 'Envelope or receipt is missing required fields', { missing })
}

export function sha256(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === 'string' ? value : canonical(value), 'utf8')
  return createHash('sha256').update(bytes).digest('hex')
}

function safeId(value, code) {
  invariant(typeof value === 'string' && ID_PATTERN.test(value), code)
  return value
}

function ensureWithin(root, target) {
  const relative = path.relative(root, target)
  invariant(relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative)), 'PATH_OUTSIDE_WORKSPACE', 'Resolved path is outside the workspace', { root, target })
}

async function rejectExistingLinkSegments(root, target, code = 'WORKSPACE_LINK_PATH_FORBIDDEN') {
  const resolvedRoot = path.resolve(root)
  const resolvedTarget = path.resolve(target)
  ensureWithin(resolvedRoot, resolvedTarget)
  const relative = path.relative(resolvedRoot, resolvedTarget)
  let cursor = resolvedRoot
  for (const segment of relative.split(path.sep).filter(Boolean)) {
    cursor = path.join(cursor, segment)
    try {
      const info = await lstat(cursor)
      invariant(!info.isSymbolicLink(), code, 'Workspace paths must not contain symbolic links or junctions', { path: cursor })
    } catch (error) {
      if (error?.code === 'ENOENT') return
      throw error
    }
  }
}

async function requireDirectoryNoLink(target, code) {
  let info
  try { info = await lstat(target) }
  catch (error) { throw new BoardContractError(code, 'Required workspace directory is unavailable', { target, cause: error.code }) }
  invariant(info.isDirectory() && !info.isSymbolicLink(), code, 'Workspace directory must be a real non-link directory', { target })
}

async function requireRegularFileNoLink(target, code) {
  let info
  try { info = await lstat(target) }
  catch (error) { throw new BoardContractError(code, 'Required workspace file is unavailable', { target, cause: error.code }) }
  invariant(info.isFile() && !info.isSymbolicLink() && info.nlink === 1, code, 'Workspace file must be an isolated regular non-link file', { target })
}

function workspacePaths(workspaceRoot, runId = null) {
  const root = path.resolve(workspaceRoot)
  const control = path.join(root, '.fbsir-board')
  const marker = path.join(control, 'workspace.json')
  const events = path.join(control, 'events')
  const checkpoints = path.join(control, 'checkpoints')
  const locks = path.join(control, 'locks')
  const collections = path.join(control, 'collections')
  const deliveries = path.join(control, 'deliveries')
  const plans = path.join(control, 'plans')
  const hostReceipts = path.join(control, 'host-receipts')
  const evidenceSources = path.join(control, 'evidence-sources')
  const materialCards = path.join(control, 'material-cards')
  const claimIndexes = path.join(control, 'claim-indexes')
  const predecessors = path.join(control, 'predecessors')
  const tasks = path.join(root, 'tasks')
  const drafts = path.join(root, 'drafts')
  const results = path.join(root, 'results')
  const receipts = path.join(root, 'receipts')
  const failures = path.join(root, 'failures')
  const deliverables = path.join(root, 'deliverables')
  const result = {
    root, control, marker, events, checkpoints, locks, collections, deliveries, plans,
    hostReceipts, evidenceSources, materialCards, claimIndexes, predecessors,
    tasks, drafts, results, receipts, failures, deliverables,
  }
  if (runId !== null) {
    invariant(RUN_ID_PATTERN.test(runId), 'RUN_ID_INVALID')
    result.eventFile = path.join(events, `${runId}.jsonl`)
    result.lockFile = path.join(locks, `${runId}.lock`)
    result.checkpointFile = path.join(checkpoints, `${runId}.json`)
    result.collectionFile = path.join(collections, `${runId}.json`)
    result.deliveryFile = path.join(deliveries, `${runId}.json`)
    result.planFile = path.join(plans, `${runId}.json`)
    result.materialCardFile = path.join(materialCards, `${runId}.json`)
  }
  for (const target of Object.values(result)) ensureWithin(root, target)
  return result
}

async function pathExists(target) {
  try { await lstat(target); return true } catch (error) { if (error?.code === 'ENOENT') return false; throw error }
}

export async function initializeWorkspace(workspaceRoot, { workspaceId = `ws_${randomUUID()}` } = {}) {
  invariant(typeof workspaceRoot === 'string' && workspaceRoot.trim(), 'WORKSPACE_PATH_REQUIRED')
  const paths = workspacePaths(workspaceRoot)
  const parsed = path.parse(paths.root)
  invariant(paths.root !== parsed.root, 'WORKSPACE_DRIVE_ROOT_FORBIDDEN')
  invariant(paths.root.toLowerCase() !== path.resolve(os.homedir()).toLowerCase(), 'WORKSPACE_HOME_FORBIDDEN')
  safeId(workspaceId, 'WORKSPACE_ID_INVALID')
  await assertWorkspacePathNoLinks(paths.root, 'WORKSPACE_ROOT_LINK_FORBIDDEN')

  if (await pathExists(paths.marker)) return requireWritableWorkspace(workspaceRoot)
  if (await pathExists(paths.root)) {
    await requireDirectoryNoLink(paths.root, 'WORKSPACE_ROOT_LINK_FORBIDDEN')
    const entries = await readdir(paths.root)
    invariant(entries.length === 0, 'WORKSPACE_NOT_DEDICATED', 'Choose an empty directory or an existing FBSir board workspace', { entries: entries.slice(0, 10) })
  }
  await mkdir(paths.events, { recursive: true })
  await mkdir(paths.checkpoints, { recursive: true })
  await mkdir(paths.locks, { recursive: true })
  await mkdir(paths.collections, { recursive: true })
  await mkdir(paths.deliveries, { recursive: true })
  await mkdir(paths.plans, { recursive: true })
  await mkdir(paths.hostReceipts, { recursive: true })
  await mkdir(paths.evidenceSources, { recursive: true })
  await mkdir(paths.materialCards, { recursive: true })
  await mkdir(paths.claimIndexes, { recursive: true })
  await mkdir(paths.predecessors, { recursive: true })
  await mkdir(paths.tasks, { recursive: true })
  await mkdir(paths.drafts, { recursive: true })
  await mkdir(paths.results, { recursive: true })
  await mkdir(paths.receipts, { recursive: true })
  await mkdir(paths.failures, { recursive: true })
  await mkdir(paths.deliverables, { recursive: true })
  const marker = {
    schema: WORKSPACE_SCHEMA,
    workspaceId,
    workspaceInstanceId: `wsi_${randomBytes(16).toString('hex')}`,
    product: PACKAGE_ID,
    productVersion: WORKSPACE_PRODUCT_VERSION,
    privacyMode: 'local_default',
    contentExport: 'deny_by_default',
    telemetryExport: 'deny_by_default',
    sharedStateWriter: WRITER_ID,
    createdAt: new Date().toISOString(),
  }
  await writeAtomic(paths.marker, `${JSON.stringify(marker, null, 2)}\n`)
  await requireWritableWorkspace(workspaceRoot)
  return marker
}

export async function readWorkspace(workspaceRoot) {
  return requireWritableWorkspace(workspaceRoot)
}

function workspaceScopeHash(marker) {
  invariant(typeof marker?.workspaceId === 'string' && /^wsi_[0-9a-f]{32}$/.test(marker?.workspaceInstanceId || ''), 'WORKSPACE_INSTANCE_ID_REQUIRED')
  return sha256({ workspaceId: marker.workspaceId, workspaceInstanceId: marker.workspaceInstanceId })
}

async function writeAtomic(target, content) {
  const temp = `${target}.${process.pid}.${randomBytes(6).toString('hex')}.tmp`
  let handle
  try {
    handle = await open(temp, fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY, 0o600)
    await handle.writeFile(content, 'utf8')
    await handle.sync()
    await handle.close()
    handle = null
    await rename(temp, target)
  } finally {
    await handle?.close()
    try { await unlink(temp) } catch (error) { if (error?.code !== 'ENOENT') throw error }
  }
}

async function publishExclusiveJson(target, value) {
  const temp = `${target}.${process.pid}.${randomBytes(6).toString('hex')}.tmp`
  let handle
  try {
    handle = await open(temp, fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY, 0o600)
    await handle.writeFile(`${JSON.stringify(value, null, 2)}\n`, 'utf8')
    await handle.sync()
    await handle.close()
    handle = null
    try {
      await link(temp, target)
      return true
    } catch (error) {
      if (error?.code !== 'EEXIST') throw error
      return false
    }
  } finally {
    await handle?.close()
    try { await unlink(temp) } catch (error) { if (error?.code !== 'ENOENT') throw error }
  }
}

function parseLockOwner(raw) {
  const trimmed = raw.trim()
  if (/^[1-9][0-9]*$/.test(trimmed)) return { pid: Number(trimmed), token: null, processIdentity: null }
  try {
    const owner = JSON.parse(trimmed)
    if (!Number.isInteger(owner.pid) || owner.pid <= 0 || typeof owner.token !== 'string' || !owner.token) return null
    const identity = owner.processIdentity
    const processIdentity = identity
      && typeof identity.value === 'string'
      && ((identity.kind === 'linux_boot_and_start_ticks' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[1-9][0-9]*$/.test(identity.value))
        || (identity.kind === 'windows_start_filetime' && /^[1-9][0-9]*$/.test(identity.value)))
      ? { kind: identity.kind, value: identity.value }
      : null
    return { pid: owner.pid, token: owner.token, processIdentity }
  } catch {
    return null
  }
}

function processIsAlive(pid) {
  try { process.kill(pid, 0); return true }
  catch (error) { return error?.code !== 'ESRCH' }
}

async function lockSnapshot(lockFile, transientAttempt = 0) {
  try {
    const raw = await readFile(lockFile, 'utf8')
    return { raw, owner: parseLockOwner(raw) }
  } catch (error) {
    if (error?.code === 'ENOENT') return null
    if (process.platform === 'win32' && error?.code === 'EPERM' && transientAttempt < 6) {
      // Windows can surface EPERM, rather than ENOENT, when open races an unlink
      // from the previous lock owner. Retry only this bounded transient window;
      // a stable permission failure still fails closed.
      await new Promise((resolve) => setTimeout(resolve, 2 ** transientAttempt))
      return lockSnapshot(lockFile, transientAttempt + 1)
    }
    throw error
  }
}

function parseLinuxProcessStartTicks(raw) {
  const closeParen = raw.lastIndexOf(')')
  if (closeParen < 0) return null
  const fieldsAfterCommand = raw.slice(closeParen + 1).trim().split(/\s+/)
  const startTicks = fieldsAfterCommand[19]
  return /^[1-9][0-9]*$/.test(startTicks || '') ? startTicks : null
}

async function linuxProcessIdentity(pid) {
  try {
    const bootId = (await readFile('/proc/sys/kernel/random/boot_id', 'utf8')).trim().toLowerCase()
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(bootId)) return null
    const startTicks = parseLinuxProcessStartTicks(await readFile(`/proc/${pid}/stat`, 'utf8'))
    return startTicks ? { kind: 'linux_boot_and_start_ticks', value: `${bootId}:${startTicks}` } : null
  } catch {
    return null
  }
}

async function windowsProcessIdentity(pid) {
  try {
    const script = `$p=Get-Process -Id ${pid} -ErrorAction Stop; [string]$p.StartTime.ToFileTimeUtc()`
    const { stdout } = await execFileAsync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], {
      encoding: 'utf8',
      timeout: 4000,
      windowsHide: true,
    })
    const filetime = stdout.trim()
    return /^[1-9][0-9]*$/.test(filetime) ? { kind: 'windows_start_filetime', value: filetime } : null
  } catch {
    return null
  }
}

async function platformProcessIdentity(pid) {
  if (process.platform === 'linux') return linuxProcessIdentity(pid)
  if (process.platform === 'win32') return windowsProcessIdentity(pid)
  return null
}

function currentProcessIdentity() {
  if (!currentProcessIdentityPromise) {
    currentProcessIdentityPromise = platformProcessIdentity(process.pid).then((identity) => {
      if (!identity) currentProcessIdentityPromise = null
      return identity
    })
  }
  return currentProcessIdentityPromise
}

async function liveProcessIdentity(pid, expectedKind) {
  const identity = pid === process.pid ? await currentProcessIdentity() : await platformProcessIdentity(pid)
  return identity?.kind === expectedKind ? identity : null
}

async function lockIsStale(snapshot) {
  if (!snapshot?.owner) return false
  if (!processIsAlive(snapshot.owner.pid)) return true
  if (!snapshot.owner.processIdentity) return false
  const liveIdentity = await liveProcessIdentity(snapshot.owner.pid, snapshot.owner.processIdentity.kind)
  if (!liveIdentity || liveIdentity.kind !== snapshot.owner.processIdentity.kind) return false
  return liveIdentity.value !== snapshot.owner.processIdentity.value
}

async function releaseOwnedLock(lockFile, token) {
  const current = await lockSnapshot(lockFile)
  if (current?.owner?.token !== token) return
  try { await unlink(lockFile) } catch (error) { if (error?.code !== 'ENOENT') throw error }
}

async function tryReapStaleLock(lockFile) {
  const stale = await lockSnapshot(lockFile)
  if (!stale?.owner || !(await lockIsStale(stale))) return false
  const staleGeneration = sha256(stale.raw).slice(0, 32)
  const reaperFile = `${lockFile}.reap.${staleGeneration}`
  const reaperToken = randomBytes(16).toString('hex')
  const processIdentity = await currentProcessIdentity()
  if (!(await publishExclusiveJson(reaperFile, { pid: process.pid, token: reaperToken, processIdentity, createdAt: new Date().toISOString() }))) {
    // Never auto-delete a generation reaper. Multiple cleaners cannot safely compare-and-unlink
    // one path without a storage-level CAS; an abandoned reaper therefore fails this generation closed.
    return false
  }
  try {
    const current = await lockSnapshot(lockFile)
    if (!current || current.raw !== stale.raw || !current.owner || !(await lockIsStale(current))) return false
    try { await unlink(lockFile) } catch (error) { if (error?.code !== 'ENOENT') throw error }
    return true
  } finally {
    await releaseOwnedLock(reaperFile, reaperToken)
  }
}

async function acquireLock(lockFile, timeoutMs = 2500) {
  const started = Date.now()
  const processIdentity = await currentProcessIdentity()
  let inspectedOwnerRaw = null
  while (true) {
    const token = randomBytes(16).toString('hex')
    if (!(await pathExists(lockFile))
      && await publishExclusiveJson(lockFile, { pid: process.pid, token, processIdentity, createdAt: new Date().toISOString() })) {
      return { token }
    }
    const current = await lockSnapshot(lockFile)
    if (current?.raw !== inspectedOwnerRaw) {
      inspectedOwnerRaw = current?.raw || null
      if (await tryReapStaleLock(lockFile)) {
        inspectedOwnerRaw = null
        continue
      }
    }
    if (Date.now() - started >= timeoutMs) throw new BoardContractError('LEDGER_LOCK_TIMEOUT', 'Timed out waiting for the event ledger lock')
    await new Promise((resolve) => setTimeout(resolve, 10))
  }
}

async function releaseLock(lock, lockFile) {
  if (!lock?.token) return
  await releaseOwnedLock(lockFile, lock.token)
}

function normalizeEventEvidenceInput(eventType, evidence) {
  invariant(isObject(evidence), 'EVIDENCE_REQUIRED')
  assertExactKeys(evidence, new Set(['level', 'receiptRef']), 'EVIDENCE_FIELD_FORBIDDEN')
  invariant(EVIDENCE_LEVELS.has(evidence.level), 'EVIDENCE_LEVEL_INVALID')
  invariant(EVENT_CATALOG[eventType]?.includes(evidence.level), 'EVIDENCE_LEVEL_UNSUPPORTED_FOR_EVENT')
  if (evidence.level === 'package_local_observation') {
    invariant(evidence.receiptRef === null, 'PACKAGE_LOCAL_RECEIPT_FORBIDDEN')
  } else if (evidence.level === 'host_runtime_receipt') {
    invariant(typeof evidence.receiptRef === 'string' && HOST_RECEIPT_REF_PATTERN.test(evidence.receiptRef), 'HOST_RECEIPT_REQUIRED')
  } else {
    invariant(typeof evidence.receiptRef === 'string' && evidence.receiptRef.length >= 1 && evidence.receiptRef.length <= 256, 'USER_CONFIRMATION_RECEIPT_REQUIRED')
  }
  return { level: evidence.level, receiptRef: evidence.receiptRef }
}

function validateStoredEvidence(eventType, evidence) {
  invariant(isObject(evidence), 'EVIDENCE_REQUIRED')
  assertExactKeys(evidence, new Set(['level', 'receiptRef']), 'EVIDENCE_FIELD_FORBIDDEN')
  invariant(EVIDENCE_LEVELS.has(evidence.level), 'EVIDENCE_LEVEL_INVALID')
  invariant(EVENT_CATALOG[eventType]?.includes(evidence.level), 'EVIDENCE_LEVEL_UNSUPPORTED_FOR_EVENT')
  if (evidence.level === 'package_local_observation') invariant(evidence.receiptRef === null, 'PACKAGE_LOCAL_RECEIPT_FORBIDDEN')
  else invariant(typeof evidence.receiptRef === 'string' && HOST_RECEIPT_REF_PATTERN.test(evidence.receiptRef), 'RECEIPT_REF_INVALID')
  return evidence
}

function normalizeMetadata(metadata = {}) {
  invariant(isObject(metadata), 'METADATA_OBJECT_REQUIRED')
  const normalized = {}
  for (const [key, value] of Object.entries(metadata)) {
    invariant(METADATA_KEYS.has(key), 'METADATA_KEY_FORBIDDEN', 'Only declared operational metadata is allowed in the event ledger', { unexpectedCount: 1 })
    invariant(!SENSITIVE_KEY.test(key), 'SENSITIVE_METADATA_KEY_FORBIDDEN', 'Content and personal data must not be written to the event ledger', { key })
    if (METADATA_NUMBER_KEYS.has(key)) {
      const minimum = key === 'count' ? 0 : 1
      invariant(Number.isInteger(value) && value >= minimum && value <= 10000, 'METADATA_NUMBER_VALUE_INVALID', 'Operational counters must be bounded integers', { key })
      normalized[key] = value
      continue
    }
    invariant(typeof value === 'string', 'METADATA_STRING_VALUE_INVALID', 'Operational metadata strings must use the declared enum or opaque reference shape', { key })
    if (key === 'agendaItemId') {
      invariant(/^agenda_[1-9][0-9]{0,5}$/.test(value), 'METADATA_STRING_VALUE_INVALID', 'Agenda metadata must use a bounded ordinal', { key })
      normalized[key] = value
      continue
    }
    if (key === 'roundId') {
      invariant(/^round_[1-9][0-9]{0,5}$/.test(value), 'METADATA_STRING_VALUE_INVALID', 'Round metadata must use a bounded ordinal', { key })
      normalized[key] = value
      continue
    }
    if (key === 'seatId') {
      invariant(PROFESSIONAL_SEAT_IDS.has(value) || SUPPORT_SEAT_IDS.has(value), 'METADATA_STRING_VALUE_INVALID', 'Seat metadata must name a packaged manifest member', { key })
      normalized[key] = value
      continue
    }
    invariant(METADATA_ENUM_VALUES[key]?.has(value), 'METADATA_STRING_VALUE_INVALID', 'Operational metadata strings must use a closed enum', { key })
    normalized[key] = value
  }
  return normalized
}

function payloadHashRequiredCode(eventType) {
  if (eventType === 'plan.frozen') return 'PLAN_PAYLOAD_HASH_REQUIRED'
  if (eventType.startsWith('seat.dispatch')) return 'TASK_PAYLOAD_HASH_REQUIRED'
  if (eventType === 'artifact.presented') return 'ARTIFACT_PAYLOAD_HASH_REQUIRED'
  if (eventType === 'user.confirmed') return 'DECISION_RECORD_PAYLOAD_HASH_REQUIRED'
  return 'EVENT_PAYLOAD_HASH_REQUIRED'
}

function parseJsonLines(raw, filePath) {
  return raw.split(/\r?\n/).filter(Boolean).map((line, index) => {
    try { return JSON.parse(line) }
    catch (error) { throw new BoardContractError('LEDGER_JSON_INVALID', 'Event ledger contains invalid JSON', { filePath, line: index + 1 }) }
  })
}

function validateStoredEvent(event, expectedSequence, previousHash, expectedRunIdHash, expectedWorkspaceScopeHash = null) {
  assertExactKeys(event, EVENT_KEYS, 'EVENT_FIELD_FORBIDDEN')
  invariant(event?.schema === EVENT_SCHEMA, 'EVENT_SCHEMA_INVALID')
  invariant(event.release?.packageId === PACKAGE_ID && event.release?.productVersion === WORKSPACE_PRODUCT_VERSION, 'EVENT_RELEASE_INVALID')
  assertExactKeys(event.release, new Set(['packageId', 'productVersion']), 'EVENT_RELEASE_FIELD_FORBIDDEN')
  assertExactKeys(event.privacy, new Set(['class', 'contentStored', 'schemaVersion']), 'EVENT_PRIVACY_FIELD_FORBIDDEN')
  invariant(event.privacy.class === 'operational_metadata' && event.privacy.contentStored === false && event.privacy.schemaVersion === 'v1', 'EVENT_PRIVACY_INVALID')
  invariant(event.sequence === expectedSequence, 'EVENT_SEQUENCE_INVALID')
  invariant(event.previousEventHash === previousHash, 'EVENT_PREVIOUS_HASH_INVALID')
  invariant(event.runIdHash === expectedRunIdHash, 'RUN_ID_HASH_INVALID', 'Stored event is not bound to the requested run')
  invariant(Number.isFinite(Date.parse(event.occurredAt)) && Number.isFinite(Date.parse(event.recordedAt)), 'EVENT_TIME_INVALID')
  invariant(typeof event.eventId === 'string' && EVENT_ID_PATTERN.test(event.eventId), 'EVENT_ID_INVALID')
  if (expectedWorkspaceScopeHash !== null) {
    const expectedEventId = `evt_${sha256({
      workspaceIdHash: expectedWorkspaceScopeHash,
      runIdHash: expectedRunIdHash,
      actorId: event.actorId,
      eventType: event.eventType,
      evidence: event.evidence,
      metadata: event.metadata,
      payloadHash: event.payloadHash,
    }).slice(0, 32)}`
    invariant(event.eventId === expectedEventId, 'EVENT_ID_DERIVATION_MISMATCH')
  }
  invariant(Object.hasOwn(EVENT_CATALOG, event.eventType), 'EVENT_TYPE_NOT_REGISTERED')
  invariant(event.actorId === WRITER_ID, 'EVENT_WRITER_INVALID')
  validateStoredEvidence(event.eventType, event.evidence)
  normalizeMetadata(event.metadata)
  if (event.payloadHash !== null) invariant(HEX_64.test(event.payloadHash), 'PAYLOAD_HASH_INVALID')
  if (HASH_BOUND_EVENT_TYPES.has(event.eventType)) invariant(typeof event.payloadHash === 'string' && HEX_64.test(event.payloadHash), payloadHashRequiredCode(event.eventType), `${event.eventType} must bind the exact durable payload hash`)
  const expectedHash = sha256(Object.fromEntries(Object.entries(event).filter(([key]) => key !== 'eventHash')))
  invariant(event.eventHash === expectedHash, 'EVENT_HASH_INVALID')
  return event
}

function validateEventTransition(previousEvents, nextEventType, nextMetadata = {}, nextPayloadHash = null) {
  const priorTypes = previousEvents.map((event) => event.eventType)
  const has = (eventType) => priorTypes.includes(eventType)
  const terminal = priorTypes.some((eventType) => eventType === 'run.failed' || eventType === 'run.stopped')
  invariant(!terminal || nextEventType === 'checkpoint.created', 'RUN_ALREADY_TERMINAL')
  if (previousEvents.length === 0) invariant(nextEventType === 'meeting.opened', 'MEETING_OPEN_REQUIRED_FIRST')
  const prerequisites = {
    'agenda.registered': ['meeting.opened'],
    'plan.frozen': ['agenda.registered'],
    'team.create_requested': ['plan.frozen'],
    'team.created': ['team.create_requested'],
    'team.create_failed': ['team.create_requested'],
    'seat.selected': ['team.created'],
    'seat.dispatch_requested': ['seat.selected'],
    'seat.dispatched': ['seat.dispatch_requested'],
    'seat.dispatch_failed': ['seat.dispatch_requested'],
    'seat.result_received': ['seat.dispatched'],
    'seat.result_recovered': ['seat.dispatched'],
    'round.independent_sealed': ['seat.selected'],
    'challenge.dispatched': ['round.independent_sealed'],
    'challenge.result_received': ['challenge.dispatched'],
    'collection.ready': ['round.independent_sealed'],
    'memo.compiled': ['collection.ready'],
    'artifact.presented': ['memo.compiled'],
    'user.confirmed': ['artifact.presented'],
    'run.failed': ['meeting.opened'],
    'run.stopped': ['meeting.opened'],
    'checkpoint.created': ['meeting.opened'],
  }
  for (const required of prerequisites[nextEventType] || []) {
    invariant(has(required), 'EVENT_PREREQUISITE_MISSING', `${nextEventType} requires ${required}`, { nextEventType, required })
  }
  if (nextEventType === 'agenda.registered') {
    invariant(Number.isInteger(nextMetadata.count) && nextMetadata.count >= 1 && nextMetadata.count <= 5, 'AGENDA_COUNT_INVALID', 'One run must contain one to five agenda items')
  }
  if (nextEventType === 'plan.frozen') {
    invariant(Number.isInteger(nextMetadata.revision) && nextMetadata.revision >= 1, 'PLAN_REVISION_METADATA_REQUIRED')
    invariant(!previousEvents.some((event) => event.eventType === 'plan.frozen' && event.metadata?.revision === nextMetadata.revision), 'PLAN_REVISION_ALREADY_FROZEN')
  }
  const seatEvents = new Set(['seat.selected', 'seat.dispatch_requested', 'seat.dispatched', 'seat.dispatch_failed', 'seat.result_received', 'seat.result_recovered', 'seat.result_failed'])
  if (seatEvents.has(nextEventType)) {
    safeId(nextMetadata.agendaItemId, 'SEAT_EVENT_AGENDA_ID_REQUIRED')
    safeId(nextMetadata.seatId, 'SEAT_EVENT_ID_REQUIRED')
    invariant(PROFESSIONAL_SEAT_IDS.has(nextMetadata.seatId) || SUPPORT_SEAT_IDS.has(nextMetadata.seatId), 'SEAT_EVENT_ID_UNAVAILABLE')
    invariant(Number.isInteger(nextMetadata.revision) && nextMetadata.revision >= 1, 'SEAT_EVENT_REVISION_REQUIRED')
    const sameScope = (event) => event.metadata?.agendaItemId === nextMetadata.agendaItemId
      && event.metadata?.seatId === nextMetadata.seatId
      && event.metadata?.revision === nextMetadata.revision
    const scopeSealed = previousEvents.some((event) => event.eventType === 'round.independent_sealed'
      && event.metadata?.agendaItemId === nextMetadata.agendaItemId
      && event.metadata?.revision === nextMetadata.revision)
    invariant(!scopeSealed, 'ROUND_ALREADY_SEALED', 'No seat event may be appended after its agenda revision is sealed')
    const priorEventForSeat = (eventType) => previousEvents.find((event) => event.eventType === eventType && sameScope(event))
    const priorForSeat = (eventType) => Boolean(priorEventForSeat(eventType))
    if (nextEventType === 'seat.selected') {
      invariant(previousEvents.some((event) => event.eventType === 'plan.frozen' && event.metadata?.revision === nextMetadata.revision), 'SEAT_PLAN_REVISION_NOT_FROZEN')
      invariant(!priorForSeat('seat.selected'), 'SEAT_ALREADY_SELECTED')
    }
    if (nextEventType === 'seat.dispatch_requested') {
      invariant(priorForSeat('seat.selected'), 'SEAT_NOT_SELECTED')
      invariant(!priorForSeat('seat.dispatch_requested'), 'SEAT_DISPATCH_ALREADY_REQUESTED')
    }
    if (nextEventType === 'seat.dispatched' || nextEventType === 'seat.dispatch_failed') {
      const requested = priorEventForSeat('seat.dispatch_requested')
      invariant(requested, 'SEAT_DISPATCH_NOT_REQUESTED')
      invariant(requested.payloadHash === nextPayloadHash, 'SEAT_DISPATCH_TASK_HASH_MISMATCH', 'Dispatch resolution must bind the same task bytes as its request')
      invariant(!priorForSeat('seat.dispatched') && !priorForSeat('seat.dispatch_failed'), 'SEAT_DISPATCH_ALREADY_RESOLVED')
    }
    if (nextEventType === 'seat.result_received' || nextEventType === 'seat.result_recovered' || nextEventType === 'seat.result_failed') {
      const dispatchSucceeded = priorForSeat('seat.dispatched')
      const dispatchFailed = priorForSeat('seat.dispatch_failed')
      invariant(nextEventType === 'seat.result_failed' ? (dispatchSucceeded || dispatchFailed) : dispatchSucceeded, 'SEAT_NOT_DISPATCHED')
      const priorTerminalResult = priorForSeat('seat.result_received') || priorForSeat('seat.result_failed')
      if (nextEventType === 'seat.result_received') {
        invariant(!priorTerminalResult, 'SEAT_RESULT_ALREADY_RECORDED')
        const recovered = priorEventForSeat('seat.result_recovered')
        if (recovered) invariant(recovered.payloadHash === nextPayloadHash, 'SEAT_RESULT_RECOVERY_HASH_MISMATCH', 'A trusted receipt may upgrade a recovered result only for the same result bytes')
      }
      else invariant(!priorTerminalResult && !priorForSeat('seat.result_recovered'), 'SEAT_RESULT_ALREADY_RECORDED')
    }
  }
  if (nextEventType === 'round.independent_sealed') {
    safeId(nextMetadata.agendaItemId, 'ROUND_AGENDA_ID_REQUIRED')
    invariant(Number.isInteger(nextMetadata.revision) && nextMetadata.revision >= 1, 'ROUND_REVISION_REQUIRED')
    const inRound = (event) => event.metadata?.agendaItemId === nextMetadata.agendaItemId && event.metadata?.revision === nextMetadata.revision
    invariant(!previousEvents.some((event) => event.eventType === 'round.independent_sealed' && inRound(event)), 'ROUND_ALREADY_SEALED')
    const selectedSeatIds = [...new Set(previousEvents.filter((event) => event.eventType === 'seat.selected' && inRound(event)).map((event) => event.metadata.seatId))]
    invariant(selectedSeatIds.length >= 1, 'ROUND_HAS_NO_SELECTED_SEATS')
    const resolvingTypes = new Set(['seat.result_received', 'seat.result_recovered', 'seat.result_failed'])
    const unresolvedSeatIds = selectedSeatIds.filter((seatId) => !previousEvents.some((event) => resolvingTypes.has(event.eventType) && inRound(event) && event.metadata?.seatId === seatId))
    invariant(unresolvedSeatIds.length === 0, 'ROUND_SELECTED_SEATS_UNRESOLVED', 'Every selected seat must have a result or a durable failure event before sealing', { unresolvedSeatIds })
  }
  if (nextEventType === 'memo.compiled' && has('challenge.dispatched')) {
    invariant(has('challenge.result_received'), 'EVENT_PREREQUISITE_MISSING', 'memo.compiled requires challenge.result_received after a challenge was dispatched')
  }
  if (nextEventType === 'memo.compiled') invariant(Number.isInteger(nextMetadata.revision) && nextMetadata.revision >= 1, 'MEMO_REVISION_REQUIRED')
  if (nextEventType === 'collection.ready') {
    invariant(Number.isInteger(nextMetadata.count) && nextMetadata.count >= 1, 'COLLECTION_COUNT_INVALID')
    invariant(Number.isInteger(nextMetadata.revision) && nextMetadata.revision >= 1, 'COLLECTION_REVISION_REQUIRED')
    const selectedAgendaIds = [...new Set(previousEvents
      .filter((event) => event.eventType === 'seat.selected' && event.metadata?.revision === nextMetadata.revision)
      .map((event) => event.metadata.agendaItemId))]
    const unsealedAgendaIds = selectedAgendaIds.filter((agendaItemId) => !previousEvents.some((event) => event.eventType === 'round.independent_sealed'
      && event.metadata?.agendaItemId === agendaItemId && event.metadata?.revision === nextMetadata.revision))
    invariant(selectedAgendaIds.length > 0 && unsealedAgendaIds.length === 0, 'COLLECTION_ROUNDS_UNSEALED', 'Every agenda in the collection revision must be independently sealed', { unsealedAgendaIds })
  }
}

function verifyEvents(events, expectedRunIdHash, expectedWorkspaceScopeHash = null) {
  let previousHash = 'genesis'
  const ids = new Set()
  events.forEach((event, index) => {
    validateEventTransition(events.slice(0, index), event.eventType, event.metadata, event.payloadHash)
    validateStoredEvent(event, index + 1, previousHash, expectedRunIdHash, expectedWorkspaceScopeHash)
    invariant(!ids.has(event.eventId), 'EVENT_ID_DUPLICATE')
    ids.add(event.eventId)
    previousHash = event.eventHash
  })
  return { ok: true, count: events.length, chainHead: previousHash }
}

async function readEvents(paths, runId, knownWorkspaceMarker = null) {
  let raw = ''
  await rejectExistingLinkSegments(paths.root, paths.eventFile, 'EVENT_FILE_LINK_FORBIDDEN')
  try {
    await requireRegularFileNoLink(paths.eventFile, 'EVENT_FILE_INVALID')
    raw = await readFile(paths.eventFile, 'utf8')
  } catch (error) {
    if (!(error instanceof BoardContractError && error.details?.cause === 'ENOENT')) throw error
  }
  const marker = knownWorkspaceMarker || await readWorkspace(paths.root)
  verifyCurrentEventLedgerBytes(raw, runId, workspaceScopeHash(marker))
  const events = parseJsonLines(raw, paths.eventFile)
  verifyEvents(events, sha256(runId), workspaceScopeHash(marker))
  for (const event of events.filter((item) => item.evidence?.level === 'host_runtime_receipt')) {
    await requireHostReceiptBinding(paths, marker, runId, event.eventType, event.metadata, event.payloadHash, event.evidence.receiptRef)
  }
  for (const event of events.filter((item) => item.eventType === 'plan.frozen')) {
    await requireFrozenPlanBinding(paths, runId, event.metadata, event.payloadHash, event.evidence)
  }
  return events
}

function hostReceiptTarget(paths, receiptRef) {
  invariant(typeof receiptRef === 'string' && HOST_RECEIPT_REF_PATTERN.test(receiptRef), 'HOST_RECEIPT_REF_INVALID')
  const target = path.join(paths.hostReceipts, `${receiptRef}.json`)
  ensureWithin(paths.root, target)
  return target
}

function validateHostReceiptRecord(record) {
  invariant(isObject(record), 'HOST_RECEIPT_RECORD_INVALID')
  assertExactKeys(record, HOST_RECEIPT_RECORD_KEYS, 'HOST_RECEIPT_RECORD_FIELD_FORBIDDEN')
  assertRequiredKeys(record, [...HOST_RECEIPT_RECORD_KEYS], 'HOST_RECEIPT_RECORD_FIELD_REQUIRED')
  invariant(record.schema === HOST_RECEIPT_RECORD_SCHEMA, 'HOST_RECEIPT_RECORD_SCHEMA_INVALID')
  invariant(typeof record.receiptRef === 'string' && HOST_RECEIPT_REF_PATTERN.test(record.receiptRef), 'HOST_RECEIPT_REF_INVALID')
  invariant(HEX_64.test(record.workspaceIdHash) && HEX_64.test(record.runIdHash), 'HOST_RECEIPT_SCOPE_INVALID')
  invariant(EVENT_CATALOG[record.eventType]?.includes('host_runtime_receipt'), 'HOST_RECEIPT_EVENT_TYPE_INVALID')
  normalizeMetadata(record.metadata)
  if (record.payloadHash !== null) invariant(HEX_64.test(record.payloadHash), 'HOST_RECEIPT_PAYLOAD_HASH_INVALID')
  if (HASH_BOUND_EVENT_TYPES.has(record.eventType)) invariant(typeof record.payloadHash === 'string' && HEX_64.test(record.payloadHash), payloadHashRequiredCode(record.eventType))
  invariant(HEX_64.test(record.hostReceiptDigest), 'HOST_RECEIPT_DIGEST_INVALID')
  invariant(record.verificationState === 'unverified_observation', 'HOST_RECEIPT_VERIFICATION_STATE_INVALID')
  invariant(record.recordedBy === WRITER_ID && Number.isFinite(Date.parse(record.recordedAt)), 'HOST_RECEIPT_RECORD_OWNER_INVALID')
  assertExactKeys(record.release, new Set(['packageId', 'productVersion']), 'HOST_RECEIPT_RELEASE_FIELD_FORBIDDEN')
  invariant(record.release.packageId === PACKAGE_ID && record.release.productVersion === WORKSPACE_PRODUCT_VERSION, 'HOST_RECEIPT_RELEASE_INVALID')
  invariant(record.evidenceBoundary === HOST_RECEIPT_RECORD_EVIDENCE_BOUNDARY, 'HOST_RECEIPT_EVIDENCE_BOUNDARY_INVALID')
  const expectedRef = `rcpt_${sha256({
    workspaceIdHash: record.workspaceIdHash,
    runIdHash: record.runIdHash,
    eventType: record.eventType,
    metadata: record.metadata,
    payloadHash: record.payloadHash,
    hostReceiptDigest: record.hostReceiptDigest,
  }).slice(0, 32)}`
  invariant(record.receiptRef === expectedRef, 'HOST_RECEIPT_REF_DERIVATION_MISMATCH')
  return record
}

async function readHostReceiptRecord(paths, receiptRef) {
  const target = hostReceiptTarget(paths, receiptRef)
  await rejectExistingLinkSegments(paths.root, target, 'HOST_RECEIPT_LINK_FORBIDDEN')
  await requireRegularFileNoLink(target, 'HOST_RECEIPT_RECORD_UNAVAILABLE')
  let record
  try { record = JSON.parse(await readFile(target, 'utf8')) }
  catch { throw new BoardContractError('HOST_RECEIPT_RECORD_INVALID', 'Host receipt record is invalid') }
  validateHostReceiptRecord(record)
  invariant(record.receiptRef === receiptRef, 'HOST_RECEIPT_REF_MISMATCH')
  return { record, target }
}

function hostReceiptScope(marker, runId, eventType, metadata, payloadHash, hostReceiptDigest) {
  return {
    workspaceIdHash: workspaceScopeHash(marker),
    runIdHash: sha256(runId),
    eventType,
    metadata,
    payloadHash,
    hostReceiptDigest,
  }
}

export async function recordHostReceiptObservation(input) {
  const snapshot = snapshotTransportData(input, 'HOST_RECEIPT_INPUT_INVALID')
  assertExactKeys(snapshot, HOST_RECEIPT_INPUT_KEYS, 'HOST_RECEIPT_INPUT_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot, [...HOST_RECEIPT_INPUT_KEYS], 'HOST_RECEIPT_INPUT_FIELD_REQUIRED')
  const { workspaceRoot, runId, actorId, eventType, payloadHash, hostReceiptDigest } = snapshot
  const workspaceMarker = await requireWritableWorkspace(workspaceRoot)
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  invariant(RUN_ID_PATTERN.test(runId), 'RUN_ID_INVALID')
  invariant(EVENT_CATALOG[eventType]?.includes('host_runtime_receipt'), 'HOST_RECEIPT_EVENT_TYPE_INVALID')
  const metadata = normalizeMetadata(snapshot.metadata)
  if (payloadHash !== null) invariant(typeof payloadHash === 'string' && HEX_64.test(payloadHash), 'HOST_RECEIPT_PAYLOAD_HASH_INVALID')
  if (HASH_BOUND_EVENT_TYPES.has(eventType)) invariant(typeof payloadHash === 'string' && HEX_64.test(payloadHash), payloadHashRequiredCode(eventType))
  invariant(typeof hostReceiptDigest === 'string' && HEX_64.test(hostReceiptDigest), 'HOST_RECEIPT_DIGEST_INVALID')
  const scope = hostReceiptScope(workspaceMarker, runId, eventType, metadata, payloadHash, hostReceiptDigest)
  const receiptRef = `rcpt_${sha256(scope).slice(0, 32)}`
  const paths = workspacePaths(workspaceRoot, runId)
  const target = hostReceiptTarget(paths, receiptRef)
  const record = validateHostReceiptRecord({
    schema: HOST_RECEIPT_RECORD_SCHEMA,
    receiptRef,
    ...scope,
    verificationState: 'unverified_observation',
    recordedBy: WRITER_ID,
    recordedAt: new Date().toISOString(),
    release: { packageId: PACKAGE_ID, productVersion: WORKSPACE_PRODUCT_VERSION },
    evidenceBoundary: HOST_RECEIPT_RECORD_EVIDENCE_BOUNDARY,
  })
  await rejectExistingLinkSegments(paths.root, paths.hostReceipts, 'HOST_RECEIPT_DIRECTORY_LINK_FORBIDDEN')
  await mkdir(paths.hostReceipts, { recursive: true })
  await rejectExistingLinkSegments(paths.root, target, 'HOST_RECEIPT_LINK_FORBIDDEN')
  const created = await publishExclusiveJson(target, record)
  if (!created) {
    const existing = await readHostReceiptRecord(paths, receiptRef)
    const comparable = ({ recordedAt, ...value }) => value
    invariant(sha256(comparable(existing.record)) === sha256(comparable(record)), 'HOST_RECEIPT_RECORD_CONFLICT')
    return { receiptRef, recordPayloadHash: sha256(existing.record), idempotent: true, evidenceBoundary: HOST_RECEIPT_RECORD_EVIDENCE_BOUNDARY }
  }
  return { receiptRef, recordPayloadHash: sha256(record), idempotent: false, evidenceBoundary: HOST_RECEIPT_RECORD_EVIDENCE_BOUNDARY }
}

async function requireHostReceiptBinding(paths, marker, runId, eventType, metadata, payloadHash, receiptRef) {
  const { record } = await readHostReceiptRecord(paths, receiptRef)
  const expected = hostReceiptScope(marker, runId, eventType, metadata, payloadHash, record.hostReceiptDigest)
  for (const key of ['workspaceIdHash', 'runIdHash', 'eventType', 'metadata', 'payloadHash']) {
    invariant(sha256(record[key]) === sha256(expected[key]), 'HOST_RECEIPT_SCOPE_MISMATCH')
  }
  invariant(record.verificationState === 'externally_verified', 'HOST_RECEIPT_EXTERNAL_VERIFIER_REQUIRED', 'Unverified host observations cannot advance the event state machine')
  return record
}

function storedUserConfirmationEvidence(marker, runId, eventType, metadata, payloadHash, sourceReceiptRef) {
  const digest = sha256({
    workspaceIdHash: workspaceScopeHash(marker),
    runIdHash: sha256(runId),
    eventType,
    metadata,
    payloadHash,
    sourceReceiptDigest: sha256(sourceReceiptRef),
  })
  return { level: 'user_confirmation', receiptRef: `rcpt_${digest.slice(0, 32)}` }
}

async function requireFrozenPlanBinding(paths, runId, metadata, payloadHash, evidence) {
  await rejectExistingLinkSegments(paths.root, paths.planFile, 'PLAN_FROZEN_PLAN_LINK_FORBIDDEN')
  await requireRegularFileNoLink(paths.planFile, 'PLAN_FROZEN_PLAN_INVALID')
  const plan = validateReviewPlan(await readJsonFile(paths.planFile, 'PLAN_FROZEN_PLAN_INVALID'))
  invariant(plan.runId === runId, 'PLAN_FROZEN_RUN_MISMATCH', 'The durable plan must belong to the event run')
  invariant(plan.revision === metadata?.revision, 'PLAN_FROZEN_REVISION_MISMATCH', 'The event revision must match the durable plan revision')
  const marker = await readWorkspace(paths.root)
  const expectedEvidence = storedUserConfirmationEvidence(marker, runId, 'plan.frozen', metadata, payloadHash, plan.confirmationReceiptId)
  invariant(evidence?.receiptRef === expectedEvidence.receiptRef, 'PLAN_FROZEN_CONFIRMATION_RECEIPT_MISMATCH', 'plan.frozen must carry the workspace-bound confirmation receipt reference')
  invariant(sha256(plan) === payloadHash, 'PLAN_FROZEN_PAYLOAD_HASH_MISMATCH', 'plan.frozen must bind the exact canonical durable plan hash')
  await requirePlanConfirmationRecordBinding(paths, marker, plan)
  return plan
}

export async function appendEvent(input) {
  const snapshot = snapshotTransportData(input, 'EVENT_INPUT_INVALID')
  assertExactKeys(snapshot, EVENT_INPUT_KEYS, 'EVENT_INPUT_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot, ['workspaceRoot', 'runId', 'actorId', 'eventType', 'evidence'], 'EVENT_INPUT_FIELD_REQUIRED')
  const { workspaceRoot, runId, actorId, eventType } = snapshot
  invariant(eventType !== 'user.confirmed', 'DECISION_DEDICATED_WRITER_REQUIRED', 'user.confirmed requires the externally verified dedicated decision writer')
  const payloadHash = Object.hasOwn(snapshot, 'payloadHash') ? snapshot.payloadHash : null
  const workspaceMarker = await requireWritableWorkspace(workspaceRoot)
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN', 'Only board-convener may append shared meeting state')
  invariant(Object.hasOwn(EVENT_CATALOG, eventType), 'EVENT_TYPE_NOT_REGISTERED')
  const inputEvidence = normalizeEventEvidenceInput(eventType, snapshot.evidence)
  const metadata = normalizeMetadata(Object.hasOwn(snapshot, 'metadata') ? snapshot.metadata : {})
  if (payloadHash !== null) invariant(HEX_64.test(payloadHash), 'PAYLOAD_HASH_INVALID')
  if (HASH_BOUND_EVENT_TYPES.has(eventType)) invariant(typeof payloadHash === 'string' && HEX_64.test(payloadHash), payloadHashRequiredCode(eventType), `${eventType} must bind the exact durable payload hash`)
  const paths = workspacePaths(workspaceRoot, runId)
  if (inputEvidence.level === 'host_runtime_receipt') {
    await requireHostReceiptBinding(paths, workspaceMarker, runId, eventType, metadata, payloadHash, inputEvidence.receiptRef)
  }
  const evidence = inputEvidence.level === 'user_confirmation'
    ? storedUserConfirmationEvidence(workspaceMarker, runId, eventType, metadata, payloadHash, inputEvidence.receiptRef)
    : inputEvidence
  const eventId = `evt_${sha256({
    workspaceIdHash: workspaceScopeHash(workspaceMarker), runIdHash: sha256(runId), actorId,
    eventType, evidence, metadata, payloadHash,
  }).slice(0, 32)}`
  const occurredAt = new Date().toISOString()
  await rejectExistingLinkSegments(paths.root, paths.eventFile, 'EVENT_FILE_LINK_FORBIDDEN')
  await rejectExistingLinkSegments(paths.root, paths.lockFile, 'EVENT_LOCK_LINK_FORBIDDEN')
  await mkdir(paths.events, { recursive: true })
  await mkdir(paths.locks, { recursive: true })
  const lock = await acquireLock(paths.lockFile)
  try {
    const events = await readEvents(paths, runId)
    const intentDigest = sha256({ runIdHash: sha256(runId), actorId, eventId, eventType, evidence, metadata, payloadHash })
    const existing = events.find((event) => event.eventId === eventId)
    if (existing) {
      invariant(existing.intentDigest === intentDigest, 'EVENT_IDEMPOTENCY_CONFLICT')
      return { ok: true, idempotent: true, event: existing, eventFile: paths.eventFile }
    }
    validateEventTransition(events, eventType, metadata, payloadHash)
    if (eventType === 'plan.frozen') await requireFrozenPlanBinding(paths, runId, metadata, payloadHash, evidence)
    const withoutHash = {
      schema: EVENT_SCHEMA,
      eventId,
      eventType,
      sequence: events.length + 1,
      occurredAt,
      recordedAt: new Date().toISOString(),
      runIdHash: sha256(runId),
      actorId,
      evidence,
      metadata,
      payloadHash,
      release: { packageId: PACKAGE_ID, productVersion: WORKSPACE_PRODUCT_VERSION },
      privacy: { class: 'operational_metadata', contentStored: false, schemaVersion: 'v1' },
      intentDigest,
      previousEventHash: events.at(-1)?.eventHash || 'genesis',
    }
    const event = { ...withoutHash, eventHash: sha256(withoutHash) }
    validateStoredEvent(event, events.length + 1, withoutHash.previousEventHash, sha256(runId), workspaceScopeHash(workspaceMarker))
    const handle = await open(paths.eventFile, fsConstants.O_CREAT | fsConstants.O_APPEND | fsConstants.O_WRONLY, 0o600)
    try {
      const info = await handle.stat()
      invariant(info.isFile() && info.nlink === 1, 'EVENT_FILE_LINK_FORBIDDEN', 'Event ledger must not be a hard link')
      await handle.write(`${canonical(event)}\n`, null, 'utf8')
      await handle.sync()
    } finally { await handle.close() }
    return { ok: true, idempotent: false, event, eventFile: paths.eventFile }
  } finally { await releaseLock(lock, paths.lockFile) }
}

export async function verifyLedger(workspaceRoot, runId) {
  const inspected = await inspectWorkspaceAccess(workspaceRoot)
  if (inspected.accessMode === 'predecessor_read_only') throw new BoardContractError('WORKSPACE_PREDECESSOR_READ_ONLY', 'Predecessor workspaces require their frozen v2 verifier')
  if (inspected.accessMode === 'legacy_read_only') throw new BoardContractError('WORKSPACE_LEGACY_READ_ONLY', 'Legacy workspaces require their frozen v1 verifier')
  if (inspected.accessMode !== 'current_read_write') throw new BoardContractError('WORKSPACE_VERSION_UNSUPPORTED')
  const paths = workspacePaths(workspaceRoot, runId)
  const events = await readEvents(paths, runId, inspected.marker)
  return { ...verifyEvents(events, sha256(runId)), runId, eventFile: paths.eventFile }
}

function boundedText(value, field, max = 4000) {
  invariant(typeof value === 'string' && value.trim(), `${field.toUpperCase()}_REQUIRED`)
  invariant(value.length <= max, `${field.toUpperCase()}_TOO_LONG`)
  return value.trim()
}

function memberArtifactTargets({ agendaItemId, seatId, revision = 1 }) {
  safeId(agendaItemId, 'MEMBER_TARGET_AGENDA_ID_INVALID')
  safeId(seatId, 'MEMBER_TARGET_SEAT_ID_INVALID')
  invariant(Number.isInteger(revision) && revision >= 1, 'MEMBER_TARGET_REVISION_INVALID')
  return {
    taskTarget: `tasks/${agendaItemId}/${seatId}.task.r${revision}.json`,
    resultTarget: `results/${agendaItemId}/${seatId}.r${revision}.json`,
    deliveryObservationTarget: `receipts/${agendaItemId}/${seatId}.r${revision}.send-message.json`,
    failureTarget: `failures/${agendaItemId}/${seatId}.r${revision}.json`,
  }
}

export function expectedMemberTargets(input) {
  return memberArtifactTargets(input)
}

export function validateProcessSupportHandoff(input) {
  invariant(isObject(input), 'SUPPORT_HANDOFF_REQUIRED')
  assertExactKeys(input, PROCESS_SUPPORT_HANDOFF_KEYS, 'SUPPORT_HANDOFF_FIELD_FORBIDDEN')
  assertRequiredKeys(input, [...PROCESS_SUPPORT_HANDOFF_KEYS], 'SUPPORT_HANDOFF_FIELD_REQUIRED')
  invariant(input.schema === PROCESS_SUPPORT_HANDOFF_SCHEMA, 'SUPPORT_HANDOFF_SCHEMA_INVALID')
  safeId(input.runId, 'SUPPORT_HANDOFF_RUN_ID_INVALID')
  safeId(input.agendaItemId, 'SUPPORT_HANDOFF_AGENDA_ID_INVALID')
  safeId(input.seatId, 'SUPPORT_HANDOFF_SEAT_ID_INVALID')
  invariant(input.seatId === 'board-secretary', 'SUPPORT_HANDOFF_SEAT_INVALID')
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'SUPPORT_HANDOFF_REVISION_INVALID')
  const expected = memberArtifactTargets(input).resultTarget
  invariant(input.resultTarget === expected, 'SUPPORT_HANDOFF_RESULT_TARGET_MISMATCH')
  invariant(typeof input.resultPayloadHash === 'string' && HEX_64.test(input.resultPayloadHash), 'SUPPORT_HANDOFF_RESULT_HASH_INVALID')
  return {
    schema: input.schema,
    runId: input.runId,
    agendaItemId: input.agendaItemId,
    seatId: input.seatId,
    revision: input.revision,
    resultTarget: input.resultTarget,
    resultPayloadHash: input.resultPayloadHash,
  }
}

function normalizeSeatSelection(input, codePrefix) {
  invariant(['quick_review', 'standard_review', 'deep_review'].includes(input.reviewMode), `${codePrefix}_REVIEW_MODE_INVALID`)
  invariant(Array.isArray(input.specialistSeatIds), `${codePrefix}_SPECIALIST_SEATS_INVALID`)
  const specialistSeatIds = input.specialistSeatIds.map((seatId) => safeId(seatId, `${codePrefix}_SPECIALIST_SEAT_ID_INVALID`))
  invariant(new Set(specialistSeatIds).size === specialistSeatIds.length, `${codePrefix}_SPECIALIST_SEAT_DUPLICATE`)
  invariant(specialistSeatIds.every((seatId) => PROFESSIONAL_SEAT_IDS.has(seatId)), `${codePrefix}_SPECIALIST_SEAT_UNAVAILABLE`)
  const seatRange = input.reviewMode === 'quick_review' ? { min: 1, max: 1 } : { min: 2, max: 3 }
  invariant(specialistSeatIds.length >= seatRange.min && specialistSeatIds.length <= seatRange.max, `${codePrefix}_SPECIALIST_SEAT_COUNT_INVALID`, 'Selected specialist count does not match the review mode', { reviewMode: input.reviewMode, expected: seatRange, actual: specialistSeatIds.length })

  invariant(Array.isArray(input.supportSeatIds), `${codePrefix}_SUPPORT_SEATS_INVALID`)
  const supportSeatIds = input.supportSeatIds.map((seatId) => safeId(seatId, `${codePrefix}_SUPPORT_SEAT_ID_INVALID`))
  invariant(new Set(supportSeatIds).size === supportSeatIds.length, `${codePrefix}_SUPPORT_SEAT_DUPLICATE`)
  invariant(supportSeatIds.every((seatId) => SUPPORT_SEAT_IDS.has(seatId)), `${codePrefix}_SUPPORT_SEAT_UNAVAILABLE`)
  return { reviewMode: input.reviewMode, specialistSeatIds, supportSeatIds }
}

export function validateSeatProposal(input) {
  invariant(isObject(input), 'PROPOSAL_ENVELOPE_REQUIRED')
  assertExactKeys(input, SEAT_PROPOSAL_KEYS, 'PROPOSAL_FIELD_FORBIDDEN')
  invariant(input.schema === SEAT_PROPOSAL_SCHEMA, 'PROPOSAL_SCHEMA_INVALID')
  const selection = normalizeSeatSelection(input, 'PROPOSAL')
  return { schema: input.schema, ...selection }
}

function expectedEntryRoute(signals) {
  if (signals.hasResumeReference) return 'continue_or_resume'
  if (signals.hasDecisionQuestion && signals.hasUserMaterial) return 'material_review_intake'
  if (signals.hasDecisionQuestion) return 'decision_intake'
  if (signals.isCapabilityQuestion) return 'capability_discovery'
  if (signals.isOutOfScope || signals.hasUserMaterial) return 'graceful_redirect'
  return 'capability_discovery'
}

export function validateEntryIntent(input) {
  assertExactKeys(input, ENTRY_INTENT_KEYS, 'ENTRY_INTENT_FIELD_FORBIDDEN')
  invariant(input.schema === ENTRY_INTENT_SCHEMA, 'ENTRY_INTENT_SCHEMA_INVALID')
  invariant(ENTRY_INTENT_ROUTES.has(input.route), 'ENTRY_INTENT_ROUTE_INVALID')
  invariant(ENTRY_INTENT_CONFIDENCE_BANDS.has(input.confidenceBand), 'ENTRY_INTENT_CONFIDENCE_INVALID')
  assertExactKeys(input.signals, ENTRY_INTENT_SIGNAL_KEYS, 'ENTRY_INTENT_SIGNAL_FIELD_FORBIDDEN')
  for (const key of ENTRY_INTENT_SIGNAL_KEYS) {
    invariant(typeof input.signals[key] === 'boolean', 'ENTRY_INTENT_SIGNAL_INVALID', 'Every entry signal must be an explicit boolean', { key })
  }
  const signals = Object.fromEntries([...ENTRY_INTENT_SIGNAL_KEYS].map((key) => [key, input.signals[key]]))
  invariant(input.route === expectedEntryRoute(signals), 'ENTRY_INTENT_ROUTE_SIGNAL_CONFLICT')
  invariant(input.firstValueType === ENTRY_FIRST_VALUE_BY_ROUTE[input.route], 'ENTRY_INTENT_FIRST_VALUE_INVALID')
  invariant(input.teamCreationAllowed === false, 'ENTRY_INTENT_TEAM_CREATION_FORBIDDEN')
  invariant(input.workspaceWriteAllowed === false, 'ENTRY_INTENT_WORKSPACE_WRITE_FORBIDDEN')
  invariant(input.evidenceBoundary === 'model_classification_validated_by_package_shape_only', 'ENTRY_INTENT_EVIDENCE_BOUNDARY_INVALID')
  return {
    schema: input.schema,
    route: input.route,
    confidenceBand: input.confidenceBand,
    signals,
    firstValueType: input.firstValueType,
    teamCreationAllowed: false,
    workspaceWriteAllowed: false,
    evidenceBoundary: input.evidenceBoundary,
  }
}

function asciiCompare(left, right) {
  if (left < right) return -1
  if (left > right) return 1
  return 0
}

function assertDenseDataArray(value, maxLength, invalidCode, countCode) {
  invariant(Array.isArray(value), invalidCode)
  invariant(value.length <= maxLength, countCode)
  const allowedOwnKeys = new Set(['length', ...Array.from({ length: value.length }, (_, index) => String(index))])
  const ownKeys = Reflect.ownKeys(value)
  invariant(
    ownKeys.length === allowedOwnKeys.size
      && ownKeys.every((key) => typeof key === 'string' && allowedOwnKeys.has(key)),
    invalidCode,
    'Contract arrays must be dense and contain only indexed values',
    { length: value.length, ownKeyCount: ownKeys.length },
  )
}

function deriveMaterialGate(received, missing, pendingVerification) {
  const hasConditionalBlocker = missing.some((item) => item.blockingFor === 'conditional_conclusion')
  const hasConflictedMaterial = received.some((item) => item.status === 'received_conflicted')
  const state = received.length === 0
    ? 'sufficient_for_framing'
    : hasConditionalBlocker || hasConflictedMaterial
      ? 'insufficient_for_conclusion'
      : 'sufficient_for_conditional_review'
  const conclusionPolicy = state === 'sufficient_for_framing'
    ? 'framing_only'
    : state === 'insufficient_for_conclusion'
      ? 'no_conclusion'
      : 'conditional_only'
  const nextAction = state === 'sufficient_for_conditional_review'
    && missing.length === 0
    && pendingVerification.length === 0
    ? 'confirm_review'
    : 'add_facts'
  return { state, conclusionPolicy, nextAction }
}

export function validateMaterialSufficiency(input) {
  invariant(isObject(input), 'MATERIAL_ENVELOPE_REQUIRED')
  assertExactKeys(input, MATERIAL_KEYS, 'MATERIAL_FIELD_FORBIDDEN')
  assertRequiredKeys(input, MATERIAL_KEY_LIST, 'MATERIAL_FIELD_REQUIRED')
  invariant(input.schema === MATERIAL_SUFFICIENCY_SCHEMA, 'MATERIAL_SCHEMA_INVALID')
  invariant(MATERIAL_STATES.has(input.state), 'MATERIAL_STATE_INVALID')

  assertDenseDataArray(input.received, 64, 'MATERIAL_RECEIVED_INVALID', 'MATERIAL_RECEIVED_COUNT_INVALID')
  const received = Array.from(input.received, (item) => {
    invariant(isObject(item), 'MATERIAL_RECEIVED_INVALID')
    assertExactKeys(item, MATERIAL_RECEIVED_KEYS, 'MATERIAL_RECEIVED_FIELD_FORBIDDEN')
    assertRequiredKeys(item, MATERIAL_RECEIVED_KEY_LIST, 'MATERIAL_RECEIVED_FIELD_REQUIRED')
    invariant(typeof item.materialRef === 'string' && MATERIAL_REF_PATTERN.test(item.materialRef), 'MATERIAL_REF_INVALID')
    invariant(typeof item.version === 'string' && MATERIAL_VERSION_PATTERN.test(item.version), 'MATERIAL_VERSION_INVALID')
    invariant(MATERIAL_RECEIVED_STATUSES.has(item.status), 'MATERIAL_STATUS_INVALID')
    return { materialRef: item.materialRef, version: item.version, status: item.status }
  }).sort((left, right) => asciiCompare(left.materialRef, right.materialRef))
  invariant(new Set(received.map((item) => item.materialRef)).size === received.length, 'MATERIAL_RECEIVED_DUPLICATE')

  assertDenseDataArray(input.missing, 32, 'MATERIAL_MISSING_INVALID', 'MATERIAL_MISSING_COUNT_INVALID')
  const missing = Array.from(input.missing, (item) => {
    invariant(isObject(item), 'MATERIAL_MISSING_INVALID')
    assertExactKeys(item, MATERIAL_GAP_KEYS, 'MATERIAL_GAP_FIELD_FORBIDDEN')
    assertRequiredKeys(item, MATERIAL_GAP_KEY_LIST, 'MATERIAL_GAP_FIELD_REQUIRED')
    invariant(typeof item.gapId === 'string' && MATERIAL_GAP_ID_PATTERN.test(item.gapId), 'MATERIAL_GAP_ID_INVALID')
    invariant(MATERIAL_GAP_IMPACTS.has(item.impact), 'MATERIAL_GAP_IMPACT_INVALID')
    invariant(MATERIAL_GAP_BLOCKERS.has(item.blockingFor), 'MATERIAL_GAP_BLOCKING_FOR_INVALID')
    return { gapId: item.gapId, impact: item.impact, blockingFor: item.blockingFor }
  }).sort((left, right) => asciiCompare(left.gapId, right.gapId))
  invariant(new Set(missing.map((item) => item.gapId)).size === missing.length, 'MATERIAL_GAP_DUPLICATE')

  assertDenseDataArray(input.pendingVerification, 64, 'MATERIAL_PENDING_VERIFICATION_INVALID', 'MATERIAL_PENDING_VERIFICATION_INVALID')
  const pendingVerification = Array.from(input.pendingVerification, (materialRef) => {
    invariant(typeof materialRef === 'string' && MATERIAL_REF_PATTERN.test(materialRef), 'MATERIAL_PENDING_REF_INVALID')
    return materialRef
  }).sort(asciiCompare)
  invariant(new Set(pendingVerification).size === pendingVerification.length, 'MATERIAL_PENDING_REF_DUPLICATE')
  const receivedRefs = new Set(received.map((item) => item.materialRef))
  invariant(pendingVerification.every((materialRef) => receivedRefs.has(materialRef)), 'MATERIAL_PENDING_REF_UNKNOWN')
  const expectedPending = received
    .filter((item) => item.status !== 'received_verified')
    .map((item) => item.materialRef)
    .sort(asciiCompare)
  invariant(
    pendingVerification.length === expectedPending.length
      && pendingVerification.every((materialRef, index) => materialRef === expectedPending[index]),
    'MATERIAL_PENDING_REF_MISMATCH',
  )

  const {
    state: expectedState,
    conclusionPolicy: expectedConclusionPolicy,
    nextAction: expectedNextAction,
  } = deriveMaterialGate(received, missing, pendingVerification)

  invariant(input.state === expectedState, 'MATERIAL_STATE_MISMATCH')
  invariant(MATERIAL_CONCLUSION_POLICIES.has(input.conclusionPolicy), 'MATERIAL_CONCLUSION_POLICY_INVALID')
  invariant(input.conclusionPolicy === expectedConclusionPolicy, 'MATERIAL_CONCLUSION_POLICY_MISMATCH')
  invariant(MATERIAL_NEXT_ACTIONS.has(input.nextAction), 'MATERIAL_NEXT_ACTION_INVALID')
  invariant(input.nextAction === expectedNextAction, 'MATERIAL_NEXT_ACTION_MISMATCH')
  invariant(input.contentStoredInEventLedger === false, 'MATERIAL_EVENT_LEDGER_CONTENT_FORBIDDEN')

  return {
    schema: MATERIAL_SUFFICIENCY_SCHEMA,
    state: expectedState,
    received,
    missing,
    pendingVerification,
    conclusionPolicy: expectedConclusionPolicy,
    nextAction: expectedNextAction,
    contentStoredInEventLedger: false,
  }
}

function mintMaterialCardRef(prefix, used) {
  let value
  do { value = `${prefix}${randomBytes(16).toString('hex')}` } while (used.has(value))
  used.add(value)
  return value
}

export function buildMaterialSufficiency(input) {
  invariant(isObject(input), 'MATERIAL_CARD_DRAFT_REQUIRED')
  assertExactKeys(input, MATERIAL_CARD_DRAFT_KEYS, 'MATERIAL_CARD_DRAFT_FIELD_FORBIDDEN')
  assertRequiredKeys(input, MATERIAL_CARD_DRAFT_KEY_LIST, 'MATERIAL_CARD_DRAFT_FIELD_REQUIRED')
  invariant(input.schema === MATERIAL_CARD_DRAFT_SCHEMA, 'MATERIAL_CARD_DRAFT_SCHEMA_INVALID')
  invariant(input.contentStoredInEventLedger === false, 'MATERIAL_CARD_EVENT_LEDGER_CONTENT_FORBIDDEN')

  assertDenseDataArray(input.received, 64, 'MATERIAL_CARD_RECEIVED_INVALID', 'MATERIAL_CARD_RECEIVED_COUNT_INVALID')
  const usedMaterialRefs = new Set()
  const usedVersionRefs = new Set()
  const receivedBindings = []
  const received = input.received.map((slot, index) => {
    invariant(isObject(slot), 'MATERIAL_CARD_RECEIVED_SLOT_INVALID')
    assertExactKeys(slot, MATERIAL_CARD_RECEIVED_SLOT_KEYS, 'MATERIAL_CARD_RECEIVED_FIELD_FORBIDDEN')
    assertRequiredKeys(slot, MATERIAL_CARD_RECEIVED_SLOT_KEY_LIST, 'MATERIAL_CARD_RECEIVED_FIELD_REQUIRED')
    invariant(MATERIAL_CARD_VERSION_KINDS.has(slot.versionKind), 'MATERIAL_CARD_VERSION_KIND_INVALID')
    invariant(MATERIAL_RECEIVED_STATUSES.has(slot.status), 'MATERIAL_CARD_STATUS_INVALID')
    invariant(MATERIAL_CARD_INPUT_STATUSES.has(slot.status), 'MATERIAL_CARD_STATUS_UNPROVEN')
    if (slot.versionKind === 'user_declared') {
      invariant(Number.isInteger(slot.versionOrdinal) && slot.versionOrdinal >= 1 && slot.versionOrdinal <= 999999, 'MATERIAL_CARD_VERSION_ORDINAL_INVALID')
    } else {
      invariant(slot.versionOrdinal === null, 'MATERIAL_CARD_VERSION_ORDINAL_INVALID')
    }
    const materialRef = mintMaterialCardRef('mat_', usedMaterialRefs)
    const version = slot.versionKind === 'user_declared'
      ? `user_declared_v${slot.versionOrdinal}`
      : mintMaterialCardRef('ref_', usedVersionRefs)
    receivedBindings.push({ slot: index + 1, materialRef, version })
    return { materialRef, version, status: slot.status }
  })

  assertDenseDataArray(input.missing, 32, 'MATERIAL_CARD_MISSING_INVALID', 'MATERIAL_CARD_MISSING_COUNT_INVALID')
  const usedGapIds = new Set()
  const missingBindings = []
  const missing = input.missing.map((slot, index) => {
    invariant(isObject(slot), 'MATERIAL_CARD_MISSING_SLOT_INVALID')
    assertExactKeys(slot, MATERIAL_CARD_MISSING_SLOT_KEYS, 'MATERIAL_CARD_MISSING_FIELD_FORBIDDEN')
    assertRequiredKeys(slot, MATERIAL_CARD_MISSING_SLOT_KEY_LIST, 'MATERIAL_CARD_MISSING_FIELD_REQUIRED')
    invariant(MATERIAL_GAP_IMPACTS.has(slot.impact), 'MATERIAL_CARD_GAP_IMPACT_INVALID')
    invariant(MATERIAL_GAP_BLOCKERS.has(slot.blockingFor), 'MATERIAL_CARD_GAP_BLOCKING_FOR_INVALID')
    const gapId = mintMaterialCardRef('gap_', usedGapIds)
    missingBindings.push({ slot: index + 1, gapId })
    return { gapId, impact: slot.impact, blockingFor: slot.blockingFor }
  })

  const pendingVerification = received
    .filter((item) => item.status !== 'received_verified')
    .map((item) => item.materialRef)
  const { state, conclusionPolicy, nextAction } = deriveMaterialGate(received, missing, pendingVerification)
  const normalized = validateMaterialSufficiency({
    schema: MATERIAL_SUFFICIENCY_SCHEMA,
    state,
    received,
    missing,
    pendingVerification,
    conclusionPolicy,
    nextAction,
    contentStoredInEventLedger: false,
  })
  return {
    normalized,
    slotBindings: {
      received: receivedBindings,
      missing: missingBindings,
    },
  }
}

function validateWorkspaceMaterialRecord(record) {
  invariant(isObject(record), 'WORKSPACE_MATERIAL_RECORD_INVALID')
  assertExactKeys(record, WORKSPACE_MATERIAL_RECORD_KEYS, 'WORKSPACE_MATERIAL_RECORD_FIELD_FORBIDDEN')
  assertRequiredKeys(record, [...WORKSPACE_MATERIAL_RECORD_KEYS], 'WORKSPACE_MATERIAL_RECORD_FIELD_REQUIRED')
  invariant(record.schema === WORKSPACE_MATERIAL_RECORD_SCHEMA, 'WORKSPACE_MATERIAL_RECORD_SCHEMA_INVALID')
  invariant(HEX_64.test(record.workspaceIdHash) && HEX_64.test(record.runIdHash) && HEX_64.test(record.draftDigest), 'WORKSPACE_MATERIAL_RECORD_DIGEST_INVALID')
  const materialCard = validateMaterialSufficiency(record.materialCard)
  invariant(materialCard.received.every((item) => item.status !== 'received_verified'), 'WORKSPACE_MATERIAL_SELF_VERIFICATION_FORBIDDEN')
  invariant(record.recordedBy === WRITER_ID && Number.isFinite(Date.parse(record.recordedAt)), 'WORKSPACE_MATERIAL_RECORD_OWNER_INVALID')
  assertExactKeys(record.release, new Set(['packageId', 'productVersion']), 'WORKSPACE_MATERIAL_RELEASE_FIELD_FORBIDDEN')
  invariant(record.release.packageId === PACKAGE_ID && record.release.productVersion === WORKSPACE_PRODUCT_VERSION, 'WORKSPACE_MATERIAL_RELEASE_INVALID')
  invariant(record.evidenceBoundary === MATERIAL_CARD_BUILD_EVIDENCE_BOUNDARY, 'WORKSPACE_MATERIAL_EVIDENCE_BOUNDARY_INVALID')
  return { ...record, materialCard }
}

async function readWorkspaceMaterialRecord(paths) {
  await rejectExistingLinkSegments(paths.root, paths.materialCardFile, 'WORKSPACE_MATERIAL_RECORD_LINK_FORBIDDEN')
  await requireRegularFileNoLink(paths.materialCardFile, 'WORKSPACE_MATERIAL_RECORD_UNAVAILABLE')
  let record
  try { record = JSON.parse(await readFile(paths.materialCardFile, 'utf8')) }
  catch { throw new BoardContractError('WORKSPACE_MATERIAL_RECORD_INVALID', 'Workspace material record is invalid') }
  return validateWorkspaceMaterialRecord(record)
}

export async function recordWorkspaceMaterialCard(input) {
  const snapshot = snapshotTransportData(input, 'WORKSPACE_MATERIAL_INPUT_INVALID')
  assertExactKeys(snapshot, WORKSPACE_MATERIAL_INPUT_KEYS, 'WORKSPACE_MATERIAL_INPUT_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot, [...WORKSPACE_MATERIAL_INPUT_KEYS], 'WORKSPACE_MATERIAL_INPUT_FIELD_REQUIRED')
  const { workspaceRoot, runId, actorId, draft } = snapshot
  const marker = await requireWritableWorkspace(workspaceRoot)
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  invariant(RUN_ID_PATTERN.test(runId), 'RUN_ID_INVALID')
  const paths = workspacePaths(workspaceRoot, runId)
  const draftDigest = sha256(draft)
  if (await pathExists(paths.materialCardFile)) {
    const existing = await readWorkspaceMaterialRecord(paths)
    invariant(existing.workspaceIdHash === workspaceScopeHash(marker) && existing.runIdHash === sha256(runId), 'WORKSPACE_MATERIAL_SCOPE_MISMATCH')
    invariant(existing.draftDigest === draftDigest, 'WORKSPACE_MATERIAL_RECORD_CONFLICT')
    return { materialCard: existing.materialCard, materialCardRef: `matcard_${sha256(existing).slice(0, 32)}`, idempotent: true }
  }
  const { normalized } = buildMaterialSufficiency(draft)
  const record = validateWorkspaceMaterialRecord({
    schema: WORKSPACE_MATERIAL_RECORD_SCHEMA,
    workspaceIdHash: workspaceScopeHash(marker),
    runIdHash: sha256(runId),
    draftDigest,
    materialCard: normalized,
    recordedBy: WRITER_ID,
    recordedAt: new Date().toISOString(),
    release: { packageId: PACKAGE_ID, productVersion: WORKSPACE_PRODUCT_VERSION },
    evidenceBoundary: MATERIAL_CARD_BUILD_EVIDENCE_BOUNDARY,
  })
  await rejectExistingLinkSegments(paths.root, paths.materialCards, 'WORKSPACE_MATERIAL_DIRECTORY_LINK_FORBIDDEN')
  await mkdir(paths.materialCards, { recursive: true })
  await rejectExistingLinkSegments(paths.root, paths.materialCardFile, 'WORKSPACE_MATERIAL_RECORD_LINK_FORBIDDEN')
  const created = await publishExclusiveJson(paths.materialCardFile, record)
  if (!created) {
    const existing = await readWorkspaceMaterialRecord(paths)
    invariant(existing.draftDigest === draftDigest, 'WORKSPACE_MATERIAL_RECORD_CONFLICT')
    return { materialCard: existing.materialCard, materialCardRef: `matcard_${sha256(existing).slice(0, 32)}`, idempotent: true }
  }
  return { materialCard: record.materialCard, materialCardRef: `matcard_${sha256(record).slice(0, 32)}`, idempotent: false }
}

function publicSourceTarget(paths, sourceRef) {
  invariant(typeof sourceRef === 'string' && /^src_[0-9a-f]{32}$/.test(sourceRef), 'PUBLIC_SOURCE_REF_INVALID')
  const target = path.join(paths.evidenceSources, `${sourceRef}.json`)
  ensureWithin(paths.root, target)
  return target
}

function validatePublicSourceRecord(record) {
  invariant(isObject(record), 'PUBLIC_SOURCE_RECORD_INVALID')
  assertExactKeys(record, PUBLIC_SOURCE_RECORD_KEYS, 'PUBLIC_SOURCE_RECORD_FIELD_FORBIDDEN')
  assertRequiredKeys(record, [...PUBLIC_SOURCE_RECORD_KEYS], 'PUBLIC_SOURCE_RECORD_FIELD_REQUIRED')
  invariant(record.schema === PUBLIC_SOURCE_RECORD_SCHEMA, 'PUBLIC_SOURCE_RECORD_SCHEMA_INVALID')
  invariant(HEX_64.test(record.workspaceIdHash) && HEX_64.test(record.runIdHash) && HEX_64.test(record.sourceDigest), 'PUBLIC_SOURCE_RECORD_DIGEST_INVALID')
  const expectedRef = `src_${sha256({ workspaceIdHash: record.workspaceIdHash, runIdHash: record.runIdHash, sourceDigest: record.sourceDigest }).slice(0, 32)}`
  invariant(record.sourceRef === expectedRef, 'PUBLIC_SOURCE_REF_DERIVATION_MISMATCH')
  invariant(record.recordedBy === WRITER_ID && Number.isFinite(Date.parse(record.recordedAt)), 'PUBLIC_SOURCE_RECORD_OWNER_INVALID')
  assertExactKeys(record.release, new Set(['packageId', 'productVersion']), 'PUBLIC_SOURCE_RELEASE_FIELD_FORBIDDEN')
  invariant(record.release.packageId === PACKAGE_ID && record.release.productVersion === WORKSPACE_PRODUCT_VERSION, 'PUBLIC_SOURCE_RELEASE_INVALID')
  invariant(record.evidenceBoundary === PUBLIC_SOURCE_EVIDENCE_BOUNDARY, 'PUBLIC_SOURCE_EVIDENCE_BOUNDARY_INVALID')
  return record
}

async function readPublicSourceRecord(paths, sourceRef) {
  const target = publicSourceTarget(paths, sourceRef)
  await rejectExistingLinkSegments(paths.root, target, 'PUBLIC_SOURCE_LINK_FORBIDDEN')
  await requireRegularFileNoLink(target, 'PUBLIC_SOURCE_RECORD_UNAVAILABLE')
  let record
  try { record = JSON.parse(await readFile(target, 'utf8')) }
  catch { throw new BoardContractError('PUBLIC_SOURCE_RECORD_INVALID', 'Public source record is invalid') }
  validatePublicSourceRecord(record)
  invariant(record.sourceRef === sourceRef, 'PUBLIC_SOURCE_REF_MISMATCH')
  return { record, target }
}

export async function recordPublicSourceObservation(input) {
  const snapshot = snapshotTransportData(input, 'PUBLIC_SOURCE_INPUT_INVALID')
  assertExactKeys(snapshot, PUBLIC_SOURCE_INPUT_KEYS, 'PUBLIC_SOURCE_INPUT_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot, [...PUBLIC_SOURCE_INPUT_KEYS], 'PUBLIC_SOURCE_INPUT_FIELD_REQUIRED')
  const { workspaceRoot, runId, actorId, sourceDigest } = snapshot
  const marker = await requireWritableWorkspace(workspaceRoot)
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  invariant(RUN_ID_PATTERN.test(runId), 'RUN_ID_INVALID')
  invariant(typeof sourceDigest === 'string' && HEX_64.test(sourceDigest), 'PUBLIC_SOURCE_DIGEST_INVALID')
  const scope = { workspaceIdHash: workspaceScopeHash(marker), runIdHash: sha256(runId), sourceDigest }
  const sourceRef = `src_${sha256(scope).slice(0, 32)}`
  const record = validatePublicSourceRecord({
    schema: PUBLIC_SOURCE_RECORD_SCHEMA,
    sourceRef,
    ...scope,
    recordedBy: WRITER_ID,
    recordedAt: new Date().toISOString(),
    release: { packageId: PACKAGE_ID, productVersion: WORKSPACE_PRODUCT_VERSION },
    evidenceBoundary: PUBLIC_SOURCE_EVIDENCE_BOUNDARY,
  })
  const paths = workspacePaths(workspaceRoot, runId)
  const target = publicSourceTarget(paths, sourceRef)
  await rejectExistingLinkSegments(paths.root, paths.evidenceSources, 'PUBLIC_SOURCE_DIRECTORY_LINK_FORBIDDEN')
  await mkdir(paths.evidenceSources, { recursive: true })
  await rejectExistingLinkSegments(paths.root, target, 'PUBLIC_SOURCE_LINK_FORBIDDEN')
  const created = await publishExclusiveJson(target, record)
  if (!created) {
    const existing = await readPublicSourceRecord(paths, sourceRef)
    const comparable = ({ recordedAt, ...value }) => value
    invariant(sha256(comparable(existing.record)) === sha256(comparable(record)), 'PUBLIC_SOURCE_RECORD_CONFLICT')
    return { sourceRef, sourcePayloadHash: sha256(existing.record), idempotent: true, evidenceBoundary: PUBLIC_SOURCE_EVIDENCE_BOUNDARY }
  }
  return { sourceRef, sourcePayloadHash: sha256(record), idempotent: false, evidenceBoundary: PUBLIC_SOURCE_EVIDENCE_BOUNDARY }
}

function artifactClaimMarkers(content) {
  const labels = new Map([
    ['【关键事实（未核验，按假设处理）】', { requestedClassification: 'fact', visibleClassification: 'assumption', critical: true }],
    ['【事实（未核验，按假设处理）】', { requestedClassification: 'fact', visibleClassification: 'assumption', critical: false }],
    ['【关键事实（证据冲突，按未知处理）】', { requestedClassification: 'fact', visibleClassification: 'unknown', critical: true }],
    ['【事实（证据冲突，按未知处理）】', { requestedClassification: 'fact', visibleClassification: 'unknown', critical: false }],
    ['【关键事实（证据缺失，按未知处理）】', { requestedClassification: 'fact', visibleClassification: 'unknown', critical: true }],
    ['【事实（证据缺失，按未知处理）】', { requestedClassification: 'fact', visibleClassification: 'unknown', critical: false }],
    ['【关键事实】', { requestedClassification: 'fact', visibleClassification: 'fact', critical: true }],
    ['【事实】', { requestedClassification: 'fact', visibleClassification: 'fact', critical: false }],
    ['【估计】', { requestedClassification: 'estimate', visibleClassification: 'estimate', critical: false }],
    ['【假设】', { requestedClassification: 'assumption', visibleClassification: 'assumption', critical: false }],
    ['【判断】', { requestedClassification: 'judgement', visibleClassification: 'judgement', critical: false }],
    ['【未知】', { requestedClassification: 'unknown', visibleClassification: 'unknown', critical: false }],
  ])
  const markers = []
  let inHtmlComment = false
  for (const rawLine of deliveryContractLinesOutsideFences(content.replaceAll('\r\n', '\n').replaceAll('\r', '\n').split('\n'))) {
    let line = rawLine
    let visible = ''
    while (line.length > 0) {
      if (inHtmlComment) {
        const close = line.indexOf('-->')
        if (close === -1) { line = ''; break }
        line = line.slice(close + 3)
        inHtmlComment = false
        continue
      }
      const open = line.indexOf('<!--')
      if (open === -1) { visible += line; line = ''; break }
      visible += line.slice(0, open)
      line = line.slice(open + 4)
      inHtmlComment = true
    }
    line = visible.trimStart()
    const match = [...labels.entries()].find(([label]) => line.startsWith(label))
    if (!match) continue
    const [label, classification] = match
    const statement = line.slice(label.length).trim()
    invariant(statement.length >= 1 && statement.length <= 2000, 'CLAIM_STATEMENT_INVALID')
    markers.push({ ordinal: markers.length + 1, statement, ...classification })
  }
  invariant(inHtmlComment === false, 'CLAIM_HTML_COMMENT_UNCLOSED')
  return markers
}

async function resolveClaimEvidenceRef(paths, workspaceIdHash, runId, ref, materialRecord) {
  if (typeof ref === 'string' && MATERIAL_REF_PATTERN.test(ref)) {
    const item = materialRecord?.materialCard.received.find((candidate) => candidate.materialRef === ref)
    invariant(item, 'CLAIM_EVIDENCE_REF_UNKNOWN')
    return { ref, kind: 'user_material', status: item.status }
  }
  if (typeof ref === 'string' && HOST_RECEIPT_REF_PATTERN.test(ref)) {
    const { record } = await readHostReceiptRecord(paths, ref)
    invariant(record.workspaceIdHash === workspaceIdHash && record.runIdHash === sha256(runId), 'CLAIM_EVIDENCE_REF_SCOPE_MISMATCH')
    return { ref, kind: 'host_receipt_observation', status: 'registered_observation' }
  }
  if (typeof ref === 'string' && /^src_[0-9a-f]{32}$/.test(ref)) {
    const { record } = await readPublicSourceRecord(paths, ref)
    invariant(record.workspaceIdHash === workspaceIdHash && record.runIdHash === sha256(runId), 'CLAIM_EVIDENCE_REF_SCOPE_MISMATCH')
    return { ref, kind: 'public_source_observation', status: 'registered_unverified' }
  }
  throw new BoardContractError('CLAIM_EVIDENCE_REF_UNKNOWN', 'Evidence reference is not registered in this workspace')
}

function classifyClaimEvidence(requestedClassification, resolvedRefs) {
  const hasConflict = resolvedRefs.some((item) => item.status === 'received_conflicted')
  const hasUnverified = resolvedRefs.some((item) => ['received_unverified', 'registered_unverified'].includes(item.status))
  const onlyHostObservations = resolvedRefs.length > 0 && resolvedRefs.every((item) => item.kind === 'host_receipt_observation')
  const evidenceStatus = resolvedRefs.length === 0
    ? 'missing'
    : hasConflict
      ? 'conflicted'
      : hasUnverified
        ? 'unverified'
        : onlyHostObservations
          ? 'registered_host_observation'
          : 'unsupported'
  let classification = requestedClassification
  let downgradeReason = null
  if (classification === 'fact') {
    if (resolvedRefs.length === 0) { classification = 'unknown'; downgradeReason = 'evidence_required' }
    else if (hasConflict) { classification = 'unknown'; downgradeReason = 'evidence_conflicted' }
    else if (hasUnverified) { classification = 'assumption'; downgradeReason = 'evidence_unverified' }
    else if (onlyHostObservations) { classification = 'assumption'; downgradeReason = 'host_receipt_authenticity_unverified' }
    else { classification = 'assumption'; downgradeReason = 'evidence_scope_unsupported' }
  }
  return { classification, evidenceStatus, downgradeReason }
}

export async function recordClaimEvidenceIndex(input) {
  const snapshot = snapshotTransportData(input, 'CLAIM_EVIDENCE_INPUT_INVALID')
  assertExactKeys(snapshot, CLAIM_RECORD_INPUT_KEYS, 'CLAIM_EVIDENCE_INPUT_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot, [...CLAIM_RECORD_INPUT_KEYS], 'CLAIM_EVIDENCE_INPUT_FIELD_REQUIRED')
  const { workspaceRoot, runId, actorId, artifactPath, draft } = snapshot
  const workspaceMarker = await requireWritableWorkspace(workspaceRoot)
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  invariant(RUN_ID_PATTERN.test(runId), 'RUN_ID_INVALID')
  invariant(isObject(draft), 'CLAIM_EVIDENCE_DRAFT_REQUIRED')
  assertExactKeys(draft, CLAIM_EVIDENCE_DRAFT_KEYS, 'CLAIM_EVIDENCE_FIELD_FORBIDDEN')
  assertRequiredKeys(draft, [...CLAIM_EVIDENCE_DRAFT_KEYS], 'CLAIM_EVIDENCE_FIELD_REQUIRED')
  invariant(draft.schema === 'fbsir.claim-evidence-draft/v1', 'CLAIM_EVIDENCE_SCHEMA_INVALID')
  invariant(draft.contentStoredInEventLedger === false, 'CLAIM_EVENT_LEDGER_CONTENT_FORBIDDEN')
  assertDenseDataArray(draft.claims, 128, 'CLAIM_LIST_INVALID', 'CLAIM_COUNT_INVALID')
  invariant(draft.claims.length >= 1, 'CLAIM_COUNT_INVALID')

  const paths = workspacePaths(workspaceRoot, runId)
  const resolvedArtifact = path.resolve(artifactPath)
  ensureWithin(paths.deliverables, resolvedArtifact)
  await rejectExistingLinkSegments(paths.root, resolvedArtifact, 'CLAIM_ARTIFACT_LINK_FORBIDDEN')
  await requireRegularFileNoLink(resolvedArtifact, 'CLAIM_ARTIFACT_FILE_INVALID')
  const content = await readFile(resolvedArtifact, 'utf8')
  const artifactSha256 = sha256(content)
  const markers = artifactClaimMarkers(content)
  invariant(markers.length >= 1 && markers.length <= 128, 'CLAIM_MARKER_COUNT_INVALID')
  invariant(draft.claims.length === markers.length, 'CLAIM_MARKER_COVERAGE_INVALID')
  let materialRecord = null
  try { materialRecord = await readWorkspaceMaterialRecord(paths) }
  catch (error) { if (error?.code !== 'WORKSPACE_MATERIAL_RECORD_UNAVAILABLE') throw error }
  if (materialRecord) invariant(
    materialRecord.workspaceIdHash === workspaceScopeHash(workspaceMarker) && materialRecord.runIdHash === sha256(runId),
    'CLAIM_EVIDENCE_REF_SCOPE_MISMATCH',
  )

  const claims = []
  const digests = new Set()
  const ordinals = new Set()
  for (const rawClaim of draft.claims) {
    invariant(isObject(rawClaim), 'CLAIM_INVALID')
    assertExactKeys(rawClaim, CLAIM_DRAFT_KEYS, 'CLAIM_FIELD_FORBIDDEN')
    assertRequiredKeys(rawClaim, [...CLAIM_DRAFT_KEYS], 'CLAIM_FIELD_REQUIRED')
    invariant(Number.isInteger(rawClaim.ordinal) && rawClaim.ordinal >= 1 && rawClaim.ordinal <= markers.length, 'CLAIM_ORDINAL_INVALID')
    invariant(!ordinals.has(rawClaim.ordinal), 'CLAIM_ORDINAL_DUPLICATE')
    invariant(rawClaim.ordinal === claims.length + 1, 'CLAIM_ORDINAL_ORDER_INVALID')
    ordinals.add(rawClaim.ordinal)
    const claimMarker = markers[rawClaim.ordinal - 1]
    assertDenseDataArray(rawClaim.evidenceRefs, 16, 'CLAIM_EVIDENCE_REFS_INVALID', 'CLAIM_EVIDENCE_REF_COUNT_INVALID')
    invariant(rawClaim.evidenceRefs.every((ref) => typeof ref === 'string'), 'CLAIM_EVIDENCE_REF_INVALID')
    invariant(new Set(rawClaim.evidenceRefs).size === rawClaim.evidenceRefs.length, 'CLAIM_EVIDENCE_REF_DUPLICATE')
    const resolvedRefs = []
    for (const ref of rawClaim.evidenceRefs) resolvedRefs.push(await resolveClaimEvidenceRef(paths, workspaceScopeHash(workspaceMarker), runId, ref, materialRecord))
    const statementDigest = sha256(claimMarker.statement)
    invariant(!digests.has(statementDigest), 'CLAIM_DIGEST_DUPLICATE')
    digests.add(statementDigest)

    const { classification, evidenceStatus, downgradeReason } = classifyClaimEvidence(claimMarker.requestedClassification, resolvedRefs)
    invariant(classification === claimMarker.visibleClassification, 'CLAIM_VISIBLE_CLASSIFICATION_REWRITE_REQUIRED', 'Visible claim marker must show the effective downgraded classification')
    const claimId = `claim_${sha256({ workspaceIdHash: workspaceScopeHash(workspaceMarker), runIdHash: sha256(runId), artifactSha256, statementDigest }).slice(0, 32)}`
    claims.push({
      ordinal: claimMarker.ordinal,
      claimId,
      statementDigest,
      critical: claimMarker.critical,
      requestedClassification: claimMarker.requestedClassification,
      classification,
      evidenceRefs: [...rawClaim.evidenceRefs],
      evidenceStatus,
      downgradeReason,
    })
  }
  const summary = Object.fromEntries([...CLAIM_CLASSIFICATIONS].map((classification) => [classification, claims.filter((item) => item.classification === classification).length]))
  summary.downgraded = claims.filter((item) => item.downgradeReason !== null).length
  const index = {
    schema: CLAIM_EVIDENCE_SCHEMA,
    workspaceIdHash: workspaceScopeHash(workspaceMarker),
    runIdHash: sha256(runId),
    artifactSha256,
    claims,
    summary,
    contentStoredInEventLedger: false,
    release: { packageId: PACKAGE_ID, productVersion: WORKSPACE_PRODUCT_VERSION },
    evidenceBoundary: CLAIM_EVIDENCE_EVIDENCE_BOUNDARY,
  }
  invariant(index.claims.filter((item) => item.classification === 'fact').every((item) => item.evidenceRefs.length > 0), 'CLAIM_FACT_EVIDENCE_REQUIRED')
  const claimIndexRef = `claimidx_${sha256({ workspaceIdHash: index.workspaceIdHash, runIdHash: index.runIdHash, artifactSha256 }).slice(0, 32)}`
  const target = path.join(paths.claimIndexes, `${claimIndexRef}.json`)
  ensureWithin(paths.root, target)
  await rejectExistingLinkSegments(paths.root, paths.claimIndexes, 'CLAIM_INDEX_DIRECTORY_LINK_FORBIDDEN')
  await mkdir(paths.claimIndexes, { recursive: true })
  await rejectExistingLinkSegments(paths.root, target, 'CLAIM_INDEX_LINK_FORBIDDEN')
  const created = await publishExclusiveJson(target, index)
  if (!created) {
    let existing
    try { existing = JSON.parse(await readFile(target, 'utf8')) }
    catch { throw new BoardContractError('CLAIM_INDEX_INVALID', 'Claim index is invalid') }
    invariant(sha256(existing) === sha256(index), 'CLAIM_INDEX_CONFLICT')
  }
  return { ...index, claimIndexRef, claimIndexPayloadHash: sha256(index), idempotent: !created }
}

async function requireClaimEvidenceIndex(paths, workspaceMarker, runId, artifactSha256, content) {
  const workspaceIdHash = workspaceScopeHash(workspaceMarker)
  const runIdHash = sha256(runId)
  const claimIndexRef = `claimidx_${sha256({ workspaceIdHash, runIdHash, artifactSha256 }).slice(0, 32)}`
  const target = path.join(paths.claimIndexes, `${claimIndexRef}.json`)
  ensureWithin(paths.root, target)
  await rejectExistingLinkSegments(paths.root, target, 'CLAIM_INDEX_LINK_FORBIDDEN')
  await requireRegularFileNoLink(target, 'DELIVERY_CLAIM_INDEX_REQUIRED')
  let index
  try { index = JSON.parse(await readFile(target, 'utf8')) }
  catch { throw new BoardContractError('CLAIM_INDEX_INVALID', 'Claim index is invalid') }
  invariant(isObject(index), 'CLAIM_INDEX_INVALID')
  assertExactKeys(index, CLAIM_INDEX_KEYS, 'CLAIM_INDEX_FIELD_FORBIDDEN')
  assertRequiredKeys(index, [...CLAIM_INDEX_KEYS], 'CLAIM_INDEX_FIELD_REQUIRED')
  invariant(index.schema === CLAIM_EVIDENCE_SCHEMA, 'CLAIM_INDEX_SCHEMA_INVALID')
  invariant(index.workspaceIdHash === workspaceIdHash && index.runIdHash === runIdHash && index.artifactSha256 === artifactSha256, 'CLAIM_INDEX_SCOPE_MISMATCH')
  invariant(index.contentStoredInEventLedger === false, 'CLAIM_EVENT_LEDGER_CONTENT_FORBIDDEN')
  assertExactKeys(index.release, new Set(['packageId', 'productVersion']), 'CLAIM_INDEX_RELEASE_FIELD_FORBIDDEN')
  invariant(index.release.packageId === PACKAGE_ID && index.release.productVersion === WORKSPACE_PRODUCT_VERSION, 'CLAIM_INDEX_RELEASE_INVALID')
  invariant(index.evidenceBoundary === CLAIM_EVIDENCE_EVIDENCE_BOUNDARY, 'CLAIM_INDEX_EVIDENCE_BOUNDARY_INVALID')
  const markers = artifactClaimMarkers(content)
  assertDenseDataArray(index.claims, 128, 'CLAIM_INDEX_CLAIMS_INVALID', 'CLAIM_INDEX_CLAIM_COUNT_INVALID')
  invariant(index.claims.length === markers.length && markers.length >= 1, 'CLAIM_MARKER_COVERAGE_INVALID')
  let materialRecord = null
  try { materialRecord = await readWorkspaceMaterialRecord(paths) }
  catch (error) { if (error?.code !== 'WORKSPACE_MATERIAL_RECORD_UNAVAILABLE') throw error }
  if (materialRecord) invariant(materialRecord.workspaceIdHash === workspaceIdHash && materialRecord.runIdHash === runIdHash, 'CLAIM_EVIDENCE_REF_SCOPE_MISMATCH')
  for (let offset = 0; offset < index.claims.length; offset += 1) {
    const claim = index.claims[offset]
    const marker = markers[offset]
    invariant(isObject(claim), 'CLAIM_INDEX_CLAIM_INVALID')
    assertExactKeys(claim, CLAIM_INDEX_CLAIM_KEYS, 'CLAIM_INDEX_CLAIM_FIELD_FORBIDDEN')
    assertRequiredKeys(claim, [...CLAIM_INDEX_CLAIM_KEYS], 'CLAIM_INDEX_CLAIM_FIELD_REQUIRED')
    invariant(claim.ordinal === offset + 1, 'CLAIM_INDEX_ORDINAL_INVALID')
    const statementDigest = sha256(marker.statement)
    const claimId = `claim_${sha256({ workspaceIdHash, runIdHash, artifactSha256, statementDigest }).slice(0, 32)}`
    invariant(claim.claimId === claimId && claim.statementDigest === statementDigest, 'CLAIM_INDEX_STATEMENT_BINDING_INVALID')
    invariant(claim.critical === marker.critical && claim.requestedClassification === marker.requestedClassification, 'CLAIM_INDEX_CLASSIFICATION_BINDING_INVALID')
    assertDenseDataArray(claim.evidenceRefs, 16, 'CLAIM_EVIDENCE_REFS_INVALID', 'CLAIM_EVIDENCE_REF_COUNT_INVALID')
    invariant(new Set(claim.evidenceRefs).size === claim.evidenceRefs.length, 'CLAIM_EVIDENCE_REF_DUPLICATE')
    const resolvedRefs = []
    for (const ref of claim.evidenceRefs) resolvedRefs.push(await resolveClaimEvidenceRef(paths, workspaceIdHash, runId, ref, materialRecord))
    const expected = classifyClaimEvidence(marker.requestedClassification, resolvedRefs)
    invariant(expected.classification === marker.visibleClassification, 'CLAIM_VISIBLE_CLASSIFICATION_REWRITE_REQUIRED')
    invariant(
      claim.classification === expected.classification
        && claim.evidenceStatus === expected.evidenceStatus
        && claim.downgradeReason === expected.downgradeReason,
      'CLAIM_INDEX_CLASSIFICATION_INVALID',
    )
  }
  const expectedSummary = Object.fromEntries([...CLAIM_CLASSIFICATIONS].map((classification) => [classification, index.claims.filter((item) => item.classification === classification).length]))
  expectedSummary.downgraded = index.claims.filter((item) => item.downgradeReason !== null).length
  invariant(sha256(index.summary) === sha256(expectedSummary), 'CLAIM_INDEX_SUMMARY_INVALID')
  invariant(index.claims.every((item) => item.classification !== 'fact'), 'CLAIM_INDEX_UNVERIFIED_FACT_FORBIDDEN')
  return {
    claimIndexRef,
    claimIndexPayloadHash: sha256(index),
    claimCount: index.claims.length,
    summary: expectedSummary,
    coverageScope: 'declared_markers_only',
    unmarkedClaimCompletenessProven: false,
    factTruthProven: false,
    evidenceBoundary: CLAIM_EVIDENCE_EVIDENCE_BOUNDARY,
  }
}

export async function verifyClaimEvidenceIndex(input) {
  const snapshot = snapshotTransportData(input, 'CLAIM_VERIFY_INPUT_INVALID')
  assertExactKeys(snapshot, CLAIM_VERIFY_INPUT_KEYS, 'CLAIM_VERIFY_INPUT_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot, [...CLAIM_VERIFY_INPUT_KEYS], 'CLAIM_VERIFY_INPUT_FIELD_REQUIRED')
  const { workspaceRoot, runId, artifactPath } = snapshot
  const workspaceMarker = await readWorkspace(workspaceRoot)
  invariant(RUN_ID_PATTERN.test(runId), 'RUN_ID_INVALID')
  const paths = workspacePaths(workspaceRoot, runId)
  const resolvedArtifact = path.resolve(artifactPath)
  ensureWithin(paths.deliverables, resolvedArtifact)
  await rejectExistingLinkSegments(paths.root, resolvedArtifact, 'CLAIM_ARTIFACT_LINK_FORBIDDEN')
  await requireRegularFileNoLink(resolvedArtifact, 'CLAIM_ARTIFACT_FILE_INVALID')
  const content = await readFile(resolvedArtifact, 'utf8')
  return requireClaimEvidenceIndex(paths, workspaceMarker, runId, sha256(content), content)
}

function decisionText(value, maximumLength, code) {
  invariant(typeof value === 'string', code)
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index)
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(index + 1)
      invariant(next >= 0xdc00 && next <= 0xdfff, code, 'Decision text must contain well-formed Unicode')
      index += 1
    } else {
      invariant(!(unit >= 0xdc00 && unit <= 0xdfff), code, 'Decision text must contain well-formed Unicode')
    }
  }
  invariant(value.normalize('NFC') === value, code, 'Decision text must use Unicode NFC')
  invariant(value.trim() === value, code, 'Decision text must not have leading or trailing whitespace')
  invariant(!/[\u0000-\u0008\u000B-\u001F\u007F-\u009F]/u.test(value), code, 'Decision text contains forbidden control characters')
  invariant(!/[\u061C\u200E\u200F\u202A-\u202E\u2066-\u2069]/u.test(value), code, 'Decision text contains forbidden bidirectional controls')
  const visible = value.replace(/[\p{White_Space}\p{Default_Ignorable_Code_Point}]/gu, '')
  const length = Array.from(value).length
  invariant(visible.length > 0 && length <= maximumLength, code)
  return value
}

function canonicalDecisionTime(value, code) {
  if (value === null) return null
  invariant(typeof value === 'string' && CANONICAL_UTC_TIMESTAMP_PATTERN.test(value), code)
  const timestamp = Date.parse(value)
  invariant(Number.isFinite(timestamp) && new Date(timestamp).toISOString() === value, code)
  return value
}

function decisionTypedId(value, pattern, code) {
  invariant(typeof value === 'string' && pattern.test(value), code)
  return value
}

function assertUniqueDecisionIds(values, key, code) {
  invariant(new Set(values.map((value) => value[key])).size === values.length, code)
}

export function validateDecisionRecord(input) {
  const snapshot = snapshotTransportData(input, 'DECISION_RECORD_INVALID')
  assertExactKeys(snapshot, DECISION_RECORD_KEYS, 'DECISION_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot, DECISION_RECORD_KEY_LIST, 'DECISION_FIELD_REQUIRED')
  invariant(snapshot.schema === DECISION_RECORD_SCHEMA, 'DECISION_SCHEMA_INVALID')
  invariant(typeof snapshot.runId === 'string' && RUN_ID_PATTERN.test(snapshot.runId), 'DECISION_RUN_ID_INVALID')
  invariant(Number.isSafeInteger(snapshot.revision) && snapshot.revision >= 1, 'DECISION_REVISION_INVALID')
  invariant(snapshot.decisionOwner === 'user', 'DECISION_OWNER_INVALID')
  if (snapshot.status === 'user_confirmed') {
    throw new BoardContractError('DECISION_EXTERNAL_CONFIRMATION_REQUIRED', 'Generic package-local validation cannot promote a pending decision to user_confirmed')
  }
  invariant(snapshot.status === 'confirmation_pending', 'DECISION_STATUS_INVALID')
  invariant(snapshot.confirmation === null, 'DECISION_CONFIRMATION_FORBIDDEN')
  invariant(snapshot.recordedBy === null && snapshot.recordedAt === null, 'DECISION_RECORDING_STATE_FORBIDDEN')

  invariant(typeof snapshot.workspaceScopeHash === 'string' && HEX_64.test(snapshot.workspaceScopeHash), 'DECISION_WORKSPACE_SCOPE_HASH_INVALID')
  assertExactKeys(snapshot.sourceArtifact, DECISION_SOURCE_ARTIFACT_KEYS, 'DECISION_SOURCE_ARTIFACT_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot.sourceArtifact, DECISION_SOURCE_ARTIFACT_KEY_LIST, 'DECISION_SOURCE_ARTIFACT_FIELD_REQUIRED')
  invariant(DECISION_ARTIFACT_TYPES.has(snapshot.sourceArtifact.artifactType), 'DECISION_SOURCE_ARTIFACT_TYPE_INVALID')
  invariant(typeof snapshot.sourceArtifact.artifactDigest === 'string' && HEX_64.test(snapshot.sourceArtifact.artifactDigest), 'DECISION_SOURCE_ARTIFACT_DIGEST_INVALID')
  invariant(typeof snapshot.sourceArtifact.presentationEventHash === 'string' && HEX_64.test(snapshot.sourceArtifact.presentationEventHash), 'DECISION_PRESENTATION_EVENT_HASH_INVALID')

  assertExactKeys(snapshot.decision, DECISION_BODY_KEYS, 'DECISION_BODY_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot.decision, DECISION_BODY_KEY_LIST, 'DECISION_BODY_FIELD_REQUIRED')
  invariant(DECISION_CODES.has(snapshot.decision.decisionCode), 'DECISION_CODE_INVALID')
  decisionText(snapshot.decision.statement, 8000, 'DECISION_STATEMENT_INVALID')

  assertDenseDataArray(snapshot.decision.declinedOptions, 20, 'DECISION_DECLINED_OPTIONS_INVALID', 'DECISION_DECLINED_OPTIONS_COUNT_INVALID')
  for (const option of snapshot.decision.declinedOptions) decisionText(option, 1000, 'DECISION_DECLINED_OPTION_INVALID')
  invariant(new Set(snapshot.decision.declinedOptions).size === snapshot.decision.declinedOptions.length, 'DECISION_DECLINED_OPTION_DUPLICATE')

  assertDenseDataArray(snapshot.decision.triggers, 20, 'DECISION_TRIGGERS_INVALID', 'DECISION_TRIGGERS_COUNT_INVALID')
  for (const trigger of snapshot.decision.triggers) {
    assertExactKeys(trigger, DECISION_TRIGGER_KEYS, 'DECISION_TRIGGER_FIELD_FORBIDDEN')
    assertRequiredKeys(trigger, DECISION_TRIGGER_KEY_LIST, 'DECISION_TRIGGER_FIELD_REQUIRED')
    decisionTypedId(trigger.triggerId, DECISION_TRIGGER_ID_PATTERN, 'DECISION_TRIGGER_ID_INVALID')
    decisionText(trigger.condition, 1000, 'DECISION_TRIGGER_CONDITION_INVALID')
    decisionText(trigger.response, 1000, 'DECISION_TRIGGER_RESPONSE_INVALID')
  }
  assertUniqueDecisionIds(snapshot.decision.triggers, 'triggerId', 'DECISION_TRIGGER_ID_DUPLICATE')
  const triggerIds = new Set(snapshot.decision.triggers.map((trigger) => trigger.triggerId))

  assertDenseDataArray(snapshot.decision.leadingIndicators, 20, 'DECISION_INDICATORS_INVALID', 'DECISION_INDICATORS_COUNT_INVALID')
  for (const indicator of snapshot.decision.leadingIndicators) {
    assertExactKeys(indicator, DECISION_INDICATOR_KEYS, 'DECISION_INDICATOR_FIELD_FORBIDDEN')
    assertRequiredKeys(indicator, DECISION_INDICATOR_KEY_LIST, 'DECISION_INDICATOR_FIELD_REQUIRED')
    decisionTypedId(indicator.indicatorId, DECISION_INDICATOR_ID_PATTERN, 'DECISION_INDICATOR_ID_INVALID')
    decisionText(indicator.metric, 500, 'DECISION_INDICATOR_METRIC_INVALID')
    decisionText(indicator.target, 500, 'DECISION_INDICATOR_TARGET_INVALID')
    if (indicator.reviewTriggerId !== null) {
      decisionTypedId(indicator.reviewTriggerId, DECISION_TRIGGER_ID_PATTERN, 'DECISION_INDICATOR_TRIGGER_ID_INVALID')
      invariant(triggerIds.has(indicator.reviewTriggerId), 'DECISION_INDICATOR_TRIGGER_UNKNOWN')
    }
  }
  assertUniqueDecisionIds(snapshot.decision.leadingIndicators, 'indicatorId', 'DECISION_INDICATOR_ID_DUPLICATE')

  assertDenseDataArray(snapshot.decision.actionItems, 50, 'DECISION_ACTION_ITEMS_INVALID', 'DECISION_ACTION_ITEMS_COUNT_INVALID')
  for (const actionItem of snapshot.decision.actionItems) {
    assertExactKeys(actionItem, DECISION_ACTION_ITEM_KEYS, 'DECISION_ACTION_ITEM_FIELD_FORBIDDEN')
    assertRequiredKeys(actionItem, DECISION_ACTION_ITEM_KEY_LIST, 'DECISION_ACTION_ITEM_FIELD_REQUIRED')
    decisionTypedId(actionItem.actionItemId, DECISION_ACTION_ITEM_ID_PATTERN, 'DECISION_ACTION_ITEM_ID_INVALID')
    if (actionItem.ownerRef !== null) decisionTypedId(actionItem.ownerRef, DECISION_OWNER_REF_PATTERN, 'DECISION_ACTION_OWNER_REF_INVALID')
    canonicalDecisionTime(actionItem.dueAt, 'DECISION_ACTION_DUE_AT_INVALID')
    invariant(DECISION_ACTION_STATUSES.has(actionItem.status), 'DECISION_ACTION_STATUS_INVALID')
  }
  assertUniqueDecisionIds(snapshot.decision.actionItems, 'actionItemId', 'DECISION_ACTION_ITEM_ID_DUPLICATE')
  canonicalDecisionTime(snapshot.decision.reviewAt, 'DECISION_REVIEW_AT_INVALID')

  assertExactKeys(snapshot.release, DECISION_RELEASE_KEYS, 'DECISION_RELEASE_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot.release, DECISION_RELEASE_KEY_LIST, 'DECISION_RELEASE_FIELD_REQUIRED')
  invariant(snapshot.release.packageId === PACKAGE_ID && snapshot.release.productVersion === WORKSPACE_PRODUCT_VERSION, 'DECISION_RELEASE_INVALID')
  assertExactKeys(snapshot.privacy, DECISION_PRIVACY_KEYS, 'DECISION_PRIVACY_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot.privacy, DECISION_PRIVACY_KEY_LIST, 'DECISION_PRIVACY_FIELD_REQUIRED')
  invariant(
    snapshot.privacy.class === 'decision_record'
      && snapshot.privacy.contentStored === true
      && snapshot.privacy.telemetryExport === false
      && snapshot.privacy.schemaVersion === 'v1',
    'DECISION_PRIVACY_INVALID',
  )
  invariant(snapshot.evidenceBoundary === DECISION_RECORD_EVIDENCE_BOUNDARY, 'DECISION_EVIDENCE_BOUNDARY_INVALID')

  const expectedDigest = sha256({
    workspaceScopeHash: snapshot.workspaceScopeHash,
    runIdHash: sha256(snapshot.runId),
    revision: snapshot.revision,
    sourceArtifact: snapshot.sourceArtifact,
    decision: snapshot.decision,
  })
  invariant(snapshot.decisionDigest === expectedDigest, 'DECISION_DIGEST_MISMATCH')
  invariant(typeof snapshot.decisionRecordId === 'string' && DECISION_RECORD_ID_PATTERN.test(snapshot.decisionRecordId), 'DECISION_RECORD_ID_INVALID')
  invariant(snapshot.decisionRecordId === `decision_${expectedDigest.slice(0, 32)}`, 'DECISION_RECORD_ID_MISMATCH')
  return snapshot
}

function actionDigest(value) {
  invariant(typeof value === 'string' && HEX_64.test(value), 'ACTION_DIGEST_INVALID')
  return value
}

function actionReviewMode(value) {
  invariant(REVIEW_MODES.has(value), 'ACTION_REVIEW_MODE_INVALID')
  return value
}

function actionRunId(value) {
  invariant(typeof value === 'string' && RUN_ID_PATTERN.test(value), 'ACTION_RUN_ID_INVALID')
  return value
}

function validateHostActionArguments(actionId, input) {
  const contract = HOST_ACTION_CATALOG[actionId]
  const argumentKeys = contract.argumentKeys
  assertExactKeys(input, new Set(argumentKeys), 'ACTION_ARGUMENT_FIELD_FORBIDDEN')
  assertRequiredKeys(input, argumentKeys, 'ACTION_ARGUMENT_REQUIRED')

  if (actionId === 'confirm_review') {
    return {
      reviewMode: actionReviewMode(input.reviewMode),
      decisionCardHash: actionDigest(input.decisionCardHash),
    }
  }
  if (actionId === 'add_facts') {
    return {
      decisionCardHash: actionDigest(input.decisionCardHash),
      factUpdateDigest: actionDigest(input.factUpdateDigest),
    }
  }
  if (actionId === 'change_mode') {
    const fromReviewMode = actionReviewMode(input.fromReviewMode)
    const toReviewMode = actionReviewMode(input.toReviewMode)
    invariant(fromReviewMode !== toReviewMode, 'ACTION_MODE_CHANGE_REQUIRED')
    return {
      decisionCardHash: actionDigest(input.decisionCardHash),
      fromReviewMode,
      toReviewMode,
    }
  }
  if (actionId === 'resume_case') {
    invariant(RESUME_SOURCES.has(input.resumeSource), 'ACTION_RESUME_SOURCE_INVALID')
    const normalized = {
      resumeSource: input.resumeSource,
      sourceRunIdHash: actionDigest(input.sourceRunIdHash),
      resumeReceiptDigest: actionDigest(input.resumeReceiptDigest),
      targetRunId: actionRunId(input.targetRunId),
    }
    if (normalized.resumeSource === 'current_checkpoint') {
      invariant(sha256(normalized.targetRunId) === normalized.sourceRunIdHash, 'ACTION_CURRENT_RESUME_TARGET_MISMATCH', 'Current checkpoint resume must stay in the exact current run')
    } else {
      const conflictCode = normalized.resumeSource === 'legacy_read_only'
        ? 'ACTION_LEGACY_RESUME_TARGET_CONFLICT'
        : 'ACTION_PREDECESSOR_RESUME_TARGET_CONFLICT'
      invariant(sha256(normalized.targetRunId) !== normalized.sourceRunIdHash, conflictCode, 'Read-only resume must initialize a distinct current run')
    }
    return normalized
  }
  return {
    runId: actionRunId(input.runId),
    decisionDigest: actionDigest(input.decisionDigest),
  }
}

export function validateHostActionEnvelope(input) {
  assertExactKeys(input, HOST_ACTION_KEY_SET, 'ACTION_FIELD_FORBIDDEN')
  assertRequiredKeys(input, HOST_ACTION_KEYS, 'ACTION_FIELD_REQUIRED')
  invariant(input.schema === HOST_ACTION_SCHEMA, 'ACTION_SCHEMA_INVALID')
  invariant(typeof input.actionId === 'string' && Object.hasOwn(HOST_ACTION_CATALOG, input.actionId), 'ACTION_ID_INVALID')
  invariant(typeof input.actionInstanceId === 'string' && ACTION_INSTANCE_ID_PATTERN.test(input.actionInstanceId), 'ACTION_INSTANCE_ID_INVALID')
  assertExactKeys(input.product, HOST_ACTION_PRODUCT_KEY_SET, 'ACTION_PRODUCT_FIELD_FORBIDDEN')
  assertRequiredKeys(input.product, HOST_ACTION_PRODUCT_KEYS, 'ACTION_PRODUCT_REQUIRED')
  invariant(input.product.packageId === PACKAGE_ID && input.product.productVersion === PACKAGE_VERSION, 'ACTION_PRODUCT_INVALID')

  const contract = HOST_ACTION_CATALOG[input.actionId]
  const normalizedArguments = validateHostActionArguments(input.actionId, input.arguments)
  invariant(input.sideEffectClass === contract.sideEffectClass, 'ACTION_SIDE_EFFECT_INVALID')
  invariant(input.approvalState === contract.approvalState, 'ACTION_APPROVAL_STATE_INVALID')
  invariant(input.idempotent === true, 'ACTION_IDEMPOTENCY_REQUIRED')
  invariant(input.stopCondition === contract.stopCondition, 'ACTION_STOP_CONDITION_INVALID')
  invariant(input.doneState === contract.doneState, 'ACTION_DONE_STATE_INVALID')
  invariant(input.successorAction === contract.successorAction, 'ACTION_SUCCESSOR_INVALID')
  invariant(input.routeSignature === contract.routeSignature, 'ACTION_ROUTE_SIGNATURE_INVALID')
  invariant(input.evidenceBoundary === HOST_ACTION_EVIDENCE_BOUNDARY, 'ACTION_EVIDENCE_BOUNDARY_INVALID')

  return {
    schema: input.schema,
    actionId: input.actionId,
    actionInstanceId: input.actionInstanceId,
    product: { packageId: PACKAGE_ID, productVersion: PACKAGE_VERSION },
    arguments: normalizedArguments,
    sideEffectClass: input.sideEffectClass,
    approvalState: input.approvalState,
    idempotent: true,
    stopCondition: input.stopCondition,
    doneState: input.doneState,
    successorAction: input.successorAction,
    routeSignature: input.routeSignature,
    evidenceBoundary: input.evidenceBoundary,
  }
}

export function validateReviewPlan(input) {
  invariant(isObject(input), 'PLAN_ENVELOPE_REQUIRED')
  invariant(input.schema === PLAN_SCHEMA, 'PLAN_SCHEMA_INVALID')
  assertExactKeys(input, PLAN_KEYS, 'PLAN_FIELD_FORBIDDEN')
  assertRequiredKeys(input, PLAN_KEY_LIST, 'PLAN_FIELD_REQUIRED')
  safeId(input.runId, 'PLAN_RUN_ID_INVALID')
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'PLAN_REVISION_INVALID')
  const { reviewMode, specialistSeatIds, supportSeatIds } = normalizeSeatSelection(input, 'PLAN')
  invariant(Array.isArray(input.agendaItems) && input.agendaItems.length >= 1 && input.agendaItems.length <= 5, 'PLAN_AGENDA_COUNT_INVALID')
  const agendaItems = input.agendaItems.map((item) => {
    invariant(isObject(item), 'PLAN_AGENDA_ITEM_INVALID')
    assertExactKeys(item, AGENDA_ITEM_KEYS, 'PLAN_AGENDA_FIELD_FORBIDDEN')
    safeId(item.agendaItemId, 'PLAN_AGENDA_ID_INVALID')
    return { agendaItemId: item.agendaItemId, decisionQuestion: boundedText(item.decisionQuestion, 'plan_decision_question', 1000) }
  })
  invariant(new Set(agendaItems.map((item) => item.agendaItemId)).size === agendaItems.length, 'PLAN_AGENDA_ID_DUPLICATE')

  invariant(typeof input.decisionCardHash === 'string' && HEX_64.test(input.decisionCardHash), 'PLAN_DECISION_CARD_HASH_INVALID')
  invariant(input.userConfirmed === true, 'PLAN_USER_CONFIRMATION_REQUIRED')
  safeId(input.confirmationReceiptId, 'PLAN_CONFIRMATION_RECEIPT_INVALID')
  assertExactKeys(input.confirmationAction, PLAN_CONFIRMATION_ACTION_KEYS, 'PLAN_CONFIRMATION_ACTION_FIELD_FORBIDDEN')
  assertRequiredKeys(input.confirmationAction, PLAN_CONFIRMATION_ACTION_KEY_LIST, 'PLAN_CONFIRMATION_ACTION_FIELD_REQUIRED')
  invariant(input.confirmationAction.actionId === 'confirm_review', 'PLAN_CONFIRMATION_ACTION_ID_INVALID')
  invariant(typeof input.confirmationAction.actionInstanceId === 'string' && ACTION_INSTANCE_ID_PATTERN.test(input.confirmationAction.actionInstanceId), 'PLAN_CONFIRMATION_ACTION_INSTANCE_INVALID')
  invariant(typeof input.confirmationAction.actionEnvelopeDigest === 'string' && HEX_64.test(input.confirmationAction.actionEnvelopeDigest), 'PLAN_CONFIRMATION_ACTION_DIGEST_INVALID')
  const confirmationContract = HOST_ACTION_CATALOG.confirm_review
  const normalizedConfirmationEnvelope = validateHostActionEnvelope({
    schema: HOST_ACTION_SCHEMA,
    actionId: 'confirm_review',
    actionInstanceId: input.confirmationAction.actionInstanceId,
    product: { packageId: PACKAGE_ID, productVersion: PACKAGE_VERSION },
    arguments: { reviewMode, decisionCardHash: input.decisionCardHash },
    sideEffectClass: confirmationContract.sideEffectClass,
    approvalState: confirmationContract.approvalState,
    idempotent: true,
    stopCondition: confirmationContract.stopCondition,
    doneState: confirmationContract.doneState,
    successorAction: confirmationContract.successorAction,
    routeSignature: confirmationContract.routeSignature,
    evidenceBoundary: HOST_ACTION_EVIDENCE_BOUNDARY,
  })
  invariant(input.confirmationAction.actionEnvelopeDigest === sha256(normalizedConfirmationEnvelope), 'PLAN_CONFIRMATION_ACTION_DIGEST_MISMATCH', 'The plan must bind the exact canonical confirm_review envelope for its card and mode')
  const predecessorRunRef = normalizePredecessorRunRef(input.predecessorRunRef, input.runId)
  invariant(input.singleNextAction === 'request_team_create', 'PLAN_NEXT_ACTION_INVALID')

  return {
    schema: input.schema,
    runId: input.runId,
    revision: input.revision,
    reviewMode,
    agendaItems,
    specialistSeatIds,
    supportSeatIds,
    decisionCardHash: input.decisionCardHash,
    userConfirmed: true,
    confirmationReceiptId: input.confirmationReceiptId,
    confirmationAction: {
      actionId: 'confirm_review',
      actionInstanceId: input.confirmationAction.actionInstanceId,
      actionEnvelopeDigest: input.confirmationAction.actionEnvelopeDigest,
    },
    predecessorRunRef,
    singleNextAction: input.singleNextAction,
  }
}

function normalizePredecessorRunRef(input, runId) {
  if (input === null) return null
  invariant(isObject(input), 'PLAN_PREDECESSOR_INVALID')
  const legacy = input.schema === LEGACY_PREDECESSOR_RUN_REF_SCHEMA
  const keyList = legacy ? LEGACY_PREDECESSOR_RUN_REF_KEY_LIST : PREDECESSOR_RUN_REF_KEY_LIST
  const keys = legacy ? LEGACY_PREDECESSOR_RUN_REF_KEYS : PREDECESSOR_RUN_REF_KEYS
  assertExactKeys(input, keys, 'PLAN_PREDECESSOR_FIELD_FORBIDDEN')
  assertRequiredKeys(input, keyList, 'PLAN_PREDECESSOR_FIELD_REQUIRED')
  invariant(legacy || input.schema === PREDECESSOR_RUN_REF_SCHEMA, 'PLAN_PREDECESSOR_SCHEMA_INVALID')
  invariant(input.receiptRef === `.fbsir-board/predecessors/${runId}.json`, 'PREDECESSOR_RECEIPT_REF_INVALID')
  invariant(typeof input.receiptPayloadHash === 'string' && HEX_64.test(input.receiptPayloadHash), 'PREDECESSOR_RECEIPT_HASH_INVALID')
  invariant(typeof input.sourceRunIdHash === 'string' && HEX_64.test(input.sourceRunIdHash), 'PREDECESSOR_SOURCE_RUN_HASH_INVALID')
  invariant(input.sourceRunIdHash !== sha256(runId), 'PREDECESSOR_RUN_SCOPE_INVALID')
  if (legacy) {
    invariant(typeof input.legacyResumeDigest === 'string' && HEX_64.test(input.legacyResumeDigest), 'LEGACY_RESUME_DIGEST_INVALID')
  } else {
    invariant([LEGACY_RESUME_DIGEST_SCHEMA, PREDECESSOR_RESUME_DIGEST_SCHEMA].includes(input.resumeDigestSchema), 'PREDECESSOR_RESUME_DIGEST_SCHEMA_INVALID')
    invariant(typeof input.resumeDigest === 'string' && HEX_64.test(input.resumeDigest), 'PREDECESSOR_RESUME_DIGEST_INVALID')
  }
  return Object.fromEntries(keyList.map((key) => [key, input[key]]))
}

export function validateTaskEnvelope(input) {
  invariant(isObject(input), 'TASK_ENVELOPE_REQUIRED')
  assertExactKeys(input, TASK_KEYS, 'TASK_FIELD_FORBIDDEN')
  invariant(input.schema === TASK_SCHEMA, 'TASK_SCHEMA_INVALID')
  safeId(input.runId, 'TASK_RUN_ID_INVALID')
  safeId(input.agendaItemId, 'TASK_AGENDA_ID_INVALID')
  safeId(input.seatId, 'TASK_SEAT_ID_INVALID')
  invariant(['professional_review', 'process_support'].includes(input.taskClass), 'TASK_CLASS_INVALID')
  if (input.taskClass === 'professional_review') invariant(PROFESSIONAL_SEAT_IDS.has(input.seatId), 'TASK_PROFESSIONAL_SEAT_INVALID')
  else invariant(SUPPORT_SEAT_IDS.has(input.seatId), 'TASK_SUPPORT_SEAT_INVALID')
  invariant(['quick_review', 'standard_review', 'deep_review'].includes(input.reviewMode), 'TASK_REVIEW_MODE_INVALID')
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'TASK_REVISION_INVALID')
  boundedText(input.decisionQuestion, 'decision_question')
  invariant(Array.isArray(input.factSlices) && input.factSlices.length <= 20, 'TASK_FACT_SLICES_INVALID')
  input.factSlices.forEach((value) => boundedText(value, 'fact_slice', 1000))
  invariant(Array.isArray(input.evidenceRefs) && input.evidenceRefs.length <= 30, 'TASK_EVIDENCE_REFS_INVALID')
  input.evidenceRefs.forEach((value) => safeId(value, 'TASK_EVIDENCE_REF_INVALID'))
  requiredAssetBundleRef(input.evidenceRefs, 'TASK_ASSET_BUNDLE_REF_COUNT_INVALID')
  if (input.taskClass === 'process_support') {
    invariant(
      input.evidenceRefs.length === 1 && isCognitiveAssetBundleRef(input.evidenceRefs[0]),
      'TASK_EVIDENCE_REFS_EXACT',
      'Process-support tasks must contain exactly one verified asset bundle reference',
    )
  }
  invariant(input.firstRoundIsolation === true, 'TASK_FIRST_ROUND_ISOLATION_REQUIRED')
  invariant(input.returnTo === WRITER_ID, 'TASK_RETURN_TARGET_INVALID')
  const targets = memberArtifactTargets(input)
  invariant(input.resultTarget === targets.resultTarget, 'TASK_RESULT_TARGET_INVALID', 'Result target must be deterministic and bound to agenda, seat and revision', { expected: targets.resultTarget })
  invariant(input.deliveryObservationTarget === targets.deliveryObservationTarget, 'TASK_DELIVERY_TARGET_INVALID', 'Delivery-observation target must be deterministic and bound to agenda, seat and revision', { expected: targets.deliveryObservationTarget })
  return {
    schema: input.schema, runId: input.runId, agendaItemId: input.agendaItemId, seatId: input.seatId,
    taskClass: input.taskClass, reviewMode: input.reviewMode, revision: input.revision,
    decisionQuestion: input.decisionQuestion.trim(), factSlices: input.factSlices.map((value) => value.trim()),
    evidenceRefs: [...input.evidenceRefs], firstRoundIsolation: input.firstRoundIsolation, returnTo: input.returnTo,
    resultTarget: input.resultTarget, deliveryObservationTarget: input.deliveryObservationTarget,
  }
}

function validateSupportResultSections(sections) {
  const deliveryStatus = sections.deliveryStatus
  invariant(isObject(deliveryStatus), 'RESULT_SUPPORT_DELIVERY_STATUS_INVALID')
  assertExactKeys(deliveryStatus, SUPPORT_DELIVERY_STATUS_KEYS, 'RESULT_SUPPORT_DELIVERY_STATUS_FIELD_FORBIDDEN')
  assertRequiredKeys(deliveryStatus, [...SUPPORT_DELIVERY_STATUS_KEYS], 'RESULT_SUPPORT_DELIVERY_STATUS_FIELD_REQUIRED')
  invariant(SUPPORT_DELIVERY_STATES.has(deliveryStatus.state), 'RESULT_SUPPORT_DELIVERY_STATE_INVALID')
  invariant(typeof deliveryStatus.receiptObserved === 'boolean', 'RESULT_SUPPORT_DELIVERY_RECEIPT_INVALID')
  invariant(deliveryStatus.receiptObserved === false, 'RESULT_SUPPORT_DELIVERY_RECEIPT_FORBIDDEN')

  const sourceLedger = sections.sourceLedger
  invariant(isObject(sourceLedger), 'RESULT_SUPPORT_SOURCE_LEDGER_INVALID')
  assertExactKeys(sourceLedger, SUPPORT_SOURCE_LEDGER_KEYS, 'RESULT_SUPPORT_SOURCE_LEDGER_FIELD_FORBIDDEN')
  assertRequiredKeys(sourceLedger, [...SUPPORT_SOURCE_LEDGER_KEYS], 'RESULT_SUPPORT_SOURCE_LEDGER_FIELD_REQUIRED')
  assertDenseDataArray(sourceLedger.entries, 64, 'RESULT_SUPPORT_SOURCE_ENTRIES_INVALID', 'RESULT_SUPPORT_SOURCE_ENTRIES_COUNT_INVALID')
  assertDenseDataArray(sourceLedger.pendingVerification, 64, 'RESULT_SUPPORT_PENDING_INVALID', 'RESULT_SUPPORT_PENDING_COUNT_INVALID')
  invariant(
    sourceLedger.mutationAllowed === false
      && sourceLedger.entries.length === 0
      && sourceLedger.pendingVerification.length === 0,
    'RESULT_SUPPORT_LEDGER_MUTATION_FORBIDDEN',
    '26.8.10 process-support results cannot create or persist material references; route material changes back to the convener',
  )

  const artifactChecklist = sections.artifactChecklist
  invariant(isObject(artifactChecklist), 'RESULT_SUPPORT_ARTIFACT_CHECKLIST_INVALID')
  assertExactKeys(artifactChecklist, SUPPORT_ARTIFACT_CHECKLIST_KEYS, 'RESULT_SUPPORT_ARTIFACT_CHECKLIST_FIELD_FORBIDDEN')
  assertRequiredKeys(artifactChecklist, [...SUPPORT_ARTIFACT_CHECKLIST_KEYS], 'RESULT_SUPPORT_ARTIFACT_CHECKLIST_FIELD_REQUIRED')
  for (const key of ['requiredCount', 'readyCount', 'pendingCount']) {
    invariant(Number.isInteger(artifactChecklist[key]) && artifactChecklist[key] >= 0 && artifactChecklist[key] <= 256, 'RESULT_SUPPORT_ARTIFACT_COUNT_INVALID')
  }
  invariant(artifactChecklist.readyCount + artifactChecklist.pendingCount === artifactChecklist.requiredCount, 'RESULT_SUPPORT_ARTIFACT_COUNT_MISMATCH')
  invariant(artifactChecklist.humanAcceptanceRequired === true, 'RESULT_SUPPORT_HUMAN_ACCEPTANCE_REQUIRED')

  const capabilityStatus = sections.capabilityStatus
  invariant(isObject(capabilityStatus), 'RESULT_SUPPORT_CAPABILITY_STATUS_INVALID')
  assertExactKeys(capabilityStatus, SUPPORT_CAPABILITY_STATUS_KEYS, 'RESULT_SUPPORT_CAPABILITY_STATUS_FIELD_FORBIDDEN')
  assertRequiredKeys(capabilityStatus, [...SUPPORT_CAPABILITY_STATUS_KEYS], 'RESULT_SUPPORT_CAPABILITY_STATUS_FIELD_REQUIRED')
  invariant(SUPPORT_CAPABILITY_STATES.has(capabilityStatus.state), 'RESULT_SUPPORT_CAPABILITY_STATE_INVALID')
  invariant(capabilityStatus.materialStateEffect === 'none', 'RESULT_SUPPORT_CAPABILITY_MATERIAL_EFFECT_FORBIDDEN')
  invariant(capabilityStatus.externalFactProven === false, 'RESULT_SUPPORT_CAPABILITY_FACT_PROOF_FORBIDDEN')
  invariant(typeof capabilityStatus.manualVerificationRequired === 'boolean', 'RESULT_SUPPORT_CAPABILITY_MANUAL_VERIFICATION_INVALID')
  if (['unavailable', 'not_authorized', 'accepted_without_result'].includes(capabilityStatus.state)) {
    invariant(capabilityStatus.manualVerificationRequired === true, 'RESULT_SUPPORT_CAPABILITY_MANUAL_VERIFICATION_REQUIRED')
  }

  return {
    deliveryStatus: {
      state: deliveryStatus.state,
      receiptObserved: deliveryStatus.receiptObserved,
    },
    sourceLedger: { entries: [], pendingVerification: [], mutationAllowed: false },
    artifactChecklist: {
      requiredCount: artifactChecklist.requiredCount,
      readyCount: artifactChecklist.readyCount,
      pendingCount: artifactChecklist.pendingCount,
      humanAcceptanceRequired: true,
    },
    capabilityStatus: {
      state: capabilityStatus.state,
      materialStateEffect: 'none',
      externalFactProven: false,
      manualVerificationRequired: capabilityStatus.manualVerificationRequired,
    },
  }
}

export function validateResultEnvelope(input) {
  invariant(isObject(input), 'RESULT_ENVELOPE_REQUIRED')
  assertExactKeys(input, RESULT_KEYS, 'RESULT_FIELD_FORBIDDEN')
  invariant(
    input.schema === RESULT_SCHEMA || input.schema === PROCESS_SUPPORT_RESULT_SCHEMA,
    'RESULT_SCHEMA_INVALID',
  )
  safeId(input.runId, 'RESULT_RUN_ID_INVALID')
  safeId(input.agendaItemId, 'RESULT_AGENDA_ID_INVALID')
  safeId(input.seatId, 'RESULT_SEAT_ID_INVALID')
  invariant(['professional_review', 'process_support'].includes(input.taskClass), 'RESULT_CLASS_INVALID')
  if (input.taskClass === 'professional_review') {
    invariant(input.schema === RESULT_SCHEMA, 'RESULT_PROFESSIONAL_SCHEMA_INVALID')
    invariant(PROFESSIONAL_SEAT_IDS.has(input.seatId), 'RESULT_PROFESSIONAL_SEAT_INVALID')
  } else {
    invariant(SUPPORT_SEAT_IDS.has(input.seatId), 'RESULT_SUPPORT_SEAT_INVALID')
  }
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'RESULT_REVISION_INVALID')
  invariant(['support', '赞成', '有条件赞成', '反对', '不具备表态条件', 'not_applicable'].includes(input.stance), 'RESULT_STANCE_INVALID')
  invariant(['高', '中', '低', 'not_applicable'].includes(input.confidence), 'RESULT_CONFIDENCE_INVALID')
  invariant(typeof input.conclusionReady === 'boolean', 'RESULT_CONCLUSION_READY_INVALID')
  if (input.taskClass === 'process_support') {
    invariant(input.stance === 'not_applicable' && input.confidence === 'not_applicable' && input.conclusionReady === false, 'RESULT_SUPPORT_OPINION_FORBIDDEN')
  }
  safeId(input.receiptId, 'RESULT_RECEIPT_ID_INVALID')
  invariant(Array.isArray(input.evidenceRefs) && input.evidenceRefs.length <= 30, 'RESULT_EVIDENCE_REFS_INVALID')
  input.evidenceRefs.forEach((value) => safeId(value, 'RESULT_EVIDENCE_REF_INVALID'))
  requiredAssetBundleRef(input.evidenceRefs, 'RESULT_ASSET_BUNDLE_REF_COUNT_INVALID')
  if (input.taskClass === 'process_support' && input.schema === PROCESS_SUPPORT_RESULT_SCHEMA) {
    invariant(
      input.evidenceRefs.length === 1 && isCognitiveAssetBundleRef(input.evidenceRefs[0]),
      'RESULT_SUPPORT_EVIDENCE_REFS_EXACT',
      'Current process-support results must contain exactly the dispatched asset bundle reference',
    )
    invariant(input.receiptId === 'unavailable', 'RESULT_SUPPORT_RECEIPT_ID_FORBIDDEN')
  }
  invariant(isObject(input.sections) && Object.keys(input.sections).length >= 1 && Object.keys(input.sections).length <= 10, 'RESULT_SECTIONS_INVALID')
  const allowedSections = input.taskClass === 'professional_review' ? PROFESSIONAL_RESULT_SECTIONS : SUPPORT_RESULT_SECTIONS
  const unexpectedSections = Object.keys(input.sections).filter((key) => !allowedSections.has(key))
  invariant(unexpectedSections.length === 0, 'RESULT_SECTION_FORBIDDEN', 'Result contains sections outside its task class', { unexpectedSections })
  const requiredSections = input.taskClass === 'professional_review'
    ? ['judgement', 'conditions', 'failureConditions', 'humanGate', 'evidenceAssessment', 'dissent']
    : ['deliveryStatus', 'sourceLedger', 'artifactChecklist', 'capabilityStatus']
  const missingSections = requiredSections.filter((key) => !Object.hasOwn(input.sections, key))
  invariant(missingSections.length === 0, 'RESULT_SECTION_REQUIRED', 'Result is missing mandatory auditable sections', { missingSections })
  const sections = input.taskClass === 'process_support' && input.schema === PROCESS_SUPPORT_RESULT_SCHEMA
    ? validateSupportResultSections(input.sections)
    : Object.fromEntries(Object.entries(input.sections).map(([key, value]) => [key, boundedText(value, 'result_section', 4000)]))
  return {
    schema: input.schema, runId: input.runId, agendaItemId: input.agendaItemId, seatId: input.seatId,
    taskClass: input.taskClass, revision: input.revision, stance: input.stance, confidence: input.confidence,
    conclusionReady: input.conclusionReady, receiptId: input.receiptId, evidenceRefs: [...input.evidenceRefs],
    sections,
  }
}

export function validateWritableResultEnvelope(input) {
  const normalized = validateResultEnvelope(input)
  invariant(
    normalized.taskClass !== 'process_support' || normalized.schema === PROCESS_SUPPORT_RESULT_SCHEMA,
    'RESULT_SUPPORT_LEGACY_READ_ONLY',
    'Legacy fbsir.member-result/v1 process-support artifacts may be read but cannot be written by 26.8.10',
  )
  return normalized
}

export function validateDeliveryObservation(input) {
  invariant(isObject(input), 'DELIVERY_OBSERVATION_REQUIRED')
  assertExactKeys(input, DELIVERY_OBSERVATION_KEYS, 'DELIVERY_OBSERVATION_FIELD_FORBIDDEN')
  invariant(input.schema === DELIVERY_OBSERVATION_SCHEMA, 'DELIVERY_OBSERVATION_SCHEMA_INVALID')
  safeId(input.runId, 'DELIVERY_OBSERVATION_RUN_ID_INVALID')
  safeId(input.agendaItemId, 'DELIVERY_OBSERVATION_AGENDA_ID_INVALID')
  safeId(input.seatId, 'DELIVERY_OBSERVATION_SEAT_ID_INVALID')
  invariant(PROFESSIONAL_SEAT_IDS.has(input.seatId) || SUPPORT_SEAT_IDS.has(input.seatId), 'DELIVERY_OBSERVATION_SEAT_UNAVAILABLE')
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'DELIVERY_OBSERVATION_REVISION_INVALID')
  invariant(typeof input.resultPayloadHash === 'string' && HEX_64.test(input.resultPayloadHash), 'DELIVERY_OBSERVATION_RESULT_HASH_INVALID')
  invariant(input.channel === 'SendMessage', 'DELIVERY_OBSERVATION_CHANNEL_INVALID')
  invariant(input.recipient === WRITER_ID, 'DELIVERY_OBSERVATION_RECIPIENT_INVALID')
  invariant(input.status === 'tool_success_observed', 'DELIVERY_OBSERVATION_STATUS_INVALID')
  invariant(Number.isInteger(input.attempt) && input.attempt >= 1 && input.attempt <= 2, 'DELIVERY_OBSERVATION_ATTEMPT_INVALID')
  invariant(typeof input.observedAt === 'string' && Number.isFinite(Date.parse(input.observedAt)), 'DELIVERY_OBSERVATION_TIME_INVALID')
  invariant(input.hostReceiptId === null || typeof input.hostReceiptId === 'string', 'DELIVERY_OBSERVATION_HOST_RECEIPT_INVALID')
  if (typeof input.hostReceiptId === 'string') safeId(input.hostReceiptId, 'DELIVERY_OBSERVATION_HOST_RECEIPT_INVALID')
  return {
    schema: input.schema, runId: input.runId, agendaItemId: input.agendaItemId, seatId: input.seatId,
    revision: input.revision, resultPayloadHash: input.resultPayloadHash, channel: input.channel,
    recipient: input.recipient, status: input.status, attempt: input.attempt,
    observedAt: new Date(input.observedAt).toISOString(), hostReceiptId: input.hostReceiptId,
  }
}

export function validateFailureEnvelope(input) {
  invariant(isObject(input), 'FAILURE_ENVELOPE_REQUIRED')
  assertExactKeys(input, FAILURE_KEYS, 'FAILURE_FIELD_FORBIDDEN')
  invariant(input.schema === FAILURE_SCHEMA, 'FAILURE_SCHEMA_INVALID')
  safeId(input.runId, 'FAILURE_RUN_ID_INVALID')
  safeId(input.agendaItemId, 'FAILURE_AGENDA_ID_INVALID')
  safeId(input.seatId, 'FAILURE_SEAT_ID_INVALID')
  invariant(PROFESSIONAL_SEAT_IDS.has(input.seatId) || SUPPORT_SEAT_IDS.has(input.seatId), 'FAILURE_SEAT_UNAVAILABLE')
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'FAILURE_REVISION_INVALID')
  invariant(input.status === 'unavailable_after_retry', 'FAILURE_STATUS_INVALID')
  invariant(input.attempts === 2, 'FAILURE_ATTEMPTS_INVALID', 'A seat may be marked unavailable only after the initial attempt and one retry')
  invariant(['member_no_response', 'send_message_failed', 'result_invalid', 'member_terminal_without_result', 'retry_exhausted'].includes(input.reasonCode), 'FAILURE_REASON_INVALID')
  invariant(input.recordedBy === WRITER_ID, 'FAILURE_WRITER_INVALID')
  invariant(typeof input.recordedAt === 'string' && Number.isFinite(Date.parse(input.recordedAt)), 'FAILURE_TIME_INVALID')
  invariant(input.detailHash === null || (typeof input.detailHash === 'string' && HEX_64.test(input.detailHash)), 'FAILURE_DETAIL_HASH_INVALID')
  return {
    schema: input.schema, runId: input.runId, agendaItemId: input.agendaItemId, seatId: input.seatId, revision: input.revision,
    status: input.status, attempts: input.attempts, reasonCode: input.reasonCode,
    recordedBy: input.recordedBy, recordedAt: new Date(input.recordedAt).toISOString(), detailHash: input.detailHash,
  }
}

async function readJsonFile(filePath, code) {
  try { return JSON.parse(await readFile(filePath, 'utf8')) }
  catch (error) { throw new BoardContractError(code, 'JSON artifact could not be read', { filePath, cause: error.message }) }
}

function parseJsonBytes(bytes, filePath, code) {
  try { return JSON.parse(bytes.toString('utf8')) }
  catch (error) { throw new BoardContractError(code, 'JSON artifact could not be read', { filePath, cause: error.message }) }
}

async function persistNormalizedArtifact(workspaceRoot, target, normalized, conflictCode) {
  await rejectExistingLinkSegments(workspaceRoot, target, 'WORKSPACE_ARTIFACT_LINK_FORBIDDEN')
  await mkdir(path.dirname(target), { recursive: true })
  await rejectExistingLinkSegments(workspaceRoot, target, 'WORKSPACE_ARTIFACT_LINK_FORBIDDEN')
  const payloadHash = sha256(normalized)
  if (await pathExists(target)) {
    await requireRegularFileNoLink(target, 'WORKSPACE_ARTIFACT_FILE_INVALID')
    const current = await readJsonFile(target, conflictCode)
    invariant(sha256(current) === payloadHash, conflictCode, 'An existing durable artifact has different content', { target })
    return { target, payloadHash, idempotent: true }
  }
  await writeAtomic(target, `${JSON.stringify(normalized, null, 2)}\n`)
  return { target, payloadHash, idempotent: false }
}

function workspaceIdentityHash(marker) {
  safeId(marker.workspaceId, 'WORKSPACE_ID_INVALID')
  return sha256({
    schema: marker.schema,
    workspaceId: marker.workspaceId,
    product: marker.product,
    productVersion: marker.productVersion,
  })
}

function expectedPlanConfirmationRecord(marker, plan) {
  return {
    schema: PLAN_CONFIRMATION_RECORD_SCHEMA,
    actionId: 'confirm_review',
    actionInstanceId: plan.confirmationAction.actionInstanceId,
    actionEnvelopeDigest: plan.confirmationAction.actionEnvelopeDigest,
    runId: plan.runId,
    revision: plan.revision,
    confirmationReceiptId: plan.confirmationReceiptId,
    planPayloadHash: sha256(plan),
    workspaceIdHash: workspaceIdentityHash(marker),
    evidenceBoundary: PLAN_CONFIRMATION_RECORD_EVIDENCE_BOUNDARY,
  }
}

function validatePlanConfirmationRecord(input) {
  invariant(isObject(input), 'PLAN_CONFIRMATION_RECORD_INVALID')
  assertExactKeys(input, PLAN_CONFIRMATION_RECORD_KEYS, 'PLAN_CONFIRMATION_RECORD_INVALID')
  assertRequiredKeys(input, PLAN_CONFIRMATION_RECORD_KEY_LIST, 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(input.schema === PLAN_CONFIRMATION_RECORD_SCHEMA, 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(input.actionId === 'confirm_review', 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(typeof input.actionInstanceId === 'string' && ACTION_INSTANCE_ID_PATTERN.test(input.actionInstanceId), 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(typeof input.actionEnvelopeDigest === 'string' && HEX_64.test(input.actionEnvelopeDigest), 'PLAN_CONFIRMATION_RECORD_INVALID')
  safeId(input.runId, 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'PLAN_CONFIRMATION_RECORD_INVALID')
  safeId(input.confirmationReceiptId, 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(typeof input.planPayloadHash === 'string' && HEX_64.test(input.planPayloadHash), 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(typeof input.workspaceIdHash === 'string' && HEX_64.test(input.workspaceIdHash), 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(input.evidenceBoundary === PLAN_CONFIRMATION_RECORD_EVIDENCE_BOUNDARY, 'PLAN_CONFIRMATION_RECORD_INVALID')
  return Object.fromEntries(PLAN_CONFIRMATION_RECORD_KEY_LIST.map((key) => [key, input[key]]))
}

function planConfirmationRecordTarget(paths, plan) {
  const target = path.join(paths.receipts, 'action-confirmations', `${plan.confirmationAction.actionInstanceId}.json`)
  ensureWithin(paths.receipts, target)
  return target
}

async function readPlanConfirmationRecord(target, code) {
  await requireRegularFileNoLink(target, code)
  return validatePlanConfirmationRecord(await readJsonFile(target, 'PLAN_CONFIRMATION_RECORD_INVALID'))
}

async function requirePredecessorRunRefBinding(paths, plan) {
  if (plan.predecessorRunRef === null) {
    const unexpected = path.join(paths.predecessors, `${plan.runId}.json`)
    ensureWithin(paths.predecessors, unexpected)
    await rejectExistingLinkSegments(paths.root, unexpected, 'PREDECESSOR_RECEIPT_LINK_FORBIDDEN')
    invariant(!(await pathExists(unexpected)), 'PREDECESSOR_RUN_SCOPE_INVALID', 'A fresh plan cannot share its run scope with a predecessor receipt')
    return null
  }
  const captured = await readPredecessorResumeDigestReceipt({ targetWorkspaceRoot: paths.root, targetRunId: plan.runId })
  invariant(captured.receiptRef === plan.predecessorRunRef.receiptRef, 'PREDECESSOR_RECEIPT_REF_INVALID')
  invariant(captured.receiptPayloadHash === plan.predecessorRunRef.receiptPayloadHash, 'PREDECESSOR_RECEIPT_MISMATCH')
  invariant(captured.receipt.source.runIdHash === plan.predecessorRunRef.sourceRunIdHash, 'PREDECESSOR_RECEIPT_MISMATCH')
  if (plan.predecessorRunRef.schema === LEGACY_PREDECESSOR_RUN_REF_SCHEMA) {
    invariant(captured.receipt.schema === LEGACY_RESUME_DIGEST_SCHEMA, 'LEGACY_RESUME_DIGEST_MISMATCH')
    invariant(captured.receipt.legacyResumeDigest === plan.predecessorRunRef.legacyResumeDigest, 'LEGACY_RESUME_DIGEST_MISMATCH')
  } else {
    invariant(captured.receipt.schema === plan.predecessorRunRef.resumeDigestSchema, 'PREDECESSOR_RESUME_DIGEST_MISMATCH')
    invariant(resumeDigestFromReceipt(captured.receipt) === plan.predecessorRunRef.resumeDigest, 'PREDECESSOR_RESUME_DIGEST_MISMATCH')
  }
  return captured
}

export async function recordLegacyResumeDigest(input = {}) {
  const { sourceWorkspaceRoot, sourceRunId, targetWorkspaceRoot, targetRunId } = input
  invariant(typeof sourceWorkspaceRoot === 'string' && sourceWorkspaceRoot.trim(), 'LEGACY_RESUME_SOURCE_REQUIRED')
  invariant(typeof targetWorkspaceRoot === 'string' && targetWorkspaceRoot.trim(), 'LEGACY_RESUME_TARGET_REQUIRED')
  invariant(typeof targetRunId === 'string' && RUN_ID_PATTERN.test(targetRunId), 'LEGACY_RESUME_TARGET_RUN_ID_INVALID')
  invariant(targetRunId !== sourceRunId, 'LEGACY_RESUME_RUN_SCOPE_INVALID', 'A read-only predecessor must resume into a different new run')
  const sourceRoot = path.resolve(sourceWorkspaceRoot)
  const targetRoot = path.resolve(targetWorkspaceRoot)
  const sourceToTarget = path.relative(sourceRoot, targetRoot)
  const targetToSource = path.relative(targetRoot, sourceRoot)
  const sourceContainsTarget = sourceToTarget === '' || (!sourceToTarget.startsWith('..') && !path.isAbsolute(sourceToTarget))
  const targetContainsSource = targetToSource === '' || (!targetToSource.startsWith('..') && !path.isAbsolute(targetToSource))
  invariant(!sourceContainsTarget && !targetContainsSource, 'LEGACY_RESUME_WORKSPACE_BOUNDARY_INVALID')
  await inspectLegacyResume({ sourceWorkspaceRoot, sourceRunId })
  await requireWritableWorkspace(targetWorkspaceRoot)
  const paths = workspacePaths(targetWorkspaceRoot, targetRunId)
  const receiptTarget = path.join(paths.predecessors, `${targetRunId}.json`)
  ensureWithin(paths.predecessors, receiptTarget)
  await rejectExistingLinkSegments(paths.root, receiptTarget, 'LEGACY_RESUME_TARGET_LINK_FORBIDDEN')
  if (await pathExists(receiptTarget)) {
    if (await pathExists(paths.planFile)) {
      await rejectExistingLinkSegments(paths.root, paths.planFile, 'WORKSPACE_ARTIFACT_LINK_FORBIDDEN')
      await requireRegularFileNoLink(paths.planFile, 'MEMBER_PLAN_INVALID')
      const plan = validateReviewPlan(await readJsonFile(paths.planFile, 'MEMBER_PLAN_INVALID'))
      invariant(plan.predecessorRunRef !== null, 'PREDECESSOR_RUN_SCOPE_INVALID', 'A fresh plan cannot acquire a predecessor receipt after recording')
      await requirePredecessorRunRefBinding(paths, plan)
    }
    return recordLegacyResumeDigestUnlocked(input)
  }
  const planLockFile = path.join(paths.locks, `${targetRunId}.plan.lock`)
  ensureWithin(paths.locks, planLockFile)
  await rejectExistingLinkSegments(paths.root, planLockFile, 'PLAN_RECORD_LOCK_LINK_FORBIDDEN')
  const lock = await acquireLock(planLockFile)
  try {
    await rejectExistingLinkSegments(paths.root, paths.planFile, 'WORKSPACE_ARTIFACT_LINK_FORBIDDEN')
    invariant(!(await pathExists(paths.planFile)), 'PREDECESSOR_PLAN_ALREADY_RECORDED', 'A predecessor receipt must be recorded before the plan that binds it')
    return await recordLegacyResumeDigestUnlocked(input)
  } finally {
    await releaseLock(lock, planLockFile)
  }
}

export async function recordPredecessorResumeDigest(input = {}) {
  const { sourceWorkspaceRoot, sourceRunId, targetWorkspaceRoot, targetRunId } = input
  invariant(typeof sourceWorkspaceRoot === 'string' && sourceWorkspaceRoot.trim(), 'PREDECESSOR_RESUME_SOURCE_REQUIRED')
  invariant(typeof targetWorkspaceRoot === 'string' && targetWorkspaceRoot.trim(), 'PREDECESSOR_RESUME_TARGET_REQUIRED')
  invariant(typeof targetRunId === 'string' && RUN_ID_PATTERN.test(targetRunId), 'PREDECESSOR_RESUME_TARGET_RUN_ID_INVALID')
  invariant(targetRunId !== sourceRunId, 'PREDECESSOR_RESUME_RUN_SCOPE_INVALID', 'A read-only predecessor must resume into a different new run')
  const sourceRoot = path.resolve(sourceWorkspaceRoot)
  const targetRoot = path.resolve(targetWorkspaceRoot)
  const sourceToTarget = path.relative(sourceRoot, targetRoot)
  const targetToSource = path.relative(targetRoot, sourceRoot)
  const sourceContainsTarget = sourceToTarget === '' || (!sourceToTarget.startsWith('..') && !path.isAbsolute(sourceToTarget))
  const targetContainsSource = targetToSource === '' || (!targetToSource.startsWith('..') && !path.isAbsolute(targetToSource))
  invariant(!sourceContainsTarget && !targetContainsSource, 'PREDECESSOR_RESUME_WORKSPACE_BOUNDARY_INVALID')
  await inspectPredecessorResume({ sourceWorkspaceRoot, sourceRunId })
  await requireWritableWorkspace(targetWorkspaceRoot)
  const paths = workspacePaths(targetWorkspaceRoot, targetRunId)
  const receiptTarget = path.join(paths.predecessors, `${targetRunId}.json`)
  ensureWithin(paths.predecessors, receiptTarget)
  await rejectExistingLinkSegments(paths.root, receiptTarget, 'LEGACY_RESUME_TARGET_LINK_FORBIDDEN')
  if (await pathExists(receiptTarget)) {
    if (await pathExists(paths.planFile)) {
      await rejectExistingLinkSegments(paths.root, paths.planFile, 'WORKSPACE_ARTIFACT_LINK_FORBIDDEN')
      await requireRegularFileNoLink(paths.planFile, 'MEMBER_PLAN_INVALID')
      const plan = validateReviewPlan(await readJsonFile(paths.planFile, 'MEMBER_PLAN_INVALID'))
      invariant(plan.predecessorRunRef !== null, 'PREDECESSOR_RUN_SCOPE_INVALID', 'A fresh plan cannot acquire a predecessor receipt after recording')
      await requirePredecessorRunRefBinding(paths, plan)
    }
    return recordPredecessorResumeDigestUnlocked(input)
  }
  const planLockFile = path.join(paths.locks, `${targetRunId}.plan.lock`)
  ensureWithin(paths.locks, planLockFile)
  await rejectExistingLinkSegments(paths.root, planLockFile, 'PLAN_RECORD_LOCK_LINK_FORBIDDEN')
  const lock = await acquireLock(planLockFile)
  try {
    await rejectExistingLinkSegments(paths.root, paths.planFile, 'WORKSPACE_ARTIFACT_LINK_FORBIDDEN')
    invariant(!(await pathExists(paths.planFile)), 'PREDECESSOR_PLAN_ALREADY_RECORDED', 'A predecessor receipt must be recorded before the plan that binds it')
    return await recordPredecessorResumeDigestUnlocked(input)
  } finally {
    await releaseLock(lock, planLockFile)
  }
}

async function historicalPlanConfirmationOwner(paths, marker, plan) {
  const actionInstanceId = plan.confirmationAction.actionInstanceId
  const entries = await readdir(paths.plans, { withFileTypes: true })
  const matches = []
  for (const entry of entries.filter((item) => item.name.endsWith('.json')).sort((left, right) => left.name.localeCompare(right.name))) {
    const target = path.join(paths.plans, entry.name)
    await rejectExistingLinkSegments(paths.root, target, 'PLAN_CONFIRMATION_HISTORY_LINK_FORBIDDEN')
    await requireRegularFileNoLink(target, 'PLAN_CONFIRMATION_HISTORY_INVALID')
    const stored = await readJsonFile(target, 'PLAN_CONFIRMATION_HISTORY_INVALID')
    if (stored?.confirmationAction?.actionInstanceId !== actionInstanceId) continue
    let normalized
    try { normalized = validateReviewPlan(stored) }
    catch (error) {
      throw new BoardContractError('PLAN_CONFIRMATION_HISTORY_INVALID', 'A durable plan that references the confirmation action is invalid', { target, cause: error?.code || error?.message })
    }
    matches.push({ target, plan: normalized, record: expectedPlanConfirmationRecord(marker, normalized) })
  }
  invariant(matches.length <= 1, 'PLAN_CONFIRMATION_HISTORY_CONFLICT', 'More than one durable plan already references this confirmation action', { actionInstanceId })
  return matches[0] || null
}

async function historicalRunConfirmationOwner(paths, plan) {
  const directory = path.join(paths.receipts, 'action-confirmations')
  const entries = await readdir(directory, { withFileTypes: true })
  const matches = []
  for (const entry of entries.filter((item) => item.name.endsWith('.json')).sort((left, right) => left.name.localeCompare(right.name))) {
    const target = path.join(directory, entry.name)
    await rejectExistingLinkSegments(paths.root, target, 'PLAN_CONFIRMATION_RUN_HISTORY_LINK_FORBIDDEN')
    await requireRegularFileNoLink(target, 'PLAN_CONFIRMATION_RUN_HISTORY_INVALID')
    const stored = await readJsonFile(target, 'PLAN_CONFIRMATION_RUN_HISTORY_INVALID')
    if (stored?.runId !== plan.runId) continue
    let normalized
    try { normalized = validatePlanConfirmationRecord(stored) }
    catch (error) {
      throw new BoardContractError('PLAN_CONFIRMATION_RUN_HISTORY_INVALID', 'A durable confirmation record that references this run is invalid', { target, cause: error?.code || error?.message })
    }
    invariant(entry.name === `${normalized.actionInstanceId}.json`, 'PLAN_CONFIRMATION_RUN_HISTORY_INVALID', 'A durable confirmation record filename must match its action instance', { target })
    matches.push({ target, record: normalized })
  }
  invariant(matches.length <= 1, 'PLAN_CONFIRMATION_RUN_HISTORY_CONFLICT', 'More than one durable confirmation record already references this run', { runId: plan.runId })
  return matches[0] || null
}

async function publishPlanConfirmationRecord(target, expected) {
  return publishExclusiveJson(target, expected)
}

async function requirePlanConfirmationRecordBinding(paths, marker, plan) {
  await requirePredecessorRunRefBinding(paths, plan)
  const target = planConfirmationRecordTarget(paths, plan)
  await rejectExistingLinkSegments(paths.root, target, 'PLAN_CONFIRMATION_RECORD_LINK_FORBIDDEN')
  const current = await readPlanConfirmationRecord(target, 'PLAN_CONFIRMATION_RECORD_REQUIRED')
  const expected = expectedPlanConfirmationRecord(marker, plan)
  invariant(
    sha256(current) === sha256(expected),
    'PLAN_CONFIRMATION_RECORD_MISMATCH',
    'The durable confirmation ownership record must bind the exact workspace and plan',
    { target },
  )
  return { target, payloadHash: sha256(current), record: current }
}

async function claimPlanConfirmationRecord(paths, marker, plan) {
  const target = planConfirmationRecordTarget(paths, plan)
  const directory = path.dirname(target)
  const expected = expectedPlanConfirmationRecord(marker, plan)
  const payloadHash = sha256(expected)
  await rejectExistingLinkSegments(paths.root, directory, 'PLAN_CONFIRMATION_RECORD_LINK_FORBIDDEN')
  await mkdir(directory, { recursive: true })
  await rejectExistingLinkSegments(paths.root, target, 'PLAN_CONFIRMATION_RECORD_LINK_FORBIDDEN')
  const runOwner = await historicalRunConfirmationOwner(paths, plan)
  if (runOwner) {
    invariant(
      sha256(runOwner.record) === payloadHash,
      'PLAN_CONFIRMATION_RUN_REPLAY',
      'The run already has a different durable confirmation ownership reservation',
      { target: runOwner.target },
    )
  }
  const historicalOwner = await historicalPlanConfirmationOwner(paths, marker, plan)
  if (historicalOwner) {
    invariant(
      sha256(historicalOwner.record) === payloadHash,
      'PLAN_CONFIRMATION_ACTION_REPLAY',
      'The confirmation action instance is already referenced by a different durable plan in this workspace',
      { target: historicalOwner.target },
    )
  }
  if (await publishPlanConfirmationRecord(target, expected)) {
    return { target, payloadHash, idempotent: false }
  }
  const current = await readPlanConfirmationRecord(target, 'PLAN_CONFIRMATION_RECORD_INVALID')
  invariant(
    sha256(current) === payloadHash,
    'PLAN_CONFIRMATION_ACTION_REPLAY',
    'The confirmation action instance is already owned by a different plan in this workspace',
    { target },
  )
  return { target, payloadHash, idempotent: true }
}

export async function recordReviewPlan({ workspaceRoot, actorId, envelope }) {
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  const marker = await requireWritableWorkspace(workspaceRoot)
  const normalized = validateReviewPlan(envelope)
  const paths = workspacePaths(workspaceRoot, normalized.runId)
  const target = paths.planFile
  ensureWithin(paths.plans, target)
  const planLockFile = path.join(paths.locks, `${normalized.runId}.plan.lock`)
  ensureWithin(paths.locks, planLockFile)
  await rejectExistingLinkSegments(paths.root, planLockFile, 'PLAN_RECORD_LOCK_LINK_FORBIDDEN')
  const lock = await acquireLock(planLockFile)
  try {
    const predecessor = await requirePredecessorRunRefBinding(paths, normalized)
    const payloadHash = sha256(normalized)
    let planAlreadyPresent = false
    await rejectExistingLinkSegments(paths.root, target, 'WORKSPACE_ARTIFACT_LINK_FORBIDDEN')
    if (await pathExists(target)) {
      await requireRegularFileNoLink(target, 'WORKSPACE_ARTIFACT_FILE_INVALID')
      const current = await readJsonFile(target, 'PLAN_RECORD_CONFLICT')
      invariant(sha256(current) === payloadHash, 'PLAN_RECORD_CONFLICT', 'An existing durable artifact has different content', { target })
      planAlreadyPresent = true
    }
    const confirmation = await claimPlanConfirmationRecord(paths, marker, normalized)
    const persisted = planAlreadyPresent
      ? { target, payloadHash, idempotent: true }
      : await persistNormalizedArtifact(paths.root, target, normalized, 'PLAN_RECORD_CONFLICT')
    return {
      ...persisted,
      confirmationRecordTarget: confirmation.target,
      confirmationRecordPayloadHash: confirmation.payloadHash,
      confirmationRecordIdempotent: confirmation.idempotent,
      ...(predecessor ? {
        predecessorReceiptRef: predecessor.receiptRef,
        predecessorReceiptPayloadHash: predecessor.receiptPayloadHash,
      } : {}),
    }
  } finally {
    await releaseLock(lock, planLockFile)
  }
}

async function requireMemberArtifactPlanBinding(workspaceRoot, marker, envelope) {
  const paths = workspacePaths(workspaceRoot, envelope.runId)
  await rejectExistingLinkSegments(paths.root, paths.planFile, 'MEMBER_PLAN_LINK_FORBIDDEN')
  await requireRegularFileNoLink(paths.planFile, 'MEMBER_PLAN_REQUIRED')
  const plan = validateReviewPlan(await readJsonFile(paths.planFile, 'MEMBER_PLAN_INVALID'))
  invariant(plan.runId === envelope.runId && plan.revision === envelope.revision, 'MEMBER_PLAN_SCOPE_MISMATCH')
  const agenda = plan.agendaItems.find((item) => item.agendaItemId === envelope.agendaItemId)
  invariant(agenda, 'MEMBER_PLAN_AGENDA_MISMATCH')
  const expectedTaskClass = plan.specialistSeatIds.includes(envelope.seatId)
    ? 'professional_review'
    : plan.supportSeatIds.includes(envelope.seatId)
      ? 'process_support'
      : null
  invariant(expectedTaskClass, 'MEMBER_PLAN_SEAT_MISMATCH')
  if (Object.hasOwn(envelope, 'taskClass')) invariant(envelope.taskClass === expectedTaskClass, 'MEMBER_PLAN_TASK_CLASS_MISMATCH')
  if (Object.hasOwn(envelope, 'reviewMode')) invariant(envelope.reviewMode === plan.reviewMode, 'MEMBER_PLAN_REVIEW_MODE_MISMATCH')
  if (Object.hasOwn(envelope, 'decisionQuestion')) invariant(envelope.decisionQuestion === agenda.decisionQuestion, 'MEMBER_PLAN_QUESTION_MISMATCH')
  await requirePlanConfirmationRecordBinding(paths, marker, plan)
  return { paths, plan }
}

export async function recordTaskEnvelope({ workspaceRoot, actorId, envelope }) {
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  const marker = await requireWritableWorkspace(workspaceRoot)
  const normalized = validateTaskEnvelope(envelope)
  await requireMemberArtifactPlanBinding(workspaceRoot, marker, normalized)
  const paths = workspacePaths(workspaceRoot)
  const target = path.join(paths.root, memberArtifactTargets(normalized).taskTarget)
  ensureWithin(paths.tasks, target)
  const persisted = await persistNormalizedArtifact(paths.root, target, normalized, 'TASK_RECORD_CONFLICT')
  const taskPayloadHash = sha256(await readFile(target))
  return { ...persisted, taskPayloadHash }
}

export async function recordResultEnvelope({ workspaceRoot, envelope }) {
  const marker = await requireWritableWorkspace(workspaceRoot)
  const normalized = validateWritableResultEnvelope(envelope)
  await requireMemberArtifactPlanBinding(workspaceRoot, marker, normalized)
  const paths = workspacePaths(workspaceRoot)
  const targets = memberArtifactTargets(normalized)
  const taskPath = path.join(paths.root, targets.taskTarget)
  ensureWithin(paths.tasks, taskPath)
  await rejectExistingLinkSegments(paths.root, taskPath, 'RESULT_TASK_LINK_FORBIDDEN')
  await requireRegularFileNoLink(taskPath, 'RESULT_TASK_INVALID')
  const task = validateTaskEnvelope(await readJsonFile(taskPath, 'RESULT_TASK_INVALID'))
  invariant(
    task.runId === normalized.runId
      && task.agendaItemId === normalized.agendaItemId
      && task.seatId === normalized.seatId
      && task.revision === normalized.revision
      && task.taskClass === normalized.taskClass,
    'RESULT_TASK_IDENTITY_MISMATCH',
  )
  invariant(
    normalized.evidenceRefs.length === task.evidenceRefs.length
      && normalized.evidenceRefs.every((value, index) => value === task.evidenceRefs[index]),
    'RESULT_TASK_EVIDENCE_REFS_MISMATCH',
  )
  const target = path.join(paths.root, targets.resultTarget)
  ensureWithin(paths.results, target)
  const persisted = await persistNormalizedArtifact(paths.root, target, normalized, 'RESULT_RECORD_CONFLICT')
  if (normalized.taskClass !== 'process_support') return persisted
  return {
    ...persisted,
    handoff: validateProcessSupportHandoff({
      schema: PROCESS_SUPPORT_HANDOFF_SCHEMA,
      runId: normalized.runId,
      agendaItemId: normalized.agendaItemId,
      seatId: normalized.seatId,
      revision: normalized.revision,
      resultTarget: targets.resultTarget,
      resultPayloadHash: persisted.payloadHash,
    }),
  }
}

export async function recordDeliveryObservation({ workspaceRoot, observation }) {
  const marker = await requireWritableWorkspace(workspaceRoot)
  const normalized = validateDeliveryObservation(observation)
  await requireMemberArtifactPlanBinding(workspaceRoot, marker, normalized)
  const paths = workspacePaths(workspaceRoot)
  const target = path.join(paths.root, memberArtifactTargets(normalized).deliveryObservationTarget)
  ensureWithin(paths.receipts, target)
  return persistNormalizedArtifact(paths.root, target, normalized, 'DELIVERY_OBSERVATION_RECORD_CONFLICT')
}

export async function recordFailureEnvelope({ workspaceRoot, actorId, envelope }) {
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  const marker = await requireWritableWorkspace(workspaceRoot)
  const normalized = validateFailureEnvelope(envelope)
  await requireMemberArtifactPlanBinding(workspaceRoot, marker, normalized)
  const paths = workspacePaths(workspaceRoot)
  const target = path.join(paths.root, memberArtifactTargets(normalized).failureTarget)
  ensureWithin(paths.failures, target)
  return persistNormalizedArtifact(paths.root, target, normalized, 'FAILURE_RECORD_CONFLICT')
}

function artifactErrorCode(error) {
  if (error instanceof BoardContractError) return error.code
  if (error?.code === 'ENOENT') return 'ARTIFACT_NOT_FOUND'
  if (typeof error?.code === 'string' && /^[A-Z][A-Z0-9_]{2,127}$/.test(error.code)) return error.code
  return 'ARTIFACT_INVALID'
}

export async function collectReviewRun({ workspaceRoot, runId }) {
  const marker = await requireWritableWorkspace(workspaceRoot)
  safeId(runId, 'COLLECTION_RUN_ID_INVALID')
  const paths = workspacePaths(workspaceRoot, runId)
  const planPath = paths.planFile
  ensureWithin(paths.plans, planPath)
  await rejectExistingLinkSegments(paths.root, planPath, 'COLLECTION_PLAN_LINK_FORBIDDEN')
  await requireRegularFileNoLink(planPath, 'COLLECTION_PLAN_INVALID')
  const plan = validateReviewPlan(await readJsonFile(planPath, 'COLLECTION_PLAN_INVALID'))
  invariant(plan.runId === runId, 'COLLECTION_PLAN_RUN_MISMATCH')
  await requirePlanConfirmationRecordBinding(paths, marker, plan)
  const events = await readEvents(paths, runId, marker)

  const selectedSeats = [
    ...plan.specialistSeatIds.map((seatId) => ({ seatId, taskClass: 'professional_review', phase: 'phase1_independent', seatClass: 'professional' })),
    ...plan.supportSeatIds.map((seatId) => ({ seatId, taskClass: 'process_support', phase: 'phase1_process_support', seatClass: 'process_support' })),
  ]
  const statuses = []
  for (const agenda of plan.agendaItems) {
    for (const selectedSeat of selectedSeats) {
      const { seatId, taskClass, phase, seatClass } = selectedSeat
      const targets = memberArtifactTargets({ agendaItemId: agenda.agendaItemId, seatId, revision: plan.revision })
      const taskPath = path.join(paths.root, targets.taskTarget)
      const resultPath = path.join(paths.root, targets.resultTarget)
      const observationPath = path.join(paths.root, targets.deliveryObservationTarget)
      const failurePath = path.join(paths.root, targets.failureTarget)
      const base = { agendaItemId: agenda.agendaItemId, seatId, seatClass, taskClass, revision: plan.revision, taskTarget: targets.taskTarget, resultTarget: targets.resultTarget, deliveryObservationTarget: targets.deliveryObservationTarget, failureTarget: targets.failureTarget }

      if (!(await pathExists(taskPath))) {
        statuses.push({ ...base, status: 'awaiting_task' })
        continue
      }

      let assetBundleRef
      let taskEvidenceRefs
      let taskPayloadHash
      try {
        await rejectExistingLinkSegments(paths.root, taskPath, 'COLLECTION_TASK_LINK_FORBIDDEN')
        await requireRegularFileNoLink(taskPath, 'COLLECTION_TASK_INVALID')
        const taskBytes = await readFile(taskPath)
        taskPayloadHash = sha256(taskBytes)
        const task = validateTaskEnvelope(parseJsonBytes(taskBytes, taskPath, 'COLLECTION_TASK_INVALID'))
        invariant(task.runId === runId && task.agendaItemId === agenda.agendaItemId && task.seatId === seatId && task.revision === plan.revision, 'COLLECTION_TASK_IDENTITY_MISMATCH')
        invariant(task.taskClass === taskClass && task.reviewMode === plan.reviewMode && task.decisionQuestion === agenda.decisionQuestion, 'COLLECTION_TASK_PLAN_MISMATCH')
        assetBundleRef = requiredAssetBundleRef(task.evidenceRefs, 'COLLECTION_TASK_ASSET_BUNDLE_REF_COUNT_INVALID')
        if (taskClass === 'process_support') {
          invariant(
            task.evidenceRefs.length === 1 && isCognitiveAssetBundleRef(task.evidenceRefs[0]),
            'COLLECTION_SUPPORT_TASK_EVIDENCE_REFS_EXACT',
          )
        }
        taskEvidenceRefs = [...task.evidenceRefs]
        await verifyCognitiveAssetBundle({
          workspaceRoot: paths.root,
          input: {
            schema: BUNDLE_VERIFY_REQUEST_SCHEMA,
            agendaItemId: agenda.agendaItemId,
            seatId,
            revision: plan.revision,
            phase,
            decisionCardHash: plan.decisionCardHash,
            bundleRef: assetBundleRef,
            asOf: new Date().toISOString().slice(0, 10),
          },
        })
      } catch (error) {
        const errorCode = artifactErrorCode(error)
        const assetFailure = errorCode.startsWith('ASSET_') || errorCode.includes('ASSET_BUNDLE')
        statuses.push({ ...base, ...(taskPayloadHash ? { taskPayloadHash } : {}), status: assetFailure ? 'invalid_asset_bundle' : 'invalid_task', errorCode })
        continue
      }
      const taskBoundBase = { ...base, taskPayloadHash }

      if (await pathExists(failurePath)) {
        try {
          await rejectExistingLinkSegments(paths.root, failurePath, 'COLLECTION_FAILURE_LINK_FORBIDDEN')
          await requireRegularFileNoLink(failurePath, 'COLLECTION_FAILURE_INVALID')
          const failure = validateFailureEnvelope(await readJsonFile(failurePath, 'COLLECTION_FAILURE_INVALID'))
          invariant(failure.runId === runId && failure.agendaItemId === agenda.agendaItemId && failure.seatId === seatId && failure.revision === plan.revision, 'COLLECTION_FAILURE_IDENTITY_MISMATCH')
          statuses.push({ ...taskBoundBase, status: 'unavailable_after_retry', reasonCode: failure.reasonCode, attempts: failure.attempts, failurePayloadHash: sha256(failure), assetBundleRef })
        } catch (error) {
          statuses.push({ ...taskBoundBase, status: 'invalid_failure_evidence', errorCode: artifactErrorCode(error) })
        }
        continue
      }

      if (!(await pathExists(resultPath))) {
        statuses.push({ ...taskBoundBase, status: 'awaiting_result' })
        continue
      }

      let result
      let resultPayloadHash
      try {
        await rejectExistingLinkSegments(paths.root, resultPath, 'COLLECTION_RESULT_LINK_FORBIDDEN')
        await requireRegularFileNoLink(resultPath, 'COLLECTION_RESULT_INVALID')
        result = validateWritableResultEnvelope(await readJsonFile(resultPath, 'COLLECTION_RESULT_INVALID'))
        invariant(result.runId === runId && result.agendaItemId === agenda.agendaItemId && result.seatId === seatId && result.revision === plan.revision && result.taskClass === taskClass, 'COLLECTION_RESULT_IDENTITY_MISMATCH')
        const resultAssetBundleRef = requiredAssetBundleRef(result.evidenceRefs, 'COLLECTION_ASSET_BUNDLE_REF_COUNT_INVALID')
        invariant(resultAssetBundleRef === assetBundleRef, 'COLLECTION_ASSET_BUNDLE_REF_MISMATCH', 'Result must echo the exact bundle reference persisted in the dispatched task')
        invariant(
          result.evidenceRefs.length === taskEvidenceRefs.length
            && result.evidenceRefs.every((value, index) => value === taskEvidenceRefs[index]),
          'COLLECTION_EVIDENCE_REFS_MISMATCH',
          'Result must echo the complete evidenceRefs array persisted in the dispatched task',
        )
        resultPayloadHash = sha256(result)
      } catch (error) {
        const errorCode = artifactErrorCode(error)
        const assetFailure = errorCode.startsWith('ASSET_') || errorCode.startsWith('COLLECTION_ASSET_')
        statuses.push({ ...taskBoundBase, status: assetFailure ? 'invalid_asset_bundle' : 'invalid_result', errorCode })
        continue
      }

      if (!(await pathExists(observationPath))) {
        statuses.push({ ...taskBoundBase, status: 'awaiting_delivery_observation', resultPayloadHash })
        continue
      }

      try {
        await rejectExistingLinkSegments(paths.root, observationPath, 'COLLECTION_DELIVERY_LINK_FORBIDDEN')
        await requireRegularFileNoLink(observationPath, 'COLLECTION_DELIVERY_OBSERVATION_INVALID')
        const observation = validateDeliveryObservation(await readJsonFile(observationPath, 'COLLECTION_DELIVERY_OBSERVATION_INVALID'))
        invariant(observation.runId === runId && observation.agendaItemId === agenda.agendaItemId && observation.seatId === seatId && observation.revision === plan.revision, 'COLLECTION_DELIVERY_IDENTITY_MISMATCH')
        invariant(observation.resultPayloadHash === resultPayloadHash, 'COLLECTION_RESULT_HASH_MISMATCH')
        statuses.push({
          ...taskBoundBase, status: 'accepted', resultPayloadHash, deliveryAttempt: observation.attempt,
          hostReceiptIdReported: observation.hostReceiptId, assetBundleRef,
          assetVerificationBoundary: 'bundle_file_identity_hash_scope_freshness_and_budget_verified_not_cognitive_use_proof',
        })
      } catch (error) {
        statuses.push({ ...taskBoundBase, status: artifactErrorCode(error) === 'COLLECTION_RESULT_HASH_MISMATCH' ? 'result_hash_mismatch' : 'invalid_delivery_observation', resultPayloadHash, errorCode: artifactErrorCode(error) })
      }
    }
  }

  const eventBoundStatuses = bindCollectionStatusesToCurrentRunEvents({
    events,
    plan,
    statuses,
    planPayloadHash: sha256(plan),
  })

  const accepted = eventBoundStatuses.filter((item) => item.status === 'accepted')
  const unavailable = eventBoundStatuses.filter((item) => item.status === 'unavailable_after_retry')
  const resolved = eventBoundStatuses.filter((item) => item.status === 'accepted' || item.status === 'unavailable_after_retry')
  const invalid = eventBoundStatuses.filter((item) => item.status.startsWith('invalid_') || item.status === 'result_hash_mismatch')
  const allSelectedResolved = eventBoundStatuses.length > 0 && resolved.length === eventBoundStatuses.length
  const acceptedProfessional = accepted.filter((item) => item.seatClass === 'professional')
  const acceptedSupport = accepted.filter((item) => item.seatClass === 'process_support')
  const readyForSynthesis = allSelectedResolved && acceptedProfessional.length > 0
  const state = readyForSynthesis
    ? 'ready_for_synthesis'
    : allSelectedResolved
      ? 'blocked_no_professional_result'
      : invalid.length > 0
        ? 'invalid_member_evidence'
        : 'awaiting_member_results'
  const collection = {
    schema: COLLECTION_SCHEMA,
    runId,
    planPayloadHash: sha256(plan),
    planRevision: plan.revision,
    decisionCardHash: plan.decisionCardHash,
    reviewMode: plan.reviewMode,
    expectedResultCount: eventBoundStatuses.length,
    acceptedResultCount: accepted.length,
    acceptedProfessionalResultCount: acceptedProfessional.length,
    acceptedSupportResultCount: acceptedSupport.length,
    unavailableResultCount: unavailable.length,
    unresolvedResultCount: eventBoundStatuses.length - resolved.length,
    allSelectedResolved,
    readyForSynthesis,
    state,
    statuses: eventBoundStatuses,
    release: { packageId: PACKAGE_ID, productVersion: WORKSPACE_PRODUCT_VERSION },
    evidenceBoundary: 'durable_result_content_member_observed_sendmessage_and_current_run_event_hash_binding_only_not_host_signed_receipt_lead_consumption_or_semantic_provenance_proof',
  }
  const collectionPayloadHash = sha256(collection)
  await rejectExistingLinkSegments(paths.root, paths.collectionFile, 'COLLECTION_OUTPUT_LINK_FORBIDDEN')
  await mkdir(paths.collections, { recursive: true })
  await rejectExistingLinkSegments(paths.root, paths.collectionFile, 'COLLECTION_OUTPUT_LINK_FORBIDDEN')
  await writeAtomic(paths.collectionFile, `${JSON.stringify({ ...collection, collectionPayloadHash }, null, 2)}\n`)
  return { collection, collectionPayloadHash, collectionFile: paths.collectionFile }
}

const QUICK_DELIVERY_SECTION_HEADINGS = Object.freeze([
  '一、一句话判断',
  '二、事实 / 估计 / 假设 / 判断 / 未知与最强反证',
  '三、专业席立场及成立条件',
  '四、最大风险与失效条件',
  '五、决策质量最弱链',
  '六、唯一下一步、触发器、负责人、复审日期与人工关卡',
])

const TEN_DELIVERY_SECTION_HEADINGS = Object.freeze([
  '一、议案、选项与 Non-goals',
  '二、证据、假设与关键缺口',
  '三、各席核心判断',
  '四、质询、修正与保留异议',
  '五、建议、成立条件与失效条件',
  '六、决策质量六链门禁（最弱链 / 缺口 / 状态）',
  '七、决策日志（选择 / 指标 / 触发器 / 负责人 / 复审日期）',
  '八、7/30/90 天行动（责任方向 / 人工关卡 / 验收标准）',
  '九、证据台账、席位回执与资产包索引',
  '十、专业边界与需人工复核事项',
])

const STANDARD_DELIVERY_SUMMARY_LABELS = Object.freeze(['【表态统计】', '【一句话建议】'])

const DELIVERY_ARTIFACT_CONTRACTS = Object.freeze({
  quick_review_card: Object.freeze({
    title: '# 独董会快速审议卡',
    sectionHeadings: QUICK_DELIVERY_SECTION_HEADINGS,
    requiredSections: Object.freeze(['judgement', 'evidence', 'seat_stance', 'failure_condition', 'decision_quality', 'action_human_gate']),
    summaryLabels: Object.freeze([]),
  }),
  review_memo: Object.freeze({
    title: '# 独董会审议备忘录',
    sectionHeadings: TEN_DELIVERY_SECTION_HEADINGS,
    requiredSections: Object.freeze(['options', 'evidence', 'seat_judgements', 'dissent', 'conditions', 'decision_quality', 'decision_journal', 'action_human_gate', 'evidence_asset_index', 'professional_boundary']),
    summaryLabels: STANDARD_DELIVERY_SUMMARY_LABELS,
  }),
  deep_review_preparation_card: Object.freeze({
    title: '# 独董会深度审议准备卡',
    sectionHeadings: TEN_DELIVERY_SECTION_HEADINGS,
    requiredSections: Object.freeze(['options', 'evidence', 'seat_judgements', 'dissent', 'conditions', 'decision_quality', 'decision_journal', 'action_human_gate', 'evidence_asset_index', 'professional_boundary']),
    summaryLabels: STANDARD_DELIVERY_SUMMARY_LABELS,
  }),
})

function deliveryContractLinesOutsideFences(lines) {
  const outside = []
  let fence = null
  for (const rawLine of lines) {
    if (fence) {
      const closing = rawLine.match(/^ {0,3}(`{3,}|~{3,})[\t ]*$/)
      if (closing && closing[1][0] === fence.marker && closing[1].length >= fence.length) fence = null
      continue
    }
    const opening = rawLine.match(/^ {0,3}(`{3,})([^`]*)$/) || rawLine.match(/^ {0,3}(~{3,})(.*)$/)
    if (opening) {
      fence = { marker: opening[1][0], length: opening[1].length }
      continue
    }
    outside.push(rawLine.replace(/^ {0,3}/, ''))
  }
  invariant(fence === null, 'DELIVERY_FENCE_UNCLOSED')
  return outside
}

export function validateDeliveryArtifactStructure(content, artifactType) {
  invariant(typeof content === 'string', 'DELIVERY_ARTIFACT_CONTENT_INVALID')
  const contract = DELIVERY_ARTIFACT_CONTRACTS[artifactType]
  invariant(isObject(contract), 'DELIVERY_ARTIFACT_TYPE_INVALID')
  const lines = content.replaceAll('\r\n', '\n').replaceAll('\r', '\n').split('\n')
  const firstRawContent = lines.find((line) => line.trim().length > 0)
  invariant(firstRawContent?.replace(/^ {0,3}/, '') === contract.title, 'DELIVERY_ARTIFACT_TITLE_INVALID', 'Artifact must begin with the canonical title')
  const contractLines = deliveryContractLinesOutsideFences(lines)
  const firstContentIndex = contractLines.findIndex((line) => line.length > 0)
  invariant(firstContentIndex >= 0 && contractLines[firstContentIndex] === contract.title, 'DELIVERY_ARTIFACT_TITLE_INVALID', 'Artifact must begin with the canonical title')
  const h1Lines = contractLines.filter((line) => /^#(?:[\t ]+|$)/.test(line))
  invariant(h1Lines.length === 1 && h1Lines[0] === contract.title, 'DELIVERY_ARTIFACT_TITLE_INVALID', 'Artifact must contain exactly one canonical H1 title')
  invariant(!contractLines.some((line) => /^=+[\t ]*$/.test(line)), 'DELIVERY_ARTIFACT_TITLE_INVALID', 'Setext H1 headings are not allowed')
  invariant(!/<\s*\/?\s*h1(?:[\s\/>])/i.test(contractLines.join('\n')), 'DELIVERY_ARTIFACT_TITLE_INVALID', 'Raw HTML H1 headings are not allowed')

  const afterTitle = contractLines.slice(firstContentIndex + 1).filter((line) => line.length > 0)
  if (contract.summaryLabels.length > 0) {
    invariant(afterTitle.length >= contract.summaryLabels.length, 'DELIVERY_SUMMARY_REQUIRED')
    for (let index = 0; index < contract.summaryLabels.length; index += 1) {
      const label = contract.summaryLabels[index]
      const line = afterTitle[index]
      invariant(line.startsWith(label) && line.slice(label.length).trim().length > 0, 'DELIVERY_SUMMARY_INVALID')
      invariant(contractLines.filter((candidate) => candidate.startsWith(label)).length === 1, 'DELIVERY_SUMMARY_INVALID')
    }
  } else {
    invariant(!STANDARD_DELIVERY_SUMMARY_LABELS.some((label) => contractLines.some((line) => line.startsWith(label))), 'DELIVERY_QUICK_SUMMARY_FORBIDDEN')
  }
  invariant(afterTitle[contract.summaryLabels.length] === contract.sectionHeadings[0], 'DELIVERY_SECTION_PREAMBLE_FORBIDDEN', 'The first canonical section must immediately follow the title or required summary')

  const sectionHeadings = contractLines.filter((line) => /^[一二三四五六七八九十]+、/.test(line))
  invariant(sectionHeadings.length >= contract.sectionHeadings.length, 'DELIVERY_REQUIRED_SECTION_MISSING', 'Artifact is missing a canonical numbered section')
  invariant(sectionHeadings.length === contract.sectionHeadings.length, 'DELIVERY_SECTION_COUNT_INVALID', 'Artifact contains an extra numbered section', { expectedCount: contract.sectionHeadings.length, actualCount: sectionHeadings.length })
  invariant(sectionHeadings.every((line, index) => line === contract.sectionHeadings[index]), 'DELIVERY_SECTION_ORDER_INVALID', 'Artifact numbered section titles or order do not match the canonical contract')
  return {
    artifactType,
    canonicalTitle: contract.title,
    summaryLabels: [...contract.summaryLabels],
    sectionHeadings: [...contract.sectionHeadings],
    requiredSections: [...contract.requiredSections],
  }
}

async function validateDeliveryEventBinding(paths, runId, collection, collectionPayloadHash, artifactSha256) {
  const events = await readEvents(paths, runId)
  const verified = verifyEvents(events, sha256(runId))
  const sameSeatScope = (event, status) => event.metadata?.agendaItemId === status.agendaItemId
    && event.metadata?.seatId === status.seatId
    && event.metadata?.revision === status.revision
  invariant(events.some((event) => event.eventType === 'plan.frozen'
    && event.metadata?.revision === collection.planRevision
    && event.payloadHash === collection.planPayloadHash), 'DELIVERY_PLAN_EVENT_BINDING_MISSING', 'The frozen plan event does not bind the exact plan collected for delivery', { revision: collection.planRevision, planPayloadHash: collection.planPayloadHash })
  for (const status of collection.statuses) {
    invariant(typeof status.taskPayloadHash === 'string' && HEX_64.test(status.taskPayloadHash), 'DELIVERY_TASK_HASH_INVALID', 'Every collected task must carry its exact durable byte hash', { agendaItemId: status.agendaItemId, seatId: status.seatId, revision: status.revision })
    const dispatchRequested = events.some((event) => event.eventType === 'seat.dispatch_requested'
      && sameSeatScope(event, status) && event.payloadHash === status.taskPayloadHash)
    const dispatched = events.some((event) => event.eventType === 'seat.dispatched'
      && sameSeatScope(event, status) && event.payloadHash === status.taskPayloadHash)
    const dispatchFailed = events.some((event) => event.eventType === 'seat.dispatch_failed'
      && sameSeatScope(event, status) && event.payloadHash === status.taskPayloadHash)
    invariant(dispatchRequested && (dispatched || dispatchFailed), 'DELIVERY_TASK_EVENT_BINDING_MISSING', 'The current task bytes are not bound through request and dispatch-resolution events', { agendaItemId: status.agendaItemId, seatId: status.seatId, revision: status.revision, taskPayloadHash: status.taskPayloadHash })
    if (status.status === 'accepted') {
      invariant(dispatched, 'DELIVERY_ACCEPTED_TASK_NOT_DISPATCHED', 'An accepted result requires a successful dispatch bound to the same task bytes', { agendaItemId: status.agendaItemId, seatId: status.seatId, revision: status.revision })
      const matching = events.some((event) => ['seat.result_received', 'seat.result_recovered'].includes(event.eventType)
        && sameSeatScope(event, status) && event.payloadHash === status.resultPayloadHash)
      invariant(matching, 'DELIVERY_RESULT_EVENT_BINDING_MISSING', 'Accepted result is not bound into the verified event chain', { agendaItemId: status.agendaItemId, seatId: status.seatId, revision: status.revision })
    } else if (status.status === 'unavailable_after_retry') {
      const matching = events.some((event) => event.eventType === 'seat.result_failed'
        && sameSeatScope(event, status) && event.payloadHash === status.failurePayloadHash)
      invariant(matching, 'DELIVERY_FAILURE_EVENT_BINDING_MISSING', 'Failure-after-retry is not bound into the verified event chain', { agendaItemId: status.agendaItemId, seatId: status.seatId, revision: status.revision })
    }
  }
  const agendaIds = [...new Set(collection.statuses.map((status) => status.agendaItemId))]
  const unsealedAgendaIds = agendaIds.filter((agendaItemId) => !events.some((event) => event.eventType === 'round.independent_sealed'
    && event.metadata?.agendaItemId === agendaItemId && event.metadata?.revision === collection.planRevision))
  invariant(unsealedAgendaIds.length === 0, 'DELIVERY_ROUND_EVENT_BINDING_MISSING', 'Every collected agenda must have an exact-revision seal', { unsealedAgendaIds, revision: collection.planRevision })
  invariant(events.some((event) => event.eventType === 'collection.ready' && event.metadata?.revision === collection.planRevision && event.payloadHash === collectionPayloadHash), 'DELIVERY_COLLECTION_EVENT_BINDING_MISSING')
  invariant(events.some((event) => event.eventType === 'memo.compiled' && event.metadata?.revision === collection.planRevision && event.payloadHash === artifactSha256), 'DELIVERY_ARTIFACT_EVENT_BINDING_MISSING')
  return { eventCount: verified.count, chainHead: verified.chainHead, taskBindingCount: collection.statuses.length, binding: 'plan_task_result_or_failure_collection_and_artifact_hashes' }
}

export async function prepareDelivery({ workspaceRoot, runId, artifactPath, artifactType }) {
  await requireWritableWorkspace(workspaceRoot)
  const { collection, collectionPayloadHash } = await collectReviewRun({ workspaceRoot, runId })
  invariant(collection.readyForSynthesis, 'DELIVERY_COLLECTION_NOT_READY', 'Every selected specialist must have an accepted result or an explicit failure after one retry, and at least one professional result must remain')
  const expectedType = collection.reviewMode === 'quick_review' ? 'quick_review_card' : collection.reviewMode === 'deep_review' ? 'deep_review_preparation_card' : 'review_memo'
  invariant(artifactType === expectedType, 'DELIVERY_ARTIFACT_TYPE_INVALID', 'Artifact type must match the confirmed review mode', { expected: expectedType, actual: artifactType })
  const paths = workspacePaths(workspaceRoot, runId)
  const resolvedArtifact = path.resolve(artifactPath)
  ensureWithin(paths.deliverables, resolvedArtifact)
  await rejectExistingLinkSegments(paths.root, resolvedArtifact, 'DELIVERY_ARTIFACT_LINK_FORBIDDEN')
  await requireRegularFileNoLink(resolvedArtifact, 'DELIVERY_ARTIFACT_FILE_INVALID')
  const content = await readFile(resolvedArtifact, 'utf8')
  invariant(content.trim().length >= 80, 'DELIVERY_ARTIFACT_TOO_SHORT')
  const { requiredSections } = validateDeliveryArtifactStructure(content, artifactType)
  const artifactSha256 = sha256(content)
  const workspaceMarker = await readWorkspace(workspaceRoot)
  const claimEvidence = await requireClaimEvidenceIndex(paths, workspaceMarker, runId, artifactSha256, content)
  const eventBinding = await validateDeliveryEventBinding(paths, runId, collection, collectionPayloadHash, artifactSha256)
  const relativeArtifactPath = path.relative(paths.root, resolvedArtifact).replaceAll('\\', '/')
  const acceptedSeatIds = [...new Set(collection.statuses.filter((item) => item.status === 'accepted').map((item) => item.seatId))]
  const unavailableSeatIds = [...new Set(collection.statuses.filter((item) => item.status === 'unavailable_after_retry').map((item) => item.seatId))]
  const delivery = {
    schema: DELIVERY_SCHEMA,
    runId,
    artifactType,
    artifactRelativePath: relativeArtifactPath,
    artifactSha256,
    collectionPayloadHash,
    planPayloadHash: collection.planPayloadHash,
    planRevision: collection.planRevision,
    taskPayloadHashes: collection.statuses.map(({ agendaItemId, seatId, revision, taskPayloadHash }) => ({ agendaItemId, seatId, revision, taskPayloadHash })),
    acceptedSeatIds,
    unavailableSeatIds,
    qualityGate: { requiredSections, structuralChecksPassed: true, semanticSpcbgReviewStillHumanRequired: true },
    claimEvidence,
    eventBinding,
    state: 'ready_to_present',
    release: { packageId: PACKAGE_ID, productVersion: WORKSPACE_PRODUCT_VERSION },
    evidenceBoundary: 'local_artifact_structure_integrity_collection_and_event_hash_binding_only_not_semantic_spcbg_quality_host_presentation_user_acceptance_official_listing_or_product_credit',
  }
  await rejectExistingLinkSegments(paths.root, paths.deliveryFile, 'DELIVERY_OUTPUT_LINK_FORBIDDEN')
  await mkdir(paths.deliveries, { recursive: true })
  await rejectExistingLinkSegments(paths.root, paths.deliveryFile, 'DELIVERY_OUTPUT_LINK_FORBIDDEN')
  await writeAtomic(paths.deliveryFile, `${JSON.stringify(delivery, null, 2)}\n`)
  return { delivery, deliveryFile: paths.deliveryFile, artifactPath: resolvedArtifact }
}

function parseCanonicalCheckpoint(raw, runId) {
  let checkpoint
  try { checkpoint = JSON.parse(raw) }
  catch { throw new BoardContractError('CHECKPOINT_INVALID') }
  invariant(isObject(checkpoint), 'CHECKPOINT_INVALID')
  assertExactKeys(checkpoint, CHECKPOINT_KEYS, 'CHECKPOINT_FIELD_FORBIDDEN')
  assertRequiredKeys(checkpoint, [...CHECKPOINT_KEYS], 'CHECKPOINT_FIELD_REQUIRED')
  invariant(checkpoint.schema === 'fbsir.board-checkpoint/v1', 'CHECKPOINT_SCHEMA_INVALID')
  invariant(checkpoint.runIdHash === sha256(runId), 'CHECKPOINT_RUN_MISMATCH')
  safeId(checkpoint.state, 'CHECKPOINT_STATE_INVALID')
  invariant(Number.isInteger(checkpoint.eventCount) && checkpoint.eventCount >= 1, 'CHECKPOINT_EVENT_COUNT_MISMATCH')
  invariant(typeof checkpoint.chainHead === 'string' && HEX_64.test(checkpoint.chainHead), 'CHECKPOINT_CHAIN_HEAD_MISMATCH')
  invariant(Number.isFinite(Date.parse(checkpoint.createdAt)), 'CHECKPOINT_TIME_INVALID')
  assertExactKeys(checkpoint.release, new Set(['packageId', 'productVersion']), 'CHECKPOINT_RELEASE_FIELD_FORBIDDEN')
  invariant(checkpoint.release.packageId === PACKAGE_ID && checkpoint.release.productVersion === WORKSPACE_PRODUCT_VERSION, 'CHECKPOINT_RELEASE_INVALID')
  invariant(raw === `${JSON.stringify(checkpoint, null, 2)}\n`, 'CHECKPOINT_CANONICAL_BYTES_REQUIRED')
  return checkpoint
}

async function createCheckpointUnlocked({ workspaceRoot, runId, actorId, state }) {
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  safeId(state, 'CHECKPOINT_STATE_INVALID')
  const marker = await requireWritableWorkspace(workspaceRoot)
  const paths = workspacePaths(workspaceRoot, runId)
  const events = await readEvents(paths, runId, marker)
  const ledger = verifyEvents(events, sha256(runId), workspaceScopeHash(marker))
  const checkpointEvent = events.at(-1)
  invariant(checkpointEvent?.eventType === 'checkpoint.created' && checkpointEvent.metadata?.state === state, 'CHECKPOINT_EVENT_BINDING_REQUIRED', 'A checkpoint must bind the latest checkpoint.created event and its exact state')
  await rejectExistingLinkSegments(paths.root, paths.checkpointFile, 'CHECKPOINT_LINK_FORBIDDEN')
  await mkdir(paths.checkpoints, { recursive: true })
  await rejectExistingLinkSegments(paths.root, paths.checkpointFile, 'CHECKPOINT_LINK_FORBIDDEN')
  if (await pathExists(paths.checkpointFile)) {
    await requireRegularFileNoLink(paths.checkpointFile, 'CHECKPOINT_REQUIRED')
    const info = await lstat(paths.checkpointFile)
    invariant(info.size <= MAX_CHECKPOINT_BYTES, 'CHECKPOINT_SIZE_LIMIT_EXCEEDED')
    const raw = await readFile(paths.checkpointFile, 'utf8')
    const existing = parseCanonicalCheckpoint(raw, runId)
    if (existing.eventCount === ledger.count && existing.chainHead === ledger.chainHead) {
      invariant(existing.state === state, 'CHECKPOINT_BINDING_CONFLICT')
      return { ...existing, checkpointReceiptDigest: sha256(existing), checkpointFile: paths.checkpointFile }
    }
    const priorEvent = events[existing.eventCount - 1]
    invariant(existing.eventCount < ledger.count
      && priorEvent?.eventHash === existing.chainHead
      && priorEvent.eventType === 'checkpoint.created'
      && priorEvent.metadata?.state === existing.state, 'CHECKPOINT_BINDING_CONFLICT')
  }
  const checkpoint = {
    schema: 'fbsir.board-checkpoint/v1',
    runIdHash: sha256(runId),
    state,
    eventCount: ledger.count,
    chainHead: ledger.chainHead,
    createdAt: new Date().toISOString(),
    release: { packageId: PACKAGE_ID, productVersion: WORKSPACE_PRODUCT_VERSION },
  }
  await writeAtomic(paths.checkpointFile, `${JSON.stringify(checkpoint, null, 2)}\n`)
  return { ...checkpoint, checkpointReceiptDigest: sha256(checkpoint), checkpointFile: paths.checkpointFile }
}

async function readIdempotentCheckpointReceipt({ workspaceRoot, runId, state }) {
  const marker = await requireWritableWorkspace(workspaceRoot)
  const paths = workspacePaths(workspaceRoot, runId)
  const events = await readEvents(paths, runId, marker)
  const ledger = verifyEvents(events, sha256(runId), workspaceScopeHash(marker))
  const checkpointEvent = events.at(-1)
  invariant(checkpointEvent?.eventType === 'checkpoint.created' && checkpointEvent.metadata?.state === state, 'CHECKPOINT_EVENT_BINDING_REQUIRED')
  await rejectExistingLinkSegments(paths.root, paths.checkpointFile, 'CHECKPOINT_LINK_FORBIDDEN')
  if (!(await pathExists(paths.checkpointFile))) return null
  await requireRegularFileNoLink(paths.checkpointFile, 'CHECKPOINT_REQUIRED')
  const info = await lstat(paths.checkpointFile)
  invariant(info.size <= MAX_CHECKPOINT_BYTES, 'CHECKPOINT_SIZE_LIMIT_EXCEEDED')
  const raw = await readFile(paths.checkpointFile, 'utf8')
  const existing = parseCanonicalCheckpoint(raw, runId)
  if (existing.eventCount === ledger.count && existing.chainHead === ledger.chainHead) {
    invariant(existing.state === state, 'CHECKPOINT_BINDING_CONFLICT')
    return { ...existing, checkpointReceiptDigest: sha256(existing), checkpointFile: paths.checkpointFile }
  }
  const priorEvent = events[existing.eventCount - 1]
  invariant(existing.eventCount < ledger.count
    && priorEvent?.eventHash === existing.chainHead
    && priorEvent.eventType === 'checkpoint.created'
    && priorEvent.metadata?.state === existing.state, 'CHECKPOINT_BINDING_CONFLICT')
  return null
}

export async function createCheckpoint(input) {
  invariant(isObject(input), 'CHECKPOINT_INPUT_INVALID')
  assertExactKeys(input, CHECKPOINT_INPUT_KEYS, 'CHECKPOINT_INPUT_FIELD_FORBIDDEN')
  assertRequiredKeys(input, CHECKPOINT_INPUT_KEY_LIST, 'CHECKPOINT_INPUT_FIELD_REQUIRED')
  invariant(input.actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  const paths = workspacePaths(input.workspaceRoot, input.runId)
  const existing = await readIdempotentCheckpointReceipt(input)
  if (existing) return existing
  const lock = await acquireLock(paths.lockFile, 15_000)
  try {
    return await createCheckpointUnlocked(input)
  } finally {
    await releaseLock(lock, paths.lockFile)
  }
}

function orderedResumeIds(values, order, allowed, code) {
  assertDenseDataArray(values, order.length, code, code)
  const unique = new Set()
  let previousIndex = -1
  return Array.from(values, (value) => {
    invariant(typeof value === 'string' && allowed.has(value), code)
    invariant(!unique.has(value), code)
    const index = order.indexOf(value)
    invariant(index > previousIndex, code)
    unique.add(value)
    previousIndex = index
    return value
  })
}

function expectedResumePresentation(evidenceState) {
  if (evidenceState === 'verified_current_checkpoint') return 'current_resume_card'
  if (evidenceState === 'verified_predecessor_resume_digest') return 'predecessor_read_only_resume_card'
  if (evidenceState === 'verified_legacy_resume_digest') return 'legacy_read_only_resume_card'
  return 'resume_evidence_insufficient_card'
}

function expectedResumeOpenGates(evidenceState, materialGate, actionEnabled = true, observedMilestoneIds = []) {
  if (evidenceState === 'missing') return ['source_receipt_required']
  if (['unsupported', 'receipt_mismatch', 'source_changed'].includes(evidenceState)) return ['source_unsupported_or_changed']
  if (evidenceState === 'verified_predecessor_resume_digest') {
    return [
      ...(actionEnabled ? ['explicit_resume_confirmation_required', 'new_run_binding_required'] : ['resume_action_not_presented']),
      'human_review_required', 'predecessor_content_truth_unverified',
    ]
  }
  if (evidenceState === 'verified_legacy_resume_digest') {
    return [
      ...(actionEnabled ? ['explicit_resume_confirmation_required', 'new_run_binding_required'] : ['resume_action_not_presented']),
      'human_review_required', 'legacy_content_truth_unverified',
    ]
  }
  const terminal = observedMilestoneIds.includes('run_terminal_event_observed')
  return [
    ...(terminal
      ? ['resume_action_not_presented', 'run_terminal_no_same_run_resume']
      : actionEnabled ? ['explicit_resume_confirmation_required'] : ['resume_action_not_presented']),
    'material_status_not_bound',
    'human_review_required',
  ]
}

export function validateCaseResumeCard(input) {
  invariant(isObject(input), 'RESUME_CARD_REQUIRED')
  assertExactKeys(input, CASE_RESUME_CARD_KEYS, 'RESUME_CARD_FIELD_FORBIDDEN')
  assertRequiredKeys(input, CASE_RESUME_CARD_KEY_LIST, 'RESUME_CARD_FIELD_REQUIRED')
  invariant(input.schema === CASE_RESUME_CARD_SCHEMA, 'RESUME_CARD_SCHEMA_INVALID')
  invariant(CASE_RESUME_PRESENTATION_STATES.has(input.presentationState), 'RESUME_CARD_PRESENTATION_STATE_INVALID')
  invariant(['current_read_write', 'predecessor_read_only', 'legacy_read_only', 'unsupported'].includes(input.accessMode), 'RESUME_CARD_ACCESS_MODE_INVALID')
  invariant(CASE_RESUME_EVIDENCE_STATES.has(input.evidenceState), 'RESUME_CARD_EVIDENCE_STATE_INVALID')
  if (input.evidenceState === 'verified_current_checkpoint') invariant(input.accessMode === 'current_read_write', 'RESUME_CARD_EVIDENCE_STATE_INVALID')
  if (input.evidenceState === 'verified_predecessor_resume_digest') invariant(input.accessMode === 'predecessor_read_only', 'RESUME_CARD_EVIDENCE_STATE_INVALID')
  if (input.evidenceState === 'verified_legacy_resume_digest') invariant(input.accessMode === 'legacy_read_only', 'RESUME_CARD_EVIDENCE_STATE_INVALID')
  if (input.evidenceState === 'missing' || input.evidenceState === 'unsupported') invariant(input.accessMode === 'unsupported', 'RESUME_CARD_EVIDENCE_STATE_INVALID')
  if (input.evidenceState === 'receipt_mismatch') invariant(['current_read_write', 'predecessor_read_only', 'legacy_read_only'].includes(input.accessMode), 'RESUME_CARD_EVIDENCE_STATE_INVALID')
  invariant(input.presentationState === expectedResumePresentation(input.evidenceState), 'RESUME_CARD_PRESENTATION_STATE_INVALID')

  invariant(isObject(input.source), 'RESUME_CARD_SOURCE_INVALID')
  assertExactKeys(input.source, CASE_RESUME_SOURCE_KEYS, 'RESUME_CARD_SOURCE_FIELD_FORBIDDEN')
  assertRequiredKeys(input.source, [...CASE_RESUME_SOURCE_KEYS], 'RESUME_CARD_SOURCE_FIELD_REQUIRED')
  const expectedSource = input.evidenceState === 'verified_current_checkpoint'
    ? 'current_checkpoint'
    : input.evidenceState === 'verified_predecessor_resume_digest'
      ? 'predecessor_resume_digest'
    : input.evidenceState === 'verified_legacy_resume_digest'
      ? 'legacy_resume_digest'
      : 'none'
  invariant(input.source.receiptType === expectedSource, 'RESUME_CARD_SOURCE_INVALID')
  if (expectedSource === 'none') {
    invariant(input.source.runIdHash === null && input.source.receiptDigest === null, 'RESUME_CARD_SOURCE_INVALID')
  } else {
    invariant(typeof input.source.runIdHash === 'string' && HEX_64.test(input.source.runIdHash), 'RESUME_CARD_SOURCE_INVALID')
    invariant(typeof input.source.receiptDigest === 'string' && HEX_64.test(input.source.receiptDigest), 'RESUME_CARD_SOURCE_INVALID')
  }

  const observedMilestoneIds = orderedResumeIds(input.observedMilestoneIds, CASE_RESUME_MILESTONE_ORDER, CASE_RESUME_MILESTONE_IDS, 'RESUME_CARD_MILESTONES_INVALID')
  const evidenceBindingIds = orderedResumeIds(input.evidenceBindingIds, CASE_RESUME_EVIDENCE_BINDING_ORDER, CASE_RESUME_EVIDENCE_BINDING_IDS, 'RESUME_CARD_EVIDENCE_BINDINGS_INVALID')
  const openGateIds = orderedResumeIds(input.openGateIds, CASE_RESUME_OPEN_GATE_ORDER, CASE_RESUME_OPEN_GATE_IDS, 'RESUME_CARD_OPEN_GATES_INVALID')
  if (input.evidenceState !== 'verified_current_checkpoint') invariant(observedMilestoneIds.length === 0, 'RESUME_CARD_MILESTONES_INVALID')
  if (input.evidenceState === 'verified_current_checkpoint') invariant(evidenceBindingIds.length === 1 && evidenceBindingIds[0] === 'current_checkpoint_bound', 'RESUME_CARD_EVIDENCE_BINDINGS_INVALID')
  if (input.evidenceState === 'verified_predecessor_resume_digest') invariant(evidenceBindingIds.length >= 4 && evidenceBindingIds.every((value) => value.startsWith('predecessor_')), 'RESUME_CARD_EVIDENCE_BINDINGS_INVALID')
  if (input.evidenceState === 'verified_legacy_resume_digest') invariant(evidenceBindingIds.length >= 4 && evidenceBindingIds.every((value) => value.startsWith('legacy_')), 'RESUME_CARD_EVIDENCE_BINDINGS_INVALID')
  if (!input.evidenceState.startsWith('verified_')) invariant(evidenceBindingIds.length === 0, 'RESUME_CARD_EVIDENCE_BINDINGS_INVALID')

  invariant(isObject(input.materialGate), 'RESUME_CARD_MATERIAL_GATE_INVALID')
  assertExactKeys(input.materialGate, CASE_RESUME_MATERIAL_GATE_KEYS, 'RESUME_CARD_MATERIAL_GATE_FIELD_FORBIDDEN')
  assertRequiredKeys(input.materialGate, [...CASE_RESUME_MATERIAL_GATE_KEYS], 'RESUME_CARD_MATERIAL_GATE_FIELD_REQUIRED')
  invariant(CASE_RESUME_MATERIAL_STATES.has(input.materialGate.state), 'RESUME_CARD_MATERIAL_GATE_INVALID')
  const materialCountsKnown = MATERIAL_STATES.has(input.materialGate.state)
  if (materialCountsKnown) {
    invariant(Number.isInteger(input.materialGate.missingCount) && input.materialGate.missingCount >= 0 && input.materialGate.missingCount <= 32, 'RESUME_CARD_MATERIAL_GATE_INVALID')
    invariant(Number.isInteger(input.materialGate.pendingVerificationCount) && input.materialGate.pendingVerificationCount >= 0 && input.materialGate.pendingVerificationCount <= 64, 'RESUME_CARD_MATERIAL_GATE_INVALID')
  } else {
    invariant(input.materialGate.missingCount === null && input.materialGate.pendingVerificationCount === null, 'RESUME_CARD_MATERIAL_GATE_INVALID')
  }
  if (input.evidenceState === 'verified_predecessor_resume_digest') invariant(input.materialGate.state === 'not_available_from_predecessor_digest', 'RESUME_CARD_MATERIAL_GATE_INVALID')
  if (input.evidenceState === 'verified_legacy_resume_digest') invariant(input.materialGate.state === 'not_available_from_legacy_digest', 'RESUME_CARD_MATERIAL_GATE_INVALID')
  if (!input.evidenceState.startsWith('verified_')) invariant(input.materialGate.state === 'no_verified_evidence', 'RESUME_CARD_MATERIAL_GATE_INVALID')
  if (input.evidenceState === 'verified_current_checkpoint') invariant(input.materialGate.state === 'not_bound_by_checkpoint'
    && input.materialGate.missingCount === null
    && input.materialGate.pendingVerificationCount === null, 'RESUME_CARD_MATERIAL_GATE_INVALID')
  invariant(isObject(input.nextAction), 'RESUME_CARD_NEXT_ACTION_INVALID')
  assertExactKeys(input.nextAction, CASE_RESUME_NEXT_ACTION_KEYS, 'RESUME_CARD_NEXT_ACTION_FIELD_FORBIDDEN')
  assertRequiredKeys(input.nextAction, [...CASE_RESUME_NEXT_ACTION_KEYS], 'RESUME_CARD_NEXT_ACTION_FIELD_REQUIRED')
  const expectedResumeSource = input.evidenceState === 'verified_current_checkpoint'
    ? 'current_checkpoint'
    : input.evidenceState === 'verified_predecessor_resume_digest'
      ? 'predecessor_read_only'
    : input.evidenceState === 'verified_legacy_resume_digest'
      ? 'legacy_read_only'
      : null
  if (!input.evidenceState.startsWith('verified_')) {
    invariant(input.nextAction.actionId === null
      && input.nextAction.approvalState === 'not_available'
      && input.nextAction.resumeSource === null
      && input.nextAction.targetRunRequired === false, 'RESUME_CARD_NEXT_ACTION_INVALID')
  } else {
    const enabled = input.nextAction.actionId === 'resume_case'
    invariant(input.nextAction.resumeSource === expectedResumeSource, 'RESUME_CARD_NEXT_ACTION_INVALID')
    if (enabled) {
      invariant(input.nextAction.approvalState === 'required' && input.nextAction.targetRunRequired === true, 'RESUME_CARD_NEXT_ACTION_INVALID')
    } else {
      invariant(input.nextAction.actionId === null
        && input.nextAction.approvalState === 'not_available'
        && input.nextAction.targetRunRequired === false, 'RESUME_CARD_NEXT_ACTION_INVALID')
    }
  }
  const actionEnabled = input.nextAction.actionId === 'resume_case'
  invariant(sha256(openGateIds) === sha256(expectedResumeOpenGates(input.evidenceState, input.materialGate, actionEnabled, observedMilestoneIds)), 'RESUME_CARD_OPEN_GATES_INVALID')

  invariant(isObject(input.responsibility), 'RESUME_CARD_RESPONSIBILITY_INVALID')
  assertExactKeys(input.responsibility, CASE_RESUME_RESPONSIBILITY_KEYS, 'RESUME_CARD_RESPONSIBILITY_FIELD_FORBIDDEN')
  assertRequiredKeys(input.responsibility, [...CASE_RESUME_RESPONSIBILITY_KEYS], 'RESUME_CARD_RESPONSIBILITY_FIELD_REQUIRED')
  invariant(input.responsibility.ownerStatus === 'not_present_in_receipt'
    && input.responsibility.dueAt === null
    && input.responsibility.reviewAt === null, 'RESUME_CARD_RESPONSIBILITY_INVALID')

  const expectedBoundary = input.evidenceState === 'verified_current_checkpoint'
    ? 'current_checkpoint_chain_only_no_body_semantics_or_execution_claim'
    : input.evidenceState === 'verified_predecessor_resume_digest'
      ? 'predecessor_history_only_new_26_8_10_run_required'
    : input.evidenceState === 'verified_legacy_resume_digest'
      ? 'legacy_history_only_new_26_8_10_run_required'
      : 'no_recovery_claim'
  invariant(input.recoveryBoundary === expectedBoundary, 'RESUME_CARD_RECOVERY_BOUNDARY_INVALID')
  invariant(input.contentIncluded === false, 'RESUME_CARD_CONTENT_INCLUDED_FORBIDDEN')
  invariant(input.writesPerformed === false, 'RESUME_CARD_WRITES_FORBIDDEN')
  invariant(input.evidenceBoundary === CASE_RESUME_CARD_EVIDENCE_BOUNDARY, 'RESUME_CARD_EVIDENCE_BOUNDARY_INVALID')
  return {
    schema: CASE_RESUME_CARD_SCHEMA,
    presentationState: input.presentationState,
    accessMode: input.accessMode,
    evidenceState: input.evidenceState,
    source: { ...input.source },
    observedMilestoneIds,
    evidenceBindingIds,
    openGateIds,
    materialGate: { ...input.materialGate },
    nextAction: { ...input.nextAction },
    responsibility: { ...input.responsibility },
    recoveryBoundary: input.recoveryBoundary,
    contentIncluded: false,
    writesPerformed: false,
    evidenceBoundary: CASE_RESUME_CARD_EVIDENCE_BOUNDARY,
  }
}

function insufficientResumeCard(evidenceState = 'missing', accessMode = 'unsupported') {
  return validateCaseResumeCard({
    schema: CASE_RESUME_CARD_SCHEMA,
    presentationState: 'resume_evidence_insufficient_card',
    accessMode,
    evidenceState,
    source: { receiptType: 'none', runIdHash: null, receiptDigest: null },
    observedMilestoneIds: [],
    evidenceBindingIds: [],
    openGateIds: expectedResumeOpenGates(evidenceState, { missingCount: null, pendingVerificationCount: null }),
    materialGate: { state: 'no_verified_evidence', missingCount: null, pendingVerificationCount: null },
    nextAction: { actionId: null, approvalState: 'not_available', resumeSource: null, targetRunRequired: false },
    responsibility: { ownerStatus: 'not_present_in_receipt', dueAt: null, reviewAt: null },
    recoveryBoundary: 'no_recovery_claim',
    contentIncluded: false,
    writesPerformed: false,
    evidenceBoundary: CASE_RESUME_CARD_EVIDENCE_BOUNDARY,
  })
}

export function suppressCaseResumeActionPresentation(input) {
  const card = validateCaseResumeCard(input)
  if (!card.evidenceState.startsWith('verified_') || card.nextAction.actionId === null) return card
  return validateCaseResumeCard({
    ...card,
    openGateIds: expectedResumeOpenGates(card.evidenceState, card.materialGate, false, card.observedMilestoneIds),
    nextAction: {
      actionId: null,
      approvalState: 'not_available',
      resumeSource: card.nextAction.resumeSource,
      targetRunRequired: false,
    },
  })
}

function currentObservedMilestoneIds(events) {
  const types = new Set(events.map((event) => event.eventType))
  const includesAny = (...eventTypes) => eventTypes.some((eventType) => types.has(eventType))
  const candidates = [
    ['meeting_opened_event_observed', types.has('meeting.opened')],
    ['agenda_registered_event_observed', types.has('agenda.registered')],
    ['plan_frozen_event_observed', types.has('plan.frozen')],
    ['team_creation_terminal_event_observed', includesAny('team.created', 'team.create_failed')],
    ['seat_selection_event_observed', types.has('seat.selected')],
    ['seat_dispatch_terminal_event_observed', includesAny('seat.dispatched', 'seat.dispatch_failed')],
    ['seat_result_terminal_event_observed', includesAny('seat.result_received', 'seat.result_recovered', 'seat.result_failed')],
    ['round_sealed_event_observed', types.has('round.independent_sealed')],
    ['collection_ready_event_observed', types.has('collection.ready')],
    ['memo_compiled_event_observed', types.has('memo.compiled')],
    ['artifact_presented_event_observed', types.has('artifact.presented')],
    ['user_confirmation_event_observed', types.has('user.confirmed')],
    ['run_terminal_event_observed', includesAny('run.failed', 'run.stopped')],
    ['checkpoint_event_observed', types.has('checkpoint.created')],
  ]
  return candidates.filter(([, present]) => present).map(([nodeId]) => nodeId)
}

async function buildCurrentResumeCard(workspaceRoot, runId, expectedReceiptDigest, marker) {
  const paths = workspacePaths(workspaceRoot, runId)
  const events = await readEvents(paths, runId, marker)
  const checkpointEvent = events.at(-1)
  await rejectExistingLinkSegments(paths.root, paths.checkpointFile, 'CHECKPOINT_LINK_FORBIDDEN')
  await requireRegularFileNoLink(paths.checkpointFile, 'CHECKPOINT_REQUIRED')
  const checkpointStat = await lstat(paths.checkpointFile)
  invariant(checkpointStat.size <= MAX_CHECKPOINT_BYTES, 'CHECKPOINT_SIZE_LIMIT_EXCEEDED')
  const raw = await readFile(paths.checkpointFile, 'utf8')
  const checkpoint = parseCanonicalCheckpoint(raw, runId)
  invariant(Number.isInteger(checkpoint.eventCount) && checkpoint.eventCount === events.length, 'CHECKPOINT_EVENT_COUNT_MISMATCH')
  const chainHead = events.at(-1)?.eventHash || 'genesis'
  invariant(checkpoint.chainHead === chainHead, 'CHECKPOINT_CHAIN_HEAD_MISMATCH')
  invariant(checkpointEvent?.eventType === 'checkpoint.created' && checkpointEvent.metadata?.state === checkpoint.state, 'CHECKPOINT_EVENT_BINDING_REQUIRED')
  const receiptDigest = sha256(checkpoint)
  invariant(receiptDigest === expectedReceiptDigest, 'RESUME_RECEIPT_DIGEST_MISMATCH')

  const materialGate = { state: 'not_bound_by_checkpoint', missingCount: null, pendingVerificationCount: null }
  const observedMilestoneIds = currentObservedMilestoneIds(events)
  const terminal = observedMilestoneIds.includes('run_terminal_event_observed')
  return validateCaseResumeCard({
    schema: CASE_RESUME_CARD_SCHEMA,
    presentationState: 'current_resume_card',
    accessMode: 'current_read_write',
    evidenceState: 'verified_current_checkpoint',
    source: { receiptType: 'current_checkpoint', runIdHash: sha256(runId), receiptDigest },
    observedMilestoneIds,
    evidenceBindingIds: ['current_checkpoint_bound'],
    openGateIds: expectedResumeOpenGates('verified_current_checkpoint', materialGate, !terminal, observedMilestoneIds),
    materialGate,
    nextAction: terminal
      ? { actionId: null, approvalState: 'not_available', resumeSource: 'current_checkpoint', targetRunRequired: false }
      : { actionId: 'resume_case', approvalState: 'required', resumeSource: 'current_checkpoint', targetRunRequired: true },
    responsibility: { ownerStatus: 'not_present_in_receipt', dueAt: null, reviewAt: null },
    recoveryBoundary: 'current_checkpoint_chain_only_no_body_semantics_or_execution_claim',
    contentIncluded: false,
    writesPerformed: false,
    evidenceBoundary: CASE_RESUME_CARD_EVIDENCE_BOUNDARY,
  })
}

async function buildLegacyResumeCard(workspaceRoot, runId, expectedReceiptDigest) {
  const inspected = await inspectLegacyResume({ sourceWorkspaceRoot: workspaceRoot, sourceRunId: runId })
  invariant(inspected.digestReceipt.legacyResumeDigest === expectedReceiptDigest, 'RESUME_RECEIPT_DIGEST_MISMATCH')
  const bindings = inspected.digestReceipt.bindings
  const evidenceBindingIds = [
    'legacy_workspace_bound',
    'legacy_plan_bound',
    'legacy_event_chain_bound',
    ...(bindings.checkpointSha256 ? ['legacy_checkpoint_bound'] : []),
    ...(bindings.collectionSha256 ? ['legacy_collection_bound'] : []),
    ...(bindings.deliverySha256 ? ['legacy_delivery_bound'] : []),
    'legacy_deliverable_inventory_bound',
  ]
  return validateCaseResumeCard({
    schema: CASE_RESUME_CARD_SCHEMA,
    presentationState: 'legacy_read_only_resume_card',
    accessMode: 'legacy_read_only',
    evidenceState: 'verified_legacy_resume_digest',
    source: { receiptType: 'legacy_resume_digest', runIdHash: sha256(runId), receiptDigest: expectedReceiptDigest },
    observedMilestoneIds: [],
    evidenceBindingIds,
    openGateIds: expectedResumeOpenGates('verified_legacy_resume_digest', { missingCount: null, pendingVerificationCount: null }),
    materialGate: { state: 'not_available_from_legacy_digest', missingCount: null, pendingVerificationCount: null },
    nextAction: { actionId: 'resume_case', approvalState: 'required', resumeSource: 'legacy_read_only', targetRunRequired: true },
    responsibility: { ownerStatus: 'not_present_in_receipt', dueAt: null, reviewAt: null },
    recoveryBoundary: 'legacy_history_only_new_26_8_10_run_required',
    contentIncluded: false,
    writesPerformed: false,
    evidenceBoundary: CASE_RESUME_CARD_EVIDENCE_BOUNDARY,
  })
}

async function buildPredecessorResumeCard(workspaceRoot, runId, expectedReceiptDigest) {
  const inspected = await inspectPredecessorResume({ sourceWorkspaceRoot: workspaceRoot, sourceRunId: runId })
  invariant(inspected.digestReceipt.schema === PREDECESSOR_RESUME_DIGEST_SCHEMA, 'PREDECESSOR_RESUME_RECEIPT_INVALID')
  invariant(inspected.digestReceipt.predecessorResumeDigest === expectedReceiptDigest, 'RESUME_RECEIPT_DIGEST_MISMATCH')
  const bindings = inspected.digestReceipt.bindings
  const evidenceBindingIds = [
    'predecessor_workspace_bound',
    'predecessor_plan_bound',
    'predecessor_event_chain_bound',
    ...(bindings.checkpointSha256 ? ['predecessor_checkpoint_bound'] : []),
    ...(bindings.collectionSha256 ? ['predecessor_collection_bound'] : []),
    ...(bindings.deliverySha256 ? ['predecessor_delivery_bound'] : []),
    'predecessor_deliverable_inventory_bound',
  ]
  const materialGate = { state: 'not_available_from_predecessor_digest', missingCount: null, pendingVerificationCount: null }
  return validateCaseResumeCard({
    schema: CASE_RESUME_CARD_SCHEMA,
    presentationState: 'predecessor_read_only_resume_card',
    accessMode: 'predecessor_read_only',
    evidenceState: 'verified_predecessor_resume_digest',
    source: { receiptType: 'predecessor_resume_digest', runIdHash: sha256(runId), receiptDigest: expectedReceiptDigest },
    observedMilestoneIds: [],
    evidenceBindingIds,
    openGateIds: expectedResumeOpenGates('verified_predecessor_resume_digest', materialGate),
    materialGate,
    nextAction: { actionId: 'resume_case', approvalState: 'required', resumeSource: 'predecessor_read_only', targetRunRequired: true },
    responsibility: { ownerStatus: 'not_present_in_receipt', dueAt: null, reviewAt: null },
    recoveryBoundary: 'predecessor_history_only_new_26_8_10_run_required',
    contentIncluded: false,
    writesPerformed: false,
    evidenceBoundary: CASE_RESUME_CARD_EVIDENCE_BOUNDARY,
  })
}

export async function buildCaseResumeCard(input) {
  const snapshot = snapshotTransportData(input, 'RESUME_CARD_INPUT_INVALID')
  const inputKeys = new Set(['workspaceRoot', 'runId', 'expectedReceiptDigest'])
  assertExactKeys(snapshot, inputKeys, 'RESUME_CARD_INPUT_FIELD_FORBIDDEN')
  assertRequiredKeys(snapshot, [...inputKeys], 'RESUME_CARD_INPUT_FIELD_REQUIRED')
  if (snapshot.workspaceRoot === null && snapshot.runId === null && snapshot.expectedReceiptDigest === null) return insufficientResumeCard('missing')
  if (typeof snapshot.workspaceRoot !== 'string' || !snapshot.workspaceRoot.trim()
    || typeof snapshot.runId !== 'string' || !RUN_ID_PATTERN.test(snapshot.runId)
    || typeof snapshot.expectedReceiptDigest !== 'string' || !HEX_64.test(snapshot.expectedReceiptDigest)) return insufficientResumeCard('missing')
  let accessMode = 'unsupported'
  try {
    const inspected = await inspectWorkspace(snapshot.workspaceRoot)
    accessMode = inspected.accessMode
    if (inspected.accessMode === 'current_read_write') {
      return await buildCurrentResumeCard(snapshot.workspaceRoot, snapshot.runId, snapshot.expectedReceiptDigest, inspected.marker)
    }
    if (inspected.accessMode === 'predecessor_read_only') {
      return await buildPredecessorResumeCard(snapshot.workspaceRoot, snapshot.runId, snapshot.expectedReceiptDigest)
    }
    if (inspected.accessMode === 'legacy_read_only') {
      return await buildLegacyResumeCard(snapshot.workspaceRoot, snapshot.runId, snapshot.expectedReceiptDigest)
    }
    return insufficientResumeCard('unsupported')
  } catch (error) {
    if (error instanceof BoardContractError) {
      const evidenceState = error.code === 'RESUME_RECEIPT_DIGEST_MISMATCH' ? 'receipt_mismatch' : 'source_changed'
      return insufficientResumeCard(evidenceState, accessMode)
    }
    throw error
  }
}

let lexiconCache = null
export async function loadSceneLexicon() {
  if (lexiconCache) return structuredClone(lexiconCache)
  const scriptDir = path.dirname(fileURLToPath(import.meta.url))
  const lexiconPath = path.resolve(scriptDir, '..', '..', 'references', 'scene-lexicon.v1.json')
  lexiconCache = JSON.parse(await readFile(lexiconPath, 'utf8'))
  invariant(lexiconCache.schema === 'fbsir.scene-lexicon/v1', 'SCENE_LEXICON_SCHEMA_INVALID')
  return structuredClone(lexiconCache)
}

export async function routeScene(text) {
  boundedText(text, 'scene_text', 12000)
  const lexicon = await loadSceneLexicon()
  const normalized = text.toLowerCase()
  const matches = lexicon.scenes.map((scene) => {
    const matchedTerms = scene.terms.filter((term) => normalized.includes(term.toLowerCase()))
    const negativeTerms = scene.negativeTerms.filter((term) => normalized.includes(term.toLowerCase()))
    return { sceneId: scene.sceneId, score: Math.max(0, matchedTerms.length - (negativeTerms.length * 2)), matchedTerms, negativeTerms, defaultMode: scene.defaultMode, candidateSeats: scene.candidateSeats }
  }).filter((match) => match.score > 0).sort((a, b) => b.score - a.score || a.sceneId.localeCompare(b.sceneId))
  return { schema: 'fbsir.scene-route-result/v1', matched: matches.length > 0, matches, evidenceBoundary: 'lexicon_hint_only_convener_must_confirm' }
}

export function publicCatalog() {
  return { eventTypes: Object.keys(EVENT_CATALOG), evidenceLevels: [...EVIDENCE_LEVELS], metadataKeys: [...METADATA_KEYS], writerId: WRITER_ID }
}
