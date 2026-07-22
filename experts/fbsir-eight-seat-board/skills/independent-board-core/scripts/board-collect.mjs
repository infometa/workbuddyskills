import { collectReviewRun } from './lib/core.mjs'
import { failureReceipt, parseArgs, printJson } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))

try {
  if (!args.workspace || !args.run) throw new Error('USAGE: board-collect.mjs --workspace PATH --run ID')
  const result = await collectReviewRun({ workspaceRoot: args.workspace, runId: args.run })
  printJson({
    schema: 'fbsir.board-script-receipt/v1',
    ok: true,
    action: 'review.collect',
    result,
    evidenceBoundary: result.collection.evidenceBoundary,
  })
  if (!result.collection.readyForSynthesis) process.exitCode = 2
} catch (error) {
  printJson(failureReceipt('review.collect', error))
  process.exitCode = 1
}
