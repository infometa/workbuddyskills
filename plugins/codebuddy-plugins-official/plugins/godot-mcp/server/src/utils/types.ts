import { z } from 'zod';

/**
 * Interface for FastMCP tool definition
 */
export interface MCPTool<T = any> {
  name: string;
  description: string;
  parameters: z.ZodType<T>;
  execute: (args: T) => Promise<string>;
}

/**
 * Generic response from a Godot command
 */
export interface CommandResult {
  [key: string]: any;
}