import { createCheckpoint } from './lib/core.mjs'
import { failureReceipt, parseArgs, printJson } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))
try {
  if (!args.workspace || !args.run || !args.state) throw new Error('USAGE: board-checkpoint.mjs --workspace PATH --run ID --state STATE --actor board-convener')
  const result = await createCheckpoint({ workspaceRoot: args.workspace, runId: args.run, actorId: args.actor, state: args.state })
  printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: 'checkpoint.create', result, evidenceBoundary: 'local_checkpoint_marker_only_no_automatic_recovery_or_adversarial_tamper_proof' })
} catch (error) {
  printJson(failureReceipt('checkpoint.create', error))
  process.exitCode = 1
}
