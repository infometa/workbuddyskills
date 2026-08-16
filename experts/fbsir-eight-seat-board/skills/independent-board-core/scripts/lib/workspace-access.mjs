import { createHash } from 'node:crypto'
import { lstat, readFile, readdir } from 'node:fs/promises'
import path from 'node:path'

export const PACKAGE_VERSION = '26.8.19'
export const CURRENT_WORKSPACE_RELEASE = Object.freeze({
  workspaceSchema: 'fbsir.board-workspace/v2',
  eventSchema: 'fbsir.board-event/v2',
  productVersion: '26.8.19',
})
export const PREDECESSOR_WORKSPACE_RELEASE = Object.freeze({
  workspaceSchema: 'fbsir.board-workspace/v2',
  eventSchema: 'fbsir.board-event/v2',
  productVersion: '26.8.1',
})
export const LEGACY_WORKSPACE_RELEASE = Object.freeze({
  workspaceSchema: 'fbsir.board-workspace/v1',
  eventSchema: 'fbsir.board-event/v1',
  productVersion: '26.7.20',
})

// Compatibility scalar exports. New code must bind the complete release tuple above.
export const CURRENT_PRODUCT_VERSION = CURRENT_WORKSPACE_RELEASE.productVersion
export const CURRENT_WORKSPACE_SCHEMA = CURRENT_WORKSPACE_RELEASE.workspaceSchema
export const CURRENT_EVENT_SCHEMA = CURRENT_WORKSPACE_RELEASE.eventSchema
export const PREDECESSOR_PRODUCT_VERSION = PREDECESSOR_WORKSPACE_RELEASE.productVersion
export const LEGACY_PRODUCT_VERSION = LEGACY_WORKSPACE_RELEASE.productVersion
export const LEGACY_WORKSPACE_SCHEMA = LEGACY_WORKSPACE_RELEASE.workspaceSchema

const PACKAGE_ID = 'fbsir-eight-seat-board'
const WRITER_ID = 'board-convener'
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/
const WORKSPACE_INSTANCE_ID_PATTERN = /^wsi_[0-9a-f]{32}$/
const RUN_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/
const HEX_64 = /^[0-9a-f]{64}$/
const MAX_EVENT_LEDGER_FILES = 1_024
const MAX_EVENT_LEDGER_BYTES = 16 * 1024 * 1024
const MAX_EVENTS_PER_LEDGER = 10_000
const COMMON_MARKER_KEYS = [
  'schema', 'workspaceId', 'product', 'productVersion', 'privacyMode', 'contentExport',
  'telemetryExport', 'sharedStateWriter', 'createdAt',
]
const LEGACY_MARKER_KEYS = new Set(COMMON_MARKER_KEYS)
const CURRENT_MARKER_KEYS = new Set([...COMMON_MARKER_KEYS, 'workspaceInstanceId'])
const LEGACY_DIRECTORIES = [
  '.fbsir-board', '.fbsir-board/events', '.fbsir-board/checkpoints', '.fbsir-board/locks',
  '.fbsir-board/collections', '.fbsir-board/deliveries', '.fbsir-board/plans',
  'tasks', 'drafts', 'results', 'receipts', 'failures', 'deliverables',
]
const CURRENT_DIRECTORIES = [
  ...LEGACY_DIRECTORIES,
  '.fbsir-board/host-receipts', '.fbsir-board/evidence-sources',
  '.fbsir-board/material-cards', '.fbsir-board/claim-indexes', '.fbsir-board/predecessors',
]
const EVENT_KEYS = new Set([
  'schema', 'eventId', 'eventType', 'sequence', 'occurredAt', 'recordedAt', 'runIdHash',
  'actorId', 'evidence', 'metadata', 'payloadHash', 'release', 'privacy', 'intentDigest',
  'previousEventHash', 'eventHash',
])
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
const METADATA_NUMBER_KEYS = new Set(['attempt', 'revision', 'count'])
const SEAT_IDS = new Set([
  'board-secretary', 'strategy-partner', 'capital-partner', 'growth-partner',
  'operations-partner', 'org-partner', 'legal-partner', 'digital-partner',
])
const SENSITIVE_KEY = /(content|prompt|question|answer|raw|token|secret|password|email|phone|name|address|ip|document|attachment|material)/i
const HASH_BOUND_EVENT_TYPES = new Set([
  'plan.frozen', 'seat.dispatch_requested', 'seat.dispatched', 'seat.dispatch_failed',
  'seat.result_received', 'seat.result_recovered', 'seat.result_failed', 'collection.ready', 'memo.compiled',
])
const CURRENT_HASH_BOUND_EVENT_TYPES = new Set([...HASH_BOUND_EVENT_TYPES, 'artifact.presented', 'user.confirmed'])
const METADATA_ENUM_VALUES = Object.freeze({
  artifactType: new Set(['decision_start_card', 'material_sufficiency_card', 'quick_review_card', 'review_memo', 'deep_review_preparation_card', 'action_review_card', 'case_resume_card']),
  failureClass: new Set(['team_create_failed', 'seat_dispatch_failed', 'seat_result_failed', 'run_failed', 'validation_failed', 'precondition_failed']),
  receiptStatus: new Set(['not_required', 'requested', 'received', 'verified', 'rejected', 'unavailable']),
  reviewMode: new Set(['quick_review', 'standard_review', 'deep_review']),
  state: new Set(['initialized', 'opened', 'registered', 'frozen', 'requested', 'created', 'selected', 'dispatched', 'received', 'sealed', 'ready', 'compiled', 'presented', 'confirmed', 'failed', 'stopped', 'checkpointed', 'ready_to_present']),
  valueStage: new Set(['capability_card', 'decision_start_card', 'material_sufficiency', 'conditional_review', 'decision_artifact', 'action_follow_up']),
  workspaceMode: new Set(['fresh', 'resumed', 'legacy_read_only']),
  reasonCode: new Set(['member_no_response', 'send_message_failed', 'result_invalid', 'member_terminal_without_result', 'retry_exhausted', 'user_requested_stop', 'precondition_failed', 'validation_failed']),
})

export class BoardContractError extends Error {
  constructor(code, message = code, details = {}) {
    super(message)
    this.name = 'BoardContractError'
    this.code = code
    this.details = details
  }
}

function fail(code, message, details = {}) {
  throw new BoardContractError(code, message, details)
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function exactKeys(value, expected) {
  const actual = Object.keys(value)
  return actual.length === expected.size && actual.every((key) => expected.has(key))
}

function canonical(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value)
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    return JSON.stringify(value)
  }
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`
}

function sha256(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === 'string' ? value : canonical(value), 'utf8')
  return createHash('sha256').update(bytes).digest('hex')
}

function hasUniqueJsonObjectKeys(raw) {
  let index = 0
  const maxDepth = 32
  const whitespace = /[\t\n\r ]/
  const skipWhitespace = () => { while (whitespace.test(raw[index] || '')) index += 1 }
  const parseString = () => {
    const start = index
    if (raw[index] !== '"') throw new Error('JSON_STRING_EXPECTED')
    index += 1
    while (index < raw.length) {
      const character = raw[index]
      if (character === '"') {
        index += 1
        return JSON.parse(raw.slice(start, index))
      }
      if (character === '\\') {
        index += 1
        if (raw[index] === 'u') {
          if (!/^[0-9a-fA-F]{4}$/.test(raw.slice(index + 1, index + 5))) throw new Error('JSON_ESCAPE_INVALID')
          index += 5
          continue
        }
        if (!/["\\/bfnrt]/.test(raw[index] || '')) throw new Error('JSON_ESCAPE_INVALID')
      }
      index += 1
    }
    throw new Error('JSON_STRING_UNCLOSED')
  }
  const parseValue = (depth) => {
    if (depth > maxDepth) throw new Error('JSON_DEPTH_INVALID')
    skipWhitespace()
    if (raw[index] === '"') { parseString(); return }
    if (raw[index] === '{') { parseObject(depth + 1); return }
    if (raw[index] === '[') { parseArray(depth + 1); return }
    const remainder = raw.slice(index)
    const primitive = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(remainder)?.[0]
    if (!primitive) throw new Error('JSON_VALUE_INVALID')
    index += primitive.length
  }
  const parseObject = (depth) => {
    index += 1
    skipWhitespace()
    const keys = new Set()
    if (raw[index] === '}') { index += 1; return }
    while (index < raw.length) {
      skipWhitespace()
      const key = parseString()
      if (keys.has(key)) throw new Error('JSON_DUPLICATE_KEY')
      keys.add(key)
      skipWhitespace()
      if (raw[index] !== ':') throw new Error('JSON_COLON_EXPECTED')
      index += 1
      parseValue(depth)
      skipWhitespace()
      if (raw[index] === '}') { index += 1; return }
      if (raw[index] !== ',') throw new Error('JSON_COMMA_EXPECTED')
      index += 1
    }
    throw new Error('JSON_OBJECT_UNCLOSED')
  }
  const parseArray = (depth) => {
    index += 1
    skipWhitespace()
    if (raw[index] === ']') { index += 1; return }
    while (index < raw.length) {
      parseValue(depth)
      skipWhitespace()
      if (raw[index] === ']') { index += 1; return }
      if (raw[index] !== ',') throw new Error('JSON_COMMA_EXPECTED')
      index += 1
    }
    throw new Error('JSON_ARRAY_UNCLOSED')
  }
  try {
    parseValue(0)
    skipWhitespace()
    return index === raw.length
  } catch {
    return false
  }
}

export async function assertWorkspacePathNoLinks(target, code = 'WORKSPACE_LINK_PATH_FORBIDDEN') {
  const resolved = path.resolve(target)
  const parsed = path.parse(resolved)
  let cursor = parsed.root
  const relative = path.relative(parsed.root, resolved)
  for (const segment of relative.split(path.sep).filter(Boolean)) {
    cursor = path.join(cursor, segment)
    try {
      const info = await lstat(cursor)
      if (info.isSymbolicLink()) fail(code, 'Workspace paths must not traverse symbolic links or junctions', { target: cursor })
    } catch (error) {
      if (error?.code === 'ENOENT') return
      throw error
    }
  }
}

async function requireDirectoryNoLink(target, code) {
  let info
  try { info = await lstat(target) }
  catch (error) { fail(code, 'Required workspace directory is unavailable', { target, cause: error.code }) }
  if (!info.isDirectory() || info.isSymbolicLink()) fail(code, 'Workspace directory must be a real non-link directory', { target })
}

async function requireRegularFileNoLink(target, code) {
  let info
  try { info = await lstat(target) }
  catch (error) { fail(code, 'Required workspace file is unavailable', { target, cause: error.code }) }
  if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1) fail(code, 'Workspace file must be an isolated regular non-link file', { target })
}

function commonMarkerValuesValid(marker) {
  return marker.product === PACKAGE_ID
    && marker.sharedStateWriter === WRITER_ID
    && typeof marker.workspaceId === 'string'
    && ID_PATTERN.test(marker.workspaceId)
    && marker.privacyMode === 'local_default'
    && marker.contentExport === 'deny_by_default'
    && marker.telemetryExport === 'deny_by_default'
    && typeof marker.createdAt === 'string'
    && Number.isFinite(Date.parse(marker.createdAt))
}

function classifyMarker(marker) {
  if (!isPlainObject(marker) || !commonMarkerValuesValid(marker)) return 'unsupported'
  if (marker.schema === CURRENT_WORKSPACE_RELEASE.workspaceSchema
    && marker.productVersion === CURRENT_WORKSPACE_RELEASE.productVersion
    && exactKeys(marker, CURRENT_MARKER_KEYS)
    && typeof marker.workspaceInstanceId === 'string'
    && WORKSPACE_INSTANCE_ID_PATTERN.test(marker.workspaceInstanceId)) return 'current_read_write'
  if (marker.schema === PREDECESSOR_WORKSPACE_RELEASE.workspaceSchema
    && marker.productVersion === PREDECESSOR_WORKSPACE_RELEASE.productVersion
    && exactKeys(marker, CURRENT_MARKER_KEYS)
    && typeof marker.workspaceInstanceId === 'string'
    && WORKSPACE_INSTANCE_ID_PATTERN.test(marker.workspaceInstanceId)) return 'predecessor_read_only'
  if (marker.schema === LEGACY_WORKSPACE_RELEASE.workspaceSchema
    && marker.productVersion === LEGACY_WORKSPACE_RELEASE.productVersion
    && exactKeys(marker, LEGACY_MARKER_KEYS)) return 'legacy_read_only'
  return 'unsupported'
}

export function inspectWorkspaceMarkerBytes(raw) {
  const text = Buffer.isBuffer(raw) ? raw.toString('utf8') : raw
  if (typeof text !== 'string' || Buffer.byteLength(text, 'utf8') > 16_384 || !hasUniqueJsonObjectKeys(text)) {
    return { accessMode: 'unsupported', marker: null }
  }
  let marker
  try { marker = JSON.parse(text) }
  catch { return { accessMode: 'unsupported', marker: null } }
  const accessMode = classifyMarker(marker)
  return { accessMode, marker: accessMode === 'unsupported' ? null : marker }
}

function validateEvidence(eventType, evidence, accessMode) {
  if (!isPlainObject(evidence)
    || !exactKeys(evidence, new Set(['level', 'receiptRef']))
    || !EVIDENCE_LEVELS.has(evidence.level)
    || !EVENT_CATALOG[eventType]?.includes(evidence.level)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (accessMode === 'legacy_read_only') {
    if (evidence.level === 'host_runtime_receipt' && (typeof evidence.receiptRef !== 'string' || !ID_PATTERN.test(evidence.receiptRef))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    if (evidence.receiptRef !== null && evidence.receiptRef !== undefined && (typeof evidence.receiptRef !== 'string' || !ID_PATTERN.test(evidence.receiptRef))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    return
  }
  if (evidence.level === 'package_local_observation' && evidence.receiptRef !== null) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (evidence.level !== 'package_local_observation' && (typeof evidence.receiptRef !== 'string' || !/^rcpt_[0-9a-f]{32}$/.test(evidence.receiptRef))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
}

function validateMetadata(metadata, accessMode) {
  if (!isPlainObject(metadata)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  for (const [key, value] of Object.entries(metadata)) {
    if (!METADATA_KEYS.has(key) || SENSITIVE_KEY.test(key)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    if (accessMode === 'legacy_read_only') {
      if (!(value === null || ['string', 'number', 'boolean'].includes(typeof value))
        || (typeof value === 'number' && !Number.isFinite(value))
        || (typeof value === 'string' && value.length > 256)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
      continue
    }
    if (METADATA_NUMBER_KEYS.has(key)) {
      const minimum = key === 'count' ? 0 : 1
      if (!Number.isInteger(value) || value < minimum || value > 10000) fail('WORKSPACE_EVENT_CHAIN_INVALID')
      continue
    }
    if (typeof value !== 'string') fail('WORKSPACE_EVENT_CHAIN_INVALID')
    if (key === 'agendaItemId' && !/^agenda_[1-9][0-9]{0,5}$/.test(value)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    else if (key === 'roundId' && !/^round_[1-9][0-9]{0,5}$/.test(value)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    else if (key === 'seatId' && !SEAT_IDS.has(value)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    else if (!['agendaItemId', 'roundId', 'seatId'].includes(key) && !METADATA_ENUM_VALUES[key]?.has(value)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  }
}

function validateTransition(previousEvents, event) {
  const nextEventType = event.eventType
  const nextMetadata = event.metadata
  const priorTypes = previousEvents.map((item) => item.eventType)
  const has = (type) => priorTypes.includes(type)
  if (priorTypes.some((type) => type === 'run.failed' || type === 'run.stopped') && nextEventType !== 'checkpoint.created') fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (previousEvents.length === 0 && nextEventType !== 'meeting.opened') fail('WORKSPACE_EVENT_CHAIN_INVALID')
  const prerequisites = {
    'agenda.registered': ['meeting.opened'], 'plan.frozen': ['agenda.registered'],
    'team.create_requested': ['plan.frozen'], 'team.created': ['team.create_requested'],
    'team.create_failed': ['team.create_requested'], 'seat.selected': ['team.created'],
    'seat.dispatch_requested': ['seat.selected'], 'seat.dispatched': ['seat.dispatch_requested'],
    'seat.dispatch_failed': ['seat.dispatch_requested'], 'seat.result_received': ['seat.dispatched'],
    'seat.result_recovered': ['seat.dispatched'], 'round.independent_sealed': ['seat.selected'],
    'challenge.dispatched': ['round.independent_sealed'], 'challenge.result_received': ['challenge.dispatched'],
    'collection.ready': ['round.independent_sealed'], 'memo.compiled': ['collection.ready'],
    'artifact.presented': ['memo.compiled'], 'user.confirmed': ['artifact.presented'],
    'run.failed': ['meeting.opened'], 'run.stopped': ['meeting.opened'], 'checkpoint.created': ['meeting.opened'],
  }
  if ((prerequisites[nextEventType] || []).some((required) => !has(required))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (nextEventType === 'agenda.registered' && (!Number.isInteger(nextMetadata.count) || nextMetadata.count < 1 || nextMetadata.count > 5)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (nextEventType === 'plan.frozen' && (!Number.isInteger(nextMetadata.revision) || nextMetadata.revision < 1 || previousEvents.some((item) => item.eventType === 'plan.frozen' && item.metadata?.revision === nextMetadata.revision))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  const seatEvents = new Set(['seat.selected', 'seat.dispatch_requested', 'seat.dispatched', 'seat.dispatch_failed', 'seat.result_received', 'seat.result_recovered', 'seat.result_failed'])
  if (seatEvents.has(nextEventType)) {
    if (typeof nextMetadata.agendaItemId !== 'string' || !ID_PATTERN.test(nextMetadata.agendaItemId) || !SEAT_IDS.has(nextMetadata.seatId) || !Number.isInteger(nextMetadata.revision) || nextMetadata.revision < 1) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    const sameScope = (item) => item.metadata?.agendaItemId === nextMetadata.agendaItemId && item.metadata?.seatId === nextMetadata.seatId && item.metadata?.revision === nextMetadata.revision
    const scopeSealed = previousEvents.some((item) => item.eventType === 'round.independent_sealed'
      && item.metadata?.agendaItemId === nextMetadata.agendaItemId
      && item.metadata?.revision === nextMetadata.revision)
    if (scopeSealed) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    const prior = (type) => previousEvents.find((item) => item.eventType === type && sameScope(item))
    if (nextEventType === 'seat.selected' && (!previousEvents.some((item) => item.eventType === 'plan.frozen' && item.metadata?.revision === nextMetadata.revision) || prior('seat.selected'))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    if (nextEventType === 'seat.dispatch_requested' && (!prior('seat.selected') || prior('seat.dispatch_requested'))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    if (nextEventType === 'seat.dispatched' || nextEventType === 'seat.dispatch_failed') {
      const requested = prior('seat.dispatch_requested')
      if (!requested || requested.payloadHash !== event.payloadHash || prior('seat.dispatched') || prior('seat.dispatch_failed')) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    }
    if (['seat.result_received', 'seat.result_recovered', 'seat.result_failed'].includes(nextEventType)) {
      const dispatched = Boolean(prior('seat.dispatched'))
      const dispatchFailed = Boolean(prior('seat.dispatch_failed'))
      if (nextEventType === 'seat.result_failed' ? !(dispatched || dispatchFailed) : !dispatched) fail('WORKSPACE_EVENT_CHAIN_INVALID')
      if (prior('seat.result_received') || prior('seat.result_failed') || (nextEventType !== 'seat.result_received' && prior('seat.result_recovered'))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
      const recovered = prior('seat.result_recovered')
      if (nextEventType === 'seat.result_received' && recovered && recovered.payloadHash !== event.payloadHash) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    }
  }
  if (nextEventType === 'round.independent_sealed') {
    if (typeof nextMetadata.agendaItemId !== 'string' || !ID_PATTERN.test(nextMetadata.agendaItemId) || !Number.isInteger(nextMetadata.revision) || nextMetadata.revision < 1) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    const inRound = (item) => item.metadata?.agendaItemId === nextMetadata.agendaItemId && item.metadata?.revision === nextMetadata.revision
    if (previousEvents.some((item) => item.eventType === 'round.independent_sealed' && inRound(item))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    const selected = [...new Set(previousEvents.filter((item) => item.eventType === 'seat.selected' && inRound(item)).map((item) => item.metadata.seatId))]
    const resolved = new Set(['seat.result_received', 'seat.result_recovered', 'seat.result_failed'])
    if (selected.length < 1 || selected.some((seatId) => !previousEvents.some((item) => resolved.has(item.eventType) && inRound(item) && item.metadata?.seatId === seatId))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  }
  if (nextEventType === 'memo.compiled' && (has('challenge.dispatched') && !has('challenge.result_received') || !Number.isInteger(nextMetadata.revision) || nextMetadata.revision < 1)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (nextEventType === 'collection.ready') {
    if (!Number.isInteger(nextMetadata.count) || nextMetadata.count < 1 || !Number.isInteger(nextMetadata.revision) || nextMetadata.revision < 1) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    const agendas = [...new Set(previousEvents.filter((item) => item.eventType === 'seat.selected' && item.metadata?.revision === nextMetadata.revision).map((item) => item.metadata.agendaItemId))]
    if (agendas.length < 1 || agendas.some((agendaItemId) => !previousEvents.some((item) => item.eventType === 'round.independent_sealed' && item.metadata?.agendaItemId === agendaItemId && item.metadata?.revision === nextMetadata.revision))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  }
}

function validateEventShape(event, { accessMode, schema, productVersion, runIdHash, sequence, previousEventHash, workspaceScopeHash, previousEvents }) {
  if (!isPlainObject(event) || !exactKeys(event, EVENT_KEYS)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (event.schema !== schema
    || event.sequence !== sequence
    || event.previousEventHash !== previousEventHash
    || event.runIdHash !== runIdHash
    || event.actorId !== WRITER_ID
    || typeof event.eventId !== 'string'
    || typeof event.eventType !== 'string'
    || !HEX_64.test(event.intentDigest)
    || !(event.payloadHash === null || HEX_64.test(event.payloadHash))
    || !Number.isFinite(Date.parse(event.occurredAt))
    || !Number.isFinite(Date.parse(event.recordedAt))) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (!isPlainObject(event.release)
    || !exactKeys(event.release, new Set(['packageId', 'productVersion']))
    || event.release.packageId !== PACKAGE_ID
    || event.release.productVersion !== productVersion) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (!isPlainObject(event.privacy)
    || !exactKeys(event.privacy, new Set(['class', 'contentStored', 'schemaVersion']))
    || event.privacy.class !== 'operational_metadata'
    || event.privacy.contentStored !== false
    || event.privacy.schemaVersion !== 'v1') fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (!Object.hasOwn(EVENT_CATALOG, event.eventType)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  validateEvidence(event.eventType, event.evidence, accessMode)
  validateMetadata(event.metadata, accessMode)
  const hashBoundEventTypes = accessMode === 'legacy_read_only' ? HASH_BOUND_EVENT_TYPES : CURRENT_HASH_BOUND_EVENT_TYPES
  if (hashBoundEventTypes.has(event.eventType) && !HEX_64.test(event.payloadHash || '')) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (accessMode === 'legacy_read_only' && !ID_PATTERN.test(event.eventId)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  if (workspaceScopeHash !== null) {
    const expectedEventId = `evt_${sha256({
      workspaceIdHash: workspaceScopeHash,
      runIdHash,
      actorId: event.actorId,
      eventType: event.eventType,
      evidence: event.evidence,
      metadata: event.metadata,
      payloadHash: event.payloadHash,
    }).slice(0, 32)}`
    if (event.eventId !== expectedEventId) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  }
  if (accessMode !== 'legacy_read_only') {
    const expectedIntentDigest = sha256({ runIdHash, actorId: event.actorId, eventId: event.eventId, eventType: event.eventType, evidence: event.evidence, metadata: event.metadata, payloadHash: event.payloadHash })
    if (event.intentDigest !== expectedIntentDigest) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  }
  validateTransition(previousEvents, event)
  const withoutHash = Object.fromEntries(Object.entries(event).filter(([key]) => key !== 'eventHash'))
  if (!HEX_64.test(event.eventHash) || event.eventHash !== sha256(withoutHash)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
}

async function verifyEventLedgers(root, marker, accessMode) {
  const eventsRoot = path.join(root, '.fbsir-board', 'events')
  let entries
  try { entries = await readdir(eventsRoot, { withFileTypes: true }) }
  catch { fail('WORKSPACE_EVENT_CHAIN_INVALID') }
  if (entries.length > MAX_EVENT_LEDGER_FILES) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  const release = accessMode === 'current_read_write'
    ? CURRENT_WORKSPACE_RELEASE
    : accessMode === 'predecessor_read_only'
      ? PREDECESSOR_WORKSPACE_RELEASE
      : LEGACY_WORKSPACE_RELEASE
  const workspaceScopeHash = accessMode !== 'legacy_read_only'
    ? sha256({ workspaceId: marker.workspaceId, workspaceInstanceId: marker.workspaceInstanceId })
    : null
  for (const entry of entries) {
    if (!entry.isFile() || entry.isSymbolicLink() || !entry.name.endsWith('.jsonl')) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    const runId = entry.name.slice(0, -'.jsonl'.length)
    if (!RUN_ID_PATTERN.test(runId)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    const target = path.join(eventsRoot, entry.name)
    await assertWorkspacePathNoLinks(target, 'WORKSPACE_EVENT_CHAIN_INVALID')
    const info = await lstat(target)
    if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1 || info.size > MAX_EVENT_LEDGER_BYTES) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    verifyEventLedgerBytes(await readFile(target), {
      accessMode,
      schema: release.eventSchema,
      productVersion: release.productVersion,
      runId,
      workspaceScopeHash,
    })
  }
}

function verifyEventLedgerBytes(raw, { accessMode, schema, productVersion, runId, workspaceScopeHash }) {
  const bytes = Buffer.isBuffer(raw) ? raw : Buffer.from(raw, 'utf8')
  if (bytes.length > MAX_EVENT_LEDGER_BYTES) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  let events
  try {
    events = bytes.toString('utf8').split(/\r?\n/).filter(Boolean).map((line) => {
      if (!hasUniqueJsonObjectKeys(line)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
      return JSON.parse(line)
    })
  } catch { fail('WORKSPACE_EVENT_CHAIN_INVALID') }
  if (events.length > MAX_EVENTS_PER_LEDGER) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  let previousEventHash = 'genesis'
  const runIdHash = sha256(runId)
  const previousEvents = []
  const eventIds = new Set()
  for (const [index, event] of events.entries()) {
    validateEventShape(event, {
      accessMode,
      schema,
      productVersion,
      runIdHash,
      sequence: index + 1,
      previousEventHash,
      workspaceScopeHash,
      previousEvents,
    })
    if (eventIds.has(event.eventId)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
    eventIds.add(event.eventId)
    previousEvents.push(event)
    previousEventHash = event.eventHash
  }
  return { eventCount: events.length, chainHead: previousEventHash }
}

export function verifyCurrentEventLedgerBytes(raw, runId, workspaceScopeHash) {
  if (typeof runId !== 'string' || !RUN_ID_PATTERN.test(runId) || typeof workspaceScopeHash !== 'string' || !HEX_64.test(workspaceScopeHash)) {
    fail('WORKSPACE_EVENT_CHAIN_INVALID')
  }
  return verifyEventLedgerBytes(raw, {
    accessMode: 'current_read_write',
    schema: CURRENT_WORKSPACE_RELEASE.eventSchema,
    productVersion: CURRENT_WORKSPACE_RELEASE.productVersion,
    runId,
    workspaceScopeHash,
  })
}

export function verifyPredecessorEventLedgerBytes(raw, runId, workspaceScopeHash) {
  if (typeof runId !== 'string' || !RUN_ID_PATTERN.test(runId) || typeof workspaceScopeHash !== 'string' || !HEX_64.test(workspaceScopeHash)) {
    fail('WORKSPACE_EVENT_CHAIN_INVALID')
  }
  return verifyEventLedgerBytes(raw, {
    accessMode: 'predecessor_read_only',
    schema: PREDECESSOR_WORKSPACE_RELEASE.eventSchema,
    productVersion: PREDECESSOR_WORKSPACE_RELEASE.productVersion,
    runId,
    workspaceScopeHash,
  })
}

export function verifyLegacyEventLedgerBytes(raw, runId) {
  if (typeof runId !== 'string' || !RUN_ID_PATTERN.test(runId)) fail('WORKSPACE_EVENT_CHAIN_INVALID')
  return verifyEventLedgerBytes(raw, {
    accessMode: 'legacy_read_only',
    schema: LEGACY_WORKSPACE_RELEASE.eventSchema,
    productVersion: LEGACY_WORKSPACE_RELEASE.productVersion,
    runId,
    workspaceScopeHash: null,
  })
}

export async function inspectWorkspaceAccess(workspaceRoot) {
  if (typeof workspaceRoot !== 'string' || !workspaceRoot.trim()) fail('WORKSPACE_PATH_REQUIRED')
  const root = path.resolve(workspaceRoot)
  await assertWorkspacePathNoLinks(root, 'WORKSPACE_ROOT_LINK_FORBIDDEN')
  await requireDirectoryNoLink(root, 'WORKSPACE_ROOT_LINK_FORBIDDEN')
  const control = path.join(root, '.fbsir-board')
  const markerPath = path.join(control, 'workspace.json')
  await requireDirectoryNoLink(control, 'WORKSPACE_DIRECTORY_INVALID')
  await requireRegularFileNoLink(markerPath, 'WORKSPACE_MARKER_INVALID')
  let marker
  try {
    const rawMarker = await readFile(markerPath, 'utf8')
    if (Buffer.byteLength(rawMarker, 'utf8') > 16_384) return { accessMode: 'unsupported', marker: null }
    marker = JSON.parse(rawMarker)
    if (!hasUniqueJsonObjectKeys(rawMarker)) return { accessMode: 'unsupported', marker: null }
  }
  catch (error) { fail('WORKSPACE_NOT_INITIALIZED', 'Initialize a dedicated board workspace first', { cause: error.message }) }
  const accessMode = classifyMarker(marker)
  const requiredDirectories = accessMode === 'current_read_write' || accessMode === 'predecessor_read_only'
    ? CURRENT_DIRECTORIES
    : accessMode === 'legacy_read_only'
      ? LEGACY_DIRECTORIES
      : []
  for (const relative of requiredDirectories) {
    const target = path.join(root, relative)
    await assertWorkspacePathNoLinks(target, 'WORKSPACE_DIRECTORY_LINK_FORBIDDEN')
    await requireDirectoryNoLink(target, 'WORKSPACE_DIRECTORY_INVALID')
  }
  return { accessMode, marker: accessMode === 'unsupported' ? null : marker }
}

export async function inspectWorkspace(workspaceRoot) {
  const inspected = await inspectWorkspaceAccess(workspaceRoot)
  if (inspected.accessMode !== 'unsupported') await verifyEventLedgers(path.resolve(workspaceRoot), inspected.marker, inspected.accessMode)
  return inspected
}

export async function requireWritableWorkspace(workspaceRoot) {
  const inspected = await inspectWorkspace(workspaceRoot)
  if (inspected.accessMode === 'predecessor_read_only') {
    fail('WORKSPACE_PREDECESSOR_READ_ONLY', 'Predecessor workspaces are immutable; resume into a new current workspace')
  }
  if (inspected.accessMode === 'legacy_read_only') {
    fail('WORKSPACE_LEGACY_READ_ONLY', 'Legacy workspaces are immutable; resume into a new current workspace')
  }
  if (inspected.accessMode !== 'current_read_write') {
    fail('WORKSPACE_VERSION_UNSUPPORTED', 'Workspace release tuple is not writable by this package')
  }
  return inspected.marker
}
