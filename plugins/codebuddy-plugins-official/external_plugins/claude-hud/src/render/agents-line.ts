import type { RenderContext, AgentEntry } from '../types.js';
import { yellow, green, magenta, dim } from './colors.js';

export function renderAgentsLine(ctx: RenderContext): string | null {
  const { agents } = ctx.transcript;

  if (!agents || agents.length === 0) {
    return null;
  }

  const running = agents.filter((a) => a.status === 'running');
  const completed = agents.filter((a) => a.status === 'completed');

  // Show all running + 2 most recent completed
  const toShow: AgentEntry[] = [
    ...running,
    ...completed.slice(-2),
  ].slice(0, 3);

  if (toShow.length === 0) {
    return null;
  }

  const parts = toShow.map((agent) => formatAgent(agent));
  return parts.join(' | ');
}

function formatAgent(agent: AgentEntry): string {
  const status = agent.status === 'running' ? yellow('●') : green('✓');
  const type = magenta(agent.type);

  const extras: string[] = [];

  if (agent.model) {
    extras.push(dim(`(${agent.model})`));
  }

  if (agent.description) {
    extras.push(dim(truncateDesc(agent.description)));
  }

  if (agent.status === 'running' && agent.startTime) {
    extras.push(dim(formatElapsed(Date.now() - agent.startTime)));
  }

  const extraStr = extras.length > 0 ? ' ' + extras.join(' ') : '';
  return `${status} ${type}${extraStr}`;
}

function truncateDesc(desc: string, maxLen: number = 40): string {
  if (desc.length <= maxLen) return desc;
  return desc.slice(0, maxLen - 3) + '...';
}

function formatElapsed(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
