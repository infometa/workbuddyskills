import { readJsonFile, readJsonStdin, failureReceipt, parseArgs, printJson } from './lib/cli.mjs'
import {
  BoardContractError, recordClaimEvidenceIndex, recordDeliveryObservation, recordFailureEnvelope, recordResultEnvelope,
  recordPublicSourceObservation, recordReviewPlan, recordTaskEnvelope, recordWorkspaceMaterialCard,
} from './lib/core.mjs'

const args = parseArgs(process.argv.slice(2))
const kind = args._[0]

try {
  if (!args.workspace || !['plan', 'task', 'result', 'delivery', 'failure', 'material-card', 'public-source', 'claim-index'].includes(kind)) {
    throw new Error('USAGE: board-record.mjs <plan|task|result|delivery|failure|material-card|public-source|claim-index> --workspace PATH [--run ID] [--artifact PATH] [--input FILE] [--actor board-convener]')
  }
  if (['material-card', 'public-source', 'claim-index'].includes(kind) && !args.run) throw new Error('USAGE: material-card, public-source and claim-index require --run ID')
  if (kind === 'claim-index' && !args.artifact) throw new Error('USAGE: claim-index requires --artifact PATH')
  const input = args.input ? await readJsonFile(args.input) : await readJsonStdin()
  if (kind === 'public-source' && (Object.keys(input).length !== 1 || !Object.hasOwn(input, 'sourceDigest'))) {
    throw new BoardContractError('PUBLIC_SOURCE_CLI_FIELD_FORBIDDEN', 'Public source input accepts only sourceDigest')
  }
  const result = kind === 'plan'
    ? await recordReviewPlan({ workspaceRoot: args.workspace, actorId: args.actor, envelope: input })
    : kind === 'task'
      ? await recordTaskEnvelope({ workspaceRoot: args.workspace, actorId: args.actor, envelope: input })
      : kind === 'result'
        ? await recordResultEnvelope({ workspaceRoot: args.workspace, envelope: input })
    : kind === 'delivery'
      ? await recordDeliveryObservation({ workspaceRoot: args.workspace, observation: input })
      : kind === 'failure'
        ? await recordFailureEnvelope({ workspaceRoot: args.workspace, actorId: args.actor, envelope: input })
        : kind === 'material-card'
          ? await recordWorkspaceMaterialCard({ workspaceRoot: args.workspace, runId: args.run, actorId: args.actor, draft: input })
          : kind === 'public-source'
            ? await recordPublicSourceObservation({ workspaceRoot: args.workspace, runId: args.run, actorId: args.actor, sourceDigest: input.sourceDigest })
            : await recordClaimEvidenceIndex({ workspaceRoot: args.workspace, runId: args.run, actorId: args.actor, artifactPath: args.artifact, draft: input })
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
