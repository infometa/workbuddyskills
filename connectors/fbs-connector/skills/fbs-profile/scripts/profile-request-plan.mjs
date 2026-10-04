const IDENTITY_FIELDS = Object.freeze(['productId', 'packageName', 'expertEntryId', 'packageVersion'])
const UUID = /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i
const OPERATION_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$/
const MAX_STATUS_AGE_MS = 300000
const PERSONAL_FIELDS = new Set([
  'work_role', 'industry', 'experience', 'goals', 'constraints', 'decision_style',
  'preferred_language', 'output_preference', 'delivery_preference', 'collaboration_preference'
])
const CASE_FIELDS = new Set(['objective', 'constraint', 'decision', 'success_criteria', 'deadline'])
const blocked = status => Object.freeze({ status, allowedToAttempt: false, networkCalled: false })
const plainObject = value => value !== null && typeof value === 'object' && !Array.isArray(value) &&
  (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null)
const canonical = value => {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value)
  if (typeof value === 'number' && Number.isFinite(value)) return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`
  if (plainObject(value)) return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`
  throw new TypeError('Payload must contain only JSON values')
}

/** A local idempotency helper; it never authorizes or submits a write. */
export function allocateProfileOperationId({ explicitUserIntent, action, operationId, originalPayload, retryPayload }, randomUUID = () => globalThis.crypto?.randomUUID?.()) {
  if (explicitUserIntent !== true || !['profile_manage_entry', 'profile_propose'].includes(action))
    return blocked('explicit_write_intent_required')
  if (operationId !== undefined) {
    if (typeof operationId !== 'string' || !UUID.test(operationId)) return blocked('original_operation_id_invalid')
    if (!plainObject(originalPayload) || !plainObject(retryPayload)) return blocked('retry_payload_unverified')
    let samePayload = false
    try { samePayload = canonical(originalPayload) === canonical(retryPayload) } catch { /* Fail closed. */ }
    if (!samePayload) return blocked('retry_payload_mismatch')
    return Object.freeze({ status: 'original_operation_id_reused', operationId, samePayload: true,
      containsPersonalInformation: false, networkCalled: false, authorized: false })
  }
  let value
  try { value = randomUUID() } catch { /* Fail closed. */ }
  if (typeof value !== 'string' || !UUID.test(value)) return blocked('secure_id_generation_unavailable')
  return Object.freeze({ status: 'client_operation_id_ready', operationId: value,
    containsPersonalInformation: false, networkCalled: false, authorized: false })
}

/** Episode groups one local task; operation id survives write retries; attempt id changes per call. */
export function prepareProfileCallTrace({ episodeId, operationId }, randomUUID = () => globalThis.crypto?.randomUUID?.()) {
  if (episodeId !== undefined && (typeof episodeId !== 'string' || !UUID.test(episodeId))) return blocked('episode_id_invalid')
  if (operationId !== undefined && (typeof operationId !== 'string' || !OPERATION_ID.test(operationId)))
    return blocked('operation_id_invalid')
  let nextEpisodeId = episodeId
  let attemptId
  try { nextEpisodeId ??= randomUUID(); attemptId = randomUUID() } catch { /* Fail closed. */ }
  if (typeof nextEpisodeId !== 'string' || !UUID.test(nextEpisodeId) || typeof attemptId !== 'string' || !UUID.test(attemptId))
    return blocked('secure_id_generation_unavailable')
  if (nextEpisodeId === attemptId || operationId === nextEpisodeId || operationId === attemptId)
    return blocked('trace_identifier_collision')
  return Object.freeze({ status:'local_call_trace_ready', episodeId:nextEpisodeId, operationId:operationId ?? null,
    attemptId, requestRef:null, requestRefStatus:'not_observed', episodeIdSentToService:false,
    attemptIdSentToService:false, requestRefGeneratedByClient:false, networkCalled:false })
}

/** Use local purpose status for routing, then construct only schema-approved profile_read wire keys. */
export function buildProfileReadWireArgs({ identity, contextRef, purposeCode, purposeStatus, purposeStatusObservedAtMs, fieldKeys, afterFactId }, nowMs = Date.now()) {
  if (!plainObject(identity) || !IDENTITY_FIELDS.every(key => typeof identity[key] === 'string' && identity[key].trim()))
    return blocked('current_expert_identity_missing')
  if (typeof contextRef !== 'string' || !/^pcx-[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i.test(contextRef) ||
      !Number.isFinite(nowMs) || !Number.isFinite(purposeStatusObservedAtMs) || purposeStatusObservedAtMs > nowMs ||
      nowMs - purposeStatusObservedAtMs > MAX_STATUS_AGE_MS || !plainObject(purposeStatus) ||
      purposeStatus.success !== true || !Array.isArray(purposeStatus.contexts)) return blocked('current_purpose_status_missing')
  const context = purposeStatus.contexts.find(item => item?.contextRef === contextRef && item?.purposeCode === purposeCode)
  if (!context || context.status !== 'ACTIVE' || context.authorizationCurrent !== true ||
      !Number.isSafeInteger(context.expiresAt) || context.expiresAt * 1000 <= nowMs)
    return blocked('purpose_context_not_current')
  const allowed = context.contextType === 'PERSONAL' && context.contextId === 'personal' && purposeCode === 'expert-personalization'
    ? PERSONAL_FIELDS : context.contextType === 'CASE' && typeof context.contextId === 'string' &&
      context.contextId.startsWith('case-') && purposeCode === 'decision-support' ? CASE_FIELDS : null
  if (!allowed) return blocked('purpose_context_contract_mismatch')
  if (fieldKeys !== undefined && (!Array.isArray(fieldKeys) || fieldKeys.length < 1 || fieldKeys.length > 5 ||
      new Set(fieldKeys).size !== fieldKeys.length || fieldKeys.some(key => typeof key !== 'string' || !allowed.has(key))))
    return blocked('profile_field_keys_invalid')
  if (afterFactId !== undefined && (typeof afterFactId !== 'string' || !afterFactId.trim()))
    return blocked('after_fact_id_invalid')
  const wireArgs = Object.fromEntries(IDENTITY_FIELDS.map(key => [key, identity[key]]))
  wireArgs.contextRef = contextRef
  if (fieldKeys !== undefined) wireArgs.fieldKeys = Object.freeze([...fieldKeys])
  if (afterFactId !== undefined) wireArgs.afterFactId = afterFactId
  return Object.freeze({ status: 'wire_request_prepared', wireArgs: Object.freeze(wireArgs), localPurposeCode: purposeCode,
    purposeCodeExcludedFromWire: !Object.hasOwn(wireArgs, 'purposeCode'), networkCalled: false,
    serviceAuthorizationProven: false })
}

/** Compose the existing purpose gate with this call's actual observed schema. */
export function planProfileReadRequest(input = {}, nowMs = Date.now()) {
  const local = buildProfileReadWireArgs(input, nowMs)
  if (local.status !== 'wire_request_prepared') return local
  const tool = input.tool, schema = tool?.inputSchema
  if (tool?.name !== 'profile_read' || !plainObject(schema) || schema.type !== 'object' ||
      !plainObject(schema.properties) || !Array.isArray(schema.required))
    return blocked('current_profile_read_schema_required')
  const args = local.wireArgs
  if (!Array.isArray(args.fieldKeys) || !args.fieldKeys.length || schema.required.some(key => !Object.hasOwn(args,key)))
    return blocked('profile_read_required_fields_unhandled')
  for (const [key,value] of Object.entries(args)) {
    const rule = schema.properties[key]
    if (!plainObject(rule)) return blocked('profile_read_wire_schema_mismatch')
    if (Array.isArray(value)) {
      if (key !== 'fieldKeys' || rule.type !== 'array' || !plainObject(rule.items) || !Array.isArray(rule.items.enum) ||
          !Number.isSafeInteger(rule.maxItems) || value.length > rule.maxItems ||
          value.length < (rule.minItems ?? 1) || value.some(x => !rule.items.enum.includes(x)))
        return blocked('profile_read_wire_schema_mismatch')
    } else {
      if (rule.type !== 'string' || typeof value !== 'string' ||
          (Number.isInteger(rule.maxLength) && Array.from(value).length > rule.maxLength) ||
          (Number.isInteger(rule.minLength) && Array.from(value).length < rule.minLength) ||
          (Array.isArray(rule.enum) && !rule.enum.includes(value)) ||
          (Object.hasOwn(rule,'const') && rule.const !== value)) return blocked('profile_read_wire_schema_mismatch')
      if (typeof rule.pattern === 'string') {
        try { if (!new RegExp(rule.pattern).test(value)) return blocked('profile_read_wire_schema_mismatch') }
        catch { return blocked('profile_read_wire_schema_mismatch') }
      }
    }
  }
  return Object.freeze({ ...local, status: 'current_profile_read_request_prepared', schemaObserved: true })
}
