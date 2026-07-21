import type { RenderContext } from '../types.js';
import { yellow, green, dim } from './colors.js';

export function renderTodosLine(ctx: RenderContext): string | null {
  const { todos } = ctx.transcript;

  if (!todos || todos.length === 0) {
    return null;
  }

  const inProgress = todos.find((t) => t.status === 'in_progress');
  const completed = todos.filter((t) => t.status === 'completed').length;
  const total = todos.length;

  if (!inProgress) {
    if (completed === total && total > 0) {
      return `${green('✓')} All todos complete ${dim(`(${completed}/${total})`)}`;
    }
    return null;
  }

  const content = truncateContent(inProgress.content);
  const progress = dim(`(${completed}/${total})`);

  return `${yellow('▸')} ${content} ${progress}`;
}

function truncateContent(content: string, maxLen: number = 50): string {
  if (content.length <= maxLen) return content;
  return content.slice(0, maxLen - 3) + '...';
}
