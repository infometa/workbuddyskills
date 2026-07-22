import { appendEvent, verifyLedger } from './lib/core.mjs'
import { failureReceipt, parseArgs, printJson, readJsonStdin } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))
const action = args._[0]
try {
  if (!args.workspace || !args.run || !['append', 'verify'].includes(action)) throw new Error('USAGE: board-event.mjs <append|verify> --workspace PATH --run ID')
  const result = action === 'verify'
    ? await verifyLedger(args.workspace, args.run)
    : await appendEvent({ workspaceRoot: args.workspace, runId: args.run, ...(await readJsonStdin()) })
  printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: `event.${action}`, result, evidenceBoundary: 'local_event_chain_only_not_host_tool_proof' })
} catch (error) {
  printJson(failureReceipt(`event.${action || 'unknown'}`, error))
  process.exitCode = 1
}

