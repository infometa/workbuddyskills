import type { RenderContext } from '../types.js';
import { getContextPercent, getModelName } from '../stdin.js';
import { cyan, dim, red, coloredBar } from './colors.js';

export function renderSessionLine(ctx: RenderContext): string {
  const { stdin, claudeMdCount, rulesCount, mcpCount, hooksCount, sessionDuration } = ctx;

  const modelName = getModelName(stdin);
  const contextPercent = getContextPercent(stdin);

  const parts: string[] = [];

  // Model name in brackets
  parts.push(cyan(`[${modelName}]`));

  // Context bar with percentage
  const bar = coloredBar(contextPercent, 10);
  parts.push(`${bar} ${contextPercent.toFixed(0)}%`);

  // Config counts (only show if > 0)
  const configParts: string[] = [];
  if (claudeMdCount > 0) configParts.push(`${claudeMdCount} CLAUDE.md`);
  if (rulesCount > 0) configParts.push(`${rulesCount} rules`);
  if (mcpCount > 0) configParts.push(`${mcpCount} MCPs`);
  if (hooksCount > 0) configParts.push(`${hooksCount} hooks`);

  if (configParts.length > 0) {
    parts.push(dim(`(${configParts.join(', ')})`));
  }

  // Session duration
  if (sessionDuration) {
    parts.push(dim(`⏱ ${sessionDuration}`));
  }

  // Token details at high context usage
  if (contextPercent >= 85) {
    const input = stdin.input_tokens || 0;
    const cache = (stdin.cache_creation_input_tokens || 0) + (stdin.cache_read_input_tokens || 0);
    parts.push(dim(`[${formatTokens(input)} input + ${formatTokens(cache)} cache]`));
  }

  // Warning at critical usage
  if (contextPercent >= 95) {
    parts.push(red('⚠️ COMPACT'));
  }

  return parts.join(' ');
}

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(1)}M`;
  }
  if (tokens >= 1_000) {
    return `${(tokens / 1_000).toFixed(0)}k`;
  }
  return tokens.toString();
}
