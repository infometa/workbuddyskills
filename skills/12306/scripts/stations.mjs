#!/usr/bin/env node
// Fetch and cache 12306 station data
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CACHE_FILE = join(__dirname, '..', 'data', 'stations.json');
const CACHE_TTL = 7 * 24 * 3600 * 1000;

const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
};

// --- Core functions ---

export async function loadStations(forceRefresh = false) {
  if (!forceRefresh && existsSync(CACHE_FILE)) {
    const cached = JSON.parse(readFileSync(CACHE_FILE, 'utf-8'));
    if (Date.now() - cached.ts < CACHE_TTL) return cached.data;
  }

  console.error('Fetching station data from 12306...');
  const raw = await fetchStationScript();
  const data = parseStationData(raw);

  mkdirSync(dirname(CACHE_FILE), { recursive: true });
  writeFileSync(CACHE_FILE, JSON.stringify({ ts: Date.now(), data }));
  console.error(`Cached ${Object.keys(data.STATIONS).length} stations`);

  return data;
}

export function resolveStation(data, name) {
  if (data.NAME_STATIONS[name]) return data.NAME_STATIONS[name];
  if (data.CITY_CODES[name]) return data.CITY_CODES[name];
  if (data.CITY_STATIONS[name]) return data.CITY_STATIONS[name][0];

  const trimmed = name.replace(/[市站]$/, '');
  if (data.CITY_CODES[trimmed]) return data.CITY_CODES[trimmed];
  if (data.CITY_STATIONS[trimmed]) return data.CITY_STATIONS[trimmed][0];
  return null;
}

// --- Internal helpers ---

async function fetchStationScript() {
  const homeRes = await fetch('https://www.12306.cn/index/', { headers: HEADERS });
  const homeHtml = await homeRes.text();

  const versionMatch = homeHtml.match(/station_name\.js\?station_version=([\d.]+)/);
  const jsUrl = versionMatch
    ? `https://www.12306.cn/index/script/station_name.js?station_version=${versionMatch[1]}`
    : 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js';

  const jsRes = await fetch(jsUrl, { headers: HEADERS });
  return jsRes.text();
}

function parseStationData(jsText) {
  // Format: @bjb|北京北|VAP|beijingbei|bjb|0|0357|北京|||
  //          [0]  [1]   [2]   [3]     [4] [5] [6] [7] [8][9][10]
  const raw = jsText.match(/'([^']+)'/)?.[1] || '';
  const entries = raw.split('@').filter(Boolean);

  const STATIONS = {};
  const CITY_STATIONS = {};
  const NAME_STATIONS = {};
  const CITY_CODES = {};

  for (const entry of entries) {
    const parts = entry.split('|');
    const name = parts[1], code = parts[2], pinyin = parts[3], shortPy = parts[4];
    const city = parts[7] || name; // field [7] = city name from 12306
    if (!name || !code) continue;

    STATIONS[code] = { station_name: name, station_code: code, station_pinyin: pinyin, station_short: shortPy, city };
    NAME_STATIONS[name] = { station_code: code, station_name: name };
    (CITY_STATIONS[city] ??= []).push({ station_code: code, station_name: name });
    if (name === city) CITY_CODES[city] = { station_code: code, station_name: name };
  }

  return { STATIONS, CITY_STATIONS, NAME_STATIONS, CITY_CODES };
}

// --- CLI ---

if (process.argv[1]?.includes('stations.mjs') && process.argv[2]) {
  const data = await loadStations();
  const name = process.argv[2];
  const result = resolveStation(data, name);
  if (!result) {
    console.error(`Station not found: ${name}`);
    process.exit(1);
  }

  console.log(JSON.stringify(result));
  const city = data.STATIONS[result.station_code]?.city || name;
  if (data.CITY_STATIONS[city]) {
    console.log(`\nAll stations in ${city}:`);
    for (const s of data.CITY_STATIONS[city]) console.log(`  ${s.station_name} (${s.station_code})`);
  }
}
