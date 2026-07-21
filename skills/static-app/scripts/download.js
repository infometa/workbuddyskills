#!/usr/bin/env node
/**
 * Download and extract a site from Static.app
 * Fetches download URL, downloads the zip, and extracts to workspace.
 */

const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');
const AdmZip = require('adm-zip');

const API_BASE = 'https://api.static.app/v1/sites/download';
// Resolve workspace root: script is in skills/static-app/scripts/, go up 3 levels
const WORKSPACE_DIR = path.join(__dirname, '..', '..', '..', 'staticapp');

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    apiKey: process.env.STATIC_APP_API_KEY,
    pid: null,
    outputDir: null,
    raw: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '-k' || arg === '--api-key') {
      options.apiKey = args[++i];
    } else if (arg === '-p' || arg === '--pid') {
      options.pid = args[++i];
    } else if (arg === '-o' || arg === '--output') {
      options.outputDir = args[++i];
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
Usage: node download.js [PID] [OPTIONS]

Download and extract a site from Static.app to your workspace.

Arguments:
  PID                Site PID to download

Options:
  -p, --pid          Site PID
  -k, --api-key      API key (or set STATIC_APP_API_KEY env var)
  -o, --output       Output directory (default: ./staticapp/{pid})
  --raw              Output raw JSON response for download URL
  -h, --help         Show this help

Examples:
  node download.js abc123
  node download.js -p abc123
  node download.js abc123 -o ./my-site
`);
}

async function getDownloadUrl(apiKey, pid) {
  const url = `${API_BASE}/${pid}`;
  
  console.log(`📥 Fetching download URL for site: ${pid}\n`);
  
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

async function downloadFile(url, destPath) {
  console.log(`⬇️  Downloading from ${url}...`);
  
  const response = await fetch(url, {
    redirect: 'follow'
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: Failed to download file`);
  }
  
  const fileStream = fs.createWriteStream(destPath);
  
  return new Promise((resolve, reject) => {
    response.body.pipe(fileStream);
    response.body.on('error', reject);
    fileStream.on('finish', () => {
      const stats = fs.statSync(destPath);
      console.log(`💾 Downloaded: ${formatBytes(stats.size)}`);
      resolve();
    });
  });
}

function extractZip(zipPath, extractPath) {
  console.log(`📦 Extracting to ${extractPath}...`);
  
  // Ensure extract directory exists
  if (!fs.existsSync(extractPath)) {
    fs.mkdirSync(extractPath, { recursive: true });
  }
  
  // Extract using adm-zip (pure Node.js, no shell commands)
  try {
    const zip = new AdmZip(zipPath);
    zip.extractAllTo(extractPath, true);
    console.log(`✅ Extracted successfully`);
  } catch (err) {
    console.error(`❌ Extraction failed: ${err.message}`);
    throw new Error('Extraction failed');
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function listExtractedFiles(dir, prefix = '') {
  let output = '';
  const items = fs.readdirSync(dir);
  
  items.forEach(item => {
    const fullPath = path.join(dir, item);
    const isDir = fs.statSync(fullPath).isDirectory();
    const icon = isDir ? '📁' : '📄';
    output += `${prefix}${icon} ${item}${isDir ? '/' : ''}\n`;
    
    if (isDir) {
      output += listExtractedFiles(fullPath, prefix + '  ');
    }
  });
  
  return output;
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
    console.error('   Example: node download.js abc123');
    process.exit(1);
  }
  
  try {
    // Step 1: Get download URL
    const result = await getDownloadUrl(options.apiKey, options.pid);
    
    if (options.raw) {
      console.log(JSON.stringify(result, null, 2));
      return;
    }
    
    // Extract download URL from response
    const downloadUrl = result.url || result.download_url || result.link;
    
    if (!downloadUrl) {
      console.error('❌ Error: No download URL in response');
      console.log('Response:', JSON.stringify(result, null, 2));
      process.exit(1);
    }
    
    console.log(`🔗 Download URL obtained`);
    
    // Step 2: Determine output directory
    const outputDir = options.outputDir || path.join(WORKSPACE_DIR, options.pid);
    const zipPath = path.join(process.cwd(), `${options.pid}-download.zip`);
    
    // Step 3: Download the file
    await downloadFile(downloadUrl, zipPath);
    
    // Step 4: Extract
    extractZip(zipPath, outputDir);
    
    // Step 5: Clean up zip file
    fs.unlinkSync(zipPath);
    console.log(`🧹 Cleaned up temporary archive`);
    
    // Step 6: Show results
    console.log(`\n✅ Site downloaded and extracted!`);
    console.log(`📁 Location: ${outputDir}`);
    console.log(`\n📂 Files:`);
    console.log(listExtractedFiles(outputDir));
    
    // Output for OpenClaw to capture
    console.log(`\nSTATIC_APP_DOWNLOAD_PATH=${outputDir}`);
    console.log(`STATIC_APP_PID=${options.pid}`);
    
  } catch (error) {
    console.error(`❌ Download failed: ${error.message}`);
    process.exit(1);
  }
}

main();