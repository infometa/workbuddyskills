#!/usr/bin/env node
/**
 * get-targeting-lookup.mjs — 定向编码转换
 *
 * 提供定向相关的数据转换能力（不做定向决策，只做编码转换）。
 * 地域和设备查询从本地资源文件读取，无需 API 调用。
 *
 * 入参:
 *   地域查询: '{"type":"geo","keyword":"广东省"}'
 *   批量地域: '{"type":"geo","keyword":"北京 上海 广东"}'
 *   设备查询: '{"type":"device","keyword":"华为"}'
 *   批量设备: '{"type":"device","keyword":"华为 小米"}'
 *
 * 地域输出:
 * {
 *   "results": [
 *     {"id": 440000, "name": "广东省", "level": "province", "city_level": 4}
 *   ]
 * }
 *
 * 设备输出:
 * {
 *   "results": [
 *     {"id": 10001, "name": "华为 Mate 60"},
 *     {"id": 10002, "name": "华为 P60"}
 *   ]
 * }
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 资源文件与脚本同属本 skill，路径始终相对于脚本目录
const RESOURCE_DIR = join(__dirname, "../resources");
const GEO_REGIONS_FILE = join(RESOURCE_DIR, "geo-regions.json");
const DEVICE_BRANDS_FILE = join(RESOURCE_DIR, "device-brands.json");

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` }));
  process.exit(1);
}

const { type, keyword } = input;

if (!type) {
  console.log(JSON.stringify({ error: "missing required field: type (\"geo\" 或 \"device\")" }));
  process.exit(1);
}
if (!keyword) {
  console.log(JSON.stringify({ error: "missing required field: keyword" }));
  process.exit(1);
}

// ─── 地域编码查询 ───

function loadGeoRegions() {
  try {
    return JSON.parse(readFileSync(GEO_REGIONS_FILE, "utf-8"));
  } catch (err) {
    throw new Error(`无法读取地域编码文件 ${GEO_REGIONS_FILE}: ${err.message}`);
  }
}

function searchGeo(keyword) {
  const regions = loadGeoRegions();
  const keywords = keyword.split(/[\s,，]+/).filter(Boolean);
  const allResults = [];

  for (const kw of keywords) {
    const kwLower = kw.toLowerCase();
    for (const [code, entry] of Object.entries(regions)) {
      const name = entry.name ?? "";
      if (name.toLowerCase().includes(kwLower) || code.includes(kw)) {
        allResults.push({
          id: parseInt(code, 10),
          name,
          level: entry.level ?? "unknown",
          city_level: entry.city_level ?? null,
          parent: entry.parent ?? null,
        });
      }
    }
  }

  // 去重
  const seen = new Set();
  const results = allResults.filter((r) => {
    if (seen.has(r.id)) return false;
    seen.add(r.id);
    return true;
  });

  return results;
}

// ─── 设备品牌型号查询 ───

function loadDeviceBrands() {
  try {
    return JSON.parse(readFileSync(DEVICE_BRANDS_FILE, "utf-8"));
  } catch (err) {
    throw new Error(`无法读取设备品牌文件 ${DEVICE_BRANDS_FILE}: ${err.message}`);
  }
}

function searchDevice(keyword) {
  const brands = loadDeviceBrands();
  const keywords = keyword.split(/[\s,，]+/).filter(Boolean);
  const allResults = [];

  for (const kw of keywords) {
    const kwLower = kw.toLowerCase();
    for (const [id, name] of Object.entries(brands)) {
      if (String(name).toLowerCase().includes(kwLower) || id.includes(kw)) {
        allResults.push({
          id: parseInt(id, 10),
          name: String(name),
        });
      }
    }
  }

  // 去重
  const seen = new Set();
  const results = allResults.filter((r) => {
    if (seen.has(r.id)) return false;
    seen.add(r.id);
    return true;
  });

  return results;
}

// ─── 主逻辑 ───

try {
  if (type === "geo") {
    const results = searchGeo(String(keyword));
    console.log(JSON.stringify({ results }, null, 2));
  } else if (type === "device") {
    const results = searchDevice(String(keyword));
    console.log(JSON.stringify({ results }, null, 2));
  } else {
    console.log(JSON.stringify({ error: `不支持的 type: "${type}"，请使用 "geo" 或 "device"` }));
    process.exit(1);
  }
} catch (err) {
  console.log(JSON.stringify({ error: err.message }));
  process.exit(1);
}
