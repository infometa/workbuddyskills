#!/usr/bin/env node
/**
 * PreToolUse hard-block: forbid Write/Edit on Godot project files
 * (project.godot / *.tscn / *.gd) when the workspace has no project.godot yet.
 *
 * The AI MUST go through init_godot_project first.
 *
 * CodeBuddy contract for PreToolUse `command` hooks:
 *   - stdin: JSON with tool_name, tool_input, etc.
 *   - exit code != 0 → block the tool call; stderr is shown to the AI.
 */
const fs = require('fs');
const path = require('path');

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', c => (raw += c));
process.stdin.on('end', () => {
  let payload = {};
  try { payload = JSON.parse(raw || '{}'); } catch { /* ignore */ }

  const toolName = payload.tool_name || payload.toolName || '';
  const input    = payload.tool_input || payload.toolInput || {};
  const filePath = input.file_path || input.filePath || input.path || '';
  if (!filePath) process.exit(0);

  const lower = filePath.toLowerCase().replace(/\\/g, '/');
  const isGodotFile =
    lower.endsWith('/project.godot') ||
    lower.endsWith('.tscn') ||
    lower.endsWith('.gd') ||
    lower.endsWith('.gdscript') ||
    lower.endsWith('.tres') ||
    lower.endsWith('.gdshader');
  if (!isGodotFile) process.exit(0);

  // Allow edits inside the plugin's own source tree (we ship .gd files in
  // addons/godot_mcp/ and templates/, those are NOT user game files).
  const pluginRoot = (process.env.CODEBUDDY_PLUGIN_ROOT
    || process.env.CLAUDE_PLUGIN_ROOT
    || '').replace(/\\/g, '/').toLowerCase();
  if (pluginRoot && lower.startsWith(pluginRoot + '/')) process.exit(0);
  // Also allow edits inside any addons/godot_mcp/ or templates/ subtree
  // regardless of where the plugin lives (covers dev-mode and copied addon).
  if (lower.includes('/addons/godot_mcp/') || lower.includes('/templates/')) {
    process.exit(0);
  }

  // Walk up looking for an existing project.godot
  let dir = path.resolve(path.dirname(filePath));
  const root = path.parse(dir).root;
  let foundProjectGodot = false;
  while (true) {
    if (fs.existsSync(path.join(dir, 'project.godot'))) {
      foundProjectGodot = true;
      break;
    }
    if (dir === root) break;
    const next = path.dirname(dir);
    if (next === dir) break;
    dir = next;
  }
  if (foundProjectGodot) process.exit(0);

  // Block.
  const ws = process.env.CODEBUDDY_WORKSPACE_ROOT
    || process.env.CLAUDE_PROJECT_DIR
    || process.cwd();
  const wsPosix = ws.replace(/\\/g, '/');
  const msg = [
    '',
    '🚫 GodotMCP guard: refusing to ' + toolName + ' "' + filePath + '"',
    '',
    'Reason: no project.godot found in any parent directory.',
    'Hand-writing Godot files (project.godot / .tscn / .gd / .tres / .gdshader)',
    'before initialising the project will produce a broken / un-importable project.',
    '',
    '✅ Required next action（4.23 重构后，请走 Skill，不要再找 MCP 创建工具）：',
    '',
    '   1. 读 skills/godot-dev/SKILL.md（统一入口，会自动分流到 godot-deploy /',
    '      godot-new），或者按工作区状态直接跳到对应子 Skill：',
    '        • 没有 ' + wsPosix + '/godot-editor/    → skills/godot-deploy/SKILL.md',
    '        • 没有 ' + wsPosix + '/active-game.json → skills/godot-new/SKILL.md',
    '   2. godot-new 会从 templates/<2d-platformer|3d-fps|empty|default>/ 复制',
    '      出整个项目（含 project.godot / scenes/ / scripts/ / addons/godot_mcp/），',
    '      并写 ${WORKSPACE}/active-game.json。',
    '   3. 后续修改场景请用 MCP 工具 build_godot_scene；查错用 get_debug_errors',
    '      / get_script_errors / get_editor_output。',
    '',
    '⚠️ 已被移除的 MCP 工具，请勿调用（一定失败）：',
    '     init_godot_project, operate_node, operate_scene, operate_script,',
    '     manage_project, run_project, get_project_info, scan_project_modules',
    '',
    'Do NOT retry Write/Edit on this file path.',
    '',
  ].join('\n');
  process.stderr.write(msg);
  process.exit(2); // non-zero → block
});
