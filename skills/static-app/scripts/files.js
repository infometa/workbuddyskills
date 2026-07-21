#!/usr/bin/env node
/**
 * List files of a site from Static.app
 */

const fetch = require('node-fetch');

const API_BASE = 'https://api.static.app/v1/sites/files';

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    apiKey: process.env.STATIC_APP_API_KEY,
    pid: null,
    raw: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '-k' || arg === '--api-key') {
      options.apiKey = args[++i];
    } else if (arg === '-p' || arg === '--pid') {
      options.pid = args[++i];
    } else if (arg === '--raw') {
      options.raw = true;
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
Usage: node files.js [PID] [OPTIONS]

List all files of a site from Static.app

Arguments:
  PID                Site PID to list files

Options:
  -p, --pid          Site PID
  -k, --api-key      API key (or set STATIC_APP_API_KEY env var)
  --raw              Output raw JSON response
  -h, --help         Show this help

Examples:
  node files.js abc123
  node files.js -p abc123
  node files.js abc123 --raw
`);
}

async function listFiles(apiKey, pid) {
  const url = `${API_BASE}/${pid}`;
  
  console.log(`📁 Fetching files for site: ${pid}\n`);
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return await response.json();
}

function formatFiles(files, basePath = '') {
  if (!Array.isArray(files) || files.length === 0) {
    return 'No files found.';
  }

  let output = '';
  let totalSize = 0;
  
  // Sort files: directories first, then by name
  const sorted = [...files].sort((a, b) => {
    const aIsDir = a.type === 'directory' || a.isDirectory;
    const bIsDir = b.type === 'directory' || b.isDirectory;
    if (aIsDir && !bIsDir) return -1;
    if (!aIsDir && bIsDir) return 1;
    return (a.name || a.path || '').localeCompare(b.name || b.path || '');
  });
  
  sorted.forEach(item => {
    const name = item.name || item.path || 'unnamed';
    const isDir = item.type === 'directory' || item.isDirectory;
    const size = item.size || 0;
    const sizeFormatted = formatBytes(size);
    
    if (isDir) {
      output += `📁 ${name}/\n`;
    } else {
      output += `📄 ${name} (${sizeFormatted})\n`;
      totalSize += size;
    }
  });
  
  output += `\n📊 Total: ${files.length} items, ${formatBytes(totalSize)}\n`;
  
  return output;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
    console.error('   Example: node files.js abc123');
    process.exit(1);
  }
  
  try {
    const result = await listFiles(options.apiKey, options.pid);
    
    if (options.raw) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      // Handle different response formats
      const files = Array.isArray(result) ? result : (result.files || result.data || []);
      console.log(formatFiles(files));
    }
    
  } catch (error) {
    console.error(`❌ Failed to list files: ${error.message}`);
    process.exit(1);
  }
}

main();
