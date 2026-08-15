#!/usr/bin/env node
import path from 'node:path'

import {
  buildCognitiveAssetBundle,
  defaultCognitiveAssetRoot,
  hashDecisionCard,
  validateCognitiveCatalog,
  verifyCognitiveAssetBundle,
} from './lib/cognitive-assets.mjs'
import { failureReceipt, parseArgs, printJson, readJsonStdin } from './lib/cli.mjs'

const args = parseArgs(process.argv.slice(2))
const [domain, verb] = args._
const action = domain === 'catalog' && verb === 'validate'
  ? 'asset.catalog.validate'
  : domain === 'decision-card' && verb === 'hash'
    ? 'asset.decision-card.hash'
  : domain === 'bundle' && verb === 'build'
    ? 'asset.bundle.build'
    : domain === 'bundle' && verb === 'verify'
      ? 'asset.bundle.verify'
      : 'asset.command.invalid'

try {
  const assetRoot = path.resolve(args['asset-root'] || defaultCognitiveAssetRoot())
  if (domain === 'catalog' && verb === 'validate') {
    const result = await validateCognitiveCatalog({ assetRoot, asOf: args['as-of'] || new Date().toISOString().slice(0, 10), rejectStale: true })
    printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: 'asset.catalog.validate', result, evidenceBoundary: result.evidenceBoundary })
  } else if (domain === 'decision-card' && verb === 'hash') {
    const input = await readJsonStdin()
    const result = hashDecisionCard(input)
    printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: 'asset.decision-card.hash', result, evidenceBoundary: result.evidenceBoundary })
  } else if (domain === 'bundle' && verb === 'build') {
    const input = await readJsonStdin()
    const result = await buildCognitiveAssetBundle({ assetRoot, workspaceRoot: args['workspace-root'], input })
    printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: 'asset.bundle.build', result, evidenceBoundary: result.evidenceBoundary })
  } else if (domain === 'bundle' && verb === 'verify') {
    const input = await readJsonStdin()
    const result = await verifyCognitiveAssetBundle({ assetRoot, workspaceRoot: args['workspace-root'], input })
    printJson({ schema: 'fbsir.board-script-receipt/v1', ok: true, action: 'asset.bundle.verify', result, evidenceBoundary: result.evidenceBoundary })
  } else {
    const error = new Error('Usage: board-assets.mjs catalog validate | decision-card hash | bundle build | bundle verify')
    error.code = 'ASSET_COMMAND_INVALID'
    throw error
  }
} catch (error) {
  printJson(failureReceipt(action, error))
  process.exitCode = 1
}
