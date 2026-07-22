import { readJsonFile, readJsonStdin, failureReceipt, parseArgs, printJson } from './lib/cli.mjs'
import { recordDeliveryObservation, recordFailureEnvelope, recordResultEnvelope, recordReviewPlan, recordTaskEnvelope } from './lib/core.mjs'

const args = parseArgs(process.argv.slice(2))
const kind = args._[0]

try {
  if (!args.workspace || !['plan', 'task', 'result', 'delivery', 'failure'].includes(kind)) {
    throw new Error('USAGE: board-record.mjs <plan|task|result|delivery|failure> --workspace PATH [--input FILE] [--actor board-convener]')
  }
  const input = args.input ? await readJsonFile(args.input) : await readJsonStdin()
  const result = kind === 'plan'
    ? await recordReviewPlan({ workspaceRoot: args.workspace, actorId: args.actor, envelope: input })
    : kind === 'task'
      ? await recordTaskEnvelope({ workspaceRoot: args.workspace, actorId: args.actor, envelope: input })
      : kind === 'result'
        ? await recordResultEnvelope({ workspaceRoot: args.workspace, envelope: input })
    : kind === 'delivery'
      ? await recordDeliveryObservation({ workspaceRoot: args.workspace, observation: input })
      : await recordFailureEnvelope({ workspaceRoot: args.workspace, actorId: args.actor, envelope: input })
  printJson({
    schema: 'fbsir.board-script-receipt/v1',
    ok: true,
    action: `record.${kind}`,
    result,
    evidenceBoundary: kind === 'delivery'
      ? 'member_observed_sendmessage_tool_success_only_not_host_signed_receipt_or_lead_consumption_proof'
      : 'durable_workspace_artifact_only_not_host_dispatch_or_completion_proof',
  })
} catch (error) {
  printJson(failureReceipt(`record.${kind || 'unknown'}`, error))
  process.exitCode = 1
}
