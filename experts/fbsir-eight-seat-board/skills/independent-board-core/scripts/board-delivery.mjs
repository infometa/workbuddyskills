import { prepareDelivery } from './lib/core.mjs'
import { failureReceipt, parseArgs, printJson } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))

try {
  if (!args.workspace || !args.run || !args.artifact || !args.type) {
    throw new Error('USAGE: board-delivery.mjs --workspace PATH --run ID --artifact PATH --type <quick_review_card|review_memo|deep_review_preparation_card>')
  }
  const result = await prepareDelivery({ workspaceRoot: args.workspace, runId: args.run, artifactPath: args.artifact, artifactType: args.type })
  printJson({
    schema: 'fbsir.board-script-receipt/v1',
    ok: true,
    action: 'delivery.prepare',
    result,
    evidenceBoundary: result.delivery.evidenceBoundary,
  })
} catch (error) {
  printJson(failureReceipt('delivery.prepare', error))
  process.exitCode = 1
}
