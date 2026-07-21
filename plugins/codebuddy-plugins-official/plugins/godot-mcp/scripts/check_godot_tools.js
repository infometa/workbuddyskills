/**
 * Check if godot-tools extension is available and prompt for installation if missing.
 * Called from SessionStart hook in hooks/hooks.json.
 *
 * CLI --install-extension installs to VS Code, not to the current IDE (CodeBuddy/Cursor),
 * so we only detect and prompt — actual install must happen via IDE's "Install from VSIX".
 */
const path = require('path');
const fs = require('fs');

const VSIX_NAME = 'geequlim.godot-tools-2.6.1.vsix';
const EXTENSION_ID = 'geequlim.godot-tools';
const LOG_PREFIX = '[godot-mcp]';

function getVsixPath() {
  const pluginRoot = process.env.CODEBUDDY_PLUGIN_ROOT
    || process.env.CLAUDE_PLUGIN_ROOT
    || path.resolve(__dirname, '..');
  return path.join(pluginRoot, 'tools', VSIX_NAME);
}

function isExtensionInstalled() {
  // Check common IDE extension directories
  const home = process.env.USERPROFILE || process.env.HOME || '';
  const candidates = [
    path.join(home, '.codebuddy', 'extensions'),
    path.join(home, '.cursor', 'extensions'),
    path.join(home, '.vscode', 'extensions'),
  ];

  for (const extDir of candidates) {
    if (!fs.existsSync(extDir)) continue;
    try {
      const entries = fs.readdirSync(extDir);
      if (entries.some(e => e.startsWith('geequlim.godot-tools'))) {
        return extDir;
      }
    } catch {
      // skip
    }
  }
  return null;
}

function main() {
  const found = isExtensionInstalled();
  if (found) {
    return; // already installed somewhere
  }

  const vsixPath = getVsixPath();
  if (!fs.existsSync(vsixPath)) {
    console.warn(`${LOG_PREFIX} godot-tools not installed. VSIX not found at ${vsixPath}.`);
    console.warn(`${LOG_PREFIX} Install manually: Ctrl+Shift+P → "Extensions: Install from VSIX"`);
    return;
  }

  console.warn(`${LOG_PREFIX} godot-tools extension not detected.`);
  console.warn(`${LOG_PREFIX} To install: Ctrl+Shift+P → "Extensions: Install from VSIX" → select:`);
  console.warn(`${LOG_PREFIX}   ${vsixPath}`);
}

main();
