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

function hasUniqueJsonObjectKeys(raw) {
  let index = 0
  const whitespace = /[\t\n\r ]/
  const skipWhitespace = () => { while (whitespace.test(raw[index] || '')) index += 1 }
  const parseString = () => {
    const start = index
    if (raw[index] !== '"') throw new SyntaxError('JSON string expected')
    index += 1
    while (index < raw.length) {
      const character = raw[index]
      if (character === '"') {
        index += 1
        return JSON.parse(raw.slice(start, index))
      }
      if (character === '\\') {
        index += 1
        if (raw[index] === 'u') {
          if (!/^[0-9a-fA-F]{4}$/.test(raw.slice(index + 1, index + 5))) throw new SyntaxError('Invalid JSON escape')
          index += 5
          continue
        }
        if (!/["\\/bfnrt]/.test(raw[index] || '')) throw new SyntaxError('Invalid JSON escape')
      }
      index += 1
    }
    throw new SyntaxError('Unclosed JSON string')
  }
  const parseValue = (depth) => {
    if (depth > 32) throw new SyntaxError('JSON nesting limit exceeded')
    skipWhitespace()
    if (raw[index] === '"') { parseString(); return }
    if (raw[index] === '{') { parseObject(depth + 1); return }
    if (raw[index] === '[') { parseArray(depth + 1); return }
    const primitive = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(raw.slice(index))?.[0]
    if (!primitive) throw new SyntaxError('Invalid JSON value')
    index += primitive.length
  }
  const parseObject = (depth) => {
    index += 1
    skipWhitespace()
    const keys = new Set()
    if (raw[index] === '}') { index += 1; return }
    while (index < raw.length) {
      skipWhitespace()
      const key = parseString()
      if (keys.has(key)) throw new SyntaxError('Duplicate JSON object key')
      keys.add(key)
      skipWhitespace()
      if (raw[index] !== ':') throw new SyntaxError('JSON colon expected')
      index += 1
      parseValue(depth)
      skipWhitespace()
      if (raw[index] === '}') { index += 1; return }
      if (raw[index] !== ',') throw new SyntaxError('JSON comma expected')
      index += 1
    }
    throw new SyntaxError('Unclosed JSON object')
  }
  const parseArray = (depth) => {
    index += 1
    skipWhitespace()
    if (raw[index] === ']') { index += 1; return }
    while (index < raw.length) {
      parseValue(depth)
      skipWhitespace()
      if (raw[index] === ']') { index += 1; return }
      if (raw[index] !== ',') throw new SyntaxError('JSON comma expected')
      index += 1
    }
    throw new SyntaxError('Unclosed JSON array')
  }
  parseValue(0)
  skipWhitespace()
  if (index !== raw.length) throw new SyntaxError('Trailing JSON input')
}

export async function readJsonStdinNoDuplicateKeys() {
  const chunks = []
  let totalBytes = 0
  for await (const chunk of process.stdin) {
    totalBytes += chunk.length
    if (totalBytes > 1024 * 1024) throw new SyntaxError('JSON input exceeds the one MiB contract limit')
    chunks.push(chunk)
  }
  const raw = Buffer.concat(chunks).toString('utf8').trim()
  if (!raw) return {}
  hasUniqueJsonObjectKeys(raw)
  return JSON.parse(raw)
}

export async function readJsonFile(filePath) {
  return JSON.parse(await readFile(filePath, 'utf8'))
}

export function printJson(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`)
}

function safeFailureDetails(details) {
  if (!details || typeof details !== 'object' || Array.isArray(details)) return {}
  const numericKeys = new Set([
    'actual', 'expected', 'count', 'expectedCount', 'actualCount', 'missingCount',
    'unexpectedCount', 'length', 'ownKeyCount', 'revision', 'attempt',
  ])
  return Object.fromEntries(Object.entries(details).filter(([key, value]) => (
    numericKeys.has(key) && Number.isSafeInteger(value) && Math.abs(value) <= 1000000
  )))
}

export function failureReceipt(action, error) {
  const malformedJson = error instanceof SyntaxError
  const contractFailure = typeof error?.code === 'string' && error.code.length > 0
  return {
    schema: 'fbsir.board-script-receipt/v1',
    ok: false,
    action,
    failure: {
      code: malformedJson ? 'JSON_INPUT_INVALID' : error?.code || 'UNEXPECTED_ERROR',
      message: malformedJson
        ? 'JSON input is invalid'
        : contractFailure
          ? 'Request failed contract validation'
          : 'Unexpected error',
      details: malformedJson ? {} : safeFailureDetails(error?.details),
    },
    evidenceBoundary: 'script_failure_only_no_host_runtime_claim',
  }
}

