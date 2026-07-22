import { initializeWorkspace, readWorkspace } from './lib/core.mjs'
import { failureReceipt, parseArgs, printJson } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))
const action = args._[0]
try {
  if (!args.workspace || !['init', 'status'].includes(action)) throw new Error('USAGE: board-workspace.mjs <init|status> --workspace PATH [--workspace-id ID]')
  const marker = action === 'init'
    ? await initializeWorkspace(args.workspace, { workspaceId: args['workspace-id'] })
    : await readWorkspace(args.workspace)
  printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: `workspace.${action}`, marker, evidenceBoundary: 'local_workspace_state_only' })
} catch (error) {
  printJson(failureReceipt(`workspace.${action || 'unknown'}`, error))
  process.exitCode = 1
}

