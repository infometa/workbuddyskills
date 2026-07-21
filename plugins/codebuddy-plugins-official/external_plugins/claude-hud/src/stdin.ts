import type { StdinData } from './types.js';

export async function readStdin(): Promise<StdinData | null> {
  if (process.stdin.isTTY) {
    return null;
  }

  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }

  const input = Buffer.concat(chunks).toString('utf8').trim();
  if (!input) {
    return null;
  }

  try {
    return JSON.parse(input) as StdinData;
  } catch {
    return null;
  }
}

export function getContextPercent(stdin: StdinData): number {
  const { context_window, input_tokens, cache_creation_input_tokens, cache_read_input_tokens } = stdin;

  if (!context_window || context_window === 0) {
    return 0;
  }

  const total = (input_tokens || 0) + (cache_creation_input_tokens || 0) + (cache_read_input_tokens || 0);
  return (total / context_window) * 100;
}

export function getModelName(stdin: StdinData): string {
  return stdin.model?.display_name || stdin.model?.id || 'Unknown';
}
