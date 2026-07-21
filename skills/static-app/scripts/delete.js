#!/usr/bin/env node
/**
 * Delete site from Static.app
 */

const fetch = require('node-fetch');

const API_BASE = 'https://api.static.app/v1/sites';

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    apiKey: process.env.STATIC_APP_API_KEY,
    pid: null,
    force: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '-k' || arg === '--api-key') {
      options.apiKey = args[++i];
    } else if (arg === '-p' || arg === '--pid') {
      options.pid = args[++i];
    } else if (arg === '-f' || arg === '--force') {
      options.force = true;
    } else if (arg === '-h' || arg === '--help') {
      showHelp();
      process.exit(0);
    } else if (!arg.startsWith('-') && !options.pid) {
      options.pid = arg;
    }
  }

  return options;
}

function showHelp() {
  console.log(`
Usage: node delete.js [PID] [OPTIONS]

Delete a site from Static.app

Arguments:
  PID                Site PID to delete

Options:
  -p, --pid          Site PID to delete
  -k, --api-key      API key (or set STATIC_APP_API_KEY env var)
  -f, --force        Skip confirmation prompt
  -h, --help         Show this help

Examples:
  node delete.js abc123
  node delete.js -p abc123
  node delete.js abc123 --force
`);
}

async function deleteSite(apiKey, pid) {
  const url = `${API_BASE}/${pid}`;
  
  console.log(`🗑️  Deleting site: ${pid}...\n`);
  
  const response = await fetch(url, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  // DELETE may return 204 No Content or empty body
  if (response.status === 204 || response.status === 200) {
    return { success: true, message: 'Site deleted successfully' };
  }

  // Try to parse JSON, but handle empty responses
  const text = await response.text();
  if (!text || text.trim() === '') {
    return { success: true, message: 'Site deleted successfully' };
  }
  
  try {
    return JSON.parse(text);
  } catch (e) {
    return { success: true, message: 'Site deleted successfully' };
  }
}

async function confirmDeletion(pid) {
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question(`⚠️  Are you sure you want to delete site "${pid}"? (yes/no): `, (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === 'yes');
    });
  });
}

async function main() {
  const options = parseArgs();
  
  if (!options.apiKey) {
    console.error('❌ Error: API key required. Provide --api-key or set STATIC_APP_API_KEY env var.');
    console.error('   Get your API key at: https://static.app/account/api');
    process.exit(1);
  }
  
  if (!options.pid) {
    console.error('❌ Error: PID required. Provide PID as argument or use --pid.');
    console.error('   Example: node delete.js abc123');
    process.exit(1);
  }
  
  // Confirm deletion unless --force is used
  if (!options.force) {
    const confirmed = await confirmDeletion(options.pid);
    if (!confirmed) {
      console.log('\n❌ Deletion cancelled.');
      process.exit(0);
    }
  }
  
  try {
    const result = await deleteSite(options.apiKey, options.pid);
    
    console.log(`✅ Site "${options.pid}" deleted successfully!`);
    
  } catch (error) {
    console.error(`❌ Failed to delete site: ${error.message}`);
    process.exit(1);
  }
}

main();
