import { routeScene } from './lib/core.mjs'
import { failureReceipt, printJson, readJsonStdin } from './lib/cli.mjs'

try {
  const input = await readJsonStdin()
  const result = await routeScene(input.text)
  printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: 'scene.route', result, evidenceBoundary: 'deterministic_dictionary_hint_only' })
} catch (error) {
  printJson(failureReceipt('scene.route', error))
  process.exitCode = 1
}

