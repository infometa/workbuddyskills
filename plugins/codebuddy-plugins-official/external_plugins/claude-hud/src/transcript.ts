import * as fs from 'fs';
import * as readline from 'readline';
import type { TranscriptData, ToolEntry, AgentEntry, TodoItem } from './types.js';

interface TranscriptEntry {
  type?: string;
  message?: {
    content?: Array<{
      type?: string;
      id?: string;
      name?: string;
      input?: Record<string, unknown>;
      tool_use_id?: string;
      is_error?: boolean;
    }>;
  };
  timestamp?: string;
}

export async function parseTranscript(transcriptPath: string): Promise<TranscriptData> {
  const tools: Map<string, ToolEntry> = new Map();
  const agents: Map<string, AgentEntry> = new Map();
  let todos: TodoItem[] = [];
  let sessionStart: Date | undefined;

  if (!transcriptPath || !fs.existsSync(transcriptPath)) {
    return { tools: [], agents: [], todos: [] };
  }

  try {
    const fileStream = fs.createReadStream(transcriptPath);
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity,
    });

    for await (const line of rl) {
      if (!line.trim()) continue;

      try {
        const entry = JSON.parse(line) as TranscriptEntry;
        processEntry(entry, tools, agents, todos, (t) => (todos = t), (d) => { if (!sessionStart) sessionStart = d; });
      } catch {
        // Skip malformed JSON lines
      }
    }
  } catch {
    // Return partial results on error
  }

  return {
    tools: Array.from(tools.values()).slice(-20),
    agents: Array.from(agents.values()).slice(-10),
    todos,
    sessionStart,
  };
}

function processEntry(
  entry: TranscriptEntry,
  tools: Map<string, ToolEntry>,
  agents: Map<string, AgentEntry>,
  _todos: TodoItem[],
  setTodos: (todos: TodoItem[]) => void,
  setSessionStart: (date: Date) => void
): void {
  if (entry.timestamp) {
    setSessionStart(new Date(entry.timestamp));
  }

  const content = entry.message?.content;
  if (!Array.isArray(content)) return;

  for (const block of content) {
    if (block.type === 'tool_use' && block.id && block.name) {
      if (block.name === 'Task') {
        // Task tool = agent
        const input = block.input as { subagent_type?: string; description?: string; model?: string } | undefined;
        agents.set(block.id, {
          id: block.id,
          type: (input?.subagent_type as string) || 'unknown',
          description: input?.description as string,
          model: input?.model as string,
          status: 'running',
          startTime: Date.now(),
        });
      } else if (block.name === 'TodoWrite') {
        // TodoWrite updates todos
        const input = block.input as { todos?: TodoItem[] } | undefined;
        if (input?.todos) {
          setTodos(input.todos);
        }
      } else {
        // Regular tool
        tools.set(block.id, {
          id: block.id,
          name: block.name,
          status: 'running',
          target: extractTarget(block.name, block.input),
          startTime: Date.now(),
        });
      }
    } else if (block.type === 'tool_result' && block.tool_use_id) {
      const tool = tools.get(block.tool_use_id);
      if (tool) {
        tool.status = block.is_error ? 'error' : 'completed';
        tool.endTime = Date.now();
      }

      const agent = agents.get(block.tool_use_id);
      if (agent) {
        agent.status = 'completed';
        agent.endTime = Date.now();
      }
    }
  }
}

function extractTarget(toolName: string, input?: Record<string, unknown>): string | undefined {
  if (!input) return undefined;

  switch (toolName) {
    case 'Read':
    case 'Write':
    case 'Edit':
      return input.file_path as string;
    case 'Glob':
      return input.pattern as string;
    case 'Grep':
      return input.pattern as string;
    case 'Bash':
      return input.command as string;
    default:
      return undefined;
  }
}
