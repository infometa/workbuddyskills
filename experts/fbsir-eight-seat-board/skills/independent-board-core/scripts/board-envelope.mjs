import { BoardContractError, DECISION_RECORD_EVIDENCE_BOUNDARY, MATERIAL_CARD_BUILD_EVIDENCE_BOUNDARY, MATERIAL_SUFFICIENCY_EVIDENCE_BOUNDARY, PROCESS_SUPPORT_HANDOFF_EVIDENCE_BOUNDARY, buildMaterialSufficiency, sha256, validateDecisionRecord, validateDeliveryObservation, validateEntryIntent, validateFailureEnvelope, validateHostActionEnvelope, validateMaterialSufficiency, validateProcessSupportHandoff, validateReviewPlan, validateSeatProposal, validateTaskEnvelope, validateWritableResultEnvelope } from './lib/core.mjs'
import { failureReceipt, parseArgs, printJson, readJsonStdinNoDuplicateKeys } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))
const kind = args._[0]
const validators = Object.freeze({
  entry: validateEntryIntent,
  'material-inspect': validateMaterialSufficiency,
  action: validateHostActionEnvelope,
  decision: validateDecisionRecord,
  proposal: validateSeatProposal,
  plan: validateReviewPlan,
  task: validateTaskEnvelope,
  result: validateWritableResultEnvelope,
  'support-handoff': validateProcessSupportHandoff,
  delivery: validateDeliveryObservation,
  failure: validateFailureEnvelope,
})
function receiptAction(targetKind) {
  if (targetKind === 'material-card') return 'envelope.material-card.build'
  if (targetKind === 'material-inspect') return 'envelope.material.inspect'
  if (targetKind === 'material') return 'envelope.material.disabled'
  return `envelope.${targetKind || 'unknown'}.validate`
}
try {
  if (kind === 'material') throw new BoardContractError('MATERIAL_DIRECT_CLI_DISABLED', 'Use material-card to build first-value references or material-inspect for digest-only read-only inspection')
  if (kind !== 'material-card' && !Object.hasOwn(validators, kind)) throw new Error('USAGE: board-envelope.mjs <entry|material-card|material-inspect|action|decision|proposal|plan|task|result|support-handoff|delivery|failure> < envelope.json')
  let input
  try { input = await readJsonStdinNoDuplicateKeys() }
  catch (error) {
    if (error instanceof SyntaxError) throw new BoardContractError('JSON_INPUT_INVALID', 'Input must be valid JSON')
    throw error
  }
  if (kind === 'material-card') {
    const built = buildMaterialSufficiency(input)
    printJson({
      schema: 'fbsir.board-script-receipt/v1',
      ok: true,
      action: 'envelope.material-card.build',
      payloadHash: sha256(built.normalized),
      normalized: built.normalized,
      slotBindings: built.slotBindings,
      evidenceBoundary: MATERIAL_CARD_BUILD_EVIDENCE_BOUNDARY,
    })
  } else {
    const normalized = validators[kind](input)
    const evidenceBoundary = kind === 'material-inspect'
      ? MATERIAL_SUFFICIENCY_EVIDENCE_BOUNDARY
      : kind === 'support-handoff'
        ? PROCESS_SUPPORT_HANDOFF_EVIDENCE_BOUNDARY
        : kind === 'decision'
          ? DECISION_RECORD_EVIDENCE_BOUNDARY
          : 'envelope_shape_only_not_dispatch_or_completion_proof'
    if (kind === 'material-inspect') {
      printJson({
        schema: 'fbsir.board-script-receipt/v1',
        ok: true,
        action: receiptAction(kind),
        payloadHash: sha256(normalized),
        readOnly: true,
        notForDecisionStart: true,
        normalizedOmitted: true,
        evidenceBoundary,
      })
    } else if (kind === 'decision') {
      printJson({
        schema: 'fbsir.board-script-receipt/v1',
        ok: true,
        action: receiptAction(kind),
        payloadHash: sha256(normalized),
        normalizedOmitted: true,
        evidenceBoundary,
      })
    } else {
      printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: receiptAction(kind), payloadHash: sha256(normalized), normalized, evidenceBoundary })
    }
  }
} catch (error) {
  printJson(failureReceipt(receiptAction(kind), error))
  process.exitCode = 1
}
