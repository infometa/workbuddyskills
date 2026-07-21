#!/usr/bin/env node
/**
 * List sites from Static.app
 */

const fetch = require('node-fetch');

const API_URL = 'https://api.static.app/v1/sites';

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    apiKey: process.env.STATIC_APP_API_KEY,
    raw: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '-k' || arg === '--api-key') {
      options.apiKey = args[++i];
    } else if (arg === '--raw') {
      options.raw = true;
    } else if (arg === '-h' || arg === '--help') {
      showHelp();
      process.exit(0);
    }
  }

  return options;
}

function showHelp() {
  console.log(`
Usage: node list.js [OPTIONS]

List all sites from Static.app account

Options:
  -k, --api-key    API key (or set STATIC_APP_API_KEY env var)
  --raw            Output raw JSON response
  -h, --help       Show this help

Examples:
  node list.js
  node list.js --raw
  node list.js -k sk_xxxxxxxx
`);
}

async function listSites(apiKey) {
  console.log('📋 Fetching sites from Static.app...\n');
  
  const response = await fetch(API_URL, {
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

function formatSites(sites) {
  if (!Array.isArray(sites) || sites.length === 0) {
    return 'No sites found.';
  }

  let output = `Found ${sites.length} site(s):\n\n`;
  
  sites.forEach((site, index) => {
    const name = site.name || site.title || 'Unnamed';
    const url = site.url || site.site_url || (site.subdomain ? `https://${site.subdomain}.static.app` : 'N/A');
    // Use pid as primary identifier (not id)
    const pid = site.pid || site.site_pid || 'N/A';
    const status = site.status || site.state || 'unknown';
    
    output += `${index + 1}. ${name}\n`;
    output += `   URL: ${url}\n`;
    output += `   PID: ${pid}\n`;
    output += `   Status: ${status}\n`;
    if (site.updated_at || site.last_deploy) {
      output += `   Updated: ${site.updated_at || site.last_deploy}\n`;
    }
    output += '\n';
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
  
  try {
    const sites = await listSites(options.apiKey);
    
    if (options.raw) {
      console.log(JSON.stringify(sites, null, 2));
    } else {
      console.log(formatSites(sites));
    }
    
  } catch (error) {
    console.error(`❌ Failed to list sites: ${error.message}`);
    process.exit(1);
  }
}

main();
