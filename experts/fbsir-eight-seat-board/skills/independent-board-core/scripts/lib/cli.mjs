import { readFile } from 'node:fs/promises'

export function parseArgs(tokens) {
  const result = { _: [] }
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index]
    if (!token.startsWith('--')) { result._.push(token); continue }
    const key = token.slice(2)
    const next = tokens[index + 1]
    if (next === undefined || next.startsWith('--')) result[key] = true
    else { result[key] = next; index += 1 }
  }
  return result
}

export async function readJsonStdin() {
  const chunks = []
  for await (const chunk of process.stdin) chunks.push(chunk)
  const raw = Buffer.concat(chunks).toString('utf8').trim()
  return raw ? JSON.parse(raw) : {}
}

export async function readJsonFile(filePath) {
  return JSON.parse(await readFile(filePath, 'utf8'))
}

export function printJson(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`)
}

export function failureReceipt(action, error) {
  return {
    schema: 'fbsir.board-script-receipt/v1',
    ok: false,
    action,
    failure: {
      code: error?.code || 'UNEXPECTED_ERROR',
      message: error?.message || String(error),
      details: error?.details || {},
    },
    evidenceBoundary: 'script_failure_only_no_host_runtime_claim',
  }
}

