import type { RenderContext } from '../types.js';
import { yellow, green, cyan, dim } from './colors.js';

const SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

export function renderToolsLine(ctx: RenderContext): string | null {
  const { tools } = ctx.transcript;

  if (!tools || tools.length === 0) {
    return null;
  }

  const running = tools.filter((t) => t.status === 'running');
  const completed = tools.filter((t) => t.status === 'completed');

  const parts: string[] = [];

  // Running tools (show up to 2)
  if (running.length > 0) {
    const spinnerIndex = Math.floor(Date.now() / 100) % SPINNER_FRAMES.length;
    const spinner = yellow(SPINNER_FRAMES[spinnerIndex]);

    const runningDisplay = running.slice(0, 2).map((t) => {
      const target = t.target ? ` ${dim(truncatePath(t.target))}` : '';
      return `${spinner} ${cyan(t.name)}${target}`;
    });

    parts.push(...runningDisplay);

    if (running.length > 2) {
      parts.push(dim(`+${running.length - 2} more`));
    }
  }

  // Completed tools (show top 4 by frequency)
  if (completed.length > 0) {
    const counts: Record<string, number> = {};
    for (const tool of completed) {
      counts[tool.name] = (counts[tool.name] || 0) + 1;
    }

    const sorted = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4);

    const completedDisplay = sorted.map(([name, count]) => {
      return `${green('✓')} ${name}${count > 1 ? dim(`×${count}`) : ''}`;
    });

    parts.push(...completedDisplay);
  }

  if (parts.length === 0) {
    return null;
  }

  return parts.join(' | ');
}

export function truncatePath(pathStr: string, maxLen: number = 20): string {
  if (pathStr.length <= maxLen) return pathStr;

  const parts = pathStr.split('/');
  const fileName = parts[parts.length - 1];

  if (fileName.length >= maxLen - 3) {
    return '...' + fileName.slice(-(maxLen - 3));
  }

  return '...' + fileName;
}
