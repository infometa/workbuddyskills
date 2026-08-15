import { failureReceipt, parseArgs, printJson } from './lib/cli.mjs'
import { inspectPredecessorResume } from './lib/legacy-resume.mjs'
import { BoardContractError, buildCaseResumeCard, recordPredecessorResumeDigest, suppressCaseResumeActionPresentation } from './lib/core.mjs'

const args = parseArgs(process.argv.slice(2))
const action = args._[0]

try {
  if (!['inspect', 'record', 'card'].includes(action)) {
    throw new BoardContractError('RESUME_USAGE_INVALID')
  }
  if (action !== 'card' && (!args['source-workspace'] || !args['source-run'])) {
    throw new BoardContractError('RESUME_USAGE_INVALID')
  }
  if (action === 'record' && (!args.workspace || !args.run)) {
    throw new BoardContractError('RESUME_USAGE_INVALID')
  }
  let result = action === 'card'
    ? await buildCaseResumeCard({
      workspaceRoot: args.workspace || null,
      runId: args.run || null,
      expectedReceiptDigest: args['receipt-digest'] || null,
    })
    : action === 'inspect'
      ? await inspectPredecessorResume({ sourceWorkspaceRoot: args['source-workspace'], sourceRunId: args['source-run'] })
      : await recordPredecessorResumeDigest({
        sourceWorkspaceRoot: args['source-workspace'],
        sourceRunId: args['source-run'],
        targetWorkspaceRoot: args.workspace,
        targetRunId: args.run,
      })
  if (action === 'card' && args['inspect-only']) result = suppressCaseResumeActionPresentation(result)
  printJson({
    schema: 'fbsir.board-script-receipt/v1',
    ok: true,
    action: `resume.${action}`,
    result,
    evidenceBoundary: 'read_only_resume_card_or_stable_handle_captured_exact_predecessor_or_legacy_digest_or_cooperative_new_workspace_receipt_only_not_atomic_cross_file_snapshot_hostile_same_identity_race_content_truth_host_receipt_current_run_completion_or_product_credit',
  })
} catch (error) {
  printJson(failureReceipt(`resume.${action || 'unknown'}`, error))
  process.exitCode = 1
}
