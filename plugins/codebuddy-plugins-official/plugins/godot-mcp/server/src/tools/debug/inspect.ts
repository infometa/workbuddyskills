import { z } from 'zod';
import { getGodotConnection } from '../../utils/godot_connection.js';
import { MCPTool, CommandResult } from '../../utils/types.js';

interface ScriptError {
  type: string;
  message: string;
  line: number;
  column?: number;
  file?: string;
  code_snippet?: string;
  context?: string;
  suggestion?: string;
  severity?: string;
}

interface DebugError {
  type: string;
  file: string;
  line: number;
  message: string;
  severity: string;
}

interface DebugErrorsResult extends CommandResult {
  errors: DebugError[];
  total_errors: number;
  compile_errors: number;
  log_errors: number;
  timestamp: string;
}

interface DetailedErrorResult extends CommandResult {
  script_path: string;
  errors: ScriptError[];
  warnings: ScriptError[];
  total_lines: number;
  content: string;
}

/**
 * Debug group: minimal toolkit for the debug-fix loop.
 *   1. get_debug_errors    → one-shot scan of the whole project
 *   2. get_script_errors   → drill into a single script for fix details
 *   3. get_editor_output   → raw editor log tail for runtime issues
 */
export const debugTools: MCPTool[] = [
  {
    name: 'get_debug_errors',
    description:
      'One-shot project scan: returns ALL current GDScript compilation errors plus errors ' +
      'extracted from the Godot editor log. Primary entry point for the debug-fix cycle:\n' +
      '1) call get_debug_errors → 2) for each error call get_script_errors for fix context → ' +
      '3) operate_script(action="edit") to apply the fix → 4) repeat until no errors.',
    parameters: z.object({
      include_log_errors: z.boolean().optional().describe('Include errors from Godot log file (default: true)'),
      directory: z.string().optional().describe('Root directory to scan (default: "res://")'),
      exclude_addons: z.boolean().optional().describe('Skip addons/ directory (default: true)'),
      project: z.string().optional().describe('Target project (defaults to active)'),
    }),
    execute: async ({ include_log_errors, directory, exclude_addons, project }: {
      include_log_errors?: boolean; directory?: string; exclude_addons?: boolean; project?: string;
    }): Promise<string> => {
      const godot = getGodotConnection(project);
      try {
        const result = await godot.sendCommand<DebugErrorsResult>('get_debug_errors', {
          include_log_errors: include_log_errors ?? true,
          directory: directory ?? 'res://',
          exclude_addons: exclude_addons ?? true,
        });

        if (result.total_errors === 0) {
          return `✓ No errors found in the project.\n\nTimestamp: ${result.timestamp}`;
        }

        let output = `✗ Found ${result.total_errors} error(s) (${result.compile_errors} compile, ${result.log_errors} log)\n`;
        output += `Timestamp: ${result.timestamp}\n\n`;
        for (let i = 0; i < result.errors.length; i++) {
          const err = result.errors[i];
          output += `── Error ${i + 1} ──\n`;
          output += `Type: ${err.type}\nSeverity: ${err.severity}\nMessage: ${err.message}\n`;
          if (err.file) {
            output += `File: ${err.file}`;
            if (err.line > 0) output += `:${err.line}`;
            output += '\n';
          }
          output += '\n';
        }
        output += `\nNext: call get_script_errors(script_path) for fix context, then operate_script(action="edit") to apply.`;
        return output;
      } catch (error) {
        throw new Error(`Failed to get debug errors: ${(error as Error).message}`);
      }
    },
  },

  {
    name: 'get_script_errors',
    description:
      'Get DETAILED error information for a single script: exact line/column, code snippet, ' +
      'surrounding context, fix suggestions, and the full script content. ' +
      'Use after get_debug_errors to obtain the context needed to apply a fix.',
    parameters: z.object({
      script_path: z.string().describe('Path to the script (e.g. "res://scripts/player.gd")'),
      include_warnings: z.boolean().optional().describe('Include warnings (default: true)'),
      project: z.string().optional().describe('Target project (defaults to active)'),
    }),
    execute: async ({ script_path, include_warnings = true, project }: {
      script_path: string; include_warnings?: boolean; project?: string;
    }): Promise<string> => {
      const godot = getGodotConnection(project);
      try {
        const result = await godot.sendCommand<DetailedErrorResult>('get_script_errors', {
          script_path, include_warnings,
        });

        let output = `Detailed Error Report: ${script_path}\n${'═'.repeat(50)}\n\n`;
        output += `Total Lines: ${result.total_lines}\nErrors: ${result.errors.length}\n`;
        if (include_warnings) output += `Warnings: ${result.warnings.length}\n`;
        output += '\n';

        if (result.errors.length === 0 && result.warnings.length === 0) {
          return output + `✓ No issues found.\n`;
        }

        if (result.errors.length > 0) {
          output += `Errors:\n${'─'.repeat(50)}\n\n`;
          for (let i = 0; i < result.errors.length; i++) {
            const e = result.errors[i];
            output += `[Error ${i + 1}] ${e.message}\nLocation: Line ${e.line}`;
            if (e.column) output += `, Column ${e.column}`;
            output += '\n';
            if (e.context) output += `\nContext:\n${e.context}\n`;
            if (e.suggestion) output += `\nSuggestion: ${e.suggestion}\n`;
            output += '\n';
          }
        }
        if (include_warnings && result.warnings.length > 0) {
          output += `Warnings:\n${'─'.repeat(50)}\n`;
          for (const w of result.warnings) output += `Line ${w.line}: ${w.message}\n`;
          output += '\n';
        }
        output += `\nFull Script Content:\n${'─'.repeat(50)}\n\`\`\`gdscript\n${result.content}\n\`\`\`\n`;
        return output;
      } catch (error) {
        throw new Error(`Failed to get script errors: ${(error as Error).message}`);
      }
    },
  },

  {
    name: 'get_editor_output',
    description:
      'Read the raw Godot editor Output panel log (errors, warnings, print() output). ' +
      'Use to diagnose runtime issues that do not surface as compile errors.',
    parameters: z.object({
      lines: z.number().int().min(1).max(1000).optional()
        .describe('Number of recent lines (default: 100)'),
      filter: z.enum(['all', 'errors', 'warnings']).optional()
        .describe('Filter: all | errors | warnings (default: all)'),
      project: z.string().optional().describe('Target project (defaults to active)'),
    }),
    execute: async ({ lines, filter, project }: { lines?: number; filter?: string; project?: string }): Promise<string> => {
      const godot = getGodotConnection(project);
      try {
        const result = await godot.sendCommand<CommandResult>('get_editor_output', {
          lines: lines ?? 100,
          filter: filter ?? 'all',
        });

        let output = `Godot Editor Output (${result.filter} | last ${result.returned_lines} of ${result.total_lines} lines)\n`;
        output += `Log file: ${result.log_path}\n${'─'.repeat(60)}\n`;
        output += result.output || '(empty)';

        if (result.script_errors && result.script_errors.length > 0) {
          output += '\n\n── Script Compilation Errors ──\n';
          for (const err of result.script_errors) output += `  ${err.script}: ${err.status}\n`;
        }
        return output;
      } catch (error) {
        throw new Error(`Failed to get editor output: ${(error as Error).message}`);
      }
    },
  },
];
