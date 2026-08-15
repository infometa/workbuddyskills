import { constants as fsConstants } from 'node:fs'
import { createHash, randomBytes } from 'node:crypto'
import { link, lstat, open, readdir, unlink } from 'node:fs/promises'
import path from 'node:path'

import {
  BoardContractError,
  LEGACY_WORKSPACE_RELEASE,
  PREDECESSOR_WORKSPACE_RELEASE,
  assertWorkspacePathNoLinks,
  inspectWorkspace,
  inspectWorkspaceMarkerBytes,
  requireWritableWorkspace,
  verifyLegacyEventLedgerBytes,
  verifyPredecessorEventLedgerBytes,
} from './workspace-access.mjs'

export const LEGACY_RESUME_DIGEST_SCHEMA = 'fbsir.legacy-resume-digest/v1'
export const LEGACY_RESUME_EVIDENCE_BOUNDARY = 'stable_handle_captured_legacy_bytes_and_chain_binding_with_cooperative_target_publish_only_not_atomic_cross_file_snapshot_hostile_same_identity_race_content_truth_host_receipt_current_run_completion_or_product_credit'
export const PREDECESSOR_RESUME_DIGEST_SCHEMA = 'fbsir.predecessor-resume-digest/v2'
export const PREDECESSOR_RESUME_EVIDENCE_BOUNDARY = 'stable_handle_captured_exact_predecessor_or_legacy_bytes_release_tuple_and_chain_binding_with_cooperative_target_publish_only_not_atomic_cross_file_snapshot_hostile_same_identity_race_content_truth_host_receipt_current_run_completion_or_product_credit'
export const PREDECESSOR_RUN_REF_SCHEMA = 'fbsir.predecessor-run-ref/v2'

const PACKAGE_ID = 'fbsir-eight-seat-board'
const RUN_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/
const MAX_FILE_BYTES = 16 * 1024 * 1024
const MAX_DELIVERABLE_FILES = 1_024
const MAX_DELIVERABLE_BYTES = 64 * 1024 * 1024
const MAX_DELIVERABLE_DIRECTORIES = 1_024
const MAX_DELIVERABLE_DEPTH = 32
const HEX_64 = /^[0-9a-f]{64}$/
const DIGEST_RECEIPT_KEYS = new Set(['schema', 'source', 'bindings', 'legacyResumeDigest', 'accessMode', 'contentExported'])
const DIGEST_SOURCE_KEYS = new Set(['product', 'productVersion', 'workspaceSchema', 'workspaceIdHash', 'runIdHash'])
const PREDECESSOR_DIGEST_RECEIPT_KEYS = new Set(['schema', 'source', 'bindings', 'predecessorResumeDigest', 'accessMode', 'contentExported'])
const PREDECESSOR_DIGEST_SOURCE_KEYS = new Set(['product', 'workspaceRelease', 'workspaceIdHash', 'runIdHash'])
const WORKSPACE_RELEASE_KEYS = new Set(['workspaceSchema', 'eventSchema', 'productVersion'])
const DIGEST_BINDING_KEYS = new Set([
  'markerSha256', 'planSha256', 'eventChainHead', 'checkpointSha256', 'collectionSha256',
  'deliverySha256', 'deliverableInventorySha256',
])

function fail(code, message = code) {
  throw new BoardContractError(code, message)
}

function plainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null)
}

function exactKeys(value, expected) {
  return plainObject(value) && Object.keys(value).length === expected.size
    && Object.keys(value).every((key) => expected.has(key))
}

function hashOrNull(value) {
  return value === null || (typeof value === 'string' && HEX_64.test(value))
}

export function validateLegacyResumeDigestReceipt(input) {
  if (!exactKeys(input, DIGEST_RECEIPT_KEYS)) fail('PREDECESSOR_RECEIPT_INVALID')
  if (input.schema !== LEGACY_RESUME_DIGEST_SCHEMA || input.accessMode !== 'legacy_read_only' || input.contentExported !== false) {
    fail('PREDECESSOR_RECEIPT_INVALID')
  }
  if (!exactKeys(input.source, DIGEST_SOURCE_KEYS)
    || input.source.product !== PACKAGE_ID
    || input.source.productVersion !== LEGACY_WORKSPACE_RELEASE.productVersion
    || input.source.workspaceSchema !== LEGACY_WORKSPACE_RELEASE.workspaceSchema
    || !HEX_64.test(input.source.workspaceIdHash)
    || !HEX_64.test(input.source.runIdHash)) fail('PREDECESSOR_RECEIPT_INVALID')
  if (!exactKeys(input.bindings, DIGEST_BINDING_KEYS)
    || !HEX_64.test(input.bindings.markerSha256)
    || !HEX_64.test(input.bindings.planSha256)
    || !(input.bindings.eventChainHead === 'genesis' || HEX_64.test(input.bindings.eventChainHead))
    || !hashOrNull(input.bindings.checkpointSha256)
    || !hashOrNull(input.bindings.collectionSha256)
    || !hashOrNull(input.bindings.deliverySha256)
    || !HEX_64.test(input.bindings.deliverableInventorySha256)
    || !HEX_64.test(input.legacyResumeDigest)) fail('PREDECESSOR_RECEIPT_INVALID')
  return {
    schema: input.schema,
    source: Object.fromEntries([...DIGEST_SOURCE_KEYS].map((key) => [key, input.source[key]])),
    bindings: Object.fromEntries([...DIGEST_BINDING_KEYS].map((key) => [key, input.bindings[key]])),
    legacyResumeDigest: input.legacyResumeDigest,
    accessMode: input.accessMode,
    contentExported: input.contentExported,
  }
}

export function validatePredecessorResumeDigestReceipt(input) {
  if (!exactKeys(input, PREDECESSOR_DIGEST_RECEIPT_KEYS)) fail('PREDECESSOR_RECEIPT_INVALID')
  if (input.schema !== PREDECESSOR_RESUME_DIGEST_SCHEMA
    || input.accessMode !== 'predecessor_read_only'
    || input.contentExported !== false) fail('PREDECESSOR_RECEIPT_INVALID')
  if (!exactKeys(input.source, PREDECESSOR_DIGEST_SOURCE_KEYS)
    || input.source.product !== PACKAGE_ID
    || !exactKeys(input.source.workspaceRelease, WORKSPACE_RELEASE_KEYS)
    || Object.entries(PREDECESSOR_WORKSPACE_RELEASE).some(([key, value]) => input.source.workspaceRelease[key] !== value)
    || !HEX_64.test(input.source.workspaceIdHash)
    || !HEX_64.test(input.source.runIdHash)) fail('PREDECESSOR_RECEIPT_INVALID')
  if (!exactKeys(input.bindings, DIGEST_BINDING_KEYS)
    || !HEX_64.test(input.bindings.markerSha256)
    || !HEX_64.test(input.bindings.planSha256)
    || !(input.bindings.eventChainHead === 'genesis' || HEX_64.test(input.bindings.eventChainHead))
    || !hashOrNull(input.bindings.checkpointSha256)
    || !hashOrNull(input.bindings.collectionSha256)
    || !hashOrNull(input.bindings.deliverySha256)
    || !HEX_64.test(input.bindings.deliverableInventorySha256)
    || !HEX_64.test(input.predecessorResumeDigest)) fail('PREDECESSOR_RECEIPT_INVALID')
  return {
    schema: input.schema,
    source: {
      product: input.source.product,
      workspaceRelease: Object.fromEntries([...WORKSPACE_RELEASE_KEYS].map((key) => [key, input.source.workspaceRelease[key]])),
      workspaceIdHash: input.source.workspaceIdHash,
      runIdHash: input.source.runIdHash,
    },
    bindings: Object.fromEntries([...DIGEST_BINDING_KEYS].map((key) => [key, input.bindings[key]])),
    predecessorResumeDigest: input.predecessorResumeDigest,
    accessMode: input.accessMode,
    contentExported: input.contentExported,
  }
}

export function validateResumeDigestReceipt(input) {
  if (input?.schema === LEGACY_RESUME_DIGEST_SCHEMA) return validateLegacyResumeDigestReceipt(input)
  if (input?.schema === PREDECESSOR_RESUME_DIGEST_SCHEMA) return validatePredecessorResumeDigestReceipt(input)
  fail('PREDECESSOR_RECEIPT_INVALID')
}

function canonical(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value)
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) fail('LEGACY_RESUME_CANONICAL_INVALID')
    return JSON.stringify(value)
  }
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`
  }
  fail('LEGACY_RESUME_CANONICAL_INVALID')
}

function sha256(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === 'string' ? value : canonical(value), 'utf8')
  return createHash('sha256').update(bytes).digest('hex')
}

function domainSha256(domain, value) {
  return sha256(Buffer.concat([Buffer.from(`${domain}\0`, 'utf8'), Buffer.from(canonical(value), 'utf8')]))
}

function lexicalPathOrder(left, right) {
  return left.path < right.path ? -1 : left.path > right.path ? 1 : 0
}

function workspaceRelative(root, target) {
  const relative = path.relative(root, target)
  if (!relative || relative.startsWith('..') || path.isAbsolute(relative)) fail('LEGACY_RESUME_PATH_OUTSIDE_SOURCE')
  return relative.split(path.sep).join('/')
}

function isWithin(parent, candidate) {
  const relative = path.relative(parent, candidate)
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative))
}

function assertSeparatedWorkspaceRoots(sourceWorkspaceRoot, targetWorkspaceRoot) {
  const source = path.resolve(sourceWorkspaceRoot)
  const target = path.resolve(targetWorkspaceRoot)
  if (isWithin(source, target) || isWithin(target, source)) fail('LEGACY_RESUME_WORKSPACE_BOUNDARY_INVALID')
  return { source, target }
}

function fileCode(domain, suffix) {
  return `LEGACY_RESUME_${domain}_${suffix}`
}

function sameStableStat(left, right) {
  return ['dev', 'ino', 'nlink', 'size', 'mode', 'mtimeNs', 'ctimeNs'].every((key) => left[key] === right[key])
}

function sameIdentityStat(left, right) {
  return ['dev', 'ino', 'mode'].every((key) => left[key] === right[key])
}

async function readIsolatedFile(root, target, { required = true, maxBytes = MAX_FILE_BYTES, domain = 'SOURCE' } = {}) {
  await assertWorkspacePathNoLinks(target, fileCode(domain, 'LINK_FORBIDDEN'))
  let before
  try { before = await lstat(target, { bigint: true }) }
  catch (error) {
    if (!required && error?.code === 'ENOENT') return null
    fail(fileCode(domain, 'FILE_REQUIRED'))
  }
  if (!before.isFile() || before.isSymbolicLink() || before.nlink !== 1n || before.size > BigInt(maxBytes)) fail(fileCode(domain, 'FILE_INVALID'))
  let handle
  try { handle = await open(target, 'r') }
  catch { fail(fileCode(domain, 'CHANGED_DURING_READ')) }
  try {
    const opened = await handle.stat({ bigint: true })
    if (!opened.isFile() || opened.nlink !== 1n || opened.size > BigInt(maxBytes)) fail(fileCode(domain, 'FILE_INVALID'))
    if (!sameStableStat(before, opened)) fail(fileCode(domain, 'CHANGED_DURING_READ'))
    const bytes = await handle.readFile()
    const afterHandle = await handle.stat({ bigint: true })
    let afterPath
    try { afterPath = await lstat(target, { bigint: true }) }
    catch { fail(fileCode(domain, 'CHANGED_DURING_READ')) }
    if (BigInt(bytes.length) !== opened.size || !sameStableStat(opened, afterHandle) || !sameStableStat(afterHandle, afterPath)
      || afterPath.isSymbolicLink()) fail(fileCode(domain, 'CHANGED_DURING_READ'))
    return { path: workspaceRelative(root, target), size: bytes.length, sha256: sha256(bytes), bytes }
  } finally {
    await handle.close()
  }
}

async function listDeliverables(root) {
  const base = path.join(root, 'deliverables')
  const files = []
  let totalBytes = 0
  let directoryCount = 0
  async function walk(directory, depth) {
    directoryCount += 1
    if (directoryCount > MAX_DELIVERABLE_DIRECTORIES || depth > MAX_DELIVERABLE_DEPTH) fail('LEGACY_RESUME_RESOURCE_LIMIT')
    await assertWorkspacePathNoLinks(directory, 'LEGACY_RESUME_SOURCE_LINK_FORBIDDEN')
    let entries
    try { entries = await readdir(directory, { withFileTypes: true }) }
    catch { fail('LEGACY_RESUME_DELIVERABLE_DIRECTORY_INVALID') }
    entries.sort((left, right) => left.name < right.name ? -1 : left.name > right.name ? 1 : 0)
    for (const entry of entries) {
      const target = path.join(directory, entry.name)
      if (entry.isSymbolicLink() || (!entry.isDirectory() && !entry.isFile())) fail('LEGACY_RESUME_SOURCE_LINK_FORBIDDEN')
      if (entry.isDirectory()) await walk(target, depth + 1)
      else {
        if (files.length >= MAX_DELIVERABLE_FILES) fail('LEGACY_RESUME_RESOURCE_LIMIT')
        const file = await readIsolatedFile(root, target)
        totalBytes += file.size
        if (totalBytes > MAX_DELIVERABLE_BYTES) fail('LEGACY_RESUME_RESOURCE_LIMIT')
        files.push(publicFileRecord(file))
      }
    }
  }
  await walk(base, 0)
  return files.sort(lexicalPathOrder)
}

function publicFileRecord(file) {
  return { path: file.path, size: file.size, sha256: file.sha256 }
}

export async function inspectLegacyResume({ sourceWorkspaceRoot, sourceRunId } = {}) {
  if (typeof sourceWorkspaceRoot !== 'string' || !sourceWorkspaceRoot.trim()) fail('LEGACY_RESUME_SOURCE_REQUIRED')
  if (typeof sourceRunId !== 'string' || !RUN_ID_PATTERN.test(sourceRunId)) fail('LEGACY_RESUME_RUN_ID_INVALID')
  const inspected = await inspectWorkspace(sourceWorkspaceRoot)
  if (inspected.accessMode !== 'legacy_read_only') fail('LEGACY_RESUME_SOURCE_UNSUPPORTED')

  const root = path.resolve(sourceWorkspaceRoot)
  const control = path.join(root, '.fbsir-board')
  const targets = {
    marker: path.join(control, 'workspace.json'),
    plan: path.join(control, 'plans', `${sourceRunId}.json`),
    event: path.join(control, 'events', `${sourceRunId}.jsonl`),
    checkpoint: path.join(control, 'checkpoints', `${sourceRunId}.json`),
    collection: path.join(control, 'collections', `${sourceRunId}.json`),
    delivery: path.join(control, 'deliveries', `${sourceRunId}.json`),
  }
  const marker = await readIsolatedFile(root, targets.marker)
  const plan = await readIsolatedFile(root, targets.plan)
  const event = await readIsolatedFile(root, targets.event)
  const checkpoint = await readIsolatedFile(root, targets.checkpoint, { required: false })
  const collection = await readIsolatedFile(root, targets.collection, { required: false })
  const delivery = await readIsolatedFile(root, targets.delivery, { required: false })
  const deliverables = await listDeliverables(root)

  const capturedMarker = inspectWorkspaceMarkerBytes(marker.bytes)
  if (capturedMarker.accessMode !== 'legacy_read_only') fail('LEGACY_RESUME_SOURCE_UNSUPPORTED')
  let verifiedEvent
  try { verifiedEvent = verifyLegacyEventLedgerBytes(event.bytes, sourceRunId) }
  catch { fail('LEGACY_RESUME_EVENT_LEDGER_INVALID') }
  delete marker.bytes
  delete plan.bytes
  delete event.bytes
  if (checkpoint) delete checkpoint.bytes
  if (collection) delete collection.bytes
  if (delivery) delete delivery.bytes
  const byteInventory = [marker, plan, event, checkpoint, collection, delivery, ...deliverables]
    .filter(Boolean)
    .map(publicFileRecord)
    .sort(lexicalPathOrder)
  const deliverableInventory = deliverables.map(publicFileRecord)
  const source = {
    product: PACKAGE_ID,
    productVersion: LEGACY_WORKSPACE_RELEASE.productVersion,
    workspaceSchema: LEGACY_WORKSPACE_RELEASE.workspaceSchema,
    workspaceIdHash: sha256(capturedMarker.marker.workspaceId),
    runIdHash: sha256(sourceRunId),
  }
  const bindings = {
    markerSha256: marker.sha256,
    planSha256: plan.sha256,
    eventChainHead: verifiedEvent.chainHead,
    checkpointSha256: checkpoint?.sha256 || null,
    collectionSha256: collection?.sha256 || null,
    deliverySha256: delivery?.sha256 || null,
    deliverableInventorySha256: domainSha256('fbsir.deliverable-inventory/v1', deliverableInventory),
  }
  const digestReceipt = validateLegacyResumeDigestReceipt({
    schema: LEGACY_RESUME_DIGEST_SCHEMA,
    source,
    bindings,
    legacyResumeDigest: domainSha256(LEGACY_RESUME_DIGEST_SCHEMA, { source, bindings, byteInventory }),
    accessMode: 'legacy_read_only',
    contentExported: false,
  })
  return {
    digestReceipt,
    summary: {
      sourceRunIdHash: source.runIdHash,
      eventCount: verifiedEvent.eventCount,
      deliverableCount: deliverableInventory.length,
      deliverables: deliverableInventory.map((item) => ({ relativePath: item.path, size: item.size, sha256: item.sha256 })),
    },
    evidenceBoundary: LEGACY_RESUME_EVIDENCE_BOUNDARY,
  }
}

async function inspectExactPredecessorResume({ sourceWorkspaceRoot, sourceRunId } = {}) {
  if (typeof sourceWorkspaceRoot !== 'string' || !sourceWorkspaceRoot.trim()) fail('PREDECESSOR_RESUME_SOURCE_REQUIRED')
  if (typeof sourceRunId !== 'string' || !RUN_ID_PATTERN.test(sourceRunId)) fail('PREDECESSOR_RESUME_RUN_ID_INVALID')
  const inspected = await inspectWorkspace(sourceWorkspaceRoot)
  if (inspected.accessMode !== 'predecessor_read_only') fail('PREDECESSOR_RESUME_SOURCE_UNSUPPORTED')

  const root = path.resolve(sourceWorkspaceRoot)
  const control = path.join(root, '.fbsir-board')
  const targets = {
    marker: path.join(control, 'workspace.json'),
    plan: path.join(control, 'plans', `${sourceRunId}.json`),
    event: path.join(control, 'events', `${sourceRunId}.jsonl`),
    checkpoint: path.join(control, 'checkpoints', `${sourceRunId}.json`),
    collection: path.join(control, 'collections', `${sourceRunId}.json`),
    delivery: path.join(control, 'deliveries', `${sourceRunId}.json`),
  }
  const marker = await readIsolatedFile(root, targets.marker)
  const plan = await readIsolatedFile(root, targets.plan)
  const event = await readIsolatedFile(root, targets.event)
  const checkpoint = await readIsolatedFile(root, targets.checkpoint, { required: false })
  const collection = await readIsolatedFile(root, targets.collection, { required: false })
  const delivery = await readIsolatedFile(root, targets.delivery, { required: false })
  const deliverables = await listDeliverables(root)

  const capturedMarker = inspectWorkspaceMarkerBytes(marker.bytes)
  if (capturedMarker.accessMode !== 'predecessor_read_only') fail('PREDECESSOR_RESUME_SOURCE_UNSUPPORTED')
  const workspaceScopeHash = sha256({
    workspaceId: capturedMarker.marker.workspaceId,
    workspaceInstanceId: capturedMarker.marker.workspaceInstanceId,
  })
  let verifiedEvent
  try { verifiedEvent = verifyPredecessorEventLedgerBytes(event.bytes, sourceRunId, workspaceScopeHash) }
  catch { fail('PREDECESSOR_RESUME_EVENT_LEDGER_INVALID') }
  delete marker.bytes
  delete plan.bytes
  delete event.bytes
  if (checkpoint) delete checkpoint.bytes
  if (collection) delete collection.bytes
  if (delivery) delete delivery.bytes
  const byteInventory = [marker, plan, event, checkpoint, collection, delivery, ...deliverables]
    .filter(Boolean)
    .map(publicFileRecord)
    .sort(lexicalPathOrder)
  const deliverableInventory = deliverables.map(publicFileRecord)
  const source = {
    product: PACKAGE_ID,
    workspaceRelease: { ...PREDECESSOR_WORKSPACE_RELEASE },
    workspaceIdHash: sha256(capturedMarker.marker.workspaceId),
    runIdHash: sha256(sourceRunId),
  }
  const bindings = {
    markerSha256: marker.sha256,
    planSha256: plan.sha256,
    eventChainHead: verifiedEvent.chainHead,
    checkpointSha256: checkpoint?.sha256 || null,
    collectionSha256: collection?.sha256 || null,
    deliverySha256: delivery?.sha256 || null,
    deliverableInventorySha256: domainSha256('fbsir.deliverable-inventory/v1', deliverableInventory),
  }
  const digestReceipt = validatePredecessorResumeDigestReceipt({
    schema: PREDECESSOR_RESUME_DIGEST_SCHEMA,
    source,
    bindings,
    predecessorResumeDigest: domainSha256(PREDECESSOR_RESUME_DIGEST_SCHEMA, { source, bindings, byteInventory }),
    accessMode: 'predecessor_read_only',
    contentExported: false,
  })
  return {
    digestReceipt,
    summary: {
      sourceRunIdHash: source.runIdHash,
      eventCount: verifiedEvent.eventCount,
      deliverableCount: deliverableInventory.length,
      deliverables: deliverableInventory.map((item) => ({ relativePath: item.path, size: item.size, sha256: item.sha256 })),
    },
    evidenceBoundary: PREDECESSOR_RESUME_EVIDENCE_BOUNDARY,
  }
}

export async function inspectPredecessorResume(input = {}) {
  if (typeof input.sourceWorkspaceRoot !== 'string' || !input.sourceWorkspaceRoot.trim()) fail('PREDECESSOR_RESUME_SOURCE_REQUIRED')
  const inspected = await inspectWorkspace(input.sourceWorkspaceRoot)
  if (inspected.accessMode === 'predecessor_read_only') return inspectExactPredecessorResume(input)
  if (inspected.accessMode === 'legacy_read_only') return inspectLegacyResume(input)
  fail('PREDECESSOR_RESUME_SOURCE_UNSUPPORTED')
}

export async function readLegacyResumeDigestReceipt({ targetWorkspaceRoot, targetRunId } = {}) {
  if (typeof targetWorkspaceRoot !== 'string' || !targetWorkspaceRoot.trim()) fail('LEGACY_RESUME_TARGET_REQUIRED')
  if (typeof targetRunId !== 'string' || !RUN_ID_PATTERN.test(targetRunId)) fail('LEGACY_RESUME_TARGET_RUN_ID_INVALID')
  const root = path.resolve(targetWorkspaceRoot)
  await requireWritableWorkspace(root)
  const receiptRef = `.fbsir-board/predecessors/${targetRunId}.json`
  const target = path.join(root, ...receiptRef.split('/'))
  let captured
  try { captured = await readIsolatedFile(root, target, { domain: 'TARGET' }) }
  catch (error) {
    if (error?.code === 'LEGACY_RESUME_TARGET_FILE_REQUIRED') fail('PREDECESSOR_RECEIPT_REQUIRED')
    throw error
  }
  let parsed
  try { parsed = JSON.parse(captured.bytes.toString('utf8')) }
  catch { fail('PREDECESSOR_RECEIPT_INVALID') }
  const receipt = validateLegacyResumeDigestReceipt(parsed)
  const expectedBytes = Buffer.from(`${JSON.stringify(receipt, null, 2)}\n`, 'utf8')
  if (!captured.bytes.equals(expectedBytes)) fail('PREDECESSOR_RECEIPT_INVALID')
  return { receipt, receiptRef, receiptPayloadHash: sha256(receipt) }
}

export async function readPredecessorResumeDigestReceipt({ targetWorkspaceRoot, targetRunId } = {}) {
  if (typeof targetWorkspaceRoot !== 'string' || !targetWorkspaceRoot.trim()) fail('PREDECESSOR_RESUME_TARGET_REQUIRED')
  if (typeof targetRunId !== 'string' || !RUN_ID_PATTERN.test(targetRunId)) fail('PREDECESSOR_RESUME_TARGET_RUN_ID_INVALID')
  const root = path.resolve(targetWorkspaceRoot)
  await requireWritableWorkspace(root)
  const receiptRef = `.fbsir-board/predecessors/${targetRunId}.json`
  const target = path.join(root, ...receiptRef.split('/'))
  let captured
  try { captured = await readIsolatedFile(root, target, { domain: 'TARGET' }) }
  catch (error) {
    if (error?.code === 'LEGACY_RESUME_TARGET_FILE_REQUIRED') fail('PREDECESSOR_RECEIPT_REQUIRED')
    throw error
  }
  let parsed
  try { parsed = JSON.parse(captured.bytes.toString('utf8')) }
  catch { fail('PREDECESSOR_RECEIPT_INVALID') }
  const receipt = validateResumeDigestReceipt(parsed)
  const expectedBytes = Buffer.from(`${JSON.stringify(receipt, null, 2)}\n`, 'utf8')
  if (!captured.bytes.equals(expectedBytes)) fail('PREDECESSOR_RECEIPT_INVALID')
  return { receipt, receiptRef, receiptPayloadHash: sha256(receipt) }
}

export function resumeDigestFromReceipt(receipt) {
  const validated = validateResumeDigestReceipt(receipt)
  return validated.schema === LEGACY_RESUME_DIGEST_SCHEMA
    ? validated.legacyResumeDigest
    : validated.predecessorResumeDigest
}

function planReferenceFor(receipt, receiptRef, receiptPayloadHash) {
  return {
    schema: PREDECESSOR_RUN_REF_SCHEMA,
    receiptRef,
    receiptPayloadHash,
    sourceRunIdHash: receipt.source.runIdHash,
    resumeDigestSchema: receipt.schema,
    resumeDigest: resumeDigestFromReceipt(receipt),
  }
}

async function publishDigestReceipt(targetRoot, target, digestReceipt) {
  const parent = path.dirname(target)
  await assertWorkspacePathNoLinks(parent, 'LEGACY_RESUME_TARGET_LINK_FORBIDDEN')
  let parentPathBefore
  try { parentPathBefore = await lstat(parent, { bigint: true }) }
  catch { fail('LEGACY_RESUME_TARGET_PARENT_INVALID') }
  if (!parentPathBefore.isDirectory() || parentPathBefore.isSymbolicLink()) fail('LEGACY_RESUME_TARGET_PARENT_INVALID')
  let parentHandle
  try { parentHandle = await open(parent, 'r') }
  catch { fail('LEGACY_RESUME_TARGET_ATOMIC_PUBLISH_UNAVAILABLE') }
  const expectedBytes = Buffer.from(`${JSON.stringify(digestReceipt, null, 2)}\n`, 'utf8')
  const assertParentStable = async () => {
    const opened = await parentHandle.stat({ bigint: true })
    let current
    try { current = await lstat(parent, { bigint: true }) }
    catch { fail('LEGACY_RESUME_TARGET_PARENT_CHANGED') }
    if (!opened.isDirectory() || opened.isSymbolicLink() || !sameIdentityStat(parentPathBefore, opened)
      || !sameIdentityStat(opened, current) || current.isSymbolicLink()) fail('LEGACY_RESUME_TARGET_PARENT_CHANGED')
  }
  try {
    await assertParentStable()
    let existing
    try { existing = await readIsolatedFile(targetRoot, target, { domain: 'TARGET' }) }
    catch (error) {
      if (error?.code !== 'LEGACY_RESUME_TARGET_FILE_REQUIRED') throw error
    }
    if (existing) {
      if (!existing.bytes.equals(expectedBytes)) fail('LEGACY_RESUME_RECEIPT_CONFLICT')
      await assertParentStable()
      return true
    }

    const temp = `${target}.${process.pid}.${randomBytes(6).toString('hex')}.tmp`
    let handle
    try {
      await assertParentStable()
      handle = await open(temp, fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY, 0o600)
      await assertParentStable()
      await handle.writeFile(expectedBytes)
      await handle.sync()
      await handle.close()
      handle = null
      try { await link(temp, target) }
      catch (error) {
        if (error?.code !== 'EEXIST') throw error
        const winner = await readIsolatedFile(targetRoot, target, { domain: 'TARGET' })
        if (!winner.bytes.equals(expectedBytes)) fail('LEGACY_RESUME_RECEIPT_CONFLICT')
        await assertParentStable()
        return true
      }
      await assertParentStable()
      return false
    } finally {
      await handle?.close()
      try { await unlink(temp) } catch (error) { if (error?.code !== 'ENOENT') throw error }
    }
  } finally {
    await parentHandle?.close()
  }
}

export async function recordLegacyResumeDigestUnlocked({ sourceWorkspaceRoot, sourceRunId, targetWorkspaceRoot, targetRunId } = {}) {
  if (typeof sourceWorkspaceRoot !== 'string' || !sourceWorkspaceRoot.trim()) fail('LEGACY_RESUME_SOURCE_REQUIRED')
  if (typeof targetWorkspaceRoot !== 'string' || !targetWorkspaceRoot.trim()) fail('LEGACY_RESUME_TARGET_REQUIRED')
  if (typeof targetRunId !== 'string' || !RUN_ID_PATTERN.test(targetRunId)) fail('LEGACY_RESUME_TARGET_RUN_ID_INVALID')
  if (targetRunId === sourceRunId) fail('LEGACY_RESUME_RUN_SCOPE_INVALID', 'A read-only predecessor must resume into a different new run')
  const roots = assertSeparatedWorkspaceRoots(sourceWorkspaceRoot, targetWorkspaceRoot)
  const inspected = await inspectLegacyResume({ sourceWorkspaceRoot: roots.source, sourceRunId })
  await requireWritableWorkspace(roots.target)
  const repeated = await inspectLegacyResume({ sourceWorkspaceRoot: roots.source, sourceRunId })
  if (repeated.digestReceipt.legacyResumeDigest !== inspected.digestReceipt.legacyResumeDigest) fail('LEGACY_RESUME_SOURCE_CHANGED_DURING_READ')

  const receiptRef = `.fbsir-board/predecessors/${targetRunId}.json`
  const target = path.join(roots.target, ...receiptRef.split('/'))
  await assertWorkspacePathNoLinks(target, 'LEGACY_RESUME_TARGET_LINK_FORBIDDEN')
  const idempotent = await publishDigestReceipt(roots.target, target, inspected.digestReceipt)
  return {
    digestReceipt: inspected.digestReceipt,
    receiptRef,
    receiptPayloadHash: sha256(inspected.digestReceipt),
    idempotent,
    summary: inspected.summary,
    evidenceBoundary: LEGACY_RESUME_EVIDENCE_BOUNDARY,
  }
}

export async function recordPredecessorResumeDigestUnlocked({ sourceWorkspaceRoot, sourceRunId, targetWorkspaceRoot, targetRunId } = {}) {
  if (typeof sourceWorkspaceRoot !== 'string' || !sourceWorkspaceRoot.trim()) fail('PREDECESSOR_RESUME_SOURCE_REQUIRED')
  if (typeof targetWorkspaceRoot !== 'string' || !targetWorkspaceRoot.trim()) fail('PREDECESSOR_RESUME_TARGET_REQUIRED')
  if (typeof targetRunId !== 'string' || !RUN_ID_PATTERN.test(targetRunId)) fail('PREDECESSOR_RESUME_TARGET_RUN_ID_INVALID')
  if (targetRunId === sourceRunId) fail('PREDECESSOR_RESUME_RUN_SCOPE_INVALID', 'A read-only predecessor must resume into a different new run')
  const roots = assertSeparatedWorkspaceRoots(sourceWorkspaceRoot, targetWorkspaceRoot)
  const inspected = await inspectPredecessorResume({ sourceWorkspaceRoot: roots.source, sourceRunId })
  await requireWritableWorkspace(roots.target)
  const repeated = await inspectPredecessorResume({ sourceWorkspaceRoot: roots.source, sourceRunId })
  if (resumeDigestFromReceipt(repeated.digestReceipt) !== resumeDigestFromReceipt(inspected.digestReceipt)) {
    fail('PREDECESSOR_RESUME_SOURCE_CHANGED_DURING_READ')
  }

  const receiptRef = `.fbsir-board/predecessors/${targetRunId}.json`
  const target = path.join(roots.target, ...receiptRef.split('/'))
  await assertWorkspacePathNoLinks(target, 'LEGACY_RESUME_TARGET_LINK_FORBIDDEN')
  const idempotent = await publishDigestReceipt(roots.target, target, inspected.digestReceipt)
  const receiptPayloadHash = sha256(inspected.digestReceipt)
  return {
    digestReceipt: inspected.digestReceipt,
    receiptRef,
    receiptPayloadHash,
    planReference: planReferenceFor(inspected.digestReceipt, receiptRef, receiptPayloadHash),
    idempotent,
    summary: inspected.summary,
    evidenceBoundary: inspected.evidenceBoundary,
  }
}
