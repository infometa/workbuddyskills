#!/usr/bin/env node
/**
 * Static.app deployment script for OpenClaw.
 * Uploads a directory as a zip archive to Static.app hosting.
 */

const fs = require('fs');
const path = require('path');
const archiver = require('archiver');
const FormData = require('form-data');
const fetch = require('node-fetch');

const API_URL = 'https://api.static.app/v1/sites/zip/';
const DEFAULT_EXCLUDE = ['node_modules', '.git', '.github', '*.md', 'package*.json', '.env', '.openclaw'];

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    sourceDir: '.',
    apiKey: process.env.STATIC_APP_API_KEY,
    pid: null,
    exclude: null,
    keepZip: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '-k' || arg === '--api-key') {
      options.apiKey = args[++i];
    } else if (arg === '-p' || arg === '--pid') {
      options.pid = args[++i];
    } else if (arg === '-e' || arg === '--exclude') {
      options.exclude = args[++i];
    } else if (arg === '--keep-zip') {
      options.keepZip = true;
    } else if (!arg.startsWith('-')) {
      options.sourceDir = arg;
    }
  }

  return options;
}

function shouldExclude(filePath, excludePatterns) {
  const parts = filePath.split(path.sep);
  const fileName = parts[parts.length - 1];
  
  for (const pattern of excludePatterns) {
    // Handle directory patterns
    if (parts.includes(pattern)) return true;
    
    // Handle glob patterns like *.md
    if (pattern.startsWith('*')) {
      const ext = pattern.slice(1);
      if (fileName.endsWith(ext)) return true;
    }
    
    // Handle wildcard in middle like package*.json
    if (pattern.includes('*')) {
      const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
      if (regex.test(fileName)) return true;
    }
    
    // Exact match
    if (fileName === pattern) return true;
  }
  
  return false;
}

async function createZipArchive(sourceDir, excludePatterns) {
  const sourcePath = path.resolve(sourceDir);
  const zipPath = path.join(process.cwd(), 'static-app-deploy.zip');
  
  console.log(`📦 Creating zip archive from ${sourcePath}...`);
  
  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream(zipPath);
    const archive = archiver('zip', { zlib: { level: 9 } });

    output.on('close', () => {
      const size = archive.pointer();
      console.log(`📦 Archive created: ${size.toLocaleString()} bytes`);
      resolve(zipPath);
    });

    archive.on('error', (err) => {
      reject(err);
    });

    archive.on('warning', (err) => {
      if (err.code === 'ENOENT') {
        console.warn(`⚠️  Warning: ${err.message}`);
      } else {
        reject(err);
      }
    });

    archive.pipe(output);

    // Read directory and add files
    function addDirectory(dir, baseDir) {
      const items = fs.readdirSync(dir);
      
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const relPath = path.relative(baseDir, fullPath);
        
        if (shouldExclude(relPath, excludePatterns)) {
          continue;
        }
        
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
          addDirectory(fullPath, baseDir);
        } else {
          archive.file(fullPath, { name: relPath });
        }
      }
    }

    addDirectory(sourcePath, sourcePath);
    archive.finalize();
  });
}

async function deploy(apiKey, zipPath, pid) {
  console.log(`🚀 Uploading to Static.app...`);
  
  const form = new FormData();
  // Read file into buffer to handle redirects properly
  const fileBuffer = fs.readFileSync(zipPath);
  form.append('archive', fileBuffer, { filename: 'deploy.zip' });
  
  if (pid) {
    form.append('pid', pid);
    console.log(`   Updating existing site: ${pid}`);
  }

  const response = await fetch(API_URL, {
    method: 'POST',
    body: form,
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      ...form.getHeaders()
    },
    redirect: 'follow'
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  const result = await response.json();
  
  // Extract URLs from various possible response formats
  let siteUrl = result.url || result.site_url;
  if (!siteUrl && result.subdomain) {
    siteUrl = `https://${result.subdomain}.static.app`;
  }
  
  // Use pid as primary identifier (not id)
  const sitePid = result.pid || result.site_pid || pid;
  
  return {
    sitePid,
    siteUrl,
    deployUrl: result.deploy_url || siteUrl
  };
}

async function main() {
  const options = parseArgs();
  
  if (!options.apiKey) {
    console.error('❌ Error: API key required. Provide --api-key or set STATIC_APP_API_KEY env var.');
    console.error('   Get your API key at: https://static.app/account/api');
    process.exit(1);
  }
  
  // Parse exclude patterns
  const exclude = [...DEFAULT_EXCLUDE];
  if (options.exclude) {
    exclude.push(...options.exclude.split(',').map(p => p.trim()));
  }
  
  try {
    // Create zip
    const zipPath = await createZipArchive(options.sourceDir, exclude);
    
    // Deploy
    const result = await deploy(options.apiKey, zipPath, options.pid);
    
    // Clean up
    if (!options.keepZip) {
      fs.unlinkSync(zipPath);
      console.log(`🧹 Cleaned up temporary archive`);
    } else {
      console.log(`💾 Kept archive: ${zipPath}`);
    }
    
    // Output results
    console.log(`\n✅ Deployment successful!`);
    console.log(`🌐 Site URL: ${result.siteUrl}`);
    if (result.sitePid) {
      console.log(`📋 PID: ${result.sitePid}`);
    }
    
    // Output for OpenClaw to capture
    console.log(`\nSTATIC_APP_URL=${result.siteUrl}`);
    console.log(`STATIC_APP_PID=${result.sitePid}`);
    
  } catch (error) {
    console.error(`❌ Deployment failed: ${error.message}`);
    process.exit(1);
  }
}

main();
