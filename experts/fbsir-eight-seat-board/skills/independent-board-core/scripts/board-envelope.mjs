import { sha256, validateDeliveryObservation, validateFailureEnvelope, validateResultEnvelope, validateReviewPlan, validateSeatProposal, validateTaskEnvelope } from './lib/core.mjs'
import { failureReceipt, parseArgs, printJson, readJsonStdin } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))
const kind = args._[0]
try {
  if (!['proposal', 'plan', 'task', 'result', 'delivery', 'failure'].includes(kind)) throw new Error('USAGE: board-envelope.mjs <proposal|plan|task|result|delivery|failure> < envelope.json')
  const input = await readJsonStdin()
  const normalized = kind === 'proposal'
    ? validateSeatProposal(input)
    : kind === 'plan'
      ? validateReviewPlan(input)
      : kind === 'task'
        ? validateTaskEnvelope(input)
        : kind === 'result'
          ? validateResultEnvelope(input)
          : kind === 'delivery'
            ? validateDeliveryObservation(input)
            : validateFailureEnvelope(input)
  printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: `envelope.${kind}.validate`, payloadHash: sha256(normalized), normalized, evidenceBoundary: 'envelope_shape_only_not_dispatch_or_completion_proof' })
} catch (error) {
  printJson(failureReceipt(`envelope.${kind || 'unknown'}.validate`, error))
  process.exitCode = 1
}
