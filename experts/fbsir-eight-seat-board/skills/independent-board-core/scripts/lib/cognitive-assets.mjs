import { createHash, randomUUID } from 'node:crypto'
import { lstat, mkdir, open, readFile, rename, unlink, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const CATALOG_SCHEMA = 'fbsir.cognitive-asset-manifest/v1'
export const SOURCE_LEDGER_SCHEMA = 'fbsir.cognitive-source-ledger/v1'
export const SELECTION_REQUEST_SCHEMA = 'fbsir.asset-selection-request/v1'
export const BUNDLE_SCHEMA = 'fbsir.asset-bundle/v1'
export const BUNDLE_VERIFY_REQUEST_SCHEMA = 'fbsir.asset-bundle-verification-request/v1'
export const DECISION_CARD_HASH_REQUEST_SCHEMA = 'fbsir.decision-card-hash-request/v1'

const MODULE_DIR = path.dirname(fileURLToPath(import.meta.url))
const DEFAULT_ASSET_ROOT = path.resolve(MODULE_DIR, '..', '..', 'references', 'cognitive-assets')
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/
const SOURCE_ID_PATTERN = /^src:[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/
const HEX_64 = /^[0-9a-f]{64}$/
const VERSION_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/
const ASSET_BUNDLE_REF_PATTERN = /^assetbundle:[0-9a-f]{64}$/
const KINDS = new Set(['method', 'checklist', 'counterexample', 'case'])
const PHASES = new Set(['phase0_intake', 'phase1_independent', 'phase1_process_support', 'phase2_challenge', 'phase3_synthesis'])
const VALIDITY_CLASSES = new Set(['structural_method', 'internal_curated', 'historical_case', 'periodic_benchmark', 'live_fact', 'legal_authority'])
const STALE_POLICIES = new Set(['exclude', 'require_review', 'require_live_verification'])
const REQUIRED_SCHEMA_FILES = [
  'asset-manifest.schema.json', 'source-ledger.schema.json', 'asset-bundle.schema.json',
  'method-card.schema.json', 'checklist-card.schema.json', 'counterexample-card.schema.json', 'case-card.schema.json',
]
const MANIFEST_KEYS = new Set(['schema', 'catalogVersion', 'productVersion', 'generatedAt', 'seatIds', 'phasePolicies', 'assets', 'evidenceBoundary'])
const PHASE_POLICY_KEYS = new Set(['allowedKinds', 'requiredKinds', 'maxItems', 'maxChars'])
const ASSET_KEYS = new Set([
  'assetId', 'kind', 'version', 'status', 'ownerSeatIds', 'phaseAllowlist', 'sceneIds',
  'isDefaultForSeat', 'priority', 'triggers', 'exclusions', 'applicability', 'freshness',
  'sourceRefs', 'contentPath', 'contentSha256', 'contentChars', 'requiredHeadings',
  'productionEligible', 'supersedes', 'changeSummary',
])
const APPLICABILITY_KEYS = new Set(['jurisdictions', 'industries', 'companyStages', 'decisionTypes', 'requires', 'notFor'])
const FRESHNESS_KEYS = new Set(['validityClass', 'asOf', 'reviewBy', 'stalePolicy'])
const SOURCE_LEDGER_KEYS = new Set(['schema', 'catalogVersion', 'sources', 'evidenceBoundary'])
const SOURCE_KEYS = new Set([
  'sourceId', 'sourceType', 'title', 'publisherOrOwner', 'locator', 'publishedAt', 'retrievedAt',
  'effectiveFrom', 'effectiveTo', 'jurisdictions', 'authorityLevel', 'verificationStatus',
  'contentSha256', 'rightsBoundary', 'sensitivity', 'reviewBy', 'stalePolicy', 'summary',
])
const SELECTION_KEYS = new Set(['schema', 'agendaItemId', 'seatId', 'revision', 'phase', 'decisionCardHash', 'sceneIds', 'routingTerms', 'asOf'])
const VERIFY_KEYS = new Set(['schema', 'agendaItemId', 'seatId', 'revision', 'phase', 'decisionCardHash', 'bundleRef', 'asOf'])
const DECISION_CARD_HASH_KEYS = new Set(['schema', 'content'])
const BUNDLE_KEYS = new Set([
  'schema', 'catalogVersion', 'asOf', 'agendaItemId', 'seatId', 'revision', 'phase',
  'decisionCardHash', 'routingInput', 'routingInputHash', 'selectedAssets', 'routingReasons', 'charCount',
  'evidenceBoundary', 'bundleDigest',
])
const BUNDLE_ASSET_KEYS = new Set(['assetId', 'kind', 'version', 'ownerSeatIds', 'sourceRefs', 'contentPath', 'contentSha256', 'content'])
const ROUTING_INPUT_KEYS = new Set(['sceneIds', 'routingTerms'])
const ROUTING_REASON_KEYS = new Set(['assetId', 'kind', 'score', 'reasonCodes'])
const HEADING_SETS = Object.freeze({
  method: ['决策问题', '适用与不适用', '最小输入', '方法步骤', '输出形状', '失败模式', '停止与人工关卡', '来源与边界'],
  checklist: ['使用时点', '检查项', '完成规则', '缺失处理', '来源与边界'],
  counterexample: ['诱人主张', '失败机制', '识别信号', '反证要求', '更安全替代', '来源与边界'],
  case: ['情境', '决策', '可得证据', '过程', '结果与观察期', '干扰因素', '可迁移模式', '不可迁移边界', '来源与匿名化'],
})
const KIND_ORDER = Object.freeze({ method: 0, checklist: 1, counterexample: 2, case: 3 })
const INJECTION_PATTERN = /(ignore\s+(all\s+)?previous\s+instructions|忽略.{0,10}(之前|以上).{0,10}(指令|规则)|\bTeamCreate\s*\(|\bSendMessage\s*\()/i

function fail(code, message = code, details = {}) {
  const error = new Error(message)
  error.code = code
  error.details = details
  throw error
}

function invariant(condition, code, message = code, details = {}) {
  if (!condition) fail(code, message, details)
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function assertExactKeys(value, allowed, code) {
  invariant(isObject(value), code, 'Expected an object')
  const unexpected = Object.keys(value).filter((key) => !allowed.has(key))
  invariant(unexpected.length === 0, code, 'Object contains undeclared fields', { unexpected })
}

function requiredKeys(value, required, code) {
  const missing = required.filter((key) => !Object.hasOwn(value, key))
  invariant(missing.length === 0, code, 'Object is missing required fields', { missing })
}

function nonEmptyText(value, code, max = 1000) {
  invariant(typeof value === 'string' && value.trim().length > 0 && value.length <= max, code)
  return value.trim()
}

function safeId(value, code) {
  invariant(typeof value === 'string' && ID_PATTERN.test(value), code)
  return value
}

function safeSourceId(value, code) {
  invariant(typeof value === 'string' && SOURCE_ID_PATTERN.test(value), code)
  return value
}

function dateOnly(value, code, nullable = false) {
  if (value === null && nullable) return null
  invariant(typeof value === 'string' && DATE_PATTERN.test(value), code)
  const parsed = new Date(`${value}T00:00:00.000Z`)
  invariant(!Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value, code)
  return value
}

function stringArray(value, code, { min = 0, max = 40, itemMax = 200, pattern = null } = {}) {
  invariant(Array.isArray(value) && value.length >= min && value.length <= max, code)
  const normalized = value.map((item) => nonEmptyText(item, code, itemMax))
  invariant(new Set(normalized).size === normalized.length, code, 'Array values must be unique')
  if (pattern) normalized.forEach((item) => invariant(pattern.test(item), code))
  return normalized
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map((entry) => canonical(entry)).join(',')}]`
  if (isObject(value)) return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`
  return JSON.stringify(value)
}

export function cognitiveSha256(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === 'string' ? value : canonical(value), 'utf8')
  return createHash('sha256').update(bytes).digest('hex')
}

export function hashDecisionCard(input) {
  assertExactKeys(input, DECISION_CARD_HASH_KEYS, 'DECISION_CARD_HASH_FIELD_FORBIDDEN')
  requiredKeys(input, [...DECISION_CARD_HASH_KEYS], 'DECISION_CARD_HASH_FIELD_REQUIRED')
  invariant(input.schema === DECISION_CARD_HASH_REQUEST_SCHEMA, 'DECISION_CARD_HASH_SCHEMA_INVALID')
  nonEmptyText(input.content, 'DECISION_CARD_HASH_CONTENT_INVALID', 20000)
  const normalized = normalizeContent(input.content).trim()
  return {
    schema: 'fbsir.decision-card-hash/v1',
    decisionCardHash: cognitiveSha256(normalized),
    charCount: charCount(normalized),
    evidenceBoundary: 'transient_normalized_decision_card_hash_only_content_not_persisted',
  }
}

function normalizeContent(value) {
  return value.replace(/\r\n?/g, '\n')
}

function charCount(value) {
  return Array.from(value).length
}

function ensureWithin(root, target, code = 'ASSET_PATH_OUTSIDE_ROOT') {
  const relative = path.relative(path.resolve(root), path.resolve(target))
  invariant(relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative)), code, 'Resolved path escapes its root', { root, target })
}

async function rejectExistingSymlinkSegments(root, target, code = 'ASSET_SYMLINK_PATH_FORBIDDEN') {
  const resolvedRoot = path.resolve(root)
  const resolvedTarget = path.resolve(target)
  ensureWithin(resolvedRoot, resolvedTarget, code)
  const relative = path.relative(resolvedRoot, resolvedTarget)
  let cursor = resolvedRoot
  for (const segment of relative.split(path.sep).filter(Boolean)) {
    cursor = path.join(cursor, segment)
    try {
      const info = await lstat(cursor)
      invariant(!info.isSymbolicLink(), code, 'Workspace asset path must not contain symbolic links', { path: cursor })
    } catch (error) {
      if (error?.code === 'ENOENT') return
      throw error
    }
  }
}

async function readJson(filePath, code) {
  let raw
  try { raw = await readFile(filePath, 'utf8') }
  catch (error) { fail(code, `Unable to read ${filePath}`, { cause: error.code }) }
  try { return JSON.parse(raw) }
  catch (error) { fail(code, `Invalid JSON in ${filePath}`, { cause: error.message }) }
}

async function regularFile(filePath, code) {
  let info
  try { info = await lstat(filePath) }
  catch (error) { fail(code, `Required file is missing: ${filePath}`, { cause: error.code }) }
  invariant(info.isFile() && !info.isSymbolicLink(), code, 'Path must be a regular non-symlink file', { filePath })
}

function setEquals(left, right) {
  return left.size === right.size && [...left].every((item) => right.has(item))
}

function sameStringSet(left, right) {
  return setEquals(new Set(left), new Set(right))
}

function uniqueSorted(values) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b))
}

function isStale(reviewBy, asOf) {
  return reviewBy < asOf
}

function sourceEffectivity(source, asOf) {
  if (source.effectiveFrom !== null && source.effectiveFrom > asOf) return 'not_yet_effective'
  if (source.effectiveTo !== null && source.effectiveTo < asOf) return 'expired'
  return 'effective'
}

function isSourceAvailable(source, asOf) {
  return !isStale(source.reviewBy, asOf) && sourceEffectivity(source, asOf) === 'effective'
}

export function defaultCognitiveAssetRoot() {
  return DEFAULT_ASSET_ROOT
}

async function validateSchemas(assetRoot) {
  const schemaRoot = path.join(assetRoot, 'schemas')
  for (const fileName of REQUIRED_SCHEMA_FILES) {
    const filePath = path.join(schemaRoot, fileName)
    ensureWithin(schemaRoot, filePath, 'ASSET_SCHEMA_PATH_INVALID')
    await regularFile(filePath, 'ASSET_SCHEMA_FILE_INVALID')
    const schema = await readJson(filePath, 'ASSET_SCHEMA_JSON_INVALID')
    invariant(schema.$schema === 'https://json-schema.org/draft/2020-12/schema', 'ASSET_SCHEMA_DIALECT_INVALID', undefined, { fileName })
  }
}

async function validateRoster(assetRoot, seatIds) {
  const packageRoot = path.resolve(assetRoot, '..', '..', '..', '..')
  const pluginPath = path.join(packageRoot, '.codebuddy-plugin', 'plugin.json')
  ensureWithin(packageRoot, pluginPath, 'ASSET_PLUGIN_PATH_INVALID')
  const plugin = await readJson(pluginPath, 'ASSET_PLUGIN_MANIFEST_INVALID')
  invariant(Array.isArray(plugin.members), 'ASSET_PLUGIN_ROSTER_INVALID')
  const pluginSeats = new Set(plugin.members.map((member) => safeId(member?.id, 'ASSET_PLUGIN_SEAT_ID_INVALID')))
  const catalogSeats = new Set(seatIds)
  invariant(setEquals(pluginSeats, catalogSeats), 'ASSET_SEAT_ROSTER_MISMATCH', 'Cognitive asset seatIds must exactly match the current plugin roster', {
    missingFromCatalog: [...pluginSeats].filter((id) => !catalogSeats.has(id)),
    unavailableInPlugin: [...catalogSeats].filter((id) => !pluginSeats.has(id)),
  })
  return packageRoot
}

async function validateSceneIds(assetRoot, assets) {
  const lexiconPath = path.resolve(assetRoot, '..', 'scene-lexicon.v1.json')
  const lexicon = await readJson(lexiconPath, 'ASSET_SCENE_LEXICON_INVALID')
  invariant(lexicon.schema === 'fbsir.scene-lexicon/v1' && Array.isArray(lexicon.scenes), 'ASSET_SCENE_LEXICON_INVALID')
  const valid = new Set(lexicon.scenes.map((scene) => scene.sceneId))
  for (const asset of assets) {
    for (const sceneId of asset.sceneIds) invariant(sceneId === '*' || valid.has(sceneId), 'ASSET_SCENE_ID_INVALID', undefined, { assetId: asset.assetId, sceneId })
  }
  return valid
}

function validateSource(source) {
  assertExactKeys(source, SOURCE_KEYS, 'ASSET_SOURCE_FIELD_FORBIDDEN')
  requiredKeys(source, [...SOURCE_KEYS], 'ASSET_SOURCE_FIELD_REQUIRED')
  safeSourceId(source.sourceId, 'ASSET_SOURCE_ID_INVALID')
  invariant(['internal_curated', 'user_first_party', 'official_primary', 'research_primary', 'standard', 'secondary'].includes(source.sourceType), 'ASSET_SOURCE_TYPE_INVALID')
  nonEmptyText(source.title, 'ASSET_SOURCE_TITLE_INVALID', 300)
  nonEmptyText(source.publisherOrOwner, 'ASSET_SOURCE_PUBLISHER_INVALID', 200)
  nonEmptyText(source.locator, 'ASSET_SOURCE_LOCATOR_INVALID', 1000)
  dateOnly(source.publishedAt, 'ASSET_SOURCE_PUBLISHED_DATE_INVALID', true)
  dateOnly(source.retrievedAt, 'ASSET_SOURCE_RETRIEVED_DATE_INVALID')
  dateOnly(source.effectiveFrom, 'ASSET_SOURCE_EFFECTIVE_FROM_INVALID', true)
  dateOnly(source.effectiveTo, 'ASSET_SOURCE_EFFECTIVE_TO_INVALID', true)
  invariant(source.effectiveFrom === null || source.effectiveTo === null || source.effectiveFrom <= source.effectiveTo, 'ASSET_SOURCE_EFFECTIVE_RANGE_INVALID', undefined, { sourceId: source.sourceId })
  stringArray(source.jurisdictions, 'ASSET_SOURCE_JURISDICTIONS_INVALID', { min: 1, max: 20, itemMax: 40 })
  invariant(['internal_curated', 'user_first_party', 'official_primary', 'peer_reviewed_primary', 'standards_body', 'secondary'].includes(source.authorityLevel), 'ASSET_SOURCE_AUTHORITY_INVALID')
  invariant(['curated_summary', 'link_verified', 'content_hash_verified', 'needs_review'].includes(source.verificationStatus), 'ASSET_SOURCE_VERIFICATION_INVALID')
  invariant(source.contentSha256 === null || (typeof source.contentSha256 === 'string' && HEX_64.test(source.contentSha256)), 'ASSET_SOURCE_HASH_INVALID')
  invariant(['internal_authorized_summary', 'user_authorized', 'public_official_link_short_summary', 'link_and_short_paraphrase_only'].includes(source.rightsBoundary), 'ASSET_SOURCE_RIGHTS_INVALID')
  invariant(['public', 'internal', 'confidential', 'restricted'].includes(source.sensitivity), 'ASSET_SOURCE_SENSITIVITY_INVALID')
  dateOnly(source.reviewBy, 'ASSET_SOURCE_REVIEW_DATE_INVALID')
  invariant(STALE_POLICIES.has(source.stalePolicy), 'ASSET_SOURCE_STALE_POLICY_INVALID')
  nonEmptyText(source.summary, 'ASSET_SOURCE_SUMMARY_INVALID', 500)
  if (['official_primary', 'research_primary', 'standard', 'secondary'].includes(source.sourceType)) {
    invariant(/^https:\/\//i.test(source.locator), 'ASSET_EXTERNAL_SOURCE_HTTPS_REQUIRED', undefined, { sourceId: source.sourceId })
    invariant(source.sensitivity === 'public', 'ASSET_EXTERNAL_SOURCE_MUST_BE_PUBLIC', undefined, { sourceId: source.sourceId })
  }
}

function validateApplicability(value, assetId) {
  assertExactKeys(value, APPLICABILITY_KEYS, 'ASSET_APPLICABILITY_FIELD_FORBIDDEN')
  requiredKeys(value, [...APPLICABILITY_KEYS], 'ASSET_APPLICABILITY_FIELD_REQUIRED')
  for (const key of ['jurisdictions', 'industries', 'companyStages', 'decisionTypes']) stringArray(value[key], 'ASSET_APPLICABILITY_LIST_INVALID', { min: 1, max: 30, itemMax: 160 })
  for (const key of ['requires', 'notFor']) stringArray(value[key], 'ASSET_APPLICABILITY_LIST_INVALID', { min: 0, max: 30, itemMax: 160 })
  invariant(value.jurisdictions.length > 0, 'ASSET_APPLICABILITY_JURISDICTION_REQUIRED', undefined, { assetId })
}

function validateFreshness(value) {
  assertExactKeys(value, FRESHNESS_KEYS, 'ASSET_FRESHNESS_FIELD_FORBIDDEN')
  requiredKeys(value, [...FRESHNESS_KEYS], 'ASSET_FRESHNESS_FIELD_REQUIRED')
  invariant(VALIDITY_CLASSES.has(value.validityClass), 'ASSET_VALIDITY_CLASS_INVALID')
  dateOnly(value.asOf, 'ASSET_AS_OF_INVALID')
  dateOnly(value.reviewBy, 'ASSET_REVIEW_BY_INVALID')
  invariant(value.reviewBy >= value.asOf, 'ASSET_REVIEW_BEFORE_AS_OF')
  invariant(STALE_POLICIES.has(value.stalePolicy), 'ASSET_STALE_POLICY_INVALID')
}

function validatePhasePolicy(name, policy) {
  assertExactKeys(policy, PHASE_POLICY_KEYS, 'ASSET_PHASE_POLICY_FIELD_FORBIDDEN')
  requiredKeys(policy, [...PHASE_POLICY_KEYS], 'ASSET_PHASE_POLICY_FIELD_REQUIRED')
  const allowedKinds = stringArray(policy.allowedKinds, 'ASSET_PHASE_ALLOWED_KINDS_INVALID', { min: 1, max: 4, itemMax: 20 })
  const requiredKinds = stringArray(policy.requiredKinds, 'ASSET_PHASE_REQUIRED_KINDS_INVALID', { min: 0, max: 4, itemMax: 20 })
  allowedKinds.forEach((kind) => invariant(KINDS.has(kind), 'ASSET_PHASE_KIND_INVALID'))
  requiredKinds.forEach((kind) => invariant(allowedKinds.includes(kind), 'ASSET_PHASE_REQUIRED_KIND_NOT_ALLOWED'))
  invariant(Number.isInteger(policy.maxItems) && policy.maxItems >= 1 && policy.maxItems <= 4, 'ASSET_PHASE_MAX_ITEMS_INVALID')
  invariant(Number.isInteger(policy.maxChars) && policy.maxChars >= 200 && policy.maxChars <= 12000, 'ASSET_PHASE_MAX_CHARS_INVALID')
  invariant(policy.maxItems >= requiredKinds.length, 'ASSET_PHASE_REQUIRED_KIND_BUDGET_INVALID')
  if (name.startsWith('phase1_')) invariant(!allowedKinds.includes('case') && !allowedKinds.includes('counterexample'), 'ASSET_PHASE1_ANCHORING_KIND_FORBIDDEN')
}

async function validateAsset(assetRoot, asset, manifest, sourceMap) {
  assertExactKeys(asset, ASSET_KEYS, 'ASSET_FIELD_FORBIDDEN')
  requiredKeys(asset, [...ASSET_KEYS], 'ASSET_FIELD_REQUIRED')
  safeId(asset.assetId, 'ASSET_ID_INVALID')
  invariant(KINDS.has(asset.kind), 'ASSET_KIND_INVALID')
  invariant(typeof asset.version === 'string' && VERSION_PATTERN.test(asset.version), 'ASSET_VERSION_INVALID')
  invariant(['active', 'deprecated', 'withdrawn'].includes(asset.status), 'ASSET_STATUS_INVALID')
  const owners = stringArray(asset.ownerSeatIds, 'ASSET_OWNER_SEATS_INVALID', { min: 1, max: 9, itemMax: 128, pattern: ID_PATTERN })
  owners.forEach((seatId) => invariant(manifest.seatIds.includes(seatId), 'ASSET_OWNER_SEAT_UNAVAILABLE', undefined, { assetId: asset.assetId, seatId }))
  const phases = stringArray(asset.phaseAllowlist, 'ASSET_PHASE_ALLOWLIST_INVALID', { min: 1, max: 5, itemMax: 40 })
  phases.forEach((phase) => {
    invariant(PHASES.has(phase), 'ASSET_PHASE_INVALID')
    invariant(manifest.phasePolicies[phase].allowedKinds.includes(asset.kind), 'ASSET_KIND_NOT_ALLOWED_IN_PHASE', undefined, { assetId: asset.assetId, phase })
  })
  stringArray(asset.sceneIds, 'ASSET_SCENE_IDS_INVALID', { min: 1, max: 10, itemMax: 64 })
  invariant(typeof asset.isDefaultForSeat === 'boolean', 'ASSET_DEFAULT_FLAG_INVALID')
  invariant(Number.isInteger(asset.priority) && asset.priority >= 0 && asset.priority <= 1000, 'ASSET_PRIORITY_INVALID')
  stringArray(asset.triggers, 'ASSET_TRIGGERS_INVALID', { min: 0, max: 30, itemMax: 80 })
  stringArray(asset.exclusions, 'ASSET_EXCLUSIONS_INVALID', { min: 0, max: 30, itemMax: 80 })
  validateApplicability(asset.applicability, asset.assetId)
  validateFreshness(asset.freshness)
  const sourceRefs = stringArray(asset.sourceRefs, 'ASSET_SOURCE_REFS_INVALID', { min: 1, max: 20, itemMax: 124, pattern: SOURCE_ID_PATTERN })
  sourceRefs.forEach((sourceRef) => invariant(sourceMap.has(sourceRef), 'ASSET_SOURCE_REF_UNRESOLVED', undefined, { assetId: asset.assetId, sourceRef }))
  invariant(typeof asset.contentPath === 'string' && asset.contentPath.endsWith('.md') && !asset.contentPath.includes('\\') && !asset.contentPath.split('/').includes('..'), 'ASSET_CONTENT_PATH_INVALID')
  invariant(typeof asset.contentSha256 === 'string' && HEX_64.test(asset.contentSha256), 'ASSET_CONTENT_HASH_INVALID')
  invariant(Number.isInteger(asset.contentChars) && asset.contentChars > 0 && asset.contentChars <= 12000, 'ASSET_CONTENT_CHARS_INVALID')
  const headings = stringArray(asset.requiredHeadings, 'ASSET_REQUIRED_HEADINGS_INVALID', { min: 1, max: 12, itemMax: 80 })
  invariant(sameStringSet(headings, HEADING_SETS[asset.kind]), 'ASSET_REQUIRED_HEADINGS_KIND_MISMATCH', undefined, { assetId: asset.assetId, kind: asset.kind })
  invariant(typeof asset.productionEligible === 'boolean', 'ASSET_PRODUCTION_FLAG_INVALID')
  invariant(asset.supersedes === null || (typeof asset.supersedes === 'string' && ID_PATTERN.test(asset.supersedes)), 'ASSET_SUPERSEDES_INVALID')
  nonEmptyText(asset.changeSummary, 'ASSET_CHANGE_SUMMARY_INVALID', 300)
  if (asset.kind === 'case' && asset.productionEligible) invariant(asset.freshness.validityClass === 'historical_case', 'ASSET_PRODUCTION_CASE_FRESHNESS_INVALID')
  if (asset.kind === 'counterexample' || asset.kind === 'case') invariant(!asset.phaseAllowlist.some((phase) => phase.startsWith('phase1_')), 'ASSET_PHASE1_OUTCOME_CARD_FORBIDDEN')

  const contentFile = path.resolve(assetRoot, asset.contentPath)
  ensureWithin(assetRoot, contentFile)
  await regularFile(contentFile, 'ASSET_CONTENT_FILE_INVALID')
  const content = normalizeContent(await readFile(contentFile, 'utf8'))
  invariant(cognitiveSha256(content) === asset.contentSha256, 'ASSET_CONTENT_HASH_MISMATCH', undefined, { assetId: asset.assetId })
  invariant(charCount(content) === asset.contentChars, 'ASSET_CONTENT_CHAR_COUNT_MISMATCH', undefined, { assetId: asset.assetId, expected: asset.contentChars, actual: charCount(content) })
  headings.forEach((heading) => invariant(content.includes(`## ${heading}`), 'ASSET_CONTENT_HEADING_MISSING', undefined, { assetId: asset.assetId, heading }))
  sourceRefs.forEach((sourceRef) => invariant(content.includes(`[${sourceRef}]`), 'ASSET_CONTENT_SOURCE_MARKER_MISSING', undefined, { assetId: asset.assetId, sourceRef }))
  invariant(!INJECTION_PATTERN.test(content), 'ASSET_CONTENT_INSTRUCTION_INJECTION_PATTERN', undefined, { assetId: asset.assetId })
  return content
}

function validateSupersedes(assets) {
  const map = new Map(assets.map((asset) => [asset.assetId, asset]))
  for (const asset of assets) if (asset.supersedes !== null) invariant(map.has(asset.supersedes), 'ASSET_SUPERSEDES_TARGET_MISSING', undefined, { assetId: asset.assetId, supersedes: asset.supersedes })
  for (const asset of assets) {
    const seen = new Set()
    let cursor = asset
    while (cursor?.supersedes !== null) {
      invariant(!seen.has(cursor.assetId), 'ASSET_SUPERSEDES_CYCLE', undefined, { assetId: asset.assetId })
      seen.add(cursor.assetId)
      cursor = map.get(cursor.supersedes)
    }
  }
}

function validateDefaultCoverage(manifest) {
  for (const seatId of manifest.seatIds) {
    for (const phase of PHASES) {
      const seatPhaseAssets = manifest.assets.filter((asset) => asset.ownerSeatIds.includes(seatId) && asset.phaseAllowlist.includes(phase) && asset.status === 'active' && asset.productionEligible)
      if (seatPhaseAssets.length === 0) continue
      for (const kind of manifest.phasePolicies[phase].requiredKinds) {
        invariant(seatPhaseAssets.some((asset) => asset.kind === kind && asset.isDefaultForSeat), 'ASSET_DEFAULT_REQUIRED_KIND_MISSING', undefined, { seatId, phase, kind })
      }
    }
  }
}

async function loadCatalog({ assetRoot = DEFAULT_ASSET_ROOT, asOf, rejectStale = true } = {}) {
  const resolvedRoot = path.resolve(assetRoot)
  dateOnly(asOf, 'ASSET_VALIDATION_DATE_INVALID')
  await validateSchemas(resolvedRoot)
  const manifestPath = path.join(resolvedRoot, 'manifest.v1.json')
  const sourceLedgerPath = path.join(resolvedRoot, 'source-ledger.v1.json')
  await regularFile(manifestPath, 'ASSET_MANIFEST_FILE_INVALID')
  await regularFile(sourceLedgerPath, 'ASSET_SOURCE_LEDGER_FILE_INVALID')
  const manifest = await readJson(manifestPath, 'ASSET_MANIFEST_JSON_INVALID')
  const ledger = await readJson(sourceLedgerPath, 'ASSET_SOURCE_LEDGER_JSON_INVALID')

  assertExactKeys(manifest, MANIFEST_KEYS, 'ASSET_MANIFEST_FIELD_FORBIDDEN')
  requiredKeys(manifest, [...MANIFEST_KEYS], 'ASSET_MANIFEST_FIELD_REQUIRED')
  invariant(manifest.schema === CATALOG_SCHEMA, 'ASSET_MANIFEST_SCHEMA_INVALID')
  invariant(typeof manifest.catalogVersion === 'string' && VERSION_PATTERN.test(manifest.catalogVersion), 'ASSET_CATALOG_VERSION_INVALID')
  invariant(manifest.productVersion === '26.7.20', 'ASSET_PRODUCT_VERSION_INVALID')
  dateOnly(manifest.generatedAt, 'ASSET_GENERATED_DATE_INVALID')
  const seatIds = stringArray(manifest.seatIds, 'ASSET_SEAT_IDS_INVALID', { min: 1, max: 30, itemMax: 128, pattern: ID_PATTERN })
  await validateRoster(resolvedRoot, seatIds)
  invariant(isObject(manifest.phasePolicies), 'ASSET_PHASE_POLICIES_INVALID')
  invariant(sameStringSet(Object.keys(manifest.phasePolicies), [...PHASES]), 'ASSET_PHASE_POLICY_SET_INVALID')
  for (const phase of PHASES) validatePhasePolicy(phase, manifest.phasePolicies[phase])
  invariant(Array.isArray(manifest.assets) && manifest.assets.length > 0, 'ASSET_LIST_INVALID')
  nonEmptyText(manifest.evidenceBoundary, 'ASSET_EVIDENCE_BOUNDARY_INVALID', 200)

  assertExactKeys(ledger, SOURCE_LEDGER_KEYS, 'ASSET_SOURCE_LEDGER_FIELD_FORBIDDEN')
  requiredKeys(ledger, [...SOURCE_LEDGER_KEYS], 'ASSET_SOURCE_LEDGER_FIELD_REQUIRED')
  invariant(ledger.schema === SOURCE_LEDGER_SCHEMA, 'ASSET_SOURCE_LEDGER_SCHEMA_INVALID')
  invariant(ledger.catalogVersion === manifest.catalogVersion, 'ASSET_SOURCE_CATALOG_VERSION_MISMATCH')
  invariant(Array.isArray(ledger.sources) && ledger.sources.length > 0, 'ASSET_SOURCE_LIST_INVALID')
  ledger.sources.forEach(validateSource)
  const sourceIds = ledger.sources.map((source) => source.sourceId)
  invariant(new Set(sourceIds).size === sourceIds.length, 'ASSET_SOURCE_ID_DUPLICATE')
  const sourceMap = new Map(ledger.sources.map((source) => [source.sourceId, source]))
  nonEmptyText(ledger.evidenceBoundary, 'ASSET_SOURCE_EVIDENCE_BOUNDARY_INVALID', 200)

  const assetIds = manifest.assets.map((asset) => asset?.assetId)
  invariant(new Set(assetIds).size === assetIds.length, 'ASSET_ID_DUPLICATE')
  const contents = new Map()
  for (const asset of manifest.assets) contents.set(asset.assetId, await validateAsset(resolvedRoot, asset, manifest, sourceMap))
  await validateSceneIds(resolvedRoot, manifest.assets)
  validateSupersedes(manifest.assets)
  validateDefaultCoverage(manifest)

  const staleAssetIds = manifest.assets.filter((asset) => isStale(asset.freshness.reviewBy, asOf)).map((asset) => asset.assetId)
  const staleSourceIds = ledger.sources.filter((source) => isStale(source.reviewBy, asOf)).map((source) => source.sourceId)
  const notYetEffectiveSourceIds = ledger.sources.filter((source) => sourceEffectivity(source, asOf) === 'not_yet_effective').map((source) => source.sourceId)
  const expiredSourceIds = ledger.sources.filter((source) => sourceEffectivity(source, asOf) === 'expired').map((source) => source.sourceId)
  if (rejectStale) {
    invariant(staleAssetIds.length === 0, 'ASSET_CATALOG_CONTAINS_STALE_ASSET', undefined, { staleAssetIds, asOf })
    invariant(staleSourceIds.length === 0, 'ASSET_CATALOG_CONTAINS_STALE_SOURCE', undefined, { staleSourceIds, asOf })
    invariant(notYetEffectiveSourceIds.length === 0, 'ASSET_CATALOG_CONTAINS_NOT_YET_EFFECTIVE_SOURCE', undefined, { notYetEffectiveSourceIds, asOf })
    invariant(expiredSourceIds.length === 0, 'ASSET_CATALOG_CONTAINS_EXPIRED_SOURCE', undefined, { expiredSourceIds, asOf })
  }

  return { assetRoot: resolvedRoot, manifest, ledger, sourceMap, contents, staleAssetIds, staleSourceIds }
}

export async function validateCognitiveCatalog({ assetRoot = DEFAULT_ASSET_ROOT, asOf = new Date().toISOString().slice(0, 10), rejectStale = true } = {}) {
  const loaded = await loadCatalog({ assetRoot, asOf, rejectStale })
  const byKind = Object.fromEntries([...KINDS].map((kind) => [kind, loaded.manifest.assets.filter((asset) => asset.kind === kind).length]))
  return {
    schema: 'fbsir.cognitive-catalog-validation/v1',
    ok: true,
    catalogVersion: loaded.manifest.catalogVersion,
    productVersion: loaded.manifest.productVersion,
    seatCount: loaded.manifest.seatIds.length,
    assetCount: loaded.manifest.assets.length,
    sourceCount: loaded.ledger.sources.length,
    byKind,
    staleAssetIds: loaded.staleAssetIds,
    staleSourceIds: loaded.staleSourceIds,
    productionCaseCount: loaded.manifest.assets.filter((asset) => asset.kind === 'case' && asset.productionEligible && asset.status === 'active').length,
    evidenceBoundary: 'static_catalog_source_hash_freshness_and_roster_validation_only',
  }
}

function normalizeSelectionRequest(input) {
  assertExactKeys(input, SELECTION_KEYS, 'ASSET_SELECTION_FIELD_FORBIDDEN')
  requiredKeys(input, [...SELECTION_KEYS], 'ASSET_SELECTION_FIELD_REQUIRED')
  invariant(input.schema === SELECTION_REQUEST_SCHEMA, 'ASSET_SELECTION_SCHEMA_INVALID')
  safeId(input.agendaItemId, 'ASSET_SELECTION_AGENDA_ID_INVALID')
  safeId(input.seatId, 'ASSET_SELECTION_SEAT_ID_INVALID')
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'ASSET_SELECTION_REVISION_INVALID')
  invariant(PHASES.has(input.phase), 'ASSET_SELECTION_PHASE_INVALID')
  invariant(typeof input.decisionCardHash === 'string' && HEX_64.test(input.decisionCardHash), 'ASSET_SELECTION_DECISION_HASH_INVALID')
  const sceneIds = uniqueSorted(stringArray(input.sceneIds, 'ASSET_SELECTION_SCENE_IDS_INVALID', { min: 0, max: 10, itemMax: 64 }))
  const routingTerms = uniqueSorted(stringArray(input.routingTerms, 'ASSET_SELECTION_TERMS_INVALID', { min: 0, max: 20, itemMax: 80 }).map((term) => term.toLowerCase()))
  dateOnly(input.asOf, 'ASSET_SELECTION_AS_OF_INVALID')
  return { ...input, sceneIds, routingTerms }
}

function normalizeBundleRoutingInput(input) {
  assertExactKeys(input, ROUTING_INPUT_KEYS, 'ASSET_BUNDLE_ROUTING_INPUT_FIELD_FORBIDDEN')
  requiredKeys(input, [...ROUTING_INPUT_KEYS], 'ASSET_BUNDLE_ROUTING_INPUT_FIELD_REQUIRED')
  const normalized = {
    sceneIds: uniqueSorted(stringArray(input.sceneIds, 'ASSET_BUNDLE_ROUTING_SCENE_IDS_INVALID', { min: 0, max: 10, itemMax: 64 })),
    routingTerms: uniqueSorted(stringArray(input.routingTerms, 'ASSET_BUNDLE_ROUTING_TERMS_INVALID', { min: 0, max: 20, itemMax: 80 }).map((term) => term.toLowerCase())),
  }
  invariant(canonical(input) === canonical(normalized), 'ASSET_BUNDLE_ROUTING_INPUT_NOT_NORMALIZED')
  return normalized
}

function routingMatch(asset, request) {
  const normalizedScenes = new Set(request.sceneIds)
  const sceneMatches = asset.sceneIds.filter((sceneId) => sceneId === '*' || normalizedScenes.has(sceneId))
  const triggerMatches = asset.triggers.filter((trigger) => request.routingTerms.some((term) => term.includes(trigger.toLowerCase()) || trigger.toLowerCase().includes(term)))
  const exclusionMatches = asset.exclusions.filter((term) => request.routingTerms.some((value) => value.includes(term.toLowerCase()) || term.toLowerCase().includes(value)))
  if (exclusionMatches.length > 0) return null
  if (!asset.isDefaultForSeat && sceneMatches.length === 0 && triggerMatches.length === 0) return null
  const reasonCodes = []
  if (sceneMatches.length > 0) reasonCodes.push('scene_match')
  if (triggerMatches.length > 0) reasonCodes.push('trigger_match')
  if (asset.isDefaultForSeat) reasonCodes.push('seat_default')
  return { asset, score: asset.priority + (sceneMatches.length * 100) + (triggerMatches.length * 10) + (asset.isDefaultForSeat ? 1 : 0), reasonCodes }
}

function selectAssets(loaded, request) {
  const { manifest, sourceMap } = loaded
  invariant(manifest.seatIds.includes(request.seatId), 'ASSET_SELECTION_SEAT_UNAVAILABLE')
  for (const sceneId of request.sceneIds) {
    invariant(manifest.assets.some((asset) => asset.sceneIds.includes(sceneId)) || sceneId === '*', 'ASSET_SELECTION_SCENE_UNAVAILABLE', undefined, { sceneId })
  }
  const policy = manifest.phasePolicies[request.phase]
  const candidates = manifest.assets
    .filter((asset) => asset.status === 'active' && asset.productionEligible)
    .filter((asset) => asset.ownerSeatIds.includes(request.seatId))
    .filter((asset) => asset.phaseAllowlist.includes(request.phase) && policy.allowedKinds.includes(asset.kind))
    .filter((asset) => !isStale(asset.freshness.reviewBy, request.asOf))
    .filter((asset) => asset.sourceRefs.every((sourceRef) => isSourceAvailable(sourceMap.get(sourceRef), request.asOf)))
    .map((asset) => routingMatch(asset, request))
    .filter(Boolean)
    .sort((left, right) => right.score - left.score || left.asset.assetId.localeCompare(right.asset.assetId))

  const selected = []
  for (const requiredKind of policy.requiredKinds) {
    const match = candidates.find((candidate) => candidate.asset.kind === requiredKind && !selected.some((item) => item.asset.assetId === candidate.asset.assetId))
    invariant(match, 'ASSET_REQUIRED_KIND_UNAVAILABLE', undefined, { seatId: request.seatId, phase: request.phase, requiredKind })
    selected.push(match)
  }
  for (const candidate of candidates) {
    if (selected.length >= policy.maxItems) break
    if (!selected.some((item) => item.asset.assetId === candidate.asset.assetId)) selected.push(candidate)
  }
  selected.sort((left, right) => KIND_ORDER[left.asset.kind] - KIND_ORDER[right.asset.kind] || left.asset.assetId.localeCompare(right.asset.assetId))
  invariant(selected.length <= policy.maxItems, 'ASSET_SELECTION_ITEM_BUDGET_EXCEEDED')
  if (request.phase.startsWith('phase1_')) invariant(selected.every((entry) => entry.asset.kind === 'method' || entry.asset.kind === 'checklist'), 'ASSET_PHASE1_OUTCOME_CARD_SELECTED')
  return { policy, selected }
}

function materializeRoutingReasons(selection) {
  return selection.selected.map(({ asset, score, reasonCodes }) => ({
    assetId: asset.assetId,
    kind: asset.kind,
    score,
    reasonCodes: uniqueSorted(reasonCodes),
  }))
}

function materializeBundle(loaded, request, selection) {
  const selectedAssets = selection.selected.map(({ asset }) => ({
    assetId: asset.assetId,
    kind: asset.kind,
    version: asset.version,
    ownerSeatIds: [...asset.ownerSeatIds],
    sourceRefs: [...asset.sourceRefs],
    contentPath: asset.contentPath,
    contentSha256: asset.contentSha256,
    content: loaded.contents.get(asset.assetId),
  }))
  const count = selectedAssets.reduce((total, asset) => total + charCount(asset.content), 0)
  invariant(count <= selection.policy.maxChars, 'ASSET_SELECTION_CHAR_BUDGET_EXCEEDED', undefined, { actual: count, maximum: selection.policy.maxChars })
  const routingInput = { sceneIds: [...request.sceneIds], routingTerms: [...request.routingTerms] }
  const base = {
    schema: BUNDLE_SCHEMA,
    catalogVersion: loaded.manifest.catalogVersion,
    asOf: request.asOf,
    agendaItemId: request.agendaItemId,
    seatId: request.seatId,
    revision: request.revision,
    phase: request.phase,
    decisionCardHash: request.decisionCardHash,
    routingInput,
    routingInputHash: cognitiveSha256(routingInput),
    selectedAssets,
    routingReasons: materializeRoutingReasons(selection),
    charCount: count,
    evidenceBoundary: 'bundle_selected_materialized_and_hash_bound_not_cognitive_use_proof',
  }
  return { ...base, bundleDigest: cognitiveSha256(base) }
}

async function validateWorkspaceRoot(workspaceRoot) {
  const resolved = path.resolve(workspaceRoot)
  let info
  try { info = await lstat(resolved) }
  catch (error) { fail('ASSET_WORKSPACE_INVALID', 'Workspace root is unavailable', { cause: error.code }) }
  invariant(info.isDirectory() && !info.isSymbolicLink(), 'ASSET_WORKSPACE_INVALID')
  const markerPath = path.join(resolved, '.fbsir-board', 'workspace.json')
  ensureWithin(resolved, markerPath, 'ASSET_WORKSPACE_MARKER_PATH_INVALID')
  await rejectExistingSymlinkSegments(resolved, markerPath, 'ASSET_WORKSPACE_MARKER_SYMLINK_FORBIDDEN')
  await regularFile(markerPath, 'ASSET_WORKSPACE_MARKER_INVALID')
  const marker = await readJson(markerPath, 'ASSET_WORKSPACE_MARKER_INVALID')
  invariant(marker.schema === 'fbsir.board-workspace/v1' && marker.productVersion === '26.7.20', 'ASSET_WORKSPACE_MARKER_INVALID')
  return resolved
}

function bundleTarget(workspaceRoot, agendaItemId, seatId, revision) {
  const tasksRoot = path.join(workspaceRoot, 'tasks')
  const target = path.join(tasksRoot, agendaItemId, `${seatId}.assets.r${revision}.json`)
  ensureWithin(tasksRoot, target, 'ASSET_BUNDLE_TARGET_OUTSIDE_TASKS')
  return target
}

async function writeBundleAtomic(target, bundle) {
  await mkdir(path.dirname(target), { recursive: true })
  const lockPath = `${target}.lock`
  let lockHandle
  try { lockHandle = await open(lockPath, 'wx') }
  catch (error) { fail('ASSET_BUNDLE_LOCKED', 'Another writer holds the bundle lock', { target, cause: error.code }) }
  let tempPath = null
  try {
    try {
      const existing = await readJson(target, 'ASSET_BUNDLE_EXISTING_INVALID')
      invariant(existing.bundleDigest === bundle.bundleDigest && canonical(existing) === canonical(bundle), 'ASSET_BUNDLE_CONFLICT', 'A different bundle already exists at the deterministic target', { target })
      return true
    } catch (error) {
      if (error.code !== 'ASSET_BUNDLE_EXISTING_INVALID') throw error
      if (error.details?.cause !== 'ENOENT') throw error
    }
    tempPath = `${target}.${randomUUID()}.tmp`
    ensureWithin(path.dirname(target), tempPath, 'ASSET_BUNDLE_TEMP_PATH_INVALID')
    await writeFile(tempPath, `${JSON.stringify(bundle, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' })
    await rename(tempPath, target)
    tempPath = null
    return false
  } finally {
    if (tempPath) await unlink(tempPath).catch(() => {})
    await lockHandle.close().catch(() => {})
    await unlink(lockPath).catch(() => {})
  }
}

function validateBundleShape(bundle) {
  assertExactKeys(bundle, BUNDLE_KEYS, 'ASSET_BUNDLE_FIELD_FORBIDDEN')
  requiredKeys(bundle, [...BUNDLE_KEYS], 'ASSET_BUNDLE_FIELD_REQUIRED')
  invariant(bundle.schema === BUNDLE_SCHEMA, 'ASSET_BUNDLE_SCHEMA_INVALID')
  invariant(typeof bundle.catalogVersion === 'string' && VERSION_PATTERN.test(bundle.catalogVersion), 'ASSET_BUNDLE_CATALOG_VERSION_INVALID')
  dateOnly(bundle.asOf, 'ASSET_BUNDLE_AS_OF_INVALID')
  safeId(bundle.agendaItemId, 'ASSET_BUNDLE_AGENDA_ID_INVALID')
  safeId(bundle.seatId, 'ASSET_BUNDLE_SEAT_ID_INVALID')
  invariant(Number.isInteger(bundle.revision) && bundle.revision >= 1, 'ASSET_BUNDLE_REVISION_INVALID')
  invariant(PHASES.has(bundle.phase), 'ASSET_BUNDLE_PHASE_INVALID')
  invariant(typeof bundle.decisionCardHash === 'string' && HEX_64.test(bundle.decisionCardHash), 'ASSET_BUNDLE_DECISION_HASH_INVALID')
  normalizeBundleRoutingInput(bundle.routingInput)
  invariant(typeof bundle.routingInputHash === 'string' && HEX_64.test(bundle.routingInputHash), 'ASSET_BUNDLE_ROUTING_HASH_INVALID')
  invariant(Array.isArray(bundle.selectedAssets) && bundle.selectedAssets.length <= 4, 'ASSET_BUNDLE_ASSETS_INVALID')
  for (const asset of bundle.selectedAssets) {
    assertExactKeys(asset, BUNDLE_ASSET_KEYS, 'ASSET_BUNDLE_ASSET_FIELD_FORBIDDEN')
    requiredKeys(asset, [...BUNDLE_ASSET_KEYS], 'ASSET_BUNDLE_ASSET_FIELD_REQUIRED')
    safeId(asset.assetId, 'ASSET_BUNDLE_ASSET_ID_INVALID')
    invariant(KINDS.has(asset.kind), 'ASSET_BUNDLE_ASSET_KIND_INVALID')
    invariant(typeof asset.version === 'string' && VERSION_PATTERN.test(asset.version), 'ASSET_BUNDLE_ASSET_VERSION_INVALID')
    stringArray(asset.ownerSeatIds, 'ASSET_BUNDLE_OWNER_SEATS_INVALID', { min: 1, max: 9, itemMax: 128, pattern: ID_PATTERN })
    stringArray(asset.sourceRefs, 'ASSET_BUNDLE_SOURCE_REFS_INVALID', { min: 1, max: 20, itemMax: 124, pattern: SOURCE_ID_PATTERN })
    nonEmptyText(asset.contentPath, 'ASSET_BUNDLE_CONTENT_PATH_INVALID', 300)
    invariant(typeof asset.contentSha256 === 'string' && HEX_64.test(asset.contentSha256), 'ASSET_BUNDLE_CONTENT_HASH_INVALID')
    nonEmptyText(asset.content, 'ASSET_BUNDLE_CONTENT_INVALID', 12000)
  }
  invariant(Array.isArray(bundle.routingReasons) && bundle.routingReasons.length === bundle.selectedAssets.length, 'ASSET_BUNDLE_ROUTING_REASONS_INVALID')
  for (const reason of bundle.routingReasons) {
    assertExactKeys(reason, ROUTING_REASON_KEYS, 'ASSET_BUNDLE_ROUTING_FIELD_FORBIDDEN')
    requiredKeys(reason, [...ROUTING_REASON_KEYS], 'ASSET_BUNDLE_ROUTING_FIELD_REQUIRED')
    safeId(reason.assetId, 'ASSET_BUNDLE_ROUTING_ASSET_ID_INVALID')
    invariant(KINDS.has(reason.kind), 'ASSET_BUNDLE_ROUTING_KIND_INVALID')
    invariant(Number.isInteger(reason.score), 'ASSET_BUNDLE_ROUTING_SCORE_INVALID')
    stringArray(reason.reasonCodes, 'ASSET_BUNDLE_REASON_CODES_INVALID', { min: 1, max: 5, itemMax: 64, pattern: /^[a-z][a-z0-9_]{0,63}$/ })
  }
  invariant(Number.isInteger(bundle.charCount) && bundle.charCount >= 0 && bundle.charCount <= 12000, 'ASSET_BUNDLE_CHAR_COUNT_INVALID')
  invariant(bundle.evidenceBoundary === 'bundle_selected_materialized_and_hash_bound_not_cognitive_use_proof', 'ASSET_BUNDLE_EVIDENCE_BOUNDARY_INVALID')
  invariant(typeof bundle.bundleDigest === 'string' && HEX_64.test(bundle.bundleDigest), 'ASSET_BUNDLE_DIGEST_INVALID')
}

export async function buildCognitiveAssetBundle({ assetRoot = DEFAULT_ASSET_ROOT, workspaceRoot, input }) {
  const request = normalizeSelectionRequest(input)
  const loaded = await loadCatalog({ assetRoot, asOf: request.asOf, rejectStale: false })
  const selection = selectAssets(loaded, request)
  const bundle = materializeBundle(loaded, request, selection)
  const resolvedWorkspace = await validateWorkspaceRoot(workspaceRoot)
  const target = bundleTarget(resolvedWorkspace, request.agendaItemId, request.seatId, request.revision)
  await rejectExistingSymlinkSegments(resolvedWorkspace, target, 'ASSET_BUNDLE_SYMLINK_FORBIDDEN')
  const idempotent = await writeBundleAtomic(target, bundle)
  return {
    schema: 'fbsir.asset-bundle-build-result/v1',
    ok: true,
    target,
    bundleRef: `assetbundle:${bundle.bundleDigest}`,
    bundleDigest: bundle.bundleDigest,
    selectedAssetIds: bundle.selectedAssets.map((asset) => asset.assetId),
    charCount: bundle.charCount,
    idempotent,
    evidenceBoundary: 'bundle_selected_materialized_and_hash_bound_not_cognitive_use_proof',
  }
}

function normalizeVerifyRequest(input) {
  assertExactKeys(input, VERIFY_KEYS, 'ASSET_BUNDLE_VERIFY_FIELD_FORBIDDEN')
  requiredKeys(input, [...VERIFY_KEYS], 'ASSET_BUNDLE_VERIFY_FIELD_REQUIRED')
  invariant(input.schema === BUNDLE_VERIFY_REQUEST_SCHEMA, 'ASSET_BUNDLE_VERIFY_SCHEMA_INVALID')
  safeId(input.agendaItemId, 'ASSET_BUNDLE_VERIFY_AGENDA_ID_INVALID')
  safeId(input.seatId, 'ASSET_BUNDLE_VERIFY_SEAT_ID_INVALID')
  invariant(Number.isInteger(input.revision) && input.revision >= 1, 'ASSET_BUNDLE_VERIFY_REVISION_INVALID')
  invariant(PHASES.has(input.phase), 'ASSET_BUNDLE_VERIFY_PHASE_INVALID')
  invariant(typeof input.decisionCardHash === 'string' && HEX_64.test(input.decisionCardHash), 'ASSET_BUNDLE_VERIFY_DECISION_HASH_INVALID')
  invariant(typeof input.bundleRef === 'string' && ASSET_BUNDLE_REF_PATTERN.test(input.bundleRef), 'ASSET_BUNDLE_VERIFY_REF_INVALID')
  dateOnly(input.asOf, 'ASSET_BUNDLE_VERIFY_AS_OF_INVALID')
  return { ...input }
}

export async function verifyCognitiveAssetBundle({ assetRoot = DEFAULT_ASSET_ROOT, workspaceRoot, input }) {
  const request = normalizeVerifyRequest(input)
  const resolvedWorkspace = await validateWorkspaceRoot(workspaceRoot)
  const target = bundleTarget(resolvedWorkspace, request.agendaItemId, request.seatId, request.revision)
  await rejectExistingSymlinkSegments(resolvedWorkspace, target, 'ASSET_BUNDLE_SYMLINK_FORBIDDEN')
  await regularFile(target, 'ASSET_BUNDLE_FILE_INVALID')
  const bundle = await readJson(target, 'ASSET_BUNDLE_FILE_INVALID')
  validateBundleShape(bundle)
  const loaded = await loadCatalog({ assetRoot, asOf: request.asOf, rejectStale: false })
  invariant(bundle.catalogVersion === loaded.manifest.catalogVersion, 'ASSET_BUNDLE_CATALOG_MISMATCH')
  invariant(bundle.agendaItemId === request.agendaItemId && bundle.seatId === request.seatId && bundle.revision === request.revision, 'ASSET_BUNDLE_IDENTITY_MISMATCH')
  invariant(bundle.phase === request.phase, 'ASSET_BUNDLE_PHASE_OR_DATE_MISMATCH')
  invariant(bundle.asOf <= request.asOf, 'ASSET_BUNDLE_AS_OF_AFTER_VERIFY_DATE', undefined, { bundleAsOf: bundle.asOf, verificationAsOf: request.asOf })
  invariant(bundle.decisionCardHash === request.decisionCardHash, 'ASSET_BUNDLE_DECISION_HASH_MISMATCH')
  const digestBase = { ...bundle }
  delete digestBase.bundleDigest
  const digest = cognitiveSha256(digestBase)
  invariant(digest === bundle.bundleDigest, 'ASSET_BUNDLE_DIGEST_MISMATCH')
  invariant(request.bundleRef === `assetbundle:${digest}`, 'ASSET_BUNDLE_REF_MISMATCH')
  const routingInput = normalizeBundleRoutingInput(bundle.routingInput)
  invariant(bundle.routingInputHash === cognitiveSha256(routingInput), 'ASSET_BUNDLE_ROUTING_INPUT_HASH_MISMATCH')
  const policy = loaded.manifest.phasePolicies[bundle.phase]
  invariant(bundle.selectedAssets.length <= policy.maxItems, 'ASSET_BUNDLE_ITEM_BUDGET_EXCEEDED')
  invariant(bundle.charCount === bundle.selectedAssets.reduce((total, asset) => total + charCount(asset.content), 0), 'ASSET_BUNDLE_CHAR_COUNT_MISMATCH')
  invariant(bundle.charCount <= policy.maxChars, 'ASSET_BUNDLE_CHAR_BUDGET_EXCEEDED')
  if (bundle.phase.startsWith('phase1_')) invariant(bundle.selectedAssets.every((asset) => asset.kind === 'method' || asset.kind === 'checklist'), 'ASSET_BUNDLE_PHASE1_OUTCOME_CARD_FORBIDDEN')
  for (const selected of bundle.selectedAssets) {
    invariant(selected.ownerSeatIds.includes(bundle.seatId), 'ASSET_BUNDLE_CROSS_SEAT_ASSET')
    invariant(cognitiveSha256(normalizeContent(selected.content)) === selected.contentSha256, 'ASSET_BUNDLE_EMBEDDED_CONTENT_HASH_MISMATCH', undefined, { assetId: selected.assetId })
    const current = loaded.manifest.assets.find((asset) => asset.assetId === selected.assetId)
    invariant(current && current.status === 'active' && current.productionEligible, 'ASSET_BUNDLE_ASSET_NO_LONGER_ACTIVE', undefined, { assetId: selected.assetId })
    invariant(current.ownerSeatIds.includes(bundle.seatId) && current.phaseAllowlist.includes(bundle.phase), 'ASSET_BUNDLE_ASSET_SCOPE_MISMATCH', undefined, { assetId: selected.assetId })
    invariant(current.kind === selected.kind, 'ASSET_BUNDLE_ASSET_KIND_MISMATCH', undefined, { assetId: selected.assetId })
    invariant(canonical(current.ownerSeatIds) === canonical(selected.ownerSeatIds), 'ASSET_BUNDLE_ASSET_OWNER_SEATS_MISMATCH', undefined, { assetId: selected.assetId })
    invariant(canonical(current.sourceRefs) === canonical(selected.sourceRefs), 'ASSET_BUNDLE_ASSET_SOURCE_REFS_MISMATCH', undefined, { assetId: selected.assetId })
    invariant(current.contentPath === selected.contentPath, 'ASSET_BUNDLE_ASSET_CONTENT_PATH_MISMATCH', undefined, { assetId: selected.assetId })
    invariant(current.version === selected.version && current.contentSha256 === selected.contentSha256, 'ASSET_BUNDLE_ASSET_VERSION_MISMATCH', undefined, { assetId: selected.assetId })
    invariant(!isStale(current.freshness.reviewBy, request.asOf), 'ASSET_BUNDLE_ASSET_STALE', undefined, { assetId: selected.assetId })
    for (const sourceRef of selected.sourceRefs) {
      const source = loaded.sourceMap.get(sourceRef)
      invariant(source, 'ASSET_BUNDLE_SOURCE_REF_UNRESOLVED', undefined, { assetId: selected.assetId, sourceRef })
      invariant(!isStale(source.reviewBy, request.asOf), 'ASSET_BUNDLE_SOURCE_STALE', undefined, { assetId: selected.assetId, sourceRef, reviewBy: source.reviewBy, asOf: request.asOf })
      const effectivity = sourceEffectivity(source, request.asOf)
      invariant(effectivity !== 'not_yet_effective', 'ASSET_BUNDLE_SOURCE_NOT_YET_EFFECTIVE', undefined, { assetId: selected.assetId, sourceRef, effectiveFrom: source.effectiveFrom, asOf: request.asOf })
      invariant(effectivity !== 'expired', 'ASSET_BUNDLE_SOURCE_EXPIRED', undefined, { assetId: selected.assetId, sourceRef, effectiveTo: source.effectiveTo, asOf: request.asOf })
    }
  }
  for (const kind of policy.requiredKinds) invariant(bundle.selectedAssets.some((asset) => asset.kind === kind), 'ASSET_BUNDLE_REQUIRED_KIND_MISSING', undefined, { kind })
  const replayRequest = normalizeSelectionRequest({
    schema: SELECTION_REQUEST_SCHEMA,
    agendaItemId: bundle.agendaItemId,
    seatId: bundle.seatId,
    revision: bundle.revision,
    phase: bundle.phase,
    decisionCardHash: bundle.decisionCardHash,
    sceneIds: routingInput.sceneIds,
    routingTerms: routingInput.routingTerms,
    asOf: bundle.asOf,
  })
  const replaySelection = selectAssets(loaded, replayRequest)
  const expectedAssetIds = replaySelection.selected.map(({ asset }) => asset.assetId)
  const selectedAssetIds = bundle.selectedAssets.map((asset) => asset.assetId)
  invariant(canonical(selectedAssetIds) === canonical(expectedAssetIds), 'ASSET_BUNDLE_ROUTED_ASSET_SET_MISMATCH', undefined, { expectedAssetIds, selectedAssetIds })
  const expectedRoutingReasons = materializeRoutingReasons(replaySelection)
  invariant(canonical(bundle.routingReasons) === canonical(expectedRoutingReasons), 'ASSET_BUNDLE_ROUTING_REASONS_MISMATCH')
  return {
    schema: 'fbsir.asset-bundle-verification-result/v1',
    ok: true,
    target,
    bundleRef: request.bundleRef,
    bundleDigest: digest,
    selectedAssetIds: bundle.selectedAssets.map((asset) => asset.assetId),
    charCount: bundle.charCount,
    evidenceBoundary: 'bundle_file_identity_hash_scope_and_budget_verified_not_cognitive_use_proof',
  }
}

export function isCognitiveAssetBundleRef(value) {
  return typeof value === 'string' && ASSET_BUNDLE_REF_PATTERN.test(value)
}

export function validateCognitiveAssetEvidenceRefs(evidenceRefs, expectedBundleRef) {
  invariant(Array.isArray(evidenceRefs), 'ASSET_EVIDENCE_REFS_INVALID')
  invariant(typeof expectedBundleRef === 'string' && ASSET_BUNDLE_REF_PATTERN.test(expectedBundleRef), 'ASSET_EVIDENCE_EXPECTED_REF_INVALID')
  const bundleRefs = evidenceRefs.filter((value) => isCognitiveAssetBundleRef(value))
  invariant(bundleRefs.length === 1, 'ASSET_EVIDENCE_REF_COUNT_INVALID', 'Task or result evidenceRefs must contain exactly one cognitive asset bundle reference', { count: bundleRefs.length })
  invariant(bundleRefs[0] === expectedBundleRef, 'ASSET_EVIDENCE_REF_MISMATCH')
  return { ok: true, bundleRef: bundleRefs[0], evidenceBoundary: 'evidence_ref_bound_to_verified_bundle_not_cognitive_use_proof' }
}
