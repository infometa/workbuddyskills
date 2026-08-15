import { appendEvent, BoardContractError, recordHostReceiptObservation, verifyLedger } from './lib/core.mjs'
import { failureReceipt, parseArgs, printJson, readJsonStdinNoDuplicateKeys } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))
const action = args._[0]
try {
  if (!args.workspace || !args.run || !['append', 'register-host-receipt', 'verify'].includes(action)) throw new Error('USAGE: board-event.mjs <append|register-host-receipt|verify> --workspace PATH --run ID')
  const input = action === 'verify' ? null : await readJsonStdinNoDuplicateKeys()
  if (input && (Object.hasOwn(input, 'workspaceRoot') || Object.hasOwn(input, 'runId'))) {
    throw new BoardContractError('EVENT_CLI_SCOPE_FIELD_FORBIDDEN', 'Workspace and run scope must come from CLI authority')
  }
  const result = action === 'verify'
    ? await verifyLedger(args.workspace, args.run)
    : action === 'register-host-receipt'
      ? await recordHostReceiptObservation({ ...input, workspaceRoot: args.workspace, runId: args.run })
      : await appendEvent({ ...input, workspaceRoot: args.workspace, runId: args.run })
  printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: `event.${action}`, result, evidenceBoundary: 'local_event_chain_only_not_host_tool_proof' })
} catch (error) {
  printJson(failureReceipt(`event.${action || 'unknown'}`, error))
  process.exitCode = 1
}

