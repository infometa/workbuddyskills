import { constants as fsConstants, readFileSync } from 'node:fs'
import { createHash, randomBytes, randomUUID } from 'node:crypto'
import { lstat, mkdir, open, readFile, readdir, rename, unlink, writeFile } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  BUNDLE_VERIFY_REQUEST_SCHEMA,
  isCognitiveAssetBundleRef,
  verifyCognitiveAssetBundle,
} from './cognitive-assets.mjs'

export const PACKAGE_ID = 'fbsir-eight-seat-board'
export const PRODUCT_VERSION = '26.7.20'
export const WORKSPACE_SCHEMA = 'fbsir.board-workspace/v1'
export const EVENT_SCHEMA = 'fbsir.board-event/v1'
export const SEAT_PROPOSAL_SCHEMA = 'fbsir.review-seat-proposal/v1'
export const PLAN_SCHEMA = 'fbsir.review-plan/v1'
export const TASK_SCHEMA = 'fbsir.member-task/v1'
export const RESULT_SCHEMA = 'fbsir.member-result/v1'
export const DELIVERY_OBSERVATION_SCHEMA = 'fbsir.member-delivery-observation/v1'
export const FAILURE_SCHEMA = 'fbsir.member-failure/v1'
export const COLLECTION_SCHEMA = 'fbsir.review-collection/v1'
export const DELIVERY_SCHEMA = 'fbsir.review-delivery/v1'

const RUN_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/
const HEX_64 = /^[0-9a-f]{64}$/
const WRITER_ID = 'board-convener'
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
const PLAN_KEYS = new Set([
  'schema', 'runId', 'revision', 'reviewMode', 'agendaItems', 'specialistSeatIds',
  'supportSeatIds', 'decisionCardHash', 'userConfirmed', 'confirmationReceiptId', 'singleNextAction',
])
const SEAT_PROPOSAL_KEYS = new Set(['schema', 'reviewMode', 'specialistSeatIds', 'supportSeatIds'])
const AGENDA_ITEM_KEYS = new Set(['agendaItemId', 'decisionQuestion'])
const RESULT_KEYS = new Set([
  'schema', 'runId', 'agendaItemId', 'seatId', 'taskClass', 'revision', 'stance',
  'confidence', 'conclusionReady', 'receiptId', 'evidenceRefs', 'sections',
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
  'collection.ready', 'memo.compiled',
])
const PROFESSIONAL_RESULT_SECTIONS = new Set(['judgement', 'conditions', 'failureConditions', 'humanGate', 'evidenceAssessment', 'dissent'])
const SUPPORT_RESULT_SECTIONS = new Set(['deliveryStatus', 'sourceLedger', 'artifactChecklist', 'capabilityStatus'])

export class BoardContractError extends Error {
  constructor(code, message, details = {}) {
    super(message)
    this.name = 'BoardContractError'
    this.code = code
    this.details = details
  }
}

function invariant(condition, code, message = code, details = {}) {
  if (!condition) throw new BoardContractError(code, message, details)
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
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
  invariant(unexpected.length === 0, code, 'Envelope or receipt contains undeclared fields', { unexpected })
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
  invariant(info.isFile() && !info.isSymbolicLink(), code, 'Workspace file must be a regular non-link file', { target })
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
  const tasks = path.join(root, 'tasks')
  const drafts = path.join(root, 'drafts')
  const results = path.join(root, 'results')
  const receipts = path.join(root, 'receipts')
  const failures = path.join(root, 'failures')
  const deliverables = path.join(root, 'deliverables')
  const result = { root, control, marker, events, checkpoints, locks, collections, deliveries, plans, tasks, drafts, results, receipts, failures, deliverables }
  if (runId !== null) {
    invariant(RUN_ID_PATTERN.test(runId), 'RUN_ID_INVALID')
    result.eventFile = path.join(events, `${runId}.jsonl`)
    result.lockFile = path.join(locks, `${runId}.lock`)
    result.checkpointFile = path.join(checkpoints, `${runId}.json`)
    result.collectionFile = path.join(collections, `${runId}.json`)
    result.deliveryFile = path.join(deliveries, `${runId}.json`)
    result.planFile = path.join(plans, `${runId}.json`)
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

  if (await pathExists(paths.marker)) return readWorkspace(workspaceRoot)
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
  await mkdir(paths.tasks, { recursive: true })
  await mkdir(paths.drafts, { recursive: true })
  await mkdir(paths.results, { recursive: true })
  await mkdir(paths.receipts, { recursive: true })
  await mkdir(paths.failures, { recursive: true })
  await mkdir(paths.deliverables, { recursive: true })
  const marker = {
    schema: WORKSPACE_SCHEMA,
    workspaceId,
    product: PACKAGE_ID,
    productVersion: PRODUCT_VERSION,
    privacyMode: 'local_default',
    contentExport: 'deny_by_default',
    telemetryExport: 'deny_by_default',
    sharedStateWriter: WRITER_ID,
    createdAt: new Date().toISOString(),
  }
  await writeAtomic(paths.marker, `${JSON.stringify(marker, null, 2)}\n`)
  await readWorkspace(workspaceRoot)
  return marker
}

export async function readWorkspace(workspaceRoot) {
  const paths = workspacePaths(workspaceRoot)
  await requireDirectoryNoLink(paths.root, 'WORKSPACE_ROOT_LINK_FORBIDDEN')
  for (const directory of [paths.control, paths.events, paths.checkpoints, paths.locks, paths.collections, paths.deliveries, paths.plans, paths.tasks, paths.drafts, paths.results, paths.receipts, paths.failures, paths.deliverables]) {
    await rejectExistingLinkSegments(paths.root, directory, 'WORKSPACE_DIRECTORY_LINK_FORBIDDEN')
    await requireDirectoryNoLink(directory, 'WORKSPACE_DIRECTORY_INVALID')
  }
  await rejectExistingLinkSegments(paths.root, paths.marker, 'WORKSPACE_MARKER_LINK_FORBIDDEN')
  await requireRegularFileNoLink(paths.marker, 'WORKSPACE_MARKER_INVALID')
  let marker
  try { marker = JSON.parse(await readFile(paths.marker, 'utf8')) }
  catch (error) { throw new BoardContractError('WORKSPACE_NOT_INITIALIZED', 'Initialize a dedicated board workspace first', { cause: error.message }) }
  invariant(marker.schema === WORKSPACE_SCHEMA, 'WORKSPACE_SCHEMA_INVALID')
  invariant(marker.product === PACKAGE_ID && marker.productVersion === PRODUCT_VERSION, 'WORKSPACE_RELEASE_MISMATCH')
  invariant(marker.sharedStateWriter === WRITER_ID, 'WORKSPACE_WRITER_INVALID')
  return marker
}

async function writeAtomic(target, content) {
  const temp = `${target}.${process.pid}.${randomBytes(6).toString('hex')}.tmp`
  await writeFile(temp, content, { encoding: 'utf8', mode: 0o600, flag: 'wx' })
  await rename(temp, target)
}

async function acquireLock(lockFile, timeoutMs = 2500) {
  const started = Date.now()
  while (true) {
    try {
      const handle = await open(lockFile, fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY, 0o600)
      await handle.writeFile(`${process.pid}\n`, 'utf8')
      await handle.sync()
      return handle
    } catch (error) {
      if (error?.code !== 'EEXIST') throw error
      if (Date.now() - started >= timeoutMs) throw new BoardContractError('LEDGER_LOCK_TIMEOUT', 'Timed out waiting for the event ledger lock')
      await new Promise((resolve) => setTimeout(resolve, 10))
    }
  }
}

async function releaseLock(handle, lockFile) {
  try { await handle?.close() } finally {
    try { await unlink(lockFile) } catch (error) { if (error?.code !== 'ENOENT') throw error }
  }
}

function validateEvidence(eventType, evidence) {
  invariant(isObject(evidence), 'EVIDENCE_REQUIRED')
  assertExactKeys(evidence, new Set(['level', 'receiptRef']), 'EVIDENCE_FIELD_FORBIDDEN')
  invariant(EVIDENCE_LEVELS.has(evidence.level), 'EVIDENCE_LEVEL_INVALID')
  invariant(EVENT_CATALOG[eventType]?.includes(evidence.level), 'EVIDENCE_LEVEL_UNSUPPORTED_FOR_EVENT')
  if (evidence.level === 'host_runtime_receipt') {
    invariant(typeof evidence.receiptRef === 'string' && evidence.receiptRef.trim(), 'HOST_RECEIPT_REQUIRED')
  }
  if (evidence.receiptRef !== null && evidence.receiptRef !== undefined) safeId(evidence.receiptRef, 'RECEIPT_REF_INVALID')
}

function validateMetadata(metadata = {}) {
  invariant(isObject(metadata), 'METADATA_OBJECT_REQUIRED')
  for (const [key, value] of Object.entries(metadata)) {
    invariant(METADATA_KEYS.has(key), 'METADATA_KEY_FORBIDDEN', 'Only operational metadata is allowed in the event ledger', { key })
    invariant(!SENSITIVE_KEY.test(key), 'SENSITIVE_METADATA_KEY_FORBIDDEN', 'Content and personal data must not be written to the event ledger', { key })
    invariant(value === null || ['string', 'number', 'boolean'].includes(typeof value), 'METADATA_VALUE_INVALID', 'Metadata values must be scalar', { key })
    if (typeof value === 'string') invariant(value.length <= 256, 'METADATA_VALUE_TOO_LONG', 'Hash or index content instead of storing it', { key })
  }
}

function payloadHashRequiredCode(eventType) {
  if (eventType === 'plan.frozen') return 'PLAN_PAYLOAD_HASH_REQUIRED'
  if (eventType.startsWith('seat.dispatch')) return 'TASK_PAYLOAD_HASH_REQUIRED'
  return 'EVENT_PAYLOAD_HASH_REQUIRED'
}

function parseJsonLines(raw, filePath) {
  return raw.split(/\r?\n/).filter(Boolean).map((line, index) => {
    try { return JSON.parse(line) }
    catch (error) { throw new BoardContractError('LEDGER_JSON_INVALID', 'Event ledger contains invalid JSON', { filePath, line: index + 1 }) }
  })
}

function validateStoredEvent(event, expectedSequence, previousHash, expectedRunIdHash) {
  assertExactKeys(event, EVENT_KEYS, 'EVENT_FIELD_FORBIDDEN')
  invariant(event?.schema === EVENT_SCHEMA, 'EVENT_SCHEMA_INVALID')
  invariant(event.release?.packageId === PACKAGE_ID && event.release?.productVersion === PRODUCT_VERSION, 'EVENT_RELEASE_INVALID')
  assertExactKeys(event.release, new Set(['packageId', 'productVersion']), 'EVENT_RELEASE_FIELD_FORBIDDEN')
  assertExactKeys(event.privacy, new Set(['class', 'contentStored', 'schemaVersion']), 'EVENT_PRIVACY_FIELD_FORBIDDEN')
  invariant(event.privacy.class === 'operational_metadata' && event.privacy.contentStored === false && event.privacy.schemaVersion === 'v1', 'EVENT_PRIVACY_INVALID')
  invariant(event.sequence === expectedSequence, 'EVENT_SEQUENCE_INVALID')
  invariant(event.previousEventHash === previousHash, 'EVENT_PREVIOUS_HASH_INVALID')
  invariant(event.runIdHash === expectedRunIdHash, 'RUN_ID_HASH_INVALID', 'Stored event is not bound to the requested run')
  invariant(Number.isFinite(Date.parse(event.occurredAt)) && Number.isFinite(Date.parse(event.recordedAt)), 'EVENT_TIME_INVALID')
  safeId(event.eventId, 'EVENT_ID_INVALID')
  invariant(Object.hasOwn(EVENT_CATALOG, event.eventType), 'EVENT_TYPE_NOT_REGISTERED')
  invariant(event.actorId === WRITER_ID, 'EVENT_WRITER_INVALID')
  validateEvidence(event.eventType, event.evidence)
  validateMetadata(event.metadata)
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
      if (nextEventType === 'seat.result_received') invariant(!priorForSeat('seat.result_received') && !priorForSeat('seat.result_failed'), 'SEAT_RESULT_ALREADY_RECORDED')
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

function verifyEvents(events, expectedRunIdHash) {
  let previousHash = 'genesis'
  const ids = new Set()
  events.forEach((event, index) => {
    validateEventTransition(events.slice(0, index), event.eventType, event.metadata, event.payloadHash)
    validateStoredEvent(event, index + 1, previousHash, expectedRunIdHash)
    invariant(!ids.has(event.eventId), 'EVENT_ID_DUPLICATE')
    ids.add(event.eventId)
    previousHash = event.eventHash
  })
  return { ok: true, count: events.length, chainHead: previousHash }
}

async function readEvents(paths, runId) {
  let raw = ''
  await rejectExistingLinkSegments(paths.root, paths.eventFile, 'EVENT_FILE_LINK_FORBIDDEN')
  try {
    await requireRegularFileNoLink(paths.eventFile, 'EVENT_FILE_INVALID')
    raw = await readFile(paths.eventFile, 'utf8')
  } catch (error) {
    if (!(error instanceof BoardContractError && error.details?.cause === 'ENOENT')) throw error
  }
  const events = parseJsonLines(raw, paths.eventFile)
  verifyEvents(events, sha256(runId))
  return events
}

export async function appendEvent({ workspaceRoot, runId, actorId, eventId = `evt_${randomUUID()}`, eventType, evidence, metadata = {}, payloadHash = null, occurredAt = new Date().toISOString() }) {
  await readWorkspace(workspaceRoot)
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN', 'Only board-convener may append shared meeting state')
  safeId(eventId, 'EVENT_ID_INVALID')
  invariant(Object.hasOwn(EVENT_CATALOG, eventType), 'EVENT_TYPE_NOT_REGISTERED')
  invariant(Number.isFinite(Date.parse(occurredAt)), 'EVENT_TIME_INVALID')
  validateEvidence(eventType, evidence)
  validateMetadata(metadata)
  if (payloadHash !== null) invariant(HEX_64.test(payloadHash), 'PAYLOAD_HASH_INVALID')
  if (HASH_BOUND_EVENT_TYPES.has(eventType)) invariant(typeof payloadHash === 'string' && HEX_64.test(payloadHash), payloadHashRequiredCode(eventType), `${eventType} must bind the exact durable payload hash`)
  const paths = workspacePaths(workspaceRoot, runId)
  await rejectExistingLinkSegments(paths.root, paths.eventFile, 'EVENT_FILE_LINK_FORBIDDEN')
  await rejectExistingLinkSegments(paths.root, paths.lockFile, 'EVENT_LOCK_LINK_FORBIDDEN')
  await mkdir(paths.events, { recursive: true })
  await mkdir(paths.locks, { recursive: true })
  const lock = await acquireLock(paths.lockFile)
  try {
    const events = await readEvents(paths, runId)
    const intentDigest = sha256({ runId, actorId, eventId, eventType, evidence, metadata, payloadHash })
    const existing = events.find((event) => event.eventId === eventId)
    if (existing) {
      invariant(existing.intentDigest === intentDigest, 'EVENT_IDEMPOTENCY_CONFLICT')
      return { ok: true, idempotent: true, event: existing, eventFile: paths.eventFile }
    }
    validateEventTransition(events, eventType, metadata, payloadHash)
    const withoutHash = {
      schema: EVENT_SCHEMA,
      eventId,
      eventType,
      sequence: events.length + 1,
      occurredAt,
      recordedAt: new Date().toISOString(),
      runIdHash: sha256(runId),
      actorId,
      evidence: { receiptRef: null, ...evidence },
      metadata,
      payloadHash,
      release: { packageId: PACKAGE_ID, productVersion: PRODUCT_VERSION },
      privacy: { class: 'operational_metadata', contentStored: false, schemaVersion: 'v1' },
      intentDigest,
      previousEventHash: events.at(-1)?.eventHash || 'genesis',
    }
    const event = { ...withoutHash, eventHash: sha256(withoutHash) }
    validateStoredEvent(event, events.length + 1, withoutHash.previousEventHash, sha256(runId))
    const handle = await open(paths.eventFile, fsConstants.O_CREAT | fsConstants.O_APPEND | fsConstants.O_WRONLY, 0o600)
    try { await handle.write(`${JSON.stringify(event)}\n`, null, 'utf8'); await handle.sync() } finally { await handle.close() }
    return { ok: true, idempotent: false, event, eventFile: paths.eventFile }
  } finally { await releaseLock(lock, paths.lockFile) }
}

export async function verifyLedger(workspaceRoot, runId) {
  await readWorkspace(workspaceRoot)
  const paths = workspacePaths(workspaceRoot, runId)
  const events = await readEvents(paths, runId)
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

export function validateReviewPlan(input) {
  invariant(isObject(input), 'PLAN_ENVELOPE_REQUIRED')
  assertExactKeys(input, PLAN_KEYS, 'PLAN_FIELD_FORBIDDEN')
  invariant(input.schema === PLAN_SCHEMA, 'PLAN_SCHEMA_INVALID')
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
    singleNextAction: input.singleNextAction,
  }
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

export function validateResultEnvelope(input) {
  invariant(isObject(input), 'RESULT_ENVELOPE_REQUIRED')
  assertExactKeys(input, RESULT_KEYS, 'RESULT_FIELD_FORBIDDEN')
  invariant(input.schema === RESULT_SCHEMA, 'RESULT_SCHEMA_INVALID')
  safeId(input.runId, 'RESULT_RUN_ID_INVALID')
  safeId(input.agendaItemId, 'RESULT_AGENDA_ID_INVALID')
  safeId(input.seatId, 'RESULT_SEAT_ID_INVALID')
  invariant(['professional_review', 'process_support'].includes(input.taskClass), 'RESULT_CLASS_INVALID')
  if (input.taskClass === 'professional_review') invariant(PROFESSIONAL_SEAT_IDS.has(input.seatId), 'RESULT_PROFESSIONAL_SEAT_INVALID')
  else invariant(SUPPORT_SEAT_IDS.has(input.seatId), 'RESULT_SUPPORT_SEAT_INVALID')
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
  invariant(isObject(input.sections) && Object.keys(input.sections).length >= 1 && Object.keys(input.sections).length <= 10, 'RESULT_SECTIONS_INVALID')
  const allowedSections = input.taskClass === 'professional_review' ? PROFESSIONAL_RESULT_SECTIONS : SUPPORT_RESULT_SECTIONS
  const unexpectedSections = Object.keys(input.sections).filter((key) => !allowedSections.has(key))
  invariant(unexpectedSections.length === 0, 'RESULT_SECTION_FORBIDDEN', 'Result contains sections outside its task class', { unexpectedSections })
  const requiredSections = input.taskClass === 'professional_review'
    ? ['judgement', 'conditions', 'failureConditions', 'humanGate', 'evidenceAssessment', 'dissent']
    : ['deliveryStatus', 'sourceLedger', 'artifactChecklist', 'capabilityStatus']
  const missingSections = requiredSections.filter((key) => !Object.hasOwn(input.sections, key))
  invariant(missingSections.length === 0, 'RESULT_SECTION_REQUIRED', 'Result is missing mandatory auditable sections', { missingSections })
  Object.values(input.sections).forEach((value) => boundedText(value, 'result_section', 4000))
  return {
    schema: input.schema, runId: input.runId, agendaItemId: input.agendaItemId, seatId: input.seatId,
    taskClass: input.taskClass, revision: input.revision, stance: input.stance, confidence: input.confidence,
    conclusionReady: input.conclusionReady, receiptId: input.receiptId, evidenceRefs: [...input.evidenceRefs],
    sections: Object.fromEntries(Object.entries(input.sections).map(([key, value]) => [key, value.trim()])),
  }
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

export async function recordReviewPlan({ workspaceRoot, actorId, envelope }) {
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  await readWorkspace(workspaceRoot)
  const normalized = validateReviewPlan(envelope)
  const paths = workspacePaths(workspaceRoot, normalized.runId)
  const target = paths.planFile
  ensureWithin(paths.plans, target)
  return persistNormalizedArtifact(paths.root, target, normalized, 'PLAN_RECORD_CONFLICT')
}

export async function recordTaskEnvelope({ workspaceRoot, actorId, envelope }) {
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  await readWorkspace(workspaceRoot)
  const normalized = validateTaskEnvelope(envelope)
  const paths = workspacePaths(workspaceRoot)
  const target = path.join(paths.root, memberArtifactTargets(normalized).taskTarget)
  ensureWithin(paths.tasks, target)
  const persisted = await persistNormalizedArtifact(paths.root, target, normalized, 'TASK_RECORD_CONFLICT')
  const taskPayloadHash = sha256(await readFile(target))
  return { ...persisted, taskPayloadHash }
}

export async function recordResultEnvelope({ workspaceRoot, envelope }) {
  await readWorkspace(workspaceRoot)
  const normalized = validateResultEnvelope(envelope)
  const paths = workspacePaths(workspaceRoot)
  const target = path.join(paths.root, memberArtifactTargets(normalized).resultTarget)
  ensureWithin(paths.results, target)
  return persistNormalizedArtifact(paths.root, target, normalized, 'RESULT_RECORD_CONFLICT')
}

export async function recordDeliveryObservation({ workspaceRoot, observation }) {
  await readWorkspace(workspaceRoot)
  const normalized = validateDeliveryObservation(observation)
  const paths = workspacePaths(workspaceRoot)
  const target = path.join(paths.root, memberArtifactTargets(normalized).deliveryObservationTarget)
  ensureWithin(paths.receipts, target)
  return persistNormalizedArtifact(paths.root, target, normalized, 'DELIVERY_OBSERVATION_RECORD_CONFLICT')
}

export async function recordFailureEnvelope({ workspaceRoot, actorId, envelope }) {
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  await readWorkspace(workspaceRoot)
  const normalized = validateFailureEnvelope(envelope)
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
  await readWorkspace(workspaceRoot)
  safeId(runId, 'COLLECTION_RUN_ID_INVALID')
  const paths = workspacePaths(workspaceRoot, runId)
  const planPath = paths.planFile
  ensureWithin(paths.plans, planPath)
  await rejectExistingLinkSegments(paths.root, planPath, 'COLLECTION_PLAN_LINK_FORBIDDEN')
  await requireRegularFileNoLink(planPath, 'COLLECTION_PLAN_INVALID')
  const plan = validateReviewPlan(await readJsonFile(planPath, 'COLLECTION_PLAN_INVALID'))
  invariant(plan.runId === runId, 'COLLECTION_PLAN_RUN_MISMATCH')

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
        result = validateResultEnvelope(await readJsonFile(resultPath, 'COLLECTION_RESULT_INVALID'))
        invariant(result.runId === runId && result.agendaItemId === agenda.agendaItemId && result.seatId === seatId && result.revision === plan.revision && result.taskClass === taskClass, 'COLLECTION_RESULT_IDENTITY_MISMATCH')
        const resultAssetBundleRef = requiredAssetBundleRef(result.evidenceRefs, 'COLLECTION_ASSET_BUNDLE_REF_COUNT_INVALID')
        invariant(resultAssetBundleRef === assetBundleRef, 'COLLECTION_ASSET_BUNDLE_REF_MISMATCH', 'Result must echo the exact bundle reference persisted in the dispatched task')
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

  const accepted = statuses.filter((item) => item.status === 'accepted')
  const unavailable = statuses.filter((item) => item.status === 'unavailable_after_retry')
  const resolved = statuses.filter((item) => item.status === 'accepted' || item.status === 'unavailable_after_retry')
  const invalid = statuses.filter((item) => item.status.startsWith('invalid_') || item.status === 'result_hash_mismatch')
  const allSelectedResolved = statuses.length > 0 && resolved.length === statuses.length
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
    expectedResultCount: statuses.length,
    acceptedResultCount: accepted.length,
    acceptedProfessionalResultCount: acceptedProfessional.length,
    acceptedSupportResultCount: acceptedSupport.length,
    unavailableResultCount: unavailable.length,
    unresolvedResultCount: statuses.length - resolved.length,
    allSelectedResolved,
    readyForSynthesis,
    state,
    statuses,
    release: { packageId: PACKAGE_ID, productVersion: PRODUCT_VERSION },
    evidenceBoundary: 'durable_result_content_and_member_observed_sendmessage_success_only_not_host_signed_receipt_or_lead_consumption_proof',
  }
  const collectionPayloadHash = sha256(collection)
  await rejectExistingLinkSegments(paths.root, paths.collectionFile, 'COLLECTION_OUTPUT_LINK_FORBIDDEN')
  await mkdir(paths.collections, { recursive: true })
  await rejectExistingLinkSegments(paths.root, paths.collectionFile, 'COLLECTION_OUTPUT_LINK_FORBIDDEN')
  await writeAtomic(paths.collectionFile, `${JSON.stringify({ ...collection, collectionPayloadHash }, null, 2)}\n`)
  return { collection, collectionPayloadHash, collectionFile: paths.collectionFile }
}

const DELIVERY_MARKER_GROUPS = Object.freeze({
  quick_review_card: [
    ['judgement', /一句话判断|one[- ]sentence judgement|recommendation/i],
    ['evidence', /事实|估计|假设|判断|未知|evidence|assumption/i],
    ['seat_stance', /专业席|席位|seat (stance|judgement)/i],
    ['failure_condition', /失效|最大风险|failure condition|stop condition/i],
    ['decision_quality', /决策质量|decision[- ]quality/i],
    ['action_human_gate', /下一步|人工关卡|触发器|负责人|复审|next action|human gate|trigger|owner|review date/i],
  ],
  review_memo: [
    ['options', /议案|选项|non-goals?|decision and options/i],
    ['evidence', /证据|假设|未知|evidence and assumptions/i],
    ['seat_judgements', /各席|席位判断|seat judgements/i],
    ['dissent', /异议|质询|dissent/i],
    ['conditions', /成立条件|失效条件|conditions?|failure conditions?/i],
    ['decision_quality', /决策质量|decision[- ]quality/i],
    ['decision_journal', /决策日志|decision journal/i],
    ['action_human_gate', /7\/30\/90|行动|人工关卡|action and human gate/i],
    ['evidence_asset_index', /证据台账|资产包索引|evidence ledger|asset index/i],
    ['professional_boundary', /专业边界|人工复核|professional boundary|human review/i],
  ],
  deep_review_preparation_card: [
    ['options', /议案|选项|non-goals?|decision and options/i],
    ['evidence', /证据|假设|未知|evidence and assumptions/i],
    ['seat_judgements', /各席|席位判断|seat judgements/i],
    ['dissent', /异议|质询|dissent/i],
    ['conditions', /成立条件|失效条件|conditions?|failure conditions?/i],
    ['decision_quality', /决策质量|decision[- ]quality/i],
    ['decision_journal', /决策日志|decision journal/i],
    ['action_human_gate', /7\/30\/90|行动|人工关卡|action and human gate/i],
    ['evidence_asset_index', /证据台账|资产包索引|evidence ledger|asset index/i],
    ['professional_boundary', /专业边界|人工复核|professional boundary|human review/i],
  ],
})

function validateDeliveryStructure(content, artifactType) {
  const groups = DELIVERY_MARKER_GROUPS[artifactType]
  invariant(Array.isArray(groups), 'DELIVERY_ARTIFACT_TYPE_INVALID')
  const missing = groups.filter(([, pattern]) => !pattern.test(content)).map(([id]) => id)
  invariant(missing.length === 0, 'DELIVERY_REQUIRED_SECTION_MISSING', 'Artifact is missing required decision-quality and audit sections', { missing })
  return groups.map(([id]) => id)
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
  const expectedTitle = artifactType === 'quick_review_card' ? '# 独董会快速审议卡' : artifactType === 'deep_review_preparation_card' ? '# 独董会深度审议准备卡' : '# 独董会审议备忘录'
  invariant(content.includes(expectedTitle), 'DELIVERY_ARTIFACT_TITLE_INVALID', 'Artifact must include the canonical title', { expectedTitle })
  const requiredSections = validateDeliveryStructure(content, artifactType)
  const artifactSha256 = sha256(content)
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
    eventBinding,
    state: 'ready_to_present',
    release: { packageId: PACKAGE_ID, productVersion: PRODUCT_VERSION },
    evidenceBoundary: 'local_artifact_structure_integrity_collection_and_event_hash_binding_only_not_semantic_spcbg_quality_host_presentation_user_acceptance_official_listing_or_product_credit',
  }
  await rejectExistingLinkSegments(paths.root, paths.deliveryFile, 'DELIVERY_OUTPUT_LINK_FORBIDDEN')
  await mkdir(paths.deliveries, { recursive: true })
  await rejectExistingLinkSegments(paths.root, paths.deliveryFile, 'DELIVERY_OUTPUT_LINK_FORBIDDEN')
  await writeAtomic(paths.deliveryFile, `${JSON.stringify(delivery, null, 2)}\n`)
  return { delivery, deliveryFile: paths.deliveryFile, artifactPath: resolvedArtifact }
}

export async function createCheckpoint({ workspaceRoot, runId, actorId, state }) {
  invariant(actorId === WRITER_ID, 'SHARED_WRITER_FORBIDDEN')
  safeId(state, 'CHECKPOINT_STATE_INVALID')
  const ledger = await verifyLedger(workspaceRoot, runId)
  const paths = workspacePaths(workspaceRoot, runId)
  await rejectExistingLinkSegments(paths.root, paths.checkpointFile, 'CHECKPOINT_LINK_FORBIDDEN')
  await mkdir(paths.checkpoints, { recursive: true })
  await rejectExistingLinkSegments(paths.root, paths.checkpointFile, 'CHECKPOINT_LINK_FORBIDDEN')
  const checkpoint = {
    schema: 'fbsir.board-checkpoint/v1',
    runIdHash: sha256(runId),
    state,
    eventCount: ledger.count,
    chainHead: ledger.chainHead,
    createdAt: new Date().toISOString(),
    release: { packageId: PACKAGE_ID, productVersion: PRODUCT_VERSION },
  }
  await writeAtomic(paths.checkpointFile, `${JSON.stringify(checkpoint, null, 2)}\n`)
  return { ...checkpoint, checkpointFile: paths.checkpointFile }
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
